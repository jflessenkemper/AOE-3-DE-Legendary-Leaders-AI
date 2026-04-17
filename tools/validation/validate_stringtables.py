from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.validation.common import REPO_ROOT, build_repo_root_parser, find_children, find_first_child, get_attr_case_insensitive, repo_relative

STRINGS_ROOT = REPO_ROOT / "data" / "strings"


def stringmods_repo_root(file_path: Path) -> Path:
    if file_path.name == "stringmods.xml" and len(file_path.parents) >= 4:
        return file_path.parents[3]
    return REPO_ROOT


def find_language_node(root) -> ET.Element | None:
    string_table = find_first_child(root, "stringtable")
    if string_table is None:
        return None
    return find_first_child(string_table, "language")


def validate_stringmods(file_path: Path) -> list[str]:
    issues: list[str] = []
    expected_language = file_path.parent.name.lower()
    report_root = stringmods_repo_root(file_path)

    try:
        root = ET.parse(file_path).getroot()
    except ET.ParseError as exc:
        return [f"{repo_relative(file_path, report_root)}: XML parse error: {exc}"]

    language_node = find_language_node(root)
    if language_node is None:
        return [f"{repo_relative(file_path, report_root)}: missing StringTable/Language node"]

    actual_language = get_attr_case_insensitive(language_node, "name").lower()
    if actual_language != expected_language:
        issues.append(
            f"{repo_relative(file_path, report_root)}: folder is '{expected_language}' but language name is '{actual_language or 'missing'}'"
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
        issues.append(f"{repo_relative(file_path, report_root)}: {empty_locids} strings missing _locID")
    if invalid_locids:
        issues.append(f"{repo_relative(file_path, report_root)}: invalid _locID values: {', '.join(sorted(set(invalid_locids)))}")
    if duplicate_locids:
        issues.append(f"{repo_relative(file_path, report_root)}: duplicate _locID values: {', '.join(duplicate_locids)}")
    if empty_strings:
        issues.append(f"{repo_relative(file_path, report_root)}: empty string values for locids: {', '.join(empty_strings[:20])}")

    return issues


def validate_stringtables(repo_root: Path = REPO_ROOT) -> list[str]:
    strings_root = repo_root / "data" / "strings"
    if not strings_root.exists():
        return [f"Strings folder not found: {repo_relative(strings_root, repo_root)}"]

    stringmods_files = sorted(strings_root.rglob("stringmods.xml"))
    if not stringmods_files:
        return ["No stringmods.xml files found under data/strings."]

    issues: list[str] = []
    for file_path in stringmods_files:
        issues.extend(validate_stringmods(file_path))
    return issues


def main() -> int:
    parser = build_repo_root_parser("Validate StringTable files.")
    args = parser.parse_args()
    repo_root = args.repo_root.resolve()
    issues = validate_stringtables(repo_root)
    stringmods_files = sorted((repo_root / "data" / "strings").rglob("stringmods.xml")) if (repo_root / "data" / "strings").exists() else []

    if issues:
        print("StringTable validation failed:")
        for issue in issues:
            print(f" - {issue}")
        return 1

    print(f"Validated {len(stringmods_files)} StringTable file(s) successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
