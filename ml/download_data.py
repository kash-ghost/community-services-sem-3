# -*- coding: utf-8 -*-
"""
download_data.py
----------------
Phase 2 -- Data Acquisition

Downloads all datasets needed for the Gurugram flood susceptibility project
and saves them to data/raw/<source>/.

Run:
    python ml/download_data.py

Sources acquired:
    1. Open-Meteo historical rainfall (JSON -> CSV)
    2. Copernicus DEM GLO-30 tiles (GeoTIFF)
    3. ESA WorldCover v2 2021 tile (GeoTIFF)
    4. OSM waterways + water polygons (GeoJSON via Overpass API)
    5. GMDA flood survey -- already downloaded in Phase 1

All downloads logged to data/reports/download_log.json.
"""
from __future__ import annotations

import json
import logging
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

ROOT     = Path(__file__).resolve().parent.parent
RAW_RAIN = ROOT / "data" / "raw" / "rainfall"
RAW_ELEV = ROOT / "data" / "raw" / "elevation"
RAW_LC   = ROOT / "data" / "raw" / "landcover"
REPORTS  = ROOT / "data" / "reports"
for d in (RAW_RAIN, RAW_ELEV, RAW_LC, REPORTS):
    d.mkdir(parents=True, exist_ok=True)

BBOX          = (76.80, 28.20, 77.25, 28.55)   # xmin ymin xmax ymax (WGS84)
CENTROID_LAT  = 28.4595
CENTROID_LON  = 77.0266
RAIN_START    = "2015-01-01"
RAIN_END      = "2024-09-30"
TIMEOUT       = 90   # seconds


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _download_file(url: str, dest: Path, desc: str, chunk_size: int = 65536) -> bool:
    try:
        r = requests.get(url, stream=True, timeout=TIMEOUT)
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0
        with dest.open("wb") as fh:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    fh.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded / total * 100
                        mb  = downloaded / 1_048_576
                        print(f"\r  {desc}: {mb:.1f} MB / {total/1_048_576:.1f} MB  ({pct:.0f}%)",
                              end="", flush=True)
        print()
        log.info("%s -> %s  (%d bytes)", desc, dest.name, downloaded)
        return True
    except requests.RequestException as exc:
        log.error("%s download FAILED: %s", desc, exc)
        if dest.exists():
            dest.unlink()
        return False


def _post_overpass(data: dict, timeout: int = 90) -> tuple[bool, dict | str]:
    url = "https://overpass-api.de/api/interpreter"
    try:
        r = requests.post(url, data=data, timeout=timeout)
        r.raise_for_status()
        return True, r.json()
    except requests.RequestException as exc:
        return False, str(exc)
    except ValueError as exc:
        return False, f"Non-JSON: {exc}"


# ---------------------------------------------------------------------------
# 1. Open-Meteo Rainfall
# ---------------------------------------------------------------------------
def download_rainfall() -> dict:
    log.info("=== 1/4  Rainfall (Open-Meteo ERA5-Land) ===")
    dest = RAW_RAIN / "openmeteo_gurugram_2015_2024.json"
    if dest.exists():
        log.info("Cached: %s", dest.name)
        return {"status": "cached", "file": str(dest)}

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": CENTROID_LAT,
        "longitude": CENTROID_LON,
        "start_date": RAIN_START,
        "end_date": RAIN_END,
        "daily": "precipitation_sum,rain_sum,temperature_2m_max,temperature_2m_min",
        "timezone": "Asia/Kolkata",
    }
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        payload = r.json()
        dest.write_text(json.dumps(payload, indent=2))
        days = len(payload.get("daily", {}).get("time", []))
        log.info("Rainfall: %d daily records -> %s", days, dest.name)
        return {"status": "ok", "records": days, "file": str(dest)}
    except Exception as exc:
        log.error("Rainfall FAILED: %s", exc)
        return {"status": "error", "error": str(exc)}


# ---------------------------------------------------------------------------
# 2. Copernicus DEM GLO-30
# ---------------------------------------------------------------------------
DEM_STEMS = [
    "Copernicus_DSM_COG_10_N28_00_E076_00_DEM",
    "Copernicus_DSM_COG_10_N28_00_E077_00_DEM",
]
DEM_BASE = "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com"


def download_dem() -> dict:
    log.info("=== 2/4  Copernicus DEM GLO-30 ===")
    results = {}
    for stem in DEM_STEMS:
        dest = RAW_ELEV / f"{stem}.tif"
        if dest.exists() and dest.stat().st_size > 1_000_000:
            log.info("Cached: %s  (%.1f MB)", dest.name, dest.stat().st_size / 1e6)
            results[stem] = {"status": "cached", "file": str(dest),
                             "size_mb": round(dest.stat().st_size / 1e6, 1)}
            continue
        url = f"{DEM_BASE}/{stem}/{stem}.tif"
        log.info("Downloading: %s", url)
        ok = _download_file(url, dest, stem)
        if ok:
            results[stem] = {"status": "ok", "file": str(dest),
                             "size_mb": round(dest.stat().st_size / 1e6, 1)}
        else:
            results[stem] = {"status": "error", "url": url}
    return results


# ---------------------------------------------------------------------------
# 3. ESA WorldCover v2 (2021)
# ---------------------------------------------------------------------------
def _wc_tile_name(lat: float, lon: float) -> str:
    tl = int(math.floor(lat / 3) * 3)
    tlo = int(math.floor(lon / 3) * 3)
    ls = f"N{abs(tl):02d}"  if tl  >= 0 else f"S{abs(tl):02d}"
    lo = f"E{abs(tlo):03d}" if tlo >= 0 else f"W{abs(tlo):03d}"
    return f"ESA_WorldCover_v200_2021_v300_{ls}{lo}_Map"


def download_landcover() -> dict:
    log.info("=== 3/4  ESA WorldCover 2021 ===")
    corners = [(BBOX[1], BBOX[0]), (BBOX[3], BBOX[0]),
               (BBOX[1], BBOX[2]), (BBOX[3], BBOX[2])]
    tiles = list({_wc_tile_name(la, lo) for la, lo in corners})
    log.info("Required tiles: %s", tiles)

    results = {}
    for tile in tiles:
        dest = RAW_LC / f"{tile}.tif"
        if dest.exists() and dest.stat().st_size > 5_000_000:
            log.info("Cached: %s  (%.0f MB)", dest.name, dest.stat().st_size / 1e6)
            results[tile] = {"status": "cached", "file": str(dest),
                             "size_mb": round(dest.stat().st_size / 1e6, 0)}
            continue

        # Primary: public S3 bucket
        url = (f"https://esa-worldcover.s3.eu-central-1.amazonaws.com"
               f"/v200/2021/map/{tile}.tif")
        log.info("Trying: %s", url)
        ok = _download_file(url, dest, tile)

        if not ok or not dest.exists():
            log.warning("WorldCover %s unavailable -- land-cover features will be NaN", tile)
            results[tile] = {"status": "unavailable",
                             "note": "Download manually from https://zenodo.org/record/7254221"}
        else:
            results[tile] = {"status": "ok", "file": str(dest),
                             "size_mb": round(dest.stat().st_size / 1e6, 0)}
    return results


# ---------------------------------------------------------------------------
# 4. OSM (Overpass API)
# ---------------------------------------------------------------------------
def _overpass_to_geojson(result: dict, geom_type: str) -> dict:
    features = []
    for elem in result.get("elements", []):
        props = dict(elem.get("tags", {}))
        props["osm_id"]   = elem.get("id")
        props["osm_type"] = elem.get("type")
        gdata = elem.get("geometry", [])
        geom = None
        if geom_type == "line" and gdata:
            coords = [[pt["lon"], pt["lat"]] for pt in gdata]
            if len(coords) >= 2:
                geom = {"type": "LineString", "coordinates": coords}
        elif geom_type == "poly":
            members = elem.get("members", [])
            if members:
                for m in members:
                    if m.get("role") == "outer" and m.get("geometry"):
                        c = [[pt["lon"], pt["lat"]] for pt in m["geometry"]]
                        if len(c) >= 4:
                            geom = {"type": "Polygon", "coordinates": [c]}
                        break
            elif gdata and len(gdata) >= 4:
                c = [[pt["lon"], pt["lat"]] for pt in gdata]
                geom = {"type": "Polygon", "coordinates": [c]}
        if geom:
            features.append({"type": "Feature", "geometry": geom, "properties": props})
    return {"type": "FeatureCollection", "features": features}


