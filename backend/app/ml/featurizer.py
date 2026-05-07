"""Molecular featurizer — converts SMILES to ML-ready feature vectors.

Supports multiple fingerprint types and descriptor blocks with optional
feature scaling for regression tasks.
"""
import numpy as np
import pandas as pd
from typing import List, Optional, Tuple
from sklearn.preprocessing import StandardScaler

from app.services.chemistry import (
    parse_smiles, get_morgan_fingerprint, get_molecular_properties,
)
from app.config import MORGAN_RADIUS, MORGAN_NBITS

# ── Additional Fingerprints ───────────────────────────────────────

def _get_maccs_keys(mol) -> np.ndarray:
    """Generate 167-bit MACCS fingerprint."""
    from rdkit.Chem import MACCSkeys, DataStructs
    fp = MACCSkeys.GenMACCSKeys(mol)
    arr = np.zeros(167, dtype=np.int8)
    DataStructs.ConvertToNumpyArray(fp, arr)
    return arr


def _get_rdkit_descriptors(mol) -> np.ndarray:
    """Calculate extended RDKit descriptors beyond basic physicochemical."""
    from rdkit.Chem import Descriptors, rdMolDescriptors, Fragments

    try:
        descriptors = [
            Descriptors.MolWt(mol),
            Descriptors.MolLogP(mol),
            Descriptors.TPSA(mol),
            rdMolDescriptors.CalcNumHBD(mol),
            rdMolDescriptors.CalcNumHBA(mol),
            rdMolDescriptors.CalcNumRotatableBonds(mol),
            rdMolDescriptors.CalcNumAromaticRings(mol),
            rdMolDescriptors.CalcNumAliphaticRings(mol),
            rdMolDescriptors.CalcNumHeterocycles(mol),
            Descriptors.NumValenceElectrons(mol),
            Descriptors.NumRadicalElectrons(mol),
            Descriptors.MaxPartialCharge(mol) or 0.0,
            Descriptors.MinPartialCharge(mol) or 0.0,
            rdMolDescriptors.CalcFractionCSP3(mol),
            Descriptors.HeavyAtomCount(mol),
            rdMolDescriptors.CalcNumAmideBonds(mol),
            rdMolDescriptors.CalcNumBridgeheadAtoms(mol),
            rdMolDescriptors.CalcNumSpiroAtoms(mol),
            Descriptors.RingCount(mol),
            Descriptors.FractionCSP3(mol),
            Descriptors.HeavyAtomMolWt(mol),
            Descriptors.NHOHCount(mol),
            Descriptors.NOCount(mol),
            Descriptors.BalabanJ(mol) if Descriptors.RingCount(mol) > 0 else 0.0,
        ]
    except Exception:
        # Fallback for molecules where some descriptors fail
        descriptors = [0.0] * 24

    # Replace NaN/Inf with 0
    result = np.array(descriptors, dtype=np.float64)
    result = np.nan_to_num(result, nan=0.0, posinf=0.0, neginf=0.0)
    return result


# ── Core Featurizer ───────────────────────────────────────────────

def featurize_single(
    smiles: str,
    use_maccs: bool = False,
    use_extended_descriptors: bool = False,
) -> Optional[np.ndarray]:
    """Convert a single SMILES string to a feature vector.

    Default: Morgan fingerprint (2048-bit) + 9 physicochemical descriptors = 2057-dim
    With MACCS: + 167 MACCS key bits = 2224-dim
    With extended: + 24 extra descriptors = 2081-dim (or 2248 with MACCS)
    """
    mol = parse_smiles(smiles)
    if mol is None:
        return None

    parts = []

    # Morgan fingerprint (always included)
    fp = get_morgan_fingerprint(mol, radius=MORGAN_RADIUS, n_bits=MORGAN_NBITS)
    parts.append(fp.astype(np.float64))

    # MACCS keys (optional)
    if use_maccs:
        maccs = _get_maccs_keys(mol)
        parts.append(maccs.astype(np.float64))

    # Physicochemical descriptors (always included)
    props = get_molecular_properties(mol)
    basic_desc = np.array([
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
    parts.append(basic_desc)

    # Extended descriptors (optional)
    if use_extended_descriptors:
        ext = _get_rdkit_descriptors(mol)
        parts.append(ext)

    return np.concatenate(parts)


def featurize_batch(
    smiles_list: List[str],
    use_maccs: bool = False,
    use_extended_descriptors: bool = False,
) -> Tuple[np.ndarray, List[int], List[int]]:
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
        if not isinstance(smiles, str) or not smiles.strip():
            failed_indices.append(i)
            continue
        feat = featurize_single(
            smiles.strip(),
            use_maccs=use_maccs,
            use_extended_descriptors=use_extended_descriptors,
        )
        if feat is not None:
            features.append(feat)
            valid_indices.append(i)
        else:
            failed_indices.append(i)

    if not features:
        return np.array([]), valid_indices, failed_indices

    return np.array(features), valid_indices, failed_indices


def get_feature_names(
    use_maccs: bool = False,
    use_extended_descriptors: bool = False,
) -> List[str]:
    """Get feature names for interpretability."""
    names = [f"morgan_bit_{i}" for i in range(MORGAN_NBITS)]

    if use_maccs:
        names += [f"maccs_bit_{i}" for i in range(167)]

    names += [
        "molecular_weight", "logp", "hbd", "hba", "tpsa",
        "rotatable_bonds", "aromatic_rings", "lipinski_violations", "qed_score",
    ]

    if use_extended_descriptors:
        names += [
            "ext_molwt", "ext_logp", "ext_tpsa", "ext_hbd", "ext_hba",
            "ext_rotatable", "ext_aromatic_rings", "ext_aliphatic_rings",
            "ext_heterocycles", "ext_valence_e", "ext_radical_e",
            "ext_max_partial_charge", "ext_min_partial_charge", "ext_frac_csp3",
            "ext_heavy_atoms", "ext_amide_bonds", "ext_bridgehead_atoms",
            "ext_spiro_atoms", "ext_ring_count", "ext_frac_csp3_v2",
            "ext_heavy_atom_mw", "ext_nhoh_count", "ext_no_count",
            "ext_balaban_j",
        ]

    return names


# ── Feature Scaling ───────────────────────────────────────────────

def create_scaler(X: np.ndarray) -> StandardScaler:
    """Fit a StandardScaler on feature matrix (for regression tasks)."""
    scaler = StandardScaler()
    scaler.fit(X)
    return scaler


def apply_scaler(X: np.ndarray, scaler: StandardScaler) -> np.ndarray:
    """Apply fitted scaler to feature matrix."""
    return scaler.transform(X)
