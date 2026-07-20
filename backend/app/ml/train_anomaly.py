"""Train the IsolationForest anomaly detector and report precision/recall."""
from __future__ import annotations

import json
import os

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import (
    classification_report,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from app.ml.generate_data import generate_movement_data

FEATURES = ["speed_kmh", "dist_from_prev_m", "inactivity_min", "dist_from_route_m"]


def train(models_dir: str = "ml_models") -> dict:
    os.makedirs(models_dir, exist_ok=True)
    df = generate_movement_data()
    X = df[FEATURES].values
    y = df["label"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    scaler = StandardScaler().fit(X_train)
    Xtr, Xte = scaler.transform(X_train), scaler.transform(X_test)

    contamination = float(y_train.mean())  # expected anomaly fraction
    model = IsolationForest(
        n_estimators=200, contamination=contamination, random_state=42, n_jobs=-1
    )
    # Unsupervised: fit on training features only
    model.fit(Xtr)

    # Evaluate against known labels: predict -1 (anomaly) / 1 (normal)
    pred = model.predict(Xte)
    y_pred = (pred == -1).astype(int)
    scores = -model.decision_function(Xte)  # higher = more anomalous

    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test, y_pred, average="binary", zero_division=0
    )
    auc = roc_auc_score(y_test, scores)

    joblib.dump(model, os.path.join(models_dir, "anomaly_isoforest.joblib"))
    joblib.dump(scaler, os.path.join(models_dir, "anomaly_scaler.joblib"))

    metrics = {
        "model": "IsolationForest",
        "task": "anomaly detection (unsupervised)",
        "features": FEATURES,
        "n_train": len(X_train),
        "n_test": len(X_test),
        "contamination": round(contamination, 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1": round(float(f1), 4),
        "roc_auc": round(float(auc), 4),
    }
    print("=== IsolationForest anomaly detector ===")
    print(classification_report(y_test, y_pred, target_names=["normal", "anomaly"],
                                zero_division=0))
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    train()
