#!/usr/bin/env python3
"""Visual consistency check for the 48 leader portraits.

Soft-skip if ANTHROPIC_API_KEY isn't set — the static `validate_art_coverage`
already covers the hard gates (file existence, valid PNG header). This
script answers the *qualitative* question:

    "Do these 48 portraits look like one consistent art set, or is one
     obviously off (wrong DPI, AI-upscaled, wrong border treatment)?"

It splits the 48 icons into batches of 8 and asks Haiku per batch. Total
cost ≈ $0.05 at current Haiku pricing (well under the Opus baseline this
project tries to avoid).

Usage:
    python3 tools/validation/validate_art_consistency.py            # dry-run
    AOE3_RUN_VISION=1 python3 tools/validation/validate_art_consistency.py
"""
from __future__ import annotations
import argparse
import base64
import json
import os
import re
import sys
import urllib.request
import urllib.error
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AI_DIR = REPO / "game" / "ai"

_API_URL = "https://api.anthropic.com/v1/messages"
_API_VERSION = "2023-06-01"
_MODEL = os.environ.get("AOE3_VISION_MODEL", "claude-haiku-4-5-20251001")
_TIMEOUT = float(os.environ.get("AOE3_VISION_TIMEOUT", "60"))
_BATCH_SIZE = 8

_SYSTEM = (
    "You audit visual consistency of UI portrait icons for a video-game mod. "
    "Given N portraits in a single message, decide if they belong to the "
    "same art set: comparable framing, comparable resolution, comparable "
    "border/treatment, no obvious AI upscaling artifacts. Respond with a "
    "single JSON object on one line, no prose, no markdown:\n"
    '  {"consistent": true|false, "outliers": [<filename>, ...], '
    '"reason": "<short>"}'
)


def _personality_icons() -> list[Path]:
    icons: list[Path] = []
    for p in sorted(AI_DIR.glob("*.personality")):
        m = re.search(r"<icon>([^<]+)</icon>", p.read_text(encoding="utf-8", errors="ignore"))
        if m:
            f = REPO / m.group(1).strip()
            if f.exists():
                icons.append(f)
    return icons


def _b64(p: Path) -> str | None:
    try:
        data = p.read_bytes()
    except OSError:
        return None
    if not data or len(data) > 5 * 1024 * 1024:
        return None
    return base64.standard_b64encode(data).decode("ascii")


def _judge_batch(paths: list[Path], api_key: str) -> dict:
    images = []
    for p in paths:
        b = _b64(p)
        if b is None:
            continue
        images.append({"type": "image", "source": {
            "type": "base64", "media_type": "image/png", "data": b}})
        images.append({"type": "text", "text": p.name})
    if not images:
        return {"consistent": None, "reason": "no images readable"}

    payload = {
        "model": _MODEL,
        "max_tokens": 512,
        "system": _SYSTEM,
        "messages": [{
            "role": "user",
            "content": images + [{
                "type": "text",
                "text": f"Audit these {len(paths)} portraits for visual consistency. "
                        f"Reply with the JSON object only.",
            }],
        }],
    }

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(_API_URL, data=body, method="POST", headers={
        "x-api-key": api_key,
        "anthropic-version": _API_VERSION,
        "content-type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        return {"consistent": None, "reason": f"API error: {e}"}

    text = ""
    for blk in data.get("content", []):
        if isinstance(blk, dict) and blk.get("type") == "text":
            text = blk.get("text", "").strip()
            break
    # Tolerate fenced output.
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.M)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"consistent": None, "reason": f"non-JSON response: {text[:200]}"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="just list what would be sent (no API calls)")
    args = ap.parse_args(argv)

    icons = _personality_icons()
    print(f"Collected {len(icons)} portrait icons")
    batches = [icons[i:i + _BATCH_SIZE] for i in range(0, len(icons), _BATCH_SIZE)]
    print(f"Will audit in {len(batches)} batches of up to {_BATCH_SIZE}")

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    run_live = os.environ.get("AOE3_RUN_VISION") == "1"

    if args.dry_run or not api_key or not run_live:
        why = ("dry-run" if args.dry_run
               else "ANTHROPIC_API_KEY not set" if not api_key
               else "set AOE3_RUN_VISION=1 to run")
        print(f"\nSoft-skipping live audit ({why}).")
        for i, b in enumerate(batches):
            print(f"  batch {i+1}: {', '.join(p.name for p in b)}")
        return 0

    fails = 0
    for i, b in enumerate(batches):
        v = _judge_batch(b, api_key)
        ok = v.get("consistent")
        marker = "OK" if ok is True else ("SKIP" if ok is None else "FAIL")
        print(f"batch {i+1}: {marker}  {v.get('reason', '')}")
        if v.get("outliers"):
            print(f"    outliers: {', '.join(v['outliers'])}")
        if ok is False:
            fails += 1
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
