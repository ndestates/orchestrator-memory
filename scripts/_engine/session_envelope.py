"""Session context envelope — fixed-size spin-up context for any AI platform.

Computes identity, runtime/MCP, branch sync, vault, security (optional), and
open/next from resume card or TODO — outside the model. Agents print compact
text only; expand sections only when status is non-green.

Token law: scripts mint context; models see status + pointers, not skill prose.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from _engine.manifest_identity import check_manifest_identity
from _engine.mcp_runtime_policy import session_mcp_brief
from _engine.platform_surface import platform_brief
from _engine.version_open import apply_to_envelope as apply_version_open

ENVELOPE_VERSION = 1
SESSIONS_REL = Path("reports") / "sessions"
LATEST_JSON = "context-latest.json"
LATEST_TXT = "context-latest.txt"
MAX_OPEN = 5
MAX_OPEN_CHARS = 72


def _workstream_brief(root: Path) -> dict[str, Any]:
    """Lean multi-workstream registry line for session-start (Phase 2)."""
    reg = root / SESSIONS_REL / "workstreams.yaml"
    if not reg.is_file():
        return {"present": "no"}
    try:
        # Prefer shared CLI module (same process) when importable
        import importlib.util

        ws_path = root / "scripts" / "workstream.py"
        if not ws_path.is_file():
            return {"present": "no"}
        spec = importlib.util.spec_from_file_location("orch_workstream", ws_path)
        if spec is None or spec.loader is None:
            return {"present": "no"}
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        brief = mod.load_brief(reg, max_show=5)
        brief["line"] = mod.format_brief_line(brief)
        return brief
    except Exception:
        return {"present": "no"}



def _run(cmd: list[str], cwd: Path, timeout: int = 45) -> tuple[int, str, str]:
    try:
        r = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()
    except Exception as exc:
        return 1, "", str(exc)


def _parse_kv_lines(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        if "=" not in line or line.startswith("mcp_start_options"):
            continue
        if line.endswith("<<") or line.startswith(">>"):
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if key:
            out[key] = val.strip()
    return out


def _short(s: str, n: int = MAX_OPEN_CHARS) -> str:
    s = re.sub(r"\s+", " ", (s or "").strip())
    if len(s) <= n:
        return s
    return s[: n - 1] + "…"


def _git_branch(root: Path) -> str:
    code, out, _ = _run(["git", "branch", "--show-current"], root)
    return out if code == 0 and out else "unknown"


def _resume_branch_info(
    root: Path, *, apply: bool = False, reuse_cache: bool = True
) -> dict[str, str]:
    """Call resume-branch.sh — pickup + sync; optional auto-switch to remote_last.

    Post-apply kv is cached so check + situation reuse the same snapshot
    (CTX.sync and SITUATION.sync must not split). session-resume must pass
    reuse_cache=False so a prior session-start apply does not steal the branch.
    """
    from _engine.resume_branch_cache import load as _kv_load
    from _engine.resume_branch_cache import save as _kv_save

    if reuse_cache and not apply:
        cached = _kv_load(root)
        if cached:
            return cached
    script = root / "scripts" / "resume-branch.sh"
    if not script.is_file():
        return {}
    cmd = ["bash", str(script)]
    if apply:
        cmd.append("--apply")
    code, out, _ = _run(cmd, root, timeout=90)
    if code != 0:
        return {}
    kv = _parse_kv_lines(out)
    if kv:
        try:
            _kv_save(root, kv)
        except OSError:
            pass
    return kv


def _pickup_fields(
    *,
    branch: str,
    resume: dict[str, Any],
    rb: dict[str, str],
    resume_session: bool = False,
) -> dict[str, Any]:
    """Where work continues.

    session-start: remote_last first; card after switch/pull.
    session-resume: immediately prior session Branch from the session-end card.
    """
    last = (rb.get("operator_last_branch") or "").strip()
    pointer = (rb.get("operator_pointer_found") or "no").lower()
    match = (rb.get("operator_resume_match") or "no").lower()
    switch = (rb.get("switch_offer") or "no").lower()
    remote_last = (rb.get("remote_last") or "").strip()
    resume_first = (resume.get("resume_first") or "no").lower()
    has_card = bool(resume.get("card") or resume.get("path"))
    switch_result = (rb.get("switch_result") or "none").strip()
    switch_applied = (rb.get("switch_applied") or "no").lower()
    switch_error = (rb.get("switch_error") or "").strip()
    on_remote_last = (rb.get("on_remote_last") or "").lower()
    if not on_remote_last:
        on_remote_last = "yes" if (remote_last and branch == remote_last) else "no"
    align = (rb.get("align_recommendations") or "").strip()
    vs_summary = (rb.get("vs_remote_last_summary") or "").strip()
    card_match = (resume.get("card_branch_match") or "").lower()

    card_branch = (resume.get("card_branch") or "").strip()
    if resume_session and card_branch:
        continue_target = card_branch
    else:
        # session-start: preferred target is remote_last (latest remote activity).
        continue_target = remote_last if remote_last else (last if pointer == "yes" else branch)
    vault_stale = bool(
        last and remote_last and last != remote_last and switch_applied != "yes"
    )
    last_worked_display = remote_last if remote_last else (last or branch)

    offer = "no"
    if switch_result == "blocked_dirty" and remote_last and remote_last != branch:
        offer = "yes"
    elif switch == "yes" and remote_last and remote_last != branch:
        offer = "yes"
    elif on_remote_last != "yes" and remote_last:
        offer = "yes"
    elif resume_first == "yes" and has_card:
        offer = "yes"
    elif card_match == "no":
        offer = "yes"
    elif pointer == "yes" and last and last != branch and switch_applied != "yes":
        offer = "yes"

    if switch_result == "blocked_dirty":
        # Only emitted when *leaving* current branch is blocked by real WIP
        ask = (
            f"Blocked auto-switch to remote_last=`{remote_last}` — real WIP on `{branch}`. "
            f"Commit/stash, then re-run session-start (must land on latest remote work branch). "
            f"[switch_result={switch_result}]"
        )
        if align:
            ask += f" Align: {align[:160]}"
    elif switch_result in ("switched", "pulled", "already_on") and switch_applied == "yes":
        ask = (
            f"On latest remote branch `{remote_last or branch}` "
            f"(switch_result={switch_result}; order=fetch→switch/pull→card). "
        )
        if (rb.get("working_tree") or "") == "dirty":
            ask += "Local dirty OK (already on tip). "
        if resume_first == "yes":
            ask += "Resume card fresh for this tip — continue? [continue | fresh]"
            if (resume.get("card_tip_stale") or "") == "yes":
                snap = resume.get("card_remote_last") or "prior tip"
                ask += (
                    f" Card snapshot tip was `{snap}`; live tip is "
                    f"`{remote_last}` (overlay applied — do not switch to the snapshot)."
                )
        elif card_match == "no":
            ask += (
                f"Card branch mismatch (card={resume.get('card_branch')}) — "
                "full start; card is not team-tip handoff."
            )
        else:
            ask += "Surface check+card; full start if card stale."
    elif switch_result in (
        "checkout_failed",
        "pull_failed",
        "no_remote_last",
        "switched_pull_failed",
    ):
        ask = (
            f"Auto-switch failed ({switch_result}"
            + (f": {switch_error}" if switch_error else "")
            + f"). Current `{branch}`; target `{continue_target or remote_last}`."
        )
    elif on_remote_last != "yes" and remote_last:
        ask = (
            f"Off team tip: current=`{branch}` remote_last=`{remote_last}` "
            f"({vs_summary or 'see align'}). "
            f"Prefer checkout `{remote_last}` for team continuity. "
            f"[switch={remote_last} | stay={branch}+align]"
        )
        if align:
            ask += f" · {align[:120]}"
    elif resume_first == "yes":
        ask = (
            f"Resume card fresh on `{branch}` — continue this work? "
            f"[continue | fresh] — open/next already on envelope"
        )
    else:
        ask = (
            f"On `{branch}` remote_last={remote_last or 'none'} "
            f"switch_result={switch_result or 'none'} — check+card always required"
        )

    return {
        "pickup_offer": offer,
        "operator_last_branch": last_worked_display or "none",
        "vault_last_branch": last or "none",
        "vault_stale": "yes" if vault_stale else "no",
        "operator_pointer_found": pointer,
        "operator_resume_match": match,
        "remote_last": remote_last or "none",
        "on_remote_last": on_remote_last,
        "switch_offer": switch,
        "switch_applied": switch_applied,
        "switch_result": switch_result or "none",
        "switch_error": switch_error,
        "continue_target": continue_target or branch,
        "pickup_ask": ask,
        "auto_switch_policy": "fetch_then_remote_last_then_card",
        "align_recommendations": align,
        "vs_remote_last_summary": vs_summary,
        "startup_order": "fetch → remote_last switch/pull → then card",
        "card_branch_match": resume.get("card_branch_match") or "n/a",
        "card_branch": resume.get("card_branch"),
        "card_tip_stale": resume.get("card_tip_stale") or "no",
        "card_remote_last": resume.get("card_remote_last"),
    }


def _detect_runtime(root: Path) -> dict[str, str]:
    code, out, _ = _run(
        ["bash", "scripts/detect-project-runtime.sh", "--with-manifest-identity"],
        root,
        timeout=90,
    )
    if code != 0:
        return {}
    return _parse_kv_lines(out)


def _situation_brief(root: Path) -> dict[str, Any]:
    """Where we are / in flight / repetition gate (required for session understanding)."""
    script = root / "scripts" / "session-situation-brief.py"
    if not script.is_file():
        return {"status": "missing"}
    # Full rebuild at session-start; chain step may --use-cache afterward
    code, out, _ = _run(
        ["python3", str(script), "--json", "--write"], root, timeout=120
    )
    if code != 0 or not out:
        return {"status": "fail"}
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return {"status": "fail"}
    return data


def _emit_session_startup_vault(root: Path, env: dict[str, Any]) -> str:
    """Best-effort vault record of remote_last-first startup (double-check trail)."""
    try:
        try:
            from scripts._engine import vault as vmod
        except ImportError:
            from _engine import vault as vmod  # type: ignore
        ledger = root / "reports" / "vault" / "events.jsonl"
        if not ledger.parent.is_dir():
            return "skip"
        ev = vmod.emit_session_startup(
            branch=str(env.get("branch") or ""),
            remote_last=str(env.get("remote_last") or "") or None,
            switch_result=str(env.get("switch_result") or "") or None,
            switch_applied=str(env.get("switch_applied") or "") or None,
            on_remote_last=str(env.get("on_remote_last") or "") or None,
            resume_first=str(env.get("resume_first") or "") or None,
            card_path=str((env.get("ptrs") or {}).get("resume") or env.get("resume_path") or "")
            or None,
            card_branch=str(env.get("card_branch") or "") or None,
            card_branch_match=str(env.get("card_branch_match") or "") or None,
            align_recommendations=str(env.get("align_recommendations") or "") or None,
            phase="session-start",
            source="session-start",
            ledger_path=ledger,
            root=root,
            extra={
                "sync": env.get("sync"),
                "behind_develop": env.get("behind_develop"),
                "template_version": env.get("template_version"),
            },
        )
        return (ev.get("content_hash") or "")[:16] or "ok"
    except Exception:
        return "fail"


def _vault_ok(root: Path) -> str:
    script = root / "scripts" / "session-vault-brief.py"
    if not script.is_file():
        return "n/a"
    code, out, _ = _run(["python3", str(script), "--json"], root, timeout=30)
    if code == 0 and out:
        try:
            data = json.loads(out)
            if data.get("verify_ok") is True:
                return "OK"
            if data.get("status") == "ok" and not data.get("issues"):
                return "OK"
            if data.get("status") == "ok":
                return "OK"
            if data.get("verify_ok") is False:
                return "FAIL"
        except json.JSONDecodeError:
            pass
    code2, out2, _ = _run(["python3", str(script)], root, timeout=30)
    if "ledger=OK" in out2 or "Vault: ledger=OK" in out2:
        return "OK"
    return "unknown"


def _security_status(root: Path) -> tuple[str, str | None]:
    """Use today's sweep report if present; do not re-run (token + time)."""
    sec_dir = root / "reports" / "security"
    if not sec_dir.is_dir():
        return "n/a", None
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = sec_dir / f"session-sweep-{today}.md"
    if not path.is_file():
        # latest session-sweep-*
        candidates = sorted(sec_dir.glob("session-sweep-*.md"), reverse=True)
        path = candidates[0] if candidates else None
    if path is None or not path.is_file():
        return "n/a", None
    try:
        text = path.read_text(encoding="utf-8", errors="replace")[:2000]
    except OSError:
        return "n/a", None
    m = re.search(
        r"(?:\*\*)?Overall(?:\*\*)?\s*[|\s:]+(?:\*\*)?(PASS|WARN|FAIL)",
        text,
        re.I,
    )
    if not m:
        m = re.search(r"overall[=:\s]+(PASS|WARN|FAIL)", text, re.I)
    status = m.group(1).upper() if m else "unknown"
    rel = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
    return status, rel


