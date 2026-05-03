"""Build multi-page research website from Skeleton.ipynb.

Usage:
    python scripts/build_skeleton_site.py

After editing the notebook, run this script to regenerate all HTML pages
in docs/. Then commit and push to update the GitHub Pages site.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = ROOT / "Skeleton.ipynb"
OUTPUT_DIR = ROOT / "docs"
IMAGES_SRC = ROOT / "demos_images"
IMAGES_DST = OUTPUT_DIR / "images"

# ── Page definitions ──
# Each page is defined by a regex that matches the H1 heading that starts it.
# All cells from that H1 until the next H1 (or EOF) are included.
# The "title" is the display title shown in the rendered page.

PAGES = [
    {
        "id": "data-cleaning",
        "file": "data-cleaning.html",
        "title": "Chemical Data Cleaning",
        "heading_pattern": r"^#\s+Summary of Chemical Data Cleaning",
    },
    {
        "id": "data-preparation",
        "file": "data-preparation.html",
        "title": "Data Preparation",
        "heading_pattern": r"^#\s+.*Data Preparation|^#\s+Done in Data Preparation",
    },
    {
        "id": "workflow",
        "file": "workflow.html",
        "title": "Workflow Framework",
        "heading_pattern": r"^#\s+Workflow Template|^#\s+Tool:\s*Recursive",
    },
    {
        "id": "chapter2",
        "file": "chapter2.html",
        "title": "Chapter 2: Pollution Assessment",
        "heading_pattern": r"^#\s+Chapter 2",
    },
    {
        "id": "chapter3",
        "file": "chapter3.html",
        "title": "Chapter 3: Environmental Standardization",
        "heading_pattern": r"^#\s+Chapter 3",
    },
]


def _normalize_source(source: object) -> str:
    if isinstance(source, list):
        return "".join(str(s) for s in source).rstrip()
    return str(source).rstrip()


def _load_cells(notebook_path: Path) -> list[dict]:
    nb = json.loads(notebook_path.read_text(encoding="utf-8"))
    cells = []
    for cell in nb.get("cells", []):
        src = _normalize_source(cell.get("source", []))
        ctype = str(cell.get("cell_type", "")).strip().lower()
        if ctype not in ("markdown", "code"):
            continue
        cells.append({"cell_type": ctype, "source": src})
    return cells


def _get_first_line(source: str) -> str:
    return source.split("\n")[0].strip() if source.strip() else ""


def _split_cells_into_pages(cells: list[dict]) -> dict[str, list[dict]]:
    """Split notebook cells into page groups based on H1 heading patterns."""
    compiled = [(p["id"], re.compile(p["heading_pattern"])) for p in PAGES]

    page_cells: dict[str, list[dict]] = {p["id"]: [] for p in PAGES}
    current_page: str | None = None

    for cell in cells:
        first_line = _get_first_line(cell["source"])

        for page_id, pattern in compiled:
            if pattern.match(first_line):
                current_page = page_id
                break

        if current_page is not None and cell["source"].strip():
            page_cells[current_page].append(cell)

    return page_cells


def _rewrite_image_paths(source: str) -> str:
    return source.replace("demos_images/", "images/")


def _build_content_page(page_def: dict, cells: list[dict]) -> str:
    page_id = page_def["id"]
    title = page_def["title"]

    processed_cells = []
    for cell in cells:
        processed_cells.append({
            "cell_type": cell["cell_type"],
            "source": _rewrite_image_paths(cell["source"]),
        })

    serialized = json.dumps(processed_cells, ensure_ascii=True)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} - Zoobenthic Assessment</title>
  <link rel="stylesheet" href="css/style.css">
  <script>
    window.MathJax = {{
      loader: {{ load: ['[tex]/extpfeil'] }},
      tex: {{ packages: {{ '[+]': ['extpfeil'] }}, inlineMath: [['$','$'],['\\\\(','\\\\)']], displayMath: [['$$','$$'],['\\\\[','\\\\]']] }},
      svg: {{ fontCache: 'global' }}
    }};
  </script>
  <script defer src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
  <script defer src="js/site.js"></script>
</head>
<body>
  <div id="site-nav"></div>
  <div class="page-layout">
    <aside id="sidebar" class="sidebar"></aside>
    <div class="sidebar-overlay"></div>
    <main class="content-area">
      <div id="notebook" class="notebook"></div>
    </main>
  </div>
  <script>
    window.PAGE_ID = "{page_id}";
    window.cells = {serialized};
  </script>
</body>
</html>
"""


def _copy_images() -> int:
    IMAGES_DST.mkdir(parents=True, exist_ok=True)
    count = 0
    if IMAGES_SRC.exists():
        for img in IMAGES_SRC.glob("*.png"):
            shutil.copy2(img, IMAGES_DST / img.name)
            count += 1
        for img in IMAGES_SRC.glob("*.jpg"):
            shutil.copy2(img, IMAGES_DST / img.name)
            count += 1
    return count


def main() -> None:
    cells = _load_cells(NOTEBOOK_PATH)
    print(f"Loaded {len(cells)} cells from {NOTEBOOK_PATH.name}")

    page_cells = _split_cells_into_pages(cells)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for page_def in PAGES:
        page_id = page_def["id"]
        pcells = page_cells[page_id]
        if not pcells:
            print(f"  WARNING: No cells matched for {page_def['file']}")
            continue

        html = _build_content_page(page_def, pcells)
        out_path = OUTPUT_DIR / page_def["file"]
        out_path.write_text(html, encoding="utf-8")
        print(f"  {page_def['file']:30s}  ({len(pcells)} cells)")

    n_imgs = _copy_images()
    print(f"  Copied {n_imgs} images to docs/images/")

    print(f"\nDone. Landing page (index.html) is NOT overwritten — edit it manually.")
    print(f"To publish: git add docs/ && git commit && git push")


if __name__ == "__main__":
    main()
