#!/usr/bin/env python3
"""Write the 24 November 2026 world-news summary image to /output/entry.png.

The image is stored in this repository as entry.png.b64 (base64 of the PNG),
because the entry is assembled from text files only. Decoding is
deterministic: every run writes exactly the same bytes.
"""
import base64
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> None:
    encoded = (HERE / "entry.png.b64").read_text(encoding="ascii").strip()
    data = base64.b64decode(encoded, validate=True)
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "entry.png").write_bytes(data)


if __name__ == "__main__":
    main()
