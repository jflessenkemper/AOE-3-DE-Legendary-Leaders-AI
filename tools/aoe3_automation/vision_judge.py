"""Claude-vision semantic judge for matrix screenshots.

Closes the only gap pHash/OCR couldn't honestly cover: "does this screenshot
*look like* the right civ playing the right doctrine?"  We send each captured
PNG to the Anthropic Messages API with a context-aware prompt that bakes in
the civ's expected doctrine from ``LEGENDARY_LEADERS_TREE.html``, and Opus
returns a structured pass/fail with reasoning.

Stdlib only — no ``anthropic`` SDK dep — so the matrix stays self-contained.
The endpoint contract is the public Messages API; if Anthropic ever ships a
breaking schema change the worst-case is one CI run failing with a clear
error rather than an opaque import-time crash.

Usage from matrix_runner::

    from tools.aoe3_automation.vision_judge import judge_screenshot

    verdict = judge_screenshot(
        image_path,
        civ_name="French",
        scene="loading",
        doctrine_summary="Frontier+Open heading=Outward, MobileNoWalls, "
                         "expects forward base, expects naval=False",
    )
    # verdict = {"pass": True, "confidence": 0.9, "reason": "..."}
    # verdict = {"pass": False, "reason": "...", "issues": [...]}
    # verdict = {"pass": None, "reason": "no_api_key"}   # soft-skip

Env config:
  ANTHROPIC_API_KEY   — required; absence makes the axis soft-skip.
  AOE3_VISION_MODEL   — override model id (default: claude-opus-4-5).
  AOE3_VISION_TIMEOUT — request timeout seconds (default: 60).
"""
from __future__ import annotations

import base64
import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional

_API_URL = "https://api.anthropic.com/v1/messages"
_API_VERSION = "2023-06-01"
_DEFAULT_MODEL = os.environ.get("AOE3_VISION_MODEL", "claude-opus-4-5")
_DEFAULT_TIMEOUT = float(os.environ.get("AOE3_VISION_TIMEOUT", "60"))

# Hard cap so the matrix never burns the context budget on a single image —
# Claude vision tops out around 8k px on the long edge anyway.
_MAX_IMAGE_BYTES = 5 * 1024 * 1024


# Per-scene prompt templates. Each one frames the question narrowly enough
# that the model returns a tight pass/fail rather than a free-form essay.
_SCENE_PROMPTS = {
    "loading": (
        "This is the AoE3 DE loading screen captured during a single-player "
        "skirmish where Player 1 is the human and the AI opponents include "
        "{civ_name}. The expected doctrine for {civ_name} is:\n\n"
        "{doctrine_summary}\n\n"
        "Confirm the loading screen looks legitimate (leader card / civ "
        "portrait visible, AoE3 art style, no obvious render glitches). "
        "Doctrine compliance is NOT judged from this scene — only verify "
        "the load did not visually fail."
    ),
    "in_game": (
        "This is mid-match HUD from the AoE3 DE skirmish where Player 1 is "
        "{civ_name}. The HTML doctrine reference promises:\n\n"
        "{doctrine_summary}\n\n"
        "Look at the resource bar, building distribution, units visible, and "
        "minimap. Check: (1) the HUD is real (not a loading screen, not a "
        "menu), (2) the visible buildings/units are consistent with this "
        "civ's age and doctrine direction, (3) no obvious crash overlays or "
        "error dialogs."
    ),
    "scoreboard": (
        "This is the AoE3 DE scoreboard overlay (Tab key) captured during "
        "a skirmish. The civs in the match are: {batch_civs}. Each civ should "
        "appear with a non-zero score column. Confirm: (1) the scoreboard "
        "lists every expected civ, (2) the layout is the real AoE3 "
        "scoreboard (player rows, score columns, civ icons), (3) no crash "
        "overlay or error dialog is on top."
    ),
}


_SYSTEM = (
    "You are a strict QA judge for a video-game test matrix. You evaluate "
    "screenshots from Age of Empires III: Definitive Edition against expected "
    "civ + doctrine state. You ALWAYS respond with a single JSON object on "
    "one line, no prose, no markdown fences. Schema:\n"
    '  {"pass": true|false, "confidence": 0..1, "reason": "<short>", '
    '"issues": ["<short>", ...]}\n'
    "Be rigorous: only return pass=true if the screenshot is a real, "
    "non-corrupted in-game frame consistent with the stated civ/doctrine. "
    "Solid-colour images, menu screens when in-game was expected, crash "
    "overlays, and missing UI elements all = pass:false."
)


def _b64_image(path: Path) -> Optional[str]:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if not data or len(data) > _MAX_IMAGE_BYTES:
        return None
    return base64.standard_b64encode(data).decode("ascii")


