"""Materialize an orchestrator release from GitHub into a local cache.

Used by ``orchestrator upgrade --from-github`` so apps can upgrade without a
sibling monorepo checkout. Prefers git clone (token-aware); falls back to
tarball download.

Cache: ``$ORCHESTRATOR_CACHE/releases/<version>`` (default ``~/.cache/orchestrator``).
"""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .remote_version import (
    RemoteVersion,
    _api_base,
    _repo,
    _timeout,
    _token,
    fetch_latest_release_version,
)


@dataclass(frozen=True)
class MaterializedRelease:
    version: str
    tag: str
    path: Path
    source: str


def cache_root() -> Path:
    raw = (os.environ.get("ORCHESTRATOR_CACHE") or "").strip()
    if raw:
        base = Path(raw).expanduser()
    else:
        base = Path.home() / ".cache" / "orchestrator"
    return (base / "releases").resolve()


def _headers() -> dict[str, str]:
    h = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "orchestrator-cli-github-materialize",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = _token()
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def resolve_release(tag: str | None = None) -> RemoteVersion:
    """Resolve *tag* (``v1.8.5`` / ``1.8.5`` / None=latest) to a RemoteVersion."""
    if tag is None or str(tag).strip().lower() in ("", "latest"):
        latest = fetch_latest_release_version()
        if latest is None:
            raise RuntimeError(
                "Could not resolve latest GitHub release "
                f"(repo={_repo()}). Set GITHUB_TOKEN for private repos, "
                "or pass an explicit tag: --from-github v1.8.5"
            )
        return latest

    raw = str(tag).strip()
    ver = raw.lstrip("v")
    tag_name = raw if raw.startswith("v") else f"v{ver}"
    # Validate tag exists when possible
    url = f"{_api_base()}/repos/{_repo()}/releases/tags/{tag_name}"
    req = urllib.request.Request(url, headers=_headers(), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=_timeout()) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        if isinstance(data, dict) and data.get("tag_name"):
            t = str(data["tag_name"]).strip()
            return RemoteVersion(version=t.lstrip("v"), source=f"github:tag:{t}", tag=t)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, OSError):
        # Tag may still exist as a git ref without a formal Release object
        pass
    return RemoteVersion(
        version=ver,
        source=f"github:ref:{tag_name}",
        tag=tag_name,
    )


def _is_valid_root(path: Path) -> bool:
    return (path / "scripts" / "deploy-bundle.yaml").is_file() and (
        path / "VERSION"
    ).is_file()


def _git_clone(tag: str, dest: Path) -> None:
    repo = _repo()
    token = _token()
    if token:
        url = f"https://x-access-token:{token}@github.com/{repo}.git"
    else:
        url = f"https://github.com/{repo}.git"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    cmd = [
        "git",
        "clone",
        "--depth",
        "1",
        "--branch",
        tag,
        url,
        str(dest),
    ]
    # Hide token in error paths: run without shell
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    if proc.returncode != 0:
        # scrub token from stderr
        err = (proc.stderr or proc.stdout or "").replace(token or "", "***")
        raise RuntimeError(f"git clone failed for {tag}: {err[:500]}")


def _tarball_extract(tag: str, dest: Path) -> None:
    repo = _repo()
    # codeload prefers this shape
    url = f"https://codeload.github.com/{repo}/tar.gz/refs/tags/{tag}"
    headers = {"User-Agent": "orchestrator-cli-github-materialize"}
    token = _token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=max(_timeout(), 60.0)) as resp:
            blob = resp.read()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"tarball download failed for {tag}: {exc}") from exc

    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    with tempfile.TemporaryDirectory(prefix="orch-gh-") as tmp:
        tmp_path = Path(tmp)
        with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tf:
            tf.extractall(tmp_path)
        # GitHub tarballs extract to owner-repo-sha/
        children = [p for p in tmp_path.iterdir() if p.is_dir()]
        if not children:
            raise RuntimeError("tarball contained no directory")
        shutil.move(str(children[0]), str(dest))


def materialize_github_release(
    tag: str | None = None,
    *,
    force: bool = False,
) -> MaterializedRelease:
    """Download/clone release into cache; return path usable as template root."""
    rel = resolve_release(tag)
    tag_name = rel.tag or f"v{rel.version}"
    dest = cache_root() / rel.version

    if dest.is_dir() and _is_valid_root(dest) and not force:
        return MaterializedRelease(
            version=rel.version,
            tag=tag_name,
            path=dest,
            source=f"cache:{dest}",
        )

    errors: list[str] = []
    try:
        _git_clone(tag_name, dest)
        if _is_valid_root(dest):
            return MaterializedRelease(
                version=rel.version,
                tag=tag_name,
                path=dest,
                source=f"git:{_repo()}@{tag_name}",
            )
        errors.append("git clone produced invalid template root")
    except Exception as exc:  # noqa: BLE001 — try tarball fallback
        errors.append(f"git: {exc}")

    try:
        _tarball_extract(tag_name, dest)
        if _is_valid_root(dest):
            return MaterializedRelease(
                version=rel.version,
                tag=tag_name,
                path=dest,
                source=f"tarball:{_repo()}@{tag_name}",
            )
        errors.append("tarball produced invalid template root")
    except Exception as exc:  # noqa: BLE001
        errors.append(f"tarball: {exc}")

    raise RuntimeError(
        "Failed to materialize GitHub release "
        f"{tag_name} for {_repo()}: " + " | ".join(errors)
    )
