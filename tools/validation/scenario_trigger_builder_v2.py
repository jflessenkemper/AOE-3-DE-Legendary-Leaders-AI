#!/usr/bin/env python3
"""
SCENARIO TRIGGER BUILDER V2: Proper length-prefixed string handling

Now with correct encoding for:
- Length-prefixed strings: [4-byte LE length] + [UTF-8 string] + [null]
- Dynamic string replacement with proper length updates
- Safe padding when strings change size
"""

import zlib
import shutil
import struct
from pathlib import Path
from typing import List, Tuple, Optional

CAMPAIGN_SCN = Path.home() / ".local/share/Steam/steamapps/common/AoE3DE/Game/Campaign/Age 3 Tutorial/age3tutorial1.age3scn"
ANEWWORLD = Path.home() / ".local/share/Steam/userdata/209941315/933110/remote/scenario@ANEWWORLD.age3Yscn"
ANEWWORLD_BACKUP = ANEWWORLD.with_suffix('.backup_pre_v2')
HEADER_SIZE = 8


class LengthPrefixedString:
    """Handle length-prefixed string encoding/decoding"""

    @staticmethod
    def encode(text: str) -> bytes:
        """Encode string as: [4-byte LE length] + [UTF-8 string] + [null]"""
        utf8_bytes = text.encode('utf-8')
        length = len(utf8_bytes) + 1  # +1 for null terminator
        length_bytes = struct.pack('<I', length)
        return length_bytes + utf8_bytes + b'\x00'

    @staticmethod
    def decode_at(data: bytes, offset: int) -> Optional[Tuple[str, int]]:
        """
        Decode string at offset.
        Returns: (string, total_bytes_consumed) or None if invalid
        """
        if offset + 4 > len(data):
            return None

        length = struct.unpack('<I', data[offset:offset+4])[0]

        # Safety checks
        if length < 1 or length > 1000 or offset + 4 + length > len(data):
            return None

        string_bytes = data[offset+4:offset+4+length]

        try:
            string = string_bytes.decode('utf-8')
            # Should end with null
            if string[-1] == '\x00':
                return string[:-1], 4 + length
            else:
                return None
        except:
            return None


class ScenarioTriggerBuilderV2:
    """Build and inject triggers with proper string encoding"""

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

        pos = 0
        for i in range(trigger_num):
            idx = data.find(trigger_marker, pos)
            if idx == -1:
                return None
            pos = idx + 1

        trigger_start = data.rfind(trigger_marker, 0, pos)
        trigger_end = data.find(trigger_marker, trigger_start + 8)
        if trigger_end == -1:
            trigger_end = trigger_start + 3000

        trigger_data = data[trigger_start:trigger_end]
        return trigger_start, trigger_data

    @staticmethod
    def find_and_replace_length_prefixed(
        data: bytes, old_string: str, new_string: str
    ) -> bytes:
        """
        Find and replace a length-prefixed string.
        Handles encoding changes properly.
        """
        modified = bytearray(data)

        # Find all length-prefixed strings
        offset = 0
        while offset < len(modified) - 5:
            result = LengthPrefixedString.decode_at(bytes(modified), offset)

            if result:
                decoded_string, consumed_bytes = result

                if decoded_string == old_string:
                    # Found it! Replace with new string
                    old_encoded = LengthPrefixedString.encode(old_string)
                    new_encoded = LengthPrefixedString.encode(new_string)

                    # Replace in modified data
                    if len(new_encoded) == len(old_encoded):
                        # Same length, simple replacement
                        modified[offset:offset+len(old_encoded)] = new_encoded
                    elif len(new_encoded) < len(old_encoded):
                        # New string is shorter, replace and pad
                        modified[offset:offset+len(new_encoded)] = new_encoded
                        # Zero-pad the rest
                        padding = len(old_encoded) - len(new_encoded)
                        for i in range(padding):
                            modified[offset+len(new_encoded)+i] = 0
                    else:
                        # New string is longer - risky, only do if space available
                        if offset + len(new_encoded) < len(modified):
                            # Shift data if needed (expensive)
                            # For now, only replace if same length
                            print(f"⚠ Cannot safely expand '{old_string}' → '{new_string}'")
                            offset += consumed_bytes
                            continue

                    return bytes(modified)

                offset += consumed_bytes
            else:
                offset += 1

        return data

    @staticmethod
    def clone_and_modify_trigger(template: bytes, trigger_def: dict) -> bytes:
        """Clone a template trigger and modify strings properly"""

        modified = bytes(template)

        # Strategy: Replace specific known strings with safe lengths

        # 1. Replace "Ignore" (7 bytes) with trigger label (pad to 7)
        label = trigger_def['label'][:6]  # Truncate to fit in 7 bytes with null
        modified = ScenarioTriggerBuilderV2.find_and_replace_length_prefixed(
            modified, 'Ignore', label
        )

        # 2. Replace script function
        # Look for the long script and replace carefully
        old_script = 'trSoundPlayDialogue("%StringID%", %EventID%, %Ignore%, %Seconds%);'
        new_script = trigger_def['script']

        if len(new_script) <= len(old_script):
            modified = ScenarioTriggerBuilderV2.find_and_replace_length_prefixed(
                modified, old_script, new_script
            )

        return modified


def main():
    print("\n" + "="*80)
    print("SCENARIO TRIGGER BUILDER V2: Proper Length-Prefixed Encoding")
    print("="*80)

    # Step 1: Get template trigger
    print(f"\n[1/5] Extracting template trigger from campaign...")

    result = ScenarioTriggerBuilderV2.decompress(CAMPAIGN_SCN)
    if not result:
        print("✗ Failed to load campaign scenario")
        return False

    _, campaign_data = result

    template_result = ScenarioTriggerBuilderV2.extract_trigger_range(campaign_data, trigger_num=2)
    if not template_result:
        print("✗ Failed to extract template trigger")
        return False

    template_offset, template_trigger = template_result
    print(f"✓ Template trigger: {len(template_trigger)} bytes at offset {template_offset:,}")

    # Step 2: Load ANEWWORLD (from backup, not modified v1)
    print(f"\n[2/5] Loading ANEWWORLD scenario...")

    # Try to use the backup from v1 if it exists
    load_path = ANEWWORLD_BACKUP if ANEWWORLD_BACKUP.exists() else ANEWWORLD

    result = ScenarioTriggerBuilderV2.decompress(load_path)
    if not result:
        print("✗ Failed to load ANEWWORLD")
        return False

    header, anewworld_data = result
    print(f"✓ Loaded ANEWWORLD: {len(anewworld_data):,} bytes")

    # Step 3: Create backup of current state
    print(f"\n[3/5] Creating backup...")

    backup_path = ANEWWORLD_BACKUP
    shutil.copy2(load_path, backup_path)
    print(f"✓ Backup: {backup_path}")

    # Step 4: Clone and prepare triggers
    print(f"\n[4/5] Cloning and modifying triggers with proper encoding...")

    trigger_defs = [
        {
            "id": 100,
            "label": "AgeUp",
            "script": 'trOutput("[AGEUP]\\n");',
        },
        {
            "id": 101,
            "label": "Units",
            "script": 'trOutput("[UNITS]\\n");',
        },
        {
            "id": 102,
            "label": "Bldgs",
            "script": 'trOutput("[BLDGS]\\n");',
        },
        {
            "id": 103,
            "label": "Cards",
            "script": 'trOutput("[CARDS]\\n");',
        },
        {
            "id": 104,
            "label": "Trade",
            "script": 'trOutput("[TRADE]\\n");',
        },
        {
            "id": 105,
            "label": "End",
            "script": 'trOutput("[DONE]\\n");',
        },
    ]

    modified_triggers = []

    for trigger_def in trigger_defs:
        modified = ScenarioTriggerBuilderV2.clone_and_modify_trigger(
            template_trigger, trigger_def
        )
        modified_triggers.append(modified)
        print(f"  ✓ Created trigger: {trigger_def['label']}")

    # Step 5: Inject into ANEWWORLD
    print(f"\n[5/5] Injecting triggers into ANEWWORLD...")

    injection_point = len(anewworld_data) - 100
    new_data = bytearray(anewworld_data)

    for modified_trigger in modified_triggers:
        new_data[injection_point:injection_point] = modified_trigger
        injection_point += len(modified_trigger)

    # Recompress
    print(f"  Recompressing... ({len(new_data):,} bytes → ", end="", flush=True)
    recompressed = ScenarioTriggerBuilderV2.compress(header, bytes(new_data))
    print(f"{len(recompressed):,} bytes)")

    # Write out
    with open(ANEWWORLD, 'wb') as f:
        f.write(recompressed)

    print(f"✓ Saved modified ANEWWORLD")

    # Verify
    print(f"\n[VERIFY] Checking modified file...")
    result = ScenarioTriggerBuilderV2.decompress(ANEWWORLD)
    if result:
        _, verify_data = result
        text = verify_data.decode('utf-8', errors='ignore')

        # Check for our labels
        found_count = 0
        for label in ['AgeUp', 'Units', 'Bldgs', 'Cards', 'Trade', 'End']:
            if label in text:
                print(f"  ✓ Found label: {label}")
                found_count += 1

        print(f"\n✓ {found_count}/6 trigger labels found in output")

    # Summary
    print(f"\n" + "="*80)
    print(f"SUMMARY")
    print(f"="*80)
    print(f"✓ Template: {len(template_trigger)} bytes")
    print(f"✓ Triggers created: {len(modified_triggers)}")
    print(f"✓ Total injected: {sum(len(t) for t in modified_triggers):,} bytes")
    print(f"✓ Original size: {len(anewworld_data):,} bytes")
    print(f"✓ New size: {len(new_data):,} bytes")
    print(f"\n✓ V2 Triggers injected with proper encoding!")

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
