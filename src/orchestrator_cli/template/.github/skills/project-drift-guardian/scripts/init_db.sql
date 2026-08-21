-- Optional local sqlite for requirements / drift log (generic; no product seeds).

CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL DEFAULT 'project',
  description TEXT,
  start_date TEXT,
  status TEXT DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS requirements (
  id INTEGER PRIMARY KEY,
  project_id INTEGER,
  title TEXT NOT NULL,
  description TEXT,
  priority INTEGER DEFAULT 3,
  status TEXT DEFAULT 'todo',
  branch TEXT,
  linked_to TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT
);

CREATE TABLE IF NOT EXISTS decisions (
  id INTEGER PRIMARY KEY,
  requirement_id INTEGER,
  decision TEXT,
  rationale TEXT,
  ai_reviewer TEXT,
  timestamp TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS branches (
  name TEXT PRIMARY KEY,
  purpose TEXT,
  status TEXT,
  linked_requirements TEXT,
  last_drift_check TEXT
);

CREATE TABLE IF NOT EXISTS drifts (
  id INTEGER PRIMARY KEY,
  requirement_id INTEGER,
  type TEXT,
  evidence TEXT,
  severity TEXT,
  detected_at TEXT DEFAULT (datetime('now')),
  resolved_at TEXT
);
