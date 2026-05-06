"""Build multi-notebook research website.

Usage:
    python scripts/build_skeleton_site.py

After editing the source notebooks, run this script to regenerate all HTML
pages in docs/. Then commit and push to update the GitHub Pages site.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKELETON_NOTEBOOK_PATH = ROOT / "Skeleton.ipynb"
HOMEPAGE_NOTEBOOK_PATH = ROOT / "Homepage.ipynb"
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
    {
        "id": "chapter4",
        "file": "chapter4.html",
        "title": "Chapter 4: ZCI of Bray-Curtis Ordination on Community Composition",
        "heading_pattern": r"^#\s+Chapter 4",
    },
]

STANDALONE_NOTEBOOK_PAGES = [
    {
        "id": "home",
        "file": "index.html",
        "title": "Zoobenthic Community Assessment",
        "browser_title": "Zoobenthic Community Assessment - Research Project",
        "description": "Research website for zoobenthic community-condition assessment using sediment chemistry and environmental descriptors.",
        "notebook_path": HOMEPAGE_NOTEBOOK_PATH,
        "layout": "home",
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

        matched_page = False
        for page_id, pattern in compiled:
            if pattern.match(first_line):
                current_page = page_id
                matched_page = True
                break

        if first_line.startswith("# ") and not matched_page:
            current_page = None

        if current_page is not None and cell["source"].strip():
            page_cells[current_page].append(cell)

    return page_cells


def _rewrite_image_paths(source: str) -> str:
    return source.replace("demos_images/", "images/")


def _build_content_page(page_def: dict, cells: list[dict]) -> str:
    page_id = page_def["id"]
    title = page_def["title"]
    browser_title = page_def.get("browser_title", f"{title} - Zoobenthic Assessment")
    description = page_def.get("description")
    layout = page_def.get("layout", "content")

    processed_cells = []
    for cell in cells:
        processed_cells.append({
            "cell_type": cell["cell_type"],
            "source": _rewrite_image_paths(cell["source"]),
        })

    serialized = json.dumps(processed_cells, ensure_ascii=True)
    meta_description = (
        f'\n  <meta name="description" content="{description}">'
        if description
        else ""
    )

    if layout == "home":
        page_layout = "page-layout no-sidebar"
        main_class = "content-area landing-content"
        sidebar_markup = ""
    else:
        page_layout = "page-layout"
        main_class = "content-area"
        sidebar_markup = """    <aside id="sidebar" class="sidebar"></aside>
    <div class="sidebar-overlay"></div>
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{browser_title}</title>{meta_description}
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
  <div class="{page_layout}">
{sidebar_markup}    <main class="{main_class}">
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
    standalone_cells: dict[str, list[dict]] = {}
    for page_def in STANDALONE_NOTEBOOK_PAGES:
        notebook_path = page_def["notebook_path"]
        cells = _load_cells(notebook_path)
        standalone_cells[page_def["id"]] = cells
        print(f"Loaded {len(cells)} cells from {notebook_path.name}")

    cells = _load_cells(SKELETON_NOTEBOOK_PATH)
    print(f"Loaded {len(cells)} cells from {SKELETON_NOTEBOOK_PATH.name}")

    page_cells = _split_cells_into_pages(cells)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for page_def in STANDALONE_NOTEBOOK_PAGES:
        pcells = standalone_cells[page_def["id"]]
        if not pcells:
            print(f"  WARNING: No cells matched for {page_def['file']}")
            continue

        html = _build_content_page(page_def, pcells)
        out_path = OUTPUT_DIR / page_def["file"]
        out_path.write_text(html, encoding="utf-8")
        print(f"  {page_def['file']:30s}  ({len(pcells)} cells)")

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

    print(f"\nDone. Landing page (index.html) is generated from {HOMEPAGE_NOTEBOOK_PATH.name}.")
    print(f"To publish: git add docs/ && git commit && git push")


if __name__ == "__main__":
    main()
