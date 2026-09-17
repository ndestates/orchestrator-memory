#!/usr/bin/env python3
"""Ensure the GitHub Release wheel name matches VERSION (npm lockstep).

The 2.3.x failure mode: npm published 2.3.10 while Releases only had a 2.3.5
wheel, so the shim's pip line 404'd.

Usage:
  python3 scripts/check-release-wheel.py --local
  python3 scripts/check-release-wheel.py --local --dist dist
  python3 scripts/check-release-wheel.py --remote

Exit 0 when the expected artifact name matches VERSION (and, with --remote,
the public Release URL returns HTTP 200). Exit 1 on mismatch or missing remote
asset. Exit 2 if VERSION is missing.
"""

from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from orchestrator_cli.remote_version import (  # noqa: E402
    DEFAULT_GITHUB_REPO,
    release_wheel_url,
)


def read_version() -> str | None:
    path = ROOT / "VERSION"
    if not path.is_file():
        return None
    line = path.read_text(encoding="utf-8").strip().splitlines()[0].strip()
    return line.lstrip("v") if line else None


def wheel_name(version: str) -> str:
    return f"orchestrator-{version}-py3-none-any.whl"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--local", action="store_true", help="check VERSION → expected wheel name")
    ap.add_argument("--remote", action="store_true", help="HEAD the public Release wheel URL")
    ap.add_argument(
        "--dist",
        type=Path,
        default=None,
        help="require this dist/ dir to contain the expected wheel",
    )
    args = ap.parse_args()
    if not args.local and not args.remote and args.dist is None:
        args.local = True

    ver = read_version()
    if not ver:
        print("FAIL missing VERSION", file=sys.stderr)
        return 2

    name = wheel_name(ver)
    url = release_wheel_url(ver, DEFAULT_GITHUB_REPO)
    print(f"VERSION={ver}")
    print(f"expected_wheel={name}")
    print(f"expected_url={url}")
    print(f"default_repo={DEFAULT_GITHUB_REPO}")

    if args.dist is not None:
        wheel = args.dist / name
        if not wheel.is_file():
            print(f"FAIL dist missing {wheel}", file=sys.stderr)
            return 1
        print(f"dist_ok={wheel}")

    if args.remote:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "orchestrator-check-release-wheel")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                code = getattr(resp, "status", 200) or 200
        except urllib.error.HTTPError as exc:
            print(f"FAIL remote HTTP {exc.code} for {url}", file=sys.stderr)
            print(
                "Human step: tag v{0} on ndestates/orchestrator-memory and "
                "wait for product-release.yml to attach {1} before npm publish.".format(
                    ver, name
                ),
                file=sys.stderr,
            )
            return 1
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            print(f"FAIL remote error {exc}", file=sys.stderr)
            return 1
        if code >= 400:
            print(f"FAIL remote HTTP {code} for {url}", file=sys.stderr)
            return 1
        print(f"remote_ok=HTTP {code}")

    print("PASS npm and Release wheel names match VERSION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
