"""Build multi-notebook research website.

Usage:
    python scripts/build_skeleton_site.py

After editing the source notebooks, run this script to regenerate all HTML
pages in docs/. Then commit and push to update the GitHub Pages site.
"""

from __future__ import annotations

import calendar
from datetime import datetime
import html
import json
import math
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHAPTERS_DIR = ROOT / "chapters"
DATA_PREPARATION_NOTEBOOK_PATH = CHAPTERS_DIR / "DataPreparation.ipynb"
ARCHITECTURE_NOTEBOOK_PATH = CHAPTERS_DIR / "Architecture.ipynb"
CHAPTER2_NOTEBOOK_PATH = CHAPTERS_DIR / "Chapter2.ipynb"
CHAPTER3_NOTEBOOK_PATH = CHAPTERS_DIR / "Chapter3.ipynb"
CHAPTER4_NOTEBOOK_PATH = CHAPTERS_DIR / "Chapter4.ipynb"
CHAPTER5_NOTEBOOK_PATH = CHAPTERS_DIR / "Chapter5.ipynb"
CHAPTER6_NOTEBOOK_PATH = CHAPTERS_DIR / "Chapter6.ipynb"
HOMEPAGE_NOTEBOOK_PATH = CHAPTERS_DIR / "Homepage.ipynb"
RECORDS_NOTEBOOK_PATH = CHAPTERS_DIR / "Records.ipynb"
GALLERY_NOTEBOOK_PATH = CHAPTERS_DIR / "Gallery.ipynb"
DRAFTS_NOTEBOOK_PATH = CHAPTERS_DIR / "Drafts.ipynb"
OUTPUT_DIR = ROOT / "docs"
IMAGES_SRC = ROOT / "demos_images"
IMAGES_DST = OUTPUT_DIR / "images"
RECORDS_DIR = OUTPUT_DIR / "Records"
DRAFTS_DIR = OUTPUT_DIR / "Drafts"
THESIS_DRAFT_SRC = ROOT.parent / "Writing" / "main" / "main.pdf"
THESIS_DRAFT_DST = DRAFTS_DIR / "ongoing-thesis.pdf"
THESIS_MAIN_TEX_PATH = ROOT.parent / "Writing" / "main" / "main.tex"
CODESPACE_FIGURES_SRC = ROOT / "codespace" / "figures"
CODESPACE_RESULTS_SRC = ROOT / "codespace" / "results"
GALLERY_IMAGES_DST = IMAGES_DST / "gallery"
GALLERY_RESULTS_DST = OUTPUT_DIR / "results"

MONTH_NUM_TO_FULL = {num: name for num, name in enumerate(calendar.month_name) if num}

STYLE_CSS_PATH = OUTPUT_DIR / "css" / "style.css"
SITE_JS_PATH = OUTPUT_DIR / "js" / "site.js"


def _asset_version(path: Path) -> str:
    try:
        return str(int(path.stat().st_mtime))
    except FileNotFoundError:
        return "1"


STYLE_CSS_VERSION = _asset_version(STYLE_CSS_PATH)
SITE_JS_VERSION = _asset_version(SITE_JS_PATH)

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
    "2026_06_01_SSC_Slides.pdf": "SSC slide deck for thesis project presentation",
    "2026_06_05_meeting_notes.pdf": "NMDS interpretation priorities: add site codes and identify taxa driving reference-degraded separation",
    "2026_06_11_meeting_notes.pdf": "Reproduce original PCA and Bray-Curtis polar ordination before extending methods",
}

# ── Page definitions ──
# Each page is defined by a regex that matches the H1 heading that starts it.
# All cells from that H1 until the next H1 (or EOF) are included.
# The "title" is the display title shown in the rendered page.

PAGES = [
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
    {
        "id": "gallery",
        "file": "gallery.html",
        "title": "Gallery",
        "browser_title": "Gallery - Zoobenthic Assessment",
        "description": "Timeline of figures and tables produced across all chapter frameworks.",
        "notebook_path": GALLERY_NOTEBOOK_PATH,
        "layout": "gallery",
    },
    {
        "id": "drafts",
        "file": "drafts.html",
        "title": "Drafts",
        "browser_title": "Drafts - Zoobenthic Assessment",
        "description": "Current thesis draft and related draft notes.",
        "notebook_path": DRAFTS_NOTEBOOK_PATH,
        "layout": "content",
    },
]


