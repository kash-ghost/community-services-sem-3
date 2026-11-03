# -*- coding: utf-8 -*-
"""
fetch_landcover.py
------------------
Downloads or window-clips the ESA WorldCover 10m (2021) tile for Gurugram.
URL: https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N27E075_Map.tif
"""
import logging
from pathlib import Path
import numpy as np
import rasterio
from rasterio.mask import mask as rio_mask
from rasterio.windows import from_bounds
from shapely.geometry import box, mapping

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
RAW_LC = ROOT / "data" / "raw" / "landcover"
PROCESSED = ROOT / "data" / "processed"
RAW_LC.mkdir(parents=True, exist_ok=True)
PROCESSED.mkdir(parents=True, exist_ok=True)

BBOX = (76.80, 28.20, 77.25, 28.55)  # xmin, ymin, xmax, ymax
TILE_URL = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N27E075_Map.tif"

def main():
    dest_proc = PROCESSED / "landcover_gurugram.tif"
    if dest_proc.exists() and dest_proc.stat().st_size > 100_000:
        log.info("landcover_gurugram.tif already exists (%d bytes)", dest_proc.stat().st_size)
        return

    log.info("Attempting window read from COG at: %s", TILE_URL)
    # Using /vsicurl/ or direct URL via rasterio
    try:
        with rasterio.Env(CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif", GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"):
            with rasterio.open(TILE_URL) as src:
                log.info("Successfully opened COG remotely. Shape: %s, CRS: %s", src.shape, src.crs)
                window = from_bounds(*BBOX, transform=src.transform)
                data = src.read(1, window=window)
                win_transform = src.window_transform(window)
                
                profile = src.profile.copy()
                profile.update(
                    height=data.shape[0],
                    width=data.shape[1],
                    transform=win_transform,
                    driver="GTiff",
                    compress="lzw",
                    nodata=0
                )
                with rasterio.open(dest_proc, "w", **profile) as dst:
                    dst.write(data, 1)
                log.info("Successfully clipped and saved landcover to %s (shape: %s)", dest_proc.name, data.shape)
                return
    except Exception as e:
        log.warning("Remote window read failed: %s. Falling back to downloading tile.", e)

    # Fallback: stream download to raw/
    dest_raw = RAW_LC / "ESA_WorldCover_10m_2021_v200_N27E075_Map.tif"
    if not dest_raw.exists():
        import requests
        log.info("Downloading full tile (~150-250MB)...")
        r = requests.get(TILE_URL, stream=True, timeout=120)
        r.raise_for_status()
        with open(dest_raw, "wb") as f:
            for chunk in r.iter_content(chunk_size=1048576):
                if chunk:
                    f.write(chunk)
        log.info("Downloaded %s (%d bytes)", dest_raw.name, dest_raw.stat().st_size)

    # Now mask from raw
    with rasterio.open(dest_raw) as src:
        aoi = box(*BBOX)
        out_image, out_transform = rio_mask(src, [mapping(aoi)], crop=True, nodata=0)
        profile = src.profile.copy()
        profile.update(
            height=out_image.shape[1],
            width=out_image.shape[2],
            transform=out_transform,
            nodata=0,
            compress="lzw",
            driver="GTiff"
        )
        with rasterio.open(dest_proc, "w", **profile) as dst:
            dst.write(out_image)
    log.info("Saved cropped landcover to %s", dest_proc.name)

if __name__ == "__main__":
    main()
