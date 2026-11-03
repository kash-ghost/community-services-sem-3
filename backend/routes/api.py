# -*- coding: utf-8 -*-
"""
api.py
------
Flask Blueprint defining the versioned REST API v1 for the
Flood Vulnerability Prediction Framework.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict

from flask import Blueprint, jsonify, request

from backend.database.mongo import get_predictions_collection, is_db_connected
from backend.schemas.prediction import validate_predict_payload
from backend.services.predictor import predictor_service

log = logging.getLogger(__name__)

api_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")

ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
REPORTS_DIR = ROOT / "data" / "reports"
MODELS_DIR = ROOT / "models"


@api_bp.route("/health", methods=["GET"])
def health_check():
    """Health status and database connectivity indicator."""
    db_status = "connected" if is_db_connected() else "unavailable"
    model_status = predictor_service.config.get("version", "fsi_v1.0") if predictor_service.is_loaded else "unloaded"
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_status,
        "model": model_status,
        "framework": "Flask 3.1",
    }), 200


@api_bp.route("/metadata", methods=["GET"])
def get_metadata():
    """Returns study area extent, feature schema, and dataset availability status."""
    audit_path = REPORTS_DIR / "source_audit.json"
    audit_data = {}
    if audit_path.exists():
        try:
            audit_data = json.loads(audit_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    gmda_file = PROCESSED_DIR / "gmda_survey_points.geojson"
    gmda_records = 0
    if gmda_file.exists():
        try:
            data = json.loads(gmda_file.read_text(encoding="utf-8"))
            gmda_records = len(data.get("features", []))
        except Exception:
            pass

    metadata = {
        "study_area": {
            "name": "Gurugram, Haryana, India",
            "bbox": [76.80, 28.20, 77.25, 28.55],
            "crs": "EPSG:4326 (WGS84)",
            "projected_crs": "EPSG:32643 (UTM 43N)",
        },
        "prediction_unit": "500m x 500m grid cells",
        "prediction_mode": "susceptibility_index",
        "model_version": predictor_service.config.get("version", "fsi_v1.0") if predictor_service.config else "fsi_v1.0",
        "datasets": [
            {"id": "DS-001", "name": "GMDA Flood Survey v2", "type": "Waterlogging observations", "records": gmda_records or 25, "status": "loaded" if gmda_file.exists() else "raw_only"},
            {"id": "DS-002", "name": "Open-Meteo ERA5-Land", "type": "Daily rainfall series", "status": "processed" if (PROCESSED_DIR / "rainfall_daily.csv").exists() else "pending"},
            {"id": "DS-004", "name": "Copernicus GLO-30 DEM", "type": "30m Digital Surface Model", "status": "processed" if (PROCESSED_DIR / "dem_gurugram.tif").exists() else "pending"},
            {"id": "DS-005", "name": "ESA WorldCover 2021", "type": "10m Land Cover classification", "status": "processed" if (PROCESSED_DIR / "landcover_gurugram.tif").exists() else "pending"},
            {"id": "DS-006", "name": "OpenStreetMap", "type": "Waterways and water bodies", "status": "processed" if (PROCESSED_DIR / "osm_waterways_gurugram.geojson").exists() else "pending"},
        ],
        "supervised_ml_feasible": False,
        "supervised_ml_rationale": "Audit proved GMDA surveydate is NULL for all 25 records; no non-flooded counterfactuals exist in public record. FSI utilized transparently.",
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }
    return jsonify(metadata), 200


@api_bp.route("/observations", methods=["GET"])
def get_observations():
    """Returns verified historical GMDA survey points."""
    obs_file = PROCESSED_DIR / "gmda_survey_points.geojson"
    if not obs_file.exists():
        raw_file = ROOT / "data" / "raw" / "gmda" / "flood_survey_v2_raw.geojson"
        if raw_file.exists():
            obs_file = raw_file

    if not obs_file.exists():
        return jsonify({"error": "Observation records not found", "code": "OBSERVATIONS_NOT_FOUND"}), 404

    try:
        data = json.loads(obs_file.read_text(encoding="utf-8"))
        features = data.get("features", [])
        return jsonify({
            "type": "FeatureCollection",
            "count": len(features),
            "data_limitations": [
                "surveydate is NULL across all 25 records — cannot establish temporal rainfall event linkage.",
                "Records depict field survey locations rather than exhaustive historical inundation perimeters.",
            ],
            "features": features,
        }), 200
    except Exception as exc:
        log.error("Failed to read observations: %s", exc)
        return jsonify({"error": "Unable to load observations.", "code": "LOAD_ERROR"}), 500


@api_bp.route("/areas", methods=["GET"])
def get_areas():
    """Returns evaluated grid cells with FSI scores as GeoJSON."""
    geojson_path = PROCESSED_DIR / "grid_cells.geojson"
    if not geojson_path.exists():
        return jsonify({
            "error": "Grid cell evaluation layer not yet generated. Complete Phase 2 feature processing first.",
            "code": "GRID_NOT_READY",
        }), 503

    try:
        data = json.loads(geojson_path.read_text(encoding="utf-8"))
        min_fsi = request.args.get("min_fsi", type=float)
        class_filter = request.args.get("class", type=str)

        features = data.get("features", [])
        if min_fsi is not None:
            features = [f for f in features if f.get("properties", {}).get("fsi", 0) >= min_fsi]
        if class_filter:
            features = [f for f in features if f.get("properties", {}).get("fsi_class") == class_filter]

        return jsonify({
            "type": "FeatureCollection",
            "total_cells": len(features),
            "model_version": predictor_service.config.get("version", "fsi_v1.0") if predictor_service.config else "fsi_v1.0",
            "features": features,
        }), 200
    except Exception as exc:
        log.error("Failed to read grid_cells.geojson: %s", exc)
        return jsonify({"error": f"Failed reading grid layer: {exc}", "code": "GRID_READ_ERROR"}), 500


@api_bp.route("/model/metrics", methods=["GET"])
def get_model_metrics():
    """Returns methodology details, feature weights, and validation statistics."""
    cfg = predictor_service.config or {}
    report_path = REPORTS_DIR / "feature_report.json"
    feature_report = {}
    if report_path.exists():
        try:
            feature_report = json.loads(report_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    return jsonify({
        "model_version": cfg.get("version", "fsi_v1.0"),
        "prediction_mode": cfg.get("prediction_mode", "susceptibility_index"),
        "weights": cfg.get("weights", {}),
        "inverted_features": cfg.get("inverted_features", []),
        "classification_thresholds": cfg.get("classification_thresholds", {}),
        "methodology_source": cfg.get("weight_source", "AHP literature synthesis (Arya & Kumar 2023)"),
        "feature_summary": feature_report.get("features", {}),
        "class_distribution": feature_report.get("fsi_class_distribution", {}),
        "fsi_mean": feature_report.get("fsi_mean"),
        "fsi_std": feature_report.get("fsi_std"),
        "supervised_ml": {
            "status": "disabled",
            "reason": "Target survey dates missing; sample size (25) insufficient for un-biased supervised train/test splitting.",
            "minimum_requirements_for_ml": ">=200 temporally timestamped points with negative verification samples.",
        },
    }), 200


@api_bp.route("/predict", methods=["POST"])
def predict():
    """Calculates susceptibility for a query coordinate and logs the inference."""
    payload = request.get_json(silent=True)
    is_valid, err_msg, parsed = validate_predict_payload(payload)
    if not is_valid:
        return jsonify({"error": err_msg, "code": "VALIDATION_ERROR"}), 422

    lat = parsed["latitude"]
    lon = parsed["longitude"]

    ok, p_err, result = predictor_service.predict_point(lat, lon)
    if not ok:
        return jsonify({"error": p_err, "code": "PREDICTOR_ERROR"}), 503

    # Log to MongoDB if connected
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **result,
    }
    col = get_predictions_collection()
    if col is not None:
        try:
            # Insert a copy without MongoDB mutating our dict with _id
            col.insert_one(dict(record))
        except Exception as e:
            log.warning("Failed saving prediction to MongoDB: %s", e)

    return jsonify(record), 200


@api_bp.route("/predictions", methods=["GET"])
def get_prediction_history():
    """Retrieves stored prediction records from MongoDB."""
    if not is_db_connected():
        return jsonify({
            "error": "Prediction history is unavailable because MongoDB is not connected.",
            "code": "DB_UNAVAILABLE",
            "note": "Start MongoDB locally or via docker-compose up -d to enable persistent history.",
        }), 503

    col = get_predictions_collection()
    if col is None:
        return jsonify({"error": "Collection handle not available", "code": "DB_ERROR"}), 500

    try:
        limit = min(request.args.get("limit", default=50, type=int), 200)
        offset = max(request.args.get("offset", default=0, type=int), 0)

        cursor = col.find({}, {"_id": 0}).sort("timestamp", -1).skip(offset).limit(limit)
        items = list(cursor)
        total = col.count_documents({})

        return jsonify({
            "total": total,
            "limit": limit,
            "offset": offset,
            "predictions": items,
        }), 200
    except Exception as exc:
        log.error("Failed fetching predictions: %s", exc)
        return jsonify({"error": "Unable to retrieve prediction history.", "code": "DB_QUERY_ERROR"}), 500