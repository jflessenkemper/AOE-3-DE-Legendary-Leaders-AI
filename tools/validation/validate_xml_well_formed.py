from __future__ import annotations

from pathlib import Path
import sys
import xml.etree.ElementTree as ET


REPO_ROOT = Path(__file__).resolve().parents[2]
XML_SUFFIXES = {".xml", ".tactics", ".material", ".dmg"}
IGNORED_DIRS = {".git", ".venv", "node_modules"}


def iter_candidate_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in XML_SUFFIXES:
            continue
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        yield path


def main() -> int:
    malformed = []
    for file_path in iter_candidate_files(REPO_ROOT):
        try:
            ET.parse(file_path)
        except ET.ParseError as exc:
            malformed.append(f"{file_path.relative_to(REPO_ROOT)}: {exc}")

    if malformed:
        print(f"Found {len(malformed)} malformed XML-like files:")
        for entry in malformed:
            print(f" - {entry}")
        return 1

    print("All XML-like files are well-formed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
