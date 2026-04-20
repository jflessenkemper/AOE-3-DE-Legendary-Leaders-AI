from __future__ import annotations

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET


REPO_ROOT = Path(__file__).resolve().parents[2]


def build_repo_root_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=REPO_ROOT,
        help="Repository root to validate. Defaults to the current workspace root.",
    )
    return parser


def repo_relative(path: Path, repo_root: Path = REPO_ROOT) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def child_elements(node: ET.Element) -> list[ET.Element]:
    return [child for child in list(node) if isinstance(child.tag, str)]


def find_first_child(node: ET.Element, name: str) -> ET.Element | None:
    target = name.lower()
    for child in child_elements(node):
        if local_name(child.tag) == target:
            return child
    return None


def find_children(node: ET.Element, name: str) -> list[ET.Element]:
    target = name.lower()
    return [child for child in child_elements(node) if local_name(child.tag) == target]


def get_child_text(node: ET.Element, name: str) -> str:
    child = find_first_child(node, name)
    if child is None or child.text is None:
        return ""
    return child.text.strip()


def get_attr_case_insensitive(node: ET.Element, key: str) -> str:
    target = key.lower()
    for attr_name, value in node.attrib.items():
        if attr_name.lower() == target:
            return value.strip()
    return ""


def normalize_path(value: str) -> str:
    return value.replace("\\", "/").strip()


def iter_repo_resource_paths(element: ET.Element):
    for child in element.iter():
        if not isinstance(child.tag, str):
            continue
        if not child.tag.endswith("WPF"):
            continue
        if child.text is None:
            continue
        value = normalize_path(child.text)
        if not value:
            continue
        if value.startswith("resources/"):
            yield child.tag, value
