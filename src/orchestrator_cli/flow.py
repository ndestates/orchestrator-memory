"""Clean-deploy flow: branch → materialize → decontaminate → gate → commit → PR."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from . import gitops
from .engine_bridge import load_engines
from .license import LicenseError
from .licensing_policy import enforce_for_flow, resolve_flow_selections
from .lock import read_lock, write_lock
from .template_root import template_root
from .version import cli_version, is_newer, template_version


class FlowError(RuntimeError):
    pass


@dataclass
class FlowOptions:
    target: Path
    mode: Literal["init", "upgrade"]
    to_version: str | None = None
    profile: str | None = None
    dry_run: bool = False
    no_pr: bool = False
    selections: str | None = None
    verify_bundle: bool = False
    # When set, ORCHESTRATOR_TEMPLATE_ROOT points here for the flow
    template_root_override: Path | None = None
    # Suppress per-file deploy chatter; keep one-line summary + errors
    quiet: bool = False
    # Auto stash (-u) dirty worktree, deploy, then stash pop (app WIP preserved)
    stash: bool = False


@dataclass
class FlowResult:
    ok: bool
    mode: str
    version: str
    branch: str | None = None
    backup_id: str | None = None
    commit: str | None = None
    pr_url: str | None = None
    profile: str | None = None
    errors: list[str] = field(default_factory=list)
    cli_hygiene: dict | None = None
    project_global: dict | None = None
    stats: dict | None = None


def _flow_print(msg: str, *, quiet: bool, force: bool = False, file=None) -> None:
    if force or not quiet or file is sys.stderr:
        print(msg, file=file if file is not None else sys.stdout, flush=True)


def _branch_name(mode: str, version: str) -> str:
    safe = version.lstrip("v").replace(".", "-")
    return f"chore/orchestrator-{mode}-{safe}"


def _rollback_failure(
    target: Path,
    deploy_mod,
    *,
    backup_id: str | None,
    prior_branch: str | None,
    flow_branch: str | None,
    dry_run: bool,
) -> None:
    if dry_run:
        return
    if backup_id:
        deploy_mod.cmd_rollback(target, backup_id, dry_run=False)
    if prior_branch and flow_branch:
        gitops.restore_branch(target, prior_branch, delete_branch=flow_branch)


def run_flow(opts: FlowOptions) -> FlowResult:
    import os

    target = opts.target.resolve()
    prev_template_env = os.environ.get("ORCHESTRATOR_TEMPLATE_ROOT")
    prev_quiet_env = os.environ.get("ORCHESTRATOR_QUIET")
    if opts.template_root_override is not None:
        os.environ["ORCHESTRATOR_TEMPLATE_ROOT"] = str(
            opts.template_root_override.resolve()
        )
    if opts.quiet:
        os.environ["ORCHESTRATOR_QUIET"] = "1"

    try:
        return _run_flow_body(opts, target)
    finally:
        if opts.template_root_override is not None:
            if prev_template_env is None:
                os.environ.pop("ORCHESTRATOR_TEMPLATE_ROOT", None)
            else:
                os.environ["ORCHESTRATOR_TEMPLATE_ROOT"] = prev_template_env
        if opts.quiet:
            if prev_quiet_env is None:
                os.environ.pop("ORCHESTRATOR_QUIET", None)
            else:
                os.environ["ORCHESTRATOR_QUIET"] = prev_quiet_env


def _run_flow_body(opts: FlowOptions, target: Path) -> FlowResult:
    import os

    version = (opts.to_version or template_version()).lstrip("v")
    result = FlowResult(ok=False, mode=opts.mode, version=version)

    if target == template_root().resolve():
        result.errors.append("target cannot be the orchestrator template source repo")
        return result

    # ORCHESTRATOR_QUIET set by run_flow when opts.quiet

    lock = read_lock(target)
    if opts.mode == "init" and lock is not None:
        result.errors.append(
            f"orchestrator already installed ({lock.get('version')}); use `orchestrator upgrade`"
        )
        return result
    if opts.mode == "upgrade" and lock is None:
        result.errors.append("orchestrator not installed; use `orchestrator init`")
        return result
    if opts.mode == "upgrade" and lock and not is_newer(version, str(lock.get("version", "0.0.0"))):
        result.errors.append(f"target already at {lock.get('version')} (requested {version})")
        return result

    if not gitops.is_repo(target):
        result.errors.append("target is not a git repository")
        return result

    stashed = False
    if not opts.dry_run and not gitops.working_tree_clean(target):
        if opts.stash:
            try:
                stashed = gitops.stash_push_including_untracked(
                    target,
                    f"orchestrator: auto-stash before {opts.mode} v{version}",
                )
            except gitops.GitOpsError as exc:
                result.errors.append(f"auto-stash failed: {exc}")
                return result
            if stashed:
                _flow_print(
                    "orchestrator: stashed local changes (-u) for clean deploy "
                    "(will stash pop after)",
                    quiet=opts.quiet,
                )
            if not gitops.working_tree_clean(target):
                result.errors.append(
                    "working tree still dirty after stash — commit or clean ignored blockers"
                )
                return result
        else:
            result.errors.append(
                "working tree is not clean — commit/stash, or re-run with --stash "
                "(auto stash -u, deploy, stash pop)"
            )
            return result

    try:
        entitlement = enforce_for_flow(target)
        flow_selections = resolve_flow_selections(opts.selections, entitlement)
    except LicenseError as exc:
        result.errors.append(f"license check failed: {exc}")
        if stashed:
            try:
                gitops.stash_pop(target)
            except gitops.GitOpsError as pop_exc:
                result.errors.append(f"stash pop after license failure: {pop_exc}")
        return result

    deploy_eng, customize_eng, contamination_eng = load_engines()
    deploy_mod = deploy_eng

    prior_branch: str | None = None
    flow_branch: str | None = None
    backup_id: str | None = None
    # When no_pr: stay on the user's current branch so install persists when they
    # keep working / switch later (commit is on *this* branch, not a disposable chore/*).
    # When PR flow: use chore/* then merge back onto the starting branch before exit.
    apply_on_current = bool(opts.no_pr)

    try:
        if not opts.dry_run:
            prior_branch = gitops.current_branch(target)
            if apply_on_current:
                flow_branch = prior_branch
                result.branch = prior_branch
                _flow_print(
                    f"orchestrator: applying {opts.mode} v{version} on current branch "
                    f"`{prior_branch}` (--no-pr: install persists on this branch)",
                    quiet=opts.quiet,
                )
            else:
                flow_branch = _branch_name(opts.mode, version)
                gitops.create_branch(target, flow_branch)
                result.branch = flow_branch
                _flow_print(
                    f"orchestrator: applying {opts.mode} v{version} on branch "
                    f"`{flow_branch}` (will merge back to `{prior_branch}` after commit)",
                    quiet=opts.quiet,
                )

        # quiet is 1.9.6+; older --from-github materializations lack the kwarg
        import inspect

        deploy_kwargs: dict = {
            "dry_run": opts.dry_run,
            "selections": flow_selections,
            "default_action": "overwrite" if opts.mode == "init" else "skip",
            "non_interactive": True,
            "yes": opts.mode == "init",
            "no_backup": opts.dry_run,
        }
        supports_quiet = False
        try:
            supports_quiet = "quiet" in inspect.signature(deploy_eng.run_deploy).parameters
        except (TypeError, ValueError):
            supports_quiet = False
        if supports_quiet:
            deploy_kwargs["quiet"] = opts.quiet
        prev_q = getattr(deploy_eng, "_QUIET", None)
        if opts.quiet and not supports_quiet and prev_q is not None:
            deploy_eng._QUIET = True  # type: ignore[attr-defined]
        try:
            deploy_result = deploy_eng.run_deploy(target, **deploy_kwargs)
        finally:
            if opts.quiet and not supports_quiet and prev_q is not None:
                deploy_eng._QUIET = prev_q  # type: ignore[attr-defined]
        backup_id = deploy_result.get("backup_id")
        result.backup_id = backup_id
        result.stats = deploy_result.get("stats")

        profile = opts.profile
        if not profile:
            profile = customize_eng.resolve_profile(target, None, auto=True)
        if not profile:
            # Heuristic so check/upgrade dry-runs work without a full manifest
            if (target / "artisan").is_file() and (target / "composer.json").is_file():
                profile = "laravel"
            elif (target / "composer.json").is_file() and (
                target / "app"
            ).is_dir():  # Laravel-ish without artisan present
                profile = "laravel"
            elif (target / "requirements.txt").is_file() or (
                target / "pyproject.toml"
            ).is_file():
                profile = "python-flask"
            elif opts.dry_run:
                profile = "laravel"
                _flow_print(
                    "orchestrator: dry-run: no stack.profile — using profile=laravel "
                    "(pass --profile for a real apply)",
                    quiet=opts.quiet,
                )
            else:
                raise FlowError(
                    "could not resolve stack profile — pass --profile "
                    "(e.g. laravel, python-flask) or set stack.profile in project-manifest.yaml"
                )
            if opts.dry_run and profile:
                _flow_print(
                    f"orchestrator: using inferred profile={profile}",
                    quiet=opts.quiet,
                )
        result.profile = profile

        # Project-manifest policy: never overwrite customized manifests; seed/amend
        # stack-aware identity for new projects (or template residue only).
        try:
            from _engine.manifest_bootstrap import ensure_project_manifest
        except ImportError:
            # Template scripts/ on PYTHONPATH via engine_bridge
            sys.path.insert(0, str(template_root() / "scripts"))
            from _engine.manifest_bootstrap import ensure_project_manifest  # type: ignore

        manifest_result = ensure_project_manifest(
            target,
            profile_id=profile,
            mode=opts.mode,
            dry_run=opts.dry_run,
            amend_residue=True,
        )
        action = manifest_result.get("action")
        note = manifest_result.get("note") or ""
        _flow_print(
            f"orchestrator: project-manifest {action}"
            + (f" — {note}" if note else ""),
            quiet=opts.quiet,
        )
        if action == "preserved":
            _flow_print(
                "orchestrator: existing project-manifest not overwritten by template",
                quiet=opts.quiet,
            )

        customize_eng.run_customize(
            target,
            profile,
            dry_run=opts.dry_run,
            sync=not opts.dry_run,
        )

        if not opts.dry_run:
            slug = target.name
            contam_kwargs: dict = {}
            try:
                import inspect as _insp

                if "quiet" in _insp.signature(contamination_eng.run).parameters:
                    contam_kwargs["quiet"] = opts.quiet
            except (TypeError, ValueError):
                pass
            rc = contamination_eng.run(target, slug, **contam_kwargs)
            if rc != 0:
                raise FlowError(f"contamination gate failed (exit {rc})")

            if opts.verify_bundle:
                _verify_bundle_against_template(target)

            # Host CLI hygiene: reinstall so pip metadata matches template VERSION
            # (avoids "orchestrator 1.9.1 (template 1.9.2)" after upgrade).
            from .cli_hygiene import refresh_host_cli

            hygiene = refresh_host_cli(version=version)
            result.cli_hygiene = hygiene
            _flow_print(
                f"orchestrator: {hygiene.get('message') or 'CLI hygiene done'}",
                quiet=opts.quiet,
            )

            write_lock(
                target,
                version=version,
                release_tag=f"v{version}",
                profile=profile,
                cli_version=cli_version(),
                installed_at=datetime.now(timezone.utc).isoformat(),
            )

            msg = (
                f"chore(orchestrator): {opts.mode} template v{version} "
                f"(profile={profile})"
            )
            result.commit = gitops.commit_all(target, msg)

            # PR path: merge chore/* into the branch the user started on, then
            # checkout that branch so switching/continuing keeps orchestrator files.
            if (
                not apply_on_current
                and prior_branch
                and flow_branch
                and prior_branch != flow_branch
            ):
                gitops.merge_into_branch(
                    target,
                    source_branch=flow_branch,
                    dest_branch=prior_branch,
                )
                result.branch = prior_branch
                _flow_print(
                    f"orchestrator: merged `{flow_branch}` into `{prior_branch}` "
                    f"and checked out `{prior_branch}` so install persists",
                    quiet=opts.quiet,
                )

            # Project-global install: baseline branch + broadcast to all local
            # branches + post-checkout hook (user does not manage per-branch).
            from .project_install import project_global_install

            global_rep = project_global_install(target)
            result.project_global = global_rep
            _flow_print(
                f"orchestrator: {global_rep.get('message') or 'project-global install done'}",
                quiet=opts.quiet,
            )

            if not opts.no_pr and flow_branch:
                base = gitops.detect_default_base(target)
                title = f"chore(orchestrator): {opts.mode} template v{version}"
                body = (
                    f"Automated orchestrator `{opts.mode}` via CLI.\n\n"
                    f"- Version: v{version}\n"
                    f"- Profile: {profile}\n"
                    f"- Backup: {backup_id or 'none'}\n"
                    f"- Applied on: `{prior_branch or flow_branch}` "
                    f"(chore branch `{flow_branch}` when used)\n"
                )
                # PR head: prefer chore branch if it exists; else current
                pr_head = flow_branch if flow_branch else result.branch
                result.pr_url = gitops.try_create_pr(
                    target,
                    title=title,
                    body=body,
                    head_branch=pr_head or prior_branch or "HEAD",
                    base=base,
                )

        result.ok = True

    except (FlowError, gitops.GitOpsError, ValueError) as exc:
        result.errors.append(str(exc))
        _rollback_failure(
            target,
            deploy_mod,
            backup_id=backup_id,
            prior_branch=prior_branch,
            flow_branch=flow_branch,
            dry_run=opts.dry_run,
        )
    except Exception as exc:  # pragma: no cover
        result.errors.append(f"unexpected error: {exc}")
        _rollback_failure(
            target,
            deploy_mod,
            backup_id=backup_id,
            prior_branch=prior_branch,
            flow_branch=flow_branch,
            dry_run=opts.dry_run,
        )
    finally:
        if stashed:
            try:
                gitops.stash_pop(target)
                _flow_print(
                    "orchestrator: restored stashed local changes (stash pop)",
                    quiet=opts.quiet,
                )
            except gitops.GitOpsError as pop_exc:
                result.errors.append(
                    f"deploy finished but stash pop failed: {pop_exc} "
                    f"— run: git -C {target} stash list"
                )
                # keep ok if deploy succeeded; surface pop issue as error too
                if result.ok:
                    result.ok = False
    return result


def _verify_bundle_against_template(target: Path) -> None:
    """Phase 2: verify high-risk files match the template stamp after deploy."""
    root = template_root()
    stamp = root / "reports/security/bundle-hashes.json"
    script = root / "scripts/orchestrator-bundle-hash.py"
    if not script.is_file():
        raise FlowError("bundle hash script missing in template — cannot --verify-bundle")
    if not stamp.is_file():
        raise FlowError(
            f"bundle stamp missing at {stamp} — run: "
            "python3 scripts/orchestrator-bundle-hash.py generate"
        )
    # Verify the *template* stamp integrity first (source of truth).
    proc = subprocess.run(
        [sys.executable, str(script), "verify", "--root", str(root), "--stamp", str(stamp)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise FlowError(
            "template bundle stamp verification failed — refuse upgrade with --verify-bundle\n"
            + (proc.stdout or proc.stderr or "")[:500]
        )
    # Compare overlapping high-risk paths that were deployed into the target.
    try:
        stamp_data = json.loads(stamp.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise FlowError(f"cannot read bundle stamp: {exc}") from exc

    mismatches: list[str] = []
    for rel, expected in (stamp_data.get("files") or {}).items():
        tp = target / rel
        if not tp.is_file():
            # Selection may omit some paths — skip missing rather than fail.
            continue
        h = hashlib.sha256(tp.read_bytes()).hexdigest()
        if h != expected:
            mismatches.append(rel)
    if mismatches:
        raise FlowError(
            "bundle hash mismatch on target after deploy: " + ", ".join(mismatches[:12])
        )


def _materialize_from_github(tag: str | None) -> tuple[Path, str]:
    """Return (template_root_path, version) after fetching GitHub release."""
    from .github_materialize import materialize_github_release

    mat = materialize_github_release(tag)
    print(
        f"orchestrator: GitHub template {mat.tag} → {mat.path} ({mat.source})",
        flush=True,
    )
    return mat.path, mat.version


def run_init(
    target: Path,
    *,
    to_version: str | None = None,
    profile: str | None = None,
    selections: str | None = None,
    dry_run: bool = False,
    no_pr: bool = False,
    verify_bundle: bool = False,
    from_github: str | bool | None = None,
    quiet: bool = False,
    stash: bool = False,
) -> int:
    template_override: Path | None = None
    if from_github is not None and from_github is not False:
        tag = None if from_github is True else str(from_github)
        template_override, gh_ver = _materialize_from_github(tag)
        to_version = to_version or gh_ver
    result = run_flow(
        FlowOptions(
            target=target,
            mode="init",
            to_version=to_version,
            profile=profile,
            selections=selections,
            dry_run=dry_run,
            no_pr=no_pr,
            verify_bundle=verify_bundle,
            template_root_override=template_override,
            quiet=quiet,
            stash=stash,
        )
    )
    return _emit_result(result)


def run_upgrade(
    target: Path,
    *,
    to_version: str | None = None,
    profile: str | None = None,
    selections: str | None = None,
    dry_run: bool = False,
    no_pr: bool = False,
    verify_bundle: bool = False,
    if_available: bool = False,
    yes: bool = False,
    from_github: str | bool | None = None,
    quiet: bool = False,
    stash: bool = False,
) -> int:
    """Upgrade target project.

    ``if_available``: no-op (exit 0) when already current; exit 3 if not installed.
    With ``if_available`` and without ``yes``, force dry-run (safe default).
    ``yes``: apply for real when combined with ``if_available``.
    ``from_github``: True/latest or a tag (``v1.8.5``) — fetch release into cache
    and use it as the template root.
    """
    from . import update_check

    import os

    target = target.resolve()
    template_override: Path | None = None

    # Materialize GitHub first so evaluate/if-available sees the right version
    if from_github is not None and from_github is not False:
        tag = None if from_github is True else str(from_github)
        template_override, gh_ver = _materialize_from_github(tag)
        to_version = to_version or gh_ver

    if if_available:
        prev_env = os.environ.get("ORCHESTRATOR_TEMPLATE_ROOT")
        if template_override is not None:
            os.environ["ORCHESTRATOR_TEMPLATE_ROOT"] = str(template_override.resolve())
        try:
            notice = update_check.evaluate(target)
        finally:
            if template_override is not None:
                if prev_env is None:
                    os.environ.pop("ORCHESTRATOR_TEMPLATE_ROOT", None)
                else:
                    os.environ["ORCHESTRATOR_TEMPLATE_ROOT"] = prev_env

        if notice.kind == update_check.UpdateKind.UP_TO_DATE:
            print(notice.message or f"orchestrator: already up to date at {notice.installed}")
            return 0
        if notice.kind in (
            update_check.UpdateKind.SKIPPED,
            update_check.UpdateKind.TEMPLATE_SOURCE,
        ):
            print(
                notice.message
                or f"orchestrator: nothing to upgrade for {target} ({notice.kind.value})"
            )
            return 0
        if notice.kind == update_check.UpdateKind.NOT_INSTALLED:
            print(notice.message)
            if notice.action:
                print(f"  → {notice.action}")
            return 3
        if notice.kind == update_check.UpdateKind.UPGRADE_AVAILABLE:
            if not to_version:
                to_version = notice.available
            print(notice.message)
            if not yes and not dry_run:
                dry_run = True
                print(
                    "orchestrator: --if-available without --yes → dry-run only "
                    "(re-run with --yes to apply)"
                )
            if yes:
                dry_run = False
        else:
            print(f"orchestrator: unexpected check kind {notice.kind.value}")
            return 2
    elif from_github is not None and from_github is not False and not yes and not dry_run:
        # Safe default: GitHub path without --yes is dry-run
        dry_run = True
        print(
            "orchestrator: --from-github without --yes → dry-run only "
            "(re-run with --yes to apply)",
            flush=True,
        )
    if yes:
        dry_run = False

    result = run_flow(
        FlowOptions(
            target=target,
            mode="upgrade",
            to_version=to_version,
            profile=profile,
            selections=selections,
            dry_run=dry_run,
            no_pr=no_pr,
            verify_bundle=verify_bundle,
            template_root_override=template_override,
            quiet=quiet,
            stash=stash,
        )
    )
    return _emit_result(result)


def _emit_result(result: FlowResult) -> int:
    if result.ok:
        parts = [f"orchestrator {result.mode} v{result.version} ok"]
        if result.branch:
            parts.append(f"branch={result.branch}")
        if result.commit:
            parts.append(f"commit={result.commit}")
        if result.pr_url:
            parts.append(f"pr={result.pr_url}")
        elif result.branch:
            parts.append("(PR not created — gh unavailable or --no-pr)")
        st = result.stats or {}
        if st:
            parts.append(
                "stats="
                f"new={st.get('new', 0)},"
                f"upd={st.get('updated', 0)},"
                f"skip={st.get('skipped', 0)},"
                f"conflict={st.get('conflict', 0)}"
            )
        hy = result.cli_hygiene or {}
        if hy.get("ok"):
            parts.append(f"cli_hygiene=ok({hy.get('metadata_after')})")
        elif hy.get("skipped"):
            parts.append("cli_hygiene=skipped")
        elif hy.get("ran"):
            parts.append("cli_hygiene=warn")
        print(" ".join(parts))
        return 0
    for err in result.errors:
        print(f"ERROR: {err}", file=sys.stderr)
    return 1