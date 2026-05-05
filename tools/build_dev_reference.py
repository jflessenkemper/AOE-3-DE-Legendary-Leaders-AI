#!/usr/bin/env python3
"""Generate DEVELOPMENT_REFERENCE.html — per-civ asset coverage map.

For every civ in the mod (22 base + 26 revolution = 48), produce a single
table listing every place the civ's identity surfaces in-game:

    • Lobby AI portrait (SmallPortraitTextureWPF + cpai_avatar_*.ddt)
    • Lobby personality (icon + nameID/tooltipID strings)
    • Loading screen flag (HomeCityFlagIconWPF, PostgameFlagIconWPF)
    • In-game flag (Portrait, HomeCityFlagTexture, BannerTexture)
    • Scoreboard name (DisplayName / RolloverName from stringmods.xml)
    • Diplomacy portrait (PortraitTexture + ESO civ_flags_quick_launch)
    • Home city flag button (HomeCityFlagButtonWPF)
    • Personality-side identity (forcedciv, chatset)

Each row shows the resolved value, the file (or string) it points at, an
inline thumbnail when the target is a PNG that exists, and a status
marker (OK / MISSING / FALLBACK).

Open the resulting file in any browser:

    python3 tools/build_dev_reference.py
    xdg-open DEVELOPMENT_REFERENCE.html

Read-only — never modifies mod files. Safe to run during a matrix run.
"""
from __future__ import annotations
import argparse
import html
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CIVMODS = REPO / "data" / "civmods.xml"
STRINGS = REPO / "data" / "strings" / "english" / "stringmods.xml"
AI_DIR = REPO / "game" / "ai"
DDT_DIR = REPO / "art" / "ui" / "singleplayer"
PNG_DIR = REPO / "resources" / "images" / "icons" / "singleplayer"
FLAG_DIR = REPO / "resources" / "images" / "icons" / "flags"


# -----------------------------------------------------------------------------
# Parsing
# -----------------------------------------------------------------------------

def _load_strings() -> dict[str, str]:
    """Map stringmods _locID → text. Last write wins (engine semantics)."""
    if not STRINGS.exists():
        return {}
    txt = STRINGS.read_text(encoding="utf-8", errors="ignore")
    out: dict[str, str] = {}
    for m in re.finditer(
            r"<[Ss]tring\s+_loc[Ii][Dd]=['\"](\d+)['\"][^>]*>([^<]*)</[Ss]tring>", txt):
        out[m.group(1)] = m.group(2).strip()
    return out


def _split_civs(xml_text: str) -> list[str]:
    """Yield each <Civ>...</Civ> block as a string."""
    return re.findall(r"<Civ>.*?</Civ>", xml_text, flags=re.DOTALL)


def _tag(block: str, name: str) -> str | None:
    m = re.search(rf"<{name}>([^<]+)</{name}>", block)
    return m.group(1).strip() if m else None


def _all_tags(block: str, name: str) -> list[str]:
    return [m.group(1).strip()
            for m in re.finditer(rf"<{name}>([^<]+)</{name}>", block)]


def _load_personalities() -> dict[str, dict]:
    """Map lower(forcedciv) → personality fields. Multi-leader civs collapse
    to the first encountered personality (matches lobby pick-list order)."""
    out: dict[str, dict] = {}
    for p in sorted(AI_DIR.glob("*.personality")):
        txt = p.read_text(encoding="utf-8", errors="ignore")
        info = {
            "file": p.name,
            "icon": _tag(txt, "icon"),
            "forcedciv": _tag(txt, "forcedciv"),
            "chatset": _tag(txt, "chatset"),
            "nameID": _tag(txt, "nameID"),
            "tooltipID": _tag(txt, "tooltipID"),
        }
        fc = (info["forcedciv"] or "").lower()
        if fc:
            out.setdefault(fc, info)
    return out


def _synth_civ_block_for_basegame(forcedciv: str, pers: dict) -> str:
    """Emit a minimal <Civ>-shaped block for base-game civs that aren't in
    civmods.xml. Personality + naming come through, civmods-only fields
    (flag textures, banner) just show as 'no-ref'."""
    nid = pers.get("nameID") or ""
    tid = pers.get("tooltipID") or ""
    return (
        f"<Civ><Name>{html.escape(forcedciv)}</Name>"
        f"<DisplayNameID>{nid}</DisplayNameID>"
        f"<RolloverNameID>{tid}</RolloverNameID>"
        f"</Civ>"
    )


