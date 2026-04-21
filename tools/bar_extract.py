#!/usr/bin/env python3
"""Extract files from AoE3 DE .bar archives.

Format (per Budschie/Resource-Manager, supporting v5-style entries which AoE3 DE v6 uses):

  Header (300 bytes for v>3):
    "ESPN" 4
    version uint32 (AoE3 DE = 6)
    unk1 uint32 (0x44332211)
    unk2 264 bytes
    checksum uint32
    num_files uint32
    if v>3: unk3 uint32 + files_table_offset int64
    else:   files_table_offset int32
    filename_hash uint32

  Files table (at files_table_offset):
    root_name_length uint32
    root_name utf16le (root_name_length * 2 bytes)
    num_root_files uint32
    entries[num_root_files]

  Entry (v>3, v5-like — AoE3 DE v6 also uses this):
    offset int64
    file_size int32                # decompressed size
    file_size2 int32               # on-disk size (compressed if isCompressed)
    file_size3 int32               # only when version >= 5
    LastWriteTime: 8 * int16 = 16 bytes
    name_length uint32
    name utf16le (name_length * 2 bytes)
    is_compressed uint32 (only v>3)
"""
import argparse
import os
import struct
import sys
from pathlib import Path


def parse_header(f):
    f.seek(0)
    espn = f.read(4)
    if espn != b"ESPN":
        raise RuntimeError(f"not an ESPN BAR (magic={espn!r})")
    version = struct.unpack("<I", f.read(4))[0]
    f.read(4)              # unk1 0x44332211
    f.read(264)            # unk2
    f.read(4)              # checksum
    num_files = struct.unpack("<I", f.read(4))[0]
    if version > 3:
        f.read(4)          # unk3
        table_offset = struct.unpack("<q", f.read(8))[0]
    else:
        table_offset = struct.unpack("<i", f.read(4))[0]
    f.read(4)              # filename hash
    return version, num_files, table_offset


def read_entries(f, version, table_offset):
    f.seek(table_offset)
    root_name_length = struct.unpack("<I", f.read(4))[0]
    root_name = f.read(root_name_length * 2).decode("utf-16-le", errors="replace")
    num_root_files = struct.unpack("<I", f.read(4))[0]

    entries = []
    # AoE3 DE v6 layout: offset(i64) + 3 sizes (i32) + name_length(u32) + name(utf16) + is_compressed(u32)
    # No LastWriteTime block (that exists in Budschie's v5 spec but AoE3 DE removed it).
    has_size3 = version >= 5
    is_v_gt3 = version > 3
    has_lwt = version <= 5

    for _ in range(num_root_files):
        if is_v_gt3:
            (offset,) = struct.unpack("<q", f.read(8))
        else:
            (offset,) = struct.unpack("<i", f.read(4))
        (file_size,)  = struct.unpack("<i", f.read(4))
        (file_size2,) = struct.unpack("<i", f.read(4))
        if has_size3:
            (file_size3,) = struct.unpack("<i", f.read(4))
        else:
            file_size3 = file_size
        if has_lwt:
            f.read(16)      # LastWriteTime (removed in v6)
        (name_length,) = struct.unpack("<I", f.read(4))
        if name_length == 0 or name_length > 4096:
            raise RuntimeError(f"bad name_length {name_length} at pos {f.tell()-4:#x}")
        name = f.read(name_length * 2).decode("utf-16-le", errors="replace")
        is_compressed = False
        if is_v_gt3:
            (ic,) = struct.unpack("<I", f.read(4))
            is_compressed = bool(ic)
        entries.append({
            "name": name,
            "offset": offset,
            "size": file_size,
            "size2": file_size2,
            "size3": file_size3,
            "compressed": is_compressed,
        })
    return root_name, entries


def maybe_decompress(data):
    """Handle ALZ4 / l33t compression. Returns raw bytes if not compressed or unsupported."""
    if data[:4] == b"alz4":
        try:
            import lz4.block
            uncompressed_size = struct.unpack("<I", data[4:8])[0]
            return lz4.block.decompress(data[16:], uncompressed_size=uncompressed_size)
        except Exception:
            return data
    if data[:4] == b"l33t":
        try:
            import zlib
            return zlib.decompress(data[8:])
        except Exception:
            return data
    if data[:4] == b"l66t":
        try:
            import zlib
            return zlib.decompress(data[12:])
        except Exception:
            return data
    return data


def extract(bar_path: Path, out_dir: Path, dry_run=False, name_filter=None, decompress=True):
    with bar_path.open("rb") as f:
        version, _hdr_count, table_offset = parse_header(f)
        root_name, entries = read_entries(f, version, table_offset)

        print(f"{bar_path.name}: v{version} files={len(entries)} table@{table_offset:#x} root={root_name!r}")
        if dry_run:
            sample = entries[:5] + (entries[-3:] if len(entries) > 8 else [])
            for e in sample:
                print(f"  {e['name']}: off={e['offset']} size={e['size']} size2={e['size2']} c={e['compressed']}")
            return entries

        written = 0
        for e in entries:
            name = e["name"].replace("\\", "/").lstrip("/")
            if name_filter and name_filter.lower() not in name.lower():
                continue
            target = out_dir / name
            target.parent.mkdir(parents=True, exist_ok=True)
            f.seek(e["offset"])
            data = f.read(e["size2"])
            if decompress:
                data = maybe_decompress(data)
            target.write_bytes(data)
            written += 1
        print(f"  wrote {written}/{len(entries)} entries to {out_dir}")
        return entries


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bar", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--filter", type=str, default=None,
                    help="case-insensitive substring; only matching names are extracted")
    ap.add_argument("--no-decompress", action="store_true")
    args = ap.parse_args()
    if args.out is None and not args.dry_run:
        ap.error("--out required unless --dry-run")
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
    extract(args.bar, args.out or Path("/tmp"), dry_run=args.dry_run,
            name_filter=args.filter, decompress=not args.no_decompress)


if __name__ == "__main__":
    main()
