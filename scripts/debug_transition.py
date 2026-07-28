from app.db.store import connect

conn = connect()
f = conn.execute("SELECT * FROM opportunity WHERE status='forecasted' LIMIT 1").fetchone()
row = dict(f)
print("test row id:", row["id"])

existing = conn.execute(
    "SELECT id, status, became_posted FROM opportunity WHERE id = ?",
    (row["id"],),
).fetchone()
print("existing status:", repr(existing["status"]))
print("incoming status would be: 'posted'")
print("became_posted:", repr(existing["became_posted"]))

just_opened = (
    existing["status"] == "forecasted"
    and "posted" == "posted"
    and not existing["became_posted"]
)
print("just_opened evaluates to:", just_opened)
