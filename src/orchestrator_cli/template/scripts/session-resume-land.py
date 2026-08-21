#!/usr/bin/env python3
"""Land same-day /chain session-resume on the immediately prior session.

GitHub is the only shared state between machines. Local stashes and unpushed
cards are invisible elsewhere. This lander:

  1. Fetches origin first
  2. Resolves the prior session from origin (session-end card / vault pointer)
     unless *this* machine has exclusive unpushed pause work
  3. Checks out that branch from origin when it exists
  4. Fast-forwards if behind and clean; never reset/discard local dirty
  5. Reports drift (ahead/behind/diverged/dirty/unpushed)

session-start still uses remote_last. session-resume does not.

Usage:
  python3 scripts/session-resume-land.py
  python3 scripts/session-resume-land.py --json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_SKIP_ORIGIN = ("HEAD", "develop", "master", "main")
_SESSION_END_REL = "reports/sessions/resume-session-end-latest.md"
_PAUSE_SOURCES = ("session-end", "session_end", "pause", "mid-day", "midday")


def _load_resume_mod():
    path = SCRIPTS / "session-resume-brief.py"
    spec = importlib.util.spec_from_file_location("session_resume_brief", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load session-resume-brief.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_preserve_mod():
    path = SCRIPTS / "eod-commit-dirty.py"
    spec = importlib.util.spec_from_file_location("eod_commit_dirty", path)
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=90)
    return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()


def _is_pause(source: str) -> bool:
    return (source or "").strip().lower() in _PAUSE_SOURCES


def _ahead_behind(root: Path, branch: str) -> tuple[int | None, int | None]:
    up = f"origin/{branch}"
    code, _, _ = _run(["git", "show-ref", "--verify", "--quiet", f"refs/remotes/{up}"], root)
    if code != 0:
        return None, None
    c1, ahead, _ = _run(["git", "rev-list", "--count", f"{up}..{branch}"], root)
    c2, behind, _ = _run(["git", "rev-list", "--count", f"{branch}..{up}"], root)
    if c1 != 0 or c2 != 0:
        return None, None
    try:
        return int(ahead or "0"), int(behind or "0")
    except ValueError:
        return None, None


def _origin_has_branch(root: Path, branch: str) -> bool:
    if not branch:
        return False
    code, _, _ = _run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/remotes/origin/{branch}"],
        root,
    )
    return code == 0


def _origin_work_refs(root: Path) -> list[tuple[str, int]]:
    code, out, _ = _run(
        [
            "git",
            "for-each-ref",
            "refs/remotes/origin/",
            "--sort=-committerdate",
            "--format=%(refname:short)|%(committerdate:unix)",
        ],
        root,
    )
    if code != 0 or not out:
        return []
    refs: list[tuple[str, int]] = []
    for line in out.splitlines():
        ref, _, ts = line.partition("|")
        name = ref.removeprefix("origin/")
        if not name or name in _SKIP_ORIGIN or name.startswith("dependabot/"):
            continue
        try:
            refs.append((name, int(ts or "0")))
        except ValueError:
            refs.append((name, 0))
    return refs


def _show_origin_file(root: Path, branch: str, rel: str) -> str:
    code, out, _ = _run(["git", "show", f"origin/{branch}:{rel}"], root)
    return out if code == 0 else ""


def _origin_session_end(root: Path, resume_mod, today: str) -> dict | None:
    """Newest same-day session-end card committed on any origin work branch."""
    best: dict | None = None
    for name, ts in _origin_work_refs(root):
        blob = _show_origin_file(root, name, _SESSION_END_REL)
        if not blob:
            continue
        compact = resume_mod._extract_card_text(blob, kind="resume")
        source = resume_mod.parse_card_source(compact)
        if not _is_pause(source):
            continue
        card_date = resume_mod.parse_card_date(compact, None)
        if card_date and card_date != today:
            continue
        branch = resume_mod.parse_card_branch(compact) or name
        cand = {
            "branch": branch,
            "origin_ref": name,
            "ts": ts,
            "source": source,
            "card_date": card_date,
        }
        if best is None or ts > int(best.get("ts") or 0):
            best = cand
    return best


def _local_card_mtime_unix(root: Path, rel: str) -> int:
    path = root / rel
    if not path.is_file():
        return 0
    try:
        return int(path.stat().st_mtime)
    except OSError:
        return 0


def resolve_prior_session(root: Path, resume_mod, today: str) -> dict:
    """GitHub-first prior session, unless this machine has exclusive unpushed pause work."""
    local_info = resume_mod.read_card(root, session_end=True)
    if local_info.get("status") != "found":
        local_info = resume_mod.read_card(root, resume_only=True)
    local_card = local_info.get("card") or ""
    local_branch = resume_mod.parse_card_branch(local_card)
    local_source = resume_mod.parse_card_source(local_card)
    local_date = local_info.get("card_date") or resume_mod.parse_card_date(local_card, None)
    local_pause = _is_pause(local_source) and (not local_date or local_date == today)

    origin_end = _origin_session_end(root, resume_mod, today)

    code, cur, _ = _run(["git", "branch", "--show-current"], root)
    cur = cur if code == 0 else ""
    code_s, porcelain, _ = _run(["git", "status", "--porcelain"], root)
    dirty = bool(porcelain) if code_s == 0 else True
    ahead = behind = None
    if local_branch:
        ahead, behind = _ahead_behind(root, local_branch)
    local_exclusive = bool(
        local_pause
        and local_branch
        and (
            dirty
            or (ahead is not None and ahead > 0)
            or not _origin_has_branch(root, local_branch)
        )
    )

    origin_newer = bool(
        origin_end
        and int(origin_end.get("ts") or 0)
        > _local_card_mtime_unix(root, _SESSION_END_REL)
        and origin_end.get("branch")
    )

    # This machine's unpushed/dirty pause wins unless origin has a *newer* pause
    # (the other laptop published a later session-end).
    if local_exclusive and local_branch and not origin_newer:
        target, via = local_branch, "local_unpushed"
    elif origin_end and origin_end.get("branch"):
        target, via = origin_end["branch"], "origin_card"
    elif local_pause and local_branch:
        target, via = local_branch, "local_card"
    else:
        target, via = None, "none"

    return {
        "target": target,
        "via": via,
        "local_pause": local_pause,
        "local_branch": local_branch or None,
        "local_source": local_source or None,
        "local_date": local_date,
        "origin_card": origin_end,
        "current": cur,
        "dirty": dirty,
        "ahead": ahead,
        "behind": behind,
        "local_exclusive": local_exclusive,
        "origin_newer": origin_newer,
        "card_path": local_info.get("path"),
    }


def _local_branch_exists(root: Path, branch: str) -> bool:
    code, _, _ = _run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
        root,
    )
    return code == 0


def _checkout_prior(root: Path, branch: str, dirty: bool, via: str) -> dict:
    """Checkout prior session. Never reset local to origin (-B). Don't move foreign dirty."""
    code, cur, _ = _run(["git", "branch", "--show-current"], root)
    cur = cur if code == 0 else ""
    if cur == branch:
        return {"ok": True, "switched": False, "stash_restored": False}
    if dirty and via == "origin_card":
        return {
            "ok": False,
            "error": (
                f"local dirty on `{cur}` is not the GitHub prior session `{branch}` "
                "— commit and push this machine, or stash is machine-local and will not "
                "follow to origin"
            ),
        }
    if dirty:
        preserve = _load_preserve_mod()
        if preserve is None:
            return {"ok": False, "error": "dirty and no stash-restore helper"}
        moved = preserve.stash_switch_restore(root, branch)
        if moved.get("status") not in ("restored", "clean"):
            return {
                "ok": False,
                "error": moved.get("error") or "stash-restore failed",
                "preserve": moved,
            }
        return {"ok": True, "switched": True, "stash_restored": True}
    if _local_branch_exists(root, branch):
        code, _, err = _run(["git", "checkout", branch], root)
        if code != 0:
            return {"ok": False, "error": err or f"checkout {branch} failed"}
        return {"ok": True, "switched": True, "stash_restored": False}
    if _origin_has_branch(root, branch):
        code, _, err = _run(
            ["git", "checkout", "-b", branch, "--track", f"origin/{branch}"],
            root,
        )
        if code != 0:
            return {"ok": False, "error": err or f"track origin/{branch} failed"}
        return {"ok": True, "switched": True, "stash_restored": False}
    return {"ok": False, "error": f"no local or origin/{branch} — push from the other machine"}


