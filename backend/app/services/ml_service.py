"""ML service — multi-model loading, inference, and result generation.

Loads 4 specialized models at startup:
- activity_bbbp: Blood-brain barrier penetration
- toxicity_tox21: 12 toxicity endpoints
- solubility_esol: Aqueous solubility (logS)
- activity_bace: BACE-1 inhibition
"""
import os
import logging
import numpy as np
from typing import Optional, List, Dict, Any

from app.ml.featurizer import featurize_single, apply_scaler
from app.ml.train_model import load_model, load_scaler, load_metrics
from app.services.chemistry import (
    parse_smiles, get_canonical_smiles, get_molecular_properties
)
from app.models.schemas import (
    PredictionResult, MolecularProperties,
    ToxicityProfile, SolubilityResult,
)
from app.config import MODEL_DIR

logger = logging.getLogger(__name__)

# ── Global Model Cache ────────────────────────────────────────────

_model_cache: Dict[str, Any] = {}
_scaler_cache: Dict[str, Any] = {}

# Model IDs for the production multi-model pipeline
PRODUCTION_MODELS = [
    "activity_bbbp",
    "toxicity_tox21",
    "solubility_esol",
    "activity_bace",
]

# Tox21 endpoint human-readable names
TOX21_ENDPOINT_NAMES = {
    "NR-AR": "Androgen Receptor",
    "NR-AR-LBD": "Androgen Receptor (Ligand Binding)",
    "NR-AhR": "Aryl Hydrocarbon Receptor",
    "NR-Aromatase": "Aromatase",
    "NR-ER": "Estrogen Receptor",
    "NR-ER-LBD": "Estrogen Receptor (Ligand Binding)",
    "NR-PPAR-gamma": "PPARγ",
    "SR-ARE": "Antioxidant Response Element",
    "SR-ATAD5": "DNA Damage (ATAD5)",
    "SR-HSE": "Heat Shock Response",
    "SR-MMP": "Mitochondrial Membrane Potential",
    "SR-p53": "p53 Tumor Suppressor",
}


def get_model(model_id: str = "default") -> Optional[Any]:
    """Get a model from cache or load from disk."""
    if model_id not in _model_cache:
        model = load_model(model_id)
        if model is not None:
            _model_cache[model_id] = model
            logger.info(f"Loaded model: {model_id}")
    return _model_cache.get(model_id)


def get_scaler(model_id: str) -> Optional[Any]:
    """Get a scaler from cache or load from disk."""
    if model_id not in _scaler_cache:
        scaler = load_scaler(model_id)
        if scaler is not None:
            _scaler_cache[model_id] = scaler
    return _scaler_cache.get(model_id)


def reload_model(model_id: str = "default"):
    """Force reload a model from disk."""
    _model_cache.pop(model_id, None)
    _scaler_cache.pop(model_id, None)
    return get_model(model_id)


def load_all_production_models():
    """Pre-load all production models into cache."""
    loaded = []
    for model_id in PRODUCTION_MODELS:
        m = get_model(model_id)
        if m is not None:
            loaded.append(model_id)
            # Also load scaler for regression models
            get_scaler(model_id)
    logger.info(f"Production models loaded: {loaded}")
    return loaded


# ── Prediction Functions ──────────────────────────────────────────

def _predict_bbbp(features: np.ndarray) -> Optional[float]:
    """Predict blood-brain barrier penetration probability."""
    model = get_model("activity_bbbp")
    if model is None:
        return None
    try:
        features_2d = features.reshape(1, -1)
        proba = model.predict_proba(features_2d)[0]
        return float(proba[1]) if len(proba) > 1 else float(proba[0])
    except Exception as e:
        logger.error(f"BBBP prediction failed: {e}")
        return None


def _predict_bace(features: np.ndarray) -> Optional[float]:
    """Predict BACE-1 inhibition probability."""
    model = get_model("activity_bace")
    if model is None:
        return None
    try:
        features_2d = features.reshape(1, -1)
        proba = model.predict_proba(features_2d)[0]
        return float(proba[1]) if len(proba) > 1 else float(proba[0])
    except Exception as e:
        logger.error(f"BACE prediction failed: {e}")
        return None


