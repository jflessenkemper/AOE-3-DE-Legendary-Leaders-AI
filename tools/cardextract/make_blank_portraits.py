"""Ship blank (all-black, fully-transparent) DDT avatar files so the base-game
cpai_avatar_<civ>.ddt doesn't show Queen Elizabeth / Napoleon / Ivan / etc.
in the Skirmish lobby portrait slot.

The existing .ddt files live in ArtUI.bar under `Art/ui/singleplayer/`.
A mod file at `art/ui/singleplayer/cpai_avatar_<civ>.ddt` should override.

DDT format (AoE3 DE RTS3 variant):
  0-3:  magic b"RTS3"
  4:    usage byte (0 = AlbedoMap)
  5:    alpha byte (1 = player color, 4 = binary, 8 = alpha blend)
  6:    format byte (1 = DXT1, 4 = grey, 7 = DXT3, 8 = DXT5)
  7:    mip count (1 for no mips)
  8-11: width (u32 LE)
  12-15: height (u32 LE)
  16-19: first-mip size (u32 LE)
  20-...: DXT-compressed pixel data

DXT1 for a 64x64 image: 4x4 block pixel groups = 16 x 16 = 256 blocks,
each block = 8 bytes = 2048 bytes of pixel data total.

For an all-transparent black DXT1 block:
  color0 = 0x0000 (black RGB565)
  color1 = 0x0000 (black RGB565)  [color0 <= color1 so 1-bit alpha mode]
  indices = 0xFFFFFFFF  (all 11 index = transparent in 1-bit-alpha mode)
That's 8 bytes all 0x00 + 4 bytes all 0xFF = specifically b"\\x00\\x00\\x00\\x00\\xff\\xff\\xff\\xff"

Actually simpler: color0 = color1 = 0 and indices 0 → all pixels = color0 = black opaque.
b"\\x00" * 8 per block = all-black opaque.

Since we just want the portrait invisible, all-black works; the frame around
the avatar slot visually reads as "no portrait". If the UI renders with alpha
blending, all-zero could also render as fully transparent.
"""
from __future__ import annotations

import shutil
import struct
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ART_DIR = REPO / "art" / "ui" / "singleplayer"
ART_DIR.mkdir(parents=True, exist_ok=True)

# 22 base civs whose lobby portrait currently shows the wrong leader
BASE_CIVS = [
    "british", "french", "spanish", "portuguese", "dutch", "germans",
    "russians", "ottomans", "swedes", "italians", "maltese", "mexicans",
    "chinese", "japanese", "indians", "aztecs", "inca",
    "haudenosaunee", "lakota", "hausa", "ethiopians", "united_states",
]


def build_blank_ddt(width: int = 64, height: int = 64) -> bytes:
    """Build an all-black DXT1 DDT matching the AoE3 RTS3 layout."""
    header = bytearray(16)
    header[0:4] = b"RTS3"
    header[4] = 0   # usage = AlbedoMap
    header[5] = 0   # alpha = none
    header[6] = 1   # format = DXT1
    header[7] = 1   # mip count
    struct.pack_into("<I", header, 8, width)
    struct.pack_into("<I", header, 12, height)

    # DXT1: 8 bytes per 4x4 block
    n_blocks = (width // 4) * (height // 4)
    block = b"\x00" * 8  # color0=0, color1=0, indices=0 → all pixels black (0,0,0)
    pixel_data = block * n_blocks

    first_mip_size = struct.pack("<I", len(pixel_data))

    return bytes(header) + first_mip_size + pixel_data


def main():
    blob = build_blank_ddt()
    print(f"Blank DDT size: {len(blob)} bytes")

    for civ in BASE_CIVS:
        dst = ART_DIR / f"cpai_avatar_{civ}.ddt"
        dst.write_bytes(blob)
        print(f"  wrote {dst.relative_to(REPO)} ({len(blob)} B)")

    print(f"\nWrote {len(BASE_CIVS)} blank DDT portraits.")


if __name__ == "__main__":
    main()
