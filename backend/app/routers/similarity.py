"""Similarity search router — /similarity endpoint."""
from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    MoleculeInput, SimilarityResponse, SimilarMolecule,
)
from app.services.similarity_service import search_similar
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter(prefix="/similarity", tags=["Similarity Search"])


class SimilarityInput(BaseModel):
    smiles: str
    top_k: int = Field(default=10, ge=1, le=50)
    min_similarity: float = Field(default=0.1, ge=0.0, le=1.0)


@router.post("", response_model=SimilarityResponse, summary="Find similar approved drugs")
async def find_similar(input_data: SimilarityInput):
    """
    Search for the most structurally similar FDA-approved drugs
    using Tanimoto similarity on Morgan fingerprints.
    """
    try:
        results = search_similar(
            query_smiles=input_data.smiles,
            top_k=input_data.top_k,
            min_similarity=input_data.min_similarity,
        )
        return SimilarityResponse(
            success=True,
            query_smiles=input_data.smiles,
            similar_molecules=[SimilarMolecule(**r) for r in results],
        )
    except ValueError as e:
        return SimilarityResponse(success=False, error=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similarity search failed: {str(e)}")
