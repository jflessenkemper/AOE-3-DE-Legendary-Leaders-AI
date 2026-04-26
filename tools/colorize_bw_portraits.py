#!/usr/bin/env python3
"""
Colorize black-and-white leader portraits with a warm duotone so they
read as hand-tinted historical prints rather than harsh greyscale.

Detects b&w portraits by sampling chroma and skips already-colored ones.
Run from repo root: python3 tools/colorize_bw_portraits.py
"""
from PIL import Image, ImageOps
import glob, os, sys

SRC_DIR = 'resources/images/icons/singleplayer'
PATTERN = 'cpai_avatar_*.png'
CHROMA_THRESHOLD = 12  # mean chroma below this = b&w
DUOTONE_DARK  = (42, 24, 16)    # warm brown shadow
DUOTONE_MID   = (160, 102, 78)  # tan midtone
DUOTONE_LIGHT = (245, 212, 176) # peach highlight


def mean_chroma(im_rgb):
    w, h = im_rgb.size
    crop = im_rgb.crop((w // 4, h // 4, 3 * w // 4, 3 * h // 4))
    px = list(crop.getdata())
    return sum(max(r, g, b) - min(r, g, b) for r, g, b in px) / len(px)


def colorize(src_path):
    im = Image.open(src_path).convert('RGBA')
    alpha = im.split()[-1]
    gray = ImageOps.autocontrast(im.convert('L'), cutoff=1)
    out = ImageOps.colorize(
        gray, black=DUOTONE_DARK, white=DUOTONE_LIGHT, mid=DUOTONE_MID,
    )
    out.putalpha(alpha)
    return out


def main():
    files = sorted(glob.glob(os.path.join(SRC_DIR, PATTERN)))
    if not files:
        print('no portraits found at', SRC_DIR)
        sys.exit(1)
    converted = 0
    for p in files:
        try:
            chroma = mean_chroma(Image.open(p).convert('RGB'))
        except Exception as e:
            print(' SKIP', os.path.basename(p), e)
            continue
        if chroma >= CHROMA_THRESHOLD:
            continue
        out = colorize(p)
        out.save(p)
        print(f' colorized chroma={chroma:5.1f}  {os.path.basename(p)}')
        converted += 1
    print(f'\n{converted} portraits colorized')


if __name__ == '__main__':
    main()
