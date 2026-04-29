#!/usr/bin/env bash
# ally_all.sh — drive ei_inject to set all opponents to Ally at game start.
#
# AoE3 DE diplomacy panel: open with Alt+D (default hotkey). Panel shows one
# row per AI player with three toggles: Ally / Neutral / Enemy. We click the
# Ally column on each opponent row, then close.
#
# Usage:
#   LIBEI_SOCKET=gamescope-0-ei ./ally_all.sh [num_opponents]
#
# Calibration: coordinates below were measured for a 1920x1080 gamescope
# surface with the default DE UI. If the panel is offset, override:
#   ALLY_X=... ROW0_Y=... ROW_DY=... ./ally_all.sh 7
#
# The script just emits ei_inject commands on stdout; pipe into the binary.
#
#   ./ally_all.sh 7 | LIBEI_SOCKET=gamescope-0-ei ./ei_inject -v

set -euo pipefail

OPPONENTS="${1:-7}"           # number of AI opponents (default: 8-player FFA = 7)
ALLY_X="${ALLY_X:-1180}"      # x of the Ally toggle column (calibrate)
ROW0_Y="${ROW0_Y:-380}"       # y of first opponent row (calibrate)
ROW_DY="${ROW_DY:-58}"        # row pitch in pixels (calibrate)
CONFIRM_X="${CONFIRM_X:-960}" # confirm/OK button if panel asks
CONFIRM_Y="${CONFIRM_Y:-960}"

# AoE3 DE keycodes (linux input-event-codes):
#   KEY_LEFTALT = 56, KEY_D = 32, KEY_ESC = 1
KEY_LEFTALT=56
KEY_D=32
KEY_ESC=1

emit() { printf '%s\n' "$*"; }

# Pre-warm pointer focus near the centre so the first move lands cleanly.
emit "move 960 540"
emit "sleep 80"

# Open Diplomacy panel (Alt+D)
emit "keydown $KEY_LEFTALT"
emit "sleep 30"
emit "key $KEY_D"
emit "sleep 30"
emit "keyup $KEY_LEFTALT"
emit "sleep 350"

# Click the Ally column on each opponent row.
y="$ROW0_Y"
for i in $(seq 1 "$OPPONENTS"); do
    emit "move $ALLY_X $y"
    emit "sleep 60"
    emit "down 1"
    emit "sleep 30"
    emit "up 1"
    emit "sleep 80"
    y=$(( y + ROW_DY ))
done

# Click confirm (if panel has an OK), then close with Esc.
emit "move $CONFIRM_X $CONFIRM_Y"
emit "sleep 60"
emit "down 1"
emit "sleep 30"
emit "up 1"
emit "sleep 200"
emit "key $KEY_ESC"
emit "sleep 100"
emit "bye"
