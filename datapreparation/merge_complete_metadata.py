from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


SAMPLE_INFO_COLUMNS = ["Latitude", "Longitude", "Waterbody", "Year"]
ENVIRONMENTAL_COLUMNS = [
    "LOI (%)",
    "MPS (Phi)",
    "Measured Depth (m)",
    "Temperature (oC)",
    "Velocity  at bottom (m/sec)",
    "Water DO Bottom (mg/L)",
]
TAXA_COLUMNS = [
    "Acari",
    "Amphipoda",
    "Caenis",
    "Ceratopogonidae",
    "Chironomidae",
    "Dreissena",
    "Gastropoda",
    "Hexagenia",
    "Hirudinea",
    "Hydropsychidae",
    "Hydrozoa",
    "Nematoda",
    "Oligochaeta",
    "Other Trichoptera",
    "Sphaeriidae",
    "Turbellaria",
]
CHEMICAL_TEMPLATE_COLUMNS = [
    "%OC",
    "1245-TCB",
    "1234-TCB",
    "QCB",
    "HCB",
    "OCS",
    "p,p'-DDE",
    "total PCB",
    "Al",
    "As",
    "Bi",
    "Ca",
    "Cd",
    "Co",
    "Cr",
    "Cu",
    "Fe",
    "Hg",
    "K",
    "Mg",
    "Mn",
    "Na",
    "Ni",
    "Pb",
    "Sb",
    "V",
    "Zn",
]
CHEMICAL_SOURCE_MAP = {
    "total PCB": "SumPCBs",
}
ENVIRONMENTAL_SOURCE_MAP = {
    "Temperature (oC)": "Temperature (degC)",
    "Velocity  at bottom (m/sec)": "Velocity at bottom (m/sec)",
}


def parse_args() -> argparse.Namespace:
    metadata_root = Path(__file__).resolve().parent
    workspace_root = metadata_root.parents[1]
    parser = argparse.ArgumentParser(
        description=(
            "Merge the cleaned chemical, environmental, and taxa tables into the "
            "same grouped workbook layout as complete_env_taxa_chemical_Apr17.xlsx."
        )
    )
    parser.add_argument(
        "--template-path",
        type=Path,
        default=workspace_root / "Project_Code" / "data" / "processed" / "complete_env_taxa_chemical_Apr17.xlsx",
    )
    parser.add_argument(
        "--chemical-path",
        type=Path,
        default=metadata_root / "cleaned" / "chemical_all_sites_cleaned.xlsx",
    )
    parser.add_argument(
        "--environmental-path",
        type=Path,
        default=metadata_root / "cleaned" / "environmental_all_sites_cleaned.xlsx",
    )
    parser.add_argument(
        "--taxa-path",
        type=Path,
        default=metadata_root / "cleaned" / "taxa_all_sites_cleaned.xlsx",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=metadata_root / "cleaned" / "complete_env_taxa_chemical_cleaned.xlsx",
    )
    return parser.parse_args()


def load_unique_table(path: Path) -> pd.DataFrame:
    dataframe = pd.read_excel(path)
    dataframe = dataframe.dropna(subset=["Integrated Code"]).copy()
    if dataframe["Integrated Code"].duplicated().any():
        duplicates = dataframe.loc[
            dataframe["Integrated Code"].duplicated(keep=False), "Integrated Code"
        ].tolist()
        raise ValueError(f"Duplicated Integrated Code values found in {path.name}: {duplicates}")
    return dataframe.set_index("Integrated Code", drop=True)


def build_chemical_section(chemical: pd.DataFrame) -> pd.DataFrame:
    chemical_section = pd.DataFrame(index=chemical.index, columns=CHEMICAL_TEMPLATE_COLUMNS, dtype=float)
    for template_column in CHEMICAL_TEMPLATE_COLUMNS:
        source_column = CHEMICAL_SOURCE_MAP.get(template_column, template_column)
        if source_column in chemical.columns:
            chemical_section[template_column] = chemical[source_column]
        else:
            chemical_section[template_column] = np.nan
    return chemical_section


def build_environmental_section(environmental: pd.DataFrame) -> pd.DataFrame:
    environmental_section = pd.DataFrame(index=environmental.index)
    for target_column in ENVIRONMENTAL_COLUMNS:
        source_column = ENVIRONMENTAL_SOURCE_MAP.get(target_column, target_column)
        environmental_section[target_column] = environmental[source_column]
    return environmental_section


def build_sample_info(chemical: pd.DataFrame) -> pd.DataFrame:
    sample_info = chemical[["Latitude", "Longitude", "Water body", "Year"]].copy()
    return sample_info.rename(columns={"Water body": "Waterbody"})


def validate_template_site_set(template_ids: list[str], common_ids: set[str]) -> None:
    template_id_set = set(template_ids)
    missing_from_common = sorted(template_id_set - common_ids)
    missing_from_template = sorted(common_ids - template_id_set)
    if missing_from_common or missing_from_template:
        raise ValueError(
            "The current three-way intersection does not match the Apr17 template site set. "
            f"Missing from current data: {missing_from_common}. "
            f"Missing from template: {missing_from_template}."
        )


def build_output_frame(template_path: Path, chemical: pd.DataFrame, environmental: pd.DataFrame, taxa: pd.DataFrame) -> pd.DataFrame:
    template_raw = pd.read_excel(template_path, header=None)
    template_ids = template_raw.iloc[4:, 0].astype(str).str.strip().tolist()

    common_ids = set(chemical.index) & set(environmental.index) & set(taxa.index)
    validate_template_site_set(template_ids, common_ids)

    row_order = [site_id for site_id in template_ids if site_id in common_ids]

    sample_info = build_sample_info(chemical)
    environmental_section = build_environmental_section(environmental)
    taxa_section = taxa[TAXA_COLUMNS].copy()
    chemical_section = build_chemical_section(chemical)

    merged = pd.DataFrame(index=row_order)
    merged.index.name = "StationID"
    merged = merged.join(sample_info, how="left")
    merged = merged.join(environmental_section, how="left")
    merged = merged.join(taxa_section, how="left")
    merged = merged.join(chemical_section, how="left")

    desired_columns = [
        "StationID",
        *SAMPLE_INFO_COLUMNS,
        *ENVIRONMENTAL_COLUMNS,
        *TAXA_COLUMNS,
        *CHEMICAL_TEMPLATE_COLUMNS,
    ]
    body = merged.reset_index()[desired_columns]
    body.columns = template_raw.columns
    return pd.concat([template_raw.iloc[:4].copy(), body], ignore_index=True)


def main() -> None:
    args = parse_args()
    chemical = load_unique_table(args.chemical_path)
    environmental = load_unique_table(args.environmental_path)
    taxa = load_unique_table(args.taxa_path)

    output_frame = build_output_frame(args.template_path, chemical, environmental, taxa)
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    output_frame.to_excel(args.output_path, index=False, header=False)

    missing_template_chemicals = [
        column for column in CHEMICAL_TEMPLATE_COLUMNS if CHEMICAL_SOURCE_MAP.get(column, column) not in chemical.columns
    ]

    print(f"Template: {args.template_path}")
    print(f"Output: {args.output_path}")
    print(f"Merged site rows: {len(output_frame) - 4}")
    print(f"Template-only chemical columns left blank: {missing_template_chemicals}")


if __name__ == "__main__":
    main()