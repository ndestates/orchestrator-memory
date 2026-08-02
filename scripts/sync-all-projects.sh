#!/usr/bin/env bash
# sync-all-projects.sh — reconcile every git repo under a root with its remote.
#
# Multi-machine hygiene: at session start (daily-standup / session-start) and
# before an orchestrator deploy, pull work that was pushed from another machine
# so no project drifts behind its remote.
#
# Policy (per repo, current tracked branch only — never auto-checkout):
#   clean + behind + fast-forwardable -> git pull --ff-only        (AUTO)
#   diverged (ahead AND behind)       -> WARN, no change (rebase/merge needed)
#   dirty working tree + behind       -> WARN, no change (stash/commit first)
#   ahead only (unpushed)             -> note
#   no upstream / detached            -> note
# Fetch is always read-only. Only fast-forwards mutate; nothing is clobbered.
#
# Usage: sync-all-projects.sh [ROOT] [--report-only] [--strict]
#   ROOT          default: $HOME/projects
#   --report-only fetch + report, never pull (safest)
#   --strict      exit 1 if any repo needs attention (diverged/dirty/ahead)
#
# Exit 0 normally (per-repo failures are reported, not fatal); 1 under --strict
# when attention is needed.
set -uo pipefail

ROOT="${HOME}/projects"
REPORT_ONLY=0
STRICT=0
for arg in "$@"; do
  case "$arg" in
    --report-only) REPORT_ONLY=1 ;;
    --strict) STRICT=1 ;;
    -*) ;;
    *) ROOT="$arg" ;;
  esac
done

if [[ ! -d "$ROOT" ]]; then
  echo "sync-all-projects: root not found: $ROOT" >&2
  exit 0
fi

pulled=0 attention=0 clean=0 total=0
declare -a NEEDS_ATTENTION=()

printf '%-26s %-26s %s\n' "PROJECT" "BRANCH" "STATUS"
printf '%-26s %-26s %s\n' "-------" "------" "------"

for dir in "$ROOT"/*/; do
  repo="${dir%/}"
  git -C "$repo" rev-parse --git-dir >/dev/null 2>&1 || continue
  name="$(basename "$repo")"
  total=$((total + 1))

  git -C "$repo" fetch --prune --quiet 2>/dev/null || true

  branch="$(git -C "$repo" symbolic-ref --short -q HEAD || echo 'DETACHED')"
  upstream="$(git -C "$repo" rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || echo '')"
  dirty=0
  [[ -n "$(git -C "$repo" status --porcelain)" ]] && dirty=1

  if [[ "$branch" == "DETACHED" ]]; then
    status="⚠ detached HEAD — checkout a branch"
    attention=$((attention + 1)); NEEDS_ATTENTION+=("$name: detached HEAD")
  elif [[ -z "$upstream" ]]; then
    status="• no upstream (local-only branch)"
  else
    counts="$(git -C "$repo" rev-list --left-right --count '@{u}...HEAD' 2>/dev/null || echo '0	0')"
    behind="$(echo "$counts" | awk '{print $1}')"
    ahead="$(echo "$counts" | awk '{print $2}')"

    if [[ "$behind" -gt 0 && "$ahead" -gt 0 ]]; then
      status="⚠ DIVERGED (ahead $ahead / behind $behind) — rebase or merge"
      attention=$((attention + 1)); NEEDS_ATTENTION+=("$name [$branch]: diverged ahead $ahead / behind $behind")
    elif [[ "$behind" -gt 0 && "$dirty" -eq 1 ]]; then
      status="⚠ behind $behind + DIRTY — stash/commit then pull"
      attention=$((attention + 1)); NEEDS_ATTENTION+=("$name [$branch]: behind $behind with uncommitted changes")
    elif [[ "$behind" -gt 0 ]]; then
      if [[ "$REPORT_ONLY" -eq 1 ]]; then
        status="↓ behind $behind (ff-able) — run pull"
        attention=$((attention + 1)); NEEDS_ATTENTION+=("$name [$branch]: behind $behind (ff-able)")
      elif git -C "$repo" pull --ff-only --quiet 2>/dev/null; then
        status="✓ PULLED (ff +$behind)"
        pulled=$((pulled + 1))
      else
        status="⚠ behind $behind — ff pull failed (inspect)"
        attention=$((attention + 1)); NEEDS_ATTENTION+=("$name [$branch]: behind $behind, ff pull failed")
      fi
    elif [[ "$ahead" -gt 0 ]]; then
      status="↑ ahead $ahead (unpushed)"
      [[ "$STRICT" -eq 1 ]] && { attention=$((attention + 1)); NEEDS_ATTENTION+=("$name [$branch]: $ahead unpushed"); }
    else
      status="✓ up to date"
      clean=$((clean + 1))
    fi
  fi
  [[ "$dirty" -eq 1 && "$status" != *DIRTY* ]] && status="$status  (working tree dirty)"
  printf '%-26s %-26s %s\n' "$name" "$branch" "$status"
done

echo
echo "Summary: $total repos · $clean up-to-date · $pulled pulled · $attention need attention"
if [[ "${#NEEDS_ATTENTION[@]}" -gt 0 ]]; then
  echo "Attention:"
  for item in "${NEEDS_ATTENTION[@]}"; do echo "  - $item"; done
fi

[[ "$STRICT" -eq 1 && "$attention" -gt 0 ]] && exit 1
exit 0
