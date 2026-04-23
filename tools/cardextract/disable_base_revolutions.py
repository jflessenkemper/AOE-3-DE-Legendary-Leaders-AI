"""Disable all base-game revolution techs so standard civs can't revolt.

Since our mod exposes the 26 revolution civs as top-level pickable civilizations,
we don't want standard civs to ALSO be able to revolt at age-up — that creates
duplicate/confusing gameplay paths.

Strategy: for each base DERevolution* tech that turns a civ into a revolutionary
state, append an override to `data/techtreemods.xml` that sets its Status to
UNOBTAINABLE. Marker comment delimits the block for idempotent re-runs.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xmb import parse_xmb

REPO = Path(__file__).resolve().parents[2]
TT_MODS = REPO / "data" / "techtreemods.xml"
BASE_TT = Path("/tmp/tt/techtreey.xml.XMB")

START = "<!-- DISABLE-BASE-REVOLUTIONS-START -->"
END = "<!-- DISABLE-BASE-REVOLUTIONS-END -->"


def find_revolution_techs() -> list[str]:
    if not BASE_TT.exists():
        raise RuntimeError(f"Run `python3 tools/bar_extract.py .../Data.bar --out /tmp/tt --filter techtreey` first")
    with BASE_TT.open("rb") as f:
        root = parse_xmb(f.read())
    # Player-facing revolution choices — these are the ones that convert a civ
    # into a revolutionary state. We exclude shared effects / helpers.
    # Keep: DERevolution<CivName>, DERevolutionUSA, etc.
    # Exclude: DERevolutionSharedEffects, DERevolutionaryNerf*, DERevolutionAge*
    SKIP = {
        "DERevolutionSharedEffects",
        "DERevolutionAge1",
        "DERevolutionAge2",
    }
    SKIP_PREFIX = ("DERevolutionary",)
    SKIP_SUFFIX = ("Shadow",)

    out = []
    for t in root.iter("tech"):
        n = t.get("name", "")
        if not (n.startswith("DERevolution") or n.startswith("Revolution")):
            continue
        if n in SKIP:
            continue
        if any(n.startswith(p) for p in SKIP_PREFIX):
            continue
        if any(n.endswith(s) for s in SKIP_SUFFIX):
            continue
        out.append(n)
    return sorted(out)


def main():
    techs = find_revolution_techs()
    print(f"Found {len(techs)} base-game revolution techs to disable")
    for t in techs:
        print(f"  {t}")

    content = TT_MODS.read_text(encoding="utf-8")
    # Strip any previous block
    content = re.sub(
        re.escape(START) + r".*?" + re.escape(END) + r"\r?\n?",
        "",
        content,
        flags=re.DOTALL,
    )

    # Build new block: each tech gets a Status=UNOBTAINABLE override
    lines = [START]
    for tech in techs:
        lines.append(f"\t<Tech name='{tech}' type='Normal'>")
        lines.append(f"\t\t<Status>UNOBTAINABLE</Status>")
        lines.append(f"\t</Tech>")
    lines.append(END)
    injection = "\n".join(lines) + "\n"

    # Insert before </techtreemods>
    content = content.replace("</techtreemods>", injection + "</techtreemods>", 1)
    TT_MODS.write_text(content, encoding="utf-8")
    print(f"\nWrote {len(techs)} UNOBTAINABLE overrides to {TT_MODS.relative_to(REPO)}")


if __name__ == "__main__":
    main()
