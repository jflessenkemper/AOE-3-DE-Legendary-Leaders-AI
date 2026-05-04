#!/usr/bin/env python3
"""Rebuild leader avatar PNGs from the high-resolution colour source images
in `art/ui/leaders/`, with NO duotone overlay.

Background
──────────
A previous batch run (the now-deprecated `tools/colorize_bw_portraits.py`)
ran `PIL.ImageOps.colorize()` over EVERY portrait that fell below a chroma
threshold. That threshold caught not just true B&W photographs but also
slightly-desaturated period oil paintings and sepia photographs that *did*
contain colour information. The duotone overlay produced uniformly orange
images for ~14 leaders.

This script does the right thing:

  1. Read the high-res source from art/ui/leaders/<source>
  2. Crop to a centred square (preserving the face)
  3. Resize to 256×256 with LANCZOS
  4. Optional: apply a light unsharp mask to compensate for resize blur
  5. Save as RGB (or RGBA if a roundel mask is requested) PNG to
     resources/images/icons/singleplayer/<target>.png

NO COLOR ALTERATION. Source colour is preserved verbatim. If the source is
genuinely B&W, the output is clean greyscale — never orange duotone.

Usage:
    python3 tools/rebuild_portraits.py            # rebuild all 14 leaders
    python3 tools/rebuild_portraits.py --dry-run  # show plan without writing
    python3 tools/rebuild_portraits.py --check    # chroma-audit current PNGs
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps

REPO = Path(__file__).resolve().parent.parent
SRC_DIR = REPO / "art/ui/leaders"
DST_DIR = REPO / "resources/images/icons/singleplayer"
TARGET = 256


@dataclass(frozen=True)
class PortraitJob:
    leader: str               # human-readable label
    source: str               # filename in art/ui/leaders/
    targets: tuple[str, ...]  # one or more target filenames in DST_DIR
    crop_y_pct: float = 0.0   # vertical bias for face crop: 0.0 = top half,
                              # 0.5 = exact centre, -0.2 = lift face higher.
                              # Most portrait paintings centre the face above
                              # the geometric centre, so we shave a bit from
                              # the bottom by default.


# Mapping: art/ui/leaders/ source → resources/images/icons/singleplayer/ target.
# Built from the audit output (14 problem files) + their colour-rich sources.
JOBS: tuple[PortraitJob, ...] = (
    PortraitJob("Hiawatha (Haudenosaunee)", "hiawatha.png",
                ("cpai_avatar_haudenosaunee.png",
                 "cpai_avatar_haudenosaunee_hiawatha.png"),
                crop_y_pct=-0.10),
    PortraitJob("Mannerheim (Finnish)", "mannerheim.png",
                ("cpai_avatar_finnish_mannerheim.png",),
                crop_y_pct=-0.05),
    PortraitJob("Papineau (French Canadian)", "papineau.png",
                ("cpai_avatar_french_canadians_papineau.png",),
                crop_y_pct=-0.10),
    PortraitJob("Usman dan Fodio (Hausa)", "usman_dan_fodio.png",
                ("cpai_avatar_hausa.png",
                 "cpai_avatar_hausa_usman.png"),
                crop_y_pct=-0.05),
    PortraitJob("Diponegoro (Indonesians)", "diponegoro.png",
                ("cpai_avatar_indonesians_diponegoro.png",),
                crop_y_pct=-0.15),
    PortraitJob("Canales Rosillo (Rio Grande)", "canales_rosillo.png",
                ("cpai_avatar_rio_grande_canales_rosillo.png",),
                crop_y_pct=-0.05),
    PortraitJob("Cuza (Romanians)", "cuza.png",
                ("cpai_avatar_romanians_cuza.png",),
                crop_y_pct=-0.20),
    PortraitJob("Kruger (South Africans)", "kruger.png",
                ("cpai_avatar_south_africans_kruger.png",),
                crop_y_pct=-0.05),
    PortraitJob("Sam Houston (Texians)", "sam_houston.png",
                ("cpai_avatar_texians_sam_houston.png",),
                crop_y_pct=-0.20),
    PortraitJob("Carrillo Puerto (Yucatan)", "carrillo_puerto.png",
                ("cpai_avatar_yucatan_carrillo_puerto.png",),
                crop_y_pct=-0.05),
    PortraitJob("Menelik II (Ethiopians)", "menelik.png",
                ("cpai_avatar_ethiopians.png",
                 "cpai_avatar_ethiopians_menelik.png"),
                crop_y_pct=-0.05),
)


def chroma_score(img: Image.Image) -> float:
    """Average chroma over the centre 50% of the image. >12 ≈ has colour."""
    arr = np.asarray(img.convert("RGB"))
    h, w = arr.shape[:2]
    centre = arr[h // 4:3 * h // 4, w // 4:3 * w // 4]
    return float(centre.max(2).astype(int).mean() - centre.min(2).astype(int).mean())


def square_crop(img: Image.Image, y_bias: float = 0.0) -> Image.Image:
    """Centre-crop to a square. y_bias shifts the crop window vertically:
    -0.5 = top of image, 0.0 = centre (default), +0.5 = bottom.
    For most portraits a slight negative bias keeps the face in frame."""
    w, h = img.size
    side = min(w, h)
    x = (w - side) // 2
    centre_y = h // 2
    biased_y = int(centre_y + y_bias * (h - side))
    y = max(0, min(h - side, biased_y - side // 2))
    return img.crop((x, y, x + side, y + side))


def process_one(job: PortraitJob, dry_run: bool = False) -> dict:
    src_path = SRC_DIR / job.source
    if not src_path.exists():
        return {"leader": job.leader, "status": "missing_source", "src": str(src_path)}

    src = Image.open(src_path).convert("RGB")
    src_chroma = chroma_score(src)

    cropped = square_crop(src, job.crop_y_pct)
    resized = cropped.resize((TARGET, TARGET), Image.LANCZOS)

    # Light unsharp mask to recover detail lost in the LANCZOS downsample.
    final = resized.filter(ImageFilter.UnsharpMask(radius=1.0, percent=80, threshold=2))
    out_chroma = chroma_score(final)

    written: list[str] = []
    if not dry_run:
        DST_DIR.mkdir(parents=True, exist_ok=True)
        for target in job.targets:
            out = DST_DIR / target
            final.save(out, "PNG", optimize=True)
            written.append(str(out.name))

    return {
        "leader": job.leader,
        "status": "ok",
        "src_chroma": round(src_chroma, 1),
        "out_chroma": round(out_chroma, 1),
        "src_size": f"{src.size[0]}x{src.size[1]}",
        "wrote": written,
        "would_write": list(job.targets) if dry_run else [],
    }


def chroma_audit() -> int:
    """Print chroma scores for every cpai_avatar_*.png currently in DST_DIR.
    >12 = has colour, ≤12 = greyscale or duotone-overlay."""
    print(f"{'file':<55s} {'size':<11s} {'chroma':>7s}  status")
    print("-" * 90)
    bad = 0
    for p in sorted(DST_DIR.glob("cpai_avatar_*.png")):
        img = Image.open(p)
        c = chroma_score(img)
        flag = "OK     " if c > 12 else "BW/DUO"
        if c <= 12:
            bad += 1
        print(f"{p.name:<55s} {img.size[0]:>4d}x{img.size[1]:<5d} {c:7.2f}  {flag}")
    print(f"\n{bad} portraits below chroma threshold (12).")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--dry-run", action="store_true",
                   help="Process and report without writing PNG output")
    p.add_argument("--check", action="store_true",
                   help="Audit chroma of all current cpai_avatar_*.png files")
    args = p.parse_args(argv)

    if args.check:
        return chroma_audit()

    print(f"{'leader':<32s} {'src→out chroma':<22s}  files")
    print("-" * 90)
    rows = []
    fail = 0
    for job in JOBS:
        r = process_one(job, dry_run=args.dry_run)
        rows.append(r)
        if r["status"] != "ok":
            fail += 1
            print(f"{r['leader']:<32s}  {r['status']:<20s}  {r.get('src','?')}")
            continue
        chroma_str = f"{r['src_chroma']:5.1f} → {r['out_chroma']:5.1f}"
        files = ", ".join(r["wrote"] or r["would_write"])
        marker = "  (dry)" if args.dry_run else ""
        print(f"{r['leader']:<32s}  {chroma_str:<22s}  {files}{marker}")

    print()
    if fail:
        print(f"FAILED {fail}/{len(JOBS)}")
        return 1
    print(f"OK {len(JOBS)}/{len(JOBS)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
