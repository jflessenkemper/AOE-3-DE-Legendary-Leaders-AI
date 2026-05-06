#!/usr/bin/env python3
"""
TIER 3: AUTOMATED COMPARISON MATRIX

Parses TIER 2 scenario test logs and compares AI behavior against:
- XS doctrine definitions (btVariables from aiSetup.xs)
- HTML playstyle descriptions
- Expected baseline metrics

Generates a validation matrix with PASS/FAIL per civ and delta metrics.
"""

import json
import re
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional

repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))

from tools.migration.anw_token_map import ANW_CIVS
from tools.migration.anw_mapping import ANW_CIVS_BY_SLUG


@dataclass
class GameMetrics:
    """Metrics extracted from a test game log"""
    civ_name: str
    civ_token: str
    first_ageup_time: Optional[float] = None  # minutes
    units_trained: Dict[str, int] = None
    buildings_built: Dict[str, int] = None
    cards_used: List[str] = None
    trade_routes_active: bool = False
    crashed: bool = False

    def __post_init__(self):
        if self.units_trained is None:
            self.units_trained = {}
        if self.buildings_built is None:
            self.buildings_built = {}
        if self.cards_used is None:
            self.cards_used = []


@dataclass
class DoctrineBaseline:
    """Expected behavior based on XS doctrines"""
    civ_token: str
    description: str
    btRushBoom: float  # 0=boom, 0.5=rush
    btOffenseDefense: float  # 0=defense, 1=offense
    btBiasCav: float
    btBiasInf: float
    btBiasArt: float
    btBiasTrade: float

    def get_expected_ageup_range(self) -> tuple:
        """Estimate age-up timing based on btRushBoom"""
        if self.btRushBoom >= 0.5:
            return (7.5, 9.0)  # Rushers age early
        else:
            return (9.0, 11.0)  # Boomers age later

    def get_expected_unit_composition(self) -> dict:
        """Estimate unit ratios based on bt biases"""
        total_bias = abs(self.btBiasCav) + abs(self.btBiasInf) + abs(self.btBiasArt)
        if total_bias == 0:
            total_bias = 1

        return {
            "cavalry": max(0, self.btBiasCav) / total_bias if total_bias else 0.33,
            "infantry": max(0, self.btBiasInf) / total_bias if total_bias else 0.33,
            "artillery": max(0, self.btBiasArt) / total_bias if total_bias else 0.33,
        }


@dataclass
class ValidationResult:
    """Result of comparing observed metrics to doctrine baseline"""
    civ_token: str
    civ_slug: str
    xs_doctrine: DoctrineBaseline
    observed_metrics: GameMetrics

    # Pass/fail flags
    ageup_passed: bool = False
    unit_composition_passed: bool = False
    card_validation_passed: bool = False
    no_crash: bool = True

    # Delta metrics
    ageup_delta: float = 0.0  # minutes
    infantry_ratio_delta: float = 0.0  # percentage points
    cavalry_ratio_delta: float = 0.0
    artillery_ratio_delta: float = 0.0

    overall_pass: bool = False


