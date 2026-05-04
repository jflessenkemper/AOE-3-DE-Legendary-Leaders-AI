#!/usr/bin/env bash
# Empirical click-sweep for AoE3 DE Skirmish lobby.
# For each candidate (x, y), click, screenshot via gamescopectl,
# pixel-diff vs baseline. Hits = clicks that change the screen.
#
# Run from gamescope-host context:
#   flatpak-spawn --host bash tools/aoe3_automation/sweep_lobby.sh
#
# Assumes the game is currently at the Skirmish lobby (default state).
set -uo pipefail
export DISPLAY=:1

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DIR="$ROOT/tools/aoe3_automation/templates/matrix/_raw/sweep"
mkdir -p "$DIR"

# Force clean lobby state before baselining: Escape closes any open picker;
# if that exited the lobby, click Skirmish to re-enter.
WIN=$(xdotool search --name "Age of Empires III" | head -1)
xdotool key --window "$WIN" Escape Escape Escape
sleep 0.7
xdotool mousemove 130 488
sleep 0.15
xdotool click 1
sleep 1.6

BASELINE="$DIR/_baseline.png"
gamescopectl screenshot "$BASELINE"
sleep 0.7
[ -s "$BASELINE" ] || { echo "FAIL: no baseline screenshot"; exit 1; }
echo "Baseline saved: $(stat -c%s "$BASELINE") bytes"

# Diff threshold: total absolute-error pixel count (normalized)
THRESH=20000

probe() {
    local x="$1" y="$2"
    local png="$DIR/probe_${x}_${y}.png"
    xdotool mousemove "$x" "$y"
    sleep 0.15
    xdotool click 1
    sleep 1.2
    gamescopectl screenshot "$png"
    sleep 0.3
    if [ ! -s "$png" ]; then
        sleep 0.6
        gamescopectl screenshot "$png"
        sleep 0.2
    fi
    # magick compare -metric AE outputs "<sum-sq> (<n_pixels>)". We want the n_pixels (in parens).
    local diff_raw diff_int
    diff_raw=$(magick compare -metric AE "$BASELINE" "$png" null: 2>&1 || true)
    diff_int=$(python3 -c "
import sys, re
s = sys.argv[1]
m = re.search(r'\(([0-9.eE+-]+)\)', s)
if m:
    print(int(float(m.group(1))))
else:
    nums = re.findall(r'[0-9.eE+-]+', s)
    print(int(float(nums[0])) if nums else 0)
" "$diff_raw" 2>/dev/null || echo 0)
    if [ "${diff_int:-0}" -gt "$THRESH" ]; then
        echo "HIT  ($x, $y): diff=$diff_int  ($diff_raw) -> $png"
    else
        echo "miss ($x, $y): diff=$diff_int"
        rm -f "$png"
    fi
    # Restore: Escape thrice to close any picker AND exit to main menu, then re-enter Skirmish.
    # Forces a known-good state (lobby baseline) before the next probe.
    xdotool key --window "$WIN" Escape Escape Escape
    sleep 0.6
    xdotool mousemove 130 488
    sleep 0.15
    xdotool click 1
    sleep 1.6
}

# P1 row: y around 110-200 — sweep x widely
echo "=== P1 row sweep ==="
for x in 230 320 400 500 600 700 800 850 900 950 1000; do
    probe "$x" 145
done

# Another y in case row is offset
echo "=== P1 row, y=170 ==="
for x in 800 850 900 950; do
    probe "$x" 170
done

# Right column dropdowns: x around 1500-1750
echo "=== Right column settings sweep ==="
for y in 320 400 480 560 640 720 800 880 960; do
    probe 1620 "$y"
done

# Advanced settings hunt: top-right icons
echo "=== Top-right icon sweep ==="
for pair in "1750,30" "1820,30" "1880,30" "1900,30" "1850,80"; do
    x="${pair%,*}"; y="${pair#*,}"
    probe "$x" "$y"
done

echo "=== DONE ==="
ls "$DIR"/*.png 2>/dev/null | grep -v _baseline
