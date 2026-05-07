"""Training pipeline for drug discovery models.

Supports:
- Binary classification (BBBP, BACE)
- Multi-label classification (Tox21 — 12 endpoints)
- Regression (ESOL — solubility)
- Scaffold splitting for chemical diversity
- Cross-validation with stratified folds
"""
import os
import json
import logging
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from sklearn.model_selection import (
    train_test_split, StratifiedKFold, KFold, cross_val_score,
)
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, mean_squared_error, mean_absolute_error, r2_score,
)
from xgboost import XGBClassifier, XGBRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from typing import Dict, Tuple, Optional, List, Any

from app.ml.featurizer import featurize_batch, create_scaler, apply_scaler
from app.config import MODEL_DIR

logger = logging.getLogger(__name__)


# ── Scaffold Splitting ────────────────────────────────────────────

def _scaffold_split(
    smiles_list: List[str],
    labels: np.ndarray,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, List[int], List[int]]:
    """Split data by molecular scaffold for more realistic evaluation.

    Molecules with the same core scaffold go into the same split,
    preventing data leakage from similar structures.
    """
    try:
        from rdkit import Chem
        from rdkit.Chem.Scaffolds.MurckoScaffold import MurckoScaffoldSmiles

        scaffolds = {}
        for i, smi in enumerate(smiles_list):
            try:
                mol = Chem.MolFromSmiles(smi)
                if mol is not None:
                    scaffold = MurckoScaffoldSmiles(
                        mol=mol, includeChirality=False
                    )
                else:
                    scaffold = f"_invalid_{i}"
            except Exception:
                scaffold = f"_error_{i}"

            scaffolds.setdefault(scaffold, []).append(i)

        # Sort scaffolds by size (largest first) for deterministic splitting
        scaffold_sets = sorted(
            scaffolds.values(), key=len, reverse=True
        )

        train_indices = []
        test_indices = []
        n_total = len(smiles_list)
        n_test = int(n_total * test_size)

        rng = np.random.RandomState(random_state)
        # Shuffle scaffold sets for randomness
        scaffold_sets_shuffled = list(scaffold_sets)
        rng.shuffle(scaffold_sets_shuffled)

        for scaffold_idxs in scaffold_sets_shuffled:
            if len(test_indices) < n_test:
                test_indices.extend(scaffold_idxs)
            else:
                train_indices.extend(scaffold_idxs)

        # Handle edge case: if test set is too large, move some to train
        if len(test_indices) > int(n_total * test_size * 1.5):
            excess = test_indices[n_test:]
            train_indices.extend(excess)
            test_indices = test_indices[:n_test]

        train_indices = sorted(train_indices)
        test_indices = sorted(test_indices)

        if labels.ndim == 1:
            return (
                None, None,  # X placeholders — caller maps by indices
                labels[train_indices], labels[test_indices],
                train_indices, test_indices,
            )
        else:
            return (
                None, None,
                labels[train_indices], labels[test_indices],
                train_indices, test_indices,
            )

    except ImportError:
        logger.warning("RDKit scaffold split unavailable, falling back to random.")
        return None, None, None, None, None, None


# ── Model Creation ────────────────────────────────────────────────

def _create_model(
    model_type: str, task_type: str, random_state: int = 42
) -> Any:
    """Create a fresh model instance."""
    if task_type == "regression":
        if model_type == "xgboost":
            return XGBRegressor(
                n_estimators=300,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.1,
                reg_lambda=1.0,
                random_state=random_state,
                n_jobs=-1,
            )
        elif model_type == "random_forest":
            return RandomForestRegressor(
                n_estimators=300,
                max_depth=12,
                random_state=random_state,
                n_jobs=-1,
            )
    else:  # classification
        if model_type == "xgboost":
            return XGBClassifier(
                n_estimators=300,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                reg_alpha=0.1,
                reg_lambda=1.0,
                random_state=random_state,
                eval_metric="logloss",
                n_jobs=-1,
            )
        elif model_type == "random_forest":
            return RandomForestClassifier(
                n_estimators=300,
                max_depth=12,
                random_state=random_state,
                n_jobs=-1,
            )

    raise ValueError(f"Unknown model_type={model_type}, task_type={task_type}")


# ── Single-Task Training ─────────────────────────────────────────