def _overpass_query(tags: list[str], geom_type: str) -> str:
    s, w, n, e = BBOX[1], BBOX[0], BBOX[3], BBOX[2]
    lines = [f"[out:json][timeout:60];("]
    for tag in tags:
        k, v = tag.split("=", 1)
        lines.append(f'  way["{k}"="{v}"]({s},{w},{n},{e});')
    lines += [");", "out geom;"]
    return "\n".join(lines)


def download_osm() -> dict:
    log.info("=== 4/4  OSM Waterways + Water Bodies ===")
    results = {}

    # Waterways (lines)
    dest_w = RAW_LC / "osm_waterways_gurugram.geojson"
    if not dest_w.exists():
        q = _overpass_query(
            ["waterway=drain","waterway=ditch","waterway=canal",
             "waterway=river","waterway=stream"], "line")
        log.info("Querying Overpass for waterways...")
        ok, resp = _post_overpass({"data": q})
        if ok and isinstance(resp, dict):
            gj = _overpass_to_geojson(resp, "line")
            dest_w.write_text(json.dumps(gj, indent=2))
            n = len(gj["features"])
            log.info("Waterways: %d features saved", n)
            results["waterways"] = {"status": "ok", "features": n, "file": str(dest_w)}
        else:
            log.error("Waterways query FAILED: %s", resp)
            results["waterways"] = {"status": "error", "error": str(resp)}
        time.sleep(2)
    else:
        log.info("Cached: %s", dest_w.name)
        results["waterways"] = {"status": "cached", "file": str(dest_w)}

    # Water polygons
    dest_p = RAW_LC / "osm_water_polygons_gurugram.geojson"
    if not dest_p.exists():
        q2 = _overpass_query(
            ["natural=water","landuse=reservoir","natural=wetland"], "poly")
        log.info("Querying Overpass for water polygons...")
        ok2, resp2 = _post_overpass({"data": q2})
        if ok2 and isinstance(resp2, dict):
            gj2 = _overpass_to_geojson(resp2, "poly")
            dest_p.write_text(json.dumps(gj2, indent=2))
            n2 = len(gj2["features"])
            log.info("Water polygons: %d features saved", n2)
            results["water_polygons"] = {"status": "ok", "features": n2, "file": str(dest_p)}
        else:
            log.error("Water polygons query FAILED: %s", resp2)
            results["water_polygons"] = {"status": "error", "error": str(resp2)}
    else:
        log.info("Cached: %s", dest_p.name)
        results["water_polygons"] = {"status": "cached", "file": str(dest_p)}

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    t0 = time.monotonic()
    log.info("Phase 2 Data Download -- Gurugram Flood Vulnerability Framework")

    log_data: dict = {
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "study_bbox": list(BBOX),
        "results": {},
    }

    log_data["results"]["rainfall"]  = download_rainfall()
    log_data["results"]["dem"]       = download_dem()
    log_data["results"]["landcover"] = download_landcover()
    log_data["results"]["osm"]       = download_osm()

    elapsed = round(time.monotonic() - t0, 1)
    log.info("=== DOWNLOAD SUMMARY (%s s) ===", elapsed)
    any_fail = False
    for src, res in log_data["results"].items():
        if isinstance(res, dict):
            s = res.get("status", "?")
        else:
            statuses = [v.get("status","?") for v in res.values() if isinstance(v,dict)]
            s = "ok" if all(st in ("ok","cached") for st in statuses) else "partial"
        flag = "OK" if s in ("ok","cached") else ("PARTIAL" if s == "partial" else "FAIL")
        if flag not in ("OK","PARTIAL"): any_fail = True
        log.info("  %-15s  %s", src, flag)

    log_data["elapsed_seconds"] = elapsed
    (REPORTS / "download_log.json").write_text(
        json.dumps(log_data, indent=2, default=str))
    log.info("Log -> data/reports/download_log.json")

    if any_fail:
        log.warning("Some downloads failed -- pipeline can continue with available data.")
        sys.exit(1)


if __name__ == "__main__":
    main()
