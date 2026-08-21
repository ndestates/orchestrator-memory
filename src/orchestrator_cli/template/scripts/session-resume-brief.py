#!/usr/bin/env python3
"""Cross-project session resume card — write on pause/EOD; read on resume or start.

Produces a portable handoff block for any orchestrator app.

Policy:
  - session-end and eod-shutdown MUST write a **rich** resume card.
  - **session-end** (mid-day) → next command is **/chain session-resume** (same day).
  - **eod-shutdown** (day closed) → next command is **/chain session-start** (new day).
  - Cards always: fetch → remote_last switch/pull → **then** load this card.
  - Always check+card after remote_last apply.
  - resume_first=yes only when card is fresh **and** Branch matches checkout.

Usage:
  python3 scripts/session-resume-brief.py write --summary "…" --done "item one" [--rich] --source session-end
  python3 scripts/session-resume-brief.py read [--compact]
  python3 scripts/session-resume-brief.py check [--json]   # session-start or session-resume

Exit 0 on success, 1 on hard failure, 2 when read/check finds no fresh card.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date, datetime, timezone

# Session-start skips when resume_first=yes (see references/resume-first.md in session-resume skill)
RESUME_FIRST_SKIP = [
    "todo_full_read",  # open items via situation + card
    "vision_read",
    "git_status_narrative",
    "compound_gate_lessons_dump",
]
# NEVER skip situation/vault/wiki awareness — session-start must know where we are
RESUME_FIRST_DEFER = ["changelog_init", "extra_codebase_docs"]
RESUME_FIRST_KEEP = [
    # Preferred one-shot (token-efficient): single model-visible artifact
    "session-spinup-bundle.py",  # → print spinup-latest.txt only
    # Or split:
    "session-context-envelope.py --write",
    "session-situation-brief.py --use-cache",  # where / in-flight / repetition
    # Depth only on demand (do not dump JSON after spinup):
    # session-vault-brief / session-wiki-brief
    # Fallback if envelope script missing on older deploys:
    "resume-branch.sh",
    "detect-project-runtime.sh --with-manifest-identity",
    "check-project-manifest.py",
    "session-security-sweep.sh",
    "vault_verify_one_liner",
]
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
_SCRIPTS_DIR = str(ROOT / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

_MANIFEST_MARKERS = (
    ".grok/project-manifest.yaml",
    ".github/project-manifest.yaml",
    ".claude/project-manifest.yaml",
    ".copilot/project-manifest.yaml",
)


def _run(cmd: list[str], cwd: Path | None = None) -> tuple[int, str, str]:
    try:
        r = subprocess.run(
            cmd, cwd=cwd or ROOT, capture_output=True, text=True, timeout=30
        )
        return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
    except Exception as exc:
        return 1, "", str(exc)


def project_root() -> Path:
    env = Path.cwd()
    for candidate in (env, *env.parents):
        for marker in _MANIFEST_MARKERS:
            if (candidate / marker).exists():
                return candidate
    return ROOT


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _find_manifest(root: Path) -> Path | None:
    for marker in _MANIFEST_MARKERS:
        path = root / marker
        if path.is_file():
            return path
    return None


def project_display_name(root: Path) -> str:
    manifest = _find_manifest(root)
    if manifest:
        text = _read_text(manifest)
        match = re.search(r'name:\s*["\']?([^"\'\n#]+)', text)
        if match:
            name = match.group(1).strip().strip('"').strip("'")
            if name and name != "Project Template":
                return name
    slug = root.name
    return slug.replace("-", " ").replace("_", " ").title()


def parse_porcelain_path(line: str) -> str:
    """Path from ``git status --porcelain`` (v1) or single-space / tab forms.

    Standard v1 is ``XY<space>PATH``. A missing extra space (``M path``) used
    ``line[3:]`` and truncated the first path character (``eports/...``).
    """
    raw = (line or "").rstrip("\n")
    if len(raw) < 2:
        return ""
    path = raw[2:].lstrip()
    if path.startswith('"') and path.endswith('"') and len(path) >= 2:
        path = path[1:-1]
    if " -> " in path:
        path = path.split(" -> ", 1)[-1].strip().strip('"')
    return path.strip()


def git_snapshot_rich(root: Path) -> dict:
    code_b, branch, _ = _run(["git", "branch", "--show-current"], cwd=root)
    code_s, status, _ = _run(["git", "status", "--porcelain"], cwd=root)
    dirty = bool(status) if code_s == 0 else True
    lines = status.splitlines() if status else []

    modified = untracked = deleted = staged = 0
    samples: list[str] = []
    for line in lines:
        if len(line) < 2:
            continue
        xy, path = line[:2], parse_porcelain_path(line)
        if not path:
            continue
        if xy == "??":
            untracked += 1
        elif "D" in xy:
            deleted += 1
        elif xy[0] != " ":
            staged += 1
        if xy[1] != " " and xy != "??":
            modified += 1
        if len(samples) < 6:
            samples.append(path)

    parts: list[str] = []
    if modified:
        parts.append(f"{modified} modified")
    if untracked:
        parts.append(f"{untracked} untracked")
    if deleted:
        parts.append(f"{deleted} deleted")
    if staged and not modified:
        parts.append(f"{staged} staged")
    dirty_detail = " + ".join(parts) if parts else "clean"
    if samples and dirty:
        sample_text = ", ".join(samples[:4])
        if len(samples) > 4:
            sample_text += ", …"
        dirty_detail += f" ({sample_text})"

    return {
        "branch": branch if code_b == 0 else "(unknown)",
        "dirty": dirty,
        "porcelain_lines": len(lines),
        "modified": modified,
        "untracked": untracked,
        "dirty_detail": dirty_detail,
        "porcelain_sample": samples[:12],
    }


def latest_todo(root: Path) -> Path | None:
    """Prefer newest dated TODO, including topic suffixes (*_foo_TODO.md).

    Primary pattern was YYYY-MM-DD_TODO.md only, which skipped named files like
    2026-07-18_freemium-license-publish_TODO.md and fell back to an older plain
    2026-07-17_TODO.md — leaving resume/envelope open-items stale after branch moves.
    """
    todo_dir = root / "TODO"
    if not todo_dir.is_dir():
        return None
    dated: list[tuple[date, str, Path]] = []
    for path in todo_dir.glob("*_TODO.md"):
        match = re.match(r"(\d{4}-\d{2}-\d{2})(?:_.+)?_TODO\.md$", path.name)
        if match:
            # Tie-break: longer topic name (topic file) before plain YYYY-MM-DD_TODO.md
            dated.append((date.fromisoformat(match.group(1)), path.name, path))
    if dated:
        # Prefer same-day plain YYYY-MM-DD_TODO.md (session spine) over topic files,
        # then longer topic names, then name.
        def _key(item: tuple) -> tuple:
            d, name, _path = item
            plain = 1 if re.match(r"\d{4}-\d{2}-\d{2}_TODO\.md$", name) else 0
            return (d, plain, len(name), name)

        dated.sort(key=_key, reverse=True)
        return dated[0][2]
    fallback = sorted(todo_dir.glob("*_TODO.md"), key=lambda p: p.name, reverse=True)
    return fallback[0] if fallback else None


def todo_date_label(path: Path | None) -> str:
    if not path:
        return date.today().isoformat()
    match = re.match(r"(\d{4}-\d{2}-\d{2})(?:_.+)?_TODO\.md$", path.name)
    return match.group(1) if match else date.today().isoformat()


def parse_open_todo_items(todo_text: str, limit: int = 6) -> list[str]:
    """Extract open checklist lines; prefer P0/P1 and Priority sections."""
    items: list[str] = []
    priority: list[str] = []
    in_open_section = False
    for line in todo_text.splitlines():
        stripped = line.strip()
        if re.match(r"^##\s+(Priority|Open|Still open|Next)", stripped, re.I):
            in_open_section = True
            continue
        if stripped.startswith("## ") and in_open_section:
            break
        match = re.match(r"^(?:-|\d+\.)\s+\[ \]\s+(.+)$", stripped)
        if not match:
            continue
        text = match.group(1).strip()
        if re.search(r"do not re-plan|done recently|carried forward", text, re.I):
            continue
        bucket = priority if re.search(r"\bP[01]\b", text, re.I) or in_open_section else items
        bucket.append(text)
    merged = priority + [i for i in items if i not in priority]
    return merged[:limit]


def detect_stack_signals(root: Path) -> str | None:
    if (root / "artisan").is_file() and (root / "composer.json").is_file():
        return "laravel"
    if (root / "manage.py").is_file():
        return "django"
    if (root / "go.mod").is_file():
        return "go"
    if (root / "package.json").is_file():
        pkg = _read_text(root / "package.json")
        if "next" in pkg.lower():
            return "nextjs"
    return None


def cache_caveat(root: Path) -> str | None:
    """Surface when spine cache likely describes template, not the real app."""
    manifest_path = _find_manifest(root)
    manifest_text = _read_text(manifest_path) if manifest_path else ""
    framework_match = re.search(r'framework:\s*["\']?(\w+)', manifest_text)
    manifest_fw = framework_match.group(1) if framework_match else "generic"
    detected = detect_stack_signals(root)

    arch = _read_text(root / "docs" / "codebase" / "ARCHITECTURE.md")
    stack_doc = _read_text(root / "docs" / "codebase" / "STACK.md")
    spine_mentions_template = bool(
        re.search(r"orchestration template|Project Template|template repo", arch + stack_doc, re.I)
    )

    caveats: list[str] = []
    if detected and manifest_fw == "generic":
        caveats.append(
            f"manifest still generic but repo looks like {detected} — customize project-manifest.yaml"
        )
    if spine_mentions_template and root.name != "orchestrator":
        caveats.append(
            "spine docs (STACK/ARCHITECTURE) still describe the template — run /read-codebase to rebuild against the real app"
        )

    checker = (
        ROOT / ".grok" / "skills" / "cache-freshness-check" / "scripts" / "cache_freshness_check.py"
    )
    if checker.is_file():
        code, stdout, _ = _run([sys.executable, str(checker), "--json"], cwd=root)
        if code == 0 and stdout:
            try:
                data = json.loads(stdout)
                status = data.get("status")
                if status in {"stale", "unknown"}:
                    rec = (data.get("recommendations") or ["/read-codebase"])[0]
                    caveats.append(f"cache {status} — {rec}")
                elif data.get("branch_drift"):
                    caveats.append(
                        "cache branch drift — "
                        + "; ".join(data.get("drift_reasons") or ["run /read-codebase on current branch"])
                    )
            except json.JSONDecodeError:
                pass

    if not caveats:
        return None
    return "; ".join(dict.fromkeys(caveats))


def parse_done_todo_items(todo_text: str, limit: int = 8) -> list[str]:
    """Checked checklist items for session context (recent done)."""
    items: list[str] = []
    for line in todo_text.splitlines():
        match = re.match(r"^(?:-|\d+\.)\s+\[x\]\s+(.+)$", line.strip(), re.I)
        if not match:
            continue
        text = match.group(1).strip()
        if re.search(r"do not re-plan|standing rules", text, re.I):
            continue
        items.append(text)
    return items[:limit]


def parse_next_items(todo_text: str, limit: int = 4) -> list[str]:
    """Carry-forward / Tomorrow / Next sections for resume context."""
    items: list[str] = []
    in_section = False
    for line in todo_text.splitlines():
        stripped = line.strip()
        if re.match(
            r"^##\s+(Carry-?forward|Tomorrow|Next session|Next|Resume)",
            stripped,
            re.I,
        ):
            in_section = True
            continue
        if stripped.startswith("## ") and in_section:
            break
        if not in_section:
            continue
        match = re.match(r"^(?:-|\d+\.)\s+(?:\[.\]\s+)?(.+)$", stripped)
        if match:
            items.append(match.group(1).strip())
    return items[:limit]


def git_head_oneline(root: Path) -> str:
    code, out, _ = _run(["git", "log", "-1", "--oneline"], cwd=root)
    return out if code == 0 else ""


def resume_branch_kv(root: Path, *, apply: bool = False) -> dict[str, str]:
    """Resume-branch facts. Reuse the session-start snapshot when fresh.

    Check/situation must not ``--apply``. Envelope apply writes the cache that
    later steps read so CTX.sync and SITUATION.sync cannot split.
    """
    from _engine.resume_branch_cache import load as _kv_load
    from _engine.resume_branch_cache import parse_kv as _kv_parse
    from _engine.resume_branch_cache import save as _kv_save

    if not apply:
        cached = _kv_load(root)
        if cached:
            return cached
    script = root / "scripts" / "resume-branch.sh"
    if not script.is_file():
        return {}
    cmd = ["bash", str(script)]
    if apply:
        cmd.append("--apply")
    code, out, _ = _run(cmd, cwd=root)
    if code != 0 or not out:
        return {}
    kv = _kv_parse(out)
    if kv:
        try:
            _kv_save(root, kv)
        except OSError:
            pass
    return kv


def remote_last_branch(root: Path) -> str:
    return (resume_branch_kv(root).get("remote_last") or "").strip()


def recent_commits(root: Path, n: int = 3) -> list[str]:
    code, out, _ = _run(["git", "log", f"-{n}", "--oneline"], cwd=root)
    if code != 0 or not out:
        return []
    return [ln.strip() for ln in out.splitlines() if ln.strip()][:n]


def workstream_primary(root: Path) -> str:
    reg = root / "reports" / "sessions" / "workstreams.yaml"
    if not reg.is_file():
        return ""
    text = _read_text(reg)
    m = re.search(r"(?m)^\s*primary:\s*[\"']?([^\s\"'#]+)", text)
    return (m.group(1).strip() if m else "") or ""


def recommended_chain_for_source(source: str = "", *, same_day: bool | None = None) -> str:
    """Which chain to run next after this card was written / when reading it.

    session-end (mid-day) → session-resume (same calendar day preferred).
    eod-shutdown / empty / stale day → session-start.
    """
    src = (source or "").strip().lower()
    if src in ("session-end", "session_end", "pause", "mid-day", "midday"):
        if same_day is False:
            return "session-start"
        return "session-resume"
    return "session-start"


def next_start_order_lines(
    *,
    remote_last: str = "",
    on_tip: bool | None = None,
    source: str = "",
) -> list[str]:
    """Mandatory chronological order for the next session open."""
    tip = remote_last or "remote_last"
    chain = recommended_chain_for_source(source)
    chain_slash = f"/chain {chain}"
    lines = [
        f"Next open: {chain_slash} (not the other one — "
        + (
            "same-day return after mid-day pause"
            if chain == "session-resume"
            else "new day / after eod-shutdown"
        )
        + ")",
    ]
    if chain == "session-resume":
        lines.extend(
            [
                "Order (mandatory): 1) fetch origin 2) checkout this card's Branch "
                "(the session you just paused) 3) THEN load this resume card "
                "4) security + lean work",
                "Do not switch to remote_last on session-resume — that is session-start only.",
            ]
        )
    else:
        lines.extend(
            [
                "Order (mandatory): 1) fetch origin 2) switch+pull remote_last "
                f"(team tip={tip}) when clean 3) THEN load this resume card "
                "4) security + lean work",
                "Do not resume from a stale local branch first — card is valid only after team tip is checked out.",
            ]
        )
    if chain == "session-resume":
        lines.append("Next open lands on this card's Branch (immediately prior session).")
    elif on_tip is False:
        lines.append(
            f"At write time this branch was NOT team tip — next open still lands on {tip}; "
            f"re-read card only if Branch matches after switch, else full /chain session-start."
        )
    elif on_tip is True:
        lines.append(f"At write time Branch matched team tip ({tip}).")
    return lines


def next_start_reminder_block(
    *,
    remote_last: str = "",
    on_tip: bool | None = None,
    source: str = "",
) -> str:
    """Human-facing reminder for session-end / eod-shutdown stdout."""
    chain = recommended_chain_for_source(source)
    title = (
        "=== NEXT: SESSION-RESUME (same day, remote_last first) ==="
        if chain == "session-resume"
        else "=== NEXT: SESSION-START (new day, remote_last first) ==="
    )
    lines = [
        title,
        "Chronological order — do not skip steps:",
        "  1. git fetch origin --prune",
        "  2. Auto-switch to remote_last (team tip) when tree clean + git pull --ff-only",
        "  3. Load resume card from THAT tip (not from pre-switch branch)",
        "  4. Security sweep → lean cache / work",
        f"  Team tip at write: {remote_last or '(unknown)'}",
    ]
    if on_tip is False:
        lines.append(
            "  Note: you ended off team tip — next open will still prefer remote_last; "
            "staying elsewhere requires commit/stash + explicit checkout and alignment context."
        )
    lines.append(
        f"  Command: /chain {chain}  (or: python3 scripts/session-context-envelope.py --write)"
    )
    if chain == "session-resume":
        lines.append(
            "  Do NOT run full /chain session-start for same-day return — use session-resume."
        )
        lines.append("  Use /chain session-start only after eod-shutdown or a new calendar day.")
    lines.append("=== end next-open reminder ===")
    return "\n".join(lines)


def parse_card_branch(card: str) -> str:
    """Extract Branch name from compact card text."""
    for line in (card or "").splitlines():
        m = re.match(r"^Branch:\s*([^\s(]+)", line.strip(), re.I)
        if m:
            return m.group(1).strip()
    return ""


def parse_card_source(card: str) -> str:
    """Extract Source: label from compact card text (session-end | eod-shutdown)."""
    for line in (card or "").splitlines():
        m = re.match(r"^Source:\s*(.+)$", line.strip(), re.I)
        if m:
            return m.group(1).strip()
    return ""


def parse_card_remote_last(card: str) -> str:
    """Team tip recorded on the card at write time (may be stale after fetch)."""
    for line in (card or "").splitlines():
        m = re.match(r"^Remote-last \(team tip\):\s*(\S+)", line.strip(), re.I)
        if m:
            return m.group(1).strip()
    return ""


def overlay_live_git_facts(
    card: str,
    *,
    remote_last: str = "",
    on_remote_last: str = "",
    align: str = "",
    sync_status: str = "",
    vs_summary: str = "",
) -> tuple[str, bool]:
    """Replace snapshot tip/align/sync on the card with live post-switch facts.

    Returns (card_for_briefing, tip_stale). Agents print ``card`` verbatim, so
    the overlay must live in that field — not only in parallel JSON keys.
    """
    card_tip = parse_card_remote_last(card)
    live = (remote_last or "").strip()
    stale = bool(card_tip and live and card_tip != live)
    if not card or not live:
        return card, stale
    on_tip = (on_remote_last or "").lower() == "yes"
    tip_flag = " · on_team_tip=yes" if on_tip else " · on_team_tip=no"
    live_remote_line = f"Remote-last (team tip): {live}{tip_flag}"
    live_note = (
        f"Live (after fetch): remote_last={live} on_tip="
        f"{'yes' if on_tip else 'no'} — card snapshot tip was {card_tip}"
    )
    out: list[str] = []
    for line in card.splitlines():
        stripped = line.strip()
        if re.match(r"^Remote-last \(team tip\):", stripped, re.I):
            out.append(live_remote_line)
            if stale:
                out.append(live_note)
            continue
        if re.match(r"^Vs team tip:", stripped, re.I):
            if on_tip:
                continue
            if vs_summary:
                out.append(f"Vs team tip: {vs_summary}")
            continue
        if sync_status and re.match(r"^Sync:", stripped, re.I):
            out.append(f"Sync: {sync_status}")
            continue
        if re.match(r"^Align:", stripped, re.I):
            if on_tip:
                continue
            if align:
                out.append(f"Align: {align}")
            continue
        if stripped.startswith("Team tip at write:"):
            out.append(
                f"Team tip at write: {card_tip or '(unknown)'} · live now: {live}"
            )
            continue
        if "next open still lands on" in stripped.lower() and on_tip:
            out.append(
                f"At write time snapshot tip was {card_tip}; "
                f"live team tip is {live} (already on it)."
            )
            continue
        if stripped.startswith("Order (mandatory):") and "team tip=" in stripped:
            out.append(
                "Order (mandatory): 1) fetch origin 2) switch+pull remote_last "
                f"(team tip={live}) when clean 3) THEN load this resume card "
                "4) security + lean work"
            )
            continue
        out.append(line)
    return "\n".join(out), stale


def template_version(root: Path) -> str:
    for rel in ("VERSION", "version"):
        path = root / rel
        if path.is_file():
            line = _read_text(path).strip().splitlines()
            if line:
                return line[0].strip()
    return ""


def behind_develop_count(root: Path) -> str:
    code, out, _ = _run(
        ["git", "rev-list", "--count", "HEAD..origin/develop"], cwd=root
    )
    if code == 0 and out.isdigit():
        return out
    return "?"


def format_card(
    *,
    project: str,
    when: str,
    branch: str,
    dirty_detail: str,
    dirty: bool,
    done: list[str],
    open_items: list[str],
    todo_label: str,
    cache_note: str | None,
    head: str = "",
    remote_last: str = "",
    version: str = "",
    behind_develop: str = "",
    next_items: list[str] | None = None,
    rich: bool = False,
    source: str = "",
    on_team_tip: bool | None = None,
    vs_remote_last: str = "",
    sync_status: str = "",
    recent: list[str] | None = None,
    workstream: str = "",
    align: str = "",
) -> str:
    lines = [
        f"{project} — resume {when}",
        f"Branch: {branch} ({'dirty: ' + dirty_detail if dirty else 'clean'}).",
    ]
    if rich or head:
        if head:
            lines.append(f"HEAD: {head}")
        if remote_last:
            tip_flag = ""
            if on_team_tip is True:
                tip_flag = " · on_team_tip=yes"
            elif on_team_tip is False:
                tip_flag = " · on_team_tip=no"
            lines.append(f"Remote-last (team tip): {remote_last}{tip_flag}")
        if vs_remote_last:
            lines.append(f"Vs team tip: {vs_remote_last}")
        if sync_status:
            lines.append(f"Sync: {sync_status}")
        if version or behind_develop:
            ver = version or "?"
            bd = behind_develop if behind_develop != "" else "?"
            lines.append(f"Ver: {ver} · behind_develop: {bd}")
        if workstream:
            lines.append(f"Workstream primary: {workstream}")
        if source:
            lines.append(f"Source: {source}")
        if recent:
            lines.append("Recent: " + " · ".join(recent[:3]))
    if done:
        numbered = "; ".join(f"({i}) {item}" for i, item in enumerate(done, 1))
        lines.append(f"Done this session: {numbered}")
    else:
        lines.append("Done this session: —")
    if open_items:
        open_text = "; ".join(open_items)
        lines.append(f"Open (from TODO {todo_label}): {open_text}")
    else:
        lines.append(f"Open (from TODO {todo_label}): —")
    next_items = next_items or []
    if next_items:
        lines.append("Next: " + "; ".join(next_items))
    if cache_note:
        lines.append(f"Cache caveat: {cache_note}")
    else:
        lines.append("Cache caveat: none — cache looks current for this branch.")
    chain = recommended_chain_for_source(source)
    # Always on rich cards; also on lean so session-end never omits the order
    if rich:
        lines.extend(
            next_start_order_lines(
                remote_last=remote_last, on_tip=on_team_tip, source=source
            )
        )
        if align and on_team_tip is False:
            lines.append(f"Align: {align}")
    else:
        lines.append(
            f"Next open: fetch → remote_last switch/pull → then card · /chain {chain}"
        )
    lines.append(f"Start with /chain {chain} (remote_last first).")
    return "\n".join(lines)


def write_card(
    root: Path,
    *,
    summary: str = "",
    done: list[str] | None = None,
    when: str | None = None,
    rich: bool = False,
    source: str = "",
) -> dict:
    today = date.today().isoformat()
    when = when or today
    snap = git_snapshot_rich(root)
    todo = latest_todo(root)
    todo_text = _read_text(todo) if todo else ""
    open_items = parse_open_todo_items(todo_text)
    next_items = parse_next_items(todo_text) if rich else []
    done_items = list(done or [])
    if summary and (not done_items or done_items == [""]):
        done_items = [summary] if summary else done_items
    elif summary and summary not in done_items:
        done_items.insert(0, summary)
    # Rich: fill done from checked TODO if caller gave little context
    if rich and len(done_items) < 2:
        for item in parse_done_todo_items(todo_text):
            if item not in done_items:
                done_items.append(item)
            if len(done_items) >= 6:
                break

    # Always collect branch/tip context for rich cards; light path still gets tip for reminder
    rb = resume_branch_kv(root)
    remote_last = (rb.get("remote_last") or "").strip()
    head = git_head_oneline(root) if rich else ""
    version = template_version(root) if rich else ""
    behind = behind_develop_count(root) if rich else ""
    on_team_tip: bool | None = None
    if remote_last:
        on_team_tip = snap["branch"] == remote_last
    vs_remote_last = ""
    sync_status = ""
    align = ""
    recent: list[str] = []
    ws = ""
    if rich:
        vb = rb.get("vs_remote_last_behind") or "0"
        va = rb.get("vs_remote_last_ahead") or "0"
        vs_remote_last = (
            rb.get("vs_remote_last_summary")
            or f"{vb} only-on-tip / {va} only-on-current"
        )
        sync_status = rb.get("sync_status") or ("dirty" if snap["dirty"] else "unknown")
        if snap["dirty"] and sync_status == "up_to_date":
            sync_status = "dirty"
        align = (rb.get("align_recommendations") or "").strip()
        recent = recent_commits(root, 3)
        ws = workstream_primary(root)

    project = project_display_name(root)
    cache_note = cache_caveat(root)
    source_label = source or ("eod-shutdown/session-end" if rich else "session")
    card = format_card(
        project=project,
        when=when,
        branch=snap["branch"],
        dirty_detail=snap["dirty_detail"],
        dirty=snap["dirty"],
        done=done_items,
        open_items=open_items,
        todo_label=todo_date_label(todo),
        cache_note=cache_note,
        head=head,
        remote_last=remote_last,
        version=version,
        behind_develop=behind,
        next_items=next_items,
        rich=rich,
        source=source_label,
        on_team_tip=on_team_tip,
        vs_remote_last=vs_remote_last,
        sync_status=sync_status,
        recent=recent,
        workstream=ws,
        align=align,
    )
    next_start_reminder = next_start_reminder_block(
        remote_last=remote_last, on_tip=on_team_tip, source=source_label
    )

    out_dir = root / "reports" / "sessions"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"resume-{when}.md"
    tip_cell = remote_last or "—"
    if on_team_tip is True:
        tip_cell += " (matched at write)"
    elif on_team_tip is False:
        tip_cell += " (this branch was off tip at write)"
    body = f"""# Session resume — {when}

{card}

## Details

| Field | Value |
|-------|--------|
| Project | {project} |
| Branch | `{snap['branch']}` |
| Dirty | {"yes" if snap['dirty'] else "no"} |
| WIP paths | {snap['porcelain_lines']} |
| HEAD | `{head or '—'}` |
| Remote-last (team tip) | `{tip_cell}` |
| On team tip at write | {"yes" if on_team_tip is True else ("no" if on_team_tip is False else "—")} |
| Sync | {sync_status or "—"} |
| Vs team tip | {vs_remote_last or "—"} |
| Version | {version or "—"} |
| behind_develop | {behind or "—"} |
| Workstream | {ws or "—"} |
| TODO | `{todo.name if todo else "—"}` |
| Source | {source_label} |
| Rich | {"yes" if rich else "no"} |

## Next open (remote_last first)

{next_start_reminder}

## Open (full)

"""
    for item in open_items:
        body += f"- [ ] {item}\n"
    if not open_items:
        body += "- (none)\n"
    body += "\n## Next / carry-forward\n\n"
    for item in next_items:
        body += f"- {item}\n"
    if not next_items:
        body += "- (none captured)\n"
    body += "\n## Done (captured)\n\n"
    for item in done_items:
        body += f"- [x] {item}\n"
    if not done_items:
        body += "- (none)\n"
    if recent:
        body += "\n## Recent commits\n\n"
        for c in recent:
            body += f"- `{c}`\n"
    body += "\n## WIP sample\n\n```\n"
    for line in snap.get("porcelain_sample") or []:
        body += line + "\n"
    if not snap.get("porcelain_sample"):
        body += "(clean)\n"
    body += "```\n"
    if align:
        body += f"\n## Align recommendations\n\n{align}\n"
    path.write_text(body, encoding="utf-8")
    alias = out_dir / "resume-latest.md"
    alias.write_text(body, encoding="utf-8")
    src_l = (source_label or "").strip().lower()
    if src_l in ("session-end", "session_end", "pause", "mid-day", "midday"):
        (out_dir / "resume-session-end-latest.md").write_text(body, encoding="utf-8")

    return {
        "status": "written",
        "path": str(path.relative_to(root)),
        "latest_path": str(alias.relative_to(root)),
        "card": card,
        "project": project,
        "branch": snap["branch"],
        "dirty": snap["dirty"],
        "rich": rich,
        "source": source_label,
        "todo": str(todo.relative_to(root)) if todo else None,
        "open": open_items,
        "next": next_items,
        "done": done_items,
        "remote_last": remote_last,
        "on_team_tip": on_team_tip,
        "next_start_reminder": next_start_reminder,
    }


def _resume_max_age_hours(root: Path) -> int:
    manifest = _find_manifest(root)
    if manifest:
        text = _read_text(manifest)
        match = re.search(r"resume_first_max_hours:\s*(\d+)", text)
        if match:
            return max(1, int(match.group(1)))
    return 24


def find_latest_resume(root: Path) -> Path | None:
    """Prefer dated ``resume-YYYY-MM-DD.md`` (newest date in the name).

    ``resume-latest.md`` is an alias rewritten on every ``write``. Sorting
    glob names reverse puts ``resume-latest.md`` *ahead* of dated cards
    (``l`` > ``2``), which made session-start load a stale alias. Never
    pick the alias when a dated card exists.
    """
    out_dir = root / "reports" / "sessions"
    if not out_dir.is_dir():
        return None
    dated: list[Path] = []
    for path in out_dir.glob("resume-*.md"):
        if path.name == "resume-latest.md":
            continue
        if re.match(r"resume-\d{4}-\d{2}-\d{2}\.md$", path.name):
            dated.append(path)
    if dated:
        dated.sort(key=lambda p: p.name, reverse=True)
        return dated[0]
    alias = out_dir / "resume-latest.md"
    if alias.is_file():
        return alias
    others = sorted(
        (p for p in out_dir.glob("resume-*.md") if p.name != "resume-latest.md"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return others[0] if others else None


def find_session_end_card(root: Path) -> Path | None:
    """Immediately prior mid-day pause — not overwritten by later eod-shutdown."""
    out_dir = root / "reports" / "sessions"
    dedicated = out_dir / "resume-session-end-latest.md"
    if dedicated.is_file():
        return dedicated
    path = find_latest_resume(root)
    if not path:
        return None
    text = _read_text(path)
    src = parse_card_source(_extract_card_text(text, kind="resume"))
    if src.lower() in ("session-end", "session_end", "pause", "mid-day", "midday"):
        return path
    return None


def find_latest_card(root: Path) -> Path | None:
    path = find_latest_resume(root)
    if path:
        return path
    out_dir = root / "reports" / "sessions"
    if not out_dir.is_dir():
        return None
    pauses = sorted(out_dir.glob("pause-*.md"), key=lambda p: p.name, reverse=True)
    return pauses[0] if pauses else None


def _card_date_from_path(path: Path) -> str | None:
    match = re.match(r"resume-(\d{4}-\d{2}-\d{2})(?:-session-end)?\.md$", path.name)
    return match.group(1) if match else None


def parse_card_date(card: str, path: Path | None = None) -> str | None:
    if path:
        from_name = _card_date_from_path(path)
        if from_name:
            return from_name
    for line in (card or "").splitlines():
        m = re.search(r"resume\s+(\d{4}-\d{2}-\d{2})", line, re.I)
        if m:
            return m.group(1)
    return None


def _card_age_hours(path: Path) -> float:
    try:
        mtime = path.stat().st_mtime
        return max(0.0, (datetime.now(timezone.utc).timestamp() - mtime) / 3600.0)
    except OSError:
        return 9999.0


def _extract_card_text(text: str, *, kind: str) -> str:
    if kind == "resume":
        card_lines: list[str] = []
        in_card = False
        for line in text.splitlines():
            if line.startswith("# Session resume"):
                in_card = True
                continue
            if in_card and line.startswith("## "):
                break
            if in_card and line.strip():
                card_lines.append(line)
        if card_lines:
            return "\n".join(card_lines).strip()
    return text.strip()


def read_card(
    root: Path, *, resume_only: bool = False, session_end: bool = False
) -> dict:
    if session_end:
        path = find_session_end_card(root)
    elif resume_only:
        path = find_latest_resume(root)
    else:
        path = find_latest_card(root)
    if not path:
        return {"status": "missing", "path": None, "card": None, "kind": None}
    kind = "resume" if path.name.startswith("resume-") else "pause"
    text = _read_text(path)
    card = _extract_card_text(text, kind=kind)
    card_date = parse_card_date(card, path) if kind == "resume" else None
    return {
        "status": "found",
        "path": str(path.relative_to(root)),
        "card": card,
        "kind": kind,
        "card_date": card_date,
        "age_hours": round(_card_age_hours(path), 2),
    }


def check_resume_first(root: Path, *, for_chain: str = "") -> dict:
    """Return resume-first gate for session-start **or** session-resume.

    session-start: after remote_last switch/pull.
    session-resume: after landing on the session-end card Branch (prior session).
    ``resume_first=yes`` only when fresh **and** card Branch matches checkout.
    """
    max_hours = _resume_max_age_hours(root)
    today = date.today().isoformat()
    want_resume = (for_chain or "").strip().lower() in (
        "session-resume",
        "resume",
    )
    card_info = (
        read_card(root, session_end=True) if want_resume else read_card(root, resume_only=True)
    )
    if want_resume and card_info.get("status") != "found":
        card_info = read_card(root, resume_only=True)
    code_b, branch_now, _ = _run(["git", "branch", "--show-current"], cwd=root)
    branch_now = branch_now if code_b == 0 else ""
    rb = resume_branch_kv(root)
    remote_last = (rb.get("remote_last") or "").strip()
    base = {
        "check": "always",
        "card_required_policy": "session-end and eod-shutdown must write resume-*.md",
        "max_age_hours": max_hours,
        "keep": list(RESUME_FIRST_KEEP),
        "branch_now": branch_now or None,
        "remote_last": remote_last or None,
        "startup_order": (
            "fetch → checkout prior session Branch → then card"
            if want_resume
            else "fetch → remote_last switch/pull → then card"
        ),
        "recommended_chain": "session-start",
        "card_source": None,
        "same_day": None,
    }
    if card_info["status"] != "found":
        return {
            **base,
            "resume_first": "no",
            "reason": "no resume-*.md card — write at session-end/eod; full session-start now",
            "max_cache_files": None,
            "skip": [],
            "defer": [],
            "card": None,
            "card_path": None,
            "card_date": None,
            "age_hours": None,
            "card_present": "no",
            "surface_card": "missing",
            "card_branch": None,
            "card_branch_match": "n/a",
        }

    card_text = card_info.get("card") or ""
    card_branch = parse_card_branch(card_text)
    card_source = parse_card_source(card_text)
    card_remote_last = parse_card_remote_last(card_text)
    branch_match = "yes" if (card_branch and branch_now and card_branch == branch_now) else (
        "unknown" if not card_branch or not branch_now else "no"
    )
    on_remote_last = "yes" if (remote_last and branch_now == remote_last) else "no"
    live_align = (rb.get("align_recommendations") or "").strip()
    live_sync = (rb.get("sync_status") or "").strip()
    live_vs = (rb.get("vs_remote_last_summary") or "").strip()
    card_date = card_info.get("card_date")
    age = float(card_info.get("age_hours") or 0)
    same_day = bool(card_date and card_date == today)
    fresh = same_day or (age <= max_hours)
    rec_chain = recommended_chain_for_source(card_source, same_day=same_day if card_date else None)
    pause_src = (card_source or "").strip().lower() in (
        "session-end",
        "session_end",
        "pause",
        "mid-day",
        "midday",
    )
    # Pause cards keep the prior session Branch. Overlay is for EOD vs live tip only.
    if pause_src and rec_chain == "session-resume":
        briefing_card, tip_stale = card_text, False
    else:
        briefing_card, tip_stale = overlay_live_git_facts(
            card_text,
            remote_last=remote_last,
            on_remote_last=on_remote_last,
            align=live_align,
            sync_status=live_sync,
            vs_summary=live_vs,
        )
    continue_target = (
        card_branch
        if (want_resume or rec_chain == "session-resume") and card_branch
        else (remote_last or branch_now)
    )

    common = {
        "card": briefing_card,
        "card_as_written": card_text if tip_stale else None,
        "card_path": card_info.get("path"),
        "card_date": card_date,
        "age_hours": age,
        "card_present": "yes",
        "surface_card": "always",
        "card_branch": card_branch or None,
        "card_branch_match": branch_match,
        "card_remote_last": card_remote_last or None,
        "card_tip_stale": "yes" if tip_stale else "no",
        "on_remote_last": on_remote_last,
        "align_recommendations": live_align or None,
        "card_source": card_source or None,
        "same_day": "yes" if same_day else "no",
        "recommended_chain": rec_chain,
        "prior_session_branch": card_branch or None,
        "continue_target": continue_target or None,
    }

    if not fresh:
        return {
            **base,
            **common,
            "recommended_chain": "session-start",
            "resume_first": "no",
            "reason": (
                f"stale card (date={card_date}, age={age}h > {max_hours}h) — "
                "full session-start; still surface card"
            ),
            "max_cache_files": None,
            "skip": [],
            "defer": [],
        }

    if branch_match == "no":
        if rec_chain == "session-resume" or want_resume:
            return {
                **base,
                **common,
                "recommended_chain": "session-resume",
                "resume_first": "no",
                "reason": (
                    f"not on prior session Branch={card_branch} "
                    f"(checkout={branch_now}) — run session-resume-land.py; "
                    "do not switch to remote_last"
                ),
                "max_cache_files": None,
                "skip": [],
                "defer": [],
            }
        return {
            **base,
            **common,
            "recommended_chain": "session-start",
            "resume_first": "no",
            "reason": (
                f"card Branch={card_branch} ≠ checkout={branch_now} "
                f"(remote_last={remote_last or 'none'}) — not team-tip handoff; "
                "full session-start; surface card + align recommendations"
            ),
            "max_cache_files": None,
            "skip": [],
            "defer": [],
        }

    cache_note = card_text
    needs_cache = "cache stale" in cache_note.lower() or "/read-codebase" in cache_note.lower()
    reason = (
        f"fresh resume card ({card_date or 'today'}, {age}h) branch_match={branch_match} "
        f"source={card_source or 'unknown'} → /chain {rec_chain}"
    )
    return {
        **base,
        **common,
        "resume_first": "yes",
        "reason": reason,
        "max_cache_files": 1 if needs_cache else 0,
        "skip": list(RESUME_FIRST_SKIP),
        "defer": list(RESUME_FIRST_DEFER),
        "cache_caveat_load": needs_cache,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)

    w = sub.add_parser("write", help="Write today's resume card (session-end / eod)")
    w.add_argument("--summary", default="", help="Session summary / primary done item")
    w.add_argument("--done", action="append", default=[], help="Done-this-session bullet (repeatable)")
    w.add_argument("--date", default="", help="Override date YYYY-MM-DD (default today)")
    w.add_argument(
        "--rich",
        action="store_true",
        help="Max context: HEAD, remote-last, ver, behind_develop, next, TODO done fill",
    )
    w.add_argument(
        "--source",
        default="",
        help="Writer label (session-end | eod-shutdown) stored in Details",
    )
    w.add_argument("--json", action="store_true")

    r = sub.add_parser("read", help="Read latest resume card for session-start")
    r.add_argument("--json", action="store_true")
    r.add_argument(
        "--compact",
        action="store_true",
        help="Card text only (no source footer — paste-friendly)",
    )

    c = sub.add_parser(
        "check",
        help="Always-run gate at session-start: surface card + resume_first lean flag",
    )
    c.add_argument("--json", action="store_true")
    c.add_argument(
        "--for",
        dest="for_chain",
        default="",
        help="session-resume | session-start (default: infer from card)",
    )

    args = ap.parse_args()
    root = project_root()

    if args.command == "write":
        when = args.date or date.today().isoformat()
        result = write_card(
            root,
            summary=args.summary.strip(),
            done=args.done,
            when=when,
            rich=bool(args.rich),
            source=(args.source or "").strip(),
        )
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(result["card"])
            print()
            print(f"Written: {result['path']}")
        return 0

    if args.command == "check":
        result = check_resume_first(root, for_chain=getattr(args, "for_chain", "") or "")
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"resume_first={result['resume_first']} ({result['reason']})")
            print(f"card_present={result.get('card_present', 'no')} surface_card={result.get('surface_card', 'n/a')}")
            if result.get("card"):
                print()
                print(result["card"])
            elif result.get("card_present") == "no":
                print()
                print("NO RESUME CARD — write one at session-end / eod-shutdown for next time.")
            if result["resume_first"] == "yes":
                print()
                print(f"max_cache_files={result['max_cache_files']}")
                print(f"skip={','.join(result['skip'])}")
        return 0

    result = read_card(root)
    if args.json:
        print(json.dumps(result, indent=2))
        return 0 if result["status"] == "found" else 2
    if result["status"] == "missing":
        print("No resume card found — run /chain session-end before leaving or start fresh.")
        return 2
    print(result["card"])
    if not getattr(args, "compact", False):
        print()
        print(f"Source: {result['path']} ({result['kind']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())