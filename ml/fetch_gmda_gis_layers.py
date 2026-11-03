# -*- coding: utf-8 -*-
"""
fetch_gmda_gis_layers.py
------------------------
Fetches authoritative vector GIS layers directly from the GMDA ArcGIS server:
1. MCG Study Boundary: flood_survey_2/FeatureServer/5
2. MCG Wards: flood_survey_2/FeatureServer/4
3. Drain Legs / Channels: Water_Infrastructure_with_Runoff/MapServer/24
4. Najafgarh / Badshahpur Drains: Water_Infrastructure_with_Runoff/MapServer/21 & 32
5. Watersheds: flood_survey_2/FeatureServer/1
"""
import json
import logging
from pathlib import Path
import requests, ssl
from urllib3.util.ssl_ import create_urllib3_context

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
RAW_GIS = ROOT / "data" / "raw" / "gmda"
PROCESSED = ROOT / "data" / "processed"
RAW_GIS.mkdir(parents=True, exist_ok=True)
PROCESSED.mkdir(parents=True, exist_ok=True)

class LegacyRenegotiationAdapter(requests.adapters.HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = create_urllib3_context()
        ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
        kwargs['ssl_context'] = ctx
        return super().init_poolmanager(*args, **kwargs)

session = requests.Session()
session.mount('https://', LegacyRenegotiationAdapter())

BASE_URL = "https://onemapdepts.gmda.gov.in/server/rest/services"

LAYERS_TO_FETCH = [
    {
        "service": "flood_survey_2/FeatureServer/5",
        "name": "mcg_boundary",
        "desc": "Official Municipal Corporation of Gurugram Boundary",
    },
    {
        "service": "flood_survey_2/FeatureServer/4",
        "name": "mcg_wards",
        "desc": "Gurugram Municipal Wards",
    },
    {
        "service": "flood_survey_2/FeatureServer/1",
        "name": "gurugram_watersheds",
        "desc": "Gurugram Watershed Hydrological Units",
    },
    {
        "service": "Water_Infrastructure_with_Runoff/MapServer/24",
        "name": "gmda_drain_legs",
        "desc": "Official GMDA Major Drainage Network (Drain Legs)",
    },
    {
        "service": "Water_Infrastructure_with_Runoff/MapServer/21",
        "name": "najafgarh_drain",
        "desc": "Najafgarh Drain Corridor",
    },
    {
        "service": "Water_Infrastructure_with_Runoff/MapServer/81",
        "name": "gmda_waterbodies_1980",
        "desc": "Historic and Mapped Water Bodies and Ponds",
    },
]

def fetch_layer(cfg):
    url = f"{BASE_URL}/{cfg['service']}/query"
    params = {
        "where": "1=1",
        "outFields": "*",
        "returnGeometry": "true",
        "f": "geojson",
    }
    log.info("Fetching %s (%s)...", cfg["name"], cfg["desc"])
    try:
        r = session.get(url, params=params, timeout=45)
        if r.status_code == 200:
            data = r.json()
            features = data.get("features", [])
            dest_raw = RAW_GIS / f"{cfg['name']}.geojson"
            dest_proc = PROCESSED / f"{cfg['name']}.geojson"
            dest_raw.write_text(json.dumps(data, indent=2), encoding="utf-8")
            dest_proc.write_text(json.dumps(data, indent=2), encoding="utf-8")
            log.info("Saved %s: %d features -> %s", cfg["name"], len(features), dest_proc.name)
            return len(features)
        else:
            log.warning("Failed %s: HTTP %s", cfg["name"], r.status_code)
            return 0
    except Exception as e:
        log.error("Error fetching %s: %s", cfg["name"], e)
        return 0

def main():
    log.info("Starting acquisition of GMDA authoritative GIS infrastructure layers...")
    summary = {}
    for cfg in LAYERS_TO_FETCH:
        count = fetch_layer(cfg)
        summary[cfg["name"]] = count
    log.info("Finished fetching GMDA layers: %s", summary)

if __name__ == "__main__":
    main()
