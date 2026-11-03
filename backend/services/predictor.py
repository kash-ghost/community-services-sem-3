# -*- coding: utf-8 -*-
"""
predictor.py
------------
Inference service for the Flood Susceptibility Index (FSI).
Performs spatial lookup for query coordinates, calculates feature contributions,
and returns transparent decision-support outputs.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DIR = ROOT / "data" / "processed"
MODELS_DIR = ROOT / "models"


class FloodPredictor:
    def __init__(self):
        self.features_df: Optional[pd.DataFrame] = None
        self.config: Optional[Dict[str, Any]] = None
        self.is_loaded: bool = False
        self.load()

    def load(self):
        """Loads features and FSI configuration from disk."""
        cfg_path = MODELS_DIR / "fsi_config.json"
        pq_path = PROCESSED_DIR / "features.parquet"

        if cfg_path.exists():
            try:
                self.config = json.loads(cfg_path.read_text(encoding="utf-8"))
            except Exception as e:
                log.error("Failed to load fsi_config.json: %s", e)

        if pq_path.exists():
            try:
                self.features_df = pd.read_parquet(pq_path)
                self.is_loaded = True
                log.info("Loaded features table with %d cells", len(self.features_df))
            except Exception as e:
                log.error("Failed to load features.parquet: %s", e)

    def predict_point(self, lat: float, lon: float) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Locates the nearest grid cell for (lat, lon) and returns susceptibility breakdown.
        """
        if not self.is_loaded or self.features_df is None or self.config is None:
            # Try reloading once in case files were generated recently
            self.load()
            if not self.is_loaded or self.features_df is None or self.config is None:
                return (
                    False,
                    "Prediction pipeline not ready. Processed features or FSI config are missing.",
                    None,
                )

        df = self.features_df
        # Distance squared to centroids (in degrees)
        dists = (df["centroid_lat"] - lat) ** 2 + (df["centroid_lon"] - lon) ** 2
        nearest_idx = dists.idxmin()
        nearest_row = df.loc[nearest_idx]

        cell_id = str(nearest_row["cell_id"])
        fsi_val = float(nearest_row["fsi"])
        fsi_class = str(nearest_row["fsi_class"])

        class_labels = {
            "low": "Low Susceptibility",
            "moderate": "Moderate Susceptibility",
            "high": "High Susceptibility",
            "very_high": "Very High Susceptibility",
            "unknown": "Indeterminate / Insufficient Data",
        }

        weights = self.config.get("weights", {})
        inverted = set(self.config.get("inverted_features", []))

        # Extract raw features and calculate individual normalized contributions
        feature_vals = {}
        contributions = {}
        for feat, w in weights.items():
            if feat in nearest_row and pd.notna(nearest_row[feat]):
                val = float(nearest_row[feat])
                feature_vals[feat] = round(val, 4)

                # Normalized contribution calculation
                col_min = float(df[feat].min())
                col_max = float(df[feat].max())
                if col_max > col_min:
                    norm = (val - col_min) / (col_max - col_min)
                else:
                    norm = 0.0

                if feat in inverted:
                    norm = 1.0 - norm

                contributions[feat] = round(float(norm * w), 4)
            else:
                feature_vals[feat] = None
                contributions[feat] = 0.0

        result = {
            "prediction_id": f"pred_{cell_id}_{int(lat * 10000)}_{int(lon * 10000)}",
            "model_version": self.config.get("version", "fsi_v1.0"),
            "prediction_mode": self.config.get("prediction_mode", "susceptibility_index"),
            "input": {"latitude": lat, "longitude": lon},
            "cell_id": cell_id,
            "result": {
                "fsi": round(fsi_val, 4),
                "fsi_class": fsi_class,
                "fsi_class_label": class_labels.get(fsi_class, fsi_class.capitalize()),
            },
            "features": feature_vals,
            "feature_contributions": contributions,
            "limitations": [
                "FSI is a heuristic multi-criteria decision-support index, not a calibrated hydrological flood probability.",
                "Topography is based on Copernicus 30m DSM, which captures rooftop surface elevation in dense urban corridors.",
                "Land cover distribution reflects 2021 ESA WorldCover baselines; recent urbanization may alter local permeability.",
                "OSM drainage lines represent mapped formal channels and may omit unrecorded roadside culverts.",
            ],
        }
        return True, None, result


# Global singleton instance
predictor_service = FloodPredictor()