def _predict_toxicity(features: np.ndarray) -> Optional[ToxicityProfile]:
    """Predict toxicity across 12 Tox21 endpoints."""
    bundle = get_model("toxicity_tox21")
    if bundle is None:
        return None

    try:
        models = bundle["models"]
        target_names = bundle["target_names"]
        features_2d = features.reshape(1, -1)

        endpoint_scores = {}
        active_scores = []

        for i, (model, name) in enumerate(zip(models, target_names)):
            if model is None:
                continue
            try:
                proba = model.predict_proba(features_2d)[0]
                score = float(proba[1]) if len(proba) > 1 else float(proba[0])
                endpoint_scores[name] = round(score, 4)
                active_scores.append(score)
            except Exception:
                continue

        if not active_scores:
            return None

        overall = float(np.mean(active_scores))

        # Risk level based on maximum endpoint score
        max_score = max(active_scores)
        if max_score < 0.3:
            risk = "Low"
        elif max_score < 0.6:
            risk = "Medium"
        else:
            risk = "High"

        high_risk = [
            name for name, score in endpoint_scores.items()
            if score > 0.5
        ]

        return ToxicityProfile(
            endpoint_scores=endpoint_scores,
            overall_score=round(overall, 4),
            risk_level=risk,
            high_risk_endpoints=high_risk,
        )
    except Exception as e:
        logger.error(f"Tox21 prediction failed: {e}")
        return None


def _predict_solubility(features: np.ndarray) -> Optional[SolubilityResult]:
    """Predict aqueous solubility (logS)."""
    model = get_model("solubility_esol")
    if model is None:
        return None

    try:
        features_2d = features.reshape(1, -1)

        # Apply scaler if available
        scaler = get_scaler("solubility_esol")
        if scaler is not None:
            features_2d = apply_scaler(features_2d, scaler)

        log_s = float(model.predict(features_2d)[0])

        # Categorize solubility
        if log_s < -6:
            category = "Insoluble"
            desc = "This molecule is predicted to be practically insoluble in water."
        elif log_s < -4:
            category = "Poorly Soluble"
            desc = "This molecule has poor aqueous solubility, which may limit oral bioavailability."
        elif log_s < -2:
            category = "Moderately Soluble"
            desc = "This molecule has moderate water solubility — acceptable for many drug applications."
        elif log_s < 0:
            category = "Soluble"
            desc = "This molecule is predicted to have good aqueous solubility."
        else:
            category = "Very Soluble"
            desc = "This molecule is predicted to be highly soluble in water."

        return SolubilityResult(
            log_s=round(log_s, 3),
            category=category,
            description=desc,
        )
    except Exception as e:
        logger.error(f"Solubility prediction failed: {e}")
        return None


# ── Summary Generation ────────────────────────────────────────────

def _generate_summary(
    activity_prob: float,
    qed: float,
    toxicity_score: float,
    lipinski_violations: int,
    bbb: Optional[float] = None,
    solubility: Optional[SolubilityResult] = None,
) -> tuple:
    """Generate plain-language summary and verdict using all model outputs."""
    # Determine verdict (multi-factor)
    scores = []
    scores.append(("activity", activity_prob, 0.3))
    scores.append(("druglikeness", qed, 0.25))
    scores.append(("safety", 1 - toxicity_score, 0.25))
    scores.append(("lipinski", max(0, (4 - lipinski_violations) / 4), 0.2))

    weighted_score = sum(s * w for _, s, w in scores)

    if weighted_score >= 0.65 and toxicity_score < 0.4 and lipinski_violations <= 1:
        verdict = "Promising"
    elif weighted_score >= 0.40 and toxicity_score < 0.65:
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

    # Build summary
    parts = []
    if verdict == "Promising":
        parts.append("This molecule shows strong potential as a drug candidate.")
    elif verdict == "Moderate":
        parts.append("This molecule has some promising characteristics but also areas of concern.")
    else:
        parts.append("This molecule may face significant challenges as a drug candidate.")

    if activity_prob >= 0.7:
        parts.append(f"It has a high predicted activity probability ({activity_prob:.0%}).")
    elif activity_prob >= 0.4:
        parts.append(f"It has a moderate predicted activity probability ({activity_prob:.0%}).")
    else:
        parts.append(f"It has a low predicted activity probability ({activity_prob:.0%}).")

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

    if bbb is not None:
        if bbb >= 0.7:
            parts.append(f"It is predicted to penetrate the blood-brain barrier (BBB probability: {bbb:.0%}).")
        elif bbb >= 0.4:
            parts.append(f"BBB penetration is uncertain (probability: {bbb:.0%}).")
        else:
            parts.append(f"It is unlikely to cross the blood-brain barrier (probability: {bbb:.0%}).")

    if solubility is not None:
        parts.append(f"Predicted aqueous solubility: {solubility.category} (logS = {solubility.log_s:.2f}).")

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
    if solubility and solubility.log_s < -4:
        tips.append("Poor solubility may limit drug absorption. Consider adding polar groups or reducing molecular weight.")
    if bbb is not None and bbb >= 0.7:
        tips.append("High BBB penetration suggests potential for CNS (central nervous system) drug development.")

    return summary, verdict, tox_risk, tips


