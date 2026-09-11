"""schema.sql lacks the attempts column that cache.py now writes to."""
import pathlib, shutil, sys

path = pathlib.Path("app/db/schema.sql")
src = path.read_text()

OLD = '''  url            TEXT,
  created_at     TEXT
);'''
NEW = '''  url            TEXT,
  created_at     TEXT,
  attempts       INTEGER DEFAULT 0        -- failed brief fetches, drives backoff
);'''

if "attempts" in src:
    sys.exit("already patched - no change made")
if OLD not in src:
    sys.exit("ANCHOR NOT FOUND - paste the brief table block")

shutil.copy(path, "app/db/schema.sql.bak4")
path.write_text(src.replace(OLD, NEW, 1))
print("patched OK")
