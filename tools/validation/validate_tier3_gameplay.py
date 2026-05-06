#!/usr/bin/env python3
"""
TIER 3: AUTOMATED GAMEPLAY VALIDATION & COMPARISON MATRIX

Parses scenario trigger outputs and compares actual AI behavior against
documented doctrines. Generates a comparison matrix showing:
- Expected doctrine (from XS code)
- HTML playstyle description
- Actual AI behavior (from scenario logs)
- Match/fail verdict
"""

import sys
import json
import re
from pathlib import Path
from dataclasses import dataclass

repo_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo_root))

from tools.migration.anw_token_map import ANW_CIVS
from tools.migration.anw_mapping import ANW_CIVS_BY_SLUG

@dataclass
class GameMetrics:
    """Extracted metrics from a 10-minute scenario game"""
    civ_name: str
    first_age_up_time: int  # seconds
    unit_composition: dict  # {"Infantry": 0.6, "Cavalry": 0.2, "Artillery": 0.1, "Native": 0.1}
    building_order: list  # ["Barracks", "Farm", "Mill", ...]
    cards_played: list  # ["Royal Mint", "French Immigrants", ...]
    trade_route_active: bool
    crash_or_softlock: bool
    game_completed: bool

def parse_scenario_log(log_file_path: str) -> GameMetrics:
    """
    Parse trigger output from scenario validator.
    Format: TYPE;TIMESTAMP;PLAYER;VALUE;[OPTIONAL]
    """
    with open(log_file_path) as f:
        lines = f.readlines()

    metrics = GameMetrics(
        civ_name="",
        first_age_up_time=0,
        unit_composition={},
        building_order=[],
        cards_played=[],
        trade_route_active=False,
        crash_or_softlock=False,
        game_completed=False,
    )

    unit_counts = {"Infantry": 0, "Cavalry": 0, "Artillery": 0, "Native": 0, "Other": 0}
    unit_type_map = {
        "Musketeer": "Infantry", "Pikeman": "Infantry", "Skirmisher": "Infantry",
        "Dragoon": "Cavalry", "Hussar": "Cavalry", "Lancer": "Cavalry",
        "Cannon": "Artillery", "Mortar": "Artillery",
        "Native": "Native",
    }

    for line in lines:
        parts = line.strip().split(";")
        if not parts or len(parts) < 2:
            continue

        event_type = parts[0]

        if event_type == "AGE_UP" and len(parts) >= 4:
            time_str = parts[1]
            time_sec = parse_time(time_str)
            if metrics.first_age_up_time == 0:
                metrics.first_age_up_time = time_sec
            metrics.civ_name = parts[2]

        elif event_type == "UNIT_TRAINED" and len(parts) >= 4:
            unit_type = parts[3]
            category = unit_type_map.get(unit_type, "Other")
            unit_counts[category] += 1

        elif event_type == "BUILDING" and len(parts) >= 4:
            building = parts[3]
            metrics.building_order.append(building)

        elif event_type == "CARD" and len(parts) >= 4:
            card_name = parts[3]
            metrics.cards_played.append(card_name)

        elif event_type == "TRADE" and len(parts) >= 4:
            if parts[3] == "active":
                metrics.trade_route_active = True

        elif event_type == "ERROR":
            metrics.crash_or_softlock = True

        elif event_type == "END":
            metrics.game_completed = True

    # Normalize unit composition
    total_units = sum(unit_counts.values())
    if total_units > 0:
        metrics.unit_composition = {k: v / total_units for k, v in unit_counts.items()}

    return metrics

def parse_time(time_str: str) -> int:
    """Convert 'MM:SS' to total seconds"""
    parts = time_str.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    return 0

def get_doctrine_traits(civ_token: str) -> dict:
    """Load XS doctrine traits for a civ"""
    with open(repo_root / "game/ai/core/aiSetup.xs") as f:
        xs_content = f.read()

    # Find this civ's case block
    pattern = rf'case c[A-Za-z]*{civ_token[3:]}:.*?//\s*([^\n]+)\n(.*?)break;'
    match = re.search(pattern, xs_content, re.DOTALL | re.IGNORECASE)

    if not match:
        return {}

    block = match.group(2)
    traits = {}

    for bt_var in ['btRushBoom', 'btOffenseDefense', 'btBiasCav', 'btBiasInf', 'btBiasArt', 'btBiasTrade']:
        m = re.search(rf'{bt_var}\s*=\s*([-\d.]+)', block)
        if m:
            traits[bt_var] = float(m.group(1))

    return traits