# ── Main Prediction Pipeline ─────────────────────────────────────

def predict_molecule(smiles: str, model_id: str = "default") -> PredictionResult:
    """Run full multi-model prediction pipeline for a single molecule."""
    mol = parse_smiles(smiles)
    if mol is None:
        raise ValueError(f"Invalid SMILES string: {smiles}")

    canonical = get_canonical_smiles(mol)
    props = get_molecular_properties(mol)

    # Get feature vector
    features = featurize_single(smiles)
    if features is None:
        raise ValueError(f"Could not featurize molecule: {smiles}")

    model_versions = {}

    # ── Activity prediction (BBBP model) ──────────────────────────
    bbb_prob = _predict_bbbp(features)
    if bbb_prob is not None:
        model_versions["activity"] = "activity_bbbp (XGBoost)"
    
    bace_prob = _predict_bace(features)
    if bace_prob is not None:
        model_versions["bace"] = "activity_bace (XGBoost)"

    # Compute overall activity as average of available model predictions
    activity_scores = [s for s in [bbb_prob, bace_prob] if s is not None]
    if activity_scores:
        activity_prob = float(np.mean(activity_scores))
    else:
        # Fallback: heuristic only if NO models are loaded
        activity_prob = _heuristic_activity(props)
        model_versions["activity"] = "heuristic (no trained model)"

    # ── Toxicity prediction (Tox21 model) ─────────────────────────
    tox_profile = _predict_toxicity(features)
    if tox_profile is not None:
        toxicity_score = tox_profile.overall_score
        model_versions["toxicity"] = "toxicity_tox21 (XGBoost × 12)"
    else:
        toxicity_score = _heuristic_toxicity(props)
        tox_profile = None
        model_versions["toxicity"] = "heuristic (no trained model)"

    # ── Solubility prediction (ESOL model) ────────────────────────
    solubility = _predict_solubility(features)
    if solubility is not None:
        model_versions["solubility"] = "solubility_esol (XGBoost)"

    # ── Drug-likeness (always RDKit QED — no model needed) ────────
    drug_likeness = props["qed_score"]
    model_versions["drug_likeness"] = "RDKit QED (deterministic)"

    # ── Generate summary with all model outputs ───────────────────
    summary, verdict, tox_risk, tips = _generate_summary(
        activity_prob, drug_likeness, toxicity_score,
        props["lipinski_violations"],
        bbb=bbb_prob,
        solubility=solubility,
    )

    # ── Confidence estimation ─────────────────────────────────────
    n_models_available = sum(1 for m in PRODUCTION_MODELS if get_model(m) is not None)
    confidence = round(n_models_available / len(PRODUCTION_MODELS), 2)

    return PredictionResult(
        smiles=smiles,
        canonical_smiles=canonical,
        drug_likeness_score=round(drug_likeness, 4),
        toxicity_risk=tox_risk,
        toxicity_score=round(toxicity_score, 4),
        activity_probability=round(activity_prob, 4),
        molecular_properties=MolecularProperties(**props),
        toxicity_profile=tox_profile,
        solubility=solubility,
        bbb_penetration=round(bbb_prob, 4) if bbb_prob is not None else None,
        bace_inhibition=round(bace_prob, 4) if bace_prob is not None else None,
        plain_language_summary=summary,
        verdict=verdict,
        tips=tips,
        model_versions=model_versions,
        confidence=confidence,
    )


# ── Heuristic Fallbacks (only used when models aren't loaded) ─────

def _heuristic_activity(props: dict) -> float:
    """Heuristic activity prediction when no model is available."""
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
    """Heuristic toxicity score when no model is available."""
    score = 0.3
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
    if props["qed_score"] < 0.3:
        score += 0.1
    return max(0.05, min(0.95, score))