def _maybe_ff_pull(root: Path, branch: str, dirty: bool) -> dict:
    ahead, behind = _ahead_behind(root, branch)
    pulled = False
    blocked = None
    if behind and behind > 0 and (ahead or 0) == 0:
        if dirty:
            blocked = "dirty_blocks_ff_pull"
        else:
            code, _, err = _run(["git", "pull", "--ff-only"], root)
            if code == 0:
                pulled = True
                ahead, behind = _ahead_behind(root, branch)
            else:
                blocked = err or "ff-only pull failed"
    diverged = bool((ahead or 0) > 0 and (behind or 0) > 0)
    return {
        "ahead": ahead,
        "behind": behind,
        "pulled": pulled,
        "diverged": diverged,
        "blocked_ff": blocked,
        "on_origin": _origin_has_branch(root, branch),
    }


def land(root: Path) -> dict:
    resume = _load_resume_mod()
    today = date.today().isoformat()
    _run(["git", "fetch", "origin", "--prune"], root)
    resolved = resolve_prior_session(root, resume, today)
    out: dict = {
        "status": "redirect_session_start",
        "landed": False,
        "prior_session_branch": resolved.get("target"),
        "branch_now": resolved.get("current"),
        "card_path": resolved.get("card_path"),
        "card_source": resolved.get("local_source"),
        "same_day": "yes" if resolved.get("local_date") == today or resolved.get("origin_card") else "no",
        "switched": False,
        "via": resolved.get("via"),
        "reason": "",
        "drift": {},
    }
    target = resolved.get("target")
    if not target:
        out["reason"] = (
            "No same-day prior session on this machine or origin — "
            "use /chain session-start"
        )
        return out

    moved = _checkout_prior(
        root, target, bool(resolved.get("dirty")), str(resolved.get("via") or "")
    )
    if not moved.get("ok"):
        out["reason"] = moved.get("error") or "could not land on prior session"
        out["branch_now"] = resolved.get("current")
        return out
    out["switched"] = bool(moved.get("switched"))
    out["stash_restored"] = bool(moved.get("stash_restored"))

    code, cur, _ = _run(["git", "branch", "--show-current"], root)
    cur = cur if code == 0 else ""
    out["branch_now"] = cur
    code_s, porcelain, _ = _run(["git", "status", "--porcelain"], root)
    dirty_now = bool(porcelain) if code_s == 0 else True
    drift = _maybe_ff_pull(root, target, dirty_now)
    drift["dirty"] = dirty_now
    drift["unpushed_commits"] = bool((drift.get("ahead") or 0) > 0)
    drift["github_has_branch"] = bool(drift.get("on_origin"))
    drift["via"] = resolved.get("via")
    if dirty_now:
        drift["uncommitted_local_wip"] = True
        drift["note"] = (
            "Uncommitted files stay on this machine only until committed and pushed"
        )
    if not drift.get("on_origin"):
        drift["note"] = (
            "Prior session branch is not on origin — other machines cannot resume it "
            "until git push"
        )
    out["drift"] = drift

    if cur == target:
        out["status"] = "landed"
        out["landed"] = True
        bits = [f"prior session `{target}` via {resolved.get('via')}"]
        if drift.get("pulled"):
            bits.append("ff-pulled origin")
        if drift.get("diverged"):
            bits.append("diverged from origin — not rewritten")
        if drift.get("blocked_ff"):
            bits.append(str(drift.get("blocked_ff")))
        out["reason"] = "; ".join(bits)
        out["prior_session_branch"] = target
    else:
        out["reason"] = f"wanted `{target}` but checkout is `{cur}`"
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--root", type=Path, default=None)
    args = ap.parse_args(argv)
    root = (args.root or ROOT).resolve()
    data = land(root)
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(
            f"session-resume-land status={data['status']} "
            f"prior={data.get('prior_session_branch')} "
            f"now={data.get('branch_now')} via={data.get('via')} "
            f"switched={data.get('switched')}"
        )
        if data.get("reason"):
            print(data["reason"])
        drift = data.get("drift") or {}
        if drift:
            print(
                "drift: "
                f"ahead={drift.get('ahead')} behind={drift.get('behind')} "
                f"dirty={drift.get('dirty')} diverged={drift.get('diverged')} "
                f"on_origin={drift.get('github_has_branch')} "
                f"pulled={drift.get('pulled')}"
            )
            if drift.get("note"):
                print(drift["note"])
    if data.get("status") == "landed":
        return 0
    if data.get("status") == "redirect_session_start":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
