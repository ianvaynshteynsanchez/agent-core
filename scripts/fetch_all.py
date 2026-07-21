import time
from app.db.store import connect
from app.sources import grants_gov

conn = connect()
rows = conn.execute(
    "SELECT id FROM opportunity WHERE source='grants_gov' "
    "AND (description IS NULL OR description='')"
).fetchall()

print(f"fetching {len(rows)} descriptions (free, ~{len(rows)//4} min)...")
ok = 0
for i, r in enumerate(rows):
    oid = r["id"].split(":", 1)[1]
    detail = grants_gov.fetch(oid)
    if detail:
        syn = detail.get("synopsis", {})
        conn.execute(
            "UPDATE opportunity SET description=?, url=COALESCE(?, url) WHERE id=?",
            (syn.get("synopsisDesc"), syn.get("fundingDescLinkUrl"), r["id"]),
        )
        ok += 1
    if i % 20 == 0:
        conn.commit()
        print(f"  {i}/{len(rows)}  ({ok} ok)")
    time.sleep(0.3)

conn.commit()
conn.close()
print(f"done: {ok} descriptions fetched")
