#!/usr/bin/env bash
# Idempotent promotion PR helpers for branch-promotion-prs.yml.
# Usage:
#   branch-promotion-pr.sh find-existing <repo> <owner> <source> <target>
#   branch-promotion-pr.sh create <repo> <owner> <source> <target> [--draft]
set -euo pipefail

cmd="${1:-}"
shift || true

head_ref() {
  local _owner="$1" source="$2"
  # Same-repo PRs: gh pr list/create --head expects the branch name only.
  # owner:branch is for cross-fork heads; using it here makes find-existing miss open PRs.
  printf '%s' "$source"
}

find_existing() {
  local repo="$1" owner="$2" source="$3" target="$4"
  local head
  head="$(head_ref "$owner" "$source")"
  gh pr list --repo "$repo" --state open --base "$target" --head "$head" \
    --json url --jq '.[0].url // ""'
}

create_promotion_pr() {
  local repo="$1" owner="$2" source="$3" target="$4"
  local draft_flag="${5:-}"
  local head body_file output url

  head="$(head_ref "$owner" "$source")"
  body_file="$(mktemp)"
  # Capture path at trap-install time — local body_file is out of scope when EXIT
  # fires after the function returns, which breaks under set -u (nounset).
  trap "rm -f '${body_file}'" EXIT

  {
    printf '%s\n' \
      "Automated branch promotion PR from \`${source}\` to \`${target}\`." \
      "" \
      "Promotion pipeline: \`feature/*\` → \`develop\` → \`master\` (production)." \
      "" \
      "Validation:" \
      "- Branch protection rules apply on the target branch." \
      "- Merge after required checks and approvals pass."
  } >"$body_file"

  set +e
  output="$(gh pr create \
    --repo "$repo" \
    --base "$target" \
    --head "$head" \
    --title "chore(sync): promote ${source} to ${target}" \
    --body-file "$body_file" \
    $draft_flag 2>&1)"
  local exit_code=$?
  set -e

  if [[ $exit_code -eq 0 ]]; then
    echo "$output"
    return 0
  fi

  if echo "$output" | grep -qi 'already exists'; then
    url="$(find_existing "$repo" "$owner" "$source" "$target")"
    if [[ -n "$url" ]]; then
      echo "REUSED $url" >&2
      echo "$url"
      return 0
    fi
  fi

  echo "$output" >&2
  return "$exit_code"
}

case "$cmd" in
  find-existing)
    [[ $# -eq 4 ]] || { echo "usage: find-existing <repo> <owner> <source> <target>" >&2; exit 2; }
    find_existing "$@"
    ;;
  create)
    [[ $# -ge 4 ]] || { echo "usage: create <repo> <owner> <source> <target> [--draft]" >&2; exit 2; }
    repo="$1" owner="$2" source="$3" target="$4"
    shift 4
    create_promotion_pr "$repo" "$owner" "$source" "$target" "$*"
    ;;
  -h|--help)
    sed -n '2,5p' "$0"
    exit 0
    ;;
  *)
    echo "unknown command: $cmd" >&2
    exit 2
    ;;
esac