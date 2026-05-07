from __future__ import annotations
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class MoleculeInput(BaseModel):
    smiles: str = Field(..., description="SMILES string representing the molecule")


class BatchMoleculeInput(BaseModel):
    smiles_list: List[str] = Field(..., description="List of SMILES strings for batch prediction")


class MolecularProperties(BaseModel):
    molecular_weight: float
    logp: float
    hbd: int
    hba: int
    tpsa: float
    rotatable_bonds: int
    aromatic_rings: int
    lipinski_violations: int
    qed_score: float


class ToxicityProfile(BaseModel):
    """Individual toxicity endpoint scores from the Tox21 model."""
    endpoint_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Score for each Tox21 endpoint (0=safe, 1=toxic)"
    )
    overall_score: float = Field(
        0.0, description="Averaged toxicity score across all endpoints"
    )
    risk_level: str = Field("Unknown", description="Low / Medium / High")
    high_risk_endpoints: List[str] = Field(
        default_factory=list,
        description="Endpoints with score > 0.5"
    )


class SolubilityResult(BaseModel):
    """Predicted aqueous solubility."""
    log_s: float = Field(0.0, description="Predicted logS (mol/L)")
    category: str = Field(
        "Unknown",
        description="Insoluble / Poorly Soluble / Moderately Soluble / Soluble / Very Soluble"
    )
    description: str = Field("", description="Plain-language explanation")


class PredictionResult(BaseModel):
    smiles: str
    canonical_smiles: str

    # Core scores
    drug_likeness_score: float
    toxicity_score: float
    toxicity_risk: str
    activity_probability: float
    verdict: str

    # Properties
    molecular_properties: MolecularProperties

    # Multi-model enrichment
    toxicity_profile: Optional[ToxicityProfile] = None
    solubility: Optional[SolubilityResult] = None
    bbb_penetration: Optional[float] = Field(None, description="P(blood-brain barrier penetration)")
    bace_inhibition: Optional[float] = Field(None, description="P(BACE-1 inhibition)")

    # Explanations
    plain_language_summary: str
    tips: List[str] = Field(default_factory=list)

    # Model metadata
    model_versions: Dict[str, str] = Field(
        default_factory=dict,
        description="Which models were used for each prediction"
    )
    confidence: Optional[float] = Field(
        None, description="Overall confidence in the prediction (0-1)"
    )


class PredictionResponse(BaseModel):
    success: bool
    prediction: Optional[PredictionResult] = None
    error: Optional[str] = None


class BatchPredictionResponse(BaseModel):
    success: bool
    predictions: List[PredictionResult] = Field(default_factory=list)
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    total: int = 0
    successful: int = 0


class TrainRequest(BaseModel):
    dataset_id: str
    model_type: str = "xgboost"
    target_column: str = "activity_label"
    smiles_column: str = "smiles"


class TrainResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    model_id: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class UploadResponse(BaseModel):
    success: bool
    dataset_id: Optional[str] = None
    filename: Optional[str] = None
    filepath: Optional[str] = None
    num_rows: Optional[int] = None
    num_columns: Optional[int] = None
    columns: Optional[List[str]] = None
    preview: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class MoleculeInfoResponse(BaseModel):
    success: bool
    smiles: Optional[str] = None
    canonical_smiles: Optional[str] = None
    molecular_properties: Optional[MolecularProperties] = None
    mol_block_3d: Optional[str] = None
    svg_2d: Optional[str] = None
    formula: Optional[str] = None
    inchi: Optional[str] = None
    inchi_key: Optional[str] = None
    property_explanations: Optional[Dict[str, str]] = None
    error: Optional[str] = None


# ── Similarity Schemas ────────────────────────────────────────────

class SimilarMolecule(BaseModel):
    name: str
    smiles: str
    similarity: float = Field(description="Tanimoto similarity 0-1")
    indication: str = Field("", description="Known medical use")


class SimilarityResponse(BaseModel):
    success: bool
    query_smiles: Optional[str] = None
    similar_molecules: List[SimilarMolecule] = Field(default_factory=list)
    error: Optional[str] = None


# ── Model Info Schemas ────────────────────────────────────────────

class ModelInfo(BaseModel):
    model_id: str
    task_type: str
    model_type: str
    trained_at: Optional[str] = None
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ModelListResponse(BaseModel):
    success: bool
    models: List[ModelInfo] = Field(default_factory=list)


# ── Chat Schemas ──────────────────────────────────────────────────

class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str


class ChatRequest(BaseModel):
    message: str
    context_smiles: Optional[str] = Field(
        None, description="Optional SMILES string for molecule-aware responses"
    )
    history: List[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    success: bool
    reply: str = ""
    sources: List[str] = Field(
        default_factory=list, description="Knowledge sources used"
    )
    error: Optional[str] = None