def validate_metrics(metrics: GameMetrics, doctrine: dict, deck_cards: list) -> dict:
    """Compare actual metrics against expected doctrine"""
    verdict = {
        "civ": metrics.civ_name,
        "tests": {},
        "passed": True,
    }

    # Test 1: No crashes
    verdict["tests"]["crash"] = {
        "expected": "No crash",
        "actual": "Crashed" if metrics.crash_or_softlock else "OK",
        "passed": not metrics.crash_or_softlock,
    }

    # Test 2: Game completed
    verdict["tests"]["game_completed"] = {
        "expected": "Game ran 10 minutes",
        "actual": "Completed" if metrics.game_completed else "Did not complete",
        "passed": metrics.game_completed,
    }

    # Test 3: Age-up timing
    # Rushers (btRushBoom >= 0.5) should age by ~8 min
    # Boomers (btRushBoom < 0.5) should age by ~10 min
    is_rusher = doctrine.get("btRushBoom", 0) >= 0.5
    expected_age_time = 480 if is_rusher else 600  # 8 or 10 min
    tolerance = 120  # ±2 min
    actual_age_time = metrics.first_age_up_time
    age_ok = abs(actual_age_time - expected_age_time) <= tolerance

    verdict["tests"]["age_up_timing"] = {
        "expected": f"{expected_age_time}s ({expected_age_time//60}m)",
        "actual": f"{actual_age_time}s ({actual_age_time//60}m)" if actual_age_time > 0 else "Not reached",
        "passed": age_ok,
    }

    # Test 4: Unit composition matches doctrine bias
    # If btBiasCav > 0.3, expect Cavalry > 30%
    # If btBiasInf > 0.3, expect Infantry > 30%
    unit_tests_passed = True

    if doctrine.get("btBiasCav", 0) > 0.3:
        if metrics.unit_composition.get("Cavalry", 0) < 0.2:
            unit_tests_passed = False

    if doctrine.get("btBiasInf", 0) > 0.3:
        if metrics.unit_composition.get("Infantry", 0) < 0.2:
            unit_tests_passed = False

    verdict["tests"]["unit_composition"] = {
        "expected": f"Inf:{doctrine.get('btBiasInf', 0):.1f}, Cav:{doctrine.get('btBiasCav', 0):.1f}",
        "actual": f"Inf:{metrics.unit_composition.get('Infantry', 0):.1f}, Cav:{metrics.unit_composition.get('Cavalry', 0):.1f}",
        "passed": unit_tests_passed,
    }

    # Test 5: All cards are from deck
    invalid_cards = [c for c in metrics.cards_played if c not in deck_cards]
    verdict["tests"]["card_validity"] = {
        "expected": "All cards from decks_anw.json",
        "actual": f"{len(metrics.cards_played)} cards played, {len(invalid_cards)} invalid",
        "passed": len(invalid_cards) == 0,
    }

    # Test 6: Trade routes (if btBiasTrade > 0)
    if doctrine.get("btBiasTrade", 0) > 0:
        verdict["tests"]["trade_routes"] = {
            "expected": "Trade routes active",
            "actual": "Active" if metrics.trade_route_active else "Not active",
            "passed": metrics.trade_route_active,
        }

    # Overall verdict
    verdict["passed"] = all(t.get("passed", False) for t in verdict["tests"].values())

    return verdict

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 validate_tier3_gameplay.py <log_file> [civ_name]")
        print("\nExample:")
        print("  python3 validate_tier3_gameplay.py age3log_validator_output.txt ANWBritish")
        sys.exit(1)

    log_file = sys.argv[1]
    specified_civ = sys.argv[2] if len(sys.argv) > 2 else None

    if not Path(log_file).exists():
        print(f"Error: {log_file} not found")
        sys.exit(1)

    # Parse scenario output
    metrics = parse_scenario_log(log_file)

    # Load doctrine and deck
    with open(repo_root / "data/decks_anw.json") as f:
        decks = json.load(f)

    civ_token = specified_civ or metrics.civ_name.replace(" ", "")
    if civ_token not in decks:
        print(f"Error: {civ_token} not found in decks_anw.json")
        sys.exit(1)

    deck_cards = []
    for age_cards in decks[civ_token].values():
        deck_cards.extend(age_cards)

    doctrine = get_doctrine_traits(civ_token)

    # Validate
    verdict = validate_metrics(metrics, doctrine, deck_cards)

    # Output
    print("\n" + "="*80)
    print(f"TIER 3: GAMEPLAY VALIDATION REPORT")
    print(f"Civ: {verdict['civ']} ({civ_token})")
    print("="*80)

    for test_name, test_result in verdict["tests"].items():
        status = "✓ PASS" if test_result["passed"] else "✗ FAIL"
        print(f"\n{test_name}:")
        print(f"  Expected: {test_result['expected']}")
        print(f"  Actual:   {test_result['actual']}")
        print(f"  {status}")

    print("\n" + "="*80)
    if verdict["passed"]:
        print(f"✓ {verdict['civ']}: ALL TESTS PASSED")
    else:
        failed = [t for t, r in verdict["tests"].items() if not r["passed"]]
        print(f"✗ {verdict['civ']}: FAILED ({', '.join(failed)})")
    print("="*80)

    exit(0 if verdict["passed"] else 1)

if __name__ == "__main__":
    main()
