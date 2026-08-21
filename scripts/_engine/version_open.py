"""Version vs open-item check for session-start.

Two clocks:
- Product: VERSION file
- Work: Marketplace / orchestrator-memory VSIX lines in TODO/resume/open items
- Memory: VERSION= snapshots in the always-on store

Marketplace drift: warn + offer retarget (never auto-rewrite).
Memory drift: session-memory-brief re-seeds automatically.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

SEMVER_RE = re.compile(r"\b(\d+\.\d+\.\d+)\b")
MEMORY_VERSION_RE = re.compile(r"VERSION\s*=\s*v?(\d+\.\d+\.\d+)", re.I)
MARKETPLACE_HINT = re.compile(
    r"marketplace|orchestrator-memory|\.vsix",
    re.I,
)


def parse_semver(raw: str) -> tuple[int, int, int] | None:
    text = (raw or "").strip().lstrip("vV")
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)", text)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def cmp_semver(left: str, right: str) -> int | None:
    a = parse_semver(left)
    b = parse_semver(right)
    if a is None or b is None:
        return None
    if a < b:
        return -1
    if a > b:
        return 1
    return 0


def is_marketplace_line(line: str) -> bool:
    return bool(MARKETPLACE_HINT.search(line or ""))


def marketplace_mentions(texts: list[str]) -> list[dict[str, str]]:
    seen: list[dict[str, str]] = []
    for text in texts:
        if not text:
            continue
        for raw_line in str(text).splitlines() or [str(text)]:
            line = raw_line.strip()
            if not line or not is_marketplace_line(line):
                continue
            for ver in SEMVER_RE.findall(line):
                seen.append({"version": ver, "line": line[:160]})
    return seen


def check_marketplace_drift(product: str, texts: list[str]) -> dict[str, Any]:
    product = (product or "").strip()
    behind: list[dict[str, str]] = []
    for item in marketplace_mentions(texts):
        cmp = cmp_semver(item["version"], product)
        if cmp is not None and cmp < 0:
            behind.append(item)
    from_ver = behind[0]["version"] if behind else ""
    ask = ""
    if behind:
        ask = (
            f"Marketplace open is {from_ver}; product is {product}. "
            f"Retarget P1 to {product} (tag+Release+upload)? [retarget | keep]"
        )
    return {
        "drift": bool(behind),
        "from": from_ver,
        "to": product,
        "items": behind[:5],
        "ask": ask,
    }


def memory_versions(memories: list[dict[str, Any]]) -> list[str]:
    found: list[str] = []
    for mem in memories or []:
        blob = f"{mem.get('raw_text') or ''}\n{mem.get('summary') or ''}"
        for ver in MEMORY_VERSION_RE.findall(blob):
            found.append(ver)
    return found


def newest_version(versions: list[str]) -> str | None:
    parsed: list[tuple[tuple[int, int, int], str]] = []
    for ver in versions:
        key = parse_semver(ver)
        if key is not None:
            parsed.append((key, ver))
    if not parsed:
        return None
    parsed.sort()
    return parsed[-1][1]


def check_memory_drift(product: str, memories: list[dict[str, Any]]) -> dict[str, Any]:
    product = (product or "").strip()
    vers = memory_versions(memories)
    store = newest_version(vers)
    stale = False
    if store and product:
        cmp = cmp_semver(store, product)
        stale = cmp is not None and cmp < 0
    return {
        "stale": stale,
        "store_version": store or "",
        "file_version": product,
    }


def gather_open_texts(root: Path, open_items: list[str] | None = None) -> list[str]:
    texts: list[str] = list(open_items or [])
    todo_dir = root / "TODO"
    if todo_dir.is_dir():
        todos = sorted(todo_dir.glob("*_TODO.md"), reverse=True)
        if todos:
            try:
                texts.append(todos[0].read_text(encoding="utf-8", errors="replace"))
            except OSError:
                pass
    sessions = root / "reports" / "sessions"
    if sessions.is_dir():
        resumes = sorted(sessions.glob("resume-*.md"), reverse=True)
        if resumes:
            try:
                texts.append(resumes[0].read_text(encoding="utf-8", errors="replace")[:12000])
            except OSError:
                pass
    return texts


def apply_to_envelope(
    envelope: dict[str, Any],
    *,
    root: Path,
    product: str,
    open_items: list[str] | None = None,
) -> dict[str, Any]:
    check = check_marketplace_drift(product, gather_open_texts(root, open_items))
    envelope["ver_open_drift"] = "yes" if check["drift"] else "no"
    envelope["ver_open_from"] = check.get("from") or ""
    envelope["ver_open_to"] = product
    envelope["ver_open_ask"] = check.get("ask") or ""
    if check["drift"]:
        expand = envelope.setdefault("expand", [])
        if "ver_open" not in expand:
            expand.append("ver_open")
        envelope.setdefault("expand_payload", {})["ver_open"] = {
            "from": check.get("from"),
            "to": check.get("to"),
            "ask": check.get("ask"),
            "items": check.get("items") or [],
        }
    return check
