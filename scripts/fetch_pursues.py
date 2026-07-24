import json

from app.db.store import connect
from app.sources import grants_gov

conn = connect()
rows = conn.execute(
    "SELECT id, native_id FROM opportunity "
    "WHERE id IN (SELECT opportunity_id FROM assessment WHERE verdict='pursue')"
).fetchall()

for r in rows:
    detail = grants_gov.fetch(r["id"].split(":", 1)[1])
    if not detail:
        print("fetch failed:", r["native_id"])
        continue
    syn = detail.get("synopsis", {})
    link = syn.get("fundingDescLinkUrl")
    conn.execute(
        "UPDATE opportunity SET raw_json=?, url=COALESCE(?, url) WHERE id=?",
        (json.dumps(detail), link, r["id"]),
    )
    print(f"{r['native_id']:24} link={link}")

conn.commit()
conn.close()
