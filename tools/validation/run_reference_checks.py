from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tools.validation.common import build_repo_root_parser
from tools.validation.validate_civ_homecities import validate_civ_homecities
from tools.validation.validate_civmods_ui import validate_civmods_ui
from tools.validation.validate_civ_crossrefs import validate_civ_crossrefs
from tools.validation.validate_homecity_cards import validate_homecity_cards
from tools.validation.validate_packaged_mod import validate_packaged_mod_with_options
from tools.validation.validate_protomods import validate_protomods
from tools.validation.validate_stringtables import validate_stringtables
from tools.validation.validate_techtree import validate_techtree
from tools.validation.validate_xml_well_formed import validate_xml_well_formed
from tools.validation.validate_xs_scripts import validate_xs_scripts


@dataclass
class ValidationResult:
    name: str
    findings: list[str]

    @property
    def passed(self) -> bool:
        return not self.findings


def run_age_of_pirates_profile(repo_root: Path, strict_display_name_ids: bool = False) -> list[ValidationResult]:
    return [
        ValidationResult("Proto", validate_protomods(repo_root)),
        ValidationResult("TechTree", validate_techtree(repo_root)),
        ValidationResult("StringTables", validate_stringtables(repo_root)),
        ValidationResult("XML Well-Formedness", validate_xml_well_formed(repo_root)),
        ValidationResult("XS", validate_xs_scripts(repo_root)),
        ValidationResult(
            "Civ Crossrefs",
            validate_civ_crossrefs(
                repo_root,
                civ_prefixes=None,
                tech_prefixes=(
                    "zp",
                    "SPC",
                    "Nat",
                    "PenalColony",
                    "Maltese",
                    "Wokou",
                    "Jewish",
                    "Auditore",
                    "Inuit",
                    "Maori",
                    "Aboriginal",
                    "Korowai",
                ),
                validate_display_name_ids=strict_display_name_ids,
                allowed_missing_string_ids={"45433", "122142"},
            ),
        ),
        ValidationResult(
            "Civ/HomeCity",
            validate_civ_homecities(
                repo_root,
                name_prefixes=None,
                homecity_glob="homecity*.xml",
                allow_missing_homecity_files=True,
            ),
        ),
        ValidationResult(
            "Homecity Cards",
            validate_homecity_cards(
                repo_root,
                homecity_glob="homecity*.xml",
                tech_prefixes=("zp", "SPC", "Nat", "Auditore", "PenalColony", "Maltese", "Wokou"),
            ),
        ),
        ValidationResult("Civ UI", validate_civmods_ui(repo_root, name_prefixes=None)),
    ]


def run_packaged_mod_profile(repo_root: Path, strict_display_name_ids: bool = False) -> list[ValidationResult]:
    packaged_result = validate_packaged_mod_with_options(
        repo_root,
        validate_display_name_ids=strict_display_name_ids,
    )
    return [ValidationResult("Packaged Mod", packaged_result.issues)]


def format_results(profile_name: str, repo_root: Path, results: list[ValidationResult]) -> str:
    lines = [f"Reference validation profile: {profile_name}", f"Target repo: {repo_root}", ""]

    passing = sum(1 for result in results if result.passed)
    failing = len(results) - passing
    lines.append(f"Summary: {passing} passed, {failing} failed")
    lines.append("")

    for result in results:
        status = "PASS" if result.passed else "FAIL"
        lines.append(f"[{status}] {result.name}")
        for finding in result.findings:
            lines.append(f"  - {finding}")
        if result.passed:
            lines.append("  - no findings")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = build_repo_root_parser("Run a reusable reference-mod validation profile.")
    parser.add_argument(
        "--profile",
        choices=["age-of-pirates", "packaged-mod"],
        default="age-of-pirates",
        help="Reference validation profile to run.",
    )
    parser.add_argument(
        "--report-file",
        type=Path,
        help="Optional path to write the formatted report to.",
    )
    parser.add_argument(
        "--fail-on-findings",
        action="store_true",
        help="Return a non-zero exit code when the reference repo has findings.",
    )
    parser.add_argument(
        "--strict-display-name-ids",
        action="store_true",
        help="Require DisplayNameID locIDs to resolve from repo StringTables in profiles that use civ cross-reference checks.",
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    if args.profile == "age-of-pirates":
        results = run_age_of_pirates_profile(repo_root, strict_display_name_ids=args.strict_display_name_ids)
    elif args.profile == "packaged-mod":
        results = run_packaged_mod_profile(repo_root, strict_display_name_ids=args.strict_display_name_ids)
    else:
        raise ValueError(f"Unsupported profile: {args.profile}")

    report = format_results(args.profile, repo_root, results)
    print(report, end="")

    if args.report_file is not None:
        args.report_file.parent.mkdir(parents=True, exist_ok=True)
        args.report_file.write_text(report, encoding="utf-8")

    has_findings = any(not result.passed for result in results)
    if has_findings and args.fail_on_findings:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
