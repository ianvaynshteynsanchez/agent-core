"""Measure reasoner agreement against hand-labeled verdicts.

Labels live in evals/verdicts.txt (or evals/verdicts-<client>.txt for
non-default clients), one per line:
    <opportunity_id> | <expected verdict> | <note> | <phrases the rationale must not contain>
Lines starting with # are ignored.
"""
import sys
import time
from app.db.store import connect
from app.reason.assess import assess_one, current_profile

import os
_CLIENT = os.getenv("CLIENT", "hera")
LABELS = ("evals/verdicts.txt" if _CLIENT == "hera"
          else f"evals/verdicts-{_CLIENT}.txt")


def load_labels():
    out = []
    with open(LABELS) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 2:
                banned = []
                if len(parts) > 3 and parts[3]:
                    banned = [b.strip().lower() for b in parts[3].split(",") if b.strip()]
                out.append((parts[0], parts[1].lower(),
                            parts[2] if len(parts) > 2 else "", banned))
    return out


def run(live=False):
    labels = load_labels()
    if not labels:
        raise SystemExit(f"No labels in {LABELS}")

    conn = connect()
    pv, ptext = current_profile(conn)
    print(f"profile v{pv} | {len(labels)} labeled cases | {'re-running' if live else 'reading stored'}\n")

    agree = disagree = missing = weak = 0
    for oid, expected, note, banned in labels:
        opp = conn.execute("SELECT * FROM opportunity WHERE id=?", (oid,)).fetchone()
        if not opp:
            print(f"  MISSING  {oid}")
            missing += 1
            continue

        if live:
            data = None
            for attempt in range(5):
                try:
                    data, _ = assess_one(conn, dict(opp), pv, ptext)
                    break
                except Exception as e:
                    if "rate_limit" in str(e) or "429" in str(e):
                        wait = 8 * (attempt + 1)
                        print(f"        rate limited, waiting {wait}s")
                        time.sleep(wait)
                        continue
                    raise
            if data is None:
                print(f"  RATELIMIT {opp['title'][:50]}")
                missing += 1
                continue
            actual = (data.get("verdict") or "").lower()
            rationale = data.get("rationale", "")
        else:
            row = conn.execute(
                "SELECT verdict, rationale FROM assessment WHERE opportunity_id=? "
                "ORDER BY profile_version DESC LIMIT 1", (oid,)).fetchone()
            if not row:
                print(f"  NOASSESS {opp['title'][:50]}")
                missing += 1
                continue
            actual, rationale = row["verdict"], row["rationale"]

        if actual == expected:
            hits = [b for b in banned if b in (rationale or "").lower()]
            if hits:
                weak += 1
                print(f"  WEAK  {expected:6} {opp['title'][:55]}")
                print(f"        right verdict, bad reasoning: {', '.join(hits)}")
                print(f"        model said: {rationale[:160]}...")
            else:
                agree += 1
                print(f"  PASS  {expected:6} {opp['title'][:55]}")
        else:
            disagree += 1
            print(f"  FAIL  expected {expected:6} got {actual:6}  {opp['title'][:45]}")
            if note:
                print(f"        why it matters: {note}")
            print(f"        model said: {rationale[:160]}...")

    conn.commit()
    conn.close()
    total = agree + disagree + weak
    pct = (agree / total * 100) if total else 0
    print(f"\n  {agree}/{total} clean ({pct:.0f}%)  |  "
          f"{disagree} wrong verdict  |  {weak} weak reasoning  |  {missing} missing")
    return pct


if __name__ == "__main__":
    run(live="--live" in sys.argv)
