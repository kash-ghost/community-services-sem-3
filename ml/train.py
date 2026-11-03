# -*- coding: utf-8 -*-
"""
train.py
--------
Phase 3 -- Machine Learning Training & Evaluation Module

Trains Baseline Logistic Regression and Random Forest Classifier ONLY if
empirically validated target labels exist in data/processed/labels.parquet.

Integrity rules:
- Never trains on synthetic or fabricated labels.
- Evaluates held-out splits strictly (never reports train-set metrics as test performance).
- If labelled data is insufficient (<200 records), exits cleanly without generating deceptive metrics.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
import sys
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
MODELS = ROOT / "models"
REPORTS = ROOT / "data" / "reports"
MODELS.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

FEATURE_COLS = [
    "elevation_m",
    "slope_deg",
    "built_up_frac",
    "dist_to_water_m",
    "dist_to_drain_m",
    "veg_frac",
    "water_frac",
    "monsoon_rainfall_mm",
]


def train_supervised_models(df: pd.DataFrame):
    """Executes baseline and Random Forest training on empirical labels."""
    log.info("Initiating supervised ML training on %d labelled records...", len(df))
    X = df[FEATURE_COLS].copy()
    y = df["target"].astype(int)

    # Impute or drop NaNs
    X = X.fillna(X.median())

    # Held-out split (70% train, 30% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.30, random_state=42, stratify=y
    )

    # Scaler for baseline Logistic Regression
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 1. Baseline: Logistic Regression
    baseline_lr = LogisticRegression(class_weight="balanced", random_state=42, max_iter=1000)
    baseline_lr.fit(X_train_scaled, y_train)
    lr_preds = baseline_lr.predict(X_test_scaled)
    lr_probs = baseline_lr.predict_proba(X_test_scaled)[:, 1]

    # 2. Random Forest Classifier
    rf = RandomForestClassifier(
        n_estimators=100,
        max_depth=6,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)
    rf_preds = rf.predict(X_test)
    rf_probs = rf.predict_proba(X_test)[:, 1]

    # Compute genuine test metrics
    metrics = {
        "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "baseline_logistic_regression": {
            "precision": round(float(precision_score(y_test, lr_preds, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, lr_preds, zero_division=0)), 4),
            "f1": round(float(f1_score(y_test, lr_preds, zero_division=0)), 4),
            "roc_auc": round(float(roc_auc_score(y_test, lr_probs)), 4),
            "confusion_matrix": confusion_matrix(y_test, lr_preds).tolist(),
        },
        "random_forest": {
            "precision": round(float(precision_score(y_test, rf_preds, zero_division=0)), 4),
            "recall": round(float(recall_score(y_test, rf_preds, zero_division=0)), 4),
            "f1": round(float(f1_score(y_test, rf_preds, zero_division=0)), 4),
            "roc_auc": round(float(roc_auc_score(y_test, rf_probs)), 4),
            "confusion_matrix": confusion_matrix(y_test, rf_preds).tolist(),
            "feature_importances": {
                feat: round(float(imp), 4) for feat, imp in zip(FEATURE_COLS, rf.feature_importances_)
            },
        },
    }

    # Save artifacts
    joblib.dump(baseline_lr, MODELS / "baseline_lr.pkl")
    joblib.dump(rf, MODELS / "random_forest.pkl")
    joblib.dump(scaler, MODELS / "scaler.pkl")

    eval_out = REPORTS / "evaluation_report.json"
    eval_out.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    log.info("Model artifacts and test evaluation report saved to %s", eval_out.name)


def main():
    log.info("Checking data availability for supervised ML training...")
    labels_file = PROCESSED / "labels.parquet"

    if not labels_file.exists():
        log.info(
            "INFO: No empirical supervised labels file found at %s. "
            "In accordance with project integrity standards, supervised ML training is deferred. "
            "The system is currently operating in Flood Susceptibility Index (FSI) mode.",
            labels_file,
        )
        # Record training status report
        report = {
            "status": "deferred",
            "active_mode": "Flood Susceptibility Index (FSI)",
            "supervised_models_trained": False,
            "reason": "Empirical ground-truth flood inundation polygons with timestamps are not present in public GMDA survey.",
            "ml_scaffold_status": "Ready for deployment upon ingestion of verified labels.parquet.",
        }
        (REPORTS / "training_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return

    df = pd.read_parquet(labels_file)
    if len(df) < 200 or "target" not in df.columns or df["target"].nunique() < 2:
        log.warning("Insufficient or imbalanced data in labels.parquet. Minimum 200 binary samples required.")
        return

    train_supervised_models(df)


if __name__ == "__main__":
    main()
