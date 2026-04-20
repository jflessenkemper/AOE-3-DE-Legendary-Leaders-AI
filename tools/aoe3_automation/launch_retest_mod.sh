#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/../.." && pwd)
DEFAULT_LOG_PATH="$HOME/.steam/steam/steamapps/compatdata/933110/pfx/drive_c/users/steamuser/Games/Age of Empires 3 DE/Logs/Age3Log.txt"
DEFAULT_FLOW="$REPO_ROOT/tools/aoe3_automation/flows/launch_and_capture_menu.json"
DEFAULT_ARTIFACT_ROOT="$REPO_ROOT/tools/aoe3_automation/artifacts/retest_runs"
APP_ID=933110
HOST_GAME_MATCH='(steam_app_933110|steamgameid=933110|AppId=933110|age3y\.exe|age3\.exe|RelicCardinal|reliccardinal|wine64.*933110|proton.*933110)'
HOST_HELPER_EXCLUDE='(launch_retest_mod\.sh|run_sandbox\.py|run_runtime_validation\.py|aoe3_ui_automation\.py|flatpak-spawn --host sh -lc|rg -i|pkill -f -i)'

host_sh() {
  flatpak-spawn --host sh -lc "$1"
}

host_game_ps() {
  host_sh "ps -eo pid=,ppid=,comm=,args= | rg -i '$HOST_GAME_MATCH' | rg -v -i '$HOST_HELPER_EXCLUDE' || true"
}

host_game_pids() {
  host_sh "ps -eo pid=,ppid=,comm=,args= | rg -i '$HOST_GAME_MATCH' | rg -v -i '$HOST_HELPER_EXCLUDE' | awk '{print \$1}' || true"
}

kill_host_game_processes() {
  local signal="$1"
  local pids
  pids="$(host_game_pids)"
  if [[ -z "$pids" ]]; then
    return 0
  fi

  while IFS= read -r pid; do
    [[ -n "$pid" ]] || continue
    host_sh "kill -$signal $pid >/dev/null 2>&1 || true"
  done <<< "$pids"
}

host_game_pids() {
  host_sh "ps -eo pid=,ppid=,comm=,args= | rg -i '$HOST_GAME_MATCH' | rg -v -i '$HOST_HELPER_EXCLUDE' | awk '{print \$1}' || true"
}

kill_game_processes() {
  local signal_name="$1"
  local pids
  pids="$(host_game_pids | tr '\n' ' ' | xargs)"
  if [[ -z "$pids" ]]; then
    return 0
  fi
  host_sh "kill -$signal_name $pids >/dev/null 2>&1 || true"
}

list_game_processes() {
  host_game_ps
}

game_process_count() {
  host_game_ps | wc -l | tr -d ' '
}

wait_for_game_exit() {
  local timeout_seconds="$1"
  local deadline=$((SECONDS + timeout_seconds))
  while (( SECONDS < deadline )); do
    if [[ "$(game_process_count)" == "0" ]]; then
      return 0
    fi
    sleep 1
  done
  return 1
}

ensure_game_closed() {
  echo 'Checking for stale AoE3/Proton processes on the host...'

  local initial_count
  initial_count="$(game_process_count)"
  if [[ "$initial_count" != "0" ]]; then
    echo 'AoE3 appears to still be running:'
    list_game_processes
  fi

  echo 'Requesting Steam to stop app 933110 in case the client still thinks it is open...'
  host_sh "steam steam://stop/$APP_ID >/dev/null 2>&1 || true"
  sleep 3

  if wait_for_game_exit 12; then
    echo 'AoE3 is closed.'
    return 0
  fi

  echo 'Steam still shows AoE3 as open or Proton children are lingering; sending SIGTERM to matching processes...'
  kill_game_processes TERM
  sleep 3

  if wait_for_game_exit 12; then
    echo 'AoE3 closed after process cleanup.'
    return 0
  fi

  echo 'Matched processes are still alive after SIGTERM:'
  list_game_processes
  echo 'Escalating to SIGKILL for the remaining AoE3/Proton processes...'
  kill_game_processes KILL
  sleep 2

  if wait_for_game_exit 10; then
    echo 'AoE3 closed after forced cleanup.'
    return 0
  fi

  echo 'error: AoE3 still appears to be running after cleanup attempts.' >&2
  list_game_processes >&2
  return 1
}

usage() {
  cat <<'EOF'
Usage: tools/aoe3_automation/launch_retest_mod.sh [options]

Options:
  --skip-launch            Do not launch the game through Steam.
  --skip-flow              Do not run a UI automation flow after launch.
  --skip-static            Do not run static validation before launch.
  --launch-wait SECONDS    Wait for log activity after launch when no flow is run. Defaults to 25.
  --flow PATH              Flow JSON to run. Defaults to launch_and_capture_menu.json.
  --artifacts-dir PATH     Directory to write run artifacts into.
  --log-path PATH          Override Age3Log.txt path.
  --runtime-suite NAME     Runtime suite to validate. Repeat for multiple suites.
  --help                   Show this help text.

Examples:
  tools/aoe3_automation/launch_retest_mod.sh
  tools/aoe3_automation/launch_retest_mod.sh --skip-launch --flow tools/aoe3_automation/flows/capture_open_menu.json
  tools/aoe3_automation/launch_retest_mod.sh --runtime-suite ai_rout_bootstrap
EOF
}

