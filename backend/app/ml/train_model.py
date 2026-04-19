"""Training pipeline for drug discovery models."""
import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from xgboost import XGBClassifier
from sklearn.ensemble import RandomForestClassifier
from typing import Dict, Tuple, Optional
from app.ml.featurizer import featurize_batch
from app.config import MODEL_DIR


def train_model(
    smiles_list: list,
    labels: list,
    model_type: str = "xgboost",
    model_id: str = "default",
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[object, Dict[str, float]]:
    """Train a classification model on molecular data.
    
    Args:
        smiles_list: List of SMILES strings
        labels: List of binary labels (0/1)
        model_type: 'xgboost' or 'random_forest'
        model_id: Identifier for saving the model
        test_size: Fraction of data for testing
        random_state: Random seed

    Returns:
        Tuple of (trained model, metrics dict)
    """
    # Featurize
    X, valid_indices, failed = featurize_batch(smiles_list)
    y = np.array([labels[i] for i in valid_indices])

    if len(X) < 10:
        raise ValueError(f"Too few valid molecules ({len(X)}). Need at least 10.")

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # Create model
    if model_type == "xgboost":
        model = XGBClassifier(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state,
            eval_metric="logloss",
            use_label_encoder=False,
        )
    elif model_type == "random_forest":
        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=10,
            random_state=random_state,
            n_jobs=-1,
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    # Train
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:, 1]

    metrics = {
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1_score": round(f1_score(y_test, y_pred, zero_division=0), 4),
        "roc_auc": round(roc_auc_score(y_test, y_proba), 4),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "failed_molecules": len(failed),
    }

    # Save model
    model_path = os.path.join(MODEL_DIR, f"{model_id}_model.joblib")
    joblib.dump(model, model_path)

    # Save metrics
    metrics_path = os.path.join(MODEL_DIR, f"{model_id}_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    return model, metrics


def load_model(model_id: str = "default") -> Optional[object]:
    """Load a trained model from disk."""
    model_path = os.path.join(MODEL_DIR, f"{model_id}_model.joblib")
    if os.path.exists(model_path):
        return joblib.load(model_path)
    return None
