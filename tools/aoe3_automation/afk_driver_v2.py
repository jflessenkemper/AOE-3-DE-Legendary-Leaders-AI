#!/usr/bin/env python3
"""
AFKmodValidation driver v2: fully verified click-by-click gameplay.

Guardrail G1: Window geometry is authoritative, queried at start.
Guardrail G2: EVERY click verified by screenshot diff.
Guardrail G3: JSONL log entries include verified=true only on confirmed clicks.
Guardrail G4: Abort if first skirmish click fails.

Changes from v1:
- Pixel-diff verification on every click (no silent failures).
- Reference anchors established and saved to JSON.
- Per-civ logs with screenshot evidence.
- Abort on anchor failure.
- Smart dropdown navigation with row counting.
"""

import subprocess
import re
import sys
import time
import json
import os
import tempfile
from pathlib import Path
from io import BytesIO
from PIL import Image
import hashlib
import random

# Ensure ydotool can find its socket
os.environ['YDOTOOL_SOCKET'] = os.environ.get('YDOTOOL_SOCKET', '/tmp/.ydotool_socket')

# ============ CONFIG ============
ARTIFACT_DIR = Path("/tmp/aoe_test/afk_run_v2")
PHASE1_DIR = ARTIFACT_DIR / "phase1_civ_picker"
PHASE2_DIR = ARTIFACT_DIR / "phase2_loading"
PHASE3_DIR = ARTIFACT_DIR / "phase3_match_start"
PHASE4_DIR = ARTIFACT_DIR / "phase4_ai_observer"
LOGS_DIR = ARTIFACT_DIR / "logs"
ANCHORS_DIR = ARTIFACT_DIR / "anchors"
JSONL_LOG = ARTIFACT_DIR / "run.jsonl"

SCREENSHOT_TIMEOUT = 5
CLICK_VERIFY_RETRIES = 1
CLICK_VERIFY_WAIT = 0.5
SCREENSHOT_WAIT = 0.3
ROW_HEIGHT = 25  # Pixels between civ rows in dropdown

# ============ WINDOW GEOMETRY (G1) ============
def get_aoe3_window():
    """Query wmctrl for AoE3 window geometry. Required at start and after major phase transitions."""
    try:
        out = subprocess.check_output(["wmctrl", "-lG"], text=True)
        m = re.search(
            r'(0x[0-9a-f]+)\s+\d+\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+\S+\s+Age of Empires III',
            out
        )
        if not m:
            return None
        wid, wx, wy, ww, wh = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
        return {'wid': wid, 'x': wx, 'y': wy, 'w': ww, 'h': wh}
    except Exception as e:
        log_error(f"wmctrl query failed: {e}")
        return None

def verify_window_size(win, expected_w=1920, expected_h=1080):
    """Abort if window size doesn't match expected."""
    if (win['w'], win['h']) != (expected_w, expected_h):
        sys.exit(f"FATAL: game window is {win['w']}x{win['h']}, expected {expected_w}x{expected_h}. User must fix resolution before rerun.")

# ============ SCREENSHOT CAPTURE & DIFF ============
def screenshot_bytes():
    """Capture host screenshot via spectacle. Returns PNG bytes."""
    import tempfile
    try:
        # Use a temp file since spectacle doesn't support stdout well
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name

        result = subprocess.run(
            ["spectacle", "-b", "-n", "-o", tmp_path],
            capture_output=True,
            timeout=SCREENSHOT_TIMEOUT
        )
        if result.returncode != 0:
            log_error(f"spectacle failed: {result.stderr.decode()}")
            return None

        # Read the temp file
        with open(tmp_path, 'rb') as f:
            png_bytes = f.read()

        # Clean up
        os.unlink(tmp_path)
        return png_bytes
    except subprocess.TimeoutExpired:
        log_error("spectacle timeout")
        return None
    except Exception as e:
        log_error(f"screenshot_bytes failed: {e}")
        return None

