from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


METADATA_COLUMNS = [
    "Source",
    "Integrated Code",
    "Year",
    "Water body",
    "Latitude",
    "Longitude",
]


def parse_args() -> argparse.Namespace:
    stage1_root = Path(__file__).resolve().parents[1]
    return argparse.ArgumentParser(
        description=(
            "Run correlation-matrix PCA on log2(x + 1) transformed chemical data "
            "and export loading tables."
        )
    ).parse_args(namespace=argparse.Namespace(
        input_path=stage1_root / "inputs" / "data" / "chemical_all_sites_cleaned.xlsx",
        output_dir=stage1_root / "outputs" / "tables",
    ))


def get_chemical_columns(dataframe: pd.DataFrame) -> list[str]:
    missing_metadata = [column for column in METADATA_COLUMNS if column not in dataframe.columns]
    if missing_metadata:
        raise ValueError(f"Missing required metadata columns: {missing_metadata}")

    chemical_columns = [column for column in dataframe.columns if column not in METADATA_COLUMNS]
    if not chemical_columns:
        raise ValueError("No chemical columns were found after the metadata columns.")
    return chemical_columns


def validate_input(dataframe: pd.DataFrame, chemical_columns: list[str]) -> pd.DataFrame:
    numeric = dataframe[chemical_columns].apply(pd.to_numeric, errors="raise")
    if numeric.isna().any().any():
        missing_counts = numeric.isna().sum()
        missing_counts = missing_counts[missing_counts > 0]
        raise ValueError(
            "Chemical input contains missing values after numeric conversion: "
            f"{missing_counts.to_dict()}"
        )
    min_value = numeric.min().min()
    if min_value < 0:
        raise ValueError(
            "Chemical input contains negative values, so log2(x + 1) is invalid. "
            f"Minimum value: {min_value}"
        )
    return numeric


def log2_transform(numeric: pd.DataFrame) -> pd.DataFrame:
    transformed = np.log2(numeric + 1.0)
    transformed.index = numeric.index
    transformed.columns = numeric.columns
    return transformed


def correlation_pca(transformed: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
    correlation_matrix = transformed.corr()
    eigenvalues, eigenvectors = np.linalg.eigh(correlation_matrix.to_numpy())
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]

    component_names = [f"PC{i}" for i in range(1, len(eigenvalues) + 1)]
    loadings = eigenvectors * np.sqrt(eigenvalues)

    summary = pd.DataFrame(
        {
            "Component": component_names,
            "Eigenvalue": eigenvalues,
            "Explained variance (%)": eigenvalues / eigenvalues.sum() * 100.0,
        }
    )
    summary["Cumulative variance (%)"] = summary["Explained variance (%)"].cumsum()
    summary["Retained (Kaiser > 1)"] = summary["Eigenvalue"] > 1.0

    loading_table = pd.DataFrame(loadings, index=transformed.columns, columns=component_names)
    loading_table.index.name = "Chemical"
    return correlation_matrix, summary, loading_table.to_numpy()


def select_retained_components(summary: pd.DataFrame, loadings: np.ndarray) -> tuple[list[str], np.ndarray]:
    retained_mask = summary["Retained (Kaiser > 1)"].to_numpy(dtype=bool)
    if not retained_mask.any():
        retained_mask[0] = True

    retained_components = summary.loc[retained_mask, "Component"].tolist()
    retained_loadings = loadings[:, retained_mask]
    return retained_components, retained_loadings


def varimax(loadings: np.ndarray, gamma: float = 1.0, max_iter: int = 1000, tol: float = 1e-6) -> np.ndarray:
    if loadings.shape[1] <= 1:
        return loadings.copy()

    n_rows, n_cols = loadings.shape
    rotation = np.eye(n_cols)
    previous_objective = 0.0

    for _ in range(max_iter):
        rotated = loadings @ rotation
        transformed = loadings.T @ (
            rotated ** 3 - (gamma / n_rows) * rotated @ np.diag(np.diag(rotated.T @ rotated))
        )
        left, singular_values, right_t = np.linalg.svd(transformed)
        rotation = left @ right_t
        objective = singular_values.sum()
        if objective - previous_objective <= tol:
            break
        previous_objective = objective

    return loadings @ rotation


def build_loading_table(loadings: np.ndarray, variables: list[str], component_names: list[str]) -> pd.DataFrame:
    loading_table = pd.DataFrame(loadings, index=variables, columns=component_names)
    loading_table.index.name = "Chemical"
    loading_table["Communality"] = (loading_table[component_names] ** 2).sum(axis=1)
    loading_table["Primary component"] = loading_table[component_names].abs().idxmax(axis=1)
    return loading_table.reset_index()


def build_rotated_component_summary(rotated_loadings: np.ndarray, component_names: list[str]) -> pd.DataFrame:
    ss_loadings = np.sum(rotated_loadings ** 2, axis=0)
    variance_pct = ss_loadings / rotated_loadings.shape[0] * 100.0
    rotated_summary = pd.DataFrame(
        {
            "Component": component_names,
            "SS loadings": ss_loadings,
            "Rotated variance (%)": variance_pct,
        }
    )
    rotated_summary["Rotated cumulative variance (%)"] = rotated_summary[
        "Rotated variance (%)"
    ].cumsum()
    return rotated_summary


def export_tables(
    output_dir: Path,
    correlation_matrix: pd.DataFrame,
    pca_summary: pd.DataFrame,
    unrotated_loadings: pd.DataFrame,
    rotated_loadings: pd.DataFrame,
    rotated_summary: pd.DataFrame,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "chemical_log2_correlation_matrix.xlsx": correlation_matrix,
        "chemical_log2_pca_summary.xlsx": pca_summary,
        "chemical_log2_pca_unrotated_loadings.xlsx": unrotated_loadings,
        "chemical_log2_pca_rotated_loadings.xlsx": rotated_loadings,
        "chemical_log2_pca_rotated_summary.xlsx": rotated_summary,
    }

    written_paths: list[Path] = []
    for file_name, dataframe in outputs.items():
        output_path = output_dir / file_name
        dataframe.to_excel(output_path, index=False)
        written_paths.append(output_path)
    return written_paths


def main() -> None:
    args = parse_args()
    input_path = Path(args.input_path)
    output_dir = Path(args.output_dir)

    dataframe = pd.read_excel(input_path)
    chemical_columns = get_chemical_columns(dataframe)
    numeric = validate_input(dataframe, chemical_columns)
    transformed = log2_transform(numeric)
    
    correlation_matrix, pca_summary, all_loadings = correlation_pca(transformed)
    retained_components, retained_loadings = select_retained_components(pca_summary, all_loadings)
    rotated_loadings = varimax(retained_loadings)

    unrotated_table = build_loading_table(retained_loadings, chemical_columns, retained_components)
    rotated_table = build_loading_table(rotated_loadings, chemical_columns, retained_components)
    rotated_summary = build_rotated_component_summary(rotated_loadings, retained_components)

    written_paths = export_tables(
        output_dir=output_dir,
        correlation_matrix=correlation_matrix.reset_index(names="Chemical"),
        pca_summary=pca_summary,
        unrotated_loadings=unrotated_table,
        rotated_loadings=rotated_table,
        rotated_summary=rotated_summary,
    )

    retained_count = len(retained_components)
    print(f"Input file: {input_path}")
    print(f"Chemical variables: {len(chemical_columns)}")
    print(f"Rows used for PCA: {len(transformed)}")
    print(f"Retained components (Kaiser > 1): {retained_count}")
    print("Written files:")
    for output_path in written_paths:
        print(output_path)


if __name__ == "__main__":
    main()