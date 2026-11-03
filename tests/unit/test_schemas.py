# -*- coding: utf-8 -*-
"""
test_schemas.py
---------------
Unit tests for API request validation schemas.
"""
import pytest
from backend.schemas.prediction import validate_predict_payload


def test_valid_payload():
    payload = {"latitude": 28.4595, "longitude": 77.0266}
    is_valid, err, parsed = validate_predict_payload(payload)
    assert is_valid is True
    assert err is None
    assert parsed["latitude"] == 28.4595
    assert parsed["longitude"] == 77.0266


def test_missing_coordinates():
    is_valid, err, parsed = validate_predict_payload({"latitude": 28.45})
    assert is_valid is False
    assert "longitude" in err

    is_valid, err, parsed = validate_predict_payload({"longitude": 77.02})
    assert is_valid is False
    assert "latitude" in err


def test_non_numeric_coordinates():
    is_valid, err, parsed = validate_predict_payload({"latitude": "invalid", "longitude": 77.02})
    assert is_valid is False
    assert "numeric" in err


def test_out_of_bounds():
    # North of Gurugram boundary
    is_valid, err, parsed = validate_predict_payload({"latitude": 29.5, "longitude": 77.02})
    assert is_valid is False
    assert "out of bounds" in err

    # West of Gurugram boundary
    is_valid, err, parsed = validate_predict_payload({"latitude": 28.4, "longitude": 75.0})
    assert is_valid is False
    assert "out of bounds" in err


def test_non_dict_payload():
    is_valid, err, parsed = validate_predict_payload(["not", "a", "dict"])
    assert is_valid is False
    assert "JSON object" in err