def _normalize_source(source: object) -> str:
    if isinstance(source, list):
        parts = [str(s) for s in source]
        if len(parts) > 1 and not any("\n" in part for part in parts):
            return "\n".join(parts).rstrip()
        return "".join(parts).rstrip()
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
    path_rewrites = {
        "../demos_images/": "images/",
        "./demos_images/": "images/",
        "demos_images/": "images/",
        "../codespace/figures/": "images/gallery/",
        "codespace/figures/": "images/gallery/",
        "../codespace/results/": "results/",
        "codespace/results/": "results/",
    }

    rewritten = source
    for old, new in path_rewrites.items():
        rewritten = rewritten.replace(old, new)

    return rewritten


def _format_table_value(value: object) -> str:
    if value is None:
        return ""
    try:
        if value != value:
            return ""
    except TypeError:
        pass
    if isinstance(value, float):
        if math.isclose(value, round(value), abs_tol=1e-10):
            return str(int(round(value)))
        if 0 < abs(value) < 0.0001 or abs(value) >= 10000:
            return f"{value:.3e}"
        return f"{value:.3f}".rstrip("0").rstrip(".")
    return str(value)


def _clean_table_label(value: object) -> str:
    return re.sub(r"\s+", " ", _format_table_value(value).replace("\n", " ")).strip()


def _frame_to_html_table(frame, *, include_header: bool = True) -> str:
    rows: list[str] = []
    if include_header:
        headers = "".join(
            f"<th>{html.escape(_clean_table_label(column))}</th>"
            for column in frame.columns
        )
        rows.append(f"<thead><tr>{headers}</tr></thead>")

    body_rows = []
    for _, row in frame.iterrows():
        cells = "".join(
            f"<td>{html.escape(_format_table_value(value))}</td>"
            for value in row
        )
        body_rows.append(f"<tr>{cells}</tr>")
    rows.append("<tbody>" + "".join(body_rows) + "</tbody>")

    return (
        '<div class="gallery-table-block">\n'
        '<div class="table-wrapper">\n'
        '<table class="gallery-result-table">\n'
        + "\n".join(rows)
        + "\n</table>\n</div>\n</div>"
    )


def _large_frame_summary_table(frame) -> str:
    numeric = frame.select_dtypes(include="number")
    if numeric.empty:
        preview = frame.head(20)
        return _frame_to_html_table(preview) + f'\n<p class="gallery-table-note">Showing first 20 of {len(frame):,} rows.</p>'

    summary = numeric.agg(["count", "mean", "std", "min", "median", "max"]).T.reset_index()
    summary = summary.rename(columns={"index": "Variable"})
    return _frame_to_html_table(summary) + f'\n<p class="gallery-table-note">Numeric summary of {len(frame):,} rows.</p>'


def _excel_result_to_html(href: str) -> str:
    import pandas as pd

    filename = Path(href).name
    source_path = CODESPACE_RESULTS_SRC / filename
    if not source_path.exists():
        source_path = GALLERY_RESULTS_DST / filename
    if not source_path.exists():
        return f'<p class="gallery-table-note">Table file not found: {html.escape(filename)}</p>'

    header_frame = pd.read_excel(source_path)
    if len(header_frame) > 80:
        return _large_frame_summary_table(header_frame)

    if any(str(column).startswith("Unnamed") for column in header_frame.columns):
        raw_frame = pd.read_excel(source_path, header=None)
        return _frame_to_html_table(raw_frame, include_header=False)

    return _frame_to_html_table(header_frame)


def _embed_gallery_table_links(source: str) -> str:
    pattern = re.compile(r'<a\s+class="table-download"\s+href="([^"]+\.xlsx)"\s+download>.*?</a>')
    return pattern.sub(lambda match: _excel_result_to_html(match.group(1)), source)


def _strip_latex_comments(source: str) -> str:
    cleaned_lines = []
    for line in source.splitlines():
        escaped = False
        kept_chars = []
        for char in line:
            if char == "%" and not escaped:
                break
            kept_chars.append(char)
            escaped = char == "\\" and not escaped
            if char != "\\":
                escaped = False
        cleaned_lines.append("".join(kept_chars))
    return "\n".join(cleaned_lines)


def _extract_balanced_brace(source: str, open_index: int) -> tuple[str, int] | None:
    if open_index >= len(source) or source[open_index] != "{":
        return None

    depth = 0
    value_chars = []
    escaped = False
    for index in range(open_index, len(source)):
        char = source[index]
        if char == "\\" and not escaped:
            escaped = True
            if depth > 0:
                value_chars.append(char)
            continue
        if char == "{" and not escaped:
            depth += 1
            if depth > 1:
                value_chars.append(char)
        elif char == "}" and not escaped:
            depth -= 1
            if depth == 0:
                return "".join(value_chars).strip(), index + 1
            value_chars.append(char)
        elif depth > 0:
            value_chars.append(char)
        escaped = False
    return None


def _read_latex_command_arguments(source: str, command: str) -> list[str]:
    matches = []
    command_re = re.compile(rf"\\{re.escape(command)}\*?\s*(?:\[[^\]]*\]\s*)?\{{")
    for match in command_re.finditer(source):
        brace_index = match.end() - 1
        extracted = _extract_balanced_brace(source, brace_index)
        if extracted:
            matches.append(extracted[0])
    return matches


def _resolve_tex_input(base_path: Path, tex_input: str) -> Path:
    input_path = Path(tex_input.strip())
    if input_path.suffix != ".tex":
        input_path = input_path.with_suffix(".tex")
    if not input_path.is_absolute():
        input_path = base_path.parent / input_path
    return input_path.resolve()


def _latex_title_to_text(title: str) -> str:
    title = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?", "", title)
    title = title.replace("{", "").replace("}", "")
    title = re.sub(r"\s+", " ", title)
    return title.strip()


def _scan_compiled_thesis_structure() -> list[dict]:
    if not THESIS_MAIN_TEX_PATH.exists():
        print(f"  WARNING: Thesis main.tex not found: {THESIS_MAIN_TEX_PATH}")
        return []

    main_source = _strip_latex_comments(THESIS_MAIN_TEX_PATH.read_text(encoding="utf-8"))
    input_paths = [
        _resolve_tex_input(THESIS_MAIN_TEX_PATH, tex_input)
        for tex_input in _read_latex_command_arguments(main_source, "input")
    ]

    structure = []
    for input_path in input_paths:
        if not input_path.exists():
            print(f"  WARNING: Compiled chapter input not found: {input_path}")
            continue

        source = _strip_latex_comments(input_path.read_text(encoding="utf-8"))
        chapter_titles = _read_latex_command_arguments(source, "chapter")
        section_titles = _read_latex_command_arguments(source, "section")
        chapter_title = _latex_title_to_text(chapter_titles[0]) if chapter_titles else input_path.stem
        structure.append({
            "chapter": chapter_title,
            "sections": [_latex_title_to_text(title) for title in section_titles],
        })

    return structure


def _format_thesis_update_time() -> str:
    timestamp_path = THESIS_DRAFT_SRC if THESIS_DRAFT_SRC.exists() else THESIS_DRAFT_DST
    if not timestamp_path.exists():
        return "Unavailable"
    timestamp = datetime.fromtimestamp(timestamp_path.stat().st_mtime)
    return timestamp.strftime("%B %d; %H:%M")


def _format_compiled_structure_markdown(structure: list[dict]) -> str:
    if not structure:
        return "Compiled Structure:\n\nNo compiled chapters were detected from `main.tex`."

    lines = ["Compiled Structure:"]
    for index, chapter in enumerate(structure, start=1):
        section_count = len(chapter["sections"])
        section_label = "section" if section_count == 1 else "sections"
        lines.append(f"\nChapter {index}: {chapter['chapter']} ({section_count} {section_label})")
        if section_count:
            for section in chapter["sections"]:
                lines.append(f"- {section}")
        else:
            lines.append("- No sections detected")
    return "\n".join(lines)


def _inject_draft_metadata(cells: list[dict]) -> list[dict]:
    latest_update = f"Latest Update: {_format_thesis_update_time()}"
    compiled_structure = _format_compiled_structure_markdown(_scan_compiled_thesis_structure())
    link_pattern = re.compile(r"^- \[Thesis Draft in Progress\]\(Drafts/ongoing-thesis\.pdf\)\s*$", re.MULTILINE)

    updated_cells = []
    inserted = False
    for cell in cells:
        if inserted or cell["cell_type"] != "markdown":
            updated_cells.append(cell)
            continue

        source = cell["source"]
        if link_pattern.search(source):
            source = link_pattern.sub(
                f"{latest_update}\n\n- [Thesis Draft in Progress](Drafts/ongoing-thesis.pdf)\n\n{compiled_structure}",
                source,
                count=1,
            )
            inserted = True
        updated_cells.append({"cell_type": cell["cell_type"], "source": source})

    if not inserted:
        updated_cells.append({
            "cell_type": "markdown",
            "source": f"{latest_update}\n\n- [Thesis Draft in Progress](Drafts/ongoing-thesis.pdf)\n\n{compiled_structure}",
        })

    return updated_cells


