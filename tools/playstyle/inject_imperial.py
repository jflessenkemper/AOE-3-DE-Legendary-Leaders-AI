"""Inject imperial-doctrine peer playstyle data into a_new_world.html.

Reads ``IMPERIAL_PLAYSTYLE_DATA`` from ``tools.playstyle.imperial_data``
and merges each entry's keys into the matching ``window.NATION_PLAYSTYLE``
record in the HTML, then rewrites the file in place.

Idempotent: re-running on an already-injected HTML produces no diff
(json.loads → dict.update → json.dumps round-trips deterministically).

Usage:
    python3 -m tools.playstyle.inject_imperial          # rewrite in place
    python3 -m tools.playstyle.inject_imperial --check  # exit 1 if drift
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HTML_REL = Path("a_new_world.html")

PLAYSTYLE_OBJECT_RE = re.compile(
    r"(window\.NATION_PLAYSTYLE\s*=\s*)(\{.*?\})(;)",
    re.DOTALL,
)


def _load_data() -> dict[str, dict]:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from tools.playstyle.imperial_data import IMPERIAL_PLAYSTYLE_DATA  # type: ignore

    return IMPERIAL_PLAYSTYLE_DATA


def _format_block(data: dict) -> str:
    # Pretty-print to roughly match the existing HTML indent style: 2-space
    # indent, sorted by key not enforced (we want stable output).
    return json.dumps(data, indent=2, ensure_ascii=False)


def inject(repo_root: Path = REPO_ROOT, *, check: bool = False) -> tuple[bool, list[str]]:
    """Return (changed, issues). When ``check`` is True the file is not
    rewritten; ``changed`` reports whether a rewrite would occur."""
    html_path = repo_root / HTML_REL
    text = html_path.read_text(encoding="utf-8")

    match = PLAYSTYLE_OBJECT_RE.search(text)
    if match is None:
        return (False, ["NATION_PLAYSTYLE block not found in HTML"])

    try:
        data = json.loads(match.group(2))
    except json.JSONDecodeError as exc:
        return (False, [f"NATION_PLAYSTYLE not JSON-parseable: {exc}"])

    imperial = _load_data()
    issues: list[str] = []

    missing = sorted(set(data.keys()) - set(imperial.keys()))
    orphan = sorted(set(imperial.keys()) - set(data.keys()))
    for key in missing:
        issues.append(f"imperial data missing entry for civ '{key}'")
    for key in orphan:
        issues.append(f"imperial data has orphan entry for civ '{key}' (not in NATION_PLAYSTYLE)")

    merged: dict[str, dict] = {}
    for key, value in data.items():
        new_value = dict(value)
        if key in imperial:
            new_value.update(imperial[key])
        merged[key] = new_value

    new_block = _format_block(merged)
    new_text = text[: match.start()] + match.group(1) + new_block + match.group(3) + text[match.end():]

    changed = new_text != text
    if changed and not check:
        html_path.write_text(new_text, encoding="utf-8")
    return (changed, issues)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="Do not rewrite the HTML; exit 1 if injection would change the file.",
    )
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    args = parser.parse_args()

    try:
        changed, issues = inject(args.repo_root.resolve(), check=args.check)
    except ImportError:
        print("ERROR: tools.playstyle.imperial_data not found — run after data file is authored.")
        return 1

    for issue in issues:
        print(f" - {issue}")

    if issues:
        return 1

    if args.check:
        if changed:
            print("HTML drift: imperial fields would be injected. Run without --check to apply.")
            return 1
        print("HTML imperial fields up to date.")
        return 0

    print("HTML imperial fields injected." if changed else "HTML already up to date.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