def _post_json(payload: dict, *, api_key: str, timeout: float) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        _API_URL,
        data=body,
        method="POST",
        headers={
            "x-api-key": api_key,
            "anthropic-version": _API_VERSION,
            "content-type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _extract_text(api_response: dict) -> str:
    """Pull the first text block out of a Messages API response."""
    for block in api_response.get("content", []):
        if isinstance(block, dict) and block.get("type") == "text":
            return block.get("text", "")
    return ""


def _parse_verdict(text: str) -> dict:
    """The system prompt asks for one-line JSON; be defensive anyway."""
    text = text.strip()
    # Strip accidental code fences if the model added them.
    if text.startswith("```"):
        text = text.strip("`")
        # remove leading "json\n" if present
        if text.lower().startswith("json"):
            text = text[4:].lstrip()
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        # Last-ditch: scan for the first {...} balanced span.
        depth = 0
        start = -1
        for i, c in enumerate(text):
            if c == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0 and start >= 0:
                    try:
                        obj = json.loads(text[start:i + 1])
                        break
                    except json.JSONDecodeError:
                        continue
        else:
            return {"pass": False, "reason": "model returned non-JSON",
                    "raw": text[:300]}
    if not isinstance(obj, dict):
        return {"pass": False, "reason": "model returned non-object",
                "raw": text[:300]}
    # Normalise types.
    obj["pass"] = bool(obj.get("pass"))
    if "confidence" in obj:
        try:
            obj["confidence"] = float(obj["confidence"])
        except (TypeError, ValueError):
            obj["confidence"] = 0.0
    obj.setdefault("issues", [])
    obj.setdefault("reason", "")
    return obj


def judge_screenshot(image_path: Path,
                     *,
                     civ_name: str,
                     scene: str,
                     doctrine_summary: str = "",
                     batch_civs: Optional[list[str]] = None,
                     model: Optional[str] = None,
                     timeout: Optional[float] = None,
                     ) -> dict:
    """Send ``image_path`` to Claude vision and return the parsed verdict.

    Always returns a dict; never raises. ``pass`` is ``None`` only when the
    axis must soft-skip (no API key configured / image unreadable). Caller
    should treat ``pass=None`` as "axis not exercised this run" rather than
    a fail.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return {"pass": None, "reason": "ANTHROPIC_API_KEY not set"}

    if scene not in _SCENE_PROMPTS:
        return {"pass": False, "reason": f"unknown scene {scene!r}"}

    b64 = _b64_image(image_path)
    if b64 is None:
        return {"pass": None,
                "reason": f"image unreadable / too large: {image_path}"}

    prompt = _SCENE_PROMPTS[scene].format(
        civ_name=civ_name,
        doctrine_summary=doctrine_summary or "(no expectation row found)",
        batch_civs=", ".join(batch_civs or [civ_name]),
    )

    payload = {
        "model": model or _DEFAULT_MODEL,
        "max_tokens": 512,
        "system": _SYSTEM,
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": b64,
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }],
    }

    try:
        resp = _post_json(payload, api_key=api_key,
                          timeout=timeout or _DEFAULT_TIMEOUT)
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8", "replace")
        except Exception:
            err_body = ""
        return {"pass": False,
                "reason": f"vision API HTTP {e.code}: {err_body[:200]}"}
    except (urllib.error.URLError, TimeoutError) as e:
        return {"pass": None, "reason": f"vision API unreachable: {e}"}
    except Exception as e:  # pragma: no cover - defensive
        return {"pass": None, "reason": f"vision API error: {e}"}

    text = _extract_text(resp)
    verdict = _parse_verdict(text)
    verdict["model"] = resp.get("model", model or _DEFAULT_MODEL)
    verdict["scene"] = scene
    verdict["civ"] = civ_name
    return verdict


def doctrine_summary_from_expectation(exp) -> str:
    """Format a CivExpectation into a one-line doctrine summary the model
    can use as the ground-truth contract for that civ."""
    if exp is None:
        return "(no expectation row found)"
    parts = [
        f"leader_key={getattr(exp, 'leader_key', '?')}",
        f"terrain={getattr(exp, 'terrain_primary', '?')}+"
        f"{getattr(exp, 'terrain_secondary', '?')}",
        f"heading={getattr(exp, 'heading', '?')}",
        f"heading_axis={getattr(exp, 'heading_axis', '?')}",
        f"water_bias={getattr(exp, 'water_bias', '?')}",
    ]
    return ", ".join(parts)


__all__ = [
    "judge_screenshot",
    "doctrine_summary_from_expectation",
]
