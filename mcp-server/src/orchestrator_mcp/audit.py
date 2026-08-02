"""Append-only audit logging for MCP tool invocations."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class AuditEntry:
    timestamp: str
    tool: str
    status: str
    duration_ms: int
    details: dict[str, Any]


class AuditLogger:
    def __init__(self, audit_dir: Path) -> None:
        self.audit_dir = audit_dir
        self.audit_dir.mkdir(parents=True, exist_ok=True)

    def _log_path(self) -> Path:
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return self.audit_dir / f"audit-{day}.jsonl"

    def record(
        self,
        tool: str,
        status: str,
        duration_ms: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        entry = AuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            tool=tool,
            status=status,
            duration_ms=duration_ms,
            details=details or {},
        )
        line = json.dumps(asdict(entry), separators=(",", ":"))
        with self._log_path().open("a", encoding="utf-8") as handle:
            handle.write(line + "\n")


def timed_audit(logger: AuditLogger, tool: str):
    """Context manager factory for timed audit records."""

    class _Timer:
        def __init__(self) -> None:
            self.start = 0.0
            self.details: dict[str, Any] = {}

        def __enter__(self):
            self.start = time.perf_counter()
            return self

        def __exit__(self, exc_type, exc, _tb):
            duration_ms = int((time.perf_counter() - self.start) * 1000)
            status = "error" if exc else "ok"
            if exc:
                self.details["error"] = str(exc)
            logger.record(tool, status, duration_ms, self.details)

    return _Timer()