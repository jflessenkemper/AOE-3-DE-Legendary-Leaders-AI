"""AoE3:DE BAR archive reader (format version 2/4/5/6).

Spec reverse-engineered from eBaeza/Resource-Manager (MIT) BarFile.cs +
BarFileHeader.cs + BarEntry.cs + alz4Utils.cs. Pure Python; payloads compressed
with the AoE3 'alz4' wrapper around an LZ4 block.
"""
from __future__ import annotations

import io
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

import lz4.block


_MAGIC = b"ESPN"
_ALZ4_MAGIC = b"alz4"
_HEADER_FIXED_SIZE = 4 + 4 + 4 + 264 + 4 + 4  # = 284 (through NumberOfFiles)


@dataclass
class BarEntry:
    offset: int
    size_compressed: int
    size_decompressed: int
    size_extra: int
    name: str
    is_compressed: bool

    @property
    def normalized_name(self) -> str:
        return self.name.replace("\\", "/").lower()


@dataclass
class BarArchive:
    path: Path
    version: int
    file_count: int
    files_table_offset: int
    root_path: str
    entries: list[BarEntry]

    def find(self, predicate) -> Iterator[BarEntry]:
        for e in self.entries:
            if predicate(e):
                yield e

    def read_payload(self, entry: BarEntry) -> bytes:
        with self.path.open("rb") as f:
            f.seek(entry.offset)
            blob = f.read(entry.size_compressed if entry.is_compressed
                          else entry.size_decompressed)
        if entry.is_compressed:
            return alz4_decompress(blob)
        return blob


def alz4_decompress(blob: bytes) -> bytes:
    if blob[:4] != _ALZ4_MAGIC:
        raise ValueError(f"alz4 magic missing: {blob[:4]!r}")
    uncompressed_size, compressed_size, _version = struct.unpack_from(
        "<iii", blob, 4)
    payload = blob[16:16 + compressed_size]
    return lz4.block.decompress(payload, uncompressed_size=uncompressed_size)


def open_bar(path: str | Path) -> BarArchive:
    path = Path(path)
    with path.open("rb") as f:
        head = f.read(_HEADER_FIXED_SIZE)
        if head[:4] != _MAGIC:
            raise ValueError(f"not a BAR (got {head[:4]!r})")
        version, unk1 = struct.unpack_from("<II", head, 4)
        if version not in (2, 4, 5, 6):
            raise ValueError(f"unsupported BAR version {version}")
        # bytes 12..275 = 264-byte Unk2 (zeros in practice)
        checksum, file_count = struct.unpack_from("<II", head, 12 + 264)

        if version > 3:
            unk3 = struct.unpack("<I", f.read(4))[0]
            files_table_offset = struct.unpack("<q", f.read(8))[0]
        else:
            unk3 = 0
            files_table_offset = struct.unpack("<i", f.read(4))[0]
        file_name_hash = struct.unpack("<I", f.read(4))[0]
        del unk1, unk3, checksum, file_name_hash  # not needed downstream

        f.seek(files_table_offset)
        root_len = struct.unpack("<I", f.read(4))[0]
        root_path = f.read(root_len * 2).decode("utf-16-le")
        num_root_files = struct.unpack("<I", f.read(4))[0]

        entries: list[BarEntry] = []
        for _ in range(num_root_files):
            if version > 3:
                offset = struct.unpack("<q", f.read(8))[0]
            else:
                offset = struct.unpack("<i", f.read(4))[0]
            size_compressed, size_decompressed = struct.unpack("<ii", f.read(8))
            size_extra = (struct.unpack("<i", f.read(4))[0]
                          if version >= 5 else size_decompressed)
            if version < 6:
                # 16-byte BarEntryLastWriteTime (8 * int16)
                f.read(16)
            name_len = struct.unpack("<I", f.read(4))[0]
            name = f.read(name_len * 2).decode("utf-16-le")
            is_compressed = bool(struct.unpack("<I", f.read(4))[0]) \
                if version > 3 else False
            entries.append(BarEntry(
                offset=offset,
                size_compressed=size_compressed,
                size_decompressed=size_decompressed,
                size_extra=size_extra,
                name=name,
                is_compressed=is_compressed,
            ))

    return BarArchive(
        path=path,
        version=version,
        file_count=num_root_files,
        files_table_offset=files_table_offset,
        root_path=root_path,
        entries=entries,
    )


# ── CLI ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    arc = open_bar(sys.argv[1])
    print(f"BAR v{arc.version}, root={arc.root_path!r}, "
          f"{arc.file_count} files, table@{arc.files_table_offset}")
    needle = sys.argv[2].lower() if len(sys.argv) > 2 else None
    for e in arc.entries:
        if needle and needle not in e.normalized_name:
            continue
        print(f"  {'C' if e.is_compressed else '-'} "
              f"{e.size_decompressed:>10}  {e.name}")