# -----------------------------------------------------------------------------
# Resolution
# -----------------------------------------------------------------------------

def _resolve(value: str | None) -> tuple[Path | None, str]:
    """Resolve an in-XML reference like 'objects\\flags\\french' or
    'resources/images/icons/singleplayer/cpai_avatar_french.png' into a
    real (Path, status) pair.

    Status: 'ok' | 'missing' | 'engine-only' | 'no-ref'
    """
    if not value:
        return None, "no-ref"

    # Normalise backslashes (Windows-style paths in XML).
    norm = value.replace("\\", "/")

    # Direct path with extension — check it.
    if Path(norm).suffix:
        p = REPO / norm
        return (p, "ok") if p.exists() else (p, "missing")

    # Engine path without extension (e.g. "objects/flags/french") —
    # the .ddt lives under art/. We can probe a couple of candidate
    # locations but most aren't shipped by us; treat as engine-only.
    candidates = [
        REPO / "art" / (norm + ".ddt"),
        DDT_DIR / (Path(norm).name + ".ddt"),
    ]
    for c in candidates:
        if c.exists():
            return c, "ok"
    return None, "engine-only"


def _ddt_for_png(png_path: Path | None) -> tuple[Path | None, bool]:
    """Map a PNG portrait to its .ddt counterpart, return (path, exists)."""
    if png_path is None:
        return None, False
    # Convention: art/ui/singleplayer/<basename>.ddt for SmallPortrait avatars
    if "singleplayer" in png_path.parts:
        ddt = DDT_DIR / (png_path.stem + ".ddt")
        return ddt, ddt.exists()
    return None, False


# -----------------------------------------------------------------------------
# HTML emission
# -----------------------------------------------------------------------------

CSS = """
:root { --ok:#1a7f37; --warn:#9a6700; --fail:#cf222e; --muted:#656d76;
        --bg:#0d1117; --fg:#e6edf3; --row:#151b23; --border:#30363d; }
* { box-sizing: border-box; }
body { background: var(--bg); color: var(--fg); font: 13px/1.5
       -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
       margin: 0; padding: 24px; }
h1 { margin: 0 0 8px; font-size: 22px; }
.lede { color: var(--muted); margin-bottom: 24px; }
.toc { columns: 3 200px; column-gap: 24px; margin: 0 0 24px; padding: 12px;
       background: var(--row); border: 1px solid var(--border); border-radius: 6px; }
.toc a { color: #58a6ff; text-decoration: none; display: block; padding: 2px 0; }
.toc a:hover { text-decoration: underline; }
.civ { background: var(--row); border: 1px solid var(--border); border-radius: 6px;
       padding: 16px; margin-bottom: 18px; }
.civ h2 { margin: 0 0 4px; font-size: 17px; }
.civ .meta { color: var(--muted); font-size: 12px; margin-bottom: 12px; }
table { width: 100%; border-collapse: collapse; }
th, td { text-align: left; vertical-align: top; padding: 6px 8px;
         border-bottom: 1px solid var(--border); font-size: 12px; }
th { color: var(--muted); font-weight: 600; }
td.what { width: 200px; color: var(--muted); }
td.value { font-family: ui-monospace, "JetBrains Mono", Consolas, monospace;
           color: #e6edf3; word-break: break-all; }
td.thumb { width: 80px; }
td.thumb img { max-width: 64px; max-height: 64px; border-radius: 4px;
               border: 1px solid var(--border); display: block; background: #fff; }
.tag { display: inline-block; padding: 2px 8px; border-radius: 10px;
       font-size: 11px; font-weight: 600; }
.tag.ok      { background: rgba(46,160,67,0.15);  color: #3fb950; }
.tag.missing { background: rgba(248,81,73,0.15);  color: #f85149; }
.tag.fallback{ background: rgba(187,128,9,0.15);  color: #d29922; }
.tag.engine  { background: rgba(101,109,118,0.15);color: var(--muted); }
.tag.no-ref  { background: rgba(101,109,118,0.10);color: var(--muted); }
.summary { display: flex; gap: 14px; margin-bottom: 12px; }
.summary .pill { background: var(--bg); padding: 4px 10px; border-radius: 4px;
                 border: 1px solid var(--border); font-size: 12px; }
.summary .pill b { color: #fff; }
"""


def _status_tag(status: str) -> str:
    return f'<span class="tag {status}">{status.upper()}</span>'


