"""ML service — model loading, inference, and plain-language result generation."""
import os
import numpy as np
from typing import Optional, List
from app.ml.featurizer import featurize_single
from app.ml.train_model import load_model
from app.services.chemistry import (
    parse_smiles, get_canonical_smiles, get_molecular_properties
)
from app.models.schemas import PredictionResult, MolecularProperties
from app.config import MODEL_DIR

# Global model cache
_model_cache = {}


def get_model(model_id: str = "default"):
    """Get a model from cache or load from disk."""
    if model_id not in _model_cache:
        model = load_model(model_id)
        if model is not None:
            _model_cache[model_id] = model
    return _model_cache.get(model_id)


def reload_model(model_id: str = "default"):
    """Force reload a model from disk."""
    if model_id in _model_cache:
        del _model_cache[model_id]
    return get_model(model_id)


def _generate_summary(
    activity_prob: float,
    qed: float,
    toxicity_score: float,
    lipinski_violations: int,
) -> tuple:
    """Generate plain-language summary and verdict."""
    # Determine verdict
    if activity_prob >= 0.7 and qed >= 0.4 and toxicity_score < 0.4 and lipinski_violations <= 1:
        verdict = "Promising"
    elif activity_prob >= 0.4 and qed >= 0.25 and toxicity_score < 0.6:
        verdict = "Moderate"
    else:
        verdict = "Poor"

    # Toxicity risk level
    if toxicity_score < 0.3:
        tox_risk = "Low"
    elif toxicity_score < 0.6:
        tox_risk = "Medium"
    else:
        tox_risk = "High"

    # Plain language summary
    parts = []
    if verdict == "Promising":
        parts.append("This molecule shows strong potential as a drug candidate.")
    elif verdict == "Moderate":
        parts.append("This molecule has some promising characteristics but also areas of concern.")
    else:
        parts.append("This molecule may face significant challenges as a drug candidate.")

    if activity_prob >= 0.7:
        parts.append(f"It has a high probability ({activity_prob:.0%}) of being biologically active.")
    elif activity_prob >= 0.4:
        parts.append(f"It has a moderate probability ({activity_prob:.0%}) of being biologically active.")
    else:
        parts.append(f"It has a low probability ({activity_prob:.0%}) of being biologically active.")

    if tox_risk == "Low":
        parts.append("The predicted toxicity risk is low, which is favorable.")
    elif tox_risk == "Medium":
        parts.append("There is a moderate toxicity risk that would need further investigation.")
    else:
        parts.append("The predicted toxicity risk is high, which is a significant concern.")

    if qed >= 0.5:
        parts.append(f"The drug-likeness score ({qed:.2f}/1.0) indicates good drug-like properties.")
    elif qed >= 0.3:
        parts.append(f"The drug-likeness score ({qed:.2f}/1.0) is acceptable but could be improved.")
    else:
        parts.append(f"The drug-likeness score ({qed:.2f}/1.0) suggests poor drug-like properties.")

    summary = " ".join(parts)

    # Tips
    tips = []
    if lipinski_violations > 0:
        tips.append(f"This molecule violates {lipinski_violations} of Lipinski's rules — oral bioavailability may be limited.")
    if toxicity_score >= 0.5:
        tips.append("Consider structural modifications to reduce predicted toxicity.")
    if activity_prob < 0.5:
        tips.append("The low activity prediction suggests this compound may need optimization.")
    if qed >= 0.5 and activity_prob >= 0.6:
        tips.append("This molecule is a good starting point for further optimization in drug development.")
    if lipinski_violations == 0:
        tips.append("Passes all Lipinski rules — likely to have good oral absorption.")

    return summary, verdict, tox_risk, tips


def predict_molecule(smiles: str, model_id: str = "default") -> PredictionResult:
    """Run full prediction pipeline for a single molecule."""
    mol = parse_smiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES string: {smiles}")

    canonical = get_canonical_smiles(mol)
    props = get_molecular_properties(mol)

    # Get feature vector
    features = featurize_single(smiles)
    if features is None:
        raise ValueError(f"Could not featurize molecule: {smiles}")

    # Load model and predict
    model = get_model(model_id)
    if model is None:
        # If no trained model exists, use heuristic predictions based on properties
        activity_prob = _heuristic_activity(props)
        toxicity_score = _heuristic_toxicity(props)
    else:
        features_2d = features.reshape(1, -1)
        proba = model.predict_proba(features_2d)[0]
        activity_prob = float(proba[1]) if len(proba) > 1 else float(proba[0])
        # Use QED-based toxicity heuristic (model only predicts activity)
        toxicity_score = _heuristic_toxicity(props)

    drug_likeness = props["qed_score"]
    summary, verdict, tox_risk, tips = _generate_summary(
        activity_prob, drug_likeness, toxicity_score, props["lipinski_violations"]
    )

    return PredictionResult(
        smiles=smiles,
        canonical_smiles=canonical,
        drug_likeness_score=round(drug_likeness, 4),
        toxicity_risk=tox_risk,
        toxicity_score=round(toxicity_score, 4),
        activity_probability=round(activity_prob, 4),
        molecular_properties=MolecularProperties(**props),
        plain_language_summary=summary,
        verdict=verdict,
        tips=tips,
    )


def _heuristic_activity(props: dict) -> float:
    """Heuristic activity prediction based on molecular properties when no model is available."""
    score = 0.5
    qed = props["qed_score"]
    score += (qed - 0.5) * 0.4

    if props["lipinski_violations"] == 0:
        score += 0.1
    elif props["lipinski_violations"] >= 2:
        score -= 0.15

    if 150 <= props["molecular_weight"] <= 500:
        score += 0.05
    if -0.5 <= props["logp"] <= 5.0:
        score += 0.05
    if props["tpsa"] <= 140:
        score += 0.05

    return max(0.05, min(0.95, score))


def _heuristic_toxicity(props: dict) -> float:
    """Heuristic toxicity score based on molecular properties."""
    score = 0.3  # Base score

    if props["molecular_weight"] > 500:
        score += 0.1
    if props["logp"] > 5:
        score += 0.15
    if props["logp"] > 6:
        score += 0.1
    if props["tpsa"] > 140:
        score += 0.1
    if props["lipinski_violations"] >= 2:
        score += 0.1
    if props["rotatable_bonds"] > 10:
        score += 0.05

    # Low QED correlates with higher toxicity risk
    if props["qed_score"] < 0.3:
        score += 0.1

    return max(0.05, min(0.95, score))
