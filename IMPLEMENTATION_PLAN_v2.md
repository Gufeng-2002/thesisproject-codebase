# Implementation Plan — Chapter Workspaces, Two Cases, Thin Notebooks

This supersedes the prior plan. Three substantive changes:

1. **Layout is chapter-first.** Each of Chapter 2, 3, 4 is a *workspace* with its own `inputs/`, `process/`, `outputs/` folders. The process notebook *lives inside* the process folder. The Inputs–Process–Outputs structure on disk mirrors the Architecture vocabulary one-for-one.
2. **Inputs are plain tables.** The merged-xlsx-with-MultiIndex format is dropped. The bootstrap step (`p00`) reads four plain files — `sample_info.xlsx`, `chemical.xlsx`, `environmental.xlsx`, `taxa.xlsx` — with `StationID` as a single-column index and a single header row.
3. **Figure designs come from the chapter notebooks, not from `src/zci/`.** The existing `src/zci/viz/*` code is a *visual reference for what worked*, not a template. Every figure spec in Part 4 below is lifted from the chapter notebooks' computation-process specs (axes, panels, legend, annotations).

The "thin notebook + case config + Python everywhere + small `base/` package" core stays.

---

## Part 0 — What is being built

Three chapter workspaces (Ch2, Ch3, Ch4). Each workspace has one or more thin computation-process notebooks. All notebooks share a `base/` package. Each runs for one *case* (DR or corridor) at a time. Inputs to a chapter come from a shared `data/prepared/{case}/` folder (produced by a one-time bootstrap notebook). Artifacts cross chapter boundaries through a tiny *artifact registry* in `base.config` — no notebook builds paths by hand.

---

## Part 1 — Filesystem layout

```
project_root/
│
├── data/                                          [INPUT — committed]
│   ├── raw/                                       ← four plain tables, see §3
│   │   ├── sample_info.xlsx
│   │   ├── chemical.xlsx
│   │   ├── environmental.xlsx
│   │   └── taxa.xlsx
│   ├── maps/                                      ← shapefiles for map figures
│   │   ├── lake_stclair/
│   │   ├── lake_erie/
│   │   ├── lake_huron/
│   │   ├── detroit_river_aoc_shapefile/
│   │   └── aoc_mi_stclair_2021/
│   └── prepared/                                  [OUTPUT of p00 — gitignored]
│       ├── DR/
│       │   ├── sample_info.parquet                (213 × 7)
│       │   ├── M.parquet                          (213 × 16)
│       │   ├── E.parquet                          (213 × 6)
│       │   └── T.parquet                          (213 × 16)
│       └── corridor/
│           ├── sample_info.parquet                (310 × 7)
│           ├── M.parquet                          (310 × 16)
│           ├── E.parquet                          (310 × 5)
│           └── T.parquet                          (310 × 16)
│
├── base/                                          [CODE — see Part 2]
│   ├── __init__.py
│   ├── config.py
│   ├── io.py
│   ├── schemas.py
│   ├── log.py
│   ├── transforms/
│   ├── bridging/
│   ├── modeling/
│   ├── interpreters/
│   └── plotting/
│
├── bootstrap/                                     [bootstrap notebook — not a chapter]
│   └── p00_prepare_inputs.ipynb
│
├── chapters/                                      [the three chapter workspaces]
│   │
│   ├── ch2/
│   │   ├── inputs/
│   │   │   ├── metadata/                          ← links/views to data/prepared/{case}/
│   │   │   └── artifacts/                         ← (empty for Ch2 — no prior chapters)
│   │   ├── process/
│   │   │   ├── p01_contamination_stressors.ipynb
│   │   │   └── p02_reference_validation.ipynb
│   │   └── outputs/
│   │       └── {case}/
│   │           ├── artifacts/                     ← A1, A2 → consumed by Ch3, Ch4
│   │           │   ├── A1.parquet
│   │           │   └── A2.parquet
│   │           └── results/
│   │               ├── tables/                    ← xlsx
│   │               └── figures/                   ← png 300 dpi
│   │
│   ├── ch3/
│   │   ├── inputs/
│   │   │   ├── metadata/
│   │   │   └── artifacts/                         ← reads A1, A2 from ch2/outputs
│   │   ├── process/
│   │   │   ├── p03_reference_clusters.ipynb
│   │   │   ├── p04_concordance_consensus.ipynb
│   │   │   └── p05_env_classifier.ipynb
│   │   └── outputs/
│   │       └── {case}/
│   │           ├── artifacts/
│   │           │   ├── A3.parquet
│   │           │   ├── A4.parquet
│   │           │   └── A5.parquet
│   │           └── results/
│   │               ├── tables/
│   │               └── figures/
│   │
│   └── ch4/
│       ├── inputs/
│       ├── process/
│       │   ├── p06_braycurtis_with_poles.ipynb
│       │   ├── p07_nmds_per_cluster.ipynb
│       │   └── p08_zci_projection.ipynb
│       └── outputs/
│           └── {case}/
│               ├── artifacts/
│               │   ├── A6.parquet
│               │   ├── A7.pkl
│               │   ├── A8.pkl
│               │   └── A9.parquet
│               └── results/
│                   ├── tables/
│                   └── figures/
│
├── site/                                          [DOCUMENTATION — narrative notebooks]
│   ├── Homepage.ipynb
│   ├── Architecture.ipynb
│   ├── DataPreparation.ipynb
│   ├── Chapter2.ipynb
│   ├── Chapter3.ipynb
│   ├── Chapter4.ipynb
│   ├── Chapter5.ipynb
│   ├── Chapter6.ipynb
│   └── Records.ipynb
│
├── scripts/
│   ├── run_all.py                                 ← --case DR | corridor | both
│   └── build_skeleton_site.py                     ← regenerates docs/ from site/
│
├── demos_images/                                  ← chapter-narrative illustrations (stays)
│
├── docs/                                          ← auto-generated site
│
├── logs/                                          ← gitignored
│   └── {case}/{YYYY-MM-DD_HHMM}/
│
├── tests/
│   └── test_base/
│
├── _archive/
│   └── zci_legacy/                                ← old src/zci/ moved here, kept for reference
│
├── pyproject.toml
├── .gitignore
└── README.md
```

### Why `inputs/` exists in each chapter even when populated by symbolic reference

The `inputs/metadata/` and `inputs/artifacts/` folders are **logical views**, not duplicated data. They serve two purposes:

1. **Documentation.** A reader opening `chapters/ch3/` sees immediately *what goes in*, where the metadata is sourced from, which prior-chapter artifacts are consumed. This is the "Inputs–Process–Outputs" structure on disk — exactly the Architecture template, made navigable.
2. **Optional materialization.** If you ever want a chapter to be *self-contained* (e.g. to share a single chapter's reproducibility bundle), the orchestrator can populate `inputs/` with actual copies on demand. In normal operation they're empty (or contain a small `README.md` pointing to the real source).

**In normal operation, `io.load_artifact("A1")` does not read from `chapters/ch3/inputs/artifacts/A1.parquet`.** It resolves to the *producer* chapter's `outputs/`, using the artifact registry below. The `inputs/` folders are conceptual scaffolding, not the actual path. This is the right tradeoff: the visible structure matches the Architecture vocabulary, the runtime behavior avoids file duplication.

### Per-folder commit rules

| Folder                                | Committed?     | Case-scoped? |
|---------------------------------------|----------------|--------------|
| `data/raw/`                           | yes            | no           |
| `data/maps/`                          | yes            | no           |
| `data/prepared/{case}/`               | **no**         | yes          |
| `base/`                               | yes            | no           |
| `bootstrap/p00_*.ipynb`               | yes            | no           |
| `chapters/ch*/inputs/`                | yes (empty + README) | no     |
| `chapters/ch*/process/p*.ipynb`       | yes            | no           |
| `chapters/ch*/outputs/{case}/artifacts/` | **no**      | yes          |
| `chapters/ch*/outputs/{case}/results/`| yes            | yes          |
| `site/`                               | yes            | no           |
| `demos_images/`                       | yes            | no           |
| `docs/`                               | yes            | no           |
| `logs/`                               | **no**         | yes          |
| `_archive/`                           | yes            | no           |

---

## Part 2 — The `base/` package

Same as before, with one change: `base.config` now holds the artifact *producer registry* that tells `io` which chapter writes which artifact.

```
base/
├── config.py                  Case, CASES, set_case(), ARTIFACT_PRODUCERS, PATHS
├── io.py                      load_artifact, save_artifact, save_table, save_figure
├── schemas.py                 pandera schemas for sample_info, M, E, T, A1..A9
├── log.py                     get_logger
│
├── transforms/
│   ├── log_plus_one.py
│   └── standardize.py
│
├── bridging/
│   ├── select.py              by_bool_column, by_cluster_membership, by_status
│   ├── slice_matrix.py
│   ├── random_subset.py
│   ├── bootstrap.py           rows-with-replacement
│   ├── centroid.py
│   ├── correlation_matrix.py
│   ├── pole_appender.py
│   └── prediction_grid.py
│
├── modeling/
│   ├── pca.py                 fit + rotate (varimax) → PCAResult
│   ├── dissim.py              manhattan, euclidean, braycurtis
│   ├── hclust.py              Ward → WardResult
│   ├── anova.py               node-wise + finalized + FDR
│   ├── pvclust.py             multiscale bootstrap → AU p-values
│   ├── consensus.py           B-resample → co-assignment + margins
│   ├── rda.py                 fit + adj-R² + permutation test
│   ├── nmds.py                PAV + gradient descent + multistart + stratified Shepard
│   ├── classifiers/
│   │   ├── lda.py
│   │   ├── mrt.py
│   │   └── cv.py
│   └── projection.py          scalar projector + residual extractor (Ch4 F3)
│
├── interpreters/
│   ├── empirical_dist.py
│   ├── metric_diagnostics.py
│   ├── confusion.py
│   ├── posterior_threshold.py
│   ├── correlations.py
│   └── zci_pivot.py           long→wide for Ch4 F3 documental form
│
└── plotting/
    ├── style.py
    ├── corridor_map.py        plot_corridor_bifurcation
    ├── dr_map.py              plot_dr_bifurcation
    ├── ecdf.py
    ├── rda_density.py
    ├── dendrogram.py
    ├── barplots.py
    ├── concordance_scatter.py
    ├── decision_regions.py
    ├── histograms.py
    ├── shepard.py
    ├── stress_scree.py
    └── ordination.py
```

### The artifact producer registry

```python
# base/config.py
ARTIFACT_PRODUCERS = {
    "A1": "ch2", "A2": "ch2",
    "A3": "ch3", "A4": "ch3", "A5": "ch3",
    "A6": "ch4", "A7": "ch4", "A8": "ch4", "A9": "ch4",
}

# Metadata (M, E, T, sample_info) lives in data/prepared/{case}/
# Resolved separately by io.load_metadata("M")
```

That single dict is all the cross-chapter wiring needed. `io.load_artifact("A3")` reads:

```
chapters/{ARTIFACT_PRODUCERS["A3"]}/outputs/{config.CASE}/artifacts/A3.parquet
```

`io.save_artifact(df, "A3")` writes to the same path. **Producer and consumer notebooks both call the same function**; they only differ in whether the file exists yet. No notebook constructs paths by hand. Adding a future Chapter 5 artifact is one entry in the registry.

### Two design rules that make this work

1. **`base/modeling/` and `base/interpreters/` never import `config`.** They take matrices, not paths. This is the rule that makes future per-framework tweaks automatically case-compatible.
2. **All I/O goes through `base.io`.** The four functions `load_metadata`, `load_artifact`, `save_artifact`, `save_table`, `save_figure` are the only places that read `config.CASE` and the registry.

---

## Part 3 — Inputs: the four plain tables

`data/raw/` holds four plain Excel files. Single header row each. `StationID` is the row key in all four. No MultiIndex anywhere.

| File                  | Index      | Columns                                                              | Rows |
|-----------------------|------------|----------------------------------------------------------------------|------|
| `sample_info.xlsx`    | StationID  | Integrated Code, Year, Water body, Latitude, Longitude, chemical_source, taxa_source | 310 |
| `chemical.xlsx`       | StationID  | 16 chemical concentration columns (Co, Al, Ni, Mn, Fe, Cr, Cu, Hg, Pb, Zn, SumPCBs, Cd, OCS, p,p'-DDE, As, Ca) | 310 |
| `environmental.xlsx`  | StationID  | LOI (%), Measured Depth (m), Temperature (oC), Water DO Bottom (mg/L), MPS (Phi), Velocity at bottom (m/sec) | 310 |
| `taxa.xlsx`           | StationID  | 16 taxa columns in proportional-octave form                          | 310 |

**Pending confirmation** (decision 1 in Part 9): the column name in `environmental.xlsx` for the velocity descriptor — pick *one* canonical spelling and use it everywhere. Recommend `Velocity at bottom (m/sec)` (single space, fix the typo in `environemntal`). The schema will reject anything else, so this needs to be set before the tables are exported.

### `p00_prepare_inputs.ipynb` (bootstrap)

Lives in `bootstrap/`, runs once per case. Four cells:

```python
# ── Cell 1: SETUP ─────────────────────────────────────────────────────────
from base import config, io
config.set_case("DR")          # ← case switch

# ── Cell 2: INPUTS ────────────────────────────────────────────────────────
sample_info = io.read_raw("sample_info")
M_full = io.read_raw("chemical")
E_full = io.read_raw("environmental")
T_full = io.read_raw("taxa")

# ── Cell 3: PROCESS (case filter) ─────────────────────────────────────────
case = config.current()
mask = sample_info["Water body"].isin(case.water_bodies)
if case.require_velocity:
    mask &= E_full["Velocity at bottom (m/sec)"].notna()

sample_info = sample_info.loc[mask]
M = M_full.loc[mask]
E = E_full.loc[mask, list(case.env_columns)]   # corridor drops Velocity
T = T_full.loc[mask]

# ── Cell 4: OUTPUTS ───────────────────────────────────────────────────────
io.save_metadata(sample_info, "sample_info")
io.save_metadata(M, "M")
io.save_metadata(E, "E")
io.save_metadata(T, "T")
```

DR run produces `data/prepared/DR/{sample_info,M,E,T}.parquet` (213 rows, E has 6 columns). Corridor run produces `data/prepared/corridor/...` (310 rows, E has 5 columns).

---

## Part 4 — Output protocol (chapter-spec form)

The contract between each notebook and the chapter narrative is the table/figure spec written in the chapter notebooks. The `src/zci/` figures are visual references for *what worked aesthetically*, not templates. Every spec below traces back to a "table:" or "figure:" entry in the corresponding chapter notebook's Output section.

Format conventions: tables in **xlsx**, figures in **png at 300 dpi** with `bbox_inches="tight"`. Multi-panel figures use one grid per spec (no concatenated subplots from different framings).

### Chapter 2 workspace (`chapters/ch2/`)

#### `process/p01_contamination_stressors.ipynb` (Ch2 F1)

Tables in `outputs/{case}/results/tables/`:

- `ch2_pca_loadings.xlsx` — rotated component loadings $\mathbf{L}'$.
  - rows: (chemical) × (PC$_1$, …, PC$_m$)
  - shape: $16 \times m$

- `ch2_pca_variance_explained.xlsx`
  - rows: (Eigenvalue, Proportion of Variance, Cumulative Proportion)
  - shape: $3 \times m$

- `ch2_contamination_scores.xlsx` — site-level SumRel + MaxRel.
  - rows: (StationID, $s_1$, …, $s_m$, SumRel, MaxRel)
  - shape: $N \times (m + 3)$

- `ch2_site_rankings.xlsx` — combined ranking under both scoring rules.
  - rows: (StationID, SumRel, SumRel_rank, MaxRel, MaxRel_rank)
  - shape: $N \times 5$

Figures in `outputs/{case}/results/figures/`:

- `ch2_sumrel_geographic_bifurcation.png` — site-level map per Ch2 F1 demo.
  - x-axis, y-axis: geographic (Longitude, Latitude) over the water-body background
  - markers: shape encodes water body, color encodes the three-way SumRel split (green = lowest 20%, red = top 20%, gray = middle)
  - background: shapefile of DR AOC only (DR case) or full corridor (corridor case)
  - companion right panel: empirical CDF of SumRel with lower/upper threshold lines
  - layout: two-panel, 16 × 7 inches

- `ch2_maxrel_geographic_bifurcation.png` — same as above for MaxRel.

#### `process/p02_reference_validation.ipynb` (Ch2 F2)

Tables:

- `ch2_rda_validation_summary.xlsx` — per-subset RDA outcomes.
  - rows: (subset_id, subset_type, $m_{\mathrm{ref}}$, $\bar R^2_{\mathbf{S}_{R_b}}$, $\bar R^2_{\mathbf{c}_{R_b}}$, $F_{\mathbf{S}_{R_b}}$, $F_{\mathbf{c}_{R_b}}$, $p_{\mathbf{S}_{R_b}}$, $p_{\mathbf{c}_{R_b}}$, $\bar{\mathbf{c}}_{R_b}$)
  - shape: $(B+1) \times 10$
  - row 1 = the reference subset; rows 2..B+1 = the random subsets.

Figures (per chapter spec):

- `ch2_rda_r2_density.png`
  - x-axis: values of $\bar R^2_{\mathbf{S}_{R_b}}$
  - y-axis: empirical probability density
  - curve: smoothed density across $B$ random subsets
  - highlighted marker: $\bar R^2_{\mathbf{S}_{R_{\mathrm{ref}}}}$ of the least-stressed reference subset, drawn as a vertical line plus point

- `ch2_rda_pvalue_density.png` — same layout for the permutation p-value.

Artifacts (consumed by Ch3, Ch4):

- `A1.parquet` — augmented site-level table.
  - rows: (StationID, PC$_1$, …, PC$_m$, SumRel, MaxRel)
  - shape: $N \times (m + 2)$

- `A2.parquet` — reference subset membership indicator.
  - rows: (StationID, if_reference)
  - shape: $N \times 2$

### Chapter 3 workspace (`chapters/ch3/`)

#### `process/p03_reference_clusters.ipynb` (Ch3 F1)

Tables:

- `ch3_node_wise_anova.xlsx` (chapter spec)
  - rows: (split_id, $n_{\mathrm{left}}$, $n_{\mathrm{right}}$, taxon, $\bar x_{\mathrm{left}}$, $\bar x_{\mathrm{right}}$, F, p, $p_{\mathrm{FDR}}$)
  - shape: $((K-1) \times n_{\mathrm{sig\,taxa}}) \times 9$

- `ch3_finalized_anova_au.xlsx` (chapter spec)
  - rows: (taxon, SS$_{\mathrm{between}}$(df), SS$_{\mathrm{within}}$(df), F, p, $\bar x_{C_1}$, …, $\bar x_{C_K}$, AU$_{C_1}$, …, AU$_{C_K}$)
  - shape: $(16 + 2) \times (5 + 2K)$  (16 taxa rows + 2 summary rows)

Figures (per chapter spec):

- `ch3_ward_dendrogram.png`
  - x-axis: site labels of $m_{\mathrm{ref}}$ reference sites, leaves colored by the $K$ cluster labels
  - y-axis: linkage value $\Delta$ at each bifurcation
  - annotations: AU p-value at each of the $K-1$ bifurcation nodes producing the finalized clusters
  - legend: colors for the $K$ clusters

- `ch3_taxa_barplots.png`
  - x-axis: 16 taxon ticks, each holding $K$ bars
  - y-axis: mean relative concentration $\bar p_{jk}$ of taxon $j$ in cluster $k$
  - annotations: asterisks marking taxa with significant finalized-cluster ANOVA p-values
  - legend: colors for the $K$ clusters

Artifact:

- `A3.parquet`
  - rows: (StationID, cluster_label)
  - shape: $m_{\mathrm{ref}} \times 2$

#### `process/p04_concordance_consensus.ipynb` (Ch3 F2)

Tables:

- `ch3_consensus_margins.xlsx`
  - rows: (StationID, anchor_cluster, $\mu_i^{(T)}$, $\mu_i^{(E)}$, concordance_status)
  - shape: $m_{\mathrm{ref}} \times 5$

- `ch3_concordance_status_summary.xlsx` — value-counts of the four statuses.
  - rows: (status, count, percent)
  - shape: $4 \times 3$

Figure (per chapter spec):

- `ch3_concordance_scatter.png`
  - x-axis: $\mu_i^{(T)}$
  - y-axis: $\mu_i^{(E)}$
  - points: one per site, colored by anchor cluster label $C_j$
  - annotations: the four sign-pair quadrants shaded and labeled by concordance category (concordant, taxa-only stable, env-only stable, ambiguous)

Artifact:

- `A4.parquet`
  - rows: (StationID, cluster_label, $\mu_i^{(T)}$, $\mu_i^{(E)}$, concordance_status)
  - shape: $m_{\mathrm{ref}} \times 5$

#### `process/p05_env_classifier.ipynb` (Ch3 F3)

Tables (per chapter spec):

- `ch3_classifier_cv_confusion.xlsx`
- `ch3_stratified_confusion.xlsx` — confusion stratified by concordance status (the chapter's gating diagnostic).
- `ch3_posterior_probabilities.xlsx`
  - rows: (StationID, $P(C_1|e)$, …, $P(C_K|e)$, plausible_class_set)
  - shape: $N \times (K + 2)$
  - `plausible_class_set` stored as comma-separated string of cluster IDs.

Figures (per chapter spec):

- `ch3_pca_decision_regions_pc12.png`, `_pc13.png`, `_pc23.png` — three PC-pair panels.
  - axes: PCA scores (PC$_a$, PC$_b$) of the standardized $E$ matrix
  - background: classifier decision regions colored by predicted class
  - points: reference sites (colored by true Ward cluster) and non-reference sites (colored by predicted cluster), distinguished by marker shape
  - annotations: PCA loading arrows for the 5–6 environmental descriptors

Artifact:

- `A5.parquet`
  - rows: (StationID, $P(C_1|e)$, …, $P(C_K|e)$, predicted_class, plausible_class_set)
  - shape: $N \times (K + 3)$

### Chapter 4 workspace (`chapters/ch4/`)

#### `process/p06_braycurtis_with_poles.ipynb` (Ch4 F1)

Tables (per chapter spec):

- `ch4_pole_compositions.xlsx`
  - rows: (cluster $C_k$, pole_type, taxon$_1$, …, taxon$_{16}$)
  - shape: $2K \times (p + 2)$

- `ch4_pole_distances.xlsx`
  - rows: (StationID, $C_k$, $BC_{i, E_{\mathrm{ref}}^{(k)}}$, $BC_{i, E_{\mathrm{deg}}^{(k)}}$)
  - shape: $\sum_k m_k \times 4$

- `ch4_triangle_inequality.xlsx` (appendix table — marked table' in chapter spec)
  - rows: (cluster $C_k$, n_triples, n_violations, violation_rate)
  - shape: $K \times 4$

Figure (per chapter spec):

- `ch4_bc_dissim_histograms.png`
  - x-axis: Bray-Curtis dissimilarity value, ticks from 0 to 1
  - y-axis: count of site pairs
  - annotations: vertical line at $BC_{E_{\mathrm{ref}}^{(k)}, E_{\mathrm{deg}}^{(k)}}$ per panel
  - panels: one per community type $C_k$

Artifacts:

- `A6.parquet` — augmented within-type taxa matrices with poles appended.
  - rows: (StationID-or-pole-label, $C_k$, taxon$_1$, …, taxon$_{16}$)
  - shape: $\sum_k (m_k + 2) \times (p + 2)$

- `A7.pkl` — Python pickle of `dict[int, dict]`:
  ```python
  {k: {"D": np.ndarray (m_k+2, m_k+2),
       "labels": list[str],
       "ref_label": str, "deg_label": str}}
  ```

#### `process/p07_nmds_per_cluster.ipynb` (Ch4 F2)

Tables (per chapter spec):

- `ch4_nmds_fit_summary.xlsx`
  - rows: (cluster $C_k$, $q_k$, final_stress, stress_range_min, stress_range_max, iterations_to_convergence)
  - shape: $K \times 6$

- `ch4_stratified_residuals.xlsx` (appendix — table')
  - rows: (cluster $C_k$, pair_type, count, median$|r|$, IQR$|r|$, max$|r|$)
  - shape: $3K \times 6$

- `ch4_pole_geometry.xlsx` (appendix — table')
  - rows: (cluster $C_k$, $y_{\mathrm{ref},1}^{(k)}$, …, $y_{\mathrm{ref},q_{\max}}^{(k)}$, $y_{\mathrm{deg},1}^{(k)}$, …, $y_{\mathrm{deg},q_{\max}}^{(k)}$, axis_length)
  - shape: $K \times (2 q_{\max} + 2)$

Figures (per chapter spec):

- `ch4_shepard_diagrams.png`
  - x-axis: original Bray-Curtis dissimilarity $d_{ij}$
  - y-axis: ordination Euclidean distance $\delta_{ij}$
  - points: colored by pair type (pole-to-pole, real-to-pole, real-to-real)
  - overlay: monotone disparity curve $\hat d_{ij}$
  - panels: one per $C_k$

- `ch4_nmds_stress_scree.png`
  - x-axis: ordination dimensionality $q \in \{1, 2, 3, 4, 5\}$
  - y-axis: final stress at that $q$
  - reference lines: horizontal at stress = 0.10 and 0.20
  - panels: one per $C_k$

- `ch4_nmds_ordination.png`
  - x-axis: NMDS axis 1
  - y-axis: NMDS axis 2
  - points: $m_k$ real sites in grey, $E_{\mathrm{ref}}^{(k)}$ as green star, $E_{\mathrm{deg}}^{(k)}$ as red star
  - annotations: line segment connecting $\mathbf{y}_{\mathrm{ref}}^{(k)}$ to $\mathbf{y}_{\mathrm{deg}}^{(k)}$
  - panels: one per $C_k$

Artifact:

- `A8.pkl` — `dict[int, dict]`:
  ```python
  {k: {"Y": np.ndarray (m_k+2, q_k),
       "labels": list[str],
       "ref_label": str, "deg_label": str,
       "stress": float, "q": int}}
  ```

#### `process/p08_zci_projection.ipynb` (Ch4 F3)

Tables (per chapter spec):

- `ch4_zci_distribution.xlsx`
  - rows: (cluster $C_k$, min_zci, max_zci, n_sites_below_0, n_sites_above_1, median_residual)
  - shape: $K \times 6$

- `ch4_zci_contamination_correlation.xlsx`
  - rows: (cluster $C_k$, spearman_rho, p_value)
  - shape: $K \times 3$

- `ch4_zci_per_site.xlsx` — *documental* wide form (one row per site).
  - rows: (StationID, ZCI_C$_1$, residual_C$_1$, …, ZCI_C$_K$, residual_C$_K$)
  - shape: $N \times (1 + 2K)$
  - cells are NaN where the site is not plausibly in that cluster.
  - **Bridging note** (see §5).

Figures (per chapter spec):

- `ch4_zci_ordination_overlay.png`
  - axes: NMDS axis 1 and 2
  - points: real sites colored by ZCI value (continuous colormap from ZCI = 0 to ZCI = 1)
  - $E_{\mathrm{ref}}^{(k)}$ at green end, $E_{\mathrm{deg}}^{(k)}$ at red end
  - annotations: gradient axis line, perpendicular dashed segments from each site to its foot on the axis
  - panels: one per $C_k$

- `ch4_zci_histograms.png`
  - x-axis: ZCI value, ticks at 0 and 1
  - y-axis: site count
  - reference lines: vertical at ZCI = 0 and ZCI = 1
  - panels: one per $C_k$

Artifact:

- `A9.parquet` — internal *long* form.
  - rows: (StationID, $C_k$, ZCI, residual)
  - shape: $\sum_k m_k \times 4$
  - one site may have multiple rows (one per plausible cluster).

---

## Part 5 — The ZCI bridging step

`p08` produces two views of the same data, and they go to different places:

- **Internal/working form** — `A9.parquet` in `chapters/ch4/outputs/{case}/artifacts/`. **Long form**: one row per (site, cluster). Easy to compute, easy to filter, easy to join with `A1`/`A5`. Stays inside the artifact pipeline.

- **Documental/chapter form** — `ch4_zci_per_site.xlsx` in `chapters/ch4/outputs/{case}/results/tables/`. **Wide form**: one row per site, with `(ZCI_C_k, residual_C_k)` column pairs. This is what the chapter narrative renders.

The bridging is one function call inside `p08`:

```python
A9      = projection.compute_zci(A8, A1)                # long form
zci_doc = interpreters.zci_pivot(A9, n_clusters=K)      # wide form
io.save_artifact(A9, "A9")
io.save_table(zci_doc, "ch4_zci_per_site")
```

`zci_pivot()` is one function in `base/interpreters/zci_pivot.py` — 15 lines. It does `pd.pivot_table(...)` and flattens the resulting MultiIndex columns to `ZCI_C1, residual_C1, ZCI_C2, ...`.

---

## Part 6 — Cases

```python
# base/config.py
@dataclass(frozen=True)
class Case:
    name: str
    water_bodies: tuple[str, ...]
    require_velocity: bool
    env_columns: tuple[str, ...]
    n_sites_expected: int
    m_ref: int                  # case-specific

CASES = {
    "DR":       Case("DR",       ("DR",),                True,  ENV_FULL,         213, 43),
    "corridor": Case("corridor", ("DR","LSC","SCR"),     False, ENV_NO_VELOCITY,  310, 62),
}
```

- DR strict: 213 sites, 6 env columns including Velocity, $m_{\mathrm{ref}} = 43$.
- Corridor: 310 sites, 5 env columns (Velocity excluded), $m_{\mathrm{ref}} = 62$.
- Switch by calling `config.set_case("DR")` in Cell 1 of each notebook. Kernel restart to switch in interactive use. `run_all.py --case both` runs fresh subprocess per case.

---

## Part 7 — Maps and shapefiles

`data/maps/` requires five subfolders (copied from the existing project):

```
data/maps/
├── lake_stclair/lake_stclair.shp  (+ .dbf, .shx, .prj, .cpg)
├── lake_erie/lake_erie.shp        (+ ...)
├── lake_huron/lake_huron.shp      (+ ...)
├── detroit_river_aoc_shapefile/AOC_MI_Detroit_2021.shp  (+ ...)
└── aoc_mi_stclair_2021/AOC_MI_StClair_2021.shp          (+ ...)
```

Two plotting functions in `base/plotting/`:

- `corridor_map.plot_corridor_bifurcation(scores, lat, lon, waterbody, maps_dir)` — used when `config.current().name == "corridor"`. Full Huron-Erie Corridor background.
- `dr_map.plot_dr_bifurcation(scores, lat, lon, waterbody, maps_dir)` — used when `config.current().name == "DR"`. Detroit River AOC only.

A thin dispatcher `plotting.bifurcation_map(...)` picks the right one based on the active case. `p01` calls just this dispatcher.

Dependencies: `geopandas` (drags in `fiona`, `pyproj`, `shapely`). The heaviest dependency in the project; document in `pyproject.toml`.

---

## Part 8 — The four-cell notebook template

Every notebook in `chapters/*/process/` has exactly four code cells plus markdown:

```python
# ── Cell 1: SETUP ─────────────────────────────────────────────────────────
from base import config, io, log
from base.bridging import select
from base.modeling import dissim, hclust, anova, pvclust
from base.plotting import dendrogram, barplots, style

config.set_case("DR")           # ← the only case-aware line
style.apply_thesis_style()
logger = log.get_logger(__name__)

# ── Cell 2: INPUTS ────────────────────────────────────────────────────────
T  = io.load_metadata("T")
A2 = io.load_artifact("A2")     # resolved to chapters/ch2/outputs/DR/artifacts/A2.parquet
T_ref = select.by_bool_column(T.join(A2[["if_reference"]]), "if_reference")

# ── Cell 3: PROCESS ───────────────────────────────────────────────────────
D_ref    = dissim.manhattan(T_ref)
ward     = hclust.ward(D_ref, n_clusters=config.K)
node_an  = anova.node_wise(T_ref, ward.bifurcations)
final_an = anova.finalized(T_ref, ward.labels)
pvc      = pvclust.run(T_ref, dissim="manhattan", method="ward",
                       n_boot=config.B_PVCLUST, scales=config.PVCLUST_SCALES,
                       seed=config.SEED)

# ── Cell 4: OUTPUTS ───────────────────────────────────────────────────────
io.save_artifact(ward.labels_table, "A3")    # → chapters/ch3/outputs/DR/artifacts/A3.parquet
io.save_table(node_an.to_table(),   "ch3_node_wise_anova")
io.save_table(final_an.to_table().join(pvc.au_by_cluster), "ch3_finalized_anova_au")
io.save_figure(dendrogram.plot(ward, au_pvalues=pvc.au_by_node), "ch3_ward_dendrogram")
io.save_figure(barplots.taxa_by_cluster(T_ref, ward.labels,
                                         sig_taxa=final_an.significant),
               "ch3_taxa_barplots")
```

The same notebook works for both cases — only the `set_case` argument changes.

---

## Part 9 — Pending decisions

These are the only open items. Each has a recommendation; confirm or override before the agent starts.

| # | Decision | Recommended |
|---|----------|-------------|
| 1 | Velocity column name spelling in `environmental.xlsx` — pick one canonical form | `Velocity at bottom (m/sec)` (single space, fixed typo) |
| 2 | `sample_info` is a separate file (not folded into `chemical.xlsx`)? | yes, separate file |
| 3 | DR strict 213 sites, no imputation | **confirmed** |
| 4 | $K = 3$ as a hard config constant | yes |
| 5 | $m_{\mathrm{ref}} = \lfloor 0.20 N\rfloor$ → 43 (DR), 62 (corridor) | yes |
| 6 | PCA rotation in Ch2 F1 — varimax (resolves prose/code inconsistency) | varimax |
| 7 | Pole size in Ch4 F1 = $\lfloor 0.20 m_k\rfloor$, floor at 3 | yes |
| 8 | NMDS stress thresholds 0.10 / 0.20, escalate $q$ if final stress > 0.20 | yes |
| 9 | Multi-cluster-per-site → A9 in long form, pivoted to wide form for docs | yes |
| 10 | `outputs/{case}/results/` committed to git, `outputs/{case}/artifacts/` gitignored | yes |
| 11 | Chapter pages default to DR with corridor toggle (built by `build_skeleton_site.py`) | yes |
| 12 | `inputs/` folders in each chapter exist as scaffolding (empty + README) | yes |
| 13 | Tables = xlsx, figures = png at 300 dpi | yes |

---

## Part 10 — Build order for the agent

12 PR-sized steps in execution order. Each ends with a verification command.

| Step | Build                                                                     | Verify                                            |
|------|---------------------------------------------------------------------------|---------------------------------------------------|
| 1    | `data/raw/*.xlsx` (four plain files exported from current merged data)   | `python -c "import pandas as pd; [pd.read_excel(p) for p in ['data/raw/sample_info.xlsx', ...]]"` |
| 2    | `data/maps/` copied from existing repo                                    | `ls data/maps/*/*.shp` shows 5 files               |
| 3    | `base/{config,io,schemas,log}.py` + artifact registry                    | `pytest tests/test_base/test_plumbing.py`          |
| 4    | `bootstrap/p00_prepare_inputs.ipynb` runs for DR and corridor             | `data/prepared/{DR,corridor}/{M,E,T,sample_info}.parquet` exist with correct shapes |
| 5    | `base/transforms/`, `base/bridging/`                                      | `pytest tests/test_base/test_bridging.py`          |
| 6    | `base/modeling/{pca,dissim,hclust}.py`                                    | `pytest tests/test_base/test_modeling_core.py`     |
| 7    | `base/plotting/{style,corridor_map,dr_map,ecdf}.py`                       | manual inspection of one sample figure             |
| 8    | `chapters/ch2/process/p01.ipynb` + `p02.ipynb` for both cases             | both cases produce all Ch2 outputs in Part 4       |
| 9    | `base/modeling/{anova,pvclust,consensus,classifiers}.py`                 | `pytest tests/test_base/test_modeling_full.py`     |
| 10   | `chapters/ch3/process/p03,p04,p05.ipynb` for both cases                  | both cases produce all Ch3 outputs                 |
| 11   | `base/modeling/{nmds,projection}.py` + `interpreters/zci_pivot.py`       | `pytest tests/test_base/test_nmds.py`              |
| 12   | `chapters/ch4/process/p06,p07,p08.ipynb` for both cases                  | both cases produce all Ch4 outputs                 |
| 13   | `scripts/run_all.py` + `_manifest.json` writing                          | `python scripts/run_all.py --case both` clean run  |
| 14   | Update `scripts/build_skeleton_site.py` for the new layout (chapter case toggle) | `python scripts/build_skeleton_site.py` regenerates `docs/` |

Optional Step 15: an `rpy2`-backed test comparing Python pvclust AU values against R `pvclust` on a fixed seed. Marked `@pytest.mark.r_optional`.

---

## Part 11 — What the agent does first

Before writing any code:

1. **Export the four plain tables.** Read `merged_310_sites_taxa_chemical_environmental_data.xlsx` once, split by group (`sample_info`, `chemical`, `environmental`, `taxa`), rename the `environemntal` typo, write four xlsx files to `data/raw/`. Single header row each. `StationID` as the row index. Do not retain MultiIndex columns. Stop and confirm shapes match Part 3 before continuing.

2. **Verify the maps folder.** Locate the shapefiles in the existing project (under whichever directory `src/zci/viz/map_plots.py` currently reads from) and copy them to `data/maps/` preserving the five subfolder names. Stop and report if any are missing.

3. **Confirm the 13 pending decisions in Part 9.** Apply the recommendations as defaults if no explicit override is given.

Then proceed with Step 3 of Part 10.

---

## Part 12 — Summary of changes from the prior plan

What changed:
- **Layout**: flat (`artifacts/DR/`, `results/DR/`) → chapter-first (`chapters/ch2/outputs/DR/{artifacts,results}/`).
- **Inputs**: one merged MultiIndex xlsx → four plain xlsx (`sample_info`, `chemical`, `environmental`, `taxa`).
- **Notebook location**: `notebooks/` → `chapters/ch*/process/`. The notebook *is* the process and lives inside the process folder.
- **Figure protocol**: the `src/zci/viz/*` ports → chapter notebook specs. Existing code stays as a visual reference in `_archive/zci_legacy/`.
- **Artifact paths**: notebooks no longer construct paths. A *producer registry* in `config.py` maps each artifact name to its producer chapter. `io.load_artifact("A3")` resolves automatically.

What stayed:
- The `base/` package and its internal structure (Transformations, Bridging tools, Models, Interpreters, Plotting — matching the Architecture vocabulary).
- The four-cell thin-notebook template.
- The case-config design (DR and corridor switchable via one config call).
- The constants table (seeds, $K$, $m_{\mathrm{ref}}$, bootstrap counts, NMDS thresholds, pole sizes).
- Python everywhere, with one optional R-verification test for pvclust.
- Output formats: xlsx for tables, png at 300 dpi for figures.
- The DR / corridor case-toggle on chapter pages.
