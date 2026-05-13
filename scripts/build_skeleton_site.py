"""Build multi-notebook research website.

Usage:
    python scripts/build_skeleton_site.py

After editing the source notebooks, run this script to regenerate all HTML
pages in docs/. Then commit and push to update the GitHub Pages site.
"""

from __future__ import annotations

import calendar
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PREPARATION_NOTEBOOK_PATH = ROOT / "DataPreparation.ipynb"
ARCHITECTURE_NOTEBOOK_PATH = ROOT / "Architecture.ipynb"
CHAPTER2_NOTEBOOK_PATH = ROOT / "Chapter2.ipynb"
CHAPTER3_NOTEBOOK_PATH = ROOT / "Chapter3.ipynb"
CHAPTER4_NOTEBOOK_PATH = ROOT / "Chapter4.ipynb"
CHAPTER5_NOTEBOOK_PATH = ROOT / "Chapter5.ipynb"
CHAPTER6_NOTEBOOK_PATH = ROOT / "Chapter6.ipynb"
HOMEPAGE_NOTEBOOK_PATH = ROOT / "Homepage.ipynb"
RECORDS_NOTEBOOK_PATH = ROOT / "Records.ipynb"
OUTPUT_DIR = ROOT / "docs"
IMAGES_SRC = ROOT / "demos_images"
IMAGES_DST = OUTPUT_DIR / "images"
RECORDS_DIR = OUTPUT_DIR / "Records"

MONTH_NUM_TO_FULL = {num: name for num, name in enumerate(calendar.month_name) if num}

