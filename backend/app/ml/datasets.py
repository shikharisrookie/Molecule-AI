"""MoleculeNet dataset loaders for training production models.

Supports BBBP, Tox21, ESOL, and BACE — four gold-standard benchmarks
covering activity, toxicity, solubility, and target-specific inhibition.
"""
import os
import csv
import logging
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.config import DATA_DIR

logger = logging.getLogger(__name__)

DATASETS_DIR = DATA_DIR / "datasets"
DATASETS_DIR.mkdir(parents=True, exist_ok=True)

# ── Dataset Registry ──────────────────────────────────────────────

DATASET_REGISTRY: Dict[str, dict] = {
    "bbbp": {
        "name": "BBBP (Blood-Brain Barrier Penetration)",
        "task_type": "classification",
        "num_tasks": 1,
        "target_columns": ["p_np"],
        "smiles_column": "smiles",
        "description": "Binary classification of blood-brain barrier penetration.",
        "expected_size": 2039,
    },
    "tox21": {
        "name": "Tox21 (Toxicity in 21st Century)",
        "task_type": "classification",
        "num_tasks": 12,
        "target_columns": [
            "NR-AR", "NR-AR-LBD", "NR-AhR", "NR-Aromatase", "NR-ER",
            "NR-ER-LBD", "NR-PPAR-gamma", "SR-ARE", "SR-ATAD5",
            "SR-HSE", "SR-MMP", "SR-p53",
        ],
        "smiles_column": "smiles",
        "description": "Multi-label toxicity prediction across 12 biological endpoints.",
        "expected_size": 7831,
    },
    "esol": {
        "name": "ESOL (Estimated SOLubility)",
        "task_type": "regression",
        "num_tasks": 1,
        "target_columns": ["measured log solubility in mols per litre"],
        "smiles_column": "smiles",
        "description": "Predict aqueous solubility (logS) of molecules.",
        "expected_size": 1128,
    },
    "bace": {
        "name": "BACE (β-Secretase 1 Inhibitors)",
        "task_type": "classification",
        "num_tasks": 1,
        "target_columns": ["Class"],
        "smiles_column": "mol",
        "description": "Binary classification of BACE-1 inhibition (Alzheimer's target).",
        "expected_size": 1513,
    },
}


# ── DeepChem Loader ───────────────────────────────────────────────

def _load_via_deepchem(dataset_name: str) -> Optional[pd.DataFrame]:
    """Load dataset using DeepChem's MoleculeNet loaders."""
    try:
        import deepchem as dc
    except ImportError:
        logger.warning("DeepChem not installed — falling back to cached CSV.")
        return None

    loader_map = {
        "bbbp": dc.molnet.load_bbbp,
        "tox21": dc.molnet.load_tox21,
        "esol": dc.molnet.load_delaney,
        "bace": dc.molnet.load_bace_classification,
    }

    loader_fn = loader_map.get(dataset_name)
    if loader_fn is None:
        logger.error(f"No DeepChem loader for dataset: {dataset_name}")
        return None

    try:
        logger.info(f"Downloading {dataset_name} via DeepChem...")
        tasks, datasets, transformers = loader_fn(
            featurizer=dc.feat.DummyFeaturizer(),
            splitter=None,  # We'll split ourselves
            data_dir=str(DATASETS_DIR / dataset_name),
        )
        full_dataset = datasets[0]

        # Build DataFrame
        meta = DATASET_REGISTRY[dataset_name]
        smiles_list = full_dataset.ids.tolist()
        labels = full_dataset.y

        df = pd.DataFrame({meta["smiles_column"]: smiles_list})
        for i, col_name in enumerate(meta["target_columns"]):
            if labels.ndim == 1:
                df[col_name] = labels
            else:
                df[col_name] = labels[:, i]

        # Cache to CSV for future offline use
        cache_path = DATASETS_DIR / f"{dataset_name}.csv"
        df.to_csv(cache_path, index=False)
        logger.info(f"Cached {dataset_name} → {cache_path} ({len(df)} rows)")
        return df

    except Exception as e:
        logger.error(f"DeepChem load failed for {dataset_name}: {e}")
        return None


# ── CSV Fallback Loader ──────────────────────────────────────────

def _load_from_csv(dataset_name: str) -> Optional[pd.DataFrame]:
    """Load from cached CSV file."""
    cache_path = DATASETS_DIR / f"{dataset_name}.csv"
    if cache_path.exists():
        df = pd.read_csv(cache_path)
        logger.info(f"Loaded {dataset_name} from cache: {len(df)} rows")
        return df
    return None


# ── Public API ────────────────────────────────────────────────────

def load_moleculenet_dataset(
    dataset_name: str,
) -> Tuple[List[str], np.ndarray, dict]:
    """Load a MoleculeNet dataset.

    Returns:
        smiles_list: List of SMILES strings
        labels: numpy array of shape (n_samples,) or (n_samples, n_tasks)
        metadata: Dict with task_type, target_columns, etc.
    """
    dataset_name = dataset_name.lower()
    if dataset_name not in DATASET_REGISTRY:
        raise ValueError(
            f"Unknown dataset: {dataset_name}. "
            f"Available: {list(DATASET_REGISTRY.keys())}"
        )

    meta = DATASET_REGISTRY[dataset_name]

    # Try cached CSV first, then DeepChem download
    df = _load_from_csv(dataset_name)
    if df is None:
        df = _load_via_deepchem(dataset_name)
    if df is None:
        raise RuntimeError(
            f"Could not load dataset '{dataset_name}'. "
            f"Install deepchem (`pip install deepchem`) or place "
            f"a cached CSV at {DATASETS_DIR / f'{dataset_name}.csv'}"
        )

    # Extract SMILES and labels
    smiles_col = meta["smiles_column"]
    target_cols = meta["target_columns"]

    if smiles_col not in df.columns:
        # Try common alternatives
        for alt in ["smiles", "SMILES", "Smiles", "mol", "canonical_smiles"]:
            if alt in df.columns:
                smiles_col = alt
                break
        else:
            raise ValueError(
                f"SMILES column '{meta['smiles_column']}' not found. "
                f"Available: {list(df.columns)}"
            )

    smiles_list = df[smiles_col].tolist()

    # Extract labels — handle missing columns gracefully
    available_targets = [c for c in target_cols if c in df.columns]
    if not available_targets:
        raise ValueError(
            f"No target columns found. Expected: {target_cols}, "
            f"Available: {list(df.columns)}"
        )

    if len(available_targets) == 1:
        labels = df[available_targets[0]].values
    else:
        labels = df[available_targets].values

    # Update metadata with actual columns found
    meta_copy = {**meta, "actual_target_columns": available_targets}

    logger.info(
        f"Loaded {dataset_name}: {len(smiles_list)} molecules, "
        f"{len(available_targets)} task(s), type={meta['task_type']}"
    )

    return smiles_list, labels, meta_copy


def get_available_datasets() -> Dict[str, dict]:
    """Return registry of all available datasets with their metadata."""
    result = {}
    for name, meta in DATASET_REGISTRY.items():
        cached = (DATASETS_DIR / f"{name}.csv").exists()
        result[name] = {**meta, "cached": cached}
    return result
