# -*- coding: utf-8 -*-
"""
prediction.py
-------------
Request validation schemas for the Flood Vulnerability prediction API.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# Supported study area bounds for Gurugram
MIN_LAT = 28.20
MAX_LAT = 28.55
MIN_LON = 76.80
MAX_LON = 77.25


def validate_predict_payload(data: Any) -> Tuple[bool, Optional[str], Optional[Dict[str, float]]]:
    """
    Validates the incoming JSON payload for /api/v1/predict.
    Returns (is_valid, error_message, parsed_data).
    """
    if not isinstance(data, dict):
        return False, "Request body must be a JSON object", None

    if "latitude" not in data or "longitude" not in data:
        return False, "Both 'latitude' and 'longitude' fields are required", None

    try:
        lat = float(data["latitude"])
        lon = float(data["longitude"])
    except (TypeError, ValueError):
        return False, "'latitude' and 'longitude' must be numeric values", None

    if not (MIN_LAT <= lat <= MAX_LAT):
        return (
            False,
            f"'latitude' {lat} is out of bounds. Supported range for Gurugram study area is [{MIN_LAT}, {MAX_LAT}]",
            None,
        )

    if not (MIN_LON <= lon <= MAX_LON):
        return (
            False,
            f"'longitude' {lon} is out of bounds. Supported range for Gurugram study area is [{MIN_LON}, {MAX_LON}]",
            None,
        )

    return True, None, {"latitude": lat, "longitude": lon}
