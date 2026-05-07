"""Bootstrap script — download datasets and train all production models.

Run once:  python -m app.ml.pretrain

This will:
1. Download BBBP, Tox21, ESOL, BACE from MoleculeNet
2. Train 4 specialized XGBoost models
3. Save everything to backend/app/ml/pretrained/
4. Generate a training_report.json with all metrics
"""
import json
import logging
import sys
import os
import time
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

import numpy as np

# Add parent to path so we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.ml.datasets import load_moleculenet_dataset, DATASET_REGISTRY
from app.ml.train_model import train_model, train_multilabel_model, load_metrics
from app.config import MODEL_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def pretrain_all():
    """Train all production models from MoleculeNet datasets."""
    print("\n" + "=" * 60)
    print("  MOLECULE-AI — Production Model Training")
    print("=" * 60 + "\n")

    start_time = time.time()
    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "models": {},
        "errors": [],
    }

    # ── 1. BBBP (Blood-Brain Barrier Penetration) ─────────────────
    try:
        logger.info("━━━ [1/4] Training BBBP Activity Model ━━━")
        smiles, labels, meta = load_moleculenet_dataset("bbbp")
        _, metrics = train_model(
            smiles_list=smiles,
            labels=labels.tolist(),
            model_type="xgboost",
            task_type="classification",
            model_id="activity_bbbp",
            use_scaffold_split=True,
        )
        report["models"]["activity_bbbp"] = metrics
        logger.info(f"✓ BBBP: ROC-AUC = {metrics.get('roc_auc', 'N/A')}")
    except Exception as e:
        logger.error(f"✗ BBBP training failed: {e}")
        report["errors"].append({"model": "activity_bbbp", "error": str(e)})

    # ── 2. Tox21 (Toxicity — 12 endpoints) ────────────────────────
    try:
        logger.info("\n━━━ [2/4] Training Tox21 Toxicity Model ━━━")
        smiles, labels, meta = load_moleculenet_dataset("tox21")
        target_names = meta.get("actual_target_columns", meta["target_columns"])
        _, metrics = train_multilabel_model(
            smiles_list=smiles,
            labels=labels,
            target_names=target_names,
            model_type="xgboost",
            model_id="toxicity_tox21",
        )
        report["models"]["toxicity_tox21"] = metrics
        logger.info(f"✓ Tox21: Mean AUC = {metrics.get('mean_roc_auc', 'N/A')}")
    except Exception as e:
        logger.error(f"✗ Tox21 training failed: {e}")
        report["errors"].append({"model": "toxicity_tox21", "error": str(e)})

    # ── 3. ESOL (Solubility — Regression) ─────────────────────────
    try:
        logger.info("\n━━━ [3/4] Training ESOL Solubility Model ━━━")
        smiles, labels, meta = load_moleculenet_dataset("esol")
        _, metrics = train_model(
            smiles_list=smiles,
            labels=labels.tolist(),
            model_type="xgboost",
            task_type="regression",
            model_id="solubility_esol",
            use_scaffold_split=True,
        )
        report["models"]["solubility_esol"] = metrics
        logger.info(f"✓ ESOL: RMSE = {metrics.get('rmse', 'N/A')}, R² = {metrics.get('r2', 'N/A')}")
    except Exception as e:
        logger.error(f"✗ ESOL training failed: {e}")
        report["errors"].append({"model": "solubility_esol", "error": str(e)})

    # ── 4. BACE (β-Secretase Inhibitors) ──────────────────────────
    try:
        logger.info("\n━━━ [4/4] Training BACE Activity Model ━━━")
        smiles, labels, meta = load_moleculenet_dataset("bace")
        _, metrics = train_model(
            smiles_list=smiles,
            labels=labels.tolist(),
            model_type="xgboost",
            task_type="classification",
            model_id="activity_bace",
            use_scaffold_split=True,
        )
        report["models"]["activity_bace"] = metrics
        logger.info(f"✓ BACE: ROC-AUC = {metrics.get('roc_auc', 'N/A')}")
    except Exception as e:
        logger.error(f"✗ BACE training failed: {e}")
        report["errors"].append({"model": "activity_bace", "error": str(e)})

    # ── Save Training Report ──────────────────────────────────────
    elapsed = time.time() - start_time
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    report["total_time_seconds"] = round(elapsed, 1)
    report["n_models_trained"] = len(report["models"])
    report["n_errors"] = len(report["errors"])

    report_path = MODEL_DIR / "training_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    # ── Summary ───────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  TRAINING COMPLETE")
    print("=" * 60)
    print(f"  Time elapsed: {elapsed:.1f}s")
    print(f"  Models trained: {report['n_models_trained']}")
    print(f"  Errors: {report['n_errors']}")
    print(f"  Report: {report_path}")
    print()

    for model_id, metrics in report["models"].items():
        task = metrics.get("task_type", "unknown")
        if task == "classification":
            print(f"  [OK] {model_id:25s}  AUC={metrics.get('roc_auc', 'N/A')}  F1={metrics.get('f1_score', 'N/A')}")
        elif task == "regression":
            print(f"  [OK] {model_id:25s}  RMSE={metrics.get('rmse', 'N/A')}  R2={metrics.get('r2', 'N/A')}")
        elif task == "multilabel_classification":
            print(f"  [OK] {model_id:25s}  Mean AUC={metrics.get('mean_roc_auc', 'N/A')}  Endpoints={metrics.get('n_trained', 'N/A')}/{metrics.get('n_endpoints', 'N/A')}")

    for err in report["errors"]:
        print(f"  [FAIL] {err['model']:25s}  ERROR: {err['error']}")

    print("=" * 60 + "\n")

    return report


if __name__ == "__main__":
    pretrain_all()