def _resume_gate(root: Path, *, for_chain: str = "") -> dict[str, Any]:
    script = root / "scripts" / "session-resume-brief.py"
    if not script.is_file():
        return {"resume_first": "no", "card": None, "open": [], "path": None}
    cmd = ["python3", str(script), "check", "--json"]
    if for_chain:
        cmd.extend(["--for", for_chain])
    code, out, _ = _run(cmd, root, timeout=30)
    if code != 0 or not out:
        return {"resume_first": "no", "card": None, "open": [], "path": None}
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return {"resume_first": "no", "card": None, "open": [], "path": None}
    open_items = _open_from_card(data.get("card") or "")
    return {
        "resume_first": data.get("resume_first") or "no",
        "card": data.get("card"),
        "open": open_items,
        "path": data.get("card_path"),
        "max_cache_files": data.get("max_cache_files"),
        "reason": data.get("reason"),
        "card_branch": data.get("card_branch"),
        "card_branch_match": data.get("card_branch_match"),
        "card_remote_last": data.get("card_remote_last"),
        "card_tip_stale": data.get("card_tip_stale") or "no",
        "on_remote_last": data.get("on_remote_last"),
        "align_recommendations": data.get("align_recommendations"),
        "startup_order": data.get("startup_order"),
    }


def _open_from_card(card: str) -> list[str]:
    if not card:
        return []
    # Prefer "Open (from TODO …):" line
    for line in card.splitlines():
        if line.lower().startswith("open"):
            body = line.split(":", 1)[-1].strip()
            parts = re.split(r";\s*|\s+\*\*|\s+\| ", body)
            items = []
            for p in parts:
                p = re.sub(r"\*+", "", p).strip(" -•")
                if len(p) < 8:
                    continue
                # strip leading verbs noise lightly
                items.append(_short(p))
                if len(items) >= MAX_OPEN:
                    break
            return items
    return []


