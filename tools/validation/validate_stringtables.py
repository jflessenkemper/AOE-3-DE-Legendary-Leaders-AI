from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


REPO_ROOT = Path(__file__).resolve().parents[2]
STRINGS_ROOT = REPO_ROOT / "data" / "strings"


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def child_elements(node):
    return [child for child in list(node) if isinstance(child.tag, str)]


def find_first_child(node, name: str):
    target = name.lower()
    for child in child_elements(node):
        if local_name(child.tag) == target:
            return child
    return None


def find_children(node, name: str):
    target = name.lower()
    return [child for child in child_elements(node) if local_name(child.tag) == target]


def get_attr_case_insensitive(node, key: str) -> str:
    target = key.lower()
    for attr_name, value in node.attrib.items():
        if attr_name.lower() == target:
            return value
    return ""


def find_language_node(root) -> ET.Element | None:
    string_table = find_first_child(root, "stringtable")
    if string_table is None:
        return None
    return find_first_child(string_table, "language")


def validate_stringmods(file_path: Path) -> list[str]:
    issues: list[str] = []
    expected_language = file_path.parent.name.lower()

    try:
        root = ET.parse(file_path).getroot()
    except ET.ParseError as exc:
        return [f"{file_path.relative_to(REPO_ROOT)}: XML parse error: {exc}"]

    language_node = find_language_node(root)
    if language_node is None:
        return [f"{file_path.relative_to(REPO_ROOT)}: missing StringTable/Language node"]

    actual_language = get_attr_case_insensitive(language_node, "name").lower()
    if actual_language != expected_language:
        issues.append(
            f"{file_path.relative_to(REPO_ROOT)}: folder is '{expected_language}' but language name is '{actual_language or 'missing'}'"
        )

    locids: list[str] = []
    empty_locids = 0
    empty_strings: list[str] = []
    invalid_locids: list[str] = []

    for string_node in find_children(language_node, "string"):
        locid = get_attr_case_insensitive(string_node, "_locid").strip()
        text = (string_node.text or "").strip()

        if locid == "":
            empty_locids += 1
        else:
            locids.append(locid)
            if not locid.isdigit():
                invalid_locids.append(locid)

        if text == "":
            empty_strings.append(locid or "<missing locid>")

    duplicate_locids = sorted(locid for locid, count in Counter(locids).items() if count > 1)

    if empty_locids:
        issues.append(f"{file_path.relative_to(REPO_ROOT)}: {empty_locids} strings missing _locID")
    if invalid_locids:
        issues.append(f"{file_path.relative_to(REPO_ROOT)}: invalid _locID values: {', '.join(sorted(set(invalid_locids)))}")
    if duplicate_locids:
        issues.append(f"{file_path.relative_to(REPO_ROOT)}: duplicate _locID values: {', '.join(duplicate_locids)}")
    if empty_strings:
        issues.append(f"{file_path.relative_to(REPO_ROOT)}: empty string values for locids: {', '.join(empty_strings[:20])}")

    return issues


def main() -> int:
    if not STRINGS_ROOT.exists():
        print(f"Strings folder not found: {STRINGS_ROOT.relative_to(REPO_ROOT)}")
        return 1

    stringmods_files = sorted(STRINGS_ROOT.rglob("stringmods.xml"))
    if not stringmods_files:
        print("No stringmods.xml files found under data/strings.")
        return 1

    issues: list[str] = []
    for file_path in stringmods_files:
        issues.extend(validate_stringmods(file_path))

    if issues:
        print("StringTable validation failed:")
        for issue in issues:
            print(f" - {issue}")
        return 1

    print(f"Validated {len(stringmods_files)} StringTable file(s) successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
