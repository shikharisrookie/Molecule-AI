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


class PredictionResult(BaseModel):
    smiles: str
    canonical_smiles: str
    drug_likeness_score: float
    toxicity_score: float
    toxicity_risk: str
    activity_probability: float
    verdict: str
    molecular_properties: MolecularProperties
    plain_language_summary: str


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
    model_type: str
    target_column: str
    smiles_column: str


class TrainResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    model_id: Optional[str] = None
    metrics: Optional[Dict[str, float]] = None
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