def _open_from_todo(root: Path) -> list[str]:
    todo_dir = root / "TODO"
    if not todo_dir.is_dir():
        return []
    files = sorted(todo_dir.glob("*_TODO.md"), reverse=True)
    if not files:
        return []
    try:
        text = files[0].read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    items: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^\s*(?:[-*]|\d+\.)\s+\[\s*\]\s+(.+)", line)
        if not m:
            continue
        items.append(_short(m.group(1)))
        if len(items) >= MAX_OPEN:
            break
    return items


def _latest_todo_path(root: Path) -> str | None:
    todo_dir = root / "TODO"
    if not todo_dir.is_dir():
        return None
    files = sorted(todo_dir.glob("*_TODO.md"), reverse=True)
    if not files:
        return None
    return str(files[0].relative_to(root))


def _mcp_from_runtime(root: Path, runtime_kv: dict[str, str]) -> dict[str, Any]:
    runtime = runtime_kv.get("runtime") or "local"
    has_ddev = runtime_kv.get("has_ddev") == "1"
    has_compose = runtime_kv.get("has_compose") == "1"
    has_mcp = runtime_kv.get("has_mcp_server") == "1"
    mcp_ready = runtime_kv.get("mcp_ready") or "no"
    brief = session_mcp_brief(
        root=root,
        runtime=runtime,
        has_ddev=has_ddev,
        has_compose=has_compose,
        has_mcp_server=has_mcp,
        mcp_ready=mcp_ready,
        ddev_running=runtime_kv.get("ddev_running") or "n/a",
        compose_running=runtime_kv.get("compose_running") or "n/a",
        mcp_note=runtime_kv.get("mcp_note") or "",
    )
    return brief


