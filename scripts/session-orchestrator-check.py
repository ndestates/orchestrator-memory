#!/usr/bin/env python3
"""Session-start: announce if this app needs orchestrator init or upgrade.

Works **inside app repos and ddev** with only the stdlib — does **not** require
``pip install orchestrator`` or ``PYTHONPATH`` to the template.

Available version resolution (first / best-of):

1. ``ORCHESTRATOR_TEMPLATE_VERSION`` env
2. ``scripts/orchestrator-template-version`` (shipped with the template deploy)
3. Sibling checkout ``../orchestrator/VERSION`` (common monorepo layout)
4. ``orchestrator_cli.template_version()`` if the CLI package is importable
5. **GitHub Releases latest** (optional network; opt out ``ORCHESTRATOR_NO_REMOTE_VERSION=1``)
6. Fall back to the installed lock version (can only confirm "installed", not a newer release)

Session-start auto-upgrade (apps only)::

  python3 scripts/session-orchestrator-check.py --auto-apply

When a newer GitHub (or local) template is available and the tree is **clean**,
runs ``orchestrator upgrade . --from-github <tag> --if-available --yes --no-pr``.

Safety (hard)::

- **Never** auto-apply on the orchestrator **template source** repo
- Upgrade uses deploy ``default_action=skip`` → customized app scripts preserved
- ``ensure_project_manifest`` **preserves** existing project-manifest (no template overwrite)
- Dirty working tree → skip auto-apply (offer only; never discard WIP)
- Opt out: ``ORCHESTRATOR_SESSION_AUTO_UPGRADE=0`` or ``ORCHESTRATOR_NO_UPDATE_CHECK=1``
- Init (not installed) is **not** auto-applied (too destructive); only upgrade

Usage (from app root, including ``ddev exec``)::

  python3 scripts/session-orchestrator-check.py
  python3 scripts/session-orchestrator-check.py --json
  python3 scripts/session-orchestrator-check.py --offer
  python3 scripts/session-orchestrator-check.py --prompt   # TTY: ask to apply
  python3 scripts/session-orchestrator-check.py --auto-apply  # session-start

Exit: 0 up-to-date/skip/applied, 2 upgrade available (not applied), 3 not installed,
4 auto-apply failed.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

LOCK_NAME = ".orchestrator-version"
STAMP_REL = Path("scripts") / "orchestrator-template-version"


def _parse_semver_core(v: str) -> tuple[int, int, int]:
    """MAJOR.MINOR.PATCH only (legacy). Prefer _version_key for comparisons."""
    parts = (v.strip().lstrip("v").split("-")[0].split("."))[:3]
    nums = [int(p) for p in parts if p.isdigit()]
    while len(nums) < 3:
        nums.append(0)
    return (nums[0], nums[1], nums[2])


def _version_key(v: str) -> tuple:
    """PEP440-ish key so 1.9.0-pre.5 < 1.9.0 and pre.5 > pre.3 (stdlib).

    Aligns with ``orchestrator_cli.version.is_newer`` when packaging is present.
    """
    raw = (v or "").strip().lstrip("v")
    try:
        from packaging.version import Version  # type: ignore

        return (0, Version(raw))  # type: ignore[return-value]
    except Exception:
        pass
    # Stdlib fallback: core + optional -pre.N / -rc.N / -a.N / -b.N
    import re

    m = re.match(
        r"^(\d+)\.(\d+)\.(\d+)(?:[-.]?(?P<pre>a|b|rc|pre|alpha|beta|dev)\.?(\d+))?$",
        raw,
        re.I,
    )
    if not m:
        return (1, _parse_semver_core(raw), 0, 0)
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    pre_label = (m.group("pre") or "").lower()
    pre_num = int(m.group(5) or 0) if m.group("pre") else 0
    # Final release sorts after any pre of same core: pre_rank 0 for finals via high sentinel
    if not pre_label:
        return (1, major, minor, patch, 99, 0)  # final
    rank = {
        "dev": 1,
        "a": 2,
        "alpha": 2,
        "b": 3,
        "beta": 3,
        "pre": 4,
        "rc": 5,
    }.get(pre_label, 4)
    return (1, major, minor, patch, rank, pre_num)


def _is_newer(candidate: str, current: str) -> bool:
    """True if candidate is strictly newer than current (pre-release aware)."""
    try:
        return _version_key(candidate) > _version_key(current)
    except Exception:
        return _parse_semver_core(candidate) > _parse_semver_core(current)


def _read_lock(target: Path) -> dict | None:
    p = target / LOCK_NAME
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _looks_like_project(target: Path) -> bool:
    if (target / LOCK_NAME).is_file():
        return True
    if (target / ".grok").is_dir():
        return True
    if (target / "chains" / "registry.yaml").is_file() or (target / "CHAIN.md").is_file():
        return True
    return False


def _read_version_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8").strip().splitlines()[0].strip()
        return text.lstrip("v") if text else None
    except OSError:
        return None


def _remote_suppressed() -> bool:
    return os.environ.get("ORCHESTRATOR_NO_REMOTE_VERSION", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _fetch_github_latest() -> tuple[str | None, str]:
    """Return (version, source) from GitHub Releases latest, or (None, reason)."""
    if _remote_suppressed():
        return None, "remote_suppressed"
    repo = (os.environ.get("ORCHESTRATOR_GITHUB_REPO") or "ndestates/orchestrator").strip()
    api = (os.environ.get("ORCHESTRATOR_GITHUB_API") or "https://api.github.com").rstrip("/")
    try:
        timeout = max(0.5, min(30.0, float(os.environ.get("ORCHESTRATOR_REMOTE_VERSION_TIMEOUT") or "3")))
    except ValueError:
        timeout = 3.0
    url = f"{api}/repos/{repo}/releases/latest"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "orchestrator-session-check",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    for key in ("GITHUB_TOKEN", "GH_TOKEN", "ORCHESTRATOR_GITHUB_TOKEN"):
        tok = (os.environ.get(key) or "").strip()
        if tok:
            headers["Authorization"] = f"Bearer {tok}"
            break
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        return None, "remote_unreachable"
    tag = data.get("tag_name") or data.get("name") if isinstance(data, dict) else None
    if not tag or not isinstance(tag, str):
        return None, "remote_empty"
    ver = tag.strip().lstrip("v")
    if not ver:
        return None, "remote_empty"
    return ver, f"github:{repo}/releases/latest"


def resolve_available(target: Path) -> tuple[str | None, str]:
    """Return (version, source_label). Prefer the newest among local sources and GitHub."""
    candidates: list[tuple[str, str]] = []

    env = (os.environ.get("ORCHESTRATOR_TEMPLATE_VERSION") or "").strip()
    if env:
        candidates.append((env.lstrip("v"), "env:ORCHESTRATOR_TEMPLATE_VERSION"))

    stamp = _read_version_file(target / STAMP_REL)
    if stamp:
        candidates.append((stamp, str(STAMP_REL)))

    sibling = target.parent / "orchestrator" / "VERSION"
    stamp = _read_version_file(sibling)
    if stamp:
        candidates.append((stamp, str(sibling)))

    try:
        src = Path(__file__).resolve().parents[1] / "src"
        if src.is_dir() and str(src) not in sys.path:
            sys.path.insert(0, str(src))
        from orchestrator_cli.version import template_version  # type: ignore

        candidates.append((template_version().lstrip("v"), "orchestrator_cli"))
    except Exception:
        pass

    remote_ver, remote_src = _fetch_github_latest()
    if remote_ver:
        candidates.append((remote_ver, remote_src))

    if not candidates:
        return None, "none"

    best_v, best_s = candidates[0]
    for v, s in candidates[1:]:
        if _is_newer(v, best_v):
            best_v, best_s = v, s
    return best_v, best_s


def _is_template_source(target: Path) -> bool:
    """True for the orchestrator template source repo (never auto-upgrade self)."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
        from _engine.manifest_identity import is_orchestrator_source_repo  # type: ignore

        if is_orchestrator_source_repo(target):
            return True
    except Exception:
        pass
    # Heuristic: CLI package + VERSION stamp + deploy bundle
    if (target / "src" / "orchestrator_cli").is_dir() and (
        target / "scripts" / "deploy-bundle.yaml"
    ).is_file():
        return True
    return False