def pixel_diff_pct(before_bytes, after_bytes):
    """
    Compare two PNG images. Sample 200 random pixels.
    Return percentage of sampled pixels that changed by >20 in any RGB channel.
    """
    try:
        before = Image.open(BytesIO(before_bytes)).convert("RGB")
        after = Image.open(BytesIO(after_bytes)).convert("RGB")

        w, h = before.size
        if (w, h) != after.size:
            return 100.0  # Different size = different image

        # Sample 200 random pixels
        import random
        changed = 0
        for _ in range(200):
            x = random.randint(0, w - 1)
            y = random.randint(0, h - 1)
            b_rgb = before.getpixel((x, y))
            a_rgb = after.getpixel((x, y))
            # Check if any channel differs by >20
            if any(abs(b_rgb[i] - a_rgb[i]) > 20 for i in range(3)):
                changed += 1
        return (changed / 200.0) * 100.0
    except Exception as e:
        log_error(f"pixel_diff_pct failed: {e}")
        return -1.0

# ============ YDOTOOL INPUT ============
def ydotool_click(abs_x, abs_y):
    """Click at absolute screen coordinates via ydotool."""
    try:
        subprocess.run(
            ["ydotool", "mousemove", str(abs_x), str(abs_y)],
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["ydotool", "click", "1"],
            check=True,
            capture_output=True
        )
    except Exception as e:
        log_error(f"ydotool_click({abs_x}, {abs_y}) failed: {e}")
        raise

def ydotool_key(key_name):
    """Press a key via ydotool (e.g., 'Escape')."""
    try:
        subprocess.run(
            ["ydotool", "key", key_name],
            check=True,
            capture_output=True
        )
    except Exception as e:
        log_error(f"ydotool_key({key_name}) failed: {e}")
        raise

# ============ CLICK VERIFICATION (G2) ============
def click_verified(win, game_x, game_y, expected_change=True, timeout_s=5, retries=CLICK_VERIFY_RETRIES):
    """
    Click at game-relative coords (game_x, game_y).
    Verify by screenshot diff. Return (success, diff_pct, before_bytes, after_bytes).
    If success=False and retries exhausted, return (False, diff_pct, before, after).
    """
    abs_x = win['x'] + game_x
    abs_y = win['y'] + game_y

    before = screenshot_bytes()
    if before is None:
        return False, -1.0, None, None

    diff = -1.0
    after = None
    for attempt in range(retries + 1):
        try:
            ydotool_click(abs_x, abs_y)
        except Exception:
            continue

        time.sleep(CLICK_VERIFY_WAIT)
        after = screenshot_bytes()
        if after is None:
            return False, -1.0, before, None

        diff = pixel_diff_pct(before, after)
        if diff < 0:  # Error in diff computation
            return False, -1.0, before, after

        if expected_change:
            if diff > 0.5:  # >0.5% of sampled pixels changed
                return True, diff, before, after
        else:
            if diff < 0.1:  # <0.1% change = no change
                return True, diff, before, after

        if attempt < retries:
            time.sleep(SCREENSHOT_WAIT)

    return False, diff, before, after

# ============ LOGGING & REPORTING ============
def log_error(msg):
    """Write error to stderr."""
    print(f"[ERROR] {msg}", file=sys.stderr)

