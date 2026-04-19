"""Molecular featurizer — converts SMILES to ML-ready feature vectors."""
import numpy as np
import pandas as pd
from typing import List, Optional, Tuple
from app.services.chemistry import parse_smiles, get_morgan_fingerprint, get_molecular_properties
from app.config import MORGAN_RADIUS, MORGAN_NBITS


def featurize_single(smiles: str) -> Optional[np.ndarray]:
    """Convert a single SMILES string to a feature vector.
    
    Returns Morgan fingerprint (2048-bit) concatenated with 
    9 physicochemical descriptors = 2057-dimensional vector.
    """
    mol = parse_smiles(smiles)
    if mol is None:
        return None

    # Morgan fingerprint
    fp = get_morgan_fingerprint(mol, radius=MORGAN_RADIUS, n_bits=MORGAN_NBITS)

    # Physicochemical descriptors
    props = get_molecular_properties(mol)
    desc = np.array([
        props["molecular_weight"],
        props["logp"],
        props["hbd"],
        props["hba"],
        props["tpsa"],
        props["rotatable_bonds"],
        props["aromatic_rings"],
        props["lipinski_violations"],
        props["qed_score"],
    ], dtype=np.float64)

    return np.concatenate([fp.astype(np.float64), desc])


def featurize_batch(smiles_list: List[str]) -> Tuple[np.ndarray, List[int], List[int]]:
    """Convert a list of SMILES to a feature matrix.
    
    Returns:
        features: numpy array of shape (n_valid, n_features)
        valid_indices: indices of successfully featurized molecules
        failed_indices: indices of molecules that failed featurization
    """
    features = []
    valid_indices = []
    failed_indices = []

    for i, smiles in enumerate(smiles_list):
        feat = featurize_single(smiles)
        if feat is not None:
            features.append(feat)
            valid_indices.append(i)
        else:
            failed_indices.append(i)

    if not features:
        return np.array([]), valid_indices, failed_indices

    return np.array(features), valid_indices, failed_indices


def get_feature_names() -> List[str]:
    """Get feature names for interpretability."""
    fp_names = [f"morgan_bit_{i}" for i in range(MORGAN_NBITS)]
    desc_names = [
        "molecular_weight", "logp", "hbd", "hba", "tpsa",
        "rotatable_bonds", "aromatic_rings", "lipinski_violations", "qed_score"
    ]
    return fp_names + desc_names