PDF_SUMMARIES: dict[str, str] = {
    "2025_03_21_meeting_notes.pdf": "Thesis committee formed; proposal framework established",
    "2025_05_05_meeting_notes.pdf": "Thesis framework: breakpoint regression analysis discussed",
    "2025_06_04_meeting_notes.pdf": "Prior work overview; dataset and proposal guidance",
    "2025_06_26_meeting_notes.pdf": "Data cleaning, merging, and clustering practice report",
    "2025_07_10_meeting_notes.pdf": "Test dataset progress; proposal defense timeline set",
    "2025_07_17_meeting_notes.pdf": "Proposal template sections reviewed with feedback",
    "2025_07_24_meeting_notes.pdf": "First proposal draft; dataset mismatch issues identified",
    "2025_07_25_meeting_notes.pdf": "First proposal draft review continued",
    "2025_08_07_meeting_notes.pdf": "Project framework and data analysis methods presented",
    "2025_09_04_meeting_notes.pdf": "Three-component framework: chemical, taxa, environmental",
    "2025_09_11_meeting_notes.pdf": "Reference condition study; proposal modification planned",
    "2025_10_02_meeting_notes.pdf": "Second proposal; PCA-based pollution assessment introduced",
    "2025_10_09_meeting_notes.pdf": "Third proposal revision; pollution assessment updated",
    "2025_10_16_meeting_notes.pdf": "Dataset merging completed; composite indicator discussed",
    "2025_10_23_meeting_notes.pdf": "Proposal submitted; Git version control adopted",
    "2025_10_30_meeting_notes.pdf": "PCA pollution assessment implemented; codebase refactored",
    "2025_11_06_meeting_notes.pdf": "Sediment contamination assessment: key lessons reported",
    "2025_11_13_meeting_notes.pdf": "Previous work summarized; next-step goals outlined",
    "2025_11_20_meeting_notes.pdf": "Sediment contamination assessment reproduction completed",
    "2025_12_04_meeting_notes.pdf": "Clustering analysis using PCA-derived pollution scores",
    "2025_12_11_meeting_notes.pdf": "Species composition analysis; water velocity imputed",
    "2025_12_18_meeting_notes.pdf": "RDA and LDA results; full workflow reviewed",
    "2026_01_08_meeting_notes.pdf": "Winter break update; 90% thesis framework completed",
    "2026_01_15_meeting_notes.pdf": "Environmental group partitioning; quantile regression discussed",
    "2026_01_22_meeting_notes.pdf": "Side-by-side comparison with Jian's thesis results",
    "2026_01_29_meeting_notes.pdf": "BEAST multivariate sediment assessment reproduction",
    "2026_02_05_meeting_notes.pdf": "Progress update; PhD offer from U of Alberta",
    "2026_02_11_meeting_notes.pdf": "In-person meeting; mid-term thesis report presented",
    "2026_02_26_meeting_notes.pdf": "Full computation overview; reproducibility discussed",
    "2026_02_28_SSC_Abstract-Feng Gu.pdf": "SSC abstract: ecological thresholds in zoobenthic communities",
    "2026_03_05_meeting_notes.pdf": "Computation details reviewed; thesis writing begins",
    "2026_03_12_meeting_notes.pdf": "Jian's multivariate approach presentation and comparison",
    "2026_03_15_SSC_Thesis_Summary - Feng Gu.pdf": "SSC thesis summary: stressor-response quantile detection",
    "2026_03_19_meeting_notes.pdf": "Chapter 2 discussion; RDA cut-off value advice",
    "2026_03_23_SSC_Travel_Grants.pdf": "SSC annual meeting student travel grant received",
    "2026_03_26_meeting_notes.pdf": "Chapter 2 feedback; clustering logic issues clarified",
    "2026_04_01_TRUSU_Travel_Grants.pdf": "TRUSU travel grant approved for conference attendance",
    "2026_04_02_meeting_notes.pdf": "Chapters 2-3 progress; RDA methodology discussed",
    "2026_04_16_meeting_notes.pdf": "PCA methodology review; clustering and presentation planning",
    "2026_04_21_meeting_notes.pdf": "PCA and clustering review continued",
    "2026_04_30_meeting_notes.pdf": "Data unit inconsistencies; mercury and zinc issues",
    "2026_05_07_meeting_notes.pdf": "Reviewed contaminant data discrepancies; emphasized extreme quantiles for thresholds",
}

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
        "notebook_path": DATA_PREPARATION_NOTEBOOK_PATH,
    },
    {
        "id": "data-preparation",
        "file": "data-preparation.html",
        "title": "Data Preparation",
        "heading_pattern": r"^#\s+.*Data Preparation|^#\s+Done in Data Preparation",
        "notebook_path": DATA_PREPARATION_NOTEBOOK_PATH,
    },
    {
        "id": "architecture",
        "file": "architecture.html",
        "title": "Architecture",
        "heading_pattern": r"^#\s+.*Architecture|^#\s+Workflow Template|^#\s+Tool:\s*Recursive",
        "notebook_path": ARCHITECTURE_NOTEBOOK_PATH,
    },
    {
        "id": "chapter2",
        "file": "chapter2.html",
        "title": "Chapter 2: Pollution Assessment",
        "heading_pattern": r"^#\s+Chapter 2",
        "notebook_path": CHAPTER2_NOTEBOOK_PATH,
    },
    {
        "id": "chapter3",
        "file": "chapter3.html",
        "title": "Chapter 3: Environmental Standardization",
        "heading_pattern": r"^#\s+Chapter 3",
        "notebook_path": CHAPTER3_NOTEBOOK_PATH,
    },
    {
        "id": "chapter4",
        "file": "chapter4.html",
        "title": "Chapter 4: ZCI of Bray-Curtis Ordination on Community Composition",
        "heading_pattern": r"^#\s+Chapter 4",
        "notebook_path": CHAPTER4_NOTEBOOK_PATH,
    },
    {
        "id": "chapter5",
        "file": "chapter5.html",
        "title": "Chapter 5",
        "heading_pattern": r"^#\s+Chapter 5",
        "notebook_path": CHAPTER5_NOTEBOOK_PATH,
    },
    {
        "id": "chapter6",
        "file": "chapter6.html",
        "title": "Chapter 6",
        "heading_pattern": r"^#\s+Chapter 6",
        "notebook_path": CHAPTER6_NOTEBOOK_PATH,
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


# ── Records page (meeting notes) ──

def _scan_local_meeting_notes() -> dict[int, list[dict]]:
    """Scan docs/Records/ for PDFs with a YYYY_MM_DD prefix.

    Returns entries sorted descending (most recent first) within each year.
    """
    if not RECORDS_DIR.exists():
        return {}
    by_year: dict[int, list[dict]] = {}
    for pdf in RECORDS_DIR.glob("*.pdf"):
        m = re.match(r"(\d{4})_(\d{2})_(\d{2})_(.+)\.pdf", pdf.name)
        if not m:
            continue
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        rest = m.group(4)
        month_name = MONTH_NUM_TO_FULL.get(month, f"Month{month}")
        if rest == "meeting_notes":
            display = f"{month_name} {day} Meeting Notes"
        else:
            display = f"{month_name} {day} — {rest.replace('_', ' ')}"
        summary = PDF_SUMMARIES.get(pdf.name, "")
        by_year.setdefault(year, []).append({
            "filename": pdf.name,
            "display": display,
            "summary": summary,
            "sort_key": (month, day),
        })
    for year in by_year:
        by_year[year].sort(key=lambda e: e["sort_key"], reverse=True)
    return by_year


def _build_records_page(by_year: dict[int, list[dict]],
                        notebook_cells: list[dict]) -> str:
    """Generate the Records HTML page with notebook content + collapsible year sections."""
    cells_json = json.dumps(
        [{"cell_type": c["cell_type"],
          "source": _rewrite_image_paths(c["source"])}
         for c in notebook_cells],
        ensure_ascii=True,
    )

    year_sections = ""
    for year in sorted(by_year.keys(), reverse=True):
        entries = by_year[year]
        is_open = "open" if year >= 2026 else ""
        items_html = ""
        for e in entries:
            href = f"Records/{e['filename']}"
            summary_html = (
                f'<span class="record-summary">{e["summary"]}</span>'
                if e.get("summary") else ""
            )
            items_html += (
                f'        <li class="record-item">'
                f'<a href="{href}" target="_blank" rel="noopener">'
                f'<span class="record-icon"></span>'
                f'<span class="record-text">{e["display"]}{summary_html}</span>'
                f'</a></li>\n'
            )
        year_sections += f"""    <details class="year-group" {is_open}>
      <summary class="year-heading">{year}</summary>
      <ul class="record-list">
{items_html}      </ul>
    </details>
"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Records - Zoobenthic Assessment</title>
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
  <div class="page-layout no-sidebar">
    <main class="content-area records-page">
      <div id="notebook" class="notebook"></div>
{year_sections}
    </main>
  </div>
  <script>
    window.PAGE_ID = "records";
    window.cells = {cells_json};
  </script>
</body>
</html>
"""


def main() -> None:
    standalone_cells: dict[str, list[dict]] = {}
    for page_def in STANDALONE_NOTEBOOK_PAGES:
        notebook_path = page_def["notebook_path"]
        cells = _load_cells(notebook_path)
        standalone_cells[page_def["id"]] = cells
        print(f"Loaded {len(cells)} cells from {notebook_path.name}")

    source_cells: dict[Path, list[dict]] = {}
    for notebook_path in sorted({p["notebook_path"] for p in PAGES}):
        cells = _load_cells(notebook_path)
        source_cells[notebook_path] = cells
        print(f"Loaded {len(cells)} cells from {notebook_path.name}")

    cells_by_notebook = {
        notebook_path: _split_cells_into_pages(cells)
        for notebook_path, cells in source_cells.items()
    }

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
        pcells = cells_by_notebook[page_def["notebook_path"]][page_id]
        if not pcells:
            print(f"  WARNING: No cells matched for {page_def['file']}")
            continue

        html = _build_content_page(page_def, pcells)
        out_path = OUTPUT_DIR / page_def["file"]
        out_path.write_text(html, encoding="utf-8")
        print(f"  {page_def['file']:30s}  ({len(pcells)} cells)")

    n_imgs = _copy_images()
    print(f"  Copied {n_imgs} images to docs/images/")

    # ── Records page ──
    records_cells: list[dict] = []
    if RECORDS_NOTEBOOK_PATH.exists():
        records_cells = _load_cells(RECORDS_NOTEBOOK_PATH)
        print(f"Loaded {len(records_cells)} cells from {RECORDS_NOTEBOOK_PATH.name}")

    by_year = _scan_local_meeting_notes()
    if by_year or records_cells:
        html = _build_records_page(by_year, records_cells)
        (OUTPUT_DIR / "records.html").write_text(html, encoding="utf-8")
        total = sum(len(v) for v in by_year.values())
        years = ", ".join(str(y) for y in sorted(by_year.keys()))
        print(f"  records.html                    ({total} meeting notes, years: {years})")
    else:
        print("  WARNING: No meeting notes found in docs/meeting-notes/, skipping records.html")

    print(f"\nDone. Landing page (index.html) is generated from {HOMEPAGE_NOTEBOOK_PATH.name}.")
    print("To publish: python scripts/build_skeleton_site.py && git add Chapter*.ipynb Homepage.ipynb Records.ipynb DataPreparation.ipynb Architecture.ipynb scripts/build_skeleton_site.py docs/ && git commit -m \"Update site from notebooks\" && git push")


if __name__ == "__main__":
    main()