class LogParser:
    """Parse TIER 2 test game logs"""

    @staticmethod
    def parse_log_file(log_path: Path) -> Optional[GameMetrics]:
        """Extract metrics from a test log file"""
        if not log_path.exists():
            return None

        with open(log_path) as f:
            content = f.read()

        # Extract civ token from filename (format: {CivToken}_scenario.log)
        civ_token_match = re.search(r'([A-Z][A-Za-z0-9]+)_scenario\.log', log_path.name)
        civ_token = civ_token_match.group(1) if civ_token_match else "Unknown"

        # Try to extract from content as backup
        civ_match = re.search(r'Civ:\s*(\w+)', content)
        if civ_match:
            civ_token = civ_match.group(1)

        civ_name = civ_token.replace("ANW", "")
        metrics = GameMetrics(civ_name=civ_name, civ_token=civ_token)

        # Extract age-up time (new format: [AGEUP]: First age-up: 8m 30s)
        ageup_match = re.search(r'\[AGEUP\]:\s*First age-up:\s*(\d+)m\s*(\d+)s', content)
        if ageup_match:
            minutes = int(ageup_match.group(1))
            seconds = int(ageup_match.group(2))
            metrics.first_ageup_time = minutes + seconds / 60.0
        else:
            # Fallback to old format
            ageup_match = re.search(r'First age-up:\s*(\d+)m\s*(\d+)s', content)
            if ageup_match:
                minutes = int(ageup_match.group(1))
                seconds = int(ageup_match.group(2))
                metrics.first_ageup_time = minutes + seconds / 60.0

        # Extract unit counts (new format: [UNITS_TRAINED]: Infantry(8), Cavalry(5))
        units_match = re.search(r'\[UNITS_TRAINED\]:\s*(.+?)(?=\[|$)', content)
        if units_match:
            units_str = units_match.group(1)
            for match in re.finditer(r'(\w+)\((\d+)\)', units_str):
                unit_type = match.group(1).lower()
                count = int(match.group(2))
                metrics.units_trained[unit_type] = count
        else:
            # Fallback to old format
            units_match = re.search(r'Units trained:\s*(.+?)(?=\n|$)', content)
            if units_match:
                units_str = units_match.group(1)
                for match in re.finditer(r'(\w+)\((\d+)\)', units_str):
                    unit_type = match.group(1).lower()
                    count = int(match.group(2))
                    metrics.units_trained[unit_type] = count

        # Extract buildings (new format: [BUILDINGS]: House, Farm, Stable)
        buildings_match = re.search(r'\[BUILDINGS\]:\s*(.+?)(?=\[|$)', content)
        if buildings_match:
            buildings_str = buildings_match.group(1)
            for building in buildings_str.split(','):
                building = building.strip().lower()
                if building:
                    metrics.buildings_built[building] = metrics.buildings_built.get(building, 0) + 1
        else:
            # Fallback to old format
            buildings_match = re.search(r'Buildings:\s*(.+?)(?=\n|$)', content)
            if buildings_match:
                buildings_str = buildings_match.group(1)
                for building in buildings_str.split(','):
                    building = building.strip().lower()
                    if building:
                        metrics.buildings_built[building] = metrics.buildings_built.get(building, 0) + 1

        # Extract cards used (new format: [CARDS]: [Card1], [Card2])
        cards_match = re.search(r'\[CARDS\]:\s*(.+?)(?=\[|$)', content)
        if cards_match:
            cards_str = cards_match.group(1)
            metrics.cards_used = [c.strip('[]').strip() for c in cards_str.split(',')]
        else:
            # Fallback to old format
            cards_match = re.search(r'Cards:\s*\[(.+?)\]', content)
            if cards_match:
                cards_str = cards_match.group(1)
                metrics.cards_used = [c.strip() for c in cards_str.split(',')]

        # Check trade routes (new format: [TRADE_ROUTES]: Yes)
        if re.search(r'\[TRADE_ROUTES\]:\s*Yes', content) or 'trade routes: Yes' in content.lower():
            metrics.trade_routes_active = True

        # Check for crash
        if 'crashed' in content.lower() or 'ended early' in content.lower():
            metrics.crashed = True

        return metrics


class Comparator:
    """Compare observed metrics to doctrine baselines"""

    @staticmethod
    def compare(metrics: GameMetrics, baseline: DoctrineBaseline, deck: dict) -> ValidationResult:
        """Compare observed game metrics to XS doctrine"""
        result = ValidationResult(
            civ_token=baseline.civ_token,
            civ_slug=metrics.civ_name,
            xs_doctrine=baseline,
            observed_metrics=metrics,
        )

        # 1. Age-up timing check
        if metrics.first_ageup_time:
            expected_min, expected_max = baseline.get_expected_ageup_range()
            if expected_min <= metrics.first_ageup_time <= expected_max:
                result.ageup_passed = True
            result.ageup_delta = metrics.first_ageup_time - (expected_min + expected_max) / 2

        # 2. Unit composition check
        total_units = sum(metrics.units_trained.values())
        if total_units > 0:
            observed_inf = metrics.units_trained.get('infantry', 0) / total_units
            observed_cav = metrics.units_trained.get('cavalry', 0) / total_units
            observed_art = metrics.units_trained.get('artillery', 0) / total_units

            expected = baseline.get_expected_unit_composition()
            result.infantry_ratio_delta = (observed_inf - expected['infantry']) * 100
            result.cavalry_ratio_delta = (observed_cav - expected['cavalry']) * 100
            result.artillery_ratio_delta = (observed_art - expected['artillery']) * 100

            # Pass if all within ±15%
            if all(abs(d) <= 15 for d in [result.infantry_ratio_delta, result.cavalry_ratio_delta, result.artillery_ratio_delta]):
                result.unit_composition_passed = True

        # 3. Card validation
        cards_in_deck = set()
        for age_cards in deck.values():
            cards_in_deck.update(age_cards)

        all_valid = all(card in cards_in_deck for card in metrics.cards_used)
        result.card_validation_passed = all_valid

        # 4. Crash check
        result.no_crash = not metrics.crashed

        # Overall pass
        result.overall_pass = all([
            result.ageup_passed,
            result.unit_composition_passed,
            result.card_validation_passed,
            result.no_crash,
        ])

        return result


