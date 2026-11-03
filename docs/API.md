# API DOCUMENTATION
# Flood Vulnerability Prediction Framework — Gurugram, Haryana
# Version: v1

Base URL (development): http://localhost:5000/api/v1

All responses are JSON. Timestamps are ISO 8601 UTC strings.
Errors return { "error": "<message>", "code": "<code>" }.

---

## GET /api/v1/health

Health check.

### Response 200
```json
{
  "status": "ok",
  "timestamp": "2026-10-20T18:00:00Z",
  "database": "connected",
  "model": "fsi_v1.0"
}
```
If MongoDB is unavailable: `"database": "unavailable"` (still returns 200; only DB-dependent routes fail).

---

## GET /api/v1/metadata

Returns study area, dataset coverage summary, and model version.

### Response 200
```json
{
  "study_area": {
    "name": "Gurugram, Haryana, India",
    "bbox": [76.80, 28.20, 77.25, 28.55],
    "crs": "EPSG:4326"
  },
  "prediction_unit": "500m x 500m grid cells",
  "prediction_mode": "susceptibility_index",
  "model_version": "fsi_v1.0",
  "datasets": [
    {"id": "DS-001", "name": "GMDA Flood Survey v2", "status": "loaded", "records": 25},
    {"id": "DS-002", "name": "Open-Meteo Rainfall", "status": "loaded"},
    {"id": "DS-004", "name": "Copernicus DEM GLO-30", "status": "loaded"},
    {"id": "DS-005", "name": "ESA WorldCover 2021", "status": "loaded"},
    {"id": "DS-006", "name": "OSM Waterways", "status": "loaded"}
  ],
  "last_updated": "2026-10-20T18:00:00Z"
}
```

---

## GET /api/v1/observations

Returns GMDA waterlogging observation points.

### Query parameters
None.

### Response 200
```json
{
  "type": "FeatureCollection",
  "count": 25,
  "data_limitations": [
    "surveydate is NULL for all 25 records — temporal analysis not supported",
    "These are inspection survey points, not dated flood-event records"
  ],
  "features": [
    {
      "type": "Feature",
      "geometry": {"type": "Point", "coordinates": [77.0044, 28.4012]},
      "properties": {
        "objectid": 406,
        "surveytype": "Waterlogging",
        "waterloggingtype": null,
        "zone": null,
        "sector": null,
        "remarks": "GMDA Jurisdiction"
      }
    }
  ]
}
```

---

## GET /api/v1/areas

Returns all grid cells with FSI scores as a GeoJSON FeatureCollection.

### Query parameters
| Param | Type | Description |
|---|---|---|
| `min_fsi` | float | Filter cells with FSI ≥ value (optional) |
| `class` | string | Filter by class: low, moderate, high, very_high (optional) |

### Response 200
```json
{
  "type": "FeatureCollection",
  "total_cells": 112,
  "generated_at": "2026-10-20T18:00:00Z",
  "model_version": "fsi_v1.0",
  "features": [
    {
      "type": "Feature",
      "geometry": {"type": "Polygon", "coordinates": [[...]]},
      "properties": {
        "cell_id": "C_042",
        "fsi": 0.73,
        "fsi_class": "high",
        "elevation_m": 214.3,
        "slope_deg": 0.8,
        "built_up_frac": 0.72,
        "dist_to_water_m": 320.0,
        "dist_to_drain_m": 180.0
      }
    }
  ]
}
```

---

## GET /api/v1/model/metrics

Returns FSI configuration, sensitivity analysis results, and (if available) supervised ML metrics.

### Response 200
```json
{
  "model_version": "fsi_v1.0",
  "prediction_mode": "susceptibility_index",
  "fsi_weights": {
    "elevation_m": 0.30,
    "slope_deg": 0.20,
    "built_up_frac": 0.15,
    "dist_to_water_m": 0.15,
    "dist_to_drain_m": 0.10,
    "veg_frac": 0.05,
    "water_frac": 0.03,
    "monsoon_rainfall_mm": 0.02
  },
  "gmda_validation": {
    "description": "Proportion of GMDA waterlogging points in High/Very High FSI cells",
    "points_in_high_susceptibility": null,
    "note": "Calculated after Phase 3"
  },
  "supervised_ml": null,
  "supervised_ml_note": "Not available — insufficient labelled training data (see METHODOLOGY.md)"
}
```

---

## POST /api/v1/predict

Calculates the FSI for a given coordinate.

### Request body
```json
{
  "latitude": 28.4595,
  "longitude": 77.0266
}
```

### Validation rules
- `latitude`: float, 28.20 ≤ lat ≤ 28.55
- `longitude`: float, 76.80 ≤ lon ≤ 77.25
- Coordinate must fall within a grid cell with feature data

### Response 200
```json
{
  "prediction_id": "pred_abc123",
  "timestamp": "2026-10-20T18:00:00Z",
  "model_version": "fsi_v1.0",
  "prediction_mode": "susceptibility_index",
  "input": {"latitude": 28.4595, "longitude": 77.0266},
  "cell_id": "C_058",
  "result": {
    "fsi": 0.61,
    "fsi_class": "high",
    "fsi_class_label": "High Susceptibility"
  },
  "features": {
    "elevation_m": 211.2,
    "slope_deg": 0.6,
    "built_up_frac": 0.68,
    "veg_frac": 0.12,
    "water_frac": 0.02,
    "dist_to_water_m": 450.0,
    "dist_to_drain_m": 220.0,
    "monsoon_rainfall_mm": 620.0
  },
  "feature_contributions": {
    "elevation_m": 0.195,
    "slope_deg": 0.127,
    "built_up_frac": 0.095,
    "dist_to_water_m": 0.088,
    "dist_to_drain_m": 0.056,
    "veg_frac": 0.028,
    "water_frac": 0.011,
    "monsoon_rainfall_mm": 0.009
  },
  "limitations": [
    "FSI is a heuristic susceptibility index, not a calibrated flood probability",
    "Elevation derived from DSM — may be inflated by building heights",
    "Land cover data is from 2021"
  ]
}
```

### Response 422 — Validation Error
```json
{"error": "Coordinate out of study area bounds", "code": "COORD_OUT_OF_BOUNDS"}
```

### Response 503 — Model Not Ready
```json
{"error": "FSI model not yet built. Run python ml/train.py first.", "code": "MODEL_NOT_READY"}
```

---

## GET /api/v1/predictions

Returns prediction history from MongoDB.

### Query parameters
| Param | Type | Description |
|---|---|---|
| `limit` | int | Max records to return (default: 50, max: 200) |
| `offset` | int | Pagination offset (default: 0) |
| `model_version` | string | Filter by model version |

### Response 200
```json
{
  "total": 15,
  "limit": 50,
  "offset": 0,
  "predictions": [
    {
      "prediction_id": "pred_abc123",
      "timestamp": "2026-10-20T18:00:00Z",
      "model_version": "fsi_v1.0",
      "input": {"latitude": 28.4595, "longitude": 77.0266},
      "fsi": 0.61,
      "fsi_class": "high"
    }
  ]
}
```

### Response 503 — Database Unavailable
```json
{"error": "Prediction history unavailable — database not connected", "code": "DB_UNAVAILABLE"}
```