def train_model(
    smiles_list: list,
    labels: list,
    model_type: str = "xgboost",
    task_type: str = "classification",
    model_id: str = "default",
    test_size: float = 0.2,
    random_state: int = 42,
    use_scaffold_split: bool = True,
    use_maccs: bool = False,
    use_extended_descriptors: bool = False,
) -> Tuple[object, Dict[str, float]]:
    """Train a single-task model on molecular data.

    Args:
        smiles_list: List of SMILES strings
        labels: List of labels (0/1 for classification, float for regression)
        model_type: 'xgboost' or 'random_forest'
        task_type: 'classification' or 'regression'
        model_id: Identifier for saving the model
        test_size: Fraction of data for testing
        random_state: Random seed
        use_scaffold_split: Use scaffold-based splitting
        use_maccs: Include MACCS fingerprint features
        use_extended_descriptors: Include extended RDKit descriptors

    Returns:
        Tuple of (trained model, metrics dict)
    """
    logger.info(f"Training {model_id}: {model_type}/{task_type} on {len(smiles_list)} molecules")

    # Featurize
    X, valid_indices, failed = featurize_batch(
        smiles_list,
        use_maccs=use_maccs,
        use_extended_descriptors=use_extended_descriptors,
    )
    y_full = np.array(labels)
    y = y_full[valid_indices]

    if len(X) < 10:
        raise ValueError(f"Too few valid molecules ({len(X)}). Need at least 10.")

    logger.info(f"Featurized: {len(X)} valid, {len(failed)} failed")

    # Handle NaN labels (common in Tox21)
    valid_label_mask = ~np.isnan(y) if np.issubdtype(y.dtype, np.floating) else np.ones(len(y), dtype=bool)
    X = X[valid_label_mask]
    y = y[valid_label_mask]
    valid_smiles = [smiles_list[valid_indices[i]] for i, m in enumerate(valid_label_mask) if m]

    if len(X) < 10:
        raise ValueError(f"Too few molecules with valid labels ({len(X)}).")

    # Split
    scaler = None
    if use_scaffold_split:
        _, _, y_train_sc, y_test_sc, train_idx, test_idx = _scaffold_split(
            valid_smiles, y, test_size=test_size, random_state=random_state,
        )
        if train_idx is not None:
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y_train_sc, y_test_sc
        else:
            # Fallback
            if task_type == "classification":
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=test_size, random_state=random_state,
                    stratify=y,
                )
            else:
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=test_size, random_state=random_state,
                )
    else:
        if task_type == "classification":
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state,
                stratify=y,
            )
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=random_state,
            )

    # Scale features for regression
    if task_type == "regression":
        scaler = create_scaler(X_train)
        X_train = apply_scaler(X_train, scaler)
        X_test = apply_scaler(X_test, scaler)

    # Convert labels to int for classification
    if task_type == "classification":
        y_train = y_train.astype(int)
        y_test = y_test.astype(int)

    # Create and train model
    model = _create_model(model_type, task_type, random_state)

    logger.info(f"Training on {len(X_train)} samples, testing on {len(X_test)}...")
    model.fit(X_train, y_train)

    # Evaluate
    if task_type == "classification":
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, "predict_proba") else y_pred.astype(float)

        metrics = {
            "accuracy": round(accuracy_score(y_test, y_pred), 4),
            "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
            "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
            "f1_score": round(f1_score(y_test, y_pred, zero_division=0), 4),
            "roc_auc": round(roc_auc_score(y_test, y_proba), 4),
        }
    else:  # regression
        y_pred = model.predict(X_test)
        metrics = {
            "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 4),
            "mae": round(float(mean_absolute_error(y_test, y_pred)), 4),
            "r2": round(float(r2_score(y_test, y_pred)), 4),
        }

    metrics.update({
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "failed_molecules": len(failed),
        "total_molecules": len(smiles_list),
        "task_type": task_type,
        "model_type": model_type,
        "model_id": model_id,
        "trained_at": datetime.utcnow().isoformat(),
        "use_scaffold_split": use_scaffold_split,
    })

    # Save model
    model_path = os.path.join(MODEL_DIR, f"{model_id}_model.joblib")
    joblib.dump(model, model_path)
    logger.info(f"Saved model → {model_path}")

    # Save scaler if regression
    if scaler is not None:
        scaler_path = os.path.join(MODEL_DIR, f"{model_id}_scaler.joblib")
        joblib.dump(scaler, scaler_path)
        logger.info(f"Saved scaler → {scaler_path}")

    # Save metrics
    metrics_path = os.path.join(MODEL_DIR, f"{model_id}_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info(f"Training complete: {json.dumps({k: v for k, v in metrics.items() if isinstance(v, (int, float))}, indent=2)}")

    return model, metrics


# ── Multi-Label Training (Tox21) ──────────────────────────────────

def train_multilabel_model(
    smiles_list: list,
    labels: np.ndarray,
    target_names: List[str],
    model_type: str = "xgboost",
    model_id: str = "toxicity_tox21",
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[List[object], Dict[str, Any]]:
    """Train separate binary classifiers for each Tox21 endpoint.

    Returns:
        models: List of trained models (one per endpoint)
        combined_metrics: Aggregated metrics dict
    """
    logger.info(f"Training multi-label model {model_id} with {len(target_names)} endpoints")

    # Featurize once
    X, valid_indices, failed = featurize_batch(smiles_list)

    if len(X) < 10:
        raise ValueError(f"Too few valid molecules ({len(X)})")

    models = []
    endpoint_metrics = {}
    roc_aucs = []

    for i, target_name in enumerate(target_names):
        if labels.ndim == 1:
            y_full = labels
        else:
            y_full = labels[:, i]

        # Get labels for valid molecules
        y = y_full[valid_indices]

        # Drop NaN labels (very common in Tox21)
        valid_mask = ~np.isnan(y)
        X_task = X[valid_mask]
        y_task = y[valid_mask].astype(int)

        if len(X_task) < 20 or len(np.unique(y_task)) < 2:
            logger.warning(f"Skipping endpoint {target_name}: insufficient data ({len(X_task)} samples)")
            models.append(None)
            endpoint_metrics[target_name] = {"status": "skipped", "reason": "insufficient_data"}
            continue

        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X_task, y_task, test_size=test_size,
                random_state=random_state, stratify=y_task,
            )

            model = _create_model(model_type, "classification", random_state)
            model.fit(X_train, y_train)

            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)[:, 1]

            auc = roc_auc_score(y_test, y_proba)
            roc_aucs.append(auc)

            endpoint_metrics[target_name] = {
                "accuracy": round(accuracy_score(y_test, y_pred), 4),
                "roc_auc": round(auc, 4),
                "f1_score": round(f1_score(y_test, y_pred, zero_division=0), 4),
                "train_samples": len(X_train),
                "test_samples": len(X_test),
                "positive_rate": round(float(y_task.mean()), 4),
            }

            models.append(model)
            logger.info(f"  {target_name}: AUC={auc:.4f}, n={len(X_task)}")

        except Exception as e:
            logger.error(f"  Failed to train {target_name}: {e}")
            models.append(None)
            endpoint_metrics[target_name] = {"status": "failed", "error": str(e)}

    # Save all models as a single bundle
    bundle = {
        "models": models,
        "target_names": target_names,
        "n_endpoints": len(target_names),
    }
    model_path = os.path.join(MODEL_DIR, f"{model_id}_model.joblib")
    joblib.dump(bundle, model_path)

    combined_metrics = {
        "model_id": model_id,
        "model_type": model_type,
        "task_type": "multilabel_classification",
        "n_endpoints": len(target_names),
        "n_trained": sum(1 for m in models if m is not None),
        "mean_roc_auc": round(float(np.mean(roc_aucs)), 4) if roc_aucs else 0.0,
        "total_molecules": len(smiles_list),
        "failed_molecules": len(failed),
        "trained_at": datetime.utcnow().isoformat(),
        "endpoint_metrics": endpoint_metrics,
    }

    metrics_path = os.path.join(MODEL_DIR, f"{model_id}_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(combined_metrics, f, indent=2)

    logger.info(f"Multi-label training complete: {combined_metrics['n_trained']}/{len(target_names)} endpoints, mean AUC={combined_metrics['mean_roc_auc']:.4f}")

    return models, combined_metrics


# ── Model Loading ─────────────────────────────────────────────────

def load_model(model_id: str = "default") -> Optional[object]:
    """Load a trained model from disk."""
    model_path = os.path.join(MODEL_DIR, f"{model_id}_model.joblib")
    if os.path.exists(model_path):
        return joblib.load(model_path)
    return None


def load_scaler(model_id: str) -> Optional[object]:
    """Load a fitted scaler from disk."""
    scaler_path = os.path.join(MODEL_DIR, f"{model_id}_scaler.joblib")
    if os.path.exists(scaler_path):
        return joblib.load(scaler_path)
    return None


def load_metrics(model_id: str) -> Optional[Dict]:
    """Load saved metrics for a model."""
    metrics_path = os.path.join(MODEL_DIR, f"{model_id}_metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path) as f:
            return json.load(f)
    return None