def main():
    import argparse

    parser = argparse.ArgumentParser(description="TIER 3: Validate AI behavior against XS doctrines")
    parser.add_argument("--logs", type=Path, help="Directory containing TIER 2 test logs")
    args = parser.parse_args()

    print("\n" + "="*80)
    print("TIER 3: AUTOMATED COMPARISON MATRIX")
    print("="*80)

    # Load decks
    with open(repo_root / "data/decks_anw.json") as f:
        decks = json.load(f)

    # Load XS doctrines
    with open(repo_root / "game/ai/core/aiSetup.xs") as f:
        xs_content = f.read()

    doctrines = {}
    cases = re.findall(
        r'case\s+cCiv(\w+):.*?//\s*([^\n]+)\n(.*?)break;',
        xs_content,
        re.DOTALL
    )

    for civ_code, comment, block in cases:
        traits = {}
        for bt_var in ['btRushBoom', 'btOffenseDefense', 'btBiasCav', 'btBiasInf', 'btBiasArt', 'btBiasTrade']:
            match = re.search(rf'{bt_var}\s*=\s*([-\d.]+)', block)
            if match:
                traits[bt_var] = float(match.group(1))

        if traits:
            doctrines[f"ANW{civ_code}"] = DoctrineBaseline(
                civ_token=f"ANW{civ_code}",
                description=comment,
                **traits
            )

    print(f"\n✓ Loaded {len(doctrines)} XS doctrines")
    print(f"✓ Loaded {len(decks)} decks")

    # Determine log directory
    if args.logs:
        log_dir = args.logs
    else:
        log_dir = repo_root / "logs" / "tier2"

    # Validate a few key civs or all civs if logs available
    print("\n" + "="*80)
    print("VALIDATION MATRIX")
    print("="*80)
    print("\nFormat: {civ_token} | Doctrine | AgeUp | Units | Cards | Crash | Overall")
    print("-" * 80)

    results_list = []

    if log_dir.exists() and any(log_dir.glob("ANW*_scenario.log")):
        # Parse real log files
        print(f"\n✓ Found test logs in {log_dir}")
        log_files = sorted(log_dir.glob("ANW*_scenario.log"))

        for log_file in log_files:
            metrics = LogParser.parse_log_file(log_file)
            if not metrics:
                continue

            token = metrics.civ_token
            if token in doctrines and token in decks:
                baseline = doctrines[token]
                result = Comparator.compare(metrics, baseline, decks[token])
                results_list.append(result)

                status = "✓ PASS" if result.overall_pass else "✗ FAIL"
                print(f"{token:<15} | {baseline.description:<20} | " +
                      f"{'✓' if result.ageup_passed else '✗'} | " +
                      f"{'✓' if result.unit_composition_passed else '✗'} | " +
                      f"{'✓' if result.card_validation_passed else '✗'} | " +
                      f"{'✓' if result.no_crash else '✗'} | {status}")
    else:
        # Demo mode: use mock data for example civs
        print(f"\n⚠ No test logs found. Running in demo mode with mock data.")
        example_civs = ["ANWBritish", "ANWFrench", "ANWRussians"]

        for token in example_civs:
            if token in doctrines and token in decks:
                baseline = doctrines[token]

                # Create mock metrics
                metrics = GameMetrics(
                    civ_name=token.replace("ANW", ""),
                    civ_token=token,
                    first_ageup_time=9.5 if baseline.btRushBoom < 0.5 else 8.2,
                    units_trained={"infantry": 8, "cavalry": 5, "artillery": 2},
                    cards_used=["Card1", "Card2", "Card3"],
                )

                result = Comparator.compare(metrics, baseline, decks[token])
                results_list.append(result)

                status = "✓ PASS" if result.overall_pass else "✗ FAIL"
                print(f"{token:<15} | {baseline.description:<20} | " +
                      f"{'✓' if result.ageup_passed else '✗'} | " +
                      f"{'✓' if result.unit_composition_passed else '✗'} | " +
                      f"{'✓' if result.card_validation_passed else '✗'} | " +
                      f"{'✓' if result.no_crash else '✗'} | {status}")

    print("\n" + "="*80)
    if results_list:
        passed = sum(1 for r in results_list if r.overall_pass)
        total = len(results_list)
        print(f"TIER 3: Validation Summary")
        print(f"       {passed}/{total} civs passed validation")
    else:
        print("TIER 3: Ready to compare TIER 2 test logs")
        print("       Run: python validate_tier3_comparison.py --logs ./logs/tier2")
    print("="*80)


if __name__ == "__main__":
    main()
