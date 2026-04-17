from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
AI_ROOT = REPO_ROOT / "game" / "ai"
LOCAL_DECLARATION_RE = re.compile(r"^\s*(int|bool|float|string|vector)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:=|;)")
FUNCTION_RE = re.compile(r"^\s*(?:void|bool|int|float|string|vector)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
RULE_RE = re.compile(r"^\s*rule\s+([A-Za-z_][A-Za-z0-9_]*)\b")


@dataclass
class Block:
    kind: str
    name: str
    start_line: int
    body_start_line: int
    brace_depth: int = 0
    declarations: dict[str, int] | None = None
    recent_nonempty_lines: list[str] | None = None

    def __post_init__(self) -> None:
        if self.declarations is None:
            self.declarations = {}
        if self.recent_nonempty_lines is None:
            self.recent_nonempty_lines = []


def iter_xs_files(root: Path):
    yield from sorted(root.rglob("*.xs"))


def check_duplicate_names(file_path: Path, lines: list[str]) -> list[str]:
    issues: list[str] = []

    function_names = [match.group(1) for line in lines if (match := FUNCTION_RE.match(line))]
    rule_names = [match.group(1) for line in lines if (match := RULE_RE.match(line))]

    duplicate_functions = sorted(name for name, count in Counter(function_names).items() if count > 1)
    duplicate_rules = sorted(name for name, count in Counter(rule_names).items() if count > 1)

    rel_path = file_path.relative_to(REPO_ROOT)
    for name in duplicate_functions:
        issues.append(f"{rel_path}: duplicate function name '{name}'")
    for name in duplicate_rules:
        issues.append(f"{rel_path}: duplicate rule name '{name}'")

    return issues


def check_duplicate_locals(file_path: Path, lines: list[str]) -> list[str]:
    issues: list[str] = []
    pending: Block | None = None
    active: Block | None = None

    for index, line in enumerate(lines, start=1):
        if active is None:
            if pending is None:
                if match := FUNCTION_RE.match(line):
                    pending = Block("function", match.group(1), index, index)
                elif match := RULE_RE.match(line):
                    pending = Block("rule", match.group(1), index, index)

            if pending is not None and "{" in line:
                active = pending
                active.body_start_line = index
                active.brace_depth = line.count("{") - line.count("}")
                pending = None
                continue

        else:
            stripped = line.strip()
            if match := LOCAL_DECLARATION_RE.match(line):
                name = match.group(2)
                in_rule_loop_body = (
                    active.kind == "rule"
                    and any("for (" in previous for previous in active.recent_nonempty_lines)
                    and any(previous == "{" for previous in active.recent_nonempty_lines[-2:])
                )
                if in_rule_loop_body and name in active.declarations:
                    rel_path = file_path.relative_to(REPO_ROOT)
                    first_line = active.declarations[name]
                    issues.append(
                        f"{rel_path}:{index}: duplicate local '{name}' in {active.kind} '{active.name}' (first declared on line {first_line})"
                    )
                elif in_rule_loop_body:
                    active.declarations[name] = index

            active.brace_depth += line.count("{")
            active.brace_depth -= line.count("}")
            if stripped:
                active.recent_nonempty_lines.append(stripped)
                if len(active.recent_nonempty_lines) > 4:
                    active.recent_nonempty_lines.pop(0)
            if active.brace_depth <= 0:
                active = None

    return issues


def main() -> int:
    if not AI_ROOT.exists():
        print(f"AI folder not found: {AI_ROOT.relative_to(REPO_ROOT)}")
        return 1

    issues: list[str] = []
    for file_path in iter_xs_files(AI_ROOT):
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        issues.extend(check_duplicate_names(file_path, lines))
        issues.extend(check_duplicate_locals(file_path, lines))

    if issues:
        print("XS validation failed:")
        for issue in issues:
            print(f" - {issue}")
        return 1

    print("XS validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
