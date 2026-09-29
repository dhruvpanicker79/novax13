"""Render PDF pages to PNG and dump their text, so slides can be inspected.

Windows has no poppler here and the Read tool cannot rasterise, so rendering
happens in WSL via PyMuPDF and the images are written where the Windows side
can pick them up.

    python scripts/pdf_pages.py <pdf> <out_dir> [first] [last] [dpi]
"""
from __future__ import annotations

import os
import sys

import fitz


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    src, out = sys.argv[1], sys.argv[2]
    first = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    last = int(sys.argv[4]) if len(sys.argv) > 4 else 0
    dpi = int(sys.argv[5]) if len(sys.argv) > 5 else 110

    os.makedirs(out, exist_ok=True)
    doc = fitz.open(src)
    n = doc.page_count
    last = min(last or n, n)
    print(f"{os.path.basename(src)}: {n} pages, rendering {first}-{last} @ {dpi}dpi")

    for i in range(first - 1, last):
        page = doc[i]
        pix = page.get_pixmap(dpi=dpi)
        p = os.path.join(out, f"p{i + 1:02d}.png")
        pix.save(p)
        txt = page.get_text().strip()
        print(f"\n===== PAGE {i + 1} =====  ({pix.width}x{pix.height}px, "
              f"{len(txt)} chars text)")
        if txt:
            print(txt[:1800])
    return 0


if __name__ == "__main__":
    sys.exit(main())
