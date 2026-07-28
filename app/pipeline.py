"""Daily run: poll -> fetch -> filter -> assess new -> rebuild dashboard.

Every stage is wrapped. A failure in one stage logs and continues; the
dashboard still rebuilds from whatever is in the database.
"""
import sys
import time
import traceback
from datetime import datetime, timezone

from app.db.store import connect

from app.profile.load import search_keywords



def log(stage, msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {stage:10} {msg}", flush=True)


def stage(name, fn, *args, **kwargs):
    """Run a stage; never let it kill the pipeline."""
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        log(name, f"FAILED: {e}")
        traceback.print_exc()
        return None


def do_poll():
    from app.sources.poll import poll
    new_ids = poll(search_keywords(), fetch_details=False)
    log("poll", f"{len(new_ids)} new opportunities")
    return new_ids


def do_fetch():
    """Fetch descriptions for anything missing one. Free, no tokens."""
    from app.sources import grants_gov
    conn = connect()
    # Skip ones we already tried in the last 7 days - forecasted opps have
    # no synopsis to fetch, and retrying them daily wastes requests.
    rows = conn.execute(
        "SELECT id FROM opportunity WHERE source='grants_gov' "
        "AND (description IS NULL OR description='') "
        "AND (fetch_attempted IS NULL OR fetch_attempted < date('now','-7 days'))"
    ).fetchall()
    log("fetch", f"{len(rows)} missing descriptions")

    ok = 0
    for i, r in enumerate(rows):
        detail = grants_gov.fetch(r["id"].split(":", 1)[1])
        if detail:
            import json as _json
            syn = detail.get("synopsis", {})
            link = syn.get("fundingDescLinkUrl")
            conn.execute(
                "UPDATE opportunity SET description=?, url=COALESCE(?, url), "
                "raw_json=? WHERE id=?",
                (syn.get("synopsisDesc"), link, _json.dumps(detail), r["id"]),
            )
            ok += 1
        conn.execute("UPDATE opportunity SET fetch_attempted=date('now') WHERE id=?",
                     (r["id"],))
        if i % 25 == 0:
            conn.commit()
        time.sleep(0.3)
    conn.commit()
    conn.close()
    log("fetch", f"{ok} fetched")
    return ok


def do_assess():
    """Assess only shortlisted opportunities without a current assessment."""
    from app.reason.filter import shortlist
    from app.reason.assess import assess_one, current_profile

    conn = connect()
    pv, ptext = current_profile(conn)
    done = {r["opportunity_id"] for r in conn.execute(
        "SELECT opportunity_id FROM assessment WHERE profile_version=?", (pv,))}

    todo = [r for r in shortlist(verbose=False)
            if r.get("description") and r["id"] not in done]
    log("assess", f"{len(todo)} to assess (profile v{pv})")

    tokens = 0
    for opp in todo:
        for attempt in range(3):
            try:
                data, t = assess_one(conn, opp, pv, ptext)
                tokens += t
                log("assess", f"  [{data.get('verdict','?'):6}] {opp['title'][:45]}")
                conn.commit()
                break
            except Exception as e:
                msg = str(e)
                if "rate_limit" in msg or "429" in msg:
                    if "per day" in msg or "TPD" in msg:
                        log("assess", "  DAILY TOKEN LIMIT reached - stopping assess stage")
                        return tokens
                    wait = 30 * (attempt + 1)
                    log("assess", f"  rate limited, waiting {wait}s")
                    time.sleep(wait)
                    continue
                log("assess", f"  error on {opp['id']}: {e}")
                break
    conn.close()
    log("assess", f"done, {tokens} tokens")
    return tokens


def do_prune_versions():
    """Remove assessments from superseded profile versions. Prevents the
    dashboard from stacking contradictory verdicts across versions."""
    conn = connect()
    pv = conn.execute("SELECT MAX(version) v FROM profile").fetchone()["v"]
    n = conn.execute(
        "SELECT COUNT(*) c FROM assessment WHERE profile_version < ?", (pv,)
    ).fetchone()["c"]
    if n:
        conn.execute("DELETE FROM assessment WHERE profile_version < ?", (pv,))
        conn.commit()
        log("prune", f"removed {n} assessments from old profile versions")
    conn.close()
    return n


def do_prune_versions():
    """Remove assessments from superseded profile versions. Prevents the
    dashboard from stacking contradictory verdicts across versions."""
    conn = connect()
    pv = conn.execute("SELECT MAX(version) v FROM profile").fetchone()["v"]
    n = conn.execute(
        "SELECT COUNT(*) c FROM assessment WHERE profile_version < ?", (pv,)
    ).fetchone()["c"]
    if n:
        conn.execute("DELETE FROM assessment WHERE profile_version < ?", (pv,))
        conn.commit()
        log("prune", f"removed {n} assessments from old profile versions")
    conn.close()
    return n


def do_prune():
    """Drop assessments for opportunities no longer shortlisted (expired etc)."""
    from app.reason.filter import shortlist
    ids = {r["id"] for r in shortlist(verbose=False)}
    conn = connect()
    allrows = [r["opportunity_id"] for r in
               conn.execute("SELECT opportunity_id FROM assessment")]
    stale = [o for o in allrows if o not in ids]
    # Refuse only when the shortlist has collapsed - the real bad-poll signal.
    if len(ids) < 3 and len(stale) > 2:
        log("prune", f"REFUSING: shortlist collapsed to {len(ids)} - likely a bad poll")
        conn.close()
        return 0
    for o in stale:
        conn.execute("DELETE FROM assessment WHERE opportunity_id=?", (o,))
    conn.commit()
    conn.close()
    if stale:
        log("prune", f"removed {len(stale)} stale assessments")
    return len(stale)


def do_dashboard():
    from app.dashboard.build import build
    build()
    log("dash", "dashboard.html rebuilt")


def run():
    started = datetime.now(timezone.utc)
    log("start", f"pipeline run {started.isoformat()}")

    stage("poll", do_poll)
    stage("fetch", do_fetch)
    stage("prune", do_prune)
    stage("prune-v", do_prune_versions)
    stage("prune-v", do_prune_versions)
    stage("assess", do_assess)
    stage("dash", do_dashboard)

    secs = (datetime.now(timezone.utc) - started).total_seconds()
    log("done", f"completed in {secs:.0f}s")


if __name__ == "__main__":
    sys.exit(run())
