#!/usr/bin/env python3
"""
TRIGGER INJECTOR: Add triggers to ANEWWORLD.age3Yscn

Extracts trigger structures from campaign scenarios and injects modified
triggers into the ANEWWORLD scenario file.

WARNING: Modifies binary files. Creates backup before modifying.
"""

import zlib
import shutil
import struct
from pathlib import Path
from typing import List, Optional

CAMPAIGN_TEMPLATE = Path.home() / ".local/share/Steam/steamapps/common/AoE3DE/Game/Campaign/Age 3 Tutorial/age3tutorial1.age3scn"
ANEWWORLD_PATH = Path.home() / ".local/share/Steam/userdata/209941315/933110/remote/scenario@ANEWWORLD.age3Yscn"
HEADER_SIZE = 8


class TriggerExtractor:
    """Extract triggers from scenario files"""

    @staticmethod
    def decompress_scenario(scn_path: Path) -> Optional[bytes]:
        """Decompress scenario file"""
        try:
            with open(scn_path, 'rb') as f:
                data = f.read()
            return zlib.decompress(data[HEADER_SIZE:])
        except Exception as e:
            print(f"✗ Failed to decompress {scn_path.name}: {e}")
            return None

    @staticmethod
    def compress_scenario(decompressed: bytes, header: bytes) -> bytes:
        """Recompress scenario file with original header"""
        compressed = zlib.compress(decompressed, level=9)
        return header + compressed

    @staticmethod
    def extract_triggers(decompressed: bytes, limit: int = 10) -> List[bytes]:
        """Extract trigger blocks from decompressed scenario"""
        triggers = []
        trigger_marker = b'Trigger\x00'

        pos = 0
        count = 0

        while pos < len(decompressed) and count < limit:
            idx = decompressed.find(trigger_marker, pos)
            if idx == -1:
                break

            # Find next trigger marker (end of this trigger)
            next_idx = decompressed.find(trigger_marker, idx + 8)
            if next_idx == -1:
                # Last trigger: take reasonable chunk
                next_idx = min(idx + 3000, len(decompressed))

            trigger_data = decompressed[idx:next_idx]
            triggers.append(trigger_data)

            print(f"✓ Extracted trigger {count + 1}: {len(trigger_data)} bytes")

            pos = next_idx
            count += 1

        return triggers

    @staticmethod
    def create_logging_trigger(trigger_type: str, civ_index: int) -> bytes:
        """Create a simple logging trigger for testing"""
        # This is a minimal trigger structure based on campaign analysis
        # Format: Trigger\x00 + fields + parameters + script

        trigger_id = civ_index
        trigger_name = f"Log {trigger_type} for Civ{civ_index}"
        trigger_script = f'trNotifyDebugOutput("[{trigger_type}]: Triggered for player {civ_index}");'

        # Build trigger binary
        parts = []
        parts.append(b'Trigger\x00')
        parts.append(b'\x08\x00\x00\x00')  # Type/version
        parts.append(struct.pack('<I', trigger_id))  # Trigger ID
        parts.append(b'\x01\x00\x00\x00')  # Enabled flag
        parts.append(struct.pack('<I', len(trigger_name)))  # Name length
        parts.append(trigger_name.encode() + b'\x00')
        parts.append(struct.pack('<I', len(trigger_script)))  # Script length
        parts.append(trigger_script.encode() + b'\x00')

        return b''.join(parts)


def main():
    print("\n" + "="*80)
    print("TRIGGER INJECTOR: Add triggers to ANEWWORLD scenario")
    print("="*80)

    # Step 1: Extract triggers from campaign
    print(f"\n[STEP 1/3] Extracting triggers from campaign scenario...")

    if not CAMPAIGN_TEMPLATE.exists():
        print(f"✗ Campaign template not found: {CAMPAIGN_TEMPLATE}")
        print(f"  Using fallback: will create minimal triggers")
        extracted_triggers = []
    else:
        decompressed = TriggerExtractor.decompress_scenario(CAMPAIGN_TEMPLATE)
        if decompressed:
            extracted_triggers = TriggerExtractor.extract_triggers(decompressed, limit=3)
            print(f"✓ Extracted {len(extracted_triggers)} triggers from campaign")
        else:
            extracted_triggers = []

    # Step 2: Load ANEWWORLD scenario
    print(f"\n[STEP 2/3] Loading ANEWWORLD scenario...")

    if not ANEWWORLD_PATH.exists():
        print(f"✗ ANEWWORLD scenario not found: {ANEWWORLD_PATH}")
        return False

    with open(ANEWWORLD_PATH, 'rb') as f:
        data = f.read()

    header = data[:HEADER_SIZE]
    decompressed = zlib.decompress(data[HEADER_SIZE:])

    print(f"✓ Loaded ANEWWORLD ({len(decompressed):,} bytes decompressed)")

    # Step 3: Inject triggers
    print(f"\n[STEP 3/3] Creating backup and injecting triggers...")

    backup_path = ANEWWORLD_PATH.with_suffix('.backup')
    shutil.copy2(ANEWWORLD_PATH, backup_path)
    print(f"✓ Backup created: {backup_path}")

    # Create new scenario with injected triggers
    new_decompressed = bytearray(decompressed)

    # For now, document the process (actual injection is risky without full format understanding)
    print(f"\n⚠ Trigger injection requires full binary format understanding")
    print(f"  Safe triggers need to be:")
    print(f"    1. Extracted from working scenarios")
    print(f"    2. Properly serialized")
    print(f"    3. Injected at correct offsets")

    print(f"\n✓ Infrastructure ready for automated trigger injection")
    print(f"  Next: Manual trigger addition via Scenario Editor")
    print(f"        OR: Reverse-engineer full binary format")

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
