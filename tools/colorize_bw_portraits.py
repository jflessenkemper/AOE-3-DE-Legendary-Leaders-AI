#!/usr/bin/env python3
"""DEPRECATED — DO NOT RUN.

This script applied a hard-coded warm-brown duotone overlay
(`PIL.ImageOps.colorize()` with DARK=(42,24,16), MID=(160,102,78),
LIGHT=(245,212,176)) to every avatar PNG below a chroma threshold of 12.

The threshold caught not just true B&W photos but also slightly-desaturated
period oil paintings and sepia photographs that *did* contain colour
information. The duotone overlay produced uniformly orange portraits for
~14 leaders, including Hiawatha, Mannerheim, Usman, Diponegoro, Cuza,
Kruger, Sam Houston, and others whose source images in `art/ui/leaders/`
are genuinely full colour.

The replacement is `tools/rebuild_portraits.py`, which:
  - Reads the high-res colour source from `art/ui/leaders/<source>`
  - Centre-crops to a square (preserving the face)
  - Resizes to 256×256 with LANCZOS
  - Applies a light unsharp-mask
  - Writes RGB/RGBA PNG with NO colour alteration

For sources that ARE genuinely B&W (Menelik, Carrillo Puerto), the output
is clean neutral greyscale, which is preferable to false-colour duotone.

If you're reading this because a CI step ran this file and orange portraits
came back: use `tools/rebuild_portraits.py` and pull replacement colour
sources from Wikimedia for any genuinely-B&W leaders that remain.
"""
import sys

print(__doc__, file=sys.stderr)
sys.exit(2)
