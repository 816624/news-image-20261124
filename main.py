#!/usr/bin/env python3
"""Write the 24 November 2026 world-news summary image to /output/entry.png.

The image is stored in this repository as entry.png.b64 (base64 of the PNG),
because the entry is assembled from text files only. Decoding is
deterministic: every run writes exactly the same bytes.

Validation (added in the round-2 revision): after decoding, the script
verifies the PNG before writing it out --
  * the IHDR chunk declares exactly 1024x1024 pixels,
  * the decoded payload is smaller than 1 MiB,
  * decoding the base64 text a second time yields byte-identical data
    (SHA-256 comparison),
  * the file written to /output hashes identically to the decoded bytes.
Any failed check aborts with a non-zero exit code and writes nothing.
"""
import base64
import hashlib
import os
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024
MAX_BYTES = 1 * 1024 * 1024  # 1 MiB


def read_png_dimensions(data: bytes) -> tuple[int, int]:
    """Return (width, height) from a PNG's IHDR chunk, verifying the signature."""
    png_signature = b"\x89PNG\r\n\x1a\n"
    if data[:8] != png_signature:
        raise ValueError("decoded data is not a PNG (bad signature)")
    # First chunk must be IHDR: 4-byte length, 4-byte type, 13-byte payload.
    length = struct.unpack(">I", data[8:12])[0]
    chunk_type = data[12:16]
    if chunk_type != b"IHDR" or length != 13:
        raise ValueError("first PNG chunk is not a 13-byte IHDR")
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def decode_and_validate(encoded: str) -> bytes:
    """Decode the base64 payload twice and validate the PNG thoroughly."""
    first = base64.b64decode(encoded, validate=True)
    second = base64.b64decode(encoded, validate=True)
    if hashlib.sha256(first).hexdigest() != hashlib.sha256(second).hexdigest():
        raise ValueError("two decodes of entry.png.b64 differ; not deterministic")
    if len(first) >= MAX_BYTES:
        raise ValueError(f"decoded PNG is {len(first)} bytes, must be < 1 MiB")
    width, height = read_png_dimensions(first)
    if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        raise ValueError(
            f"PNG is {width}x{height}, expected "
            f"{EXPECTED_WIDTH}x{EXPECTED_HEIGHT}"
        )
    return first


def main() -> None:
    encoded = (HERE / "entry.png.b64").read_text(encoding="ascii").strip()
    data = decode_and_validate(encoded)
    digest = hashlib.sha256(data).hexdigest()
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "entry.png"
    out_path.write_bytes(data)
    written = out_path.read_bytes()
    if hashlib.sha256(written).hexdigest() != digest:
        out_path.unlink(missing_ok=True)
        raise ValueError("written file hash does not match decoded bytes")
    print(f"entry.png: {len(data)} bytes, 1024x1024, sha256={digest}")
    print("validation passed: dimensions, size < 1MiB, deterministic decode, "
          "written-file hash match")


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        sys.exit(1)