def _build_content_page(page_def: dict, cells: list[dict]) -> str:
    page_id = page_def["id"]
    title = page_def["title"]
    browser_title = page_def.get("browser_title", f"{title} - Zoobenthic Assessment")
    description = page_def.get("description")
    layout = page_def.get("layout", "content")

    processed_cells = []
    for cell in cells:
        source = _rewrite_image_paths(cell["source"])
        if layout == "gallery":
            source = _embed_gallery_table_links(source)
        processed_cells.append({
            "cell_type": cell["cell_type"],
            "source": source,
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
    elif layout == "gallery":
        page_layout = "page-layout"
        main_class = "content-area gallery-page"
        sidebar_markup = """    <aside id="sidebar" class="sidebar"></aside>
    <div class="sidebar-overlay"></div>
"""
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
    <link rel="stylesheet" href="css/style.css?v={STYLE_CSS_VERSION}">
  <script>
    window.MathJax = {{
      loader: {{ load: ['[tex]/extpfeil'] }},
      tex: {{ packages: {{ '[+]': ['extpfeil'] }}, inlineMath: [['$','$'],['\\\\(','\\\\)']], displayMath: [['$$','$$'],['\\\\[','\\\\]']] }},
      svg: {{ fontCache: 'global' }}
    }};
  </script>
  <script defer src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
    <script defer src="js/site.js?v={SITE_JS_VERSION}"></script>
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


def _copy_gallery_assets() -> tuple[int, int]:
    """Copy codespace/figures/*.png → docs/images/gallery/ and
    codespace/results/*.xlsx → docs/results/ for the Gallery page."""
    n_figs = 0
    n_tabs = 0
    if CODESPACE_FIGURES_SRC.exists():
        GALLERY_IMAGES_DST.mkdir(parents=True, exist_ok=True)
        for img in CODESPACE_FIGURES_SRC.glob("*.png"):
            shutil.copy2(img, GALLERY_IMAGES_DST / img.name)
            n_figs += 1
        for img in CODESPACE_FIGURES_SRC.glob("*.jpg"):
            shutil.copy2(img, GALLERY_IMAGES_DST / img.name)
            n_figs += 1
    if CODESPACE_RESULTS_SRC.exists():
        GALLERY_RESULTS_DST.mkdir(parents=True, exist_ok=True)
        for tab in CODESPACE_RESULTS_SRC.glob("*.xlsx"):
            shutil.copy2(tab, GALLERY_RESULTS_DST / tab.name)
            n_tabs += 1
        for tab in CODESPACE_RESULTS_SRC.glob("*.csv"):
            shutil.copy2(tab, GALLERY_RESULTS_DST / tab.name)
            n_tabs += 1
    return n_figs, n_tabs


def _copy_thesis_draft() -> bool:
    """Copy the latest thesis draft into a stable public URL."""
    if not THESIS_DRAFT_SRC.exists():
        print(f"  WARNING: Thesis draft source not found: {THESIS_DRAFT_SRC}")
        return False

    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(THESIS_DRAFT_SRC, THESIS_DRAFT_DST)
    return True


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
    <link rel="stylesheet" href="css/style.css?v={STYLE_CSS_VERSION}">
  <script>
    window.MathJax = {{
      loader: {{ load: ['[tex]/extpfeil'] }},
      tex: {{ packages: {{ '[+]': ['extpfeil'] }}, inlineMath: [['$','$'],['\\\\(','\\\\)']], displayMath: [['$$','$$'],['\\\\[','\\\\]']] }},
      svg: {{ fontCache: 'global' }}
    }};
  </script>
  <script defer src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js"></script>
    <script defer src="js/site.js?v={SITE_JS_VERSION}"></script>
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
        if page_def["id"] == "drafts":
            pcells = _inject_draft_metadata(pcells)

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

    n_gfigs, n_gtabs = _copy_gallery_assets()
    print(f"  Copied {n_gfigs} gallery figures → docs/images/gallery/")
    print(f"  Copied {n_gtabs} gallery tables  → docs/results/")

    if _copy_thesis_draft():
        print(f"  Copied thesis draft → {THESIS_DRAFT_DST.relative_to(OUTPUT_DIR)}")

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
    print("To publish: python scripts/build_skeleton_site.py && git add chapters/ scripts/build_skeleton_site.py docs/ && git commit -m \"Update site from notebooks\" && git push")


if __name__ == "__main__":
    main()
