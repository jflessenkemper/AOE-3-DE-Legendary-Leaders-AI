"""AoE3:DE XMB binary XML reader (version 8).

Spec from eBaeza/Resource-Manager XmbFile.cs (MIT). Outer wrapper is either
Alz4 or L33T-zip; the inner stream begins with 'X1'. We only support the
direct (already-decompressed) XMB body — callers feed us the inner stream.
"""
from __future__ import annotations

import io
import struct
import xml.etree.ElementTree as ET


def _read_u8(b: io.BufferedReader) -> int:
    return struct.unpack("<B", b.read(1))[0]


def _read_i32(b: io.BufferedReader) -> int:
    return struct.unpack("<i", b.read(4))[0]


def _read_u32(b: io.BufferedReader) -> int:
    return struct.unpack("<I", b.read(4))[0]


def _read_u16le_str(b: io.BufferedReader, char_count: int) -> str:
    return b.read(char_count * 2).decode("utf-16-le")


def parse_xmb(data: bytes) -> ET.Element:
    """Decode an XMB byte stream to an ElementTree root element."""
    b = io.BytesIO(data)
    if b.read(2) != b"X1":
        raise ValueError("XMB: missing X1 magic")
    _data_length = _read_u32(b)
    if b.read(2) != b"XR":
        raise ValueError("XMB: missing XR marker")
    unknown2 = _read_u32(b)
    version = _read_u32(b)
    if unknown2 != 4:
        raise ValueError(f"XMB: expected unknown2=4, got {unknown2}")
    if version != 8:
        raise ValueError(f"XMB: expected version=8, got {version}")

    n_elements = _read_u32(b)
    elements = [_read_u16le_str(b, _read_i32(b)) for _ in range(n_elements)]
    n_attrs = _read_u32(b)
    attrs = [_read_u16le_str(b, _read_i32(b)) for _ in range(n_attrs)]

    return _read_node(b, elements, attrs)


def _read_node(b: io.BufferedReader, elements: list[str],
               attrs: list[str]) -> ET.Element:
    if b.read(2) != b"XN":
        raise ValueError("XMB: missing XN node header")
    _length = _read_i32(b)
    inner_len = _read_i32(b)
    inner_text = _read_u16le_str(b, inner_len) if inner_len else ""
    name_id = _read_i32(b)
    _line_no = _read_i32(b)

    node = ET.Element(elements[name_id])
    if inner_text:
        node.text = inner_text

    n_attrs = _read_i32(b)
    for _ in range(n_attrs):
        attr_id = _read_i32(b)
        attr_len = _read_i32(b)
        attr_val = _read_u16le_str(b, attr_len) if attr_len else ""
        node.set(attrs[attr_id], attr_val)

    n_children = _read_i32(b)
    for _ in range(n_children):
        node.append(_read_node(b, elements, attrs))

    return node


# ── CLI ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    from bar import open_bar
    arc = open_bar(sys.argv[1])
    pat = sys.argv[2].lower()
    matches = [e for e in arc.entries if pat in e.normalized_name]
    if not matches:
        sys.exit(f"no entries match {pat!r}")
    e = matches[0]
    print(f"loading {e.name} ({e.size_decompressed} bytes uncompressed)")
    raw = arc.read_payload(e)
    if raw[:2] == b"X1":
        root = parse_xmb(raw)
        print(f"  root: <{root.tag}> with {len(root)} children")
        # show first few attrs of first 3 children
        for child in list(root)[:3]:
            print(f"    <{child.tag} {dict(child.attrib)}>")
    else:
        print(f"  not XMB (first 4 bytes: {raw[:4]!r})")
