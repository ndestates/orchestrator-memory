# Shared path helpers for bash tooling (Phase 2).
# Sourced by scan/sync scripts; CLI may export ORCHESTRATOR_TEMPLATE_ROOT.

_orchestrator_template_root() {
  if [[ -n "${ORCHESTRATOR_TEMPLATE_ROOT:-}" ]]; then
    printf '%s\n' "$ORCHESTRATOR_TEMPLATE_ROOT"
    return 0
  fi
  # scripts/_engine/lib.sh -> repo root (or bundled template root)
  (cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
}

_orchestrator_scripts_dir() {
  printf '%s\n' "$(_orchestrator_template_root)/scripts"
}