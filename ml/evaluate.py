# -*- coding: utf-8 -*-
"""
evaluate.py
-----------
Phase 3 -- Index Validation & Sensitivity Analysis

1. Validates the Flood Susceptibility Index (FSI) against the 25 GMDA
   waterlogging points: evaluates what proportion of surveyed waterlogged
   locations coincide with High or Very High susceptibility grid cells.
2. Conducts sensitivity analysis: perturbs feature weights by +/- 20%
   to evaluate model stability and rank robustness.
3. Outputs data/reports/fsi_sensitivity_report.json and
   data/reports/validation_report.json.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from datetime import datetime, timezone

import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from shapely.geometry import Point

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "data" / "reports"
MODELS = ROOT / "models"


def validate_against_gmda_observations(df: pd.DataFrame, cfg: dict) -> dict:
    """Computes spatial overlap between GMDA waterlogged points and FSI susceptibility classes."""
    log.info("Validating FSI against GMDA waterlogging field survey points...")
    obs_file = PROCESSED / "gmda_survey_points.geojson"
    if not obs_file.exists():
        return {"status": "skipped", "reason": "gmda_survey_points.geojson not found"}

    obs_gdf = gpd.read_file(obs_file)
    waterlog_pts = obs_gdf[obs_gdf["surveytype"] == "Waterlogging"].copy()
    total_pts = len(waterlog_pts)

    if total_pts == 0:
        return {"status": "no_points"}

    # Spatial join or nearest neighbor lookup
    # df has centroid_lon, centroid_lat, fsi, fsi_class
    matches = []
    for _, pt in waterlog_pts.iterrows():
        coords = pt.geometry.coords[0]
        lon, lat = coords[0], coords[1]
        dist_sq = (df["centroid_lon"] - lon) ** 2 + (df["centroid_lat"] - lat) ** 2
        nearest_row = df.loc[dist_sq.idxmin()]
        matches.append({
            "objectid": pt.get("objectid"),
            "location": [round(lon, 5), round(lat, 5)],
            "cell_id": nearest_row["cell_id"],
            "fsi": round(float(nearest_row["fsi"]), 4),
            "fsi_class": nearest_row["fsi_class"],
        })

    class_counts = {}
    for m in matches:
        cls = m["fsi_class"]
        class_counts[cls] = class_counts.get(cls, 0) + 1

    high_or_vhigh = class_counts.get("high", 0) + class_counts.get("very_high", 0)
    consistency_rate = round(high_or_vhigh / max(total_pts, 1) * 100, 1)

    validation_result = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "total_waterlogging_points": total_pts,
        "points_in_high_or_very_high_susceptibility": high_or_vhigh,
        "spatial_consistency_rate_pct": consistency_rate,
        "distribution_across_classes": class_counts,
        "evaluation_type": "Qualitative Spatial Consistency Check (Empirical reference, not supervised test)",
        "interpretation": (
            f"{consistency_rate}% of surveyed waterlogged locations in Gurugram fall into cells "
            "designated as High or Very High flood susceptibility by the framework."
        ),
        "point_breakdown": matches[:10],  # first 10 for provenance inspection
    }

    out_file = REPORTS / "validation_report.json"
    out_file.write_text(json.dumps(validation_result, indent=2), encoding="utf-8")
    log.info("Validation complete: %s%% consistency with GMDA points. Saved to %s", consistency_rate, out_file.name)
    return validation_result


def conduct_sensitivity_analysis(df: pd.DataFrame, cfg: dict):
    """Perturbs individual feature weights by +/-20% and computes Spearman rank correlations."""
    log.info("Running FSI sensitivity analysis across parameter weight space...")
    base_weights = cfg["weights"]
    inverted = set(cfg["inverted_features"])

    # Prepare normalized feature matrix
    norm_matrix = {}
    for feat in base_weights.keys():
        s = df[feat].astype(float).values
        mn, mx = np.nanmin(s), np.nanmax(s)
        norm = (s - mn) / (mx - mn) if mx > mn else np.zeros_like(s)
        if feat in inverted:
            norm = 1.0 - norm
        norm_matrix[feat] = norm

    base_fsi = df["fsi"].values
    sensitivity_results = {}

    for feat in base_weights.keys():
        current_w = base_weights[feat]
        # Test +20% and -20%
        for delta_name, factor in [("plus_20_pct", 1.2), ("minus_20_pct", 0.8)]:
            perturbed_weights = dict(base_weights)
            perturbed_weights[feat] = current_w * factor

            # Renormalize sum to 1.0
            total_w = sum(perturbed_weights.values())
            renorm_weights = {k: v / total_w for k, v in perturbed_weights.items()}

            # Calculate perturbed FSI
            perturbed_fsi = np.zeros(len(df))
            for f_key, w_val in renorm_weights.items():
                perturbed_fsi += w_val * norm_matrix[f_key]

            # Spearman rank correlation with baseline
            corr, _ = spearmanr(base_fsi, perturbed_fsi)
            key = f"{feat}_{delta_name}"
            sensitivity_results[key] = {
                "feature": feat,
                "variation": delta_name,
                "new_weight": round(renorm_weights[feat], 4),
                "spearman_rank_correlation": round(float(corr), 4),
                "fsi_mean_shift": round(float(np.mean(perturbed_fsi) - np.mean(base_fsi)), 4),
            }

    # Summary
    correlations = [v["spearman_rank_correlation"] for v in sensitivity_results.values()]
    summary = {
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "total_perturbation_scenarios": len(sensitivity_results),
        "min_spearman_rank_correlation": min(correlations),
        "max_spearman_rank_correlation": max(correlations),
        "average_spearman_rank_correlation": round(float(np.mean(correlations)), 4),
        "stability_assessment": (
            "Robust" if min(correlations) > 0.95 else ("Moderate" if min(correlations) > 0.85 else "Sensitive")
        ),
        "details": sensitivity_results,
    }

    out_file = REPORTS / "fsi_sensitivity_report.json"
    out_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log.info("Sensitivity analysis complete. Mean Spearman rho: %.4f (Status: %s)",
             summary["average_spearman_rank_correlation"], summary["stability_assessment"])


def main():
    pq_file = PROCESSED / "features.parquet"
    cfg_file = MODELS / "fsi_config.json"

    if not pq_file.exists() or not cfg_file.exists():
        log.error("Prerequisites missing. Run build_features.py first.")
        return

    df = pd.read_parquet(pq_file)
    cfg = json.loads(cfg_file.read_text(encoding="utf-8"))

    validate_against_gmda_observations(df, cfg)
    conduct_sensitivity_analysis(df, cfg)
    log.info("Phase 3 evaluation completed.")


if __name__ == "__main__":
    main()
