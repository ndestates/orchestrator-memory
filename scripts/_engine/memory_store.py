"""Always-on memory SQLite store (Google always-on-memory pattern, orchestrator paths).

No vectors. Structured memories + consolidations + processed_files.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_REL = Path("reports/memory/memory.db")


def default_db_path(root: Path) -> Path:
    return root / DEFAULT_REL


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL DEFAULT '',
            raw_text TEXT NOT NULL,
            summary TEXT NOT NULL,
            entities TEXT NOT NULL DEFAULT '[]',
            topics TEXT NOT NULL DEFAULT '[]',
            connections TEXT NOT NULL DEFAULT '[]',
            importance REAL NOT NULL DEFAULT 0.5,
            agent_id TEXT NOT NULL DEFAULT '',
            model_id TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            consolidated INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS consolidations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_ids TEXT NOT NULL,
            summary TEXT NOT NULL,
            insight TEXT NOT NULL,
            agent_id TEXT NOT NULL DEFAULT '',
            model_id TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS processed_files (
            path TEXT PRIMARY KEY,
            processed_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )
    return conn


def store_memory(
    db_path: Path,
    *,
    raw_text: str,
    summary: str,
    entities: list[str],
    topics: list[str],
    importance: float,
    source: str = "",
    agent_id: str = "",
    model_id: str = "",
) -> dict[str, Any]:
    conn = connect(db_path)
    try:
        cur = conn.execute(
            """INSERT INTO memories
               (source, raw_text, summary, entities, topics, importance,
                agent_id, model_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                source,
                raw_text,
                summary,
                json.dumps(entities),
                json.dumps(topics),
                float(max(0.0, min(1.0, importance))),
                agent_id,
                model_id,
                utc_now(),
            ),
        )
        conn.commit()
        mid = int(cur.lastrowid or 0)
        return {
            "memory_id": mid,
            "status": "stored",
            "summary": summary,
            "agent_id": agent_id,
            "model_id": model_id,
        }
    finally:
        conn.close()


def _row_to_memory(r: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": r["id"],
        "source": r["source"],
        "raw_text": r["raw_text"] if "raw_text" in r.keys() else "",
        "summary": r["summary"],
        "entities": json.loads(r["entities"] or "[]"),
        "topics": json.loads(r["topics"] or "[]"),
        "connections": json.loads(r["connections"] or "[]"),
        "importance": r["importance"],
        "agent_id": r["agent_id"] if "agent_id" in r.keys() else "",
        "model_id": r["model_id"] if "model_id" in r.keys() else "",
        "created_at": r["created_at"],
        "consolidated": bool(r["consolidated"]),
    }


def read_memories(
    db_path: Path, *, limit: int = 50, unconsolidated_only: bool = False
) -> dict[str, Any]:
    conn = connect(db_path)
    try:
        if unconsolidated_only:
            rows = conn.execute(
                "SELECT * FROM memories WHERE consolidated = 0 "
                "ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM memories ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        memories = [_row_to_memory(r) for r in rows]
        return {"memories": memories, "count": len(memories)}
    finally:
        conn.close()


def store_consolidation(
    db_path: Path,
    *,
    source_ids: list[int],
    summary: str,
    insight: str,
    connections: list[dict[str, Any]],
    agent_id: str = "",
    model_id: str = "",
) -> dict[str, Any]:
    if not source_ids:
        return {"status": "noop", "reason": "no source_ids"}
    conn = connect(db_path)
    try:
        conn.execute(
            """INSERT INTO consolidations
               (source_ids, summary, insight, agent_id, model_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                json.dumps(source_ids),
                summary,
                insight,
                agent_id,
                model_id,
                utc_now(),
            ),
        )
        for conn_item in connections:
            from_id = conn_item.get("from_id")
            to_id = conn_item.get("to_id")
            rel = conn_item.get("relationship", "")
            if not from_id or not to_id:
                continue
            for mid in (int(from_id), int(to_id)):
                row = conn.execute(
                    "SELECT connections FROM memories WHERE id = ?", (mid,)
                ).fetchone()
                if not row:
                    continue
                existing = json.loads(row["connections"] or "[]")
                existing.append(
                    {
                        "linked_to": int(to_id) if mid == int(from_id) else int(from_id),
                        "relationship": rel,
                    }
                )
                conn.execute(
                    "UPDATE memories SET connections = ? WHERE id = ?",
                    (json.dumps(existing), mid),
                )
        placeholders = ",".join("?" * len(source_ids))
        conn.execute(
            f"UPDATE memories SET consolidated = 1 WHERE id IN ({placeholders})",
            [int(x) for x in source_ids],
        )
        conn.commit()
        return {
            "status": "consolidated",
            "memories_processed": len(source_ids),
            "insight": insight,
            "agent_id": agent_id,
            "model_id": model_id,
        }
    finally:
        conn.close()


def read_consolidations(db_path: Path, *, limit: int = 10) -> dict[str, Any]:
    conn = connect(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM consolidations ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        items = [
            {
                "id": r["id"],
                "summary": r["summary"],
                "insight": r["insight"],
                "source_ids": json.loads(r["source_ids"] or "[]"),
                "agent_id": r["agent_id"] if "agent_id" in r.keys() else "",
                "model_id": r["model_id"] if "model_id" in r.keys() else "",
                "created_at": r["created_at"],
            }
            for r in rows
        ]
        return {"consolidations": items, "count": len(items)}
    finally:
        conn.close()


def get_stats(db_path: Path) -> dict[str, Any]:
    conn = connect(db_path)
    try:
        total = conn.execute("SELECT COUNT(*) AS c FROM memories").fetchone()["c"]
        unconsolidated = conn.execute(
            "SELECT COUNT(*) AS c FROM memories WHERE consolidated = 0"
        ).fetchone()["c"]
        consolidations = conn.execute(
            "SELECT COUNT(*) AS c FROM consolidations"
        ).fetchone()["c"]
        return {
            "total_memories": total,
            "unconsolidated": unconsolidated,
            "consolidations": consolidations,
            "db_path": str(db_path),
        }
    finally:
        conn.close()


def delete_memory(db_path: Path, memory_id: int) -> dict[str, Any]:
    conn = connect(db_path)
    try:
        row = conn.execute(
            "SELECT 1 FROM memories WHERE id = ?", (memory_id,)
        ).fetchone()
        if not row:
            return {"status": "not_found", "memory_id": memory_id}
        conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.commit()
        return {"status": "deleted", "memory_id": memory_id}
    finally:
        conn.close()


def clear_all(db_path: Path) -> dict[str, Any]:
    conn = connect(db_path)
    try:
        mem_count = conn.execute("SELECT COUNT(*) AS c FROM memories").fetchone()["c"]
        conn.execute("DELETE FROM memories")
        conn.execute("DELETE FROM consolidations")
        conn.execute("DELETE FROM processed_files")
        conn.commit()
        return {"status": "cleared", "memories_deleted": mem_count}
    finally:
        conn.close()


def mark_file_processed(db_path: Path, path: str) -> None:
    conn = connect(db_path)
    try:
        conn.execute(
            "INSERT OR REPLACE INTO processed_files (path, processed_at) VALUES (?, ?)",
            (path, utc_now()),
        )
        conn.commit()
    finally:
        conn.close()


def is_file_processed(db_path: Path, path: str) -> bool:
    conn = connect(db_path)
    try:
        row = conn.execute(
            "SELECT 1 FROM processed_files WHERE path = ?", (path,)
        ).fetchone()
        return bool(row)
    finally:
        conn.close()