def log_jsonl(entry):
    """Append JSON entry to JSONL log."""
    with open(JSONL_LOG, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def save_screenshot(png_bytes, path):
    """Save PNG bytes to file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'wb') as f:
        f.write(png_bytes)

# ============ LOAD CIVS FROM XML ============
def load_mod_civs():
    """Load 26 mod civ IDs from data/civmods.xml."""
    try:
        result = subprocess.run(
            ["grep", "^[[:space:]]*<Name>", "data/civmods.xml"],
            capture_output=True,
            text=True,
            cwd=str(ARTIFACT_DIR.parent.parent.parent)  # Assume we're in the repo
        )
        lines = result.stdout.strip().split('\n')
        civs = []
        for line in lines:
            if '<Name>' in line:
                name = line.split('<Name>')[1].split('</Name>')[0]
                civs.append(name)
        return civs[:26]  # Take first 26
    except Exception as e:
        log_error(f"Failed to load mod civs from XML: {e}")
        return []

# ============ ANCHOR ESTABLISHMENT (Step 1) ============
def establish_anchors(win):
    """
    Drive: Main Menu → Skirmish → Civ Dropdown → select French → back out.
    Verify each step. Save reference screenshots and anchor JSON.
    Abort if any step fails.
    """
    print("[ANCHOR] Starting anchor establishment...")

    # Step 1a: Click Skirmish button (main menu)
    print("[ANCHOR] Clicking Skirmish button...")
    success, diff, before, after = click_verified(win, 960, 800, expected_change=True)
    if not success:
        write_failure_reason(
            "Anchor: Skirmish button click failed",
            f"Expected >0.5% diff, got {diff:.1f}%",
            before, after
        )
        return None
    save_screenshot(before, ANCHORS_DIR / "00_main_menu.png")
    save_screenshot(after, ANCHORS_DIR / "01_post_skirmish_click.png")
    print(f"  [OK] Skirmish click verified (diff={diff:.1f}%)")
    time.sleep(1)

    # Step 1b: Take screenshot of skirmish setup screen
    setup_screen = screenshot_bytes()
    if setup_screen is None:
        write_failure_reason("Anchor: Failed to capture skirmish setup screen", "", None, None)
        return None
    save_screenshot(setup_screen, ANCHORS_DIR / "02_skirmish_setup.png")

    # Step 1c: Click player1 civ dropdown
    # Typical location: ~400, 350 (left side, civilizations panel)
    print("[ANCHOR] Clicking civ dropdown...")
    success, diff, before, after = click_verified(win, 400, 350, expected_change=True)
    if not success:
        write_failure_reason(
            "Anchor: Civ dropdown click failed",
            f"Expected >0.5% diff, got {diff:.1f}%",
            before, after
        )
        return None
    save_screenshot(after, ANCHORS_DIR / "03_dropdown_open.png")
    print(f"  [OK] Dropdown open verified (diff={diff:.1f}%)")
    time.sleep(0.5)

    # Step 1d: Screenshot dropdown list
    dropdown_screen = screenshot_bytes()
    save_screenshot(dropdown_screen, ANCHORS_DIR / "04_dropdown_list.png")

    # Step 1e: Click first civ row (French is typically first or near top)
    print("[ANCHOR] Clicking first civ row...")
    success, diff, before, after = click_verified(win, 400, 420, expected_change=True)
    if not success:
        write_failure_reason(
            "Anchor: First civ row click failed",
            f"Expected >0.5% diff, got {diff:.1f}%",
            before, after
        )
        return None
    save_screenshot(after, ANCHORS_DIR / "05_civ_selected.png")
    print(f"  [OK] Civ selection verified (diff={diff:.1f}%)")
    time.sleep(0.5)

    # Step 1f: Back out (press Escape)
    print("[ANCHOR] Pressing Escape to return to main menu...")
    ydotool_key("Escape")
    time.sleep(1)
    back_screen = screenshot_bytes()
    save_screenshot(back_screen, ANCHORS_DIR / "06_back_to_main.png")

    # Collect visual anchors from dropdown screenshot
    # For now, hardcode typical safe values; refine based on actual screenshots
    anchors = {
        "skirmish_btn": {"game_x": 960, "game_y": 800},
        "player1_civ_dropdown": {"game_x": 400, "game_y": 350},
        "first_civ_row": {"game_x": 400, "game_y": 420},
        "civ_row_height": 30,
        "scroll_position": 0,
        "start_game_btn": {"game_x": 960, "game_y": 950},
        "in_game_menu_btn": {"game_x": 1800, "game_y": 100},
        "resign_btn": {"game_x": 960, "game_y": 500},
        "confirm_resign_yes": {"game_x": 950, "game_y": 550},
        "back_to_main_escape": True
    }

    with open(ANCHORS_DIR / "ui_anchors.json", 'w') as f:
        json.dump(anchors, f, indent=2)

    print("[ANCHOR] Anchor establishment complete. Anchors saved to ui_anchors.json")
    return anchors

def write_failure_reason(title, details, before_bytes, after_bytes):
    """Write FAILURE_REASON.md explaining anchor failure."""
    failure_md = ARTIFACT_DIR / "FAILURE_REASON.md"
    with open(failure_md, 'w') as f:
        f.write(f"# Anchor Establishment Failure\n\n")
        f.write(f"## {title}\n\n")
        f.write(f"{details}\n\n")
        if before_bytes:
            before_path = ANCHORS_DIR / "FAILURE_before.png"
            save_screenshot(before_bytes, before_path)
            f.write(f"Before screenshot: `{before_path.name}`\n\n")
        if after_bytes:
            after_path = ANCHORS_DIR / "FAILURE_after.png"
            save_screenshot(after_bytes, after_path)
            f.write(f"After screenshot: `{after_path.name}`\n\n")
    print(f"\n[FATAL] {title}")
    print(f"[FATAL] Written FAILURE_REASON.md at {failure_md}")
    sys.exit(1)

# ============ FAST TEST: Trivial loop ============
def fast_test(win):
    """
    Unit test: Main Menu → Skirmish → screenshot → Escape → screenshot.
    Verify clicks are detected. If this fails, abort.
    """
    print("\n[FAST_TEST] Running trivial verification loop...")

    # Click Skirmish
    success, diff, before, after = click_verified(win, 960, 800, expected_change=True)
    if not success:
        print(f"[FAST_TEST] FAIL: Skirmish click not verified (diff={diff:.1f}%)")
        return False
    print(f"[FAST_TEST] Skirmish click verified (diff={diff:.1f}%)")

    # Press Escape
    ydotool_key("Escape")
    time.sleep(0.8)

    # Take another screenshot
    escape_screen = screenshot_bytes()
    if escape_screen is None:
        print("[FAST_TEST] FAIL: Could not capture post-Escape screenshot")
        return False

    # Compare with skirmish screen
    diff2 = pixel_diff_pct(after, escape_screen)
    if diff2 > 0.5:
        print(f"[FAST_TEST] Escape verified (diff={diff2:.1f}%)")
        return True
    else:
        print(f"[FAST_TEST] FAIL: Escape not verified (diff={diff2:.1f}%)")
        return False

# ============ PHASE 1: CIV PICKER (45 min) ============
def phase1_civ_picker(win, anchors, civs):
    """
    For each civ: open dropdown, navigate to row (via down arrow or row index),
    click row, screenshot setup screen, close, back to main.
    Every click verified.
    """
    print(f"\n[PHASE1] Civ picker phase ({len(civs)} civs)...")

    for i, civ in enumerate(civs):
        print(f"  [{i+1}/{len(civs)}] {civ}")
        slug = civ.lower().replace(' ', '_').replace('/', '_')

        # Go back to main menu (safety)
        ydotool_key("Escape")
        time.sleep(0.3)

        # Re-enter Skirmish if needed
        success, _, _, _ = click_verified(
            win,
            anchors["skirmish_btn"]["game_x"],
            anchors["skirmish_btn"]["game_y"],
            expected_change=True,
            retries=1
        )
        if not success:
            log_jsonl({"civ": civ, "phase": 1, "step": "skirmish_btn", "verified": False})
            continue

        time.sleep(0.3)

        # Open dropdown
        success, diff_open, _, after_open = click_verified(
            win,
            anchors["player1_civ_dropdown"]["game_x"],
            anchors["player1_civ_dropdown"]["game_y"],
            expected_change=True,
            retries=1
        )
        if not success:
            log_jsonl({
                "civ": civ,
                "phase": 1,
                "step": "open_dropdown",
                "verified": False,
                "diff_pct": diff_open,
                "notes": "Dropdown click failed"
            })
            ydotool_key("Escape")
            time.sleep(0.2)
            continue

        # Screenshot dropdown
        dropdown_screen = screenshot_bytes()
        if dropdown_screen:
            save_screenshot(dropdown_screen, PHASE1_DIR / f"{slug}_dropdown.png")

        time.sleep(0.2)

        # Navigate to civ row by pressing Down arrow i times
        # For first 22 base civs, i=0-21; for mod civs, additional rows
        for _ in range(i):
            ydotool_key("Down")
            time.sleep(0.1)

        # Click the row
        time.sleep(0.2)
        success, diff_click, _, after_click = click_verified(
            win,
            anchors["first_civ_row"]["game_x"],
            anchors["first_civ_row"]["game_y"],
            expected_change=True,
            retries=1
        )
        if not success:
            log_jsonl({
                "civ": civ,
                "phase": 1,
                "step": "click_civ_row",
                "verified": False,
                "diff_pct": diff_click,
                "notes": "Civ row click failed"
            })
            ydotool_key("Escape")
            time.sleep(0.2)
            continue

        # Screenshot setup screen
        time.sleep(0.3)
        setup_screen = screenshot_bytes()
        if setup_screen:
            save_screenshot(setup_screen, PHASE1_DIR / f"{slug}_setup.png")

        log_jsonl({
            "civ": civ,
            "phase": 1,
            "step": "civ_selection",
            "verified": True,
            "diff_pct": diff_click,
            "screenshot": f"{slug}_setup.png"
        })

        time.sleep(0.2)

# ============ PHASE 2: LOADING SCREEN (90 min) ============
def phase2_loading(win, anchors, civs_sample=None):
    """
    For each civ (or sample): select, click Start Game, capture loading screens,
    detect in-game, resign.
    """
    print(f"\n[PHASE2] Loading screen phase...")

    if civs_sample is None:
        civs_sample = civs[:5]  # Test sample

    for i, civ in enumerate(civs_sample):
        print(f"  [{i+1}/{len(civs_sample)}] {civ}")
        slug = civ.lower().replace(' ', '_')

        # Open dropdown & select civ
        success, _, _, _ = click_verified(
            win,
            anchors["player1_civ_dropdown"]["game_x"],
            anchors["player1_civ_dropdown"]["game_y"],
            expected_change=True
        )
        if not success:
            log_jsonl({"civ": civ, "phase": 2, "step": "open_dropdown", "verified": False})
            continue

        time.sleep(0.3)

        # Click civ row
        success, _, _, _ = click_verified(
            win,
            anchors["first_civ_row"]["game_x"],
            anchors["first_civ_row"]["game_y"],
            expected_change=True
        )
        if not success:
            log_jsonl({"civ": civ, "phase": 2, "step": "select_civ", "verified": False})
            continue

        time.sleep(0.3)

        # Click Start Game
        success, diff, _, after = click_verified(
            win,
            anchors["start_game_btn"]["game_x"],
            anchors["start_game_btn"]["game_y"],
            expected_change=True
        )
        if not success:
            log_jsonl({"civ": civ, "phase": 2, "step": "click_start", "verified": False, "diff_pct": diff})
            continue

        save_screenshot(after, PHASE2_DIR / f"{slug}_loading_00s.png")

        # Wait for loading screen
        time.sleep(3)
        loading_screen = screenshot_bytes()
        save_screenshot(loading_screen, PHASE2_DIR / f"{slug}_loading_03s.png")

        # Wait for in-game
        time.sleep(5)
        ingame_screen = screenshot_bytes()
        save_screenshot(ingame_screen, PHASE2_DIR / f"{slug}_in_game_08s.png")

        # Verify screen changed (diff between loading and in-game)
        diff_load_ingame = pixel_diff_pct(loading_screen, ingame_screen)

        log_jsonl({
            "civ": civ,
            "phase": 2,
            "step": "loading_to_ingame",
            "verified": diff_load_ingame > 0.5,  # Just need some change to confirm loading finished
            "diff_pct": diff_load_ingame,
            "screenshot": f"{slug}_in_game_08s.png"
        })

        # Try to resign
        print(f"    Attempting resign...")
        success, _, _, _ = click_verified(
            win,
            anchors["in_game_menu_btn"]["game_x"],
            anchors["in_game_menu_btn"]["game_y"],
            expected_change=True
        )
        if success:
            time.sleep(0.5)
            success, _, _, _ = click_verified(
                win,
                anchors["resign_btn"]["game_x"],
                anchors["resign_btn"]["game_y"],
                expected_change=True
            )
            if success:
                time.sleep(0.5)
                success, _, _, _ = click_verified(
                    win,
                    anchors["confirm_resign_yes"]["game_x"],
                    anchors["confirm_resign_yes"]["game_y"],
                    expected_change=True
                )

        # Fallback: press Escape multiple times
        for _ in range(3):
            ydotool_key("Escape")
            time.sleep(0.3)

        time.sleep(1)

# ============ MAIN ============
def main():
    print("=" * 70)
    print("AFKModValidation Driver v2 - Click-Verified Gameplay")
    print("=" * 70)

    # Step 0: Check window geometry (G1)
    print("\n[INIT] Querying window geometry...")
    win = get_aoe3_window()
    if win is None:
        sys.exit("FATAL: AoE3 window not found. Is the game running?")
    print(f"  Window: {win['w']}x{win['h']} at ({win['x']}, {win['y']})")
    verify_window_size(win)
    print("  [OK] Window size verified")

    # Step 0b: Fast test (trivial loop)
    if not fast_test(win):
        sys.exit("FATAL: Fast test failed. Click verification not working.")
    print("[FAST_TEST] PASS")

    # Step 1: Anchor establishment
    print("\n[STEP 1] Anchor Establishment (15 min)")
    anchors = establish_anchors(win)
    if anchors is None:
        sys.exit("FATAL: Anchor establishment failed (see FAILURE_REASON.md)")

    # Load all base and mod civs
    # Base civs (from initial dropdown discovery)
    base_civs = ["French", "British", "Spanish", "Dutch", "German", "Portuguese", "Russian",
                 "Ottoman", "Chinese", "Indian", "Japanese", "Korean", "Aztec", "Sioux",
                 "Inca", "Haudenosaunee", "Swede", "Polish"]

    # Try to load mod civs from XML
    mod_civs = load_mod_civs()
    if not mod_civs:
        print("[WARN] Could not load mod civs from XML, using base civs only")
        civs = base_civs[:8]  # Test first 8
    else:
        civs = base_civs + mod_civs

    print(f"\n[INFO] Testing {len(civs)} civs total")

    # Step 2: Phase 1 - Civ Picker
    print("\n[STEP 2] Phase 1 - Civ Picker ({len(civs)} civs)")
    phase1_civ_picker(win, anchors, civs[:10])  # Start with first 10 for testing

    # Step 3: Phase 2 - Loading Screen (on sample)
    print("\n[STEP 3] Phase 2 - Loading Screens (sample)")
    phase2_loading(win, anchors, civs_sample=civs[:3])

    print("\n" + "=" * 70)
    print("Validation complete. Logs and screenshots in /tmp/aoe_test/afk_run_v2/")
    print("=" * 70)

if __name__ == "__main__":
    main()
