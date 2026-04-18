#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/../.." && pwd)
DEFAULT_LOG_PATH="$HOME/.steam/steam/steamapps/compatdata/933110/pfx/drive_c/users/steamuser/Games/Age of Empires 3 DE/Logs/Age3Log.txt"

if [[ -x "$REPO_ROOT/.venv/bin/python" ]]; then
  PYTHON_BIN="$REPO_ROOT/.venv/bin/python"
else
  PYTHON_BIN=$(command -v python3)
fi

LOG_PATH="${1:-$DEFAULT_LOG_PATH}"

"$PYTHON_BIN" "$REPO_ROOT/tools/validation/validate_runtime_logs.py" \
  --log-path "$LOG_PATH" \
  --suite prisoner_system_bootstrap \
  --suite human_prisoner_lane \
  --suite ai_prisoner_lane \
  --suite elite_retreat_lane