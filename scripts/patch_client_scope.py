"""Wire up CLIENT. It's read from the env in load.py and never used, so
active() returns the highest-versioned profile regardless of subject."""
import pathlib, shutil, sys

edits = []

# 1. schema.sql - add the column
p = pathlib.Path("app/db/schema.sql")
s = p.read_text()
OLD = '''CREATE TABLE IF NOT EXISTS profile (
  version       INTEGER PRIMARY KEY,'''
NEW = '''CREATE TABLE IF NOT EXISTS profile (
  version       INTEGER PRIMARY KEY,
  client        TEXT NOT NULL DEFAULT 'hera',  -- which subject this describes'''
if "client        TEXT" in s:
    sys.exit("already patched (schema) - no change made")
if OLD not in s:
    sys.exit("ANCHOR NOT FOUND (schema) - nothing written")
edits.append((p, s.replace(OLD, NEW, 1), "app/db/schema.sql.bak2"))

# 2. load.py - filter by client, and fail loudly
p = pathlib.Path("app/profile/load.py")
s = p.read_text()
OLD = '''    row = conn.execute(
        "SELECT version, content FROM profile ORDER BY version DESC LIMIT 1"
    ).fetchone()
    if own:
        conn.close()
    if not row:
        raise SystemExit("No profile found.")'''
NEW = '''    row = conn.execute(
        "SELECT version, content FROM profile WHERE client=? "
        "ORDER BY version DESC LIMIT 1", (CLIENT,)
    ).fetchone()
    if own:
        conn.close()
    if not row:
        raise SystemExit(f"No profile found for client '{CLIENT}'.")'''
if "WHERE client=?" in s:
    sys.exit("already patched (load) - no change made")
if OLD not in s:
    sys.exit("ANCHOR NOT FOUND (load) - nothing written")
edits.append((p, s.replace(OLD, NEW, 1), "app/profile/load.py.bak"))

# 3 & 4. both insert sites - write the client explicitly
for fname, bak in (("app/profile/generate.py", "app/profile/generate.py.bak"),
                   ("scripts/new_profile_version.py", "scripts/new_profile_version.py.bak")):
    p = pathlib.Path(fname)
    s = p.read_text()
    OLD = '"INSERT INTO profile (version, content, created_at, note) VALUES (?,?,?,?)",'
    NEW = '"INSERT INTO profile (version, client, content, created_at, note) VALUES (?,?,?,?,?)",'
    if OLD not in s:
        sys.exit(f"ANCHOR NOT FOUND ({fname}) - nothing written")
    edits.append((p, s.replace(OLD, NEW, 1), bak))

for p, new_src, bak in edits:
    shutil.copy(p, bak)
    p.write_text(new_src)
    print(f"patched {p}")
print("\nNOTE: the two insert sites now need CLIENT passed as the 2nd value.")
print("Check the tuples following those lines - they need one more element.")
