"""Generate detail briefs for pursue opportunities, cached so the expensive
retrieval+LLM work happens once per opportunity, not every dashboard build."""
import json
from datetime import datetime, timezone

from app.db.store import connect
from app.detail.brief import build_brief
from app.detail.fetch import fetch_full_text


RETRY_AFTER_DAYS = [3, 7, 14, 30]


def _attempts(conn, opp_id):
    row = conn.execute(
        "SELECT attempts FROM brief WHERE opportunity_id=?", (opp_id,)).fetchone()
    return (row["attempts"] or 0) if row else 0


def _should_retry(conn, opp_id):
    """True if an unpublished brief is due for another attempt.

    A became_posted event inside the last 7 days always wins: that transition
    is the thing we are waiting for, and must never be delayed by the backoff.
    """
    row = conn.execute(
        "SELECT b.attempts, b.created_at, o.became_posted "
        "FROM brief b JOIN opportunity o ON o.id = b.opportunity_id "
        "WHERE b.opportunity_id=?", (opp_id,)).fetchone()
    if not row:
        return True

    if row["became_posted"]:
        try:
            age = (datetime.now(timezone.utc)
                   - datetime.fromisoformat(row["became_posted"])).days
            if age <= 7:
                return True
        except (ValueError, TypeError):
            return True   # unparseable timestamp: retry rather than suppress

    n = row["attempts"] or 0
    wait = RETRY_AFTER_DAYS[min(n, len(RETRY_AFTER_DAYS) - 1)]
    try:
        since = (datetime.now(timezone.utc)
                 - datetime.fromisoformat(row["created_at"])).days
    except (ValueError, TypeError):
        return True
    return since >= wait


def get_or_build(opp_id, native_id, force=False):
    conn = connect()
    if not force:
        row = conn.execute(
            "SELECT status, answers, url FROM brief WHERE opportunity_id=?",
            (opp_id,),
        ).fetchone()
        if row:
            conn.close()
            return {"status": row["status"],
                    "answers": json.loads(row["answers"]) if row["answers"] else {},
                    "url": row["url"]}

    # Not cached (or forced): check availability first, cheaply.
    _, url, status = fetch_full_text(native_id)
    if status != "ok":
        conn.execute(
            "INSERT OR REPLACE INTO brief "
            "(opportunity_id, native_id, status, answers, url, created_at, attempts) "
            "VALUES (?,?,?,?,?,?,?)",
            (opp_id, native_id, status, None, url,
             datetime.now(timezone.utc).isoformat(), _attempts(conn, opp_id) + 1),
        )
        conn.commit()
        conn.close()
        return {"status": status, "answers": {}, "url": url}
    conn.close()

    # Available: do the real work.
    brief = build_brief(opp_id, native_id)
    conn = connect()
    conn.execute(
        "INSERT OR REPLACE INTO brief "
        "(opportunity_id, native_id, status, answers, url, created_at, attempts) "
        "VALUES (?,?,?,?,?,?,?)",
        (opp_id, native_id, "ok", json.dumps(brief["answers"]),
         brief["url"], datetime.now(timezone.utc).isoformat(), 0),
    )
    conn.commit()
    conn.close()
    return {"status": "ok", "answers": brief["answers"], "url": brief["url"]}


def refresh_pursues():
    """Called by the pipeline: ensure every current pursue has a brief attempt.
    Cheap for cached/unpublished ones; only new publishable pursues cost tokens."""
    conn = connect()
    pv = conn.execute("SELECT MAX(version) v FROM profile").fetchone()["v"]
    rows = conn.execute(
        "SELECT o.id, o.native_id FROM assessment a "
        "JOIN opportunity o ON a.opportunity_id=o.id "
        "WHERE a.verdict='pursue' AND a.profile_version=?", (pv,)
    ).fetchall()
    conn.close()
    built = 0
    for r in rows:
        before = get_or_build(r["id"], r["native_id"])
        # retry unpublished ones only when they are due (or just went live)
        if before["status"] != "ok":
            c = connect()
            due = _should_retry(c, r["id"])
            c.close()
            if due:
                before = get_or_build(r["id"], r["native_id"], force=True)
        if before["status"] == "ok":
            built += 1
    return built, len(rows)


if __name__ == "__main__":
    # test against a known-published NOFO
    b = get_or_build("test:par-24-312", "PAR-24-312", force=True)
    print("status:", b["status"])
    for k, v in b["answers"].items():
        print(f"  {k}: {v['answer'][:80]}")
