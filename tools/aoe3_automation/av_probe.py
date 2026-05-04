"""Audio + visual probes for the matrix runner.

Two thin wrappers used to close the last "is anything actually happening?"
gaps the matrix runner couldn't see:

  * audio_rms_dbfs(seconds)        — record N seconds from PipeWire and
                                     return the RMS amplitude in dBFS
                                     (-inf for pure silence, 0 for full
                                     scale).  Used to confirm leader-voice
                                     and music actually play.

  * screenshot_with_keypress()     — press a chord (e.g. "Tab") then call
                                     AoE3's in-game PrintScreen binding
                                     while it's held, so the scoreboard is
                                     visible in the captured PNG.

  * threaded_screenshot_after()    — fire-and-forget delayed screenshot.
                                     Kicked off right after click_play()
                                     so we capture the leader-card during
                                     loading without blocking the
                                     wait_for_in_game() path.

All three are best-effort.  If PipeWire or xdotool isn't reachable they
return ``None`` / ``False`` rather than raise; the validator treats absent
data as a soft fail (axis = "skip"), not a hard failure.
"""
from __future__ import annotations

import math
import os
import struct
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable, Optional

# Reuse the AoE3-internal screenshot path; it's the only capture method
# that returns real pixels on this rig (gamescope direct-to-GPU bypasses
# the host compositor).
from tools.aoe3_automation.in_game_driver import _screenshot_raw, _focus_window  # noqa: E402

# PipeWire / PulseAudio monitor source.  AoE3 + Proton route through the
# default sink, so its monitor is the only reliable global capture point.
# parec auto-resolves "@DEFAULT_MONITOR@" to whatever the current default
# sink's monitor source is.
_PAREC_SOURCE = os.environ.get("AOE3_AUDIO_SOURCE", "@DEFAULT_MONITOR@")
# 16-bit signed LE mono @ 16 kHz keeps post-processing trivial.
_PAREC_FMT = ["--format=s16le", "--rate=16000", "--channels=1"]


def audio_rms_dbfs(seconds: float = 3.0,
                   source: str = _PAREC_SOURCE) -> Optional[float]:
    """Record ``seconds`` of audio from the default monitor source and
    return the RMS amplitude in dBFS.

    Returns:
        float dBFS in (-inf, 0]: 0 ⇒ full-scale, -60 ⇒ near-silent.
        None if parec is unavailable or recording fails.

    A normal AoE3 game loop sits around -25 to -10 dBFS during music+SFX.
    Leader-voice cues spike to ~-12 dBFS for ~2 s.  A reading below
    -55 dBFS is "effectively silent" — leader voice asset missing or the
    mod's sound bank failed to mount.
    """
    samples_needed = int(seconds * 16000)
    bytes_needed = samples_needed * 2
    cmd = ["parec", *_PAREC_FMT, "-d", source]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        return None
    try:
        buf = bytearray()
        deadline = time.monotonic() + seconds + 1.0
        while len(buf) < bytes_needed and time.monotonic() < deadline:
            chunk = proc.stdout.read(min(8192, bytes_needed - len(buf)))
            if not chunk:
                break
            buf.extend(chunk)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=1.0)
        except subprocess.TimeoutExpired:
            proc.kill()
    if len(buf) < 2:
        return None
    n = len(buf) // 2
    samples = struct.unpack(f"<{n}h", bytes(buf[:n * 2]))
    if not samples:
        return None
    sumsq = 0
    for s in samples:
        sumsq += s * s
    rms = math.sqrt(sumsq / n)
    if rms <= 0:
        return float("-inf")
    return 20.0 * math.log10(rms / 32768.0)


# ---------------------------------------------------------------------------
# Visual capture helpers
# ---------------------------------------------------------------------------


def threaded_screenshot_after(delay_s: float, path: Path) -> threading.Thread:
    """Sleep ``delay_s`` then call _screenshot_raw(path).  Non-blocking.

    Returns the running Thread so the caller can ``join()`` if desired.
    """
    def _run() -> None:
        time.sleep(delay_s)
        try:
            _screenshot_raw(path)
        except Exception as e:  # pragma: no cover - best-effort
            print(f"[av_probe] threaded screenshot warn: {e}")
    t = threading.Thread(target=_run, daemon=True, name="av_probe.shot")
    t.start()
    return t


def screenshot_with_keypress(chord: str, path: Path,
                             *, hold_s: float = 1.0) -> bool:
    """Press ``chord`` (e.g. "Tab"), wait briefly for the UI to react, fire
    AoE3's PrintScreen binding, then release the chord.

    The scoreboard overlay stays open only while Tab is held, so the chord
    must remain pressed across the screenshot keystroke.  We use
    ``xdotool keydown`` / ``keyup`` rather than ``key`` so the press is held.
    """
    env = os.environ.copy()
    env.setdefault("DISPLAY", ":1")
    try:
        _focus_window()
        subprocess.run(["xdotool", "keydown", chord],
                       env=env, capture_output=True, check=False)
        time.sleep(hold_s)
        ok = _screenshot_raw(path)
        time.sleep(0.2)
        subprocess.run(["xdotool", "keyup", chord],
                       env=env, capture_output=True, check=False)
        return ok
    except Exception as e:  # pragma: no cover - best-effort
        print(f"[av_probe] keypress shot warn: {e}")
        try:
            subprocess.run(["xdotool", "keyup", chord],
                           env=env, capture_output=True, check=False)
        except Exception:
            pass
        return False


