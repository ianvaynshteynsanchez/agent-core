from app.reason.filter import shortlist
from app.sources import grants_gov
from app.db.store import connect

conn = connect()
todo = [r for r in shortlist(verbose=False)
        if not r.get("description") and r["source"] == "grants_gov"]
print(f"fetching {len(todo)} descriptions...")

for r in todo:
    oid = r["id"].split(":", 1)[1]
    detail = grants_gov.fetch(oid)
    if not detail:
        print(f"  miss: {r['title'][:40]}")
        continue
    syn = detail.get("synopsis", {})
    conn.execute(
        "UPDATE opportunity SET description=?, url=COALESCE(?, url) WHERE id=?",
        (syn.get("synopsisDesc"), syn.get("fundingDescLinkUrl"), r["id"]),
    )
    print(f"  ok: {r['title'][:40]}")

conn.commit()
conn.close()
