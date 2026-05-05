"""Annotate every <details class="nation-node"> block with a `data-search`
attribute that aggregates nation + leader + buildstyle + playstyle + every
unit name + every card name (chip title and alt). The page-level search
input filters on this attribute, so the user can type a card or unit name
and have the matching nation expand.

Idempotent: re-running replaces the existing data-search.
"""
from __future__ import annotations

import html
import re
from pathlib import Path

HTML = Path(__file__).resolve().parents[2] / "LEGENDARY_LEADERS_TREE.html"

# Each block we annotate looks like:
#   <details class="nation-node" data-name="…" [data-search="…"]>...</details>
# We rebuild data-search from the block body so it's always in sync.
NATION_OPEN = re.compile(
    r'<details class="nation-node"([^>]*)>',
)

# Skip generated `<!-- DEV-START name="X" --> ... <!-- DEV-END name="X" -->`
# regions when extracting search terms. The Development subtree contains
# asset paths, stringIDs, and a deck rendering that would otherwise (a)
# pollute `data-search` with low-signal tokens and (b) shift the trailing
# paragraph that `tools/playtest/html_reference._extract_doctrine_prose`
# treats as the doctrine narrative.
DEV_BLOCK_RX = re.compile(
    r'<!--\s*DEV-START\s+name="[^"]+"\s*-->.*?<!--\s*DEV-END\s+name="[^"]+"\s*-->',
    re.DOTALL,
)


def extract_terms(body: str) -> list[str]:
    terms: list[str] = []

    # Nation header text: "British — Duke of Wellington"
    for m in re.finditer(
        r'<span class="nation-header[^"]*"[^>]*>(.*?)</span>',
        body, re.DOTALL,
    ):
        text = re.sub(r'<[^>]+>', ' ', m.group(1))
        text = html.unescape(text).replace("&mdash;", " ").replace("—", " ")
        terms.append(re.sub(r"\s+", " ", text).strip())

    # Buildstyle + Playstyle labels
    for m in re.finditer(
        r'<span class="cat-label">(?:Buildstyle|Playstyle):\s*([^<]+?)</span>',
        body,
    ):
        terms.append(html.unescape(m.group(1)).strip())

    # Unit names: <span class="unit"...>NAME</span> (NAME is the trailing
    # text inside the span, after the <img>)
    for m in re.finditer(
        r'<span class="unit[^"]*"[^>]*>(.*?)</span>',
        body, re.DOTALL,
    ):
        # Strip any nested <img> and tags, keep the text
        text = re.sub(r'<[^>]+>', '', m.group(1))
        text = html.unescape(text).strip()
        if text:
            terms.append(text)

    # Card titles from .card-chip title="Name — Description". Keep the
    # full text so users can also search by description keywords (e.g.
    # "Wanderlust" → description mentions Voortrekker; "Royal Mint" →
    # description mentions Riding School effects; etc.).
    for m in re.finditer(
        r'<span class="card-chip[^"]*"\s+title="([^"]+)"',
        body,
    ):
        terms.append(html.unescape(m.group(1)))

    # Card alt= on the icon images (catches any chip without a title)
    for m in re.finditer(
        r'<img class="card-icon"[^>]*alt="([^"]+)"',
        body,
    ):
        terms.append(html.unescape(m.group(1)))

    # Card-chip-noicon text (text-only chips)
    for m in re.finditer(
        r'<span class="card-chip card-chip-noicon"[^>]*>([^<]+)</span>',
        body,
    ):
        terms.append(html.unescape(m.group(1)).strip())

    # Buildstyle prose paragraph text (mentions doctrine keywords)
    for m in re.finditer(
        r'<p class="bs-prose">(.*?)</p>',
        body, re.DOTALL,
    ):
        text = re.sub(r'<[^>]+>', '', m.group(1))
        text = html.unescape(text).replace("&mdash;", " ")
        terms.append(re.sub(r"\s+", " ", text).strip())

    # Dedupe while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for t in terms:
        key = t.lower()
        if key and key not in seen:
            out.append(t)
            seen.add(key)
    return out


def _build_bsprose_index(text: str) -> dict[str, str]:
    """Map data-name → bsProse string by parsing the inline
    `window.NATION_PLAYSTYLE = { "Aztecs Montezuma": { ..., "bsProse": "..." }, ... }`
    object. The doctrine narrative lives ONLY in this JS data (no per-nation
    HTML element holds it), so we hop into it to keep `data-search` in sync
    with what `tools.playtest.html_reference._extract_doctrine_prose` expects
    (the trailing `·` segment must be the doctrine narrative).
    """
    out: dict[str, str] = {}
    pattern = re.compile(
        r'"([^"]+)"\s*:\s*\{[^{}]*?"bsProse"\s*:\s*"([^"\\]*(?:\\.[^"\\]*)*)"',
        re.DOTALL,
    )
    for m in pattern.finditer(text):
        key = m.group(1)
        if " " not in key:
            continue
        prose_raw = m.group(2)
        prose = (
            prose_raw
            .replace('\\"', '"')
            .replace('\\n', ' ')
            .replace('\\t', ' ')
        )
        prose = html.unescape(prose)
        prose = re.sub(r"\s+", " ", prose).strip()
        out[key] = prose
    return out


