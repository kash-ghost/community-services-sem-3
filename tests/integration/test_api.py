# -*- coding: utf-8 -*-
"""
test_api.py
-----------
Comprehensive integration tests for backend Flask REST API endpoints.
"""
import pytest
from backend.app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "ok"
    assert "database" in data
    assert "model" in data


def test_metadata_endpoint(client):
    res = client.get("/api/v1/metadata")
    assert res.status_code == 200
    data = res.get_json()
    assert data["study_area"]["name"] == "Gurugram, Haryana, India"
    assert len(data["datasets"]) >= 4
    assert data["supervised_ml_feasible"] is False


def test_predict_validation_error(client):
    res = client.post("/api/v1/predict", json={"latitude": 10.0, "longitude": 77.0})
    assert res.status_code == 422
    data = res.get_json()
    assert data["code"] == "VALIDATION_ERROR"
    assert "out of bounds" in data["error"]


def test_predict_valid_coordinate(client):
    # Query Gurugram central coordinate
    res = client.post("/api/v1/predict", json={"latitude": 28.4595, "longitude": 77.0266})
    assert res.status_code == 200
    data = res.get_json()
    assert "prediction_id" in data
    assert "cell_id" in data
    assert "fsi" in data["result"]
    assert 0.0 <= data["result"]["fsi"] <= 1.0
    assert data["result"]["fsi_class"] in ["low", "moderate", "high", "very_high"]
    assert "features" in data
    assert "elevation_m" in data["features"]
    assert "feature_contributions" in data
    assert len(data["limitations"]) > 0


def test_observations_endpoint(client):
    res = client.get("/api/v1/observations")
    assert res.status_code == 200
    data = res.get_json()
    assert data["type"] == "FeatureCollection"
    assert data["count"] == 25
    assert len(data["features"]) == 25


def test_areas_endpoint(client):
    res = client.get("/api/v1/areas")
    assert res.status_code == 200
    data = res.get_json()
    assert data["type"] == "FeatureCollection"
    assert data["total_cells"] > 5000
    assert len(data["features"]) > 5000


def test_model_metrics_endpoint(client):
    res = client.get("/api/v1/model/metrics")
    assert res.status_code == 200
    data = res.get_json()
    assert data["prediction_mode"] == "susceptibility_index"
    assert "elevation_m" in data["weights"]
    assert data["supervised_ml"]["status"] == "disabled"


def test_predictions_db_handling(client):
    res = client.get("/api/v1/predictions")
    assert res.status_code in (200, 503)
