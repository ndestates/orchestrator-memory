#!/usr/bin/env bash
# Session-start runtime + MCP transport detection for orchestrator template and app repos.
#
# Resolves how to run project tooling and which MCP server Grok/Cursor should use:
#   ddev            → orchestrator-ddev (stdio inside DDEV web container)
#   docker-compose  → orchestrator-host for cache/MCP reads; app cmds via compose exec
#   local           → orchestrator-host (template repo, no .ddev/)
#
# Also emits:
#   - MCP develop-only policy (never public/production hosts)
#   - Start options when mcp_ready is not yes
#   - Optional: --with-manifest-identity to run check-project-manifest
#
# Usage: bash scripts/detect-project-runtime.sh [--json] [--with-manifest-identity]
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT"

JSON=0
WITH_IDENTITY=0
for arg in "$@"; do
  case "$arg" in
    --json) JSON=1 ;;
    --with-manifest-identity) WITH_IDENTITY=1 ;;
  esac
done

manifest_env=""
manifest_file=""
for mf in .grok/project-manifest.yaml .github/project-manifest.yaml .claude/project-manifest.yaml; do
  if [[ -f "$mf" ]]; then
    manifest_file="$mf"
    manifest_env="$(grep -E '^\s*environment_manager:\s*' "$mf" | head -1 | sed -E 's/.*:\s*"?([^"#]+)"?.*/\1/' | tr -d ' "')"
    break
  fi
done

has_ddev=0
has_compose=0
has_mcp_server=0
ddev_project=""
compose_file=""
[[ -f .ddev/config.yaml ]] && has_ddev=1
if [[ -f compose.yaml ]]; then
  has_compose=1
  compose_file="compose.yaml"
elif [[ -f docker-compose.yml ]]; then
  has_compose=1
  compose_file="docker-compose.yml"
elif [[ -f docker-compose.yaml ]]; then
  has_compose=1
  compose_file="docker-compose.yaml"
fi
[[ -d mcp-server/src/orchestrator_mcp ]] && has_mcp_server=1
[[ "$has_ddev" -eq 1 ]] && ddev_project="$(awk '/^name:/{print $2; exit}' .ddev/config.yaml 2>/dev/null || true)"

runtime="local"
if [[ "$manifest_env" == "ddev" ]]; then
  runtime="ddev"
elif [[ "$manifest_env" == "docker-compose" ]]; then
  runtime="docker-compose"
elif [[ "$has_ddev" -eq 1 ]]; then
  runtime="ddev"
elif [[ "$has_compose" -eq 1 ]]; then
  runtime="docker-compose"
fi

mcp_grok_id="none"
mcp_launcher="none"
mcp_ready="no"
mcp_note=""
ddev_running="n/a"
compose_running="n/a"
app_commands_via="$runtime"
grok_config_hint=""

case "$runtime" in
  ddev)
    mcp_grok_id="orchestrator-ddev"
    mcp_launcher="scripts/mcp-ddev-stdio.sh"
    grok_config_hint="Enable [mcp_servers.orchestrator-ddev] in .grok/config.toml; disable orchestrator-host (see mcp-server/config/mcp.grok.project.example.toml)"
    if [[ "$has_mcp_server" -eq 0 ]]; then
      mcp_note="mcp-server/ missing — deploy with --selections mcp or deploy-mcp-wave.sh"
    elif ! command -v ddev >/dev/null 2>&1; then
      mcp_note="ddev not on PATH — install DDEV for local app work"
    else
      ddev_running="no"
      if ddev describe >/dev/null 2>&1; then
        ddev_running="yes"
      elif [[ -n "$ddev_project" ]] && ddev describe "$ddev_project" >/dev/null 2>&1; then
        ddev_running="yes"
      fi
      if [[ "$ddev_running" == "yes" ]]; then
        if ddev exec python3 -c "import mcp" >/dev/null 2>&1; then
          mcp_ready="yes"
        else
          mcp_note="MCP Python deps missing in DDEV — cp mcp-server/ddev/Dockerfile.mcp .ddev/web-build/ && ddev restart"
        fi
      else
        mcp_ready="pending"
        mcp_note="DDEV not running — offer: ddev start (mcp-ddev-stdio.sh can also start on first MCP connect)"
      fi
    fi
    app_commands_via="ddev exec"
    ;;
  docker-compose)
    mcp_grok_id="orchestrator-host"
    mcp_launcher="scripts/mcp-host-stdio.sh"
    grok_config_hint="Enable [mcp_servers.orchestrator-host] in .grok/config.toml (cache reads from host PROJECT_ROOT)"
    compose_running="no"
    if command -v docker >/dev/null 2>&1 && [[ -n "$compose_file" ]]; then
      if docker compose -f "$compose_file" ps -q 2>/dev/null | grep -q .; then
        compose_running="yes"
      fi
    fi
    if [[ "$has_mcp_server" -eq 0 ]]; then
      mcp_note="mcp-server/ missing at repo root"
    else
      # Auto-repair host venv so session-start / first connect do not fail
      if [[ -f scripts/ensure-mcp-host.sh ]] && bash scripts/ensure-mcp-host.sh --quiet 2>/dev/null; then
        mcp_ready="yes"
      elif [[ -x mcp-server/.venv/bin/orchestrator-mcp ]]; then
        mcp_ready="pending"
        mcp_note="Host MCP binary present but imports unhealthy — bash scripts/ensure-mcp-host.sh --force"
      else
        mcp_ready="pending"
        mcp_note="Host MCP not ready — bash scripts/ensure-mcp-host.sh (needs uv or python3-venv)"
      fi
    fi
    app_commands_via="docker compose exec (service from $compose_file)"
    ;;
  local)
    mcp_grok_id="orchestrator-host"
    mcp_launcher="scripts/mcp-host-stdio.sh"
    grok_config_hint="Template/orchestrator: enable orchestrator-host in .grok/config.toml (orchestrator-ddev disabled)"
    if [[ "$has_mcp_server" -eq 0 ]]; then
      mcp_note="No mcp-server/ — expected only for template + deployed app repos"
    else
      # Session-start path: ensure MCP host venv is healthy (uv preferred)
      if [[ -f scripts/ensure-mcp-host.sh ]] && bash scripts/ensure-mcp-host.sh --quiet 2>/dev/null; then
        mcp_ready="yes"
      elif [[ -x mcp-server/.venv/bin/orchestrator-mcp ]]; then
        mcp_ready="pending"
        mcp_note="Host MCP binary present but imports unhealthy — bash scripts/ensure-mcp-host.sh --force"
      else
        mcp_ready="pending"
        mcp_note="Host MCP not ready — bash scripts/ensure-mcp-host.sh (needs uv or python3-venv)"
      fi
    fi
    app_commands_via="host shell"
    ;;