def _row(what: str, value: str | None, status: str,
         thumb_path: Path | None = None) -> str:
    val_html = html.escape(value or "—")
    thumb_html = ""
    if thumb_path is not None and thumb_path.exists() and thumb_path.suffix.lower() in (".png", ".jpg", ".jpeg"):
        # Embed via file:// path so the browser can render it from the repo.
        rel = thumb_path.relative_to(REPO)
        thumb_html = f'<img src="{html.escape(str(rel))}" alt="">'
    return (f'<tr><td class="what">{html.escape(what)}</td>'
            f'<td class="value">{val_html}</td>'
            f'<td class="thumb">{thumb_html}</td>'
            f'<td>{_status_tag(status)}</td></tr>')


def _build_civ_block(civ_block: str, strings: dict, personalities: dict) -> str:
    name = _tag(civ_block, "Name") or "(unknown)"
    display_id = _tag(civ_block, "DisplayNameID")
    rollover_id = _tag(civ_block, "RolloverNameID")
    display_str = strings.get(display_id or "", "") if display_id else ""
    rollover_str = strings.get(rollover_id or "", "") if rollover_id else ""

    # Match this civ's personality by lower-cased Name match (engine semantics)
    pers = personalities.get(name.lower())
    pers_icon_path: Path | None = None
    if pers and pers.get("icon"):
        pers_icon_path = REPO / pers["icon"].replace("\\", "/")

    rows: list[str] = []
    n_ok = n_missing = n_fallback = 0

    def add(what: str, val: str | None, fixed_status: str | None = None,
            kind: str = "path"):
        nonlocal n_ok, n_missing, n_fallback
        thumb = None
        status = fixed_status

        if status is None:
            if val is None:
                status = "no-ref"
            elif kind == "path":
                p, st = _resolve(val)
                status = st
                thumb = p if (p and p.suffix.lower() in (".png", ".jpg", ".jpeg")) else None
            elif kind == "string":
                status = "ok" if val else "missing"
            else:
                status = "ok"

        if status == "ok":      n_ok += 1
        elif status == "missing": n_missing += 1
        elif status == "fallback": n_fallback += 1

        rows.append(_row(what, val, status, thumb))

    # ----- Identity strings (scoreboard / lobby names) -----
    add("Display name (lobby + scoreboard)",
        f"{display_id} → {display_str!r}" if display_id else None,
        fixed_status=("ok" if display_str else ("missing" if display_id else "no-ref")))
    add("Rollover name (tooltip)",
        f"{rollover_id} → {rollover_str!r}" if rollover_id else None,
        fixed_status=("ok" if rollover_str else ("missing" if rollover_id else "no-ref")))

    # ----- Lobby AI portrait (the bit the user is debugging) -----
    sp_wpf = _tag(civ_block, "SmallPortraitTextureWPF")
    add("Lobby AI portrait — WPF (UI overlay)", sp_wpf, kind="path")
    sp_tex = _tag(civ_block, "SmallPortraitTexture")
    add("Lobby AI portrait — engine .ddt (rendered)", sp_tex, kind="path")
    if sp_wpf:
        ddt, ok = _ddt_for_png(REPO / sp_wpf.replace("\\", "/"))
        add(
            "Lobby AI portrait — DDT parity check",
            (str(ddt.relative_to(REPO)) if ddt else None),
            fixed_status=("ok" if ok else "fallback"),
        )

    # ----- Personality-side -----
    if pers:
        add(f"Personality: {pers['file']} — icon", pers["icon"], kind="path")
        add(f"Personality: {pers['file']} — forcedciv",
            pers["forcedciv"], fixed_status="ok" if pers["forcedciv"] else "no-ref",
            kind="other")
        add(f"Personality: {pers['file']} — chatset",
            pers["chatset"], fixed_status="ok" if pers["chatset"] else "no-ref",
            kind="other")
        nm = pers["nameID"]; tt = pers["tooltipID"]
        nm_str = strings.get(nm or "", "") if nm else ""
        tt_str = strings.get(tt or "", "") if tt else ""
        add("Personality: scoreboard nameID",
            f"{nm} → {nm_str!r}" if nm else None,
            fixed_status=("ok" if nm_str else ("missing" if nm else "no-ref")))
        add("Personality: tooltipID",
            f"{tt} → {tt_str!r}" if tt else None,
            fixed_status=("ok" if tt_str else ("missing" if tt else "no-ref")))
    else:
        add("Personality file", None, fixed_status="missing")

    # ----- Flags everywhere -----
    add("Civ portrait (engine .ddt root)",
        _tag(civ_block, "Portrait"), kind="path")
    add("Home city flag — texture (in-game)",
        _tag(civ_block, "HomeCityFlagTexture"), kind="path")
    add("Home city flag — WPF icon (lobby/loading)",
        _tag(civ_block, "HomeCityFlagIconWPF"), kind="path")
    add("Home city flag — button WPF",
        _tag(civ_block, "HomeCityFlagButtonWPF"), kind="path")
    add("Postgame flag — texture",
        _tag(civ_block, "PostgameFlagTexture"), kind="path")
    add("Postgame flag — WPF icon",
        _tag(civ_block, "PostgameFlagIconWPF"), kind="path")

    # ----- Diplomacy / portrait sheet -----
    add("Diplomacy portrait — sheet texture",
        _tag(civ_block, "PortraitTexture"), kind="path")
    add("Banner — sheet texture (lobby browser)",
        _tag(civ_block, "BannerTexture"), kind="path")

    summary = (
        '<div class="summary">'
        f'<span class="pill"><b>{n_ok}</b> OK</span>'
        f'<span class="pill"><b>{n_missing}</b> MISSING</span>'
        f'<span class="pill"><b>{n_fallback}</b> FALLBACK (no DDT)</span>'
        '</div>'
    )

    title = display_str or name
    civ_id = name.lower().replace(" ", "-")
    return (
        f'<section class="civ" id="{civ_id}">'
        f'<h2>{html.escape(title)}</h2>'
        f'<div class="meta">civ name: <code>{html.escape(name)}</code> · '
        f'personality: <code>{html.escape(pers["file"]) if pers else "—"}</code></div>'
        f'{summary}'
        f'<table>'
        f'<thead><tr><th>What</th><th>Value</th><th>Thumb</th><th>Status</th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody>'
        f'</table>'
        f'</section>'
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", default="DEVELOPMENT_REFERENCE.html",
                    help="Output HTML file (default: repo-root)")
    args = ap.parse_args(argv)

    if not CIVMODS.exists():
        print(f"FATAL: {CIVMODS} not found", file=sys.stderr)
        return 2

    strings = _load_strings()
    personalities = _load_personalities()
    civ_blocks = _split_civs(CIVMODS.read_text(encoding="utf-8", errors="ignore"))
    civmods_names = {(_tag(b, "Name") or "").lower() for b in civ_blocks}

    # Synthesize entries for base-game civs that aren't in civmods.xml but DO
    # have a personality file we ship (Napoleon, Wellington, Catherine, etc.).
    for fc, pers in personalities.items():
        if fc and fc not in civmods_names:
            civ_blocks.append(_synth_civ_block_for_basegame(fc, pers))

    print(f"Civs covered: {len(civ_blocks)} "
          f"({len(civmods_names)} from civmods.xml + "
          f"{len(civ_blocks) - len(civmods_names)} base-game synthesised)")
    print(f"Loaded {len(strings)} string entries")
    print(f"Loaded {len(personalities)} personality files")

    sections = [_build_civ_block(b, strings, personalities) for b in civ_blocks]

    # TOC
    toc_items: list[str] = []
    for b in civ_blocks:
        nm = _tag(b, "Name") or "?"
        did = _tag(b, "DisplayNameID")
        label = strings.get(did or "", "") or nm
        cid = nm.lower().replace(" ", "-")
        toc_items.append(f'<a href="#{cid}">{html.escape(label)}</a>')

    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = REPO / out_path

    html_doc = (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        '<title>AOE 3 DE - A New World — Development Reference</title>'
        f'<style>{CSS}</style></head><body>'
        '<h1>AOE 3 DE - A New World — Development Reference</h1>'
        '<p class="lede">Per-civ asset coverage map. For each civilisation, '
        'every place its identity surfaces in the game (lobby, scoreboard, '
        'loading screen, in-game HUD, diplomacy, postgame). Spot-check rows '
        'flagged FALLBACK (engine substitutes a generic civ portrait because '
        'the leader-specific .ddt is missing) or MISSING (referenced file or '
        'string not found in the repo).</p>'
        f'<nav class="toc">{"".join(toc_items)}</nav>'
        f'{"".join(sections)}'
        '</body></html>'
    )
    out_path.write_text(html_doc, encoding="utf-8")
    print(f"Wrote {out_path.relative_to(REPO)}  ({out_path.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