def annotate(text: str) -> tuple[str, int]:
    bsprose_by_name = _build_bsprose_index(text)
    out_parts: list[str] = []
    cursor = 0
    annotated = 0
    while True:
        m = NATION_OPEN.search(text, cursor)
        if not m:
            out_parts.append(text[cursor:])
            break
        # Find the matching </details> for this nation-node, accounting
        # for nested <details> blocks (Buildstyle/Playstyle/Card Deck).
        depth = 1
        scan = m.end()
        while depth > 0:
            nxt_open = text.find("<details", scan)
            nxt_close = text.find("</details>", scan)
            if nxt_close == -1:
                raise RuntimeError("unbalanced <details> in nation block")
            if nxt_open != -1 and nxt_open < nxt_close:
                depth += 1
                scan = nxt_open + len("<details")
            else:
                depth -= 1
                scan = nxt_close + len("</details>")
        body_start = m.end()
        body_end = scan - len("</details>")
        body = text[body_start:body_end]

        # Strip any existing data-search
        attrs = re.sub(r'\s+data-search="[^"]*"', "", m.group(1))
        # Pull the data-name to look up doctrine prose from NATION_PLAYSTYLE.
        name_match = re.search(r'\bdata-name="([^"]+)"', attrs)
        data_name = name_match.group(1) if name_match else ""

        # Strip the generated Dev subtree before term extraction (see DEV_BLOCK_RX).
        scan_body = DEV_BLOCK_RX.sub("", body)
        terms = extract_terms(scan_body)
        # Append doctrine prose LAST so `_extract_doctrine_prose` (which treats
        # the trailing `·` segment as the doctrine narrative) keeps working —
        # the prose lives only in the JS data object, not in the nation-node body.
        prose = bsprose_by_name.get(data_name, "")
        if prose:
            terms.append(prose)
        search_blob = " · ".join(terms)
        search_attr = ' data-search="' + html.escape(search_blob, quote=True) + '"'

        new_open = '<details class="nation-node"' + attrs + search_attr + '>'

        out_parts.append(text[cursor:m.start()])
        out_parts.append(new_open)
        out_parts.append(body)
        out_parts.append("</details>")
        cursor = scan
        annotated += 1
    return "".join(out_parts), annotated


# ── search input + JS handler ──────────────────────────────────────────────

NEW_PLACEHOLDER = "Search nations, leaders, units, cards…"

# Single-line JS: walks `.nation-node`, matches every term against
# `data-search` (substring, case-insensitive), expands matches, hides
# misses. Empty section heads get the existing .is-empty class.
NEW_HANDLER = (
    "(()=>{const q=this.value.trim().toLowerCase();"
    "const tokens=q.split(/\\s+/).filter(Boolean);"
    "const nodes=document.querySelectorAll('.nation-node');"
    "nodes.forEach(n=>{"
    "const blob=(n.dataset.search||n.dataset.name||'').toLowerCase();"
    "const hit=!tokens.length||tokens.every(t=>blob.includes(t));"
    "n.classList.toggle('is-hidden',!hit);"
    "if(q&&hit)n.open=true});"
    "document.querySelectorAll('.section-head').forEach(s=>{"
    "const visible=s.querySelectorAll('.nation-node:not(.is-hidden)').length;"
    "s.classList.toggle('is-empty',q&&visible===0)})}).call(this)"
)

INPUT_RE = re.compile(
    r'(<input type="search" class="search" id="nation-search"\s+placeholder=")'
    r'[^"]*(" autocomplete="off"\s+oninput=")'
    r'[^"]*(">)',
    re.DOTALL,
)


def upgrade_input(text: str) -> str:
    return INPUT_RE.sub(
        lambda m: m.group(1) + NEW_PLACEHOLDER + m.group(2)
                 + html.escape(NEW_HANDLER, quote=True) + m.group(3),
        text,
        count=1,
    )


def main() -> int:
    text = HTML.read_text(encoding="utf-8")
    text, n = annotate(text)
    text = upgrade_input(text)
    HTML.write_text(text, encoding="utf-8")
    print(f"annotated {n} nation-node blocks with data-search")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
