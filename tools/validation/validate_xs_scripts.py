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
INCLUDE_RE = re.compile(r'^\s*include\s+"([^"]+)"\s*;?')
# Classic form: ``int foo(...)`` / ``bool llBar(...)``. Accepts a custom return
# type (any identifier), which covers base-game struct returns like
# ``ValidResourceInfo getValidResourceInfo(...)``.
CALLABLE_DECL_RE = re.compile(
    r"^\s*(?:mutable\s+|extern\s+)?[A-Za-z_][A-Za-z0-9_]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*\("
)
# Function-pointer form: ``int() createFoo = [](...)`` / ``bool(int) gFoo = impl``
# / function-pointer parameters ``bool(int, int) comp = defaultComp``.
FUNCTION_PTR_DECL_RE = re.compile(
    r"(?:^|,|\()\s*(?:mutable\s+|extern\s+)?[A-Za-z_][A-Za-z0-9_]*\s*\([^)]*\)\s+([A-Za-z_][A-Za-z0-9_]*)\s*="
)
KNOWN_ENGINE_PREFIXES = ("xs", "ai", "kb", "cv", "bt")
# Type keywords also match FUNCTION_CALL_RE when used in function-pointer type
# declarations like ``extern int(int, int) cvFoo``.
KNOWN_LANGUAGE_CALLS = {
    "if", "for", "switch", "while", "return",
    "int", "bool", "float", "string", "vector", "void",
}
# Engine-provided helpers that don't follow the KNOWN_ENGINE_PREFIXES convention.
KNOWN_ENGINE_CALLS = {
    "createSimpleUnitQuery",
    "createUnitQuery",
    # Math builtins exposed by the XS VM.
    "abs", "sin", "cos", "tan", "sqrt", "pow", "min", "max", "round", "ceil", "floor",
}
# AoE3 DE installs on Linux under Proton keep the game tree under
# ``steamapps/common/AoE3DE/Game/AI`` (case-sensitive on Linux). Historically
# native installs used lowercase paths.
BASE_GAME_AI_PATHS = (
    Path.home() / ".local/share/Steam/steamapps/common/AoE3DE/Game/AI",
    Path.home() / ".local/share/Steam/steamapps/common/AoE3DE/game/ai",
    Path.home() / ".steam/steam/steamapps/common/AoE3DE/Game/AI",
    Path.home() / ".steam/steam/steamapps/common/AoE3DE/game/ai",
)
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


def strip_inline_block_comments(line: str, in_block_comment: bool) -> tuple[str, bool]:
    result = []
    cursor = 0

    while cursor < len(line):
        if in_block_comment:
            end = line.find("*/", cursor)
            if end == -1:
                return ("".join(result), True)
            cursor = end + 2
            in_block_comment = False
            continue

        start = line.find("/*", cursor)
        if start == -1:
            result.append(line[cursor:])
            break

        result.append(line[cursor:start])
        cursor = start + 2
        in_block_comment = True

    return ("".join(result), in_block_comment)


def strip_string_literals(code: str) -> str:
    """Remove content inside double-quoted strings so regex scans don't match
    words like ``ENABLED (`` that appear inside log messages."""
    out: list[str] = []
    i = 0
    in_string = False
    while i < len(code):
        ch = code[i]
        if in_string:
            if ch == "\\" and i + 1 < len(code):
                i += 2
                continue
            if ch == '"':
                out.append('"')
                in_string = False
            i += 1
            continue
        if ch == '"':
            out.append('"')
            in_string = True
            i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def collect_declared_callables(ai_root: Path) -> set[str]:
    """Collect everything that can be invoked like a function: classic
    function declarations, rule names, and function-pointer declarations
    (including function-pointer parameters and lambda-assigned globals)."""
    declared: set[str] = set()
    for file_path in iter_xs_files(ai_root):
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        in_block_comment = False
        for line in lines:
            code, in_block_comment = strip_inline_block_comments(line, in_block_comment)
            code = strip_string_literals(code)
            if match := CALLABLE_DECL_RE.match(code):
                declared.add(match.group(1))
            if match := RULE_RE.match(code):
                declared.add(match.group(1))
            for match in FUNCTION_PTR_DECL_RE.finditer(code):
                declared.add(match.group(1))
    return declared


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


