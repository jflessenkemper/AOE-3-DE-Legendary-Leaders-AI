#!/usr/bin/env python3
"""
TIER 2: Scenario Binary Validation

Validates that:
1. ANEWWORLD.age3Yscn decompresses correctly
2. Contains 6 injected triggers with correct structure
3. Trigger names and scripts are properly encoded
4. File integrity is intact

This is a prerequisite to running in-game testing.
"""

import zlib
import struct
import re
import sys
from pathlib import Path
from typing import Optional, Tuple, List

REPO_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_PATH = Path.home() / ".local/share/Steam/userdata/209941315/933110/remote/scenario@ANEWWORLD.age3Yscn"

HEADER_SIZE = 8
EXPECTED_TRIGGERS = [
    {"id": 100, "label": "AgeUp", "script_contains": "trOutput"},
    {"id": 101, "label": "Units", "script_contains": "trOutput"},
    {"id": 102, "label": "Bldgs", "script_contains": "trOutput"},
    {"id": 103, "label": "Cards", "script_contains": "trOutput"},
    {"id": 104, "label": "Trade", "script_contains": "trOutput"},
    {"id": 105, "label": "End", "script_contains": "trOutput"},
]


class ScenarioValidator:
    """Validate ANEWWORLD scenario binary structure."""

    @staticmethod
    def decompress(path: Path) -> Optional[Tuple[bytes, bytes]]:
        """Decompress scenario. Returns (header, data)."""
        try:
            with open(path, 'rb') as f:
                data = f.read()
            header = data[:HEADER_SIZE]
            decompressed = zlib.decompress(data[HEADER_SIZE:])
            return header, decompressed
        except Exception as e:
            print(f"✗ Failed to decompress: {e}")
            return None

    @staticmethod
    def find_trigger_markers(data: bytes) -> List[int]:
        """Find all 'Trigger\x00' markers."""
        marker = b'Trigger\x00'
        positions = []
        offset = 0
        while True:
            pos = data.find(marker, offset)
            if pos == -1:
                break
            positions.append(pos)
            offset = pos + 1
        return positions

    @staticmethod
    def extract_trigger_block(data: bytes, start_pos: int, max_size: int = 3000) -> bytes:
        """Extract trigger block from start_pos."""
        marker = b'Trigger\x00'
        next_trigger = data.find(marker, start_pos + 8)

        if next_trigger == -1:
            end_pos = min(start_pos + max_size, len(data))
        else:
            end_pos = next_trigger

        return data[start_pos:end_pos]

    @staticmethod
    def find_strings_in_block(block: bytes) -> List[str]:
        """Extract readable UTF-8 strings from trigger block."""
        strings = []
        # Look for length-prefixed strings
        for offset in range(len(block) - 4):
            try:
                length = struct.unpack('<I', block[offset:offset+4])[0]
                if 1 <= length <= 500 and offset + 4 + length <= len(block):
                    string_bytes = block[offset+4:offset+4+length]
                    try:
                        string = string_bytes.decode('utf-8')
                        if string.endswith('\x00'):
                            string = string[:-1]
                            if len(string) > 2:  # Filter out noise
                                strings.append(string)
                    except:
                        pass
            except:
                pass
        return strings

    @staticmethod
    def validate_trigger_content(block: bytes, expected: dict) -> Tuple[bool, List[str]]:
        """Validate trigger contains expected label and script."""
        errors = []
        strings = ScenarioValidator.find_strings_in_block(block)

        # Check for expected label
        label_found = False
        for s in strings:
            if expected["label"] in s or expected["label"].lower() in s.lower():
                label_found = True
                break

        if not label_found:
            errors.append(f"Label '{expected['label']}' not found in trigger")

        # Check for script indicator
        script_found = False
        for s in strings:
            if expected["script_contains"] in s:
                script_found = True
                break

        if not script_found:
            errors.append(f"Script '{expected['script_contains']}' not found in trigger")

        return len(errors) == 0, errors


def main() -> int:
    print("\n" + "="*80)
    print("TIER 2: Scenario Binary Validation")
    print("="*80)

    # Step 1: File existence
    print(f"\n[1/4] Checking scenario file...")
    if not SCENARIO_PATH.exists():
        print(f"✗ Scenario not found: {SCENARIO_PATH}")
        return 1

    file_size = SCENARIO_PATH.stat().st_size
    print(f"✓ Found: {SCENARIO_PATH.name} ({file_size:,} bytes)")

    # Step 2: Decompression
    print(f"\n[2/4] Decompressing scenario...")
    result = ScenarioValidator.decompress(SCENARIO_PATH)
    if not result:
        return 1

    header, decompressed = result
    print(f"✓ Decompressed: {len(decompressed):,} bytes")
    print(f"  Header: {header.hex()}")

    # Step 3: Find triggers
    print(f"\n[3/4] Locating injected triggers...")
    trigger_positions = ScenarioValidator.find_trigger_markers(decompressed)
    print(f"✓ Found {len(trigger_positions)} 'Trigger' markers")

    if len(trigger_positions) < 6:
        print(f"⚠ Expected at least 6 trigger markers for injected triggers")
        print(f"  (This may be OK if original scenario had triggers)")

    # Step 4: Validate trigger content
    # Note: The first 6 triggers are from the original campaign scenario.
    # Our injected triggers start at position 7 (index 6).
    print(f"\n[4/4] Validating trigger content...")
    print(f"  Original scenario has ~6 triggers, injected triggers at positions 7-12")

    validated_count = 0
    injected_start_idx = 6  # 0-indexed, so position 7

    for expected_idx, expected in enumerate(EXPECTED_TRIGGERS, 1):
        trigger_marker_idx = injected_start_idx + expected_idx - 1

        if trigger_marker_idx >= len(trigger_positions):
            print(f"✗ Injected trigger {expected_idx} ({expected['label']}): Marker not found at position {trigger_marker_idx}")
            continue

        pos = trigger_positions[trigger_marker_idx]
        block = ScenarioValidator.extract_trigger_block(decompressed, pos)
        strings = ScenarioValidator.find_strings_in_block(block)

        success, errors = ScenarioValidator.validate_trigger_content(block, expected)

        if success:
            print(f"✓ Injected trigger {expected_idx} ({expected['label']}): Valid")
            validated_count += 1
        else:
            print(f"✗ Injected trigger {expected_idx} ({expected['label']}):")
            for e in errors:
                print(f"    - {e}")
            if strings and expected_idx <= 3:  # Debug first 3
                print(f"    Found strings (first 3): {strings[:3]}")

    # Summary
    print(f"\n" + "="*80)
    print(f"TIER 2 Validation Summary")
    print(f"="*80)
    print(f"File integrity: ✓")
    print(f"Decompression: ✓")
    print(f"Trigger markers: {len(trigger_positions)} found")
    print(f"Trigger content: {validated_count}/{len(EXPECTED_TRIGGERS)} valid")

    if validated_count == len(EXPECTED_TRIGGERS):
        print(f"\n✓ TIER 2 PASSED — Scenario ready for in-game testing")
        return 0
    else:
        print(f"\n⚠ TIER 2 PARTIAL — Some triggers missing or invalid")
        return 1


if __name__ == "__main__":
    sys.exit(main())
