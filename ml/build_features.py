# -*- coding: utf-8 -*-
"""
build_features.py
-----------------
Phase 2 -- Feature Engineering & FSI Calculation

Generates 500m x 500m grid cells across the Gurugram study area,
extracts physical and environmental features from authoritative datasets:
  F1: elevation_m (median DEM elevation)
  F2: slope_deg (mean surface slope)
  F3: built_up_frac (ESA WorldCover 10m built-up proportion)
  F4: veg_frac (ESA WorldCover vegetation proportion)
  F5: water_frac (ESA WorldCover permanent water proportion)
  F6: dist_to_water_m (distance to GMDA 1980 water bodies)
  F7: dist_to_drain_m (distance to GMDA main drain trunk legs)
  F8: monsoon_rainfall_mm (ERA5-Land monsoon rainfall baseline)

Computes the Flood Susceptibility Index (FSI) for each cell using
the AHP methodology weights from Arya & Kumar (2023).

Outputs:
  data/processed/features.parquet
  data/processed/features.csv
  data/processed/grid_cells.geojson
  models/fsi_config.json
  data/reports/feature_report.json
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
import sys
from datetime import datetime, timezone

import geopandas as gpd
import numpy as np
import pandas as pd
from pyproj import Transformer
import rasterio
from rasterio.windows import from_bounds
from shapely.geometry import box, Point
from shapely.ops import unary_union

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
MODELS = ROOT / "models"
REPORTS = ROOT / "data" / "reports"
MODELS.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

# Study bounding box in WGS84
BBOX_WGS84 = (76.80, 28.20, 77.25, 28.55)  # xmin, ymin, xmax, ymax
CELL_SIZE_M = 500
UTM_CRS = "EPSG:32643"  # UTM Zone 43N (meters)
WGS84_CRS = "EPSG:4326"

# ESA WorldCover class codes
WC_BUILT_UP = 50
WC_WATER = 80
WC_VEG = [10, 20, 30]

# Multi-criteria AHP weights (Arya & Kumar 2023)
FSI_WEIGHTS = {
    "elevation_m":         0.30,
    "slope_deg":           0.20,
    "built_up_frac":       0.15,
    "dist_to_water_m":     0.15,
    "dist_to_drain_m":     0.10,
    "veg_frac":            0.05,
    "water_frac":          0.03,
    "monsoon_rainfall_mm": 0.02,
}

# Factors where lower value indicates higher flood susceptibility
INVERTED_FEATURES = {"elevation_m", "slope_deg", "dist_to_water_m", "dist_to_drain_m", "veg_frac"}


def create_grid():
    """Generates uniform 500m cells in UTM 43N and transforms to WGS84."""
    transformer_to_utm = Transformer.from_crs(WGS84_CRS, UTM_CRS, always_xy=True)
    transformer_to_wgs = Transformer.from_crs(UTM_CRS, WGS84_CRS, always_xy=True)

    xmin_u, ymin_u = transformer_to_utm.transform(BBOX_WGS84[0], BBOX_WGS84[1])
    xmax_u, ymax_u = transformer_to_utm.transform(BBOX_WGS84[2], BBOX_WGS84[3])

    xmin_u = np.floor(xmin_u / CELL_SIZE_M) * CELL_SIZE_M
    ymin_u = np.floor(ymin_u / CELL_SIZE_M) * CELL_SIZE_M
    xmax_u = np.ceil(xmax_u / CELL_SIZE_M) * CELL_SIZE_M
    ymax_u = np.ceil(ymax_u / CELL_SIZE_M) * CELL_SIZE_M

    cols = int((xmax_u - xmin_u) / CELL_SIZE_M)
    rows = int((ymax_u - ymin_u) / CELL_SIZE_M)
    log.info("Constructing grid: %d columns x %d rows = %d cells", cols, rows, cols * rows)

    cells_utm = []
    ids = []
    cents_lon = []
    cents_lat = []

    for r in range(rows):
        for c in range(cols):
            x0 = xmin_u + c * CELL_SIZE_M
            y0 = ymin_u + r * CELL_SIZE_M
            cells_utm.append(box(x0, y0, x0 + CELL_SIZE_M, y0 + CELL_SIZE_M))
            ids.append(f"C_{r:03d}_{c:03d}")

            cx = x0 + CELL_SIZE_M / 2.0
            cy = y0 + CELL_SIZE_M / 2.0
            clon, clat = transformer_to_wgs.transform(cx, cy)
            cents_lon.append(round(clon, 6))
            cents_lat.append(round(clat, 6))

    gdf_utm = gpd.GeoDataFrame({
        "cell_id": ids,
        "centroid_lon": cents_lon,
        "centroid_lat": cents_lat,
        "geometry": cells_utm
    }, crs=UTM_CRS)

    gdf_wgs84 = gdf_utm.to_crs(WGS84_CRS)
    return gdf_utm, gdf_wgs84


def compute_dem_features(gdf_wgs84) -> pd.DataFrame:
    """Extracts median elevation and computes surface slope from dem_gurugram.tif."""
    dem_file = PROCESSED / "dem_gurugram.tif"
    if not dem_file.exists():
        log.warning("dem_gurugram.tif not found; setting DEM features to NaN")
        return pd.DataFrame({"cell_id": gdf_wgs84["cell_id"], "elevation_m": np.nan, "slope_deg": np.nan})

    log.info("Extracting DEM elevation and slope for %d cells...", len(gdf_wgs84))
    elevations = []
    slopes = []

    with rasterio.open(dem_file) as src:
        nodata = src.nodata if src.nodata is not None else -9999
        res_m = abs(src.transform.a) * 111320.0

        for geom in gdf_wgs84.geometry:
            b = geom.bounds  # minx, miny, maxx, maxy (lon, lat)
            try:
                win = from_bounds(*b, transform=src.transform)
                arr = src.read(1, window=win).astype(np.float32)
                valid = (arr != nodata) & (~np.isnan(arr))
                if np.any(valid):
                    v = arr[valid]
                    elevations.append(float(np.median(v)))

                    # Slope in degrees
                    if arr.shape[0] > 1 and arr.shape[1] > 1:
                        dy = np.gradient(arr, axis=0) / max(res_m, 1.0)
                        dx = np.gradient(arr, axis=1) / max(res_m, 1.0)
                        sl = np.degrees(np.arctan(np.sqrt(dx**2 + dy**2)))
                        slopes.append(float(np.nanmean(sl)))
                    else:
                        slopes.append(0.0)
                else:
                    elevations.append(np.nan)
                    slopes.append(np.nan)
            except Exception:
                elevations.append(np.nan)
                slopes.append(np.nan)

    log.info("DEM extracted. Valid elev count: %d, median: %.1f m",
             sum(~np.isnan(elevations)), float(np.nanmedian(elevations)))
    return pd.DataFrame({
        "cell_id": gdf_wgs84["cell_id"].values,
        "elevation_m": np.round(elevations, 2),
        "slope_deg": np.round(slopes, 2),
    })


def compute_landcover_features(gdf_wgs84) -> pd.DataFrame:
    """Calculates land cover proportions from 10m ESA WorldCover."""
    lc_file = PROCESSED / "landcover_gurugram.tif"
    if not lc_file.exists():
        log.warning("landcover_gurugram.tif not found; setting LC features to NaN")
        return pd.DataFrame({
            "cell_id": gdf_wgs84["cell_id"],
            "built_up_frac": np.nan,
            "veg_frac": np.nan,
            "water_frac": np.nan,
        })

    log.info("Extracting 10m land cover composition for %d cells...", len(gdf_wgs84))
    bu_frac = []
    vg_frac = []
    wt_frac = []

    with rasterio.open(lc_file) as src:
        for geom in gdf_wgs84.geometry:
            b = geom.bounds
            try:
                win = from_bounds(*b, transform=src.transform)
                arr = src.read(1, window=win)
                valid = arr > 0
                tot = int(np.sum(valid))
                if tot > 0:
                    bu_frac.append(float(np.sum(arr == WC_BUILT_UP)) / tot)
                    vg_frac.append(float(np.sum(np.isin(arr, WC_VEG))) / tot)
                    wt_frac.append(float(np.sum(arr == WC_WATER)) / tot)
                else:
                    bu_frac.append(0.0)
                    vg_frac.append(0.0)
                    wt_frac.append(0.0)
            except Exception:
                bu_frac.append(np.nan)
                vg_frac.append(np.nan)
                wt_frac.append(np.nan)

    log.info("Land cover extracted. Mean built-up: %.3f, veg: %.3f, water: %.4f",
             float(np.nanmean(bu_frac)), float(np.nanmean(vg_frac)), float(np.nanmean(wt_frac)))
    return pd.DataFrame({
        "cell_id": gdf_wgs84["cell_id"].values,
        "built_up_frac": np.round(bu_frac, 4),
        "veg_frac": np.round(vg_frac, 4),
        "water_frac": np.round(wt_frac, 4),
    })


def compute_distance_features(gdf_utm) -> pd.DataFrame:
    """Computes exact Euclidean distance (in meters) to nearest waterbody and drainage channel."""
    log.info("Computing Euclidean distances to hydrology infrastructure...")
    cents = gdf_utm.copy()
    cents["geometry"] = gdf_utm.geometry.centroid

    # 1. Water bodies
    wb_file = PROCESSED / "gmda_waterbodies_1980.geojson"
    if not wb_file.exists():
        wb_file = PROCESSED / "osm_water_polygons_gurugram.geojson"

    dist_w = np.full(len(gdf_utm), np.nan)
    if wb_file.exists():
        wgdf = gpd.read_file(wb_file).to_crs(UTM_CRS)
        wgdf = wgdf[wgdf.is_valid & ~wgdf.is_empty]
        if len(wgdf) > 0:
            w_union = unary_union(wgdf.geometry)
            dist_w = np.array([pt.distance(w_union) for pt in cents.geometry])
            log.info("Distance to water: min %.0f m, mean %.0f m, max %.0f m",
                     float(np.nanmin(dist_w)), float(np.nanmean(dist_w)), float(np.nanmax(dist_w)))

    # 2. Main trunk drains
    drain_file = PROCESSED / "gmda_drain_legs.geojson"
    if not drain_file.exists():
        drain_file = PROCESSED / "osm_waterways_gurugram.geojson"

    dist_d = np.full(len(gdf_utm), np.nan)
    if drain_file.exists():
        dgdf = gpd.read_file(drain_file).to_crs(UTM_CRS)
        dgdf = dgdf[dgdf.is_valid & ~dgdf.is_empty]
        if len(dgdf) > 0:
            d_union = unary_union(dgdf.geometry)
            dist_d = np.array([pt.distance(d_union) for pt in cents.geometry])
            log.info("Distance to drain: min %.0f m, mean %.0f m, max %.0f m",
                     float(np.nanmin(dist_d)), float(np.nanmean(dist_d)), float(np.nanmax(dist_d)))

    return pd.DataFrame({
        "cell_id": gdf_utm["cell_id"].values,
        "dist_to_water_m": np.round(dist_w, 1),
        "dist_to_drain_m": np.round(dist_d, 1),
    })


def compute_rainfall_feature(gdf_utm) -> pd.DataFrame:
    """Applies annual monsoon rainfall baseline."""
    rain_file = PROCESSED / "rainfall_monsoon_annual.csv"
    mean_val = 528.7
    if rain_file.exists():
        try:
            df = pd.read_csv(rain_file)
            mean_val = float(df["monsoon_total_mm"].mean())
        except Exception:
            pass
    return pd.DataFrame({
        "cell_id": gdf_utm["cell_id"].values,
        "monsoon_rainfall_mm": round(mean_val, 1),
    })


def calculate_fsi(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates weighted Multi-Criteria Flood Susceptibility Index."""
    out = df.copy()
    fsi_scores = np.zeros(len(out), dtype=float)
    total_weight_used = np.zeros(len(out), dtype=float)

    for feat, weight in FSI_WEIGHTS.items():
        if feat in out.columns:
            series = out[feat].astype(float).values
            valid_mask = ~np.isnan(series)
            if np.any(valid_mask):
                mn = np.nanmin(series)
                mx = np.nanmax(series)
                if mx > mn:
                    norm = (series - mn) / (mx - mn)
                else:
                    norm = np.zeros_like(series)

                if feat in INVERTED_FEATURES:
                    norm = 1.0 - norm

                norm[~valid_mask] = np.nan

                # Add weighted score
                fsi_scores[valid_mask] += weight * norm[valid_mask]
                total_weight_used[valid_mask] += weight

    # Where at least 70% weight accounted for, normalize to [0, 1]
    valid_fsi = total_weight_used >= 0.70
    final_fsi = np.where(valid_fsi, np.round(fsi_scores / np.where(total_weight_used > 0, total_weight_used, 1.0), 4), np.nan)
    out["fsi"] = final_fsi

    def assign_class(score):
        if np.isnan(score):
            return "unknown"
        if score < 0.25:
            return "low"
        if score < 0.50:
            return "moderate"
        if score < 0.75:
            return "high"
        return "very_high"

    out["fsi_class"] = [assign_class(s) for s in final_fsi]
    return out


def main():
    log.info("=== Phase 2: Feature Engineering & FSI Generation ===")
    gdf_utm, gdf_wgs84 = create_grid()

    # Compute individual layers
    dem_df = compute_dem_features(gdf_wgs84)
    lc_df = compute_landcover_features(gdf_wgs84)
    dist_df = compute_distance_features(gdf_utm)
    rain_df = compute_rainfall_feature(gdf_utm)

    # Merge features
    feature_df = gdf_utm[["cell_id", "centroid_lon", "centroid_lat"]].copy()
    for sub_df in [dem_df, lc_df, dist_df, rain_df]:
        feature_df = feature_df.merge(sub_df, on="cell_id", how="left")

    # Filter out cells with no elevation data (cells outside raster coverage)
    feature_df = feature_df[~feature_df["elevation_m"].isna()].reset_index(drop=True)
    log.info("Retained %d cells covering Gurugram study territory.", len(feature_df))

    # Calculate FSI
    final_df = calculate_fsi(feature_df)

    # Save feature tables
    pq_path = PROCESSED / "features.parquet"
    csv_path = PROCESSED / "features.csv"
    final_df.to_parquet(pq_path, index=False)
    final_df.to_csv(csv_path, index=False)
    log.info("Saved features: %s and %s (%d rows)", pq_path.name, csv_path.name, len(final_df))

    # Save evaluated Grid GeoJSON
    grid_geojson = gdf_wgs84.merge(final_df, on=["cell_id", "centroid_lon", "centroid_lat"], how="inner")
    grid_path = PROCESSED / "grid_cells.geojson"
    grid_geojson.to_file(grid_path, driver="GeoJSON")
    log.info("Saved evaluated grid GeoJSON: %s (%d features)", grid_path.name, len(grid_geojson))

    # Save FSI Configuration
    config = {
        "version": "fsi_v1.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "cell_size_m": CELL_SIZE_M,
        "study_bbox": list(BBOX_WGS84),
        "total_evaluated_cells": len(final_df),
        "weights": FSI_WEIGHTS,
        "inverted_features": list(INVERTED_FEATURES),
        "classification_thresholds": {
            "low": [0.00, 0.25],
            "moderate": [0.25, 0.50],
            "high": [0.50, 0.75],
            "very_high": [0.75, 1.00],
        },
        "weight_source": "Arya & Kumar (2023) AHP study, Natural Hazards 117(3)",
        "prediction_mode": "susceptibility_index",
        "supervised_ml_feasible": False,
        "supervised_ml_reason": "Audit proved GMDA surveydate is NULL across all 25 records; no non-flooded negative records exist.",
    }
    cfg_path = MODELS / "fsi_config.json"
    cfg_path.write_text(json.dumps(config, indent=2), encoding="utf-8")

    # Feature quality report
    stats = {}
    for feat in FSI_WEIGHTS.keys():
        if feat in final_df.columns:
            s = final_df[feat].dropna()
            stats[feat] = {
                "mean": round(float(s.mean()), 4) if len(s) else None,
                "std": round(float(s.std()), 4) if len(s) else None,
                "min": round(float(s.min()), 4) if len(s) else None,
                "max": round(float(s.max()), 4) if len(s) else None,
                "null_count": int(final_df[feat].isna().sum()),
                "weight": FSI_WEIGHTS[feat],
            }

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_cells": len(final_df),
        "fsi_mean": round(float(final_df["fsi"].mean()), 4),
        "fsi_std": round(float(final_df["fsi"].std()), 4),
        "fsi_class_distribution": final_df["fsi_class"].value_counts().to_dict(),
        "features": stats,
    }
    rep_path = REPORTS / "feature_report.json"
    rep_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    log.info("Feature report saved to %s", rep_path.name)
    log.info("FSI Distribution: %s", report["fsi_class_distribution"])
    log.info("=== Phase 2 Feature Engineering Complete! ===")


if __name__ == "__main__":
    main()
