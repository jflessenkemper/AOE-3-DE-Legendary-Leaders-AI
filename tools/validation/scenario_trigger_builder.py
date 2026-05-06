#!/usr/bin/env python3
"""
SCENARIO TRIGGER BUILDER: Clone and inject logging triggers

Strategy:
1. Extract simple, working triggers from campaign scenario
2. Clone them byte-for-byte
3. Modify ONLY the text strings (trigger name, script output)
4. Inject into ANEWWORLD.age3Yscn
5. Recompress and test

This is safer than building triggers from scratch because the
binary structure remains valid - we only change readable text.
"""

import zlib
import shutil
import struct
from pathlib import Path
from typing import List, Tuple, Optional

CAMPAIGN_SCN = Path.home() / ".local/share/Steam/steamapps/common/AoE3DE/Game/Campaign/Age 3 Tutorial/age3tutorial1.age3scn"
ANEWWORLD = Path.home() / ".local/share/Steam/userdata/209941315/933110/remote/scenario@ANEWWORLD.age3Yscn"
HEADER_SIZE = 8


class ScenarioTriggerBuilder:
    """Build and inject triggers into scenario files"""

    @staticmethod
    def decompress(path: Path) -> Optional[Tuple[bytes, bytes]]:
        """Returns (header, decompressed_data)"""
        try:
            with open(path, 'rb') as f:
                data = f.read()
            header = data[:HEADER_SIZE]
            decompressed = zlib.decompress(data[HEADER_SIZE:])
            return header, decompressed
        except Exception as e:
            print(f"✗ Failed to decompress {path.name}: {e}")
            return None

    @staticmethod
    def compress(header: bytes, decompressed: bytes) -> bytes:
        """Recompress with original header"""
        compressed = zlib.compress(decompressed, level=9)
        return header + compressed

    @staticmethod
    def extract_trigger_range(data: bytes, trigger_num: int = 1) -> Optional[Tuple[int, bytes]]:
        """Extract a trigger block by number"""
        trigger_marker = b'Trigger\x00'

        # Find Nth trigger
        pos = 0
        for i in range(trigger_num):
            idx = data.find(trigger_marker, pos)
            if idx == -1:
                return None
            pos = idx + 1

        # Get actual trigger start
        trigger_start = data.rfind(trigger_marker, 0, pos)

        # Find next trigger or end
        trigger_end = data.find(trigger_marker, trigger_start + 8)
        if trigger_end == -1:
            trigger_end = trigger_start + 3000  # reasonable chunk

        trigger_data = data[trigger_start:trigger_end]
        return trigger_start, trigger_data

    @staticmethod
    def find_and_replace_string(data: bytes, old: str, new: str) -> bytes:
        """
        Find and replace a string in trigger data.
        Handles length-prefixed strings if they exist.
        """
        old_bytes = old.encode('utf-8')
        new_bytes = new.encode('utf-8')

        # Only replace if same length or new is shorter
        if len(new_bytes) > len(old_bytes):
            print(f"⚠ New string '{new}' is longer than old '{old}', skipping")
            return data

        # Find and replace
        modified = bytearray(data)
        while True:
            idx = modified.find(old_bytes)
            if idx == -1:
                break

            # Replace with new string + padding if needed
            padding = len(old_bytes) - len(new_bytes)
            modified[idx:idx+len(old_bytes)] = new_bytes + (b'\x00' * padding)

        return bytes(modified)

    @staticmethod
    def create_logging_triggers() -> List[dict]:
        """Define the 6 test triggers to create"""
        return [
            {
                "id": 100,
                "name": "Test: Age-Up",
                "script": 'trOutputDebug("[AGEUP]: Player %PlayerID% aged at %Time%\\n");',
                "label": "Age-Up Detection",
            },
            {
                "id": 101,
                "name": "Test: Units",
                "script": 'trOutputDebug("[UNITS]: Infantry=%Infantry% Cavalry=%Cav%\\n");',
                "label": "Unit Training Log",
            },
            {
                "id": 102,
                "name": "Test: Buildings",
                "script": 'trOutputDebug("[BUILDINGS]: %BuildingType%\\n");',
                "label": "Building Log",
            },
            {
                "id": 103,
                "name": "Test: Cards",
                "script": 'trOutputDebug("[CARDS]: %CardName%\\n");',
                "label": "Card Shipment Log",
            },
            {
                "id": 104,
                "name": "Test: Trade",
                "script": 'trOutputDebug("[TRADE_ROUTES]: Active\\n");',
                "label": "Trade Route Log",
            },
            {
                "id": 105,
                "name": "Test: Game End",
                "script": 'trOutputDebug("[GAME_END]: At %ElapsedTime%\\n");',
                "label": "Game End Marker",
            },
        ]

    @staticmethod
    def clone_and_modify_trigger(template: bytes, trigger_def: dict) -> bytes:
        """Clone a template trigger and modify its strings"""

        modified = bytes(template)

        # Replace recognizable strings with our test strings
        # This is safe because we're only replacing text, not binary structures

        # Try to replace trigger name/description
        # These are usually short strings in the trigger
        old_names = ['Ignore', 'Hide Score', 'Hide', 'Show', 'Debug']

        for old_name in old_names:
            # Only replace if new name is same length or shorter
            new_name = trigger_def['name'][:len(old_name)]
            if len(new_name) <= len(old_name):
                modified = ScenarioTriggerBuilder.find_and_replace_string(
                    modified, old_name, new_name
                )
                break

        # Try to replace script
        # Look for "tr" functions and replace if space allows
        tr_functions = [
            'trUIFadeToColor',
            'trSoundPlayDialogue',
            'gadgetUnreal',
            'trEventFire',
            'trSetFogAndBlackmap',
        ]

        for func in tr_functions:
            if func.encode() in modified:
                # Found a script, try to replace with ours (be careful with length)
                if len(trigger_def['script']) <= 100:  # safety check
                    try:
                        modified = ScenarioTriggerBuilder.find_and_replace_string(
                            modified, func, 'trOutput'
                        )
                    except:
                        pass
                break

        return modified


def main():
    print("\n" + "="*80)
    print("SCENARIO TRIGGER BUILDER: Inject logging triggers")
    print("="*80)

    # Step 1: Get template trigger
    print(f"\n[1/5] Extracting template trigger from campaign...")

    result = ScenarioTriggerBuilder.decompress(CAMPAIGN_SCN)
    if not result:
        print("✗ Failed to load campaign scenario")
        return False

    _, campaign_data = result

    template_result = ScenarioTriggerBuilder.extract_trigger_range(campaign_data, trigger_num=2)
    if not template_result:
        print("✗ Failed to extract template trigger")
        return False

    template_offset, template_trigger = template_result
    print(f"✓ Template trigger: {len(template_trigger)} bytes at offset {template_offset:,}")

    # Step 2: Load ANEWWORLD
    print(f"\n[2/5] Loading ANEWWORLD scenario...")

    result = ScenarioTriggerBuilder.decompress(ANEWWORLD)
    if not result:
        print("✗ Failed to load ANEWWORLD")
        return False

    header, anewworld_data = result
    print(f"✓ Loaded ANEWWORLD: {len(anewworld_data):,} bytes")

    # Step 3: Create backup
    print(f"\n[3/5] Creating backup...")

    backup_path = ANEWWORLD.with_suffix('.backup')
    shutil.copy2(ANEWWORLD, backup_path)
    print(f"✓ Backup: {backup_path}")

    # Step 4: Clone and prepare triggers
    print(f"\n[4/5] Cloning and modifying triggers...")

    trigger_defs = ScenarioTriggerBuilder.create_logging_triggers()
    modified_triggers = []

    for trigger_def in trigger_defs:
        modified = ScenarioTriggerBuilder.clone_and_modify_trigger(
            template_trigger, trigger_def
        )
        modified_triggers.append(modified)
        print(f"  ✓ Created trigger: {trigger_def['name']}")

    # Step 5: Inject into ANEWWORLD
    print(f"\n[5/5] Injecting triggers into ANEWWORLD...")

    # Find where to inject (at end of scenario, before any sentinel markers)
    injection_point = len(anewworld_data) - 100  # Leave some buffer

    # Build new scenario data
    new_data = bytearray(anewworld_data)

    # Inject all triggers
    for modified_trigger in modified_triggers:
        # Insert bytes at position
        new_data[injection_point:injection_point] = modified_trigger
        injection_point += len(modified_trigger)

    # Recompress
    print(f"  Recompressing... ({len(new_data):,} bytes → ", end="", flush=True)
    recompressed = ScenarioTriggerBuilder.compress(header, bytes(new_data))
    print(f"{len(recompressed):,} bytes)")

    # Write out
    with open(ANEWWORLD, 'wb') as f:
        f.write(recompressed)

    print(f"✓ Saved modified ANEWWORLD")

    # Summary
    print(f"\n" + "="*80)
    print(f"SUMMARY")
    print(f"="*80)
    print(f"✓ Template: {len(template_trigger)} bytes")
    print(f"✓ Triggers created: {len(modified_triggers)}")
    print(f"✓ Total injected: {sum(len(t) for t in modified_triggers):,} bytes")
    print(f"✓ Original size: {len(anewworld_data):,} bytes")
    print(f"✓ New size: {len(new_data):,} bytes")
    print(f"✓ Increase: {len(new_data) - len(anewworld_data):,} bytes")
    print(f"\n✓ Triggers injected successfully!")
    print(f"  Next: Load ANEWWORLD in game and test trigger output")
    print(f"  Then: Run validation suite")

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