def flatten_loader_includes(entry_file: Path, ai_root: Path) -> list[tuple[Path, int, str]]:
    ordered_lines: list[tuple[Path, int, str]] = []
    visited: set[Path] = set()

    def visit(file_path: Path) -> None:
        resolved = file_path.resolve()
        if resolved in visited or not file_path.exists():
            return
        visited.add(resolved)

        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        for index, line in enumerate(lines, start=1):
            if match := INCLUDE_RE.match(line):
                include_path = ai_root / match.group(1).replace("\\", "/")
                visit(include_path)
                continue
            ordered_lines.append((file_path, index, line))

    visit(entry_file)
    return ordered_lines


def should_track_loader_call(function_name: str) -> bool:
    if function_name in KNOWN_LANGUAGE_CALLS:
        return False
    if function_name.startswith(KNOWN_ENGINE_PREFIXES):
        return False
    return True


def resolve_base_game_ai_root() -> Path | None:
    for candidate in BASE_GAME_AI_PATHS:
        try:
            if candidate.exists():
                return candidate
        except OSError:
            continue
    return None


CV_DECL_RE = re.compile(
    r"^\s*(?:mutable\s+|extern\s+|const\s+|extern\s+const\s+)*"
    r"(?:int|bool|float|string|vector)\s+"
    r"(cv[A-Z][A-Za-z0-9_]*)\s*(?:=|;)"
)
CV_USE_RE = re.compile(r"\b(cv[A-Z][A-Za-z0-9_]*)\b")


def collect_declared_cv_vars(ai_root: Path) -> set[str]:
    """Collect cv-prefixed civ-variable declarations including function-pointer
    variants like ``extern int(int, int) cvCreateBaseAttackRoute = ...``. These
    are settable AI knobs the engine looks up by exact name — an assignment to
    an undeclared cv-symbol produces XS ERROR 0310 at runtime."""
    declared: set[str] = set()
    for file_path in iter_xs_files(ai_root):
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        in_block_comment = False
        for line in lines:
            code, in_block_comment = strip_inline_block_comments(line, in_block_comment)
            code = strip_string_literals(code)
            if match := CV_DECL_RE.match(code):
                declared.add(match.group(1))
            # Function-pointer cv declarations.
            for match in FUNCTION_PTR_DECL_RE.finditer(code):
                name = match.group(1)
                if name.startswith("cv") and len(name) >= 3 and name[2].isupper():
                    declared.add(name)
    return declared


def check_undefined_cv_vars(repo_root: Path) -> list[str]:
    """Flag cv-prefixed symbol uses that have no extern declaration in the
    mod or base-game AI. Catches ``cvMinNumVills = 18`` patterns where the
    variable was never declared, which the XS VM rejects with
    ``XS ERROR 0310: INVALID SYMBOL LOOKUP FOR ...``."""
    ai_root = repo_root / "game" / "ai"
    if not ai_root.exists():
        return []

    declared = collect_declared_cv_vars(ai_root)
    base_root = resolve_base_game_ai_root()
    if base_root is not None:
        try:
            declared |= collect_declared_cv_vars(base_root)
        except OSError:
            pass

    issues: list[str] = []
    for file_path in iter_xs_files(ai_root):
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        in_block_comment = False
        rel_path = repo_relative(file_path, repo_root)

        for index, line in enumerate(lines, start=1):
            uncommented, in_block_comment = strip_inline_block_comments(line, in_block_comment)
            code = uncommented.split("//", 1)[0]
            # Skip the declaration line itself.
            if CV_DECL_RE.match(code):
                continue
            scan_target = strip_string_literals(code)
            if not scan_target.strip():
                continue
            for match in CV_USE_RE.finditer(scan_target):
                name = match.group(1)
                if name not in declared:
                    issues.append(
                        f"{rel_path}:{index}: undefined cv-variable '{name}' — not declared as extern int/bool/float/string/vector in the mod or base game"
                    )

    return issues


