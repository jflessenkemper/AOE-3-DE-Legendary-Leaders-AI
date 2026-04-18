from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.validation.common import REPO_ROOT, build_repo_root_parser, repo_relative


DEFAULT_LOG_PATH = Path.home() / ".steam/steam/steamapps/compatdata/933110/pfx/drive_c/users/steamuser/Games/Age of Empires 3 DE/Logs/Age3Log.txt"
DEFAULT_SPEC_PATH = REPO_ROOT / "tools" / "validation" / "runtime_specs" / "legendary_runtime_suites.json"


@dataclass(frozen=True)
class RuntimeExpectation:
    kind: str
    value: str
    description: str


def load_runtime_spec(spec_path: Path) -> dict:
    with spec_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Runtime spec must be a JSON object: {spec_path}")
    suites = payload.get("suites")
    if not isinstance(suites, list) or not suites:
        raise ValueError(f"Runtime spec must contain a non-empty 'suites' array: {spec_path}")
    return payload


def normalize_expectations(raw_items: list[dict], field: str, default_kind: str) -> list[RuntimeExpectation]:
    expectations: list[RuntimeExpectation] = []
    for item in raw_items:
        if not isinstance(item, dict):
            raise ValueError(f"Each '{field}' entry must be an object")
        value = item.get("value")
        if not isinstance(value, str) or not value:
            raise ValueError(f"Each '{field}' entry requires a non-empty string 'value'")
        kind = item.get("kind", default_kind)
        if kind not in {"substring", "regex"}:
            raise ValueError(f"Unsupported expectation kind '{kind}' in '{field}'")
        description = item.get("description", value)
        if not isinstance(description, str) or not description:
            raise ValueError(f"Each '{field}' entry requires a non-empty string 'description'")
        expectations.append(RuntimeExpectation(kind=kind, value=value, description=description))
    return expectations


def expectation_matches(expectation: RuntimeExpectation, text: str) -> bool:
    if expectation.kind == "substring":
        return expectation.value in text
    return re.search(expectation.value, text, re.MULTILINE) is not None


def expectation_position(expectation: RuntimeExpectation, text: str) -> int:
    if expectation.kind == "substring":
        return text.find(expectation.value)
    match = re.search(expectation.value, text, re.MULTILINE)
    if match is None:
        return -1
    return match.start()


def validate_runtime_log(repo_root: Path = REPO_ROOT, log_path: Path = DEFAULT_LOG_PATH,
                         spec_path: Path = DEFAULT_SPEC_PATH, suite_names: list[str] | None = None) -> list[str]:
    if not log_path.exists():
        return [f"Runtime log not found: {repo_relative(log_path, repo_root)}"]
    if not spec_path.exists():
        return [f"Runtime spec not found: {repo_relative(spec_path, repo_root)}"]

    try:
        spec = load_runtime_spec(spec_path)
    except ValueError as exc:
        return [str(exc)]

    text = log_path.read_text(encoding="utf-8", errors="replace")
    available_suites = {suite.get("name"): suite for suite in spec["suites"] if isinstance(suite, dict)}

    if suite_names is None or len(suite_names) == 0:
        selected_suite_names = list(available_suites.keys())
    else:
        selected_suite_names = suite_names

    issues: list[str] = []

    for suite_name in selected_suite_names:
        suite = available_suites.get(suite_name)
        if suite is None:
            issues.append(f"Unknown runtime suite '{suite_name}' in {repo_relative(spec_path, repo_root)}")
            continue

        required = normalize_expectations(suite.get("required", []), "required", "substring")
        forbidden = normalize_expectations(suite.get("forbidden", []), "forbidden", "substring")
        ordered = normalize_expectations(suite.get("ordered", []), "ordered", "substring")

        for expectation in required:
            if expectation_matches(expectation, text) is False:
                issues.append(f"[{suite_name}] missing required log marker: {expectation.description}")

        for expectation in forbidden:
            if expectation_matches(expectation, text) is True:
                issues.append(f"[{suite_name}] found forbidden log marker: {expectation.description}")

        if ordered:
            last_position = -1
            for expectation in ordered:
                position = expectation_position(expectation, text)
                if position < 0:
                    issues.append(f"[{suite_name}] missing ordered log marker: {expectation.description}")
                    break
                if position < last_position:
                    issues.append(f"[{suite_name}] ordered marker out of sequence: {expectation.description}")
                    break
                last_position = position

    return issues


def main() -> int:
    parser = build_repo_root_parser("Validate Age of Empires III runtime logs against suite-based Legendary Leaders expectations.")
    parser.add_argument(
        "--log-path",
        type=Path,
        default=DEFAULT_LOG_PATH,
        help="Age3Log.txt path to validate.",
    )
    parser.add_argument(
        "--spec-path",
        type=Path,
        default=DEFAULT_SPEC_PATH,
        help="JSON spec file containing one or more runtime validation suites.",
    )
    parser.add_argument(
        "--suite",
        action="append",
        default=[],
        help="Runtime suite name to validate. Repeat to validate multiple suites. Defaults to all suites in the spec.",
    )
    args = parser.parse_args()

    issues = validate_runtime_log(
        repo_root=args.repo_root.resolve(),
        log_path=args.log_path.resolve(),
        spec_path=args.spec_path.resolve(),
        suite_names=args.suite,
    )
    if issues:
        print("Runtime log validation failed:")
        for issue in issues:
            print(f" - {issue}")
        return 1

    suite_summary = ", ".join(args.suite) if args.suite else "all suites"
    print(f"Runtime log validation passed for {suite_summary}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())