"""Sync schema.sql with the live DB: brief table + two opportunity columns
that were added by hand and never checked in. A fresh clone currently breaks."""
import pathlib, shutil, sys

path = pathlib.Path("app/db/schema.sql")
src = path.read_text()

OLD_COLS = '''  embedded      INTEGER DEFAULT 0        -- has it been embedded yet?
);'''
NEW_COLS = '''  embedded      INTEGER DEFAULT 0,       -- has it been embedded yet?
  fetch_attempted TEXT,                    -- last description-fetch attempt
  became_posted   TEXT                     -- when forecasted -> posted
);'''

BRIEF = '''

-- Cached detail briefs. Expensive retrieval+LLM work, done once per opportunity.
CREATE TABLE IF NOT EXISTS brief (
  opportunity_id TEXT PRIMARY KEY REFERENCES opportunity(id),
  native_id      TEXT,
  status         TEXT,                    -- ok | not_published | error
  answers        TEXT,                    -- JSON: eligibility/budget/deadlines/scope
  url            TEXT,
  created_at     TEXT
);
'''

if "fetch_attempted" in src:
    sys.exit("already patched - no change made")
if OLD_COLS not in src:
    sys.exit("ANCHOR NOT FOUND (opportunity cols) - nothing written")

shutil.copy(path, "app/db/schema.sql.bak")
src = src.replace(OLD_COLS, NEW_COLS, 1).rstrip() + BRIEF
path.write_text(src)
print("patched OK (backup at app/db/schema.sql.bak)")
