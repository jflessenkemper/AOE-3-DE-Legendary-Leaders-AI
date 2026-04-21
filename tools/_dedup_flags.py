#!/usr/bin/env python3
"""Inspect AoE3 .bar header to determine format."""
import struct
import os
import sys

# Path is the standard Steam install path for AoE3DE on Linux.
BAR_PATH = os.environ.get('AOE3_BAR_PATH') or os.path.expanduser(
    '~/.local/share/Steam/steamapps/common/AoE3DE/Game/UI/UIResources1.bar'
)

with open(BAR_PATH, 'rb') as f:
    header = f.read(64)

print('First 64 bytes hex:', header.hex())
print('First 16 bytes ASCII:', repr(header[:16]))
print()
for i in range(0, 32, 4):
    val = struct.unpack('<I', header[i:i+4])[0]
    print(f'  bytes[{i}:{i+4}] = {header[i:i+4]!r} uint32(LE)={val}')

filesize = os.path.getsize(BAR_PATH)
print('File size:', filesize)

with open(BAR_PATH, 'rb') as f:
    f.seek(filesize - 128)
    tail = f.read(128)
print('Last 128 bytes hex:', tail.hex())
