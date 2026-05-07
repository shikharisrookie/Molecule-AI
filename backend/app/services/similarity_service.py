"""Molecular similarity search service.

Computes Tanimoto similarity between a query molecule and a library
of ~2,000 FDA-approved drugs using Morgan fingerprints.
"""
import csv
import logging
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
from rdkit import Chem, DataStructs
from rdkit.Chem import AllChem

from app.config import DATA_DIR

logger = logging.getLogger(__name__)

# ── Reference Library ─────────────────────────────────────────────

_drug_library: Optional[List[dict]] = None
_drug_fingerprints: Optional[List] = None

APPROVED_DRUGS_PATH = DATA_DIR / "approved_drugs.csv"


def _load_drug_library():
    """Load the approved drugs reference library and pre-compute fingerprints."""
    global _drug_library, _drug_fingerprints

    if not APPROVED_DRUGS_PATH.exists():
        logger.warning(f"Approved drugs file not found: {APPROVED_DRUGS_PATH}")
        _drug_library = []
        _drug_fingerprints = []
        return

    drugs = []
    fingerprints = []

    with open(APPROVED_DRUGS_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            smiles = row.get("smiles", "").strip()
            if not smiles:
                continue
            try:
                mol = Chem.MolFromSmiles(smiles)
                if mol is None:
                    continue
                fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)
                drugs.append({
                    "name": row.get("name", "Unknown"),
                    "smiles": smiles,
                    "indication": row.get("indication", ""),
                })
                fingerprints.append(fp)
            except Exception:
                continue

    _drug_library = drugs
    _drug_fingerprints = fingerprints
    logger.info(f"Loaded {len(drugs)} approved drugs for similarity search")


def get_drug_library():
    """Get the drug library, loading it if needed."""
    global _drug_library
    if _drug_library is None:
        _load_drug_library()
    return _drug_library


def get_drug_fingerprints():
    """Get pre-computed fingerprints."""
    global _drug_fingerprints
    if _drug_fingerprints is None:
        _load_drug_library()
    return _drug_fingerprints


# ── Similarity Search ─────────────────────────────────────────────

def search_similar(
    query_smiles: str,
    top_k: int = 10,
    min_similarity: float = 0.1,
) -> List[dict]:
    """Find the most similar approved drugs to a query molecule.

    Args:
        query_smiles: SMILES string of the query molecule
        top_k: Number of top matches to return
        min_similarity: Minimum Tanimoto similarity threshold

    Returns:
        List of dicts with name, smiles, similarity, indication
    """
    mol = Chem.MolFromSmiles(query_smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES: {query_smiles}")

    query_fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=2048)

    drugs = get_drug_library()
    fingerprints = get_drug_fingerprints()

    if not drugs:
        logger.warning("Drug library is empty — no similarity search possible")
        return []

    # Compute Tanimoto similarity against entire library
    similarities = DataStructs.BulkTanimotoSimilarity(query_fp, fingerprints)

    # Rank and filter
    results = []
    for i, sim in enumerate(similarities):
        if sim >= min_similarity:
            results.append({
                "name": drugs[i]["name"],
                "smiles": drugs[i]["smiles"],
                "similarity": round(float(sim), 4),
                "indication": drugs[i]["indication"],
            })

    # Sort by similarity descending
    results.sort(key=lambda x: x["similarity"], reverse=True)

    return results[:top_k]
