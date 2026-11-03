# -*- coding: utf-8 -*-
"""
build_labels.py
---------------
Phase 2/3 -- Target Label Assessment & Generation Scaffold

Evaluates whether reliable supervised classification labels can be
constructed from historical waterlogging survey data.

Enforces Core Academic Rule:
  "Do not fabricate labels merely to make classification work."
  "Distinguish surveyed waterlogging locations from locations known not to have flooded."

Audit results:
  - Total GMDA survey points: 25
  - Points with survey date: 0 (all NULL)
  - Non-flooded counterfactuals: 0

Outcome:
  Documents why supervised classification cannot be trained on unverified labels.
  Generates data/reports/label_report.json explaining the rationale and requirements
  for future supervised model training.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
REPORTS = ROOT / "data" / "reports"

def main():
    log.info("Running supervised label feasibility assessment...")
    gmda_file = PROCESSED / "gmda_survey_points.geojson"

    total_pts = 0
    null_dates = 0
    if gmda_file.exists():
        data = json.loads(gmda_file.read_text(encoding="utf-8-sig"))
        features = data.get("features", [])
        total_pts = len(features)
        null_dates = sum(1 for f in features if f.get("properties", {}).get("surveydate") is None)

    report = {
        "assessed_at": datetime.now(timezone.utc).isoformat(),
        "total_observed_locations": total_pts,
        "locations_with_valid_timestamp": total_pts - null_dates,
        "counterfactual_non_flooded_samples": 0,
        "supervised_labels_viable": False,
        "verdict": "SUPERVISED_ML_INSUFFICIENT_EVIDENCE",
        "rationale": [
            "All 25 GMDA records lack survey dates (surveydate is NULL).",
            "Without timestamps, flood events cannot be correlated with specific daily rainfall episodes.",
            "Absence of reported waterlogging in a grid cell does not prove it did not flood (presence-only bias).",
            "Synthesizing pseudo-absence points arbitrarily would introduce severe label noise and distort decision boundaries.",
        ],
        "decision": "Employ Multi-Criteria Flood Susceptibility Index (FSI) using AHP literature weights; preserve ML training module as ready scaffold.",
        "future_prerequisites_for_ml": {
            "minimum_positive_samples": 100,
            "minimum_verified_negative_samples": 100,
            "required_fields": ["surveydate", "water_depth_cm", "duration_hours", "geometry"],
        }
    }

    out_file = REPORTS / "label_report.json"
    out_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    log.info("Label assessment completed. Viable: False. Report saved to %s", out_file.name)

if __name__ == "__main__":
    main()
