-- Opportunities polled from grants.gov / SBIR.gov / NIH Guide
CREATE TABLE IF NOT EXISTS opportunity (
  id            TEXT PRIMARY KEY,        -- "sbir:HHS-2026-01-T02"
  source        TEXT NOT NULL,           -- grants_gov | sbir | nih_guide
  native_id     TEXT NOT NULL,           -- RFA-OD-25-008, topic number
  title         TEXT NOT NULL,
  agency        TEXT,
  branch        TEXT,
  program       TEXT,                    -- SBIR | STTR | grant
  phase         TEXT,
  status        TEXT,                    -- open | forecasted | closed
  release_date  TEXT,
  open_date     TEXT,
  close_date    TEXT,
  due_date      TEXT,
  url           TEXT,
  description   TEXT,                    -- full topic/solicitation text
  raw_json      TEXT,                    -- keep everything, parse later
  first_seen    TEXT NOT NULL,           -- freshness: "new since last poll"
  last_seen     TEXT NOT NULL,
  embedded      INTEGER DEFAULT 0,       -- has it been embedded yet?
  fetch_attempted TEXT,                    -- last description-fetch attempt
  became_posted   TEXT                     -- when forecasted -> posted
);

CREATE INDEX IF NOT EXISTS idx_opp_status  ON opportunity(status, due_date);
CREATE INDEX IF NOT EXISTS idx_opp_agency  ON opportunity(agency);
CREATE INDEX IF NOT EXISTS idx_opp_seen    ON opportunity(first_seen);

-- Hera's past proposals. The losses matter more than the wins.
CREATE TABLE IF NOT EXISTS proposal (
  id            TEXT PRIMARY KEY,
  title         TEXT NOT NULL,
  agency        TEXT,
  program       TEXT,
  year          INTEGER,
  outcome       TEXT NOT NULL,           -- won | lost | pending
  loss_reason   TEXT,                    -- free text, gold for fit reasoning
  text          TEXT,                    -- abstract / aims
  file          TEXT
);

-- Human-editable capability profile. The config seam.
CREATE TABLE IF NOT EXISTS profile (
  version       INTEGER PRIMARY KEY,
  client        TEXT NOT NULL DEFAULT 'hera',  -- which subject this describes
  content       TEXT NOT NULL,           -- markdown: capabilities, tech, non-fits
  created_at    TEXT NOT NULL,
  note          TEXT
);

-- The fit memo: what the agent produced and what it cost.
CREATE TABLE IF NOT EXISTS assessment (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  opportunity_id  TEXT NOT NULL REFERENCES opportunity(id),
  profile_version INTEGER REFERENCES profile(version),
  verdict         TEXT,                  -- pursue | maybe | skip
  confidence      REAL,
  rationale       TEXT,                  -- the "why", in prose
  evidence        TEXT,                  -- JSON: proposal ids / chunk ids cited
  days_to_due     INTEGER,               -- deadline risk at assessment time
  model           TEXT,
  tokens_used     INTEGER,               -- cost metering, from day one
  created_at      TEXT NOT NULL,
  UNIQUE(opportunity_id, profile_version)
);

-- Cached detail briefs. Expensive retrieval+LLM work, done once per opportunity.
CREATE TABLE IF NOT EXISTS brief (
  opportunity_id TEXT PRIMARY KEY REFERENCES opportunity(id),
  native_id      TEXT,
  status         TEXT,                    -- ok | not_published | error
  answers        TEXT,                    -- JSON: eligibility/budget/deadlines/scope
  url            TEXT,
  created_at     TEXT
);