SKIP_LAUNCH=0
SKIP_FLOW=0
SKIP_STATIC=0
LAUNCH_WAIT_SECONDS=25
FLOW_PATH="$DEFAULT_FLOW"
LOG_PATH="$DEFAULT_LOG_PATH"
ARTIFACT_DIR=""
RUNTIME_SUITES=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-launch)
      SKIP_LAUNCH=1
      shift
      ;;
    --skip-flow)
      SKIP_FLOW=1
      shift
      ;;
    --skip-static)
      SKIP_STATIC=1
      shift
      ;;
    --flow)
      FLOW_PATH="$2"
      shift 2
      ;;
    --launch-wait)
      LAUNCH_WAIT_SECONDS="$2"
      shift 2
      ;;
    --artifacts-dir)
      ARTIFACT_DIR="$2"
      shift 2
      ;;
    --log-path)
      LOG_PATH="$2"
      shift 2
      ;;
    --runtime-suite)
      RUNTIME_SUITES+=("$2")
      shift 2
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
  PYTHON_BIN="$REPO_ROOT/.venv/bin/python"
else
  PYTHON_BIN=$(command -v python3)
fi

if [[ -z "$ARTIFACT_DIR" ]]; then
  RUN_STAMP=$(date +%Y%m%d_%H%M%S)
  ARTIFACT_DIR="$DEFAULT_ARTIFACT_ROOT/$RUN_STAMP"
fi

mkdir -p "$ARTIFACT_DIR"

cd "$REPO_ROOT"

echo "Artifacts: $ARTIFACT_DIR"
echo "Log path: $LOG_PATH"

if [[ "$SKIP_LAUNCH" -eq 0 ]]; then
  ensure_game_closed
fi

if [[ -f "$LOG_PATH" ]]; then
  cp "$LOG_PATH" "$ARTIFACT_DIR/Age3Log_before.txt"
  : > "$LOG_PATH"
fi

if [[ "$SKIP_STATIC" -eq 0 ]]; then
  {
    echo '== age-of-pirates profile =='
    "$PYTHON_BIN" tools/validation/run_reference_checks.py --profile age-of-pirates
    echo
    echo '== packaged-mod profile =='
    "$PYTHON_BIN" tools/validation/run_reference_checks.py --profile packaged-mod
  } | tee "$ARTIFACT_DIR/static_validation.txt"
fi

if [[ "$SKIP_LAUNCH" -eq 0 ]]; then
  echo 'Launching AoE3 via Steam...'
  flatpak-spawn --host steam -applaunch "$APP_ID"
fi

if [[ "$SKIP_FLOW" -eq 0 ]]; then
  echo "Running flow: $FLOW_PATH"
  "$PYTHON_BIN" tools/aoe3_automation/aoe3_ui_automation.py run-flow "$FLOW_PATH"
elif [[ "$SKIP_LAUNCH" -eq 0 ]]; then
  "$PYTHON_BIN" - <<PY
from pathlib import Path
import time

log_path = Path(r'''$LOG_PATH''')
deadline = time.time() + float(r'''$LAUNCH_WAIT_SECONDS''')
last_size = log_path.stat().st_size if log_path.exists() else -1

while time.time() < deadline:
    if log_path.exists():
        current_size = log_path.stat().st_size
        if current_size > 0 and current_size != last_size:
            break
        last_size = current_size
    time.sleep(1.0)
PY
fi

"$PYTHON_BIN" tools/aoe3_automation/aoe3_ui_automation.py collect-artifacts "$ARTIFACT_DIR" --log-dir "$(dirname "$LOG_PATH")" --screenshot

if [[ -f "$LOG_PATH" ]]; then
  rg -n -i "error|failed|exception|invalid|xml|proto|warning" "$LOG_PATH" > "$ARTIFACT_DIR/runtime_findings.txt" || true
fi

if [[ ${#RUNTIME_SUITES[@]} -gt 0 ]]; then
  RUNTIME_ARGS=()
  for suite in "${RUNTIME_SUITES[@]}"; do
    RUNTIME_ARGS+=(--suite "$suite")
  done
  "$PYTHON_BIN" tools/validation/validate_runtime_logs.py --log-path "$LOG_PATH" "${RUNTIME_ARGS[@]}" | tee "$ARTIFACT_DIR/runtime_validation.txt"
fi

echo
echo 'Retest complete.'
echo "Artifacts written to: $ARTIFACT_DIR"
if [[ -f "$ARTIFACT_DIR/runtime_findings.txt" ]]; then
  echo 'Runtime findings:'
  sed -n '1,120p' "$ARTIFACT_DIR/runtime_findings.txt"
fi