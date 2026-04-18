from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import re
import sys

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.validation.common import REPO_ROOT, build_repo_root_parser, repo_relative

LOCAL_DECLARATION_RE = re.compile(r"^\s*(int|bool|float|string|vector)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:=|;)")
FUNCTION_RE = re.compile(r"^\s*(?:void|bool|int|float|string|vector)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
RULE_RE = re.compile(r"^\s*rule\s+([A-Za-z_][A-Za-z0-9_]*)\b")
FUNCTION_CALL_RE = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
STOCK_XS_CALLS = {
    "xsArrayCreateBool",
    "xsArrayCreateFloat",
    "xsArrayCreateInt",
    "xsArrayCreateString",
    "xsArrayCreateVector",
    "xsArrayGetBool",
    "xsArrayGetFloat",
    "xsArrayGetInt",
    "xsArrayGetSize",
    "xsArrayGetString",
    "xsArrayGetVector",
    "xsArrayResizeInt",
    "xsArrayResizeVector",
    "xsArraySetBool",
    "xsArraySetFloat",
    "xsArraySetInt",
    "xsArraySetString",
    "xsArraySetVector",
    "xsDisableRule",
    "xsDisableSelf",
    "xsEnableRule",
    "xsEnableRuleGroup",
    "xsGetTime",
    "xsIsRuleEnabled",
    "xsSetContextPlayer",
    "xsSetRuleMaxIntervalSelf",
    "xsSetRuleMinInterval",
    "xsSetRuleMinIntervalSelf",
    "xsVectorGetX",
    "xsVectorGetZ",
    "xsVectorLength",
    "xsVectorNormalize",
    "xsVectorSet",
    "xsVectorSetX",
    "xsVectorSetZ",
}
UNSUPPORTED_BUILTINS = {
    "xsCeil",
    "xsFloor",
    "xsRound",
}


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


def check_duplicate_names(file_path: Path, lines: list[str], repo_root: Path) -> list[str]:
    issues: list[str] = []

    function_names = [match.group(1) for line in lines if (match := FUNCTION_RE.match(line))]
    rule_names = [match.group(1) for line in lines if (match := RULE_RE.match(line))]

    duplicate_functions = sorted(name for name, count in Counter(function_names).items() if count > 1)
    duplicate_rules = sorted(name for name, count in Counter(rule_names).items() if count > 1)

    rel_path = repo_relative(file_path, repo_root)
    for name in duplicate_functions:
        issues.append(f"{rel_path}: duplicate function name '{name}'")
    for name in duplicate_rules:
        issues.append(f"{rel_path}: duplicate rule name '{name}'")

    return issues


def check_duplicate_locals(file_path: Path, lines: list[str], repo_root: Path) -> list[str]:
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
                in_loop_body = (
                    any("for (" in previous for previous in active.recent_nonempty_lines)
                    and any(previous == "{" for previous in active.recent_nonempty_lines[-2:])
                )
                if in_loop_body and name in active.declarations:
                    rel_path = repo_relative(file_path, repo_root)
                    first_line = active.declarations[name]
                    issues.append(
                        f"{rel_path}:{index}: duplicate local '{name}' in {active.kind} '{active.name}' (first declared on line {first_line})"
                    )
                elif in_loop_body:
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


def check_unsupported_builtins(file_path: Path, lines: list[str], repo_root: Path) -> list[str]:
    issues: list[str] = []
    rel_path = repo_relative(file_path, repo_root)

    for index, line in enumerate(lines, start=1):
        code = line.split("//", 1)[0]
        stripped = code.strip()
        if not stripped or stripped.startswith("//"):
            continue

        for match in FUNCTION_CALL_RE.finditer(code):
            function_name = match.group(1)
            if function_name in UNSUPPORTED_BUILTINS:
                issues.append(f"{rel_path}:{index}: unsupported XS builtin '{function_name}'")

    return issues


def check_unknown_xs_calls(file_path: Path, lines: list[str], repo_root: Path) -> list[str]:
    issues: list[str] = []
    rel_path = repo_relative(file_path, repo_root)

    for index, line in enumerate(lines, start=1):
        code = line.split("//", 1)[0]
        stripped = code.strip()
        if not stripped:
            continue

        for match in FUNCTION_CALL_RE.finditer(code):
            function_name = match.group(1)
            if function_name.startswith("xs") and function_name not in STOCK_XS_CALLS and function_name not in UNSUPPORTED_BUILTINS:
                issues.append(
                    f"{rel_path}:{index}: unknown xs-prefixed call '{function_name}' is outside the stock AoE3 XS surface"
                )

    return issues


def validate_xs_scripts(repo_root: Path = REPO_ROOT) -> list[str]:
    ai_root = repo_root / "game" / "ai"
    if not ai_root.exists():
        return [f"AI folder not found: {repo_relative(ai_root, repo_root)}"]

    issues: list[str] = []
    for file_path in iter_xs_files(ai_root):
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        issues.extend(check_duplicate_names(file_path, lines, repo_root))
        issues.extend(check_duplicate_locals(file_path, lines, repo_root))
        issues.extend(check_unsupported_builtins(file_path, lines, repo_root))
        issues.extend(check_unknown_xs_calls(file_path, lines, repo_root))

    return issues


def main() -> int:
    parser = build_repo_root_parser("Validate XS duplicate symbols and duplicate rule locals.")
    args = parser.parse_args()
    issues = validate_xs_scripts(args.repo_root.resolve())

    if issues:
        print("XS validation failed:")
        for issue in issues:
            print(f" - {issue}")
        return 1

    print("XS validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
