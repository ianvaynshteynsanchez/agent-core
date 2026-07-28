"""Generate detail briefs for pursue opportunities, cached so the expensive
retrieval+LLM work happens once per opportunity, not every dashboard build."""
import json
from datetime import datetime, timezone

from app.db.store import connect
from app.detail.brief import build_brief
from app.detail.fetch import fetch_full_text


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
            "INSERT OR REPLACE INTO brief VALUES (?,?,?,?,?,?)",
            (opp_id, native_id, status, None, url,
             datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        conn.close()
        return {"status": status, "answers": {}, "url": url}
    conn.close()

    # Available: do the real work.
    brief = build_brief(opp_id, native_id)
    conn = connect()
    conn.execute(
        "INSERT OR REPLACE INTO brief VALUES (?,?,?,?,?,?)",
        (opp_id, native_id, "ok", json.dumps(brief["answers"]),
         brief["url"], datetime.now(timezone.utc).isoformat()),
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
        # retry unpublished ones (they may have gone live since last attempt)
        if before["status"] != "ok":
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
