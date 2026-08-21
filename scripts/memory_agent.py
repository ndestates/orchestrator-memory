#!/usr/bin/env python3
"""Always-on memory agent for orchestrator (Google always-on pattern).

Uses project model-route catalog (all OSS + free_cloud + host frontiers) and
project agent inventory for role routing. SQLite store under reports/memory/.

Usage:
  python3 scripts/memory_agent.py status
  python3 scripts/memory_agent.py models
  python3 scripts/memory_agent.py agents
  python3 scripts/memory_agent.py ingest --text "..." [--source s]
  python3 scripts/memory_agent.py ingest-file PATH
  python3 scripts/memory_agent.py query "what should I work on?"
  python3 scripts/memory_agent.py consolidate
  python3 scripts/memory_agent.py seed-situation
  python3 scripts/memory_agent.py watch [--interval 5]
  python3 scripts/memory_agent.py serve [--port 8888] [--consolidate-every 30]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from _engine import memory_agents as magents  # noqa: E402
from _engine import memory_llm as mllm  # noqa: E402
from _engine import memory_models as mmodels  # noqa: E402
from _engine import memory_store as mstore  # noqa: E402

TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".json",
    ".csv",
    ".log",
    ".xml",
    ".yaml",
    ".yml",
}


def db_path(root: Path) -> Path:
    return mstore.default_db_path(root)


def inbox_path(root: Path) -> Path:
    return root / "reports" / "memory" / "inbox"


def maybe_vault_emit(root: Path, summary: str, *, area: str = "learning") -> None:
    try:
        from _engine import vault as vault_mod
    except ImportError:
        return
    ledger = root / "reports" / "vault" / "events.jsonl"
    if not ledger.parent.is_dir():
        return
    try:
        event = vault_mod.emit_lesson_event(
            summary[:500],
            source="memory_agent",
            area=area,
        )
        vault_mod.append_event(ledger, event)
    except Exception:
        pass


def cmd_status(root: Path) -> int:
    path = db_path(root)
    stats = mstore.get_stats(path)
    models = mmodels.models_inventory_brief(root)
    agents = magents.agents_inventory_brief(root)
    out = {
        **stats,
        "models_catalog_total": models["catalog_total"],
        "agents_count": agents["count"],
        "ingest_model": models["picks"]["ingest"],
        "consolidate_model": models["picks"]["consolidate"],
        "query_model": models["picks"]["query"],
        "primary_agents": agents["role_picks"],
    }
    print(json.dumps(out, indent=2))
    return 0


def cmd_models(root: Path) -> int:
    print(json.dumps(mmodels.models_inventory_brief(root), indent=2))
    return 0


def cmd_agents(root: Path) -> int:
    print(json.dumps(magents.agents_inventory_brief(root), indent=2))
    return 0


def do_ingest(
    root: Path,
    text: str,
    source: str = "",
    *,
    dual_vault: bool = True,
) -> dict[str, Any]:
    agent = magents.pick_agent_for_role("ingest", root=root)
    model = mllm.resolve_backend("ingest", root)
    extracted = mllm.llm_ingest(text, source, model)
    result = mstore.store_memory(
        db_path(root),
        raw_text=extracted.get("raw_text") or text,
        summary=str(extracted.get("summary") or ""),
        entities=list(extracted.get("entities") or []),
        topics=list(extracted.get("topics") or []),
        importance=float(extracted.get("importance") or 0.5),
        source=source,
        agent_id=agent["primary"],
        model_id=str(model.get("id") or ""),
    )
    result["backend"] = extracted.get("backend")
    result["model_pick"] = {
        "id": model.get("id"),
        "status": model.get("status"),
        "backend": model.get("backend"),
    }
    result["agent"] = agent["primary"]
    if dual_vault:
        maybe_vault_emit(
            root,
            f"memory ingest #{result.get('memory_id')}: {result.get('summary')}",
            area="learning",
        )
    return result


def do_query(root: Path, question: str) -> dict[str, Any]:
    role = "query"
    ql = question.lower()
    if any(k in ql for k in ("security", "secret", "threat")):
        role = "query_security"
    elif any(k in ql for k in ("status", "where", "version", "branch")):
        role = "query_status"
    agent = magents.pick_agent_for_role("query", root=root, question=question)
    model = mllm.resolve_backend(role if role != "query_status" else "query_status", root)
    mems = mstore.read_memories(db_path(root), limit=50)["memories"]
    cons = mstore.read_consolidations(db_path(root), limit=10)["consolidations"]
    answer = mllm.llm_query(question, mems, cons, model)
    return {
        "question": question,
        "answer": answer,
        "agent": agent["primary"],
        "agent_role": agent["role"],
        "model_pick": {
            "id": model.get("id"),
            "status": model.get("status"),
            "backend": model.get("backend"),
        },
        "memory_count": len(mems),
        "consolidation_count": len(cons),
    }


def do_consolidate(root: Path, *, min_count: int = 2) -> dict[str, Any]:
    agent = magents.pick_agent_for_role("consolidate", root=root)
    model = mllm.resolve_backend("consolidate", root)
    mems = mstore.read_memories(
        db_path(root), limit=10, unconsolidated_only=True
    )["memories"]
    if len(mems) < min_count:
        return {
            "status": "skipped",
            "reason": f"need>={min_count} unconsolidated",
            "count": len(mems),
            "agent": agent["primary"],
            "model_pick": model,
        }
    extracted = mllm.llm_consolidate(mems, model)
    result = mstore.store_consolidation(
        db_path(root),
        source_ids=[int(x) for x in extracted.get("source_ids") or []],
        summary=str(extracted.get("summary") or ""),
        insight=str(extracted.get("insight") or ""),
        connections=list(extracted.get("connections") or []),
        agent_id=agent["primary"],
        model_id=str(model.get("id") or ""),
    )
    result["backend"] = extracted.get("backend")
    result["agent"] = agent["primary"]
    result["model_pick"] = {
        "id": model.get("id"),
        "status": model.get("status"),
        "backend": model.get("backend"),
    }
    maybe_vault_emit(
        root,
        f"memory consolidate: {result.get('insight') or result.get('summary')}",
        area="learning",
    )
    return result


def seed_situation(root: Path) -> dict[str, Any]:
    """Ingest live git + VERSION + latest TODO/resume into memory (truth snapshot)."""
    import subprocess

    parts: list[str] = []
    ver = (root / "VERSION").read_text(encoding="utf-8").strip() if (root / "VERSION").is_file() else "?"
    parts.append(f"VERSION={ver}")
    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=root, text=True, timeout=5
        ).strip()
        head = subprocess.check_output(
            ["git", "log", "-1", "--oneline"], cwd=root, text=True, timeout=5
        ).strip()
        parts.append(f"branch={branch}")
        parts.append(f"HEAD={head}")
    except Exception as exc:
        parts.append(f"git_error={exc}")

    todo_dir = root / "TODO"
    if todo_dir.is_dir():
        todos = sorted(todo_dir.glob("*_TODO.md"), reverse=True)
        if todos:
            text = todos[0].read_text(encoding="utf-8", errors="replace")[:3000]
            parts.append(f"TODO file={todos[0].name}\n{text}")

    resume_dir = root / "reports" / "sessions"
    resumes = sorted(resume_dir.glob("resume-*.md"), reverse=True) if resume_dir.is_dir() else []
    if resumes:
        parts.append(
            f"Resume={resumes[0].name}\n"
            + resumes[0].read_text(encoding="utf-8", errors="replace")[:2500]
        )

    blob = "\n\n".join(parts)
    return do_ingest(root, blob, source="seed-situation")


def ingest_file(root: Path, path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"status": "error", "error": f"not a file: {path}"}
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        # Multimodal deferred: store path pointer as memory for host agents
        note = (
            f"Non-text file queued for host multimodal agent: {path.name} "
            f"(type={path.suffix}). Use Grok/Claude/Gemini host for full extract."
        )
        return do_ingest(root, note, source=str(path.name))
    text = path.read_text(encoding="utf-8", errors="replace")[:10000]
    if not text.strip():
        return {"status": "empty", "path": str(path)}
    return do_ingest(root, text, source=path.name)


def watch_once(root: Path) -> list[dict[str, Any]]:
    folder = inbox_path(root)
    folder.mkdir(parents=True, exist_ok=True)
    results = []
    for f in sorted(folder.iterdir()):
        if f.name.startswith("."):
            continue
        key = str(f.resolve())
        if mstore.is_file_processed(db_path(root), key):
            continue
        if f.suffix.lower() not in TEXT_EXTENSIONS and f.suffix.lower() not in {
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".webp",
            ".pdf",
            ".mp3",
            ".wav",
            ".mp4",
        }:
            continue
        r = ingest_file(root, f)
        mstore.mark_file_processed(db_path(root), key)
        results.append(r)
    return results


def cmd_watch(root: Path, interval: int) -> int:
    print(f"Watching {inbox_path(root)} every {interval}s (Ctrl+C to stop)", flush=True)
    try:
        while True:
            results = watch_once(root)
            for r in results:
                print(json.dumps(r), flush=True)
            time.sleep(max(1, interval))
    except KeyboardInterrupt:
        print("stopped", flush=True)
        return 0


class _MemoryHandler(BaseHTTPRequestHandler):
    root: Path = ROOT

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _json(self, code: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/status":
            stats = mstore.get_stats(db_path(self.root))
            self._json(200, stats)
            return
        if parsed.path == "/memories":
            self._json(200, mstore.read_memories(db_path(self.root)))
            return
        if parsed.path == "/models":
            self._json(200, mmodels.models_inventory_brief(self.root))
            return
        if parsed.path == "/agents":
            self._json(200, magents.agents_inventory_brief(self.root))
            return
        if parsed.path == "/query":
            q = (parse_qs(parsed.query).get("q") or [""])[0].strip()
            if not q:
                self._json(400, {"error": "missing ?q="})
                return
            self._json(200, do_query(self.root, q))
            return
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        data = self._read_json()
        if parsed.path == "/ingest":
            text = str(data.get("text") or "").strip()
            if not text:
                self._json(400, {"error": "missing text"})
                return
            self._json(200, do_ingest(self.root, text, str(data.get("source") or "api")))
            return
        if parsed.path == "/consolidate":
            self._json(200, do_consolidate(self.root))
            return
        if parsed.path == "/delete":
            mid = data.get("memory_id")
            if mid is None:
                self._json(400, {"error": "missing memory_id"})
                return
            self._json(200, mstore.delete_memory(db_path(self.root), int(mid)))
            return
        if parsed.path == "/clear":
            self._json(200, mstore.clear_all(db_path(self.root)))
            return
        self._json(404, {"error": "not found"})


async def _serve_loops(root: Path, consolidate_every: int) -> None:
    while True:
        await asyncio.sleep(max(60, consolidate_every * 60))
        try:
            r = do_consolidate(root)
            print(json.dumps({"event": "consolidate", **r}), flush=True)
        except Exception as exc:
            print(json.dumps({"event": "consolidate_error", "error": str(exc)}), flush=True)


def cmd_serve(root: Path, port: int, consolidate_every: int, watch_interval: int) -> int:
    _MemoryHandler.root = root
    inbox_path(root).mkdir(parents=True, exist_ok=True)
    server = ThreadingHTTPServer(("127.0.0.1", port), _MemoryHandler)

    def watch_loop() -> None:
        while True:
            try:
                watch_once(root)
            except Exception as exc:
                print(f"watch error: {exc}", flush=True)
            time.sleep(max(1, watch_interval))

    import threading

    threading.Thread(target=watch_loop, daemon=True).start()

    def consolidate_loop() -> None:
        while True:
            time.sleep(max(60, consolidate_every * 60))
            try:
                print(json.dumps(do_consolidate(root)), flush=True)
            except Exception as exc:
                print(f"consolidate error: {exc}", flush=True)

    threading.Thread(target=consolidate_loop, daemon=True).start()

    print(
        json.dumps(
            {
                "status": "running",
                "api": f"http://127.0.0.1:{port}",
                "inbox": str(inbox_path(root)),
                "db": str(db_path(root)),
                "consolidate_every_min": consolidate_every,
            }
        ),
        flush=True,
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("stopped", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Orchestrator always-on memory agent")
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Project root (default: repo root)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status")
    sub.add_parser("models")
    sub.add_parser("agents")
    sub.add_parser("seed-situation")
    sub.add_parser("consolidate")

    p_ing = sub.add_parser("ingest")
    p_ing.add_argument("--text", required=True)
    p_ing.add_argument("--source", default="cli")

    p_file = sub.add_parser("ingest-file")
    p_file.add_argument("path", type=Path)

    p_q = sub.add_parser("query")
    p_q.add_argument("question")

    p_w = sub.add_parser("watch")
    p_w.add_argument("--interval", type=int, default=5)

    p_s = sub.add_parser("serve")
    p_s.add_argument("--port", type=int, default=8888)
    p_s.add_argument("--consolidate-every", type=int, default=30)
    p_s.add_argument("--watch-interval", type=int, default=5)

    p_list = sub.add_parser("list")
    p_list.add_argument("--limit", type=int, default=20)

    args = parser.parse_args(argv)
    root = args.root.resolve()

    if args.cmd == "status":
        return cmd_status(root)
    if args.cmd == "models":
        return cmd_models(root)
    if args.cmd == "agents":
        return cmd_agents(root)
    if args.cmd == "seed-situation":
        print(json.dumps(seed_situation(root), indent=2))
        return 0
    if args.cmd == "ingest":
        print(json.dumps(do_ingest(root, args.text, args.source), indent=2))
        return 0
    if args.cmd == "ingest-file":
        print(json.dumps(ingest_file(root, args.path), indent=2))
        return 0
    if args.cmd == "query":
        print(json.dumps(do_query(root, args.question), indent=2))
        return 0
    if args.cmd == "consolidate":
        print(json.dumps(do_consolidate(root), indent=2))
        return 0
    if args.cmd == "watch":
        return cmd_watch(root, args.interval)
    if args.cmd == "serve":
        return cmd_serve(root, args.port, args.consolidate_every, args.watch_interval)
    if args.cmd == "list":
        print(json.dumps(mstore.read_memories(db_path(root), limit=args.limit), indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
