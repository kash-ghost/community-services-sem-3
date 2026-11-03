# METHODOLOGY
# Flood Vulnerability Prediction Framework — Gurugram, Haryana

## 1. Study Rationale

Gurugram (Gurgaon), Haryana, India, faces recurring urban flooding during the monsoon
season (June–September). Rapid impervious surface expansion, encroached natural drainage
channels, and flat micro-topography combine to cause significant waterlogging annually.

This project estimates relative flood *susceptibility* — not actual flood probability —
using publicly available geographic and meteorological data. The output is a
spatial index for decision-support purposes only.

---

## 2. Prediction Mode: Susceptibility Index

### Why Not Supervised Machine Learning?

The GMDA Flood Survey FeatureServer (the primary candidate for observed flood labels)
was audited on 2026-10-20. Findings:

- Total records: **25**
- Records with a survey date: **0** (surveydate NULL for all records)
- Records with zone/ward populated: **1**
- Available negative labels (confirmed non-flooded locations): **0**

With only 25 undated, poorly attributed positive-only observations, constructing valid
supervised classification labels is not feasible. Any attempt to train and evaluate a
Random Forest classifier on this data would produce misleading results.

**Decision:** Implement a transparent Flood Susceptibility Index (FSI). The ML training
pipeline is scaffolded and will activate automatically when sufficient labelled data
are provided.

### When Supervised ML Will Be Enabled

Supervised training will activate when `data/processed/labels.parquet` contains at
minimum 200 labelled grid cells with:
- `flooded` ∈ {0, 1}
- A documented derivation method for each label
- A temporal column indicating the observation period
- At least 20% positive class examples

---

## 3. Flood Susceptibility Index (FSI) — Definition

The FSI is calculated per 500m × 500m grid cell across the study area.

### 3.1 Prediction Unit

Grid cells of 500m × 500m are constructed in EPSG:32643 (UTM Zone 43N, meters),
then reprojected to EPSG:4326 for storage and display.

Study boundary (EPSG:4326): [76.80°E, 28.20°N, 77.25°E, 28.55°N]

### 3.2 Features

| Feature ID | Name | Description | Source | Expected Direction |
|---|---|---|---|---|
| F1 | `elevation_m` | Median elevation within cell (m) | Copernicus DEM GLO-30 | Lower → higher susceptibility |
| F2 | `slope_deg` | Mean slope within cell (°) | Derived from DEM | Flatter → higher susceptibility |
| F3 | `built_up_frac` | Fraction of built-up land cover | ESA WorldCover 2021 | Higher → higher susceptibility |
| F4 | `veg_frac` | Fraction of vegetation cover | ESA WorldCover 2021 | Higher → lower susceptibility |
| F5 | `water_frac` | Fraction of permanent water bodies | ESA WorldCover 2021 | Higher → higher susceptibility |
| F6 | `dist_to_water_m` | Distance to nearest permanent water body (m) | ESA WorldCover / OSM | Closer → higher susceptibility |
| F7 | `dist_to_drain_m` | Distance to nearest mapped waterway (m) | OSM | Closer → higher susceptibility |
| F8 | `monsoon_rainfall_mm` | Mean annual June–September total rainfall (mm) | Open-Meteo / IMD | Higher → higher susceptibility |

Note: F8 (rainfall) is spatially uniform at the Open-Meteo resolution (~9km) and
will provide minimal spatial differentiation across the study area. It is included
for completeness and will have its weight reviewed during sensitivity analysis.

### 3.3 Normalization

Each feature is rank-normalized to [0, 1] within the study area:
- Features where higher = more susceptible: normalized directly
- Features where lower = more susceptible (elevation, slope, dist_to_water, dist_to_drain):
  inverted (1 - normalized_rank)

Normalization formula: `x_norm = (x - x_min) / (x_max - x_min)`

### 3.4 Weights

Initial weights derived from Arya & Kumar (2023) AHP study for Gurugram:

| Feature | Weight |
|---|---|
| elevation_m | 0.30 |
| slope_deg | 0.20 |
| built_up_frac | 0.15 |
| dist_to_water_m | 0.15 |
| dist_to_drain_m | 0.10 |
| veg_frac | 0.05 |
| water_frac | 0.03 |
| monsoon_rainfall_mm | 0.02 |

Weights sum to 1.00. Stored in `models/fsi_config.json`.

### 3.5 FSI Calculation

```
FSI_i = sum(w_j * x_norm_i_j for j in features)
```

FSI ∈ [0, 1]. Higher FSI = higher estimated susceptibility.

### 3.6 Classification Thresholds

| Class | FSI Range | Label |
|---|---|---|
| Low | 0.00–0.25 | Low Susceptibility |
| Moderate | 0.25–0.50 | Moderate Susceptibility |
| High | 0.50–0.75 | High Susceptibility |
| Very High | 0.75–1.00 | Very High Susceptibility |

Thresholds are equal-interval, not quantile-based, for transparency.

---

## 4. Sensitivity Analysis

The FSI weights are varied ±20% (one feature at a time, others re-normalized) to
assess how sensitive the spatial pattern is to weighting assumptions.

Output: `data/reports/fsi_sensitivity_report.json`

---

## 5. Validation Against GMDA Points

The 25 GMDA waterlogging points are used as an independent spatial overlay.
For each point, the FSI of the containing grid cell is extracted.

Evaluation: What proportion of GMDA waterlogging points fall in cells with
FSI ≥ 0.50 (High or Very High susceptibility)?

This is a **qualitative spatial consistency check**, not a rigorous validation.
It is explicitly labelled as such in the frontend and documentation.

---

## 6. Machine Learning Training Scaffold

`ml/train.py` performs the following checks:
1. Reads `data/processed/labels.parquet`
2. Validates minimum sample size (≥ 200), class balance, and temporal columns
3. If valid: trains Logistic Regression (baseline) and Random Forest with spatial cross-validation
4. If invalid: logs specific failure reason and exits with code 1 (no model saved)

---

## 7. Limitations

1. FSI is a heuristic estimate, not a calibrated flood probability
2. DEM is a surface model; urban elevation is inflated by buildings
3. Land cover is from 2021; Gurugram urbanisation is rapid
4. OSM drainage is incomplete for Gurugram
5. Rainfall is spatially uniform at 9km resolution within the study area
6. The 25 GMDA points cannot validate the FSI rigorously
7. The study area covers GMDA jurisdiction; peri-urban and district boundary areas may differ in data quality