def _template_version(root: Path) -> str:
    for rel in ("VERSION", "scripts/orchestrator-template-version"):
        path = root / rel
        if path.is_file():
            try:
                return path.read_text(encoding="utf-8").strip().splitlines()[0].strip()
            except OSError:
                continue
    return "unknown"


def _orchestrator_update(root: Path) -> dict[str, Any]:
    """Automatic install/upgrade check for session-start (app users).

    Preferred path: session-orchestrator-check --auto-apply (GitHub when newer).
    Upgrade skips customized files and preserves project-manifest; dirty WIP is
    stashed then restored. Template source never auto-applies.
    """
    out: dict[str, Any] = {
        "orch_kind": "unknown",
        "orch_installed": None,
        "orch_available": None,
        "orch_offer": "no",
        "orch_message": "",
        "orch_preview": None,
        "orch_apply": None,
        "orch_auto_applied": "no",
    }
    try:
        from _engine.manifest_identity import is_orchestrator_source_repo

        if is_orchestrator_source_repo(root):
            out["orch_kind"] = "template_source"
            out["orch_available"] = _template_version(root)
            out["orch_message"] = "orchestrator template source — app lock N/A"
            return out
    except Exception:
        pass
    script = root / "scripts" / "session-orchestrator-check.py"
    if not script.is_file():
        out["orch_kind"] = "missing_script"
        out["orch_message"] = "session-orchestrator-check.py missing — upgrade template ≥1.4.2"
        return out
    # Auto-apply first (apps); long timeout for GitHub materialize + deploy
    code, stdout, _ = _run(
        [sys.executable, str(script), "--auto-apply", "--json"],
        root,
        timeout=600,
    )
    if (code != 0 or not stdout) and sys.executable != "python3":
        code, stdout, _ = _run(
            ["python3", str(script), "--auto-apply", "--json"],
            root,
            timeout=600,
        )
    if not stdout:
        out["orch_kind"] = "check_failed"
        return out
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        out["orch_kind"] = "check_failed"
        return out
    kind = str(data.get("kind") or "unknown")
    out["orch_kind"] = kind
    out["orch_installed"] = data.get("installed")
    out["orch_available"] = data.get("available")
    out["orch_offer"] = "yes" if data.get("offer") else "no"
    out["orch_message"] = _short(str(data.get("message") or ""), 200)
    out["orch_preview"] = data.get("preview_action")
    out["orch_apply"] = data.get("apply_action") or data.get("action")
    out["orch_auto_applied"] = "yes" if data.get("auto_applied") else "no"
    out["orch_auto_result"] = data.get("auto_apply_result")
    return out


