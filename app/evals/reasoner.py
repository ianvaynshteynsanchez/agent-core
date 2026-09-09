"""Measure reasoner agreement against hand-labeled verdicts.

Labels live in evals/verdicts.txt (or evals/verdicts-<client>.txt for
non-default clients), one per line:
    <opportunity_id> | <expected verdict> | <note> | <phrases the rationale must not contain>
Lines starting with # are ignored.
"""
import os
os.environ.setdefault("ASSESS_TEMP", "0")  # evals must be reproducible

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


def _assess_with_retry(conn, opp, pv, ptext):
    """One assessment with rate-limit backoff. Returns (verdict, rationale) or None."""
    for attempt in range(5):
        try:
            data, _ = assess_one(conn, dict(opp), pv, ptext)
            return (data.get("verdict") or "").lower(), data.get("rationale", "")
        except Exception as e:
            msg = str(e)
            if ("json_validate_failed" in msg or "Failed to generate JSON" in msg):
                print("        malformed JSON from model, retrying")
                time.sleep(2)
                continue
            if "rate_limit" in msg or "429" in msg:
                wait = 8 * (attempt + 1)
                print(f"        rate limited, waiting {wait}s")
                time.sleep(wait)
                continue
            raise
    return None


def _outcome(actual, expected, rationale, banned):
    """PASS | FAIL | WEAK for one assessment."""
    if actual != expected:
        return "FAIL"
    if [b for b in banned if b in (rationale or "").lower()]:
        return "WEAK"
    return "PASS"


def run(live=False, runs=1):
    labels = load_labels()
    if not labels:
        raise SystemExit(f"No labels in {LABELS}")

    conn = connect()
    pv, ptext = current_profile(conn)
    print(f"profile v{pv} | {len(labels)} labeled cases | {'re-running' if live else 'reading stored'}\n")

    agree = disagree = missing = weak = 0
    unstable = []
    for oid, expected, note, banned in labels:
        opp = conn.execute("SELECT * FROM opportunity WHERE id=?", (oid,)).fetchone()
        if not opp:
            print(f"  MISSING  {oid}")
            missing += 1
            continue

        if live:
            results = []
            for _ in range(runs):
                got = _assess_with_retry(conn, opp, pv, ptext)
                if got is None:
                    break
                results.append(got)
            if not results:
                print(f"  RATELIMIT {opp['title'][:50]}")
                missing += 1
                continue
            outcomes = [_outcome(a, expected, r, banned) for a, r in results]
            majority = max(set(outcomes), key=outcomes.count)
            if runs > 1:
                n = outcomes.count(majority)
                tag = f"({n}/{runs} stable)" if n == runs else \
                      f"({n}/{runs} - also {', '.join(sorted(set(outcomes) - {majority}))})"
                if n < runs:
                    unstable.append(opp["title"][:45])
                print(f"  {majority:5} {expected:6} {opp['title'][:45]} {tag}")
                if majority == "PASS":
                    agree += 1
                elif majority == "WEAK":
                    weak += 1
                else:
                    disagree += 1
                continue
            actual, rationale = results[0]
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
    _n = 1
    if "--runs" in sys.argv:
        _n = int(sys.argv[sys.argv.index("--runs") + 1])
    run(live="--live" in sys.argv, runs=_n)
