# -*- coding: utf-8 -*-
"""
preprocess.py
-------------
Phase 2 -- Data Preprocessing

Validates and harmonizes all raw datasets for the Gurugram study area:
1. GMDA Waterlogging survey points (25 points)
2. Open-Meteo ERA5-Land daily rainfall (3,561 days -> daily & monsoon aggregates)
3. Copernicus DEM GLO-30 (merges and crops tiles to study bbox)
4. ESA WorldCover 2021 10m (clipped to study area)
5. GMDA Drainage infrastructure (drain legs, waterbodies, MCG boundary)

Outputs saved to data/processed/.
Generates data/reports/quality_report.json.

Run:
    python ml/preprocess.py
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask as rio_mask
from rasterio.merge import merge
from shapely.geometry import box, mapping

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
RAW_GMDA = ROOT / "data" / "raw" / "gmda"
RAW_RAIN = ROOT / "data" / "raw" / "rainfall"
RAW_ELEV = ROOT / "data" / "raw" / "elevation"
RAW_LC   = ROOT / "data" / "raw" / "landcover"
PROCESSED = ROOT / "data" / "processed"
REPORTS   = ROOT / "data" / "reports"
PROCESSED.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

BBOX = (76.80, 28.20, 77.25, 28.55)  # xmin, ymin, xmax, ymax (WGS84)


def preprocess_gmda(report: dict) -> None:
    log.info("=== 1. GMDA Survey Points ===")
    src = RAW_GMDA / "flood_survey_v2_raw.geojson"
    if not src.exists():
        report["gmda"] = {"status": "missing"}
        return

    data = json.loads(src.read_text(encoding="utf-8-sig"))
    features = data.get("features", [])
    valid = []
    for f in features:
        coords = (f.get("geometry") or {}).get("coordinates", [])
        if len(coords) == 2:
            lon, lat = coords
            if BBOX[0] <= lon <= BBOX[2] and BBOX[1] <= lat <= BBOX[3]:
                valid.append(f)

    dest = PROCESSED / "gmda_survey_points.geojson"
    dest.write_text(json.dumps({"type": "FeatureCollection", "features": valid}, indent=2), encoding="utf-8")

    report["gmda"] = {
        "status": "ok",
        "total_records": len(features),
        "in_study_area": len(valid),
        "null_surveydate_count": sum(1 for f in valid if f["properties"].get("surveydate") is None),
        "waterlogging_type_count": sum(1 for f in valid if f["properties"].get("surveytype") == "Waterlogging"),
        "processed_file": str(dest),
        "supervised_ml_feasible": False,
        "note": "All 25 survey dates are NULL. Used exclusively as validation/reference overlay.",
    }
    log.info("GMDA survey points: %d valid records saved.", len(valid))


def preprocess_rainfall(report: dict) -> None:
    log.info("=== 2. Rainfall Data ===")
    src = RAW_RAIN / "openmeteo_gurugram_2015_2024.json"
    if not src.exists():
        report["rainfall"] = {"status": "missing"}
        return

    payload = json.loads(src.read_text())
    daily = payload.get("daily", {})
    df = pd.DataFrame({
        "date": pd.to_datetime(daily.get("time", [])),
        "precip_mm": daily.get("precipitation_sum", []),
        "rain_mm": daily.get("rain_sum", []),
        "temp_max_c": daily.get("temperature_2m_max", []),
        "temp_min_c": daily.get("temperature_2m_min", []),
    })
    df["month"] = df["date"].dt.month
    df["year"] = df["date"].dt.year
    df["is_monsoon"] = df["month"].isin([6, 7, 8, 9])

    monsoon_annual = (
        df[df["is_monsoon"]]
        .groupby("year")["precip_mm"]
        .sum()
        .reset_index()
        .rename(columns={"precip_mm": "monsoon_total_mm"})
    )
    mean_monsoon_mm = float(monsoon_annual["monsoon_total_mm"].mean())

    dest_daily = PROCESSED / "rainfall_daily.csv"
    dest_monsoon = PROCESSED / "rainfall_monsoon_annual.csv"
    df.to_csv(dest_daily, index=False)
    monsoon_annual.to_csv(dest_monsoon, index=False)

    report["rainfall"] = {
        "status": "ok",
        "total_days": len(df),
        "date_range": [str(df["date"].min().date()), str(df["date"].max().date())],
        "mean_annual_monsoon_mm": round(mean_monsoon_mm, 1),
        "monsoon_years": len(monsoon_annual),
        "daily_file": str(dest_daily),
        "monsoon_file": str(dest_monsoon),
    }
    log.info("Rainfall: %d days, mean annual monsoon: %.1f mm", len(df), mean_monsoon_mm)


def preprocess_dem(report: dict) -> None:
    log.info("=== 3. Copernicus DEM GLO-30 ===")
    tiles = [
        RAW_ELEV / "Copernicus_DSM_COG_10_N28_00_E076_00_DEM.tif",
        RAW_ELEV / "Copernicus_DSM_COG_10_N28_00_E077_00_DEM.tif",
    ]
    available = [t for t in tiles if t.exists() and t.stat().st_size > 1_000_000]
    if not available:
        report["dem"] = {"status": "missing"}
        return

    dest = PROCESSED / "dem_gurugram.tif"
    aoi = box(*BBOX)

    datasets = [rasterio.open(t) for t in available]
    if len(datasets) > 1:
        merged, transform = merge(datasets)
        profile = datasets[0].profile.copy()
        profile.update(
            height=merged.shape[1],
            width=merged.shape[2],
            transform=transform,
            driver="GTiff",
            compress="lzw",
        )
        for ds in datasets:
            ds.close()

        import tempfile
        tmp = Path(tempfile.mktemp(suffix=".tif"))
        with rasterio.open(tmp, "w", **profile) as dst:
            dst.write(merged)
        src_final = rasterio.open(tmp)
    else:
        src_final = datasets[0]
        tmp = None

    out_img, out_tf = rio_mask(src_final, [mapping(aoi)], crop=True, nodata=-9999)
    prof = src_final.profile.copy()
    prof.update(
        height=out_img.shape[1],
        width=out_img.shape[2],
        transform=out_tf,
        nodata=-9999,
        compress="lzw",
        driver="GTiff",
    )
    src_final.close()
    if tmp and tmp.exists():
        tmp.unlink()

    with rasterio.open(dest, "w", **prof) as dst:
        dst.write(out_img)

    with rasterio.open(dest) as chk:
        d = chk.read(1).astype(np.float32)
        valid = d != -9999
        res_m = abs(chk.transform.a) * 111320
        report["dem"] = {
            "status": "ok",
            "tiles_merged": [t.name for t in available],
            "elevation_min_m": round(float(d[valid].min()), 1),
            "elevation_max_m": round(float(d[valid].max()), 1),
            "elevation_mean_m": round(float(d[valid].mean()), 1),
            "approx_resolution_m": round(res_m, 1),
            "processed_file": str(dest),
        }
    log.info("DEM: range %.1f - %.1f m (mean %.1f m) -> %s",
             report["dem"]["elevation_min_m"], report["dem"]["elevation_max_m"],
             report["dem"]["elevation_mean_m"], dest.name)


def preprocess_landcover(report: dict) -> None:
    log.info("=== 4. ESA WorldCover 2021 ===")
    lc_file = PROCESSED / "landcover_gurugram.tif"
    if not lc_file.exists():
        report["landcover"] = {"status": "missing"}
        return

    with rasterio.open(lc_file) as chk:
        data = chk.read(1)
        total = int(np.sum(data > 0))
        built_up = int(np.sum(data == 50))
        veg = int(np.sum(np.isin(data, [10, 20, 30])))
        water = int(np.sum(data == 80))
        res_m = abs(chk.transform.a) * 111320

        report["landcover"] = {
            "status": "ok",
            "total_pixels": total,
            "approx_resolution_m": round(res_m, 1),
            "built_up_percentage": round(built_up / max(total, 1) * 100, 2),
            "vegetation_percentage": round(veg / max(total, 1) * 100, 2),
            "water_percentage": round(water / max(total, 1) * 100, 2),
            "processed_file": str(lc_file),
        }
    log.info("Landcover: built-up %.1f%%, vegetation %.1f%%, water %.2f%%",
             report["landcover"]["built_up_percentage"],
             report["landcover"]["vegetation_percentage"],
             report["landcover"]["water_percentage"])


def preprocess_drainage(report: dict) -> None:
    log.info("=== 5. GMDA Drainage and Hydrology Layers ===")
    drain_file = PROCESSED / "gmda_drain_legs.geojson"
    wb_file = PROCESSED / "gmda_waterbodies_1980.geojson"
    mcg_file = PROCESSED / "mcg_boundary.geojson"
    wards_file = PROCESSED / "mcg_wards.geojson"
    ws_file = PROCESSED / "gurugram_watersheds.geojson"

    drains_count = len(json.loads(drain_file.read_text("utf-8-sig")).get("features", [])) if drain_file.exists() else 0
    wb_count = len(json.loads(wb_file.read_text("utf-8-sig")).get("features", [])) if wb_file.exists() else 0
    wards_count = len(json.loads(wards_file.read_text("utf-8-sig")).get("features", [])) if wards_file.exists() else 0

    report["drainage_infrastructure"] = {
        "status": "ok",
        "gmda_drain_legs_count": drains_count,
        "gmda_waterbodies_count": wb_count,
        "mcg_wards_count": wards_count,
        "source": "GMDA OneMap Official GIS Server (onemapdepts.gmda.gov.in)",
    }
    log.info("Drainage: %d drain legs, %d waterbodies, %d wards ready.", drains_count, wb_count, wards_count)


def main():
    log.info("Running Phase 2 preprocessing...")
    report = {"preprocessed_at": datetime.now(timezone.utc).isoformat()}
    preprocess_gmda(report)
    preprocess_rainfall(report)
    preprocess_dem(report)
    preprocess_landcover(report)
    preprocess_drainage(report)

    out = REPORTS / "quality_report.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    log.info("Quality report saved to %s", out)
    log.info("Preprocessing complete.")

if __name__ == "__main__":
    main()