esac

# Handshake probe when host stdio MCP looks ready (list_tools + health_check).
# Skip for DDEV-only launchers — host smoke is not the client path there.
mcp_handshake="skip"
if [[ "$mcp_ready" == "yes" && -f scripts/mcp-smoke.sh ]]; then
  if [[ "${mcp_launcher}" == *mcp-host-stdio* ]]; then
    if bash scripts/mcp-smoke.sh --quiet --no-ensure 2>/dev/null; then
      mcp_handshake="yes"
    elif bash scripts/mcp-smoke.sh --quiet 2>/dev/null; then
      mcp_handshake="yes"
    else
      mcp_ready="fail"
      mcp_handshake="no"
      mcp_note="MCP handshake failed (stdio list_tools/health_check) — bash scripts/mcp-smoke.sh ; bash scripts/ensure-mcp-host.sh --force ; reconnect host MCP"
    fi
  else
    mcp_handshake="skip"
  fi
elif [[ "$mcp_ready" == "pending" ]]; then
  mcp_handshake="no"
fi

# Enrich with MCP dev-only policy + start options (and optional manifest identity)
POLICY_JSON="$(
  python3 - "$ROOT" "$runtime" "$has_ddev" "$has_compose" "$has_mcp_server" \
    "$mcp_ready" "$ddev_running" "$compose_running" "$mcp_note" "$WITH_IDENTITY" <<'PY'
