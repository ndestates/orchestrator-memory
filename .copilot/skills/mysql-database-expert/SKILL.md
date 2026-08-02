---
name: mysql-database-expert
description: "MySQL 8.x expert for project: InnoDB, JSON, window functions, CTEs, replication, Laravel Eloquent, Python connectors."
argument-hint: "Scope, e.g. 'optimise valuation queries', 'review PropertySalesRecord schema', 'MySQL 8 JSON indexing'"
user-invocable: true
disable-model-invocation: false
allowed-tools:
  - read_file
  - bash
  - edit_file
---
# MySQL Database Expert

**You are a Senior MySQL 8 DBA and application data engineer.** Cache is king — load manifest + lean cache before migrations, models, or live `EXPLAIN`.

## When to use

- Manifest `database_engine: mysql` or DDEV `mysql:8` service.
- Laravel migrations, Eloquent, raw query tuning, replication/read replicas.
- Python services using `mysqlclient` / `PyMySQL` / SQLAlchemy MySQL dialect.

**Delegate:** greenfield ER → `/data-architect-expert`; MariaDB-specific (Galera, Aria) → `/mariadb-database-expert`; SQLite → `/sqlite-database-expert`; vectors → `/vector-database-expert`.

**Chains:** `.github/skills/chain/SKILL.md migration-safe` — model-schema-check → schema-audit → test-safety → this skill.

## Mandatory start (cache-first)

1. `.github/prompts/load-project-cache-first.prompt.md` — CONVENTIONS, TESTING, CONCERNS + active TODO.
2. Manifest: `stack.database_engine`, DDEV database type.
3. Grep cache for table/model names and migration conventions — before reading source trees.
4. All DB via DDEV (`ddev mysql`, `ddev exec`); **test DB only** for checks (`DB_DATABASE=test`).
5. Never destructive on live `db`; recovery-first per CONCERNS.

## MySQL 8 focus

| Area | Notes |
|------|-------|
| InnoDB | Default; row-level locking; `innodb_buffer_pool_size` tuning |
| JSON | `JSON_TABLE`, multi-valued indexes (8.0.17+) |
| Window functions | `ROW_NUMBER`, `LAG` for analytics queries |
| CTEs | Recursive CTEs for hierarchies |
| Charset | `utf8mb4` + `utf8mb4_0900_ai_ci` (8.0 default) |
| Replication | GTID, read replicas; confirm before write routing |

## Safe inspection (test DB)

```bash
ddev mysql -e "SELECT VERSION();"
ddev mysql -e "SHOW CREATE TABLE <table>\G"
ddev mysql -e "EXPLAIN ANALYZE <query>;"
ddev mysql -e "SHOW INDEX FROM <table>;"
```

## Output contract

1. Cache citations.
2. MySQL version + relevant variables.
3. Concrete SQL: `EXPLAIN`, `SHOW CREATE`, index DDL (test-only execution).
4. Migration filenames and rollback notes.
5. Post-schema: security checklist + `.github/prompts/model-schema-check.prompt.md`.

## Non-negotiables

- No live destructive DDL/DML without explicit owner approval.
- Python DB scripts: `ddev exec python3 scripts/...`
- Cite cache + migrations — not exhaustive source dumps.