from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


REPO_ROOT = Path(__file__).resolve().parents[2]
TECHTREE_FILE = REPO_ROOT / "data" / "techtreemods.xml"


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def child_elements(node):
    return [child for child in list(node) if isinstance(child.tag, str)]


def find_first_child_text(node, name: str) -> str:
    target = name.lower()
    for child in child_elements(node):
        if local_name(child.tag) == target:
            return (child.text or "").strip()
    return ""


def get_attr_case_insensitive(node, key: str) -> str:
    target = key.lower()
    for attr_name, value in node.attrib.items():
        if attr_name.lower() == target:
            return value.strip()
    return ""


def main() -> int:
    try:
        root = ET.parse(TECHTREE_FILE).getroot()
    except ET.ParseError as exc:
        print(f"Failed to parse {TECHTREE_FILE.relative_to(REPO_ROOT)}: {exc}")
        return 1

    tech_names: list[str] = []
    dbids: list[str] = []

    for tech in child_elements(root):
        if local_name(tech.tag) != "tech":
            continue

        tech_name = get_attr_case_insensitive(tech, "name")
        dbid = find_first_child_text(tech, "dbid")

        if tech_name:
            tech_names.append(tech_name.lower())
        if dbid:
            dbids.append(dbid)

    issues: list[str] = []

    duplicate_names = sorted(name for name, count in Counter(tech_names).items() if count > 1)
    duplicate_dbids = sorted(dbid for dbid, count in Counter(dbids).items() if count > 1)

    if duplicate_names:
        issues.append(f"Duplicate tech names: {', '.join(duplicate_names)}")
    if duplicate_dbids:
        issues.append(f"Duplicate tech DBIDs: {', '.join(duplicate_dbids)}")

    if issues:
        print("TechTree validation failed:")
        for issue in issues:
            print(f" - {issue}")
        return 1

    print("TechTree validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