import json, sys
from pathlib import Path

root = Path(sys.argv[1])
runtime = sys.argv[2]
has_ddev = sys.argv[3] == "1"
has_compose = sys.argv[4] == "1"
has_mcp_server = sys.argv[5] == "1"
mcp_ready = sys.argv[6]
ddev_running = sys.argv[7]
compose_running = sys.argv[8]
mcp_note = sys.argv[9]
with_identity = sys.argv[10] == "1"

scripts = root / "scripts"
if str(scripts) not in sys.path:
    sys.path.insert(0, str(scripts))

from _engine.mcp_runtime_policy import session_mcp_brief  # noqa: E402

brief = session_mcp_brief(
    root=root,
    runtime=runtime,
    has_ddev=has_ddev,
    has_compose=has_compose,
    has_mcp_server=has_mcp_server,
    mcp_ready=mcp_ready,
    ddev_running=ddev_running,
    compose_running=compose_running,
    mcp_note=mcp_note,
)

out = {
    "mcp_policy": brief["mcp_policy"],
    "mcp_public_forbidden": brief["mcp_public_forbidden"],
    "mcp_env_safe": brief["mcp_env_safe"],
    "mcp_env_note": brief["mcp_env_note"],
    "mcp_ready": brief["mcp_ready"],
    "mcp_note": brief["mcp_note"],
    "mcp_start_offer": brief["mcp_start_offer"],
    "mcp_start_options": brief["mcp_start_options"],
    "mcp_start_options_text": brief["mcp_start_options_text"],
    "mcp_briefing_line": brief["briefing_line"],
}

if with_identity:
    try:
        from _engine.manifest_identity import check_manifest_identity  # noqa: E402

        ident = check_manifest_identity(root)
        out["manifest_identity"] = {
            "status": ident.get("status"),
            "ok": ident.get("ok"),
            "briefing_line": ident.get("briefing_line"),
            "issues": ident.get("issues") or [],
            "recommendations": ident.get("recommendations") or [],
            "project_name": ident.get("project_name"),
            "framework": ident.get("framework"),
            "detected_stack": ident.get("detected_stack") or [],
        }
    except Exception as exc:  # pragma: no cover
        out["manifest_identity"] = {
            "status": "error",
            "ok": False,
            "briefing_line": f"Manifest identity: ERROR — {exc}",
            "issues": [str(exc)],
            "recommendations": [],
        }

print(json.dumps(out))
PY
)" || POLICY_JSON='{"mcp_policy":"dev_only","mcp_public_forbidden":"yes","mcp_env_safe":"yes","mcp_ready":"'"$mcp_ready"'","mcp_note":"'"$mcp_note"'","mcp_start_offer":"no","mcp_start_options":[],"mcp_start_options_text":"","mcp_briefing_line":"","mcp_env_note":"MCP is develop-only"}'

# Overlay policy-adjusted ready/note
mcp_ready="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("mcp_ready",""))' <<<"$POLICY_JSON")"
mcp_note="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("mcp_note",""))' <<<"$POLICY_JSON")"
mcp_policy="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("mcp_policy","dev_only"))' <<<"$POLICY_JSON")"
mcp_public_forbidden="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("mcp_public_forbidden","yes"))' <<<"$POLICY_JSON")"
mcp_env_safe="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("mcp_env_safe","yes"))' <<<"$POLICY_JSON")"
mcp_env_note="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("mcp_env_note",""))' <<<"$POLICY_JSON")"
mcp_start_offer="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("mcp_start_offer","no"))' <<<"$POLICY_JSON")"
mcp_start_options_text="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("mcp_start_options_text",""))' <<<"$POLICY_JSON")"
mcp_briefing_line="$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("mcp_briefing_line",""))' <<<"$POLICY_JSON")"

