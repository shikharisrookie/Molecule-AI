"""Train router — /train endpoint."""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import TrainRequest, TrainResponse
from app.services.data_service import load_dataset
from app.ml.train_model import train_model
from app.services.ml_service import reload_model

router = APIRouter(prefix="/train", tags=["Model Training"])


@router.post("", response_model=TrainResponse, summary="Train a model on a dataset")
async def train_new_model(request: TrainRequest):
    """
    Train a new classification model on an uploaded or sample dataset.
    
    - dataset_id: Use 'sample' for the pre-loaded dataset, or provide the ID from /upload-dataset
    - model_type: 'xgboost' or 'random_forest'
    - target_column: Name of the column with labels
    - smiles_column: Name of the column with SMILES strings
    """
    # Load dataset
    df = load_dataset(request.dataset_id)
    if df is None:
        return TrainResponse(
            success=False,
            error=f"Dataset not found: {request.dataset_id}. Use 'sample' for the pre-loaded dataset."
        )

    # Validate columns
    if request.smiles_column not in df.columns:
        return TrainResponse(
            success=False,
            error=f"Column '{request.smiles_column}' not found. Available columns: {list(df.columns)}"
        )
    if request.target_column not in df.columns:
        return TrainResponse(
            success=False,
            error=f"Column '{request.target_column}' not found. Available columns: {list(df.columns)}"
        )

    try:
        smiles_list = df[request.smiles_column].tolist()
        labels = df[request.target_column].astype(int).tolist()

        model_id = f"{request.dataset_id}_{request.model_type}"
        model, metrics = train_model(
            smiles_list=smiles_list,
            labels=labels,
            model_type=request.model_type,
            model_id=model_id,
        )

        # Reload the default model if training on sample dataset
        if request.dataset_id == "sample":
            reload_model("default")

        return TrainResponse(
            success=True,
            message=f"Model trained successfully with {metrics['accuracy']:.1%} accuracy.",
            model_id=model_id,
            metrics=metrics,
        )
    except ValueError as e:
        return TrainResponse(success=False, error=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")
