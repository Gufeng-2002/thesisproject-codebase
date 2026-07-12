from __future__ import annotations

import json
import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = REPO_ROOT / "codespace" / "notebooks" / "ch4_framework2.ipynb"
APPENDIX_DIR = REPO_ROOT / "docs" / "results" / "appendix"
DR_ARTIFACT_DIR = REPO_ROOT / "codespace" / "DetroitRiverCase" / "artifacts"
DR_COMBINED_BRAY_CURTIS_PATH = DR_ARTIFACT_DIR / "A7_bray_curtis_dissimilarity_matrix.xlsx"
DR_CLUSTER_BRAY_CURTIS_PATHS = {
    "cluster_C1": DR_ARTIFACT_DIR / "A11_C1_bray_curtis_dissimilarity_matrix.xlsx",
    "cluster_C2": DR_ARTIFACT_DIR / "A12_C2_bray_curtis_dissimilarity_matrix.xlsx",
    "cluster_C3": DR_ARTIFACT_DIR / "A13_C3_bray_curtis_dissimilarity_matrix.xlsx",
}
REQUIRED_CODE_CELL_ANCHORS = (
    "from pathlib import Path",
    "if STUDY_CASE == \"DR\":",
    "from dataclasses import dataclass",
    "def summarize_multistart_stability(final_stresses) -> dict[str, float]:",
    "def build_excluded_site_taxa_diagnostic_table(",
    "from mpl_toolkits.mplot3d import Axes3D",
    "cluster_raw_tables = {",
)
INTERACTIVE_CELL_ANCHOR = "from IPython.display import HTML, display"
INTERACTIVE_CELL_SPLIT_TOKEN = "interactive_ordination_figure = render_interactive_ordination_figure("


def normalize_notebook_source(source: object) -> str:
    if isinstance(source, list):
        return "".join(str(line) for line in source)
    return str(source)


def uncomment_source(source: str) -> str:
    uncommented_lines: list[str] = []
    for line in source.splitlines():
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]
        if stripped == "#":
            uncommented_lines.append("")
        elif stripped.startswith("# "):
            uncommented_lines.append(f"{indent}{stripped[2:]}")
        else:
            uncommented_lines.append(line)
    return "\n".join(uncommented_lines)


def load_notebook_code_cells() -> dict[str, str]:
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    code_cells: dict[str, str] = {}
    for cell in notebook["cells"]:
        if cell.get("cell_type") != "code":
            continue
        source = normalize_notebook_source(cell.get("source", []))
        if INTERACTIVE_CELL_ANCHOR in uncomment_source(source):
            source = uncomment_source(source)
        first_line = source.splitlines()[0] if source.splitlines() else ""
        code_cells[first_line] = source
    return code_cells


def ensure_dr_combined_bray_curtis_workbook() -> None:
    if DR_COMBINED_BRAY_CURTIS_PATH.exists():
        return

    import pandas as pd

    missing_paths = [
        path for path in DR_CLUSTER_BRAY_CURTIS_PATHS.values()
        if not path.exists()
    ]
    if missing_paths:
        missing_list = ", ".join(str(path.relative_to(REPO_ROOT)) for path in missing_paths)
        raise FileNotFoundError(
            "Cannot build Detroit River combined Bray-Curtis workbook; "
            f"missing split workbook(s): {missing_list}"
        )

    with pd.ExcelWriter(DR_COMBINED_BRAY_CURTIS_PATH) as writer:
        for sheet_name, source_path in DR_CLUSTER_BRAY_CURTIS_PATHS.items():
            pd.read_excel(source_path).to_excel(writer, sheet_name=sheet_name, index=False)


def build_interactive_figure(study_case: str, code_cells: dict[str, str]):
    original_env = os.environ.get("CH4_FW2_STUDY_CASE")
    original_cwd = Path.cwd()
    namespace = {"__name__": "__main__", "display": lambda *args, **kwargs: None}
    os.environ["CH4_FW2_STUDY_CASE"] = study_case
    os.chdir(NOTEBOOK_PATH.parent)
    try:
        for anchor in REQUIRED_CODE_CELL_ANCHORS:
            exec(compile(code_cells[anchor], f"{NOTEBOOK_PATH.name}:{anchor}", "exec"), namespace)
        interactive_source = code_cells[INTERACTIVE_CELL_ANCHOR].split(INTERACTIVE_CELL_SPLIT_TOKEN)[0]
        exec(compile(interactive_source, f"{NOTEBOOK_PATH.name}:{INTERACTIVE_CELL_ANCHOR}", "exec"), namespace)
        figure = namespace["render_interactive_ordination_figure"](
            namespace["cluster_nmds_reports"],
            cluster_extreme_site_tables=namespace["cluster_extreme_site_tables"],
            score_col=namespace["CONTAMINATION_SCORE"],
            id_col=namespace["SITE_ID_COLUMN"],
            ref_pole_labels=namespace["CLUSTER_REF_POLE_LABELS"],
            deg_pole_labels=namespace["CLUSTER_DEG_POLE_LABELS"],
        )
    finally:
        os.chdir(original_cwd)
        if original_env is None:
            os.environ.pop("CH4_FW2_STUDY_CASE", None)
        else:
            os.environ["CH4_FW2_STUDY_CASE"] = original_env
    return figure


def export_gallery_appendix() -> list[Path]:
    APPENDIX_DIR.mkdir(parents=True, exist_ok=True)
    ensure_dr_combined_bray_curtis_workbook()
    code_cells = load_notebook_code_cells()
    written_files: list[Path] = []
    for study_case in ("corridor", "DR"):
        figure = build_interactive_figure(study_case, code_cells)
        output_path = APPENDIX_DIR / f"ch4_fw2_interactive_ordination_{study_case.lower()}.html"
        output_path.write_text(
            figure.to_html(include_plotlyjs="cdn", full_html=True),
            encoding="utf-8",
        )
        written_files.append(output_path)
    return written_files


if __name__ == "__main__":
    for output_path in export_gallery_appendix():
        print(output_path.relative_to(REPO_ROOT))
