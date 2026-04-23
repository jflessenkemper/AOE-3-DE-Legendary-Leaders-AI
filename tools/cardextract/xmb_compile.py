"""Compile plain XML to AoE3:DE XMB binary format (version 8).

Inverse of xmb.py parser. Mod filesystem XML files at paths matching
base-game packed XMB files do NOT override them (verified empirically on
2026-04-22 — mod `data/homecitybritish.xml` was ignored while base game
`Data/homecitybritish.xml.XMB` (packed inside Data.bar) was read). To make
mod overrides take effect for base-civ homecity data, we must ship our
files as .XMB at `data/homecitybritish.xml.XMB` in the mod.

Format (from xmb.py parser, MIT-licensed spec by eBaeza):
  X1 magic | data_length u32 | XR | unknown2=4 | version=8
  n_elements u32 | elements: [i32 char_count + UTF-16LE string] each
  n_attrs u32 | attrs: same
  root node:
    XN | length i32 | inner_len i32 | inner_text UTF-16LE
    name_id i32 | line_no i32
    n_attrs i32 | [(attr_id i32, attr_len i32, attr_val UTF-16LE)...]
    n_children i32 | [child_node...]

Usage:
  python3 tools/cardextract/xmb_compile.py input.xml output.xml.XMB
"""
from __future__ import annotations

import io
import struct
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def _utf16le(s: str) -> bytes:
    return s.encode("utf-16-le")


def _pack_u16str(s: str) -> bytes:
    data = _utf16le(s)
    # char_count is i32 (number of UTF-16 code units = len(data) // 2)
    char_count = len(data) // 2
    return struct.pack("<i", char_count) + data


def _collect_names(root: ET.Element) -> tuple[list[str], list[str]]:
    """Walk the tree and return (element_names, attr_names) in first-seen order."""
    elements: list[str] = []
    attrs: list[str] = []
    e_seen: set[str] = set()
    a_seen: set[str] = set()

    def visit(node: ET.Element):
        if node.tag not in e_seen:
            e_seen.add(node.tag)
            elements.append(node.tag)
        for k in node.attrib.keys():
            if k not in a_seen:
                a_seen.add(k)
                attrs.append(k)
        for child in node:
            visit(child)

    visit(root)
    return elements, attrs


def _write_node(buf: io.BytesIO, node: ET.Element,
                elem_idx: dict[str, int], attr_idx: dict[str, int]):
    # Write to a temp buffer so we can compute length
    inner = io.BytesIO()

    # XN magic
    inner.write(b"XN")
    # We'll patch in total node byte-length + inner-text-len later; build body first
    body = io.BytesIO()

    text = node.text or ""
    # Strip whitespace-only text that's just indentation (common in hand-edited XML)
    if text.strip() == "":
        text = ""

    inner_len = len(_utf16le(text)) // 2
    body.write(struct.pack("<i", inner_len))
    body.write(_utf16le(text))

    body.write(struct.pack("<i", elem_idx[node.tag]))
    body.write(struct.pack("<i", 0))  # line_no — 0 is fine at runtime

    body.write(struct.pack("<i", len(node.attrib)))
    for k, v in node.attrib.items():
        body.write(struct.pack("<i", attr_idx[k]))
        val_len = len(_utf16le(v)) // 2
        body.write(struct.pack("<i", val_len))
        body.write(_utf16le(v))

    # children
    body.write(struct.pack("<i", len(list(node))))
    for child in node:
        # Recursively write each child into `body`
        _write_node(body, child, elem_idx, attr_idx)

    # Compose node: XN + length(i32) + body
    # `length` is bytes AFTER the length field itself (i.e., = len(body_bytes)).
    # Verified by reading base game XMB: root node length field value equals
    # (total_bytes_after_length_field) = (file_size - 6_byte_node_header).
    body_bytes = body.getvalue()
    length = len(body_bytes)
    inner.write(struct.pack("<i", length))
    inner.write(body_bytes)

    buf.write(inner.getvalue())


def compile_xmb(root: ET.Element) -> bytes:
    elements, attrs = _collect_names(root)
    elem_idx = {n: i for i, n in enumerate(elements)}
    attr_idx = {n: i for i, n in enumerate(attrs)}

    # Build header + tables + root node body (into a temp buf), then prefix length.
    tbl = io.BytesIO()
    tbl.write(b"XR")
    tbl.write(struct.pack("<I", 4))  # unknown2
    tbl.write(struct.pack("<I", 8))  # version

    tbl.write(struct.pack("<I", len(elements)))
    for name in elements:
        tbl.write(_pack_u16str(name))

    tbl.write(struct.pack("<I", len(attrs)))
    for name in attrs:
        tbl.write(_pack_u16str(name))

    node_buf = io.BytesIO()
    _write_node(node_buf, root, elem_idx, attr_idx)
    tbl.write(node_buf.getvalue())

    tbl_bytes = tbl.getvalue()

    out = io.BytesIO()
    out.write(b"X1")
    # data_length: byte count of everything after X1+length field
    out.write(struct.pack("<I", len(tbl_bytes)))
    out.write(tbl_bytes)
    return out.getvalue()


def main():
    ap_src = Path(sys.argv[1])
    ap_dst = Path(sys.argv[2])
    tree = ET.parse(ap_src)
    root = tree.getroot()
    data = compile_xmb(root)
    ap_dst.write_bytes(data)
    print(f"compiled {ap_src} → {ap_dst} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
