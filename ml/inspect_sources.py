"""
inspect_sources.py
------------------
Phase 1 — Data Audit

Inspects all candidate GIS / data source endpoints and writes a structured
JSON report to data/reports/source_audit.json.

Run:
    python ml/inspect_sources.py

Outputs:
    data/reports/source_audit.json   — machine-readable audit result
    data/reports/source_audit.txt    — human-readable summary
"""
from __future__ import annotations

import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).resolve().parent.parent / "data" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

TIMEOUT = 20  # seconds per request

# ---------------------------------------------------------------------------
# Source registry
# ---------------------------------------------------------------------------
SOURCES = {
    "gmda_flood_survey": {
        "description": "GMDA Flood Survey FeatureServer layer 0",
        "base_url": "https://onemapdepts.gmda.gov.in/server/rest/services/flood_survey_2/FeatureServer/0",
        "type": "arcgis_feature_service",
    },
    "gmda_service_info": {
        "description": "GMDA FeatureServer root (service metadata)",
        "base_url": "https://onemapdepts.gmda.gov.in/server/rest/services/flood_survey_2/FeatureServer",
        "type": "arcgis_feature_service",
    },
}


def _get_json(url: str, params: dict | None = None) -> tuple[bool, dict | str]:
    """Return (success, payload_or_error_string)."""
    try:
        r = requests.get(url, params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return True, r.json()
    except requests.exceptions.Timeout:
        return False, "TIMEOUT"
    except requests.exceptions.ConnectionError as e:
        return False, f"CONNECTION_ERROR: {e}"
    except requests.exceptions.HTTPError as e:
        return False, f"HTTP_{r.status_code}: {e}"
    except ValueError:
        return False, f"NON_JSON_RESPONSE (status={r.status_code})"


def audit_arcgis_layer(base_url: str) -> dict:
    """Query an ArcGIS FeatureServer layer for metadata and a record sample."""
    result: dict = {}

    # 1. Layer metadata
    ok, meta = _get_json(base_url, {"f": "json"})
    result["metadata_accessible"] = ok
    if ok and isinstance(meta, dict):
        result["name"] = meta.get("name")
        result["type"] = meta.get("type")
        result["geometry_type"] = meta.get("geometryType")
        result["crs_wkid"] = (meta.get("extent") or {}).get("spatialReference", {}).get("wkid")
        result["fields"] = [
            {"name": f.get("name"), "type": f.get("type"), "alias": f.get("alias")}
            for f in meta.get("fields", [])
        ]
        result["has_attachments"] = meta.get("hasAttachments")
        result["max_record_count"] = meta.get("maxRecordCount")
        result["supports_query"] = "Query" in (meta.get("capabilities") or "")
        result["metadata_error"] = None
    else:
        result["fields"] = []
        result["metadata_error"] = str(meta)

    # 2. Record count
    ok2, count_resp = _get_json(
        f"{base_url}/query",
        {"where": "1=1", "returnCountOnly": "true", "f": "json"},
    )
    result["record_count_accessible"] = ok2
    if ok2 and isinstance(count_resp, dict):
        result["record_count"] = count_resp.get("count")
        result["count_error"] = count_resp.get("error")
    else:
        result["record_count"] = None
        result["count_error"] = str(count_resp)

    # 3. Sample records (first 5, attributes only)
    ok3, sample_resp = _get_json(
        f"{base_url}/query",
        {"where": "1=1", "outFields": "*", "resultRecordCount": 5, "f": "json"},
    )
    result["sample_accessible"] = ok3
    if ok3 and isinstance(sample_resp, dict):
        features = sample_resp.get("features", [])
        result["sample_count"] = len(features)
        result["sample_attributes"] = [f.get("attributes", {}) for f in features]
        result["sample_error"] = sample_resp.get("error")
        # Geometry type check
        has_geom = any(f.get("geometry") for f in features)
        result["sample_has_geometry"] = has_geom
    else:
        result["sample_count"] = 0
        result["sample_attributes"] = []
        result["sample_error"] = str(sample_resp)

    return result


def main() -> None:
    audit_time = datetime.now(timezone.utc).isoformat()
    report = {"audited_at": audit_time, "sources": {}}

    for key, src in SOURCES.items():
        log.info("Auditing: %s — %s", key, src["description"])
        t0 = time.monotonic()
        if src["type"] == "arcgis_feature_service":
            details = audit_arcgis_layer(src["base_url"])
        else:
            details = {"error": "Unsupported source type"}
        details["elapsed_seconds"] = round(time.monotonic() - t0, 2)
        details["base_url"] = src["base_url"]
        details["description"] = src["description"]
        report["sources"][key] = details

    out_json = REPORTS_DIR / "source_audit.json"
    out_txt  = REPORTS_DIR / "source_audit.txt"
    out_json.write_text(json.dumps(report, indent=2, default=str))

    # Human-readable summary
    lines = [f"DATA SOURCE AUDIT — {audit_time}", "=" * 60]
    for key, d in report["sources"].items():
        lines.append(f"\n## {key}")
        lines.append(f"   URL            : {d.get('base_url')}")
        lines.append(f"   Meta access    : {d.get('metadata_accessible')}")
        lines.append(f"   Meta error     : {d.get('metadata_error')}")
        lines.append(f"   Record count   : {d.get('record_count')}")
        lines.append(f"   Count error    : {d.get('count_error')}")
        lines.append(f"   Sample count   : {d.get('sample_count')}")
        lines.append(f"   Sample error   : {d.get('sample_error')}")
        lines.append(f"   Geometry type  : {d.get('geometry_type')}")
        lines.append(f"   Fields ({len(d.get('fields', []))})    :")
        for f in d.get("fields", []):
            lines.append(f"      {f['name']} ({f['type']})")
    out_txt.write_text("\n".join(lines))

    log.info("Report written to %s", out_json)
    log.info("Summary written to %s", out_txt)


if __name__ == "__main__":
    main()
