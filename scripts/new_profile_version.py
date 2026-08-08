"""Save profiles/vN.md as a new profile version, triggering re-assessment
of shortlisted opportunities without deleting assessment history."""
import sys
from datetime import datetime, timezone

from app.db.store import connect

path = sys.argv[1] if len(sys.argv) > 1 else "profiles/v2.md"
note = sys.argv[2] if len(sys.argv) > 2 else "profile update"

content = open(path).read()
assert len(content) > 3000, f"file looks truncated: {len(content)} chars"

conn = connect()
row = conn.execute("SELECT MAX(version) v FROM profile").fetchone()
version = (row["v"] or 0) + 1
conn.execute(
    "INSERT INTO profile (version, client, content, created_at, note) VALUES (?,?,?,?,?)",
    (version, CLIENT, content, datetime.now(timezone.utc).isoformat(), note),
)
conn.commit()
conn.close()
print(f"profile v{version} saved from {path} ({len(content)} chars)")
print("next pipeline run will assess against it; old verdicts kept for comparison")
