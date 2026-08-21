#!/usr/bin/env python3
"""Check that template version identity is aligned across mirrors.

Single source of truth: **VERSION** (full identity, e.g. 1.9.1 or 1.9.0-pre.5).

Must match exactly:
  - scripts/orchestrator-template-version  (deployed stamp apps read)
  - package.json version
  - extensions/vscode-orchestrator/package.json version (same product train as CLI)
  - extensions/vscode-orchestrator publishedCliVersion default (one-click install)
  - reports/security/bundle-hashes.json → version (when present)

Documented intentional difference:
  - hatch wheel package version may be **core only** X.Y.Z (see pyproject.toml
    [tool.hatch.version] pattern) — pre-release label stays in VERSION/stamp.

Optional:
  - GitHub latest release tag (network; --remote)
  - Installed pip package (if present)

Usage:
  python3 scripts/check-version-alignment.py
  python3 scripts/check-version-alignment.py --json
  python3 scripts/check-version-alignment.py --remote
  python3 scripts/check-version-alignment.py --fix   # run node scripts/npm/sync-version.js

Exit 0 aligned, 1 misaligned, 2 missing SSOT.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read_version_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        line = path.read_text(encoding="utf-8").strip().splitlines()[0].strip()
        return line.lstrip("v") if line else None
    except OSError:
        return None


def _core(v: str) -> str:
    return re.split(r"[-+]", v.lstrip("v"), maxsplit=1)[0]


def collect() -> dict:
    ver = _read_version_file(ROOT / "VERSION")
    stamp = _read_version_file(ROOT / "scripts" / "orchestrator-template-version")
    pkg = None
    pkg_path = ROOT / "package.json"
    if pkg_path.is_file():
        try:
            pkg = json.loads(pkg_path.read_text(encoding="utf-8")).get("version")
            if isinstance(pkg, str):
                pkg = pkg.lstrip("v")
        except (json.JSONDecodeError, OSError):
            pkg = None
    bundle = None
    bundle_path = ROOT / "reports" / "security" / "bundle-hashes.json"
    if bundle_path.is_file():
        try:
            bundle = json.loads(bundle_path.read_text(encoding="utf-8")).get("version")
            if isinstance(bundle, str):
                bundle = bundle.lstrip("v")
        except (json.JSONDecodeError, OSError):
            bundle = None

    ext_ver = None
    ext_cli_default = None
    ext_pkg_path = ROOT / "extensions" / "vscode-orchestrator" / "package.json"
    if ext_pkg_path.is_file():
        try:
            ext_pkg = json.loads(ext_pkg_path.read_text(encoding="utf-8"))
            ext_ver = ext_pkg.get("version")
            if isinstance(ext_ver, str):
                ext_ver = ext_ver.lstrip("v")
            props = (
                (ext_pkg.get("contributes") or {})
                .get("configuration", {})
                .get("properties")
                or {}
            )
            pub = props.get("orchestrator.publishedCliVersion") or {}
            ext_cli_default = pub.get("default")
            if isinstance(ext_cli_default, str):
                ext_cli_default = ext_cli_default.lstrip("v")
        except (json.JSONDecodeError, OSError, TypeError):
            ext_ver = None
            ext_cli_default = None

    hatch_pattern = None
    pyproject = ROOT / "pyproject.toml"
    if pyproject.is_file():
        m = re.search(
            r'\[tool\.hatch\.version\][^\[]*?pattern\s*=\s*"([^"]+)"',
            pyproject.read_text(encoding="utf-8"),
            re.S,
        )
        if m:
            hatch_pattern = m.group(1)

    pip_ver = None
    try:
        from importlib import metadata

        pip_ver = metadata.version("orchestrator")
    except Exception:
        pass

    return {
        "VERSION": ver,
        "stamp": stamp,
        "package.json": pkg,
        "extension.package.json": ext_ver,
        "extension.publishedCliVersion": ext_cli_default,
        "bundle_hashes.version": bundle,
        "hatch_pattern": hatch_pattern,
        "pip_installed": pip_ver,
        "core_from_VERSION": _core(ver) if ver else None,
    }


def evaluate(data: dict, *, remote: bool = False) -> dict:
    issues: list[str] = []
    warns: list[str] = []
    ver = data.get("VERSION")
    if not ver:
        return {
            "status": "FAIL",
            "issues": ["VERSION file missing or empty — single source of truth required"],
            "warns": [],
            "data": data,
            "line": "version_align=FAIL missing_VERSION",
        }

    for key in ("stamp", "package.json", "extension.package.json"):
        val = data.get(key)
        if val is None:
            # Extension optional only if path missing (template without vscode/)
            if key.startswith("extension.") and not (
                ROOT / "extensions" / "vscode-orchestrator" / "package.json"
            ).is_file():
                continue
            issues.append(f"{key}: missing")
        elif val != ver:
            issues.append(f"{key}: {val!r} != VERSION {ver!r}")

    ext_cli = data.get("extension.publishedCliVersion")
    if ext_cli is not None and ext_cli != ver:
        issues.append(
            f"extension.publishedCliVersion: {ext_cli!r} != VERSION {ver!r} "
            f"(CLI install pin must match product train)"
        )

    bundle = data.get("bundle_hashes.version")
    if bundle is None:
        warns.append("bundle_hashes.version: missing (run orchestrator-bundle-hash.py)")
    elif bundle != ver:
        # Allow core-only if VERSION is pre-release? Prefer exact match.
        if bundle == _core(ver) and ver != _core(ver):
            warns.append(
                f"bundle_hashes.version is core-only {bundle!r} while VERSION is {ver!r} "
                f"— regenerate stamp with full VERSION for apps"
            )
        else:
            issues.append(f"bundle_hashes.version: {bundle!r} != VERSION {ver!r}")

    # Hatch: core-only is intentional when VERSION has pre label
    if data.get("hatch_pattern") and r"\d" in (data.get("hatch_pattern") or ""):
        if ver != _core(ver):
            warns.append(
                f"hatch wheel version is core-only ({_core(ver)}); "
                f"full identity stays in VERSION/stamp ({ver}) — intentional"
            )

    if data.get("pip_installed") and data["pip_installed"] not in (ver, _core(ver)):
        warns.append(
            f"pip installed orchestrator=={data['pip_installed']} "
            f"(repo VERSION={ver}) — reinstall editable if developing CLI"
        )

    if remote:
        try:
            sys.path.insert(0, str(ROOT / "src"))
            from orchestrator_cli.remote_version import fetch_latest_release_version

            r = fetch_latest_release_version()
            if r and r.version:
                data["github_latest"] = r.version
                data["github_source"] = r.source
                if r.version != ver and r.version != _core(ver):
                    # On template source, local can be ahead of release
                    if _is_newer_simple(ver, r.version):
                        warns.append(
                            f"local VERSION {ver} is ahead of GitHub latest {r.version} "
                            f"(release not cut yet?)"
                        )
                    elif _is_newer_simple(r.version, ver):
                        issues.append(
                            f"GitHub latest {r.version} is newer than local VERSION {ver}"
                        )
            else:
                warns.append("github_latest: unreachable or suppressed")
        except Exception as exc:
            warns.append(f"github_latest: {exc}")

    status = "FAIL" if issues else ("WARN" if warns else "PASS")
    line = (
        f"version_align={status} VERSION={ver} "
        f"stamp={data.get('stamp')} pkg={data.get('package.json')} "
        f"ext={data.get('extension.package.json')} "
        f"cli_pin={data.get('extension.publishedCliVersion')} "
        f"bundle={data.get('bundle_hashes.version')}"
    )
    return {
        "status": status,
        "issues": issues,
        "warns": warns,
        "data": data,
        "line": line,
        "ssot": "VERSION",
        "sync_command": "node scripts/npm/sync-version.js && python3 scripts/orchestrator-bundle-hash.py",
    }


def _is_newer_simple(a: str, b: str) -> bool:
    try:
        from packaging.version import Version

        return Version(a.lstrip("v")) > Version(b.lstrip("v"))
    except Exception:
        def core(x: str) -> tuple:
            p = x.lstrip("v").split("-")[0].split(".")
            return tuple(int(n) for n in p[:3] if n.isdigit())

        return core(a) > core(b)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--remote", action="store_true", help="Also compare GitHub latest release")
    ap.add_argument(
        "--fix",
        action="store_true",
        help="Run node scripts/npm/sync-version.js then re-check (does not rewrite bundle)",
    )
    args = ap.parse_args()

    if args.fix:
        sync = ROOT / "scripts" / "npm" / "sync-version.js"
        if sync.is_file():
            subprocess.run(["node", str(sync)], cwd=ROOT, check=False)
        else:
            print("sync-version.js missing", file=sys.stderr)

    data = collect()
    result = evaluate(data, remote=args.remote)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result["line"])
        for i in result.get("issues") or []:
            print(f"  issue: {i}")
        for w in result.get("warns") or []:
            print(f"  warn: {w}")
        if result["status"] != "PASS":
            print(f"  → SSOT: {result['ssot']}")
            print(f"  → fix:  {result['sync_command']}")
        else:
            print("  ✓ VERSION, stamp, package.json, bundle aligned")
            for w in result.get("warns") or []:
                pass  # already printed
    return 0 if result["status"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main())