def _tree_clean(target: Path) -> bool:
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=target,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if r.returncode != 0:
            return False
        return not (r.stdout or "").strip()
    except Exception:
        return False


def _porcelain_paths(target: Path) -> list[str]:
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=target,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except Exception:
        return []
    if r.returncode != 0 or not (r.stdout or "").strip():
        return []
    paths: list[str] = []
    for line in r.stdout.splitlines():
        if len(line) < 4:
            continue
        p = line[3:].strip()
        if " -> " in p:
            p = p.split(" -> ", 1)[1].strip()
        p = p.strip('"')
        if p:
            paths.append(p)
    return paths


# Session spin-up noise — safe to discard before auto-upgrade (rewritten after)
_SOFT_DIRTY_PREFIXES = (
    "reports/sessions/context-latest.",
    "reports/sessions/situation-latest.",
    "reports/sessions/spinup-latest.",
    "reports/sessions/situation-fingerprint",
    "reports/sessions/vector-probe-latest.",
    "reports/security/session-sweep-",
    "reports/security/session-sweep-fingerprint",
    "reports/security/session-sweep-latest.",
)


def _is_soft_dirty_path(path: str) -> bool:
    return any(path.startswith(p) or path == p.rstrip(".") for p in _SOFT_DIRTY_PREFIXES)


def _clear_soft_dirty(target: Path) -> int:
    """Restore/remove session noise so upgrade can proceed without stashing real WIP."""
    cleared = 0
    for path in _porcelain_paths(target):
        if not _is_soft_dirty_path(path):
            continue
        full = target / path
        # Tracked: restore; untracked: delete
        r = subprocess.run(
            ["git", "ls-files", "--error-unmatch", path],
            cwd=target,
            capture_output=True,
            timeout=5,
        )
        if r.returncode == 0:
            subprocess.run(
                ["git", "restore", "--worktree", "--staged", "--", path],
                cwd=target,
                capture_output=True,
                timeout=10,
            )
        elif full.is_file():
            try:
                full.unlink()
            except OSError:
                pass
        cleared += 1
    return cleared


def _stash_wip(target: Path) -> tuple[bool, str]:
    """Stash all remaining dirty (incl untracked). Returns (ok, ref_or_error)."""
    msg = "orchestrator-session-auto-upgrade"
    r = subprocess.run(
        ["git", "stash", "push", "-u", "-m", msg],
        cwd=target,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if r.returncode != 0:
        return False, (r.stderr or r.stdout or "stash failed").strip()[:200]
    # Confirm clean
    if not _tree_clean(target):
        return False, "stash did not clean working tree"
    return True, msg


def _stash_pop(target: Path) -> tuple[bool, str]:
    r = subprocess.run(
        ["git", "stash", "pop"],
        cwd=target,
        capture_output=True,
        text=True,
        timeout=60,
    )
    if r.returncode != 0:
        return False, (r.stderr or r.stdout or "stash pop failed").strip()[:240]
    return True, "restored"


def prepare_tree_for_auto_upgrade(target: Path) -> dict:
    """Make tree clean enough for orchestrator upgrade without discarding real WIP.

    1. Drop session spin-up noise (context/situation/spinup/sweep meta)
    2. If still dirty → stash -u (including untracked)
    3. Caller must restore via restore_tree_after_auto_upgrade
    """
    result: dict = {
        "clean": False,
        "soft_cleared": 0,
        "stashed": False,
        "stash_msg": "",
        "error": "",
    }
    if _tree_clean(target):
        result["clean"] = True
        return result
    result["soft_cleared"] = _clear_soft_dirty(target)
    if _tree_clean(target):
        result["clean"] = True
        return result
    ok, info = _stash_wip(target)
    if not ok:
        result["error"] = info
        return result
    result["stashed"] = True
    result["stash_msg"] = info
    result["clean"] = True
    return result


def restore_tree_after_auto_upgrade(target: Path, prep: dict) -> dict:
    """Pop stash if we stashed; report conflicts without failing session-start hard."""
    out = {"restored": False, "error": ""}
    if not prep.get("stashed"):
        out["restored"] = True
        return out
    ok, info = _stash_pop(target)
    out["restored"] = ok
    if not ok:
        out["error"] = (
            f"stash pop after upgrade: {info} — "
            "WIP remains in git stash; run: git stash list && git stash pop"
        )
    return out


def _auto_upgrade_enabled() -> bool:
    if os.environ.get("ORCHESTRATOR_NO_UPDATE_CHECK", "").strip().lower() in (
        "1",
        "true",
        "yes",
    ):
        return False
    # Default ON for apps; opt out with =0/false/no
    v = (os.environ.get("ORCHESTRATOR_SESSION_AUTO_UPGRADE") or "1").strip().lower()
    return v not in ("0", "false", "no", "off")


def evaluate(target: Path) -> dict:
    target = target.resolve()
    if _is_template_source(target):
        available, avail_source = resolve_available(target)
        ver = _read_version_file(target / "VERSION") or available
        return {
            "kind": "template_source",
            "target": str(target),
            "installed": None,
            "available": ver,
            "available_source": avail_source,
            "message": "orchestrator: template source repo — app upgrade N/A (no auto-apply)",
            "action": None,
            "preview_action": None,
            "apply_action": None,
            "offer": False,
            "auto_apply_safe": False,
            "preserves_custom": True,
            "preserves_manifest": True,
        }

    lock = _read_lock(target)
    installed = None
    if lock and lock.get("version"):
        installed = str(lock["version"]).lstrip("v")

    available, avail_source = resolve_available(target)

    if installed is None:
        if not _looks_like_project(target):
            return {
                "kind": "skipped",
                "target": str(target),
                "installed": None,
                "available": available,
                "available_source": avail_source,
                "message": "",
                "action": None,
                "preview_action": None,
                "apply_action": None,
                "offer": False,
                "auto_apply_safe": False,
            }
        avail_s = available or "(unknown — set ORCHESTRATOR_TEMPLATE_VERSION or upgrade template)"
        return {
            "kind": "not_installed",
            "target": str(target),
            "installed": None,
            "available": available,
            "available_source": avail_source,
            "message": (
                f"orchestrator: not installed in {target} "
                f"(template {avail_s} available) — run `orchestrator init . --no-pr` "
                f"(session-start does not auto-init)"
            ),
            "action": f"orchestrator init {target} --no-pr",
            "preview_action": None,
            "apply_action": f"orchestrator init {target} --no-pr",
            "offer": True,
            "auto_apply_safe": False,
            "preserves_custom": True,
            "preserves_manifest": True,
        }

    if available and _is_newer(available, installed):
        tag = f"v{available.lstrip('v')}"
        # Prefer GitHub materialize so apps upgrade without a sibling template checkout
        preview = (
            f"orchestrator upgrade {target} --from-github {tag} --if-available --no-pr"
        )
        apply = (
            f"orchestrator upgrade {target} --from-github {tag} "
            f"--if-available --yes --no-pr"
        )
        return {
            "kind": "upgrade_available",
            "target": str(target),
            "installed": installed,
            "available": available,
            "available_source": avail_source,
            "message": (
                f"orchestrator: upgrade available — installed {installed}, "
                f"template {available} ({avail_source}); "
                f"upgrade skips customized files and preserves project-manifest"
            ),
            "action": apply,
            "preview_action": preview,
            "apply_action": apply,
            "offer": True,
            "auto_apply_safe": True,
            "preserves_custom": True,
            "preserves_manifest": True,
            # Dirty trees: soft-clear session noise + stash WIP, then upgrade
            "requires_clean_tree": False,
            "dirty_strategy": "soft_clear_then_stash",
        }

    if available:
        msg = (
            f"orchestrator: {installed} installed "
            f"(available {available} via {avail_source}) ✓ up to date"
        )
    else:
        msg = (
            f"orchestrator: {installed} installed ✓ "
            f"(no newer stamp found; host check: `orchestrator check .` from the template CLI)"
        )
    return {
        "kind": "up_to_date",
        "target": str(target),
        "installed": installed,
        "available": available or installed,
        "available_source": avail_source,
        "message": msg,
        "action": None,
        "preview_action": None,
        "apply_action": None,
        "offer": False,
        "auto_apply_safe": False,
        "preserves_custom": True,
        "preserves_manifest": True,
    }


def _print_offer(notice: dict) -> None:
    print(f"ORCHESTRATOR_UPGRADE_OFFER={'yes' if notice.get('offer') else 'no'}")
    print(f"kind={notice.get('kind')}")
    print(f"installed={notice.get('installed')}")
    print(f"available={notice.get('available')}")
    print(f"available_source={notice.get('available_source')}")
    if notice.get("preview_action"):
        print(f"preview={notice['preview_action']}")
    if notice.get("apply_action"):
        print(f"apply={notice['apply_action']}")
    print("options: preview | apply | skip")


def _run_apply(notice: dict, *, target: Path) -> int:
    cmd = notice.get("apply_action")
    if not cmd:
        print("orchestrator: nothing to apply", file=sys.stderr)
        return 1
    print(f"orchestrator: running: {cmd}", file=sys.stderr)
    # Prefer PATH CLI; fall back to module form
    parts = cmd.split()
    try:
        proc = subprocess.run(parts, check=False, cwd=target)
        return int(proc.returncode)
    except FileNotFoundError:
        # orchestrator not on PATH — try python -m
        if parts and parts[0] == "orchestrator":
            mod = [sys.executable, "-m", "orchestrator_cli", *parts[1:]]
            proc = subprocess.run(mod, check=False, cwd=target)
            return int(proc.returncode)
        raise


def auto_apply_if_needed(target: Path, notice: dict) -> dict:
    """Always attempt upgrade when available (stash WIP if needed); then restore.

    Hard guarantees from ``orchestrator upgrade``:
    - customized files skipped (default_action=skip)
    - project-manifest preserved (ensure_project_manifest)
    - never runs on template source (evaluate returns template_source)
    """
    out = dict(notice)
    out["auto_applied"] = False
    out["auto_apply_result"] = "skipped"
    out["stash_used"] = False
    out["stash_restored"] = None
    if notice.get("kind") != "upgrade_available":
        out["auto_apply_result"] = f"kind_{notice.get('kind')}"
        return out
    if not notice.get("auto_apply_safe"):
        out["auto_apply_result"] = "not_safe"
        return out
    if not _auto_upgrade_enabled():
        out["auto_apply_result"] = "disabled_by_env"
        out["message"] = (
            (notice.get("message") or "")
            + " — auto-upgrade disabled (ORCHESTRATOR_SESSION_AUTO_UPGRADE=0)"
        )
        out["offer"] = True
        return out

    prep = prepare_tree_for_auto_upgrade(target)
    out["soft_cleared"] = prep.get("soft_cleared", 0)
    if not prep.get("clean"):
        out["auto_apply_result"] = "prepare_failed"
        out["message"] = (
            (notice.get("message") or "")
            + f" — could not prepare clean tree for auto-upgrade: {prep.get('error')}"
        )
        out["offer"] = True
        return out
    if prep.get("stashed"):
        out["stash_used"] = True
        print(
            "orchestrator: stashed local WIP for auto-upgrade "
            f"(msg={prep.get('stash_msg')})",
            file=sys.stderr,
        )

    print(
        f"orchestrator: session-start auto-upgrade {notice.get('installed')} → "
        f"{notice.get('available')} "
        f"(from-github; skip customized; preserve project-manifest)",
        file=sys.stderr,
    )
    try:
        code = _run_apply(notice, target=target)
    finally:
        rest = restore_tree_after_auto_upgrade(target, prep)
        out["stash_restored"] = rest.get("restored")
        if rest.get("error"):
            out["stash_restore_error"] = rest["error"]
            print(f"orchestrator: {rest['error']}", file=sys.stderr)

    if code == 0:
        out["auto_applied"] = True
        out["auto_apply_result"] = "applied"
        # Extra hygiene if upgrade path did not reinstall CLI (old CLI without flow hook)
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
            from orchestrator_cli.cli_hygiene import refresh_host_cli  # type: ignore

            hy = refresh_host_cli(version=str(notice.get("available") or ""))
            out["cli_hygiene"] = hy.get("message")
            if hy.get("message"):
                print(f"orchestrator: {hy['message']}", file=sys.stderr)
        except Exception as exc:
            out["cli_hygiene"] = f"skipped ({exc})"
        refreshed = evaluate(target)
        out["kind"] = refreshed.get("kind")
        out["installed"] = refreshed.get("installed") or notice.get("available")
        out["available"] = refreshed.get("available")
        stash_note = ""
        if out.get("stash_used"):
            if out.get("stash_restored"):
                stash_note = "; WIP restored from stash"
            else:
                stash_note = "; WIP still in stash — run git stash pop"
        out["message"] = (
            f"orchestrator: auto-upgraded to {out['installed']} "
            f"(customized scripts skipped; project-manifest preserved{stash_note}) "
            f"— continuing session-start"
        )
        out["offer"] = False
        out["apply_action"] = None
        out["preview_action"] = None
    else:
        out["auto_apply_result"] = f"failed_exit_{code}"
        out["message"] = (
            (notice.get("message") or "")
            + f" — auto-upgrade failed (exit {code}); "
            + ("WIP restore attempted; " if out.get("stash_used") else "")
            + "continuing session-start — re-run upgrade manually if needed"
        )
        out["offer"] = True
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", nargs="?", default=".", type=Path)
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--always",
        action="store_true",
        help="also print when up to date (default: always print a one-liner)",
    )
    ap.add_argument(
        "--offer",
        action="store_true",
        help="print machine-friendly upgrade offer lines for session-start agents",
    )
    ap.add_argument(
        "--prompt",
        action="store_true",
        help="if upgrade available and stdin is a TTY, ask y/N then apply with --yes",
    )
    ap.add_argument(
        "--auto-apply",
        action="store_true",
        help=(
            "session-start: if upgrade available and tree clean, apply from GitHub "
            "(skip customized files; preserve project-manifest). Opt out: "
            "ORCHESTRATOR_SESSION_AUTO_UPGRADE=0"
        ),
    )
    args = ap.parse_args()
    always = True if not args.json else args.always
    target = Path(args.path).resolve()

    notice = evaluate(target)
    applied_failed = False
    if args.auto_apply:
        notice = auto_apply_if_needed(target, notice)
        if notice.get("auto_apply_result", "").startswith("failed"):
            applied_failed = True

    if args.json:
        print(json.dumps(notice, indent=2))
    else:
        kind = notice["kind"]
        if notice.get("auto_applied"):
            print(notice["message"])
        elif kind in ("upgrade_available", "not_installed"):
            print(notice["message"])
            if notice.get("preview_action"):
                print(f"  → preview: {notice['preview_action']}")
            if notice.get("apply_action"):
                print(f"  → apply:   {notice['apply_action']}")
            elif notice.get("action"):
                print(f"  → {notice['action']}")
            if args.offer:
                _print_offer(notice)
        elif kind == "up_to_date" and (always or args.always):
            print(notice["message"])
            if args.offer:
                _print_offer(notice)
        elif kind == "template_source" and (always or args.always):
            print(notice["message"])
        elif kind == "skipped" and args.always:
            print(
                f"orchestrator: no lock and tree does not look like an app "
                f"({notice['target']})"
            )
            if args.offer:
                _print_offer(notice)

    if args.prompt and notice.get("kind") == "upgrade_available" and not notice.get(
        "auto_applied"
    ):
        if not sys.stdin.isatty():
            print(
                "orchestrator: --prompt ignored (not a TTY); re-run interactively "
                "or use: " + (notice.get("apply_action") or ""),
                file=sys.stderr,
            )
        else:
            ans = input(
                f"Apply orchestrator upgrade {notice.get('installed')} → "
                f"{notice.get('available')} now? [y/N] "
            ).strip().lower()
            if ans in ("y", "yes"):
                return _run_apply(notice, target=target)
            print("orchestrator: upgrade skipped")

    if applied_failed:
        return 4
    if notice["kind"] == "upgrade_available":
        return 2
    if notice["kind"] == "not_installed":
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
