#!/usr/bin/env bash
# Validate GitHub Actions workflow YAML (syntax + basic structure).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "error: python3 required" >&2
  exit 1
fi

files=()
if [[ $# -eq 0 ]]; then
  shopt -s nullglob
  for f in .github/workflows/*.yml .github/workflows/*.yaml; do
    files+=("$ROOT/$f")
  done
  shopt -u nullglob
  if [[ ${#files[@]} -eq 0 ]]; then
    echo "error: no workflow files found" >&2
    exit 1
  fi
else
  for f in "$@"; do
    if [[ "$f" = /* ]]; then
      files+=("$f")
    else
      files+=("$ROOT/$f")
    fi
  done
fi

python3 - "$ROOT" "${files[@]}" <<'PY'
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("error: PyYAML required (pip install pyyaml)", file=sys.stderr)
    sys.exit(1)

root = Path(sys.argv[1])
errors = []

for arg in sys.argv[2:]:
    path = Path(arg)
    if not path.is_file():
        errors.append(f"{arg}: file not found")
        continue
    try:
        text = path.read_text(encoding="utf-8")
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        errors.append(f"{path}: YAML parse error: {exc}")
        continue
    except OSError as exc:
        errors.append(f"{path}: read error: {exc}")
        continue

    if not isinstance(data, dict):
        errors.append(f"{path}: root must be a mapping")
        continue
    if "name" not in data:
        errors.append(f"{path}: missing top-level 'name'")
    # PyYAML 1.1 parses YAML key `on:` as boolean True
    has_trigger = "on" in data or True in data
    if not has_trigger:
        errors.append(f"{path}: missing top-level 'on' trigger")
    if "jobs" not in data or not isinstance(data.get("jobs"), dict):
        errors.append(f"{path}: missing or invalid 'jobs'")
    else:
        for job_id, job in data["jobs"].items():
            if not isinstance(job, dict):
                errors.append(f"{path}: job '{job_id}' must be a mapping")
                continue
            if "runs-on" not in job and "uses" not in job:
                errors.append(f"{path}: job '{job_id}' needs 'runs-on' or reusable 'uses'")

    print(f"ok: {path.relative_to(root)}")

if errors:
    print("\nvalidation failed:", file=sys.stderr)
    for err in errors:
        print(f"  - {err}", file=sys.stderr)
    sys.exit(1)

print(f"\nvalidated {len(sys.argv) - 2} workflow file(s)")
PY