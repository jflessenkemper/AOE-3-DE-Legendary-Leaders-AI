#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


def fail(message: str) -> "NoReturn":
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def ensure_runtime_support(needs_input: bool = False) -> None:
    session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    display = os.environ.get("DISPLAY", "")
    if session_type == "wayland" and needs_input:
        fail(
            "Wayland usually blocks desktop input automation. Install a supported injector such as ydotool/wtype, "
            "or run this under X11/XWayland. You can use the 'probe-environment' command to see what is missing."
        )
    if not display and session_type != "wayland":
        fail("No desktop display detected.")


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def can_spawn_host() -> bool:
    return command_exists("flatpak-spawn")


def run_host_command(args: list[str], capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    if not can_spawn_host():
        fail("flatpak-spawn is not available")

    kwargs: dict[str, Any] = {"check": False, "text": True}
    if capture_output:
        kwargs["capture_output"] = True

    return subprocess.run(["flatpak-spawn", "--host", *args], **kwargs)


def host_command_exists(name: str) -> bool:
    result = run_host_command(["which", name], capture_output=True)
    return result.returncode == 0


def host_xdotool_available() -> bool:
    if not host_command_exists("xdotool"):
        return False
    result = run_host_command(["xdotool", "getmouselocation"], capture_output=True)
    return result.returncode == 0


def default_aoe3_log_dir() -> Path:
    return Path.home() / ".steam/steam/steamapps/compatdata/933110/pfx/drive_c/users/steamuser/Games/Age of Empires 3 DE/Logs"


def import_pillow_image():
    try:
        from PIL import Image  # type: ignore
    except Exception as exc:
        fail(f"Pillow import failed: {exc}")
    return Image


def import_cv2():
    try:
        import cv2  # type: ignore
    except Exception as exc:
        fail(f"opencv-python import failed: {exc}")
    return cv2


def detect_input_backend(needs_vision: bool = False) -> str:
    session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
    display = os.environ.get("DISPLAY", "")

    if maybe_import_pyautogui() is not None:
        return "pyautogui"

    if can_spawn_host() and host_xdotool_available():
        return "host_xdotool"

    if needs_vision:
        fail(
            "No usable input/vision backend found. Install Python requirements for local control or ensure host xdotool/import are reachable via flatpak-spawn."
        )

    if session_type == "wayland":
        fail(
            "Wayland input automation needs either local pyautogui on X11/XWayland or a host xdotool backend reachable through flatpak-spawn."
        )
    if not display:
        fail("No desktop display detected.")
    fail("No usable input backend found.")


def detect_capture_backend() -> str:
    if command_exists("gnome-screenshot"):
        return "gnome-screenshot"
    if maybe_import_pyautogui() is not None:
        return "pyautogui"
    if can_spawn_host() and host_command_exists("spectacle"):
        return "host-spectacle"
    if can_spawn_host() and host_command_exists("import"):
        return "host-import"
    fail("No screenshot backend found. Install pyautogui locally or provide a host capture tool such as spectacle.")


def capture_screen(output_path: Path, region: list[int] | None = None) -> str:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    backend = detect_capture_backend()

    if backend == "gnome-screenshot":
        subprocess.run(["gnome-screenshot", "-f", str(output_path)], check=True)
    elif backend == "pyautogui":
        pyautogui = import_pyautogui()
        pyautogui.screenshot(str(output_path))
    elif backend == "host-spectacle":
        result = run_host_command(["spectacle", "-b", "-n", "-o", str(output_path)], capture_output=True)
        if result.returncode != 0:
            message = (result.stderr or result.stdout or "unknown error").strip()
            fail(f"host screenshot failed: {message}")
    elif backend == "host-import":
        result = run_host_command(["import", "-window", "root", str(output_path)], capture_output=True)
        if result.returncode != 0:
            message = (result.stderr or result.stdout or "unknown error").strip()
            fail(f"host screenshot failed: {message}")
    else:
        fail(f"unknown screenshot backend: {backend}")

    if region is not None:
        left, top, width, height = normalize_region(region)
        Image = import_pillow_image()
        with Image.open(output_path) as image:
            cropped = image.crop((left, top, left + width, top + height))
            cropped.save(output_path)

    return backend


def locate_image_with_capture(image_path: Path, timeout: float, confidence: float, grayscale: bool,
                              region: list[int] | None) -> tuple[int, int] | None:
    cv2 = import_cv2()
    offset_x = 0
    offset_y = 0
    if region is not None:
        offset_x, offset_y, _, _ = normalize_region(region)

    deadline = time.time() + timeout
    while time.time() < deadline:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as handle:
            screenshot_path = Path(handle.name)

        try:
            capture_screen(screenshot_path, region)
            mode = cv2.IMREAD_GRAYSCALE if grayscale else cv2.IMREAD_COLOR
            haystack = cv2.imread(str(screenshot_path), mode)
            needle = cv2.imread(str(image_path), mode)
            if haystack is None:
                fail(f"failed to read screenshot: {screenshot_path}")
            if needle is None:
                fail(f"failed to read template image: {image_path}")

            result = cv2.matchTemplate(haystack, needle, cv2.TM_CCOEFF_NORMED)
            _, max_value, _, max_location = cv2.minMaxLoc(result)
            if max_value >= confidence:
                height, width = needle.shape[:2]
                return offset_x + max_location[0] + width // 2, offset_y + max_location[1] + height // 2
        finally:
            screenshot_path.unlink(missing_ok=True)

        time.sleep(0.2)

    return None


def normalize_key_name(key: str) -> str:
    if key.startswith("Key."):
        key = key[4:]

    mapping = {
        "alt": "Alt_L",
        "backspace": "BackSpace",
        "ctrl": "Control_L",
        "control": "Control_L",
        "delete": "Delete",
        "down": "Down",
        "enter": "Return",
        "esc": "Escape",
        "escape": "Escape",
        "left": "Left",
        "pagedown": "Next",
        "pageup": "Prior",
        "pgdn": "Next",
        "pgup": "Prior",
        "return": "Return",
        "right": "Right",
        "shift": "Shift_L",
        "space": "space",
        "tab": "Tab",
        "up": "Up",
    }
    return mapping.get(key.lower(), key)


def move_pointer(backend: str, x: int, y: int, duration: float = 0.0) -> None:
    if backend == "pyautogui":
        pyautogui = import_pyautogui()
        pyautogui.moveTo(x, y, duration=duration)
        return
    if backend == "host_xdotool":
        run_host_command(["xdotool", "mousemove", str(x), str(y)])
        return
    fail(f"unknown input backend: {backend}")


def click_pointer(backend: str, button: str = "left", presses: int = 1) -> None:
    if backend == "pyautogui":
        pyautogui = import_pyautogui()
        if presses == 2:
            pyautogui.doubleClick(button=button)
        else:
            pyautogui.click(button=button, clicks=presses)
        return
    if backend == "host_xdotool":
        button_map = {"left": "1", "middle": "2", "right": "3"}
        x_button = button_map.get(button, "1")
        run_host_command(["xdotool", "click", "--repeat", str(max(1, presses)), x_button])
        return
    fail(f"unknown input backend: {backend}")


def mouse_button(backend: str, button: str, pressed: bool) -> None:
    if backend == "pyautogui":
        pyautogui = import_pyautogui()
        if pressed:
            pyautogui.mouseDown(button=button)
        else:
            pyautogui.mouseUp(button=button)
        return
    if backend == "host_xdotool":
        button_map = {"left": "1", "middle": "2", "right": "3"}
        x_button = button_map.get(button, "1")
        action = "mousedown" if pressed else "mouseup"
        run_host_command(["xdotool", action, x_button])
        return
    fail(f"unknown input backend: {backend}")


def press_key(backend: str, key: str, presses: int = 1, interval: float = 0.05) -> None:
    if backend == "pyautogui":
        pyautogui = import_pyautogui()
        pyautogui.press(key, presses=presses, interval=interval)
        return
    if backend == "host_xdotool":
        normalized = normalize_key_name(key)
        for index in range(max(1, presses)):
            run_host_command(["xdotool", "key", normalized])
            if index + 1 < presses:
                time.sleep(interval)
        return
    fail(f"unknown input backend: {backend}")


def key_state(backend: str, key: str, pressed: bool) -> None:
    if backend == "pyautogui":
        pyautogui = import_pyautogui()
        if pressed:
            pyautogui.keyDown(key)
        else:
            pyautogui.keyUp(key)
        return
    if backend == "host_xdotool":
        action = "keydown" if pressed else "keyup"
        run_host_command(["xdotool", action, normalize_key_name(key)])
        return
    fail(f"unknown input backend: {backend}")


def press_hotkey(backend: str, keys: list[str]) -> None:
    if backend == "pyautogui":
        pyautogui = import_pyautogui()
        pyautogui.hotkey(*keys)
        return
    if backend == "host_xdotool":
        chord = "+".join(normalize_key_name(key) for key in keys)
        run_host_command(["xdotool", "key", chord])
        return
    fail(f"unknown input backend: {backend}")


def type_text(backend: str, text: str, interval: float = 0.02) -> None:
    if backend == "pyautogui":
        pyautogui = import_pyautogui()
        pyautogui.write(text, interval=interval)
        return
    if backend == "host_xdotool":
        delay_ms = max(1, int(interval * 1000))
        run_host_command(["xdotool", "type", "--delay", str(delay_ms), text])
        return
    fail(f"unknown input backend: {backend}")


def scroll_pointer(backend: str, clicks: int) -> None:
    if backend == "pyautogui":
        pyautogui = import_pyautogui()
        pyautogui.scroll(clicks)
        return
    if backend == "host_xdotool":
        button = "4" if clicks > 0 else "5"
        for _ in range(abs(clicks)):
            run_host_command(["xdotool", "click", button])
        return
    fail(f"unknown input backend: {backend}")


def try_capture_screenshot(output_path: Path) -> str | None:
    try:
        return capture_screen(output_path)
    except SystemExit:
        return None
    except Exception:
        return None


def collect_artifacts(output_dir: Path, log_dir: Path, include_screenshot: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    copied_any = False

    for log_name in ["Age3Log.txt", "Age3SessionData.txt"]:
        source = log_dir / log_name
        if not source.exists():
            continue
        shutil.copy2(source, output_dir / log_name)
        copied_any = True

    if include_screenshot:
        screenshot_path = output_dir / "desktop.png"
        backend = try_capture_screenshot(screenshot_path)
        if backend is not None:
            copied_any = True
            print(f"Captured screenshot via {backend}: {screenshot_path}")
        else:
            print("warning: screenshot capture backend unavailable", file=sys.stderr)

    if not copied_any:
        fail(f"No artifacts were collected from {log_dir}")

    print(f"Artifacts written to {output_dir}")


def probe_environment() -> None:
    print(f"session_type: {os.environ.get('XDG_SESSION_TYPE', 'unknown')}")
    print(f"display: {os.environ.get('DISPLAY', '') or '<unset>'}")
    print(f"wayland_display: {os.environ.get('WAYLAND_DISPLAY', '') or '<unset>'}")
    for command in ["ydotool", "wtype", "grim", "slurp", "gnome-screenshot", "xdotool"]:
        print(f"{command}: {'yes' if command_exists(command) else 'no'}")

    print(f"flatpak_spawn: {'yes' if can_spawn_host() else 'no'}")
    if can_spawn_host():
        for command in ["xdotool", "spectacle", "import", "ydotool", "ydotoold"]:
            print(f"host_{command}: {'yes' if host_command_exists(command) else 'no'}")
        print(f"host_xdotool_ready: {'yes' if host_xdotool_available() else 'no'}")

    for module in ["pyautogui", "PIL", "mss", "pynput"]:
        try:
            __import__(module)
            print(f"{module}: yes")
        except Exception:
            print(f"{module}: no")


def import_pyautogui():
    try:
        import pyautogui  # type: ignore
    except Exception as exc:
        fail(f"pyautogui import failed: {exc}")
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05
    return pyautogui


def maybe_import_pyautogui():
    try:
        import pyautogui  # type: ignore
    except Exception:
        return None
    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.05
    return pyautogui


def import_pynput():
    try:
        from pynput import keyboard, mouse  # type: ignore
    except Exception as exc:
        fail(f"pynput import failed: {exc}")
    return keyboard, mouse


def resolve_path(base_dir: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def normalize_region(region: list[int] | None) -> tuple[int, int, int, int] | None:
    if region is None:
        return None
    if len(region) != 4:
        fail("region must contain exactly 4 integers: [left, top, width, height]")
    return tuple(int(value) for value in region)


def locate_image(pyautogui, image_path: Path, timeout: float, confidence: float, grayscale: bool,
                 region: list[int] | None) -> tuple[int, int] | None:
    if pyautogui is None:
        return locate_image_with_capture(image_path, timeout, confidence, grayscale, region)

    deadline = time.time() + timeout
    search_region = normalize_region(region)
    while time.time() < deadline:
        try:
            point = pyautogui.locateCenterOnScreen(
                str(image_path),
                confidence=confidence,
                grayscale=grayscale,
                region=search_region,
            )
        except TypeError:
            point = pyautogui.locateCenterOnScreen(str(image_path), grayscale=grayscale, region=search_region)
        if point is not None:
            return int(point.x), int(point.y)
        time.sleep(0.2)
    return None


def run_flow(flow_path: Path, dry_run: bool) -> None:
    if not dry_run:
        detect_input_backend()
    payload = load_json(flow_path)
    if not isinstance(payload, dict):
        fail("flow file must contain an object")
    steps = payload.get("steps")
    if not isinstance(steps, list):
        fail("flow file must contain a 'steps' array")

    base_dir = flow_path.parent
    for index, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            fail(f"flow step {index} is not an object")
        action = step.get("action")
        if not isinstance(action, str):
            fail(f"flow step {index} is missing an action")

        print(f"[{index}/{len(steps)}] {action}")

        if action == "launch":
            command = step.get("command")
            if not command:
                fail("launch action requires 'command'")
            if dry_run:
                continue
            if isinstance(command, str):
                subprocess.Popen(command, shell=True)
            elif isinstance(command, list):
                subprocess.Popen(command)
            else:
                fail("launch command must be a string or array")
        elif action == "sleep":
            seconds = float(step.get("seconds", 1.0))
            time.sleep(seconds)
        elif action in {"wait_image", "click_image"}:
            image = step.get("image")
            if not isinstance(image, str):
                fail(f"{action} requires 'image'")
            image_path = resolve_path(base_dir, image)
            if not image_path.exists():
                fail(f"image not found: {image_path}")
            point = locate_image(
                None,
                image_path,
                timeout=float(step.get("timeout", 20.0)),
                confidence=float(step.get("confidence", 0.92)),
                grayscale=bool(step.get("grayscale", False)),
                region=step.get("region"),
            )
            if point is None:
                fail(f"timed out waiting for image: {image_path}")
            if action == "click_image" and not dry_run:
                backend = detect_input_backend()
                offset = step.get("offset", [0, 0])
                x = int(point[0] + int(offset[0]))
                y = int(point[1] + int(offset[1]))
                move_pointer(backend, x, y, duration=float(step.get("moveDuration", 0.15)))
                click_pointer(backend, presses=2 if step.get("double", False) else 1)
        elif action == "click":
            if dry_run:
                continue
            backend = detect_input_backend()
            move_pointer(backend, int(step["x"]), int(step["y"]), duration=float(step.get("moveDuration", 0.15)))
            click_pointer(backend)
        elif action == "press":
            if dry_run:
                continue
            backend = detect_input_backend()
            key = step.get("key")
            if not isinstance(key, str):
                fail("press action requires 'key'")
            press_key(backend, key, presses=int(step.get("presses", 1)), interval=float(step.get("interval", 0.05)))
        elif action == "hotkey":
            if dry_run:
                continue
            backend = detect_input_backend()
            keys = step.get("keys")
            if not isinstance(keys, list) or not keys:
                fail("hotkey action requires a non-empty 'keys' array")
            press_hotkey(backend, [str(key) for key in keys])
        elif action == "type_text":
            if dry_run:
                continue
            backend = detect_input_backend()
            text = step.get("text")
            if not isinstance(text, str):
                fail("type_text action requires 'text'")
            type_text(backend, text, interval=float(step.get("interval", 0.02)))
        elif action == "scroll":
            if dry_run:
                continue
            backend = detect_input_backend()
            scroll_pointer(backend, int(step.get("clicks", 0)))
        elif action == "screenshot":
            output = step.get("path")
            if not isinstance(output, str):
                fail("screenshot action requires 'path'")
            output_path = resolve_path(base_dir, output)
            if not dry_run:
                capture_screen(output_path)
        else:
            fail(f"unknown action: {action}")


def record_input(output_path: Path) -> None:
    ensure_runtime_support(needs_input=True)
    keyboard, mouse = import_pynput()
    events: list[dict[str, Any]] = []
    start = time.perf_counter()
    last_move_time = 0.0
    last_position: tuple[int, int] | None = None
    stop_state = {"active": False}

    def now() -> float:
        return round(time.perf_counter() - start, 4)

    def record(payload: dict[str, Any]) -> None:
        payload["t"] = now()
        events.append(payload)

    def on_move(x: int, y: int) -> None:
        nonlocal last_move_time, last_position
        current_time = time.perf_counter()
        if last_position is not None:
            dx = x - last_position[0]
            dy = y - last_position[1]
            if current_time - last_move_time < 0.02 and math.hypot(dx, dy) < 4.0:
                return
        last_move_time = current_time
        last_position = (x, y)
        record({"type": "move", "x": x, "y": y})

    def on_click(x: int, y: int, button, pressed: bool) -> None:
        record({"type": "click", "x": x, "y": y, "button": str(button), "pressed": pressed})

    def on_scroll(x: int, y: int, dx: int, dy: int) -> None:
        record({"type": "scroll", "x": x, "y": y, "dx": dx, "dy": dy})

    def normalize_key(key) -> str:
        if hasattr(key, "char") and key.char is not None:
            return key.char
        return str(key)

    def on_press(key) -> None:
        key_name = normalize_key(key)
        record({"type": "key_press", "key": key_name})
        if key_name == "Key.esc":
            stop_state["active"] = True
            return False
        return None

    def on_release(key) -> None:
        record({"type": "key_release", "key": normalize_key(key)})
        return None

    print("Recording started. Press Esc to stop.")
    mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
    keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    mouse_listener.start()
    keyboard_listener.start()
    keyboard_listener.join()
    mouse_listener.stop()
    mouse_listener.join()

    payload = {
        "version": 1,
        "recordedAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "events": events,
    }
    dump_json(output_path, payload)
    print(f"Recorded {len(events)} events to {output_path}")


def replay_input(input_path: Path, speed: float) -> None:
    backend = detect_input_backend()
    payload = load_json(input_path)
    events = payload.get("events") if isinstance(payload, dict) else None
    if not isinstance(events, list):
        fail("recording must contain an 'events' array")

    previous_time = 0.0
    button_map = {
        "Button.left": "left",
        "Button.middle": "middle",
        "Button.right": "right",
    }

    for event in events:
        if not isinstance(event, dict):
            continue
        event_time = float(event.get("t", 0.0))
        delay = max(0.0, (event_time - previous_time) / max(speed, 0.01))
        time.sleep(delay)
        previous_time = event_time

        event_type = event.get("type")
        if event_type == "move":
            move_pointer(backend, int(event["x"]), int(event["y"]))
        elif event_type == "click":
            button = button_map.get(str(event.get("button")), "left")
            x = int(event["x"])
            y = int(event["y"])
            move_pointer(backend, x, y)
            if bool(event.get("pressed", False)):
                mouse_button(backend, button, True)
            else:
                mouse_button(backend, button, False)
        elif event_type == "scroll":
            scroll_pointer(backend, int(event.get("dy", 0)))
        elif event_type == "key_press":
            key_name = str(event.get("key"))
            key_state(backend, key_name, True)
        elif event_type == "key_release":
            key_name = str(event.get("key"))
            key_state(backend, key_name, False)


def capture_reference(output_path: Path, region: list[int] | None) -> None:
    ensure_runtime_support(needs_input=False)
    capture_screen(output_path, region)
    print(f"Saved reference image to {output_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AoE3 DE desktop automation helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run-flow", help="Run an image-driven UI flow")
    run_parser.add_argument("flow", type=Path)
    run_parser.add_argument("--dry-run", action="store_true")

    record_parser = subparsers.add_parser("record-input", help="Record mouse and keyboard input until Esc")
    record_parser.add_argument("output", type=Path)

    replay_parser = subparsers.add_parser("replay-input", help="Replay a previously recorded input timeline")
    replay_parser.add_argument("input", type=Path)
    replay_parser.add_argument("--speed", type=float, default=1.0)

    capture_parser = subparsers.add_parser("capture-reference", help="Capture a screenshot for image matching")
    capture_parser.add_argument("output", type=Path)
    capture_parser.add_argument("--region", nargs=4, type=int)

    probe_parser = subparsers.add_parser("probe-environment", help="Report available desktop automation backends")

    artifacts_parser = subparsers.add_parser("collect-artifacts", help="Copy AoE3 logs and an optional screenshot")
    artifacts_parser.add_argument("output", type=Path)
    artifacts_parser.add_argument("--log-dir", type=Path, default=default_aoe3_log_dir())
    artifacts_parser.add_argument("--screenshot", action="store_true")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "run-flow":
        run_flow(args.flow.resolve(), args.dry_run)
    elif args.command == "record-input":
        record_input(args.output.resolve())
    elif args.command == "replay-input":
        replay_input(args.input.resolve(), args.speed)
    elif args.command == "capture-reference":
        capture_reference(args.output.resolve(), args.region)
    elif args.command == "probe-environment":
        probe_environment()
    elif args.command == "collect-artifacts":
        collect_artifacts(args.output.resolve(), args.log_dir.resolve(), args.screenshot)
    else:
        parser.error("unknown command")


if __name__ == "__main__":
    main()