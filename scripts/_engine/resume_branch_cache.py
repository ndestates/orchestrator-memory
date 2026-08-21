"""One resume-branch snapshot per session-start.

session-start used to shell ``resume-branch.sh`` three times (envelope --apply,
check, situation). Each call re-fetches and re-reads porcelain, so CTX.sync and
SITUATION.sync could disagree, and a stale resume card still printed last
night's team tip next to live on_remote_last=yes.

Write the post-apply kv once; later consumers reuse it while fresh.
"""

from __future__ import annotations

import time
from pathlib import Path

REL = Path("reports") / "sessions" / "resume-branch-latest.kv"
MAX_AGE_S = 180


def parse_kv(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in (text or "").splitlines():
        if "=" not in line or line.startswith("#"):
            continue
        if line.startswith("mcp_start_options") or line.endswith("<<") or line.startswith(">>"):
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if key:
            out[key] = val.strip()
    return out


def load(root: Path, *, max_age: int = MAX_AGE_S) -> dict[str, str] | None:
    path = root / REL
    if not path.is_file():
        return None
    try:
        age = time.time() - path.stat().st_mtime
        if age > max_age:
            return None
        kv = parse_kv(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return None
    if not kv.get("remote_last") and not kv.get("current"):
        return None
    kv["_cache_hit"] = "yes"
    return kv


def save(root: Path, kv: dict[str, str]) -> Path:
    path = root / REL
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"{k}={v}"
        for k, v in kv.items()
        if v is not None and not str(k).startswith("_")
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