def check_undefined_helper_calls(repo_root: Path) -> list[str]:
    """Flag calls to non-engine, non-language functions that have no definition
    anywhere in the mod's AI or the installed base-game AI. Catches e.g. a
    typo'd helper name that the engine's XS VM will reject at runtime with
    ``ERROR 0172: '...' IS NOT A VALID OPERATOR``.
    """
    ai_root = repo_root / "game" / "ai"
    if not ai_root.exists():
        return []

    declared = collect_declared_callables(ai_root)
    base_root = resolve_base_game_ai_root()
    if base_root is not None:
        try:
            declared |= collect_declared_callables(base_root)
        except OSError:
            # Base game path exists but we can't read it — fall back to mod-only.
            pass

    issues: list[str] = []
    for file_path in iter_xs_files(ai_root):
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        in_block_comment = False
        rel_path = repo_relative(file_path, repo_root)

        for index, line in enumerate(lines, start=1):
            uncommented, in_block_comment = strip_inline_block_comments(line, in_block_comment)
            code = uncommented.split("//", 1)[0]
            declaration_match = CALLABLE_DECL_RE.match(code)
            declared_here = declaration_match.group(1) if declaration_match else None
            scan_target = strip_string_literals(code)
            stripped = scan_target.strip()
            if not stripped:
                continue

            for match in FUNCTION_CALL_RE.finditer(scan_target):
                function_name = match.group(1)
                if function_name in KNOWN_LANGUAGE_CALLS:
                    continue
                if function_name.startswith(KNOWN_ENGINE_PREFIXES):
                    continue
                if function_name in STOCK_XS_CALLS or function_name in KNOWN_ENGINE_CALLS:
                    continue
                if function_name.startswith("debug"):
                    continue
                if declared_here is not None and function_name == declared_here:
                    continue
                if function_name in declared:
                    continue
                issues.append(
                    f"{rel_path}:{index}: undefined helper call '{function_name}' — not declared in the mod or base game"
                )

    return issues


def check_unresolved_loader_calls(repo_root: Path) -> list[str]:
    ai_root = repo_root / "game" / "ai"
    loader_path = ai_root / "aiLoaderStandard.xs"
    if not loader_path.exists():
        return []

    issues: list[str] = []
    known_helpers: set[str] = set()
    declared_callables = collect_declared_callables(ai_root)
    in_block_comment = False

    for file_path, index, line in flatten_loader_includes(loader_path, ai_root):
        uncommented, in_block_comment = strip_inline_block_comments(line, in_block_comment)
        code = uncommented.split("//", 1)[0]
        stripped = code.strip()
        if not stripped:
            continue

        declaration_match = CALLABLE_DECL_RE.match(code)
        if declaration_match is not None:
            known_helpers.add(declaration_match.group(1))
        if rule_match := RULE_RE.match(code):
            known_helpers.add(rule_match.group(1))
        for ptr_match in FUNCTION_PTR_DECL_RE.finditer(code):
            known_helpers.add(ptr_match.group(1))

        scan_target = strip_string_literals(code)
        for match in FUNCTION_CALL_RE.finditer(scan_target):
            function_name = match.group(1)
            if should_track_loader_call(function_name) is False:
                continue
            if function_name not in declared_callables:
                continue
            if declaration_match is not None and function_name == declaration_match.group(1):
                continue
            if function_name not in known_helpers:
                rel_path = repo_relative(file_path, repo_root)
                issues.append(
                    f"{rel_path}:{index}: helper call '{function_name}' appears before any declaration in aiLoaderStandard include order"
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

    issues.extend(check_undefined_helper_calls(repo_root))
    issues.extend(check_undefined_cv_vars(repo_root))
    issues.extend(check_unresolved_loader_calls(repo_root))

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
