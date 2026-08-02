-- project-drift-guardian init (sqlite version; adapt for MySQL migration)
-- Requirements focus on e-sign + hosting + no-drift policy

CREATE TABLE IF NOT EXISTS projects (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL DEFAULT 'target-app',
  description TEXT,
  start_date TEXT,
  status TEXT DEFAULT 'active',
  hosting TEXT DEFAULT 'droplet-or-app-platform',
  do_project_id TEXT
);

CREATE TABLE IF NOT EXISTS requirements (
  id INTEGER PRIMARY KEY,
  project_id INTEGER,
  title TEXT NOT NULL,
  description TEXT,
  priority INTEGER DEFAULT 3,
  status TEXT DEFAULT 'todo',  -- todo, in_progress, done, blocked
  branch TEXT,
  linked_to TEXT,  -- e.g. 'Document model + migration', 'SigningService embed', 'DO App Platform CI', 'signature_hash audit'
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
  linked_requirements TEXT,  -- JSON or comma list
  last_drift_check TEXT
);

CREATE TABLE IF NOT EXISTS drifts (
  id INTEGER PRIMARY KEY,
  requirement_id INTEGER,
  type TEXT,  -- code, schema, container, infra, scope, deploy
  evidence TEXT,
  severity TEXT,  -- blocker, warning, info
  detected_at TEXT DEFAULT (datetime('now')),
  resolved_at TEXT
);

CREATE TABLE IF NOT EXISTS deploys (
  id INTEGER PRIMARY KEY,
  type TEXT,  -- droplet, app-platform
  commit TEXT,
  image_tag TEXT,
  db_migration_applied TEXT,
  drift_check_passed INTEGER,
  status TEXT,
  timestamp TEXT DEFAULT (datetime('now'))
);

-- Seed example requirements (expand per target app)
INSERT OR IGNORE INTO projects (name, description) VALUES ('target-app', 'Example app: core features, Filament admin, DDEV local, DO hosting, CI with no-drift gates, safe DB updates.');

INSERT OR IGNORE INTO requirements (title, description, priority, status, linked_to) VALUES
('Public canvas signature roundtrip', 'Unauthenticated /sign/{token} flow with HTML5 canvas, consent, name confirm, capture to PNG + hash, update signer/document status, thank-you with signed PDF download. Preserve roundtrip even on partial signers.', 1, 'in_progress', 'SigningController, SigningService, esign/ views, routes/web.php'),
('Signature immutability and audit', 'Every signature creates Signature record with sha256(image + time + signer_token) hash, ip_address, user_agent, meta. Never mutate after signed_at. Visible in Filament and queries.', 1, 'in_progress', 'Signature model + migration, SigningService capture, audit fields on Signer'),
('PDF embed with FPDI + fallback', 'On capture: prefer setasign/fpdi to copy pages and stamp sig (respect pos if available); fallback to dompdf confirmation PDF. Do not lose original content in scaffold. Update Document.path to signed artifact.', 1, 'in_progress', 'SigningService embedSignatureIntoDocument, composer requires, signed-confirmation view'),
('Multi-signer ordered requests + tokens', 'SignatureRequest with ordered Signers (signing_order, per-signer signer_token unique). Status machine (pending -> partially -> completed). Expiry guard. Seeder for demo.', 2, 'in_progress', 'SignatureRequest/Signer models/migrations, EsignDemoSeeder, Controller guards'),
('Filament admin for e-sign entities', 'Resources for Document (PDF upload), SignatureRequest, Signer. Status badges, relations, actions (e.g. send request). Currently scaffolding; populate forms/tables.', 2, 'todo', 'app/Filament/Resources/* + AdminPanelProvider'),
('DigitalOcean hosting (droplet and/or App Platform)', 'Support traditional droplet (Docker or native PHP/nginx, user-managed or simple doctl provision) AND App Platform (DOCR container, auto-deploy, limited token scopes, no broad DBaaS). CI builds hardened image, pushes, deploys. Pre/post drift checks.', 1, 'in_progress', 'digitalocean-*-deploy skill, .github/workflows, doctl usage, hardened Dockerfile'),
('CI deployment with gates', 'GitHub Actions: tests, model-schema-check + schema-audit, project-drift-guardian checks (code/scope/schema/container), security-audit, build+push to DOCR (or Docker), deploy (App or droplet), DB update if needed (prod-db-maintenance or safe guard), post-deploy eval + drift report. Block on any drift or failure.', 1, 'todo', 'github-expert, git-workflow-guardrails, this guardian, CI yaml to create'),
('Safe database updates / no data loss', 'Migrations only via ddev local first. Prod: always backup first (ddev export or doctl), pre schema/model check (model-schema-check + audit), apply (prod-db-maintenance style), post-verify (counts, sample signature hashes/integrity), /eval-maintenance-task. No destructive on live. Handle signature data as critical.', 1, 'in_progress', 'prod-db-maintenance, mysql-database-expert, schema-audit-agent, migrations, EsignDemoSeeder, backup/ dir'),
('Avoid drift at all costs (core policy)', 'Enforce branch-per-feature, requirements DB as truth, continuous + mandatory pre-deploy/pre-DB/pre-CI drift scans (this skill). Any drift (scope, schema vs model, image tag, code vs requirements, unapproved direct edits) blocks until remediated + logged. Post-deploy re-check + report.', 1, 'active', 'this skill + all guards, TODO discipline, cache (docs/codebase + INDEX)');

-- Example initial branch
INSERT OR IGNORE INTO branches (name, purpose, status, linked_requirements) VALUES
('feature/example-app-scaffold', 'Initial Laravel + Filament + DDEV + .grok setup + DO prep', 'done', '1,2,3,4,5,8,9');

-- Note: In real use, extend with app tables or keep separate sqlite for guardian isolation. Update via this skill's procedures.
