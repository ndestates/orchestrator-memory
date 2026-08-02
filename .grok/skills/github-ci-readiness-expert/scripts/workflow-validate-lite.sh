#!/usr/bin/env bash
# Fallback workflow YAML validation when github-workflow-expert is not deployed.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../../../../" && pwd)"
exec python3 - "$ROOT" <<'PY'
import sys
from pathlib import Path
import yaml

root = Path(sys.argv[1])
wf = root / ".github/workflows"
errors = []
for path in sorted(wf.glob("*.yml")) + sorted(wf.glob("*.yaml")):
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        errors.append(f"{path.name}: {exc}")
        continue
    if not isinstance(data, dict):
        errors.append(f"{path.name}: root must be mapping")
        continue
    if "jobs" not in data:
        errors.append(f"{path.name}: missing jobs")
    else:
        print(f"ok: {path.relative_to(root)}")
if errors:
    for e in errors:
        print(f"  - {e}", file=sys.stderr)
    sys.exit(1)
PY