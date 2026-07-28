from app.db.store import connect
from app.sources.poll import upsert

conn = connect()
# grab a real forecasted opportunity to simulate
f = conn.execute("SELECT * FROM opportunity WHERE status='forecasted' LIMIT 1").fetchone()
if not f:
    print("no forecasted opportunity to test with")
else:
    row = dict(f)
    print(f"simulating open of: {row['title'][:55]}")
    print(f"  before: status={row['status']}, became_posted={row['became_posted']}")
    row["status"] = "posted"
    row["last_seen"] = "2026-07-26T12:00:00"
    upsert(conn, row)
    conn.commit()
    after = conn.execute("SELECT status, became_posted FROM opportunity WHERE id=?",
                         (row["id"],)).fetchone()
    print(f"  after:  status={after['status']}, became_posted={after['became_posted']}")
