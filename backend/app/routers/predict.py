"""Prediction router — /predict endpoints."""
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.schemas import (
    MoleculeInput, BatchMoleculeInput,
    PredictionResponse, BatchPredictionResponse, PredictionResult
)
from app.services.ml_service import predict_molecule
from app.db.database import get_db
from app.db.models import PredictionHistory

router = APIRouter(prefix="/predict", tags=["Predictions"])


@router.post("", response_model=PredictionResponse, summary="Predict drug properties for a single molecule")
async def predict_single(input_data: MoleculeInput, db: Session = Depends(get_db)):
    """
    Predict drug-likeness, toxicity risk, and activity probability for a single molecule.
    
    Provide a valid SMILES string and receive:
    - Drug-likeness score (0-1)
    - Toxicity risk assessment
    - Activity probability
    - Plain-language summary
    """
    try:
        result = predict_molecule(input_data.smiles)
        
        # Save to history
        history_entry = PredictionHistory(
            smiles=input_data.smiles,
            canonical_smiles=result.canonical_smiles,
            prediction_data=json.dumps(result.model_dump()),
            drug_likeness_score=result.drug_likeness_score,
            toxicity_score=result.toxicity_score,
            activity_probability=result.activity_probability,
            verdict=result.verdict,
        )
        db.add(history_entry)
        db.commit()
        
        return PredictionResponse(success=True, prediction=result)
    except ValueError as e:
        return PredictionResponse(success=False, error=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/batch", response_model=BatchPredictionResponse, summary="Batch predict for multiple molecules")
async def predict_batch(input_data: BatchMoleculeInput, db: Session = Depends(get_db)):
    """
    Predict properties for multiple molecules at once.
    
    Provide a list of SMILES strings and receive predictions for each valid molecule.
    """
    predictions = []
    errors = []

    for i, smiles in enumerate(input_data.smiles_list):
        try:
            result = predict_molecule(smiles)
            predictions.append(result)
            
            # Save to history
            history_entry = PredictionHistory(
                smiles=smiles,
                canonical_smiles=result.canonical_smiles,
                prediction_data=json.dumps(result.model_dump()),
                drug_likeness_score=result.drug_likeness_score,
                toxicity_score=result.toxicity_score,
                activity_probability=result.activity_probability,
                verdict=result.verdict,
            )
            db.add(history_entry)
        except Exception as e:
            errors.append({"index": str(i), "smiles": smiles, "error": str(e)})

    db.commit()

    return BatchPredictionResponse(
        success=True,
        predictions=predictions,
        errors=errors,
        total=len(input_data.smiles_list),
        successful=len(predictions),
    )