def background_audio_probe(seconds: float, *,
                           on_done: Callable[[Optional[float]], None]
                           ) -> threading.Thread:
    """Run audio_rms_dbfs() in a background thread; deliver the dBFS value
    via ``on_done(dbfs)`` when complete.

    Lets the matrix runner kick off audio capture during the loading
    screen without blocking wait_for_in_game.
    """
    def _run() -> None:
        try:
            on_done(audio_rms_dbfs(seconds))
        except Exception as e:  # pragma: no cover
            print(f"[av_probe] background audio warn: {e}")
            on_done(None)
    t = threading.Thread(target=_run, daemon=True, name="av_probe.audio")
    t.start()
    return t


# ---------------------------------------------------------------------------
# Visual content checks
# ---------------------------------------------------------------------------


def image_has_content(path: Path,
                      *,
                      min_bytes: int = 50_000,
                      min_stddev: float = 8.0) -> bool:
    """Return True iff ``path`` is a non-trivial image — large enough on
    disk AND has pixel variance (not a solid-colour fallback).

    gamescope occasionally hands back uniform-black PNGs when the capture
    races a frame swap. We want a green visual axis to mean "real pixels
    were captured", not "any file exists".
    """
    try:
        if not path.exists() or path.stat().st_size < min_bytes:
            return False
        from PIL import Image, ImageStat  # type: ignore
        with Image.open(path) as im:
            im = im.convert("L")  # luminance
            stat = ImageStat.Stat(im)
            return stat.stddev[0] >= min_stddev
    except Exception:
        return False


def image_contains_words(path: Path, words: list[str],
                         *, min_hits: int = 1) -> tuple[bool, list[str]]:
    """OCR ``path`` (via pytesseract if available) and return
    (matched, hits) where ``matched`` is True iff at least ``min_hits``
    of the wanted words appear in the recovered text.

    Falls back to (None-equivalent) when pytesseract is unavailable: in
    that case we return (False, []) and the caller is expected to treat
    the missing tooling as a soft fail (axis = "skip").
    """
    try:
        if not image_has_content(path):
            return (False, [])
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore
        with Image.open(path) as im:
            text = pytesseract.image_to_string(im)
        text_lower = text.lower()
        hits = [w for w in words if w.lower() in text_lower]
        return (len(hits) >= min_hits, hits)
    except Exception:
        return (False, [])


# ---------------------------------------------------------------------------
# Perceptual hashing — pixel-accurate visual diff, vendored
# ---------------------------------------------------------------------------
#
# We avoid the third-party ``imagehash`` package (extra deploy surface) by
# implementing the two hashes that matter here directly on PIL:
#
#   * aHash (average hash): downscale → grayscale → 8x8 → bit per pixel ≥ mean.
#                           Cheap, robust to small geometric jitter.
#   * dHash (difference hash): downscale to 9x8 → bit per (px > right neighbour).
#                              Robust to brightness shifts, picks up structure.
#
# Both produce 64-bit ints; Hamming distance ≤ 10 (out of 64) means "same
# scene" in practice. We compare against per-civ golden references stored as
# JSON next to the artifact tree (one captured baseline per scene per civ).
#
# The axis flips green when either hash matches within threshold — so a small
# engine-render delta on one cue (loading-art animation phase) doesn't false-
# fail the whole axis if structure (dHash) still matches.


def _ahash64(image_path: Path) -> int | None:
    """Vendored 8x8 average-hash. Returns 64-bit int or None on failure."""
    try:
        from PIL import Image  # type: ignore
        with Image.open(image_path) as im:
            im = im.convert("L").resize((8, 8))
            pixels = list(im.getdata())
        if len(pixels) != 64:
            return None
        avg = sum(pixels) / 64.0
        h = 0
        for p in pixels:
            h = (h << 1) | (1 if p >= avg else 0)
        return h
    except Exception:
        return None


def _dhash64(image_path: Path) -> int | None:
    """Vendored 9x8 difference-hash. Returns 64-bit int or None on failure."""
    try:
        from PIL import Image  # type: ignore
        with Image.open(image_path) as im:
            im = im.convert("L").resize((9, 8))
            pixels = list(im.getdata())
        if len(pixels) != 72:
            return None
        h = 0
        for row in range(8):
            for col in range(8):
                left = pixels[row * 9 + col]
                right = pixels[row * 9 + col + 1]
                h = (h << 1) | (1 if left > right else 0)
        return h
    except Exception:
        return None


def _hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def image_phash(path: Path) -> dict | None:
    """Return ``{"ahash": int, "dhash": int}`` for ``path`` or None on failure.

    Used both by the runner (compute a hash for every captured PNG) and the
    validator (compare against the per-civ golden reference)."""
    a = _ahash64(path)
    d = _dhash64(path)
    if a is None and d is None:
        return None
    return {"ahash": a, "dhash": d}


def image_matches_golden(captured_hash: dict | None,
                         golden_hash: dict | None,
                         *, max_distance: int = 10) -> bool:
    """Compare two ``image_phash`` dicts. Returns True iff EITHER aHash or
    dHash distance is within ``max_distance`` (out of 64 bits).

    The OR rule trades a tiny precision loss for substantial robustness to
    AoE3's animated leader cards — frames captured during a card slide can
    have a 10–15 bit aHash drift while keeping a tight dHash.
    """
    if not captured_hash or not golden_hash:
        return False
    ok = False
    if captured_hash.get("ahash") is not None and golden_hash.get("ahash") is not None:
        if _hamming(captured_hash["ahash"], golden_hash["ahash"]) <= max_distance:
            ok = True
    if not ok and captured_hash.get("dhash") is not None and golden_hash.get("dhash") is not None:
        if _hamming(captured_hash["dhash"], golden_hash["dhash"]) <= max_distance:
            ok = True
    return ok


__all__ = [
    "audio_rms_dbfs",
    "threaded_screenshot_after",
    "screenshot_with_keypress",
    "background_audio_probe",
    "image_has_content",
    "image_contains_words",
    "image_phash",
    "image_matches_golden",
]
