#!/usr/bin/env bash
# Set GitHub secrets from a local env file. Never logs values.
set -euo pipefail

ENV_NAME=""
ENV_FILE=""
KEYS=""

usage() {
  cat <<'EOF'
Usage: secrets-sync-from-env.sh --file PATH [--env NAME] --keys K1,K2,...

  --file PATH   Gitignored env file (KEY=value lines)
  --env NAME    Optional GitHub environment (e.g. production)
  --keys LIST   Comma-separated secret names to sync

Values are read from the file and piped to gh secret set. Names only are printed.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env) ENV_NAME="${2:-}"; shift 2 ;;
    --file) ENV_FILE="${2:-}"; shift 2 ;;
    --keys) KEYS="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "error: unknown arg: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -z "$ENV_FILE" || -z "$KEYS" ]]; then
  echo "error: --file and --keys are required" >&2
  usage
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "error: file not found: $ENV_FILE" >&2
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "error: gh CLI required" >&2
  exit 1
fi

# shellcheck disable=SC1090
set -a
source "$ENV_FILE"
set +a

IFS=',' read -ra KEY_ARR <<< "$KEYS"
for key in "${KEY_ARR[@]}"; do
  key="$(echo "$key" | xargs)"
  [[ -z "$key" ]] && continue
  val="${!key-}"
  if [[ -z "$val" ]]; then
    echo "skip: $key (empty or unset in file)" >&2
    continue
  fi
  if [[ -n "$ENV_NAME" ]]; then
    printf '%s' "$val" | gh secret set "$key" --env "$ENV_NAME"
    echo "set: $key (environment: $ENV_NAME)"
  else
    printf '%s' "$val" | gh secret set "$key"
    echo "set: $key (repository)"
  fi
done

echo "done: synced ${#KEY_ARR[@]} key name(s) (values not shown)"