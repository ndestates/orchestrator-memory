#!/usr/bin/env python3
"""Lean multi-workstream registry CLI (session v2).

Nodes = workstreams; edges are operator focus transitions + artifact refs.
Does not spawn multi-session SDKs. Cache-first: registry is small YAML only.

Usage:
  python3 scripts/workstream.py list
  python3 scripts/workstream.py focus 1
  python3 scripts/workstream.py activate 2,3
  python3 scripts/workstream.py activate all
  python3 scripts/workstream.py hold 2 --ready
  python3 scripts/workstream.py note multi-stream-graphs --next "…"
  python3 scripts/workstream.py graph

Selectors (where an id is accepted):
  1          — 1-based index from list order
  1,2,3      — several numbers
  1-3        — inclusive range
  all        — every workstream
  slug-id    — stable string id (still works)
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "reports" / "sessions" / "workstreams.yaml"




def brief_dict(data: dict, *, max_show: int = 5) -> dict:
    """Lean session-start payload (≤150 tokens when formatted)."""
    streams = list(data.get("workstreams") or [])
    primary = data.get("primary") or ""
    active = [w for w in streams if w.get("status") == "active"]
    held = [w for w in streams if str(w.get("status") or "").startswith("held")]
    parked = [w for w in streams if w.get("status") == "parked"]
    show = []
    if primary:
        show.append(primary)
    for w in streams:
        i = w.get("id")
        if i and i not in show:
            show.append(i)
        if len(show) >= max_show:
            break
    return {
        "present": "yes",
        "primary": primary,
        "active_n": len(active),
        "held_n": len(held),
        "parked_n": len(parked),
        "total": len(streams),
        "show": show[:max_show],
        "updated": data.get("updated") or "",
    }


def format_brief_line(b: dict) -> str:
    if b.get("present") != "yes":
        return "ws present=no"
    show = ",".join(b.get("show") or [])
    return (
        f"ws primary={b.get('primary') or 'none'} "
        f"active={b.get('active_n', 0)} held={b.get('held_n', 0)} "
        f"parked={b.get('parked_n', 0)} show={show or 'none'}"
    )


def load_brief(path: Path | None = None, *, max_show: int = 5) -> dict:
    path = path or DEFAULT_REGISTRY
    if not path.is_file():
        return {"present": "no"}
    try:
        data = _load(path)
    except SystemExit:
        return {"present": "no"}
    return brief_dict(data, max_show=max_show)

def _load(path: Path) -> dict:
    if yaml is None:
        raise SystemExit("PyYAML required: pip install pyyaml (or use project venv)")
    if not path.is_file():
        raise SystemExit(f"registry missing: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict) or "workstreams" not in data:
        raise SystemExit("invalid registry: need top-level workstreams list")
    return data


def _save(path: Path, data: dict) -> None:
    data["updated"] = date.today().isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _streams(data: dict) -> list[dict]:
    """Ordered workstream list (1-based index for operators)."""
    return list(data.get("workstreams") or [])


def _index_map(data: dict) -> dict[int, str]:
    return {i: str(ws.get("id") or "") for i, ws in enumerate(_streams(data), start=1)}


def _find(data: dict, wid: str) -> dict:
    for ws in _streams(data):
        if ws.get("id") == wid:
            return ws
    raise SystemExit(f"unknown workstream id: {wid}")


def _resolve_spec(data: dict, spec: str) -> list[str]:
    """Resolve operator selector to one or more stable string ids.

    Accepts: slug id | 1 | 1,2,3 | 1-3 | all
    """
    raw = (spec or "").strip()
    if not raw:
        raise SystemExit("empty workstream selector")
    streams = _streams(data)
    if not streams:
        raise SystemExit("no workstreams in registry")
    idx_map = _index_map(data)
    n = len(streams)
    low = raw.lower()
    if low == "all":
        return [str(ws.get("id")) for ws in streams if ws.get("id")]

    # comma-separated tokens (mix of nums, ranges, slugs)
    tokens = [t.strip() for t in raw.split(",") if t.strip()]
    out: list[str] = []
    seen: set[str] = set()

    def add(wid: str) -> None:
        if wid and wid not in seen:
            seen.add(wid)
            out.append(wid)

    for tok in tokens:
        if tok.lower() == "all":
            for ws in streams:
                add(str(ws.get("id")))
            continue
        # range 1-3
        if re.fullmatch(r"\d+\s*-\s*\d+", tok):
            a_s, b_s = re.split(r"\s*-\s*", tok, maxsplit=1)
            a, b = int(a_s), int(b_s)
            if a > b:
                a, b = b, a
            for i in range(a, b + 1):
                if i not in idx_map:
                    raise SystemExit(f"index out of range: {i} (1-{n})")
                add(idx_map[i])
            continue
        # single number
        if re.fullmatch(r"\d+", tok):
            i = int(tok)
            if i not in idx_map:
                raise SystemExit(f"index out of range: {i} (1-{n})")
            add(idx_map[i])
            continue
        # slug id
        _find(data, tok)  # validate
        add(tok)
    if not out:
        raise SystemExit(f"no workstreams resolved from: {spec}")
    return out


def _resolve_one(data: dict, spec: str) -> str:
    ids = _resolve_spec(data, spec)
    if len(ids) != 1:
        raise SystemExit(
            f"selector must resolve to exactly one workstream (got {len(ids)}: {', '.join(ids)}). "
            "Use a single number or slug for focus/note."
        )
    return ids[0]


def cmd_list(data: dict) -> int:
    primary = data.get("primary") or ""
    streams = _streams(data)
    print(f"primary={primary}  updated={data.get('updated', '—')}  count={len(streams)}")
    print(f"{'#':>3}  {'id':<22} {'status':<12} {'branch':<44} next")
    print("-" * 110)
    for i, ws in enumerate(streams, start=1):
        mark = "*" if ws.get("id") == primary else " "
        nxt = (ws.get("next") or "")[:36]
        print(
            f"{mark}{i:>2}  {ws.get('id', ''):<22} {ws.get('status', ''):<12} "
            f"{(ws.get('branch') or '—'):<44} {nxt}"
        )
    print("hint: use numbers 1,2,3 or all — e.g. /multi-workstream activate 2,3  |  activate all")
    return 0


def cmd_focus(data: dict, path: Path, spec: str, apply: bool) -> int:
    wid = _resolve_one(data, spec)
    ws = _find(data, wid)
    data["primary"] = wid
    if ws.get("status") in {"parked", "held", "held_ready"} and apply:
        print(
            f"note: focusing {wid} while status={ws.get('status')} "
            "(not auto-unholding)",
            file=sys.stderr,
        )
    _save(path, data)
    # show number for operator
    num = next((i for i, s in enumerate(_streams(data), 1) if s.get("id") == wid), "?")
    print(f"primary → #{num} {wid}")
    branch = ws.get("branch") or ""
    if not apply:
        print(f"branch={branch} (pass --apply to checkout when clean)")
        return 0
    if not branch:
        print("no branch set; registry updated only")
        return 0
    dirty = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if dirty.stdout.strip():
        print("BLOCKED: dirty tree — commit/stash before --apply", file=sys.stderr)
        return 2
    cur = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    if cur == branch:
        print(f"already_on {branch}")
        return 0
    r = subprocess.run(
        ["git", "checkout", branch],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode != 0:
        print(r.stderr or r.stdout, file=sys.stderr)
        return r.returncode
    print(f"checked out {branch}")
    return 0


def cmd_hold(data: dict, path: Path, spec: str, ready: bool) -> int:
    ids = _resolve_spec(data, spec)
    status = "held_ready" if ready else "held"
    for wid in ids:
        ws = _find(data, wid)
        ws["status"] = status
        ws["updated"] = date.today().isoformat()
        if data.get("primary") == wid:
            for other in _streams(data):
                if other.get("id") != wid and other.get("status") == "active":
                    data["primary"] = other["id"]
                    break
        print(f"{wid} → {status}")
    _save(path, data)
    print(f"primary={data.get('primary')}  updated={len(ids)} workstream(s)")
    return 0


def cmd_set_status(data: dict, path: Path, spec: str, status: str) -> int:
    """activate | park | unhold — supports numbers, ranges, all."""
    allowed = {"active", "parked", "held", "held_ready", "done"}
    if status not in allowed:
        print(f"invalid status: {status}", file=sys.stderr)
        return 2
    ids = _resolve_spec(data, spec)
    for wid in ids:
        ws = _find(data, wid)
        prev = ws.get("status")
        ws["status"] = status
        ws["updated"] = date.today().isoformat()
        if status != "active" and data.get("primary") == wid:
            for other in _streams(data):
                if other.get("id") != wid and other.get("status") == "active":
                    data["primary"] = other["id"]
                    break
        if status == "active" and not data.get("primary"):
            data["primary"] = wid
        print(f"{wid}: {prev} → {status}")
    _save(path, data)
    print(f"primary={data.get('primary')}  updated={len(ids)} workstream(s)")
    return 0


def cmd_add(
    data: dict,
    path: Path,
    wid: str,
    *,
    title: str | None,
    branch: str | None,
    status: str,
    next_text: str | None,
) -> int:
    """Register a new workstream id."""
    for ws in data.get("workstreams") or []:
        if ws.get("id") == wid:
            print(f"already exists: {wid}", file=sys.stderr)
            return 2
    entry = {
        "id": wid,
        "title": title or wid,
        "status": status,
        "branch": branch or "",
        "todo_ref": "",
        "artifacts": [],
        "open": "",
        "next": next_text or "",
        "updated": date.today().isoformat(),
    }
    data.setdefault("workstreams", []).append(entry)
    if status == "active" and not data.get("primary"):
        data["primary"] = wid
    _save(path, data)
    print(f"added {wid} status={status} primary={data.get('primary')}")
    return 0


def cmd_note(data: dict, path: Path, spec: str, next_text: str | None, open_text: str | None) -> int:
    wid = _resolve_one(data, spec)
    ws = _find(data, wid)
    if next_text is not None:
        ws["next"] = next_text
    if open_text is not None:
        ws["open"] = open_text
    ws["updated"] = date.today().isoformat()
    _save(path, data)
    num = next((i for i, s in enumerate(_streams(data), 1) if s.get("id") == wid), "?")
    print(f"updated #{num} {wid}")
    return 0


def cmd_graph(data: dict) -> int:
    """Emit a tiny mermaid of primary + siblings (no vault IO)."""
    primary = data.get("primary")
    print("```mermaid")
    print("flowchart TD")
    print("  split[\"split: workstream registry\"]")
    for i, ws in enumerate(_streams(data), start=1):
        nid = "".join(c if c.isalnum() else "_" for c in str(ws.get("id")))
        label = f"#{i} {ws.get('id')}|{ws.get('status')}"
        print(f"  split --> {nid}[\"{label}\"]")
        if ws.get("id") == primary:
            print(f"  {nid} --> focus[\"primary focus #{i}\"]")
    print("  focus --> merge[\"session work (serial focus)\"]")
    print("```")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Multi-workstream registry CLI")
    p.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY,
        help="path to workstreams.yaml",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sel_help = "selector: 1 | 1,2,3 | 1-3 | all | slug-id"
    sub.add_parser("list", help="list workstreams (numbered)")
    f = sub.add_parser("focus", help="set primary workstream (single selector)")
    f.add_argument("id", help=sel_help + " (exactly one)")
    f.add_argument(
        "--apply",
        action="store_true",
        help="git checkout branch when working tree is clean",
    )
    h = sub.add_parser("hold", help="mark workstream(s) held")
    h.add_argument("id", help=sel_help)
    h.add_argument(
        "--ready",
        action="store_true",
        help="status held_ready instead of held",
    )
    a = sub.add_parser("activate", help="set status active (unhold/unpark); supports all")
    a.add_argument("id", help=sel_help)
    u = sub.add_parser("unhold", help="alias of activate (held → active)")
    u.add_argument("id", help=sel_help)
    pk = sub.add_parser("park", help="set status parked")
    pk.add_argument("id", help=sel_help)
    ad = sub.add_parser("add", help="register a new workstream id (slug, not a number)")
    ad.add_argument("id", help="new slug id e.g. docs-polish")
    ad.add_argument("--title", default=None)
    ad.add_argument("--branch", default=None)
    ad.add_argument(
        "--status",
        default="active",
        choices=["active", "held", "held_ready", "parked", "done"],
    )
    ad.add_argument("--next", dest="next_text", default=None)
    n = sub.add_parser("note", help="update open/next lines (single selector)")
    n.add_argument("id", help=sel_help + " (exactly one)")
    n.add_argument("--next", dest="next_text", default=None)
    n.add_argument("--open", dest="open_text", default=None)
    sub.add_parser("graph", help="print mermaid of registry topology")
    sub.add_parser("brief", help="one-line session-start workstream summary")
    sub.add_parser("diamond", help="Shape B safe multi-lane recommendation (no auto-exec)")
    sub.add_parser("recommend", help="alias of diamond")
    sub.add_parser("serial", help="serial plan: primary only (no parallel) — alternative to diamond")
    sub.add_parser("guard", help="integrity safeguards (no merges; keep project on course)")
    sub.add_parser(
        "prompts",
        help="operator prompts: merge-ready, open PR, WIP, frozen — what is going on",
    )
    sub.add_parser("ready", help="alias of prompts (merge/PR readiness)")
    sub.add_parser("status", help="alias of prompts")
    wt = sub.add_parser("worktree", help="git worktree isolation for a workstream")
    wt_sub = wt.add_subparsers(dest="wt_cmd", required=True)
    wt_sub.add_parser("list", help="list registered worktrees")
    wta = wt_sub.add_parser("add", help="create worktree for selector (single)")
    wta.add_argument("id", help=sel_help + " (exactly one)")
    wta.add_argument(
        "--force",
        action="store_true",
        help="allow worktree even if held/parked (still blocks protected branches)",
    )
    wtr = wt_sub.add_parser("remove", help="remove worktree for selector")
    wtr.add_argument("id", help=sel_help + " (exactly one)")
    wtr.add_argument("--force", action="store_true", help="git worktree remove --force")
    wt_sub.add_parser("status", help="JSON status of git worktrees + registry")

    args = p.parse_args(argv)
    data = _load(args.registry)

    if args.cmd == "list":
        return cmd_list(data)
    if args.cmd == "focus":
        return cmd_focus(data, args.registry, args.id, args.apply)
    if args.cmd == "hold":
        return cmd_hold(data, args.registry, args.id, args.ready)
    if args.cmd in ("activate", "unhold"):
        return cmd_set_status(data, args.registry, args.id, "active")
    if args.cmd == "park":
        return cmd_set_status(data, args.registry, args.id, "parked")
    if args.cmd == "add":
        return cmd_add(
            data,
            args.registry,
            args.id,
            title=args.title,
            branch=args.branch,
            status=args.status,
            next_text=args.next_text,
        )
    if args.cmd == "note":
        return cmd_note(data, args.registry, args.id, args.next_text, args.open_text)
    if args.cmd == "graph":
        return cmd_graph(data)
    if args.cmd == "brief":
        print(format_brief_line(brief_dict(data)))
        return 0
    if args.cmd in ("diamond", "recommend"):
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "workstream_recommend.py")],
            cwd=ROOT,
        )
        return r.returncode
    if args.cmd == "serial":
        primary = data.get("primary") or ""
        print("SERIAL plan (alternative to diamond) · preserve_focus=yes · auto_execute=no")
        print(f"primary={primary or 'none'}")
        print("lanes=1")
        print(f"  L0-primary: {primary or '—'} [serial_focus]")
        print("blocked: all other tracks until you focus them")
        print("next: work primary only · use worktree for isolation · PR to merge")
        print("SAFEGUARD: no parallel · no auto-merge to develop/staging/master")
        return 0
    if args.cmd == "guard":
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "workstream_guard.py")],
            cwd=ROOT,
        )
        return r.returncode
    if args.cmd in ("prompts", "ready", "status"):
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "workstream_prompts.py")],
            cwd=ROOT,
        )
        return r.returncode
    if args.cmd == "worktree":
        # import sibling module
        sys.path.insert(0, str(ROOT / "scripts"))
        import workstream_worktree as wtw  # noqa: WPS433

        if args.wt_cmd == "list":
            return wtw.cmd_list(data)
        if args.wt_cmd == "status":
            return wtw.cmd_status_json(data)
        if args.wt_cmd == "add":
            wid = _resolve_one(data, args.id)
            return wtw.cmd_add(data, args.registry, wid, force=args.force)
        if args.wt_cmd == "remove":
            wid = _resolve_one(data, args.id)
            return wtw.cmd_remove(data, args.registry, wid, force=args.force)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