if [[ "$JSON" -eq 1 ]]; then
  python3 - <<'PY' "$ROOT" "$manifest_file" "$manifest_env" "$runtime" "$has_ddev" "$has_compose" "$has_mcp_server" \
    "$ddev_project" "$compose_file" "$ddev_running" "$compose_running" "$mcp_grok_id" "$mcp_launcher" \
    "$mcp_ready" "${mcp_handshake:-skip}" "$mcp_note" "$app_commands_via" "$grok_config_hint" \
    "$mcp_policy" "$mcp_public_forbidden" "$mcp_env_safe" "$mcp_env_note" \
    "$mcp_start_offer" "$mcp_start_options_text" "$mcp_briefing_line" "$POLICY_JSON"
import json, sys
keys = [
  "project_root", "manifest_file", "manifest_environment_manager", "runtime",
  "has_ddev", "has_compose", "has_mcp_server", "ddev_project", "compose_file",
  "ddev_running", "compose_running", "mcp_grok_server_id", "mcp_launcher",
  "mcp_ready", "mcp_handshake", "mcp_note", "app_commands_via", "grok_config_hint",
  "mcp_policy", "mcp_public_forbidden", "mcp_env_safe", "mcp_env_note",
  "mcp_start_offer", "mcp_start_options_text", "mcp_briefing_line",
]
vals = sys.argv[1:-1]
base = dict(zip(keys, vals))
# bool-ish strings stay strings for shell parity
try:
    policy = json.loads(sys.argv[-1])
except json.JSONDecodeError:
    policy = {}
base["mcp_start_options"] = policy.get("mcp_start_options") or []
if "manifest_identity" in policy:
    base["manifest_identity"] = policy["manifest_identity"]
# normalize numeric flags
for k in ("has_ddev", "has_compose", "has_mcp_server"):
    if k in base:
        base[k] = base[k]
print(json.dumps(base, indent=2))
PY
  exit 0
fi

echo "project_root=${ROOT}"
echo "manifest_file=${manifest_file:-none}"
echo "manifest_environment_manager=${manifest_env:-unset}"
echo "runtime=${runtime}"
echo "has_ddev=${has_ddev}"
echo "has_compose=${has_compose}"
echo "has_mcp_server=${has_mcp_server}"
echo "ddev_project=${ddev_project:-none}"
echo "compose_file=${compose_file:-none}"
echo "ddev_running=${ddev_running}"
echo "compose_running=${compose_running}"
echo "mcp_grok_server_id=${mcp_grok_id}"
echo "mcp_launcher=${mcp_launcher}"
echo "mcp_ready=${mcp_ready}"
echo "mcp_handshake=${mcp_handshake:-skip}"
echo "mcp_note=${mcp_note}"
echo "mcp_policy=${mcp_policy}"
echo "mcp_public_forbidden=${mcp_public_forbidden}"
echo "mcp_env_safe=${mcp_env_safe}"
echo "mcp_env_note=${mcp_env_note}"
echo "mcp_start_offer=${mcp_start_offer}"
echo "app_commands_via=${app_commands_via}"
echo "grok_config_hint=${grok_config_hint}"
echo "mcp_briefing_line=${mcp_briefing_line}"
if [[ -n "$mcp_start_options_text" && "$mcp_start_offer" == "yes" ]]; then
  echo "mcp_start_options<<"
  printf '%s\n' "$mcp_start_options_text"
  echo ">>mcp_start_options"
fi
if [[ "$WITH_IDENTITY" -eq 1 ]]; then
  python3 -c 'import json,sys; d=json.load(sys.stdin); m=d.get("manifest_identity") or {}; print("manifest_identity_status="+str(m.get("status","unknown"))); print("manifest_identity_line="+(m.get("briefing_line") or ""))' <<<"$POLICY_JSON"
fi