def _integration_lag(root: Path) -> dict[str, str]:
    """Warn when feature work is not based on origin/develop (version/base drift)."""
    out: dict[str, str] = {
        "integration": "develop",
        "behind_develop": "?",
        "version_note": "",
    }
    code, behind, _ = _run(
        ["git", "rev-list", "--count", "HEAD..origin/develop"], root, timeout=20
    )
    if code == 0 and behind.isdigit():
        out["behind_develop"] = behind
        if int(behind) > 0:
            out["version_note"] = (
                f"HEAD is {behind} commit(s) behind origin/develop — "
                "merge/rebase before release or version-sensitive work"
            )
    return out


def build_envelope(
    root: Path,
    *,
    with_security_run: bool = False,
    apply_remote_last: bool = True,
    resume_session: bool = False,
) -> dict[str, Any]:
    """Build the fixed schema used by all platforms.

    ``apply_remote_last`` (default True): run ``resume-branch.sh --apply`` so
    session-start lands on the latest remote work branch when the tree is clean.
    ``resume_session``: same-day return — do not apply remote_last; continue on
    the session-end card Branch (immediately prior session).
    """
    root = root.resolve()
    identity = check_manifest_identity(root)
    runtime_kv = _detect_runtime(root)
    mcp = _mcp_from_runtime(root, runtime_kv)
    if resume_session:
        apply_remote_last = False
    # session-start: fetch+switch/pull remote_last FIRST, then card.
    # session-resume: already landed on prior session Branch; report-only git facts.
    rb = _resume_branch_info(
        root, apply=apply_remote_last, reuse_cache=not resume_session
    )
    branch = rb.get("current") or _git_branch(root)
    resume = _resume_gate(
        root, for_chain="session-resume" if resume_session else ""
    )
    template_version = _template_version(root)
    orch = _orchestrator_update(root)
    integration = _integration_lag(root)
    sync = rb.get("sync_status") or runtime_kv.get("sync_status") or "unknown"
    pickup = _pickup_fields(
        branch=branch, resume=resume, rb=rb, resume_session=resume_session
    )
    plat = platform_brief()

    if with_security_run:
        _run(["bash", "scripts/session-security-sweep.sh"], root, timeout=120)
    sec_status, sec_path = _security_status(root)
    vault = _vault_ok(root)

    open_items = resume.get("open") or []
    if not open_items:
        open_items = _open_from_todo(root)

    expand: list[str] = []
    if identity.get("status") not in ("ok",):
        expand.append("identity")
    if mcp.get("mcp_ready") not in ("yes",):
        if mcp.get("mcp_ready") == "blocked":
            expand.append("mcp_blocked")
        elif mcp.get("mcp_ready") == "fail":
            # Handshake failed — surface start options + smoke repair first
            expand.append("mcp_start")
            expand.append("mcp_handshake_fail")
        else:
            expand.append("mcp_start")
    if sec_status in ("WARN", "FAIL"):
        expand.append("sec")
    if vault not in ("OK", "n/a"):
        expand.append("vault")
    if pickup.get("pickup_offer") == "yes":
        expand.append("pickup")
    if (rb.get("switch_result") or "") == "blocked_dirty":
        if "pickup" not in expand:
            expand.append("pickup")
    if (pickup.get("on_remote_last") or "") == "no":
        if "off_remote_last" not in expand:
            expand.append("off_remote_last")
        if "pickup" not in expand:
            expand.append("pickup")
    if integration.get("version_note"):
        expand.append("base_branch")
    # Always expand card pointer when present so agents surface check+card
    if resume.get("card") or resume.get("path"):
        if "resume_card" not in expand:
            expand.append("resume_card")
    # Automatic orchestrator upgrade/init offer (app users — never auto-apply)
    if orch.get("orch_offer") == "yes" or orch.get("orch_kind") in (
        "upgrade_available",
        "not_installed",
    ):
        expand.append("orch_upgrade")

    next_action = open_items[0] if open_items else "confirm direction with operator"
    project_name = identity.get("project_name") or root.name
    if identity.get("is_orchestrator_source"):
        project_name = root.name

    fw = identity.get("framework") or runtime_kv.get("manifest_environment_manager") or "?"
    env = runtime_kv.get("runtime") or "local"
    stack = f"{fw}@{env}"

    ptrs = {
        "todo": _latest_todo_path(root),
        "resume": resume.get("path"),
        "sweep": sec_path,
        "manifest": identity.get("manifest_path"),
        "envelope": str(SESSIONS_REL / LATEST_JSON),
    }
    # drop nulls
    ptrs = {k: v for k, v in ptrs.items() if v}

    envelope: dict[str, Any] = {
        "v": ENVELOPE_VERSION,
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project": project_name,
        "repo_slug": root.name,
        "identity": identity.get("status") or "missing",
        "identity_ok": bool(identity.get("ok")),
        "stack": stack,
        "branch": branch,
        "sync": sync,
        "sync_message": _short(rb.get("sync_message") or "", 120),
        "mcp": mcp.get("mcp_ready") or "no",
        "mcp_policy": mcp.get("mcp_policy") or "dev_only",
        "mcp_env_safe": mcp.get("mcp_env_safe") or "yes",
        "mcp_note": (mcp.get("mcp_note") or "")[:160],
        "sec": sec_status,
        "vault": vault,
        "resume_first": resume.get("resume_first") or "no",
        "max_cache_files": resume.get("max_cache_files"),
        "template_version": template_version,
        "behind_develop": integration.get("behind_develop"),
        "version_note": integration.get("version_note") or "",
        # Automatic orchestrator version check (session-start; offer only)
        **orch,
        # Platform surface — use YOUR tree only (Grok→.grok, Claude→.claude, …)
        "platform": plat.get("platform"),
        "surface_root": plat.get("surface_root"),
        "surface_manifest": plat.get("surface_manifest"),
        "surface_line": plat.get("briefing_line"),
        # Pickup / continue-where-left-off (all apps, every session-start)
        **pickup,
        "open": open_items[:MAX_OPEN],
        "next": _short(str(next_action), 100),
        "expand": list(dict.fromkeys(expand)),
        "expand_payload": {},
        "workstream": _workstream_brief(root),
    }
    apply_version_open(
        envelope,
        root=root,
        product=template_version,
        open_items=open_items,
    )
    # Promote one-line ws summary for compact CTX
    _ws = envelope.get("workstream") or {}
    if _ws.get("present") == "yes":
        envelope["ws_line"] = _ws.get("line") or ""
        envelope["ws_primary"] = _ws.get("primary") or ""
    else:
        envelope["ws_line"] = "ws present=no"
        envelope["ws_primary"] = ""


    if "identity" in expand:
        envelope["expand_payload"]["identity"] = {
            "briefing_line": identity.get("briefing_line"),
            "issues": (identity.get("issues") or [])[:5],
            "recommendations": (identity.get("recommendations") or [])[:5],
        }
    if "mcp_start" in expand or "mcp_blocked" in expand:
        opts = mcp.get("mcp_start_options") or []
        envelope["expand_payload"]["mcp"] = {
            "briefing_line": mcp.get("briefing_line"),
            "options": [
                {"id": o.get("id"), "label": o.get("label"), "commands": o.get("commands")}
                for o in opts[:4]
            ],
        }
    if "sec" in expand and sec_path:
        envelope["expand_payload"]["sec"] = {"report": sec_path, "status": sec_status}
    if "base_branch" in expand:
        envelope["expand_payload"]["base_branch"] = integration
    if "pickup" in expand or "off_remote_last" in expand:
        envelope["expand_payload"]["pickup"] = {
            "ask": pickup.get("pickup_ask"),
            "continue_target": pickup.get("continue_target"),
            "current": branch,
            "operator_last_branch": pickup.get("operator_last_branch"),
            "remote_last": pickup.get("remote_last"),
            "on_remote_last": pickup.get("on_remote_last"),
            "switch_applied": pickup.get("switch_applied"),
            "switch_result": pickup.get("switch_result"),
            "auto_switch_policy": "fetch_then_remote_last_then_card",
            "startup_order": pickup.get("startup_order"),
            "align_recommendations": pickup.get("align_recommendations"),
            "vs_remote_last_summary": pickup.get("vs_remote_last_summary"),
            "card_branch": pickup.get("card_branch"),
            "card_branch_match": pickup.get("card_branch_match"),
            "never_auto_checkout": False,
        }
    if "off_remote_last" in expand:
        envelope["expand_payload"]["off_remote_last"] = {
            "current": branch,
            "remote_last": pickup.get("remote_last"),
            "vs": pickup.get("vs_remote_last_summary"),
            "align": pickup.get("align_recommendations"),
            "recommendation": (
                f"Stay on `{branch}` only for intentional local work; "
                f"rejoin team tip `{pickup.get('remote_last')}` before PR/merge. "
                "Resume card here is local context, not automatic team handoff."
            ),
        }
    if "resume_card" in expand:
        envelope["expand_payload"]["resume_card"] = {
            "path": resume.get("path"),
            "resume_first": resume.get("resume_first"),
            "card_present": "yes" if (resume.get("card") or resume.get("path")) else "no",
            "surface": "always",
            "card": resume.get("card"),
            "card_branch": resume.get("card_branch"),
            "card_branch_match": resume.get("card_branch_match"),
            "card_tip_stale": resume.get("card_tip_stale") or "no",
            "card_remote_last": resume.get("card_remote_last"),
            "load_after": "remote_last_switch_pull",
        }
    if "orch_upgrade" in expand:
        envelope["expand_payload"]["orch_upgrade"] = {
            "kind": orch.get("orch_kind"),
            "installed": orch.get("orch_installed"),
            "available": orch.get("orch_available"),
            "message": orch.get("orch_message"),
            "preview": orch.get("orch_preview"),
            "apply": orch.get("orch_apply"),
            "auto_apply": False,
            "options": ["preview", "apply", "skip"],
        }

    # Situation: always run (even resume_first) — must understand project + in-flight work
    situation = _situation_brief(root)
    envelope["situation_status"] = situation.get("status") or "n/a"
    envelope["situation_ask"] = situation.get("ask")
    envelope["situation_gate"] = situation.get("agent_gate")
    envelope["repetition_count"] = situation.get("repetition_count") or 0
    envelope["situation_lines"] = (situation.get("briefing_lines") or [])[:20]
    if situation.get("repetition_count"):
        if "repetition" not in expand:
            expand.append("repetition")
        if "situation" not in expand:
            expand.append("situation")
        envelope["expand"] = list(dict.fromkeys(expand))
        envelope["expand_payload"]["repetition"] = {
            "count": situation.get("repetition_count"),
            "items": (situation.get("repetition") or [])[:5],
            "ask": situation.get("ask"),
            "choices": ["use prior", "continue", "re-scope"],
        }
        envelope["expand_payload"]["situation"] = {
            "where": situation.get("where"),
            "open": (situation.get("in_flight") or {}).get("open"),
            "ask": situation.get("ask"),
            "gate": situation.get("agent_gate"),
        }
    elif situation.get("status") == "ok":
        if "situation" not in expand:
            expand.append("situation")
        envelope["expand"] = list(dict.fromkeys(expand))
        envelope["expand_payload"]["situation"] = {
            "where": situation.get("where"),
            "open": (situation.get("in_flight") or {}).get("open"),
            "ask": situation.get("ask"),
            "gate": situation.get("agent_gate"),
            "repetition_count": 0,
        }

    if isinstance(envelope.get("ptrs"), dict):
        envelope["ptrs"]["situation"] = "reports/sessions/situation-latest.json"

    # Vault double-check: only on real session-start (apply path), not report-only tests
    if apply_remote_last:
        vault_startup = _emit_session_startup_vault(
            root,
            {
                **envelope,
                **pickup,
                **resume,
                "repetition_count": envelope.get("repetition_count"),
            },
        )
        envelope["vault_startup"] = vault_startup
        if vault_startup not in ("skip", "fail", ""):
            if isinstance(envelope.get("ptrs"), dict):
                envelope["ptrs"]["vault_startup"] = vault_startup
    else:
        envelope["vault_startup"] = "skipped_no_apply"

    envelope["briefing_compact"] = format_compact(envelope)
    return envelope


def format_compact(env: dict[str, Any]) -> str:
    """≤14 lines, enum-dense, no skill prose. Includes pickup + base version."""
    lines = [
        f"CTX v{env.get('v', 1)} project={env.get('project')} ver={env.get('template_version', '?')} "
        f"identity={env.get('identity')} "
        f"mcp={env.get('mcp')}@{env.get('mcp_policy')} env_safe={env.get('mcp_env_safe')} "
        f"sec={env.get('sec')} vault={env.get('vault')}",
        f"surface platform={env.get('platform', 'unknown')} "
        f"root={env.get('surface_root', '?')} "
        f"manifest={env.get('surface_manifest', '?')} "
        f"— USE THIS TREE for skills/commands (not other .platform dirs)",
        f"stack={env.get('stack')} branch={env.get('branch')} sync={env.get('sync')} "
        f"behind_develop={env.get('behind_develop')} "
        f"resume_first={env.get('resume_first')} max_cache={env.get('max_cache_files')}",
        f"pickup offer={env.get('pickup_offer', 'no')} "
        f"last={env.get('operator_last_branch', 'none')} "
        f"match={env.get('operator_resume_match', 'no')} "
        f"target={env.get('continue_target', env.get('branch'))}",
    ]
    if env.get("pickup_ask"):
        lines.append(f"ask: {env['pickup_ask']}")
    if env.get("version_note"):
        lines.append(f"base: {env['version_note']}")
    open_items = env.get("open") or []
    if open_items:
        lines.append("open: " + " | ".join(open_items[:MAX_OPEN]))
    lines.append(f"next: {env.get('next')}")
    if env.get("ver_open_drift") == "yes":
        lines.append(
            f"ver_open drift=yes from={env.get('ver_open_from') or '?'} "
            f"to={env.get('ver_open_to') or '?'} → warn+offer (do not auto-rewrite)"
        )
        if env.get("ver_open_ask"):
            lines.append(f"ver_ask: {_short(str(env.get('ver_open_ask')), 180)}")
    # Multi-workstream registry (Phase 2) — lean; max 5 ids in show=
    ws_line = env.get("ws_line")
    if ws_line:
        lines.append(ws_line)
    elif env.get("workstream"):
        lines.append(
            f"ws primary={env.get('ws_primary') or 'none'} "
            f"(see reports/sessions/workstreams.yaml)"
        )
    expand = env.get("expand") or []
    lines.append("expand: " + (",".join(expand) if expand else "none"))
    ptrs = env.get("ptrs") or {}
    if ptrs:
        ptr_s = " ".join(f"{k}={v}" for k, v in list(ptrs.items())[:5])
        lines.append(f"ptrs: {ptr_s}")
    # Switch + card policy lines (always)
    switch_result = env.get("switch_result") or "none"
    switch_applied = env.get("switch_applied") or "no"
    _tip_stale = env.get("card_tip_stale") or "no"
    _switch = (
        f"switch applied={switch_applied} result={switch_result} "
        f"remote_last={env.get('remote_last', 'none')} "
        f"on_tip={env.get('on_remote_last', '?')} "
    )
    if _tip_stale == "yes":
        _switch += (
            f"card_tip_stale=yes snapshot={env.get('card_remote_last') or '?'} "
        )
    lines.append(_switch + "policy=fetch_then_remote_last_then_card")
    if env.get("align_recommendations") and env.get("on_remote_last") == "no":
        lines.append(f"align: {_short(str(env.get('align_recommendations')), 160)}")
    # Situation + repetition (mandatory awareness)
    rep_n = env.get("repetition_count") or 0
    sit_gate = env.get("situation_gate") or ""
    if env.get("situation_status") == "ok" or rep_n:
        lines.append(
            f"situation gate={sit_gate or 'acknowledge'} "
            f"repetition={rep_n} "
            f"→ print situation-latest + ask before work"
        )
    if env.get("situation_ask"):
        lines.append(f"sit_ask: {_short(str(env.get('situation_ask')), 180)}")
    # Automatic orchestrator upgrade check (every session-start)
    orch_kind = env.get("orch_kind") or "unknown"
    orch_offer = env.get("orch_offer") or "no"
    lines.append(
        f"orch kind={orch_kind} offer={orch_offer} "
        f"installed={env.get('orch_installed') or 'none'} "
        f"available={env.get('orch_available') or 'none'}"
    )
    if orch_offer == "yes" and env.get("orch_message"):
        lines.append(f"orch: {env['orch_message']}")
        if env.get("orch_preview"):
            lines.append(f"orch_preview: {env['orch_preview']}")
        if env.get("orch_apply"):
            lines.append(f"orch_apply: {env['orch_apply']}  (options: preview|apply|skip — never auto-apply)")
    lines.append(
        "rule: print CTX + check/card always; USE surface root (Grok=.grok Claude=.claude "
        "Copilot=.github Cursor=.cursor Gemini=.gemini); shared OK: TODO docs scripts reports; "
        "ORDER: fetch→remote_last switch/pull→THEN card→situation (vault/wiki); "
        "MUST understand where-we-are + in-flight; repetition ⇒ remind + ask "
        "[use prior|continue|re-scope]; "
        "AUTO-SWITCH remote_last when clean (block real WIP; soft-dirty session noise OK); "
        "off tip ⇒ surface align; orch upgrade offer only; MCP develop-only; "
        "identity≠ok ⇒ do not trust stack; behind_develop>0 ⇒ merge develop before release; "
        "session-end+eod rich card + next-start reminder; "
        "ws= multi-workstream registry (workstream.py list|focus)"
    )
    return "\n".join(lines) + "\n"


def write_envelope_files(root: Path, envelope: dict[str, Any]) -> dict[str, str]:
    out_dir = root / SESSIONS_REL
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / LATEST_JSON
    txt_path = out_dir / LATEST_TXT
    # strip huge card text if any leaked
    serializable = {k: v for k, v in envelope.items() if k != "card_full"}
    json_path.write_text(
        json.dumps(serializable, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    txt_path.write_text(envelope.get("briefing_compact") or format_compact(envelope), encoding="utf-8")
    return {
        "json": str(json_path.relative_to(root)),
        "txt": str(txt_path.relative_to(root)),
    }
