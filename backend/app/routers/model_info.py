"""Model info router — /models endpoints."""
import os
import json
from fastapi import APIRouter
from app.models.schemas import ModelInfo, ModelListResponse
from app.ml.train_model import load_metrics
from app.config import MODEL_DIR

router = APIRouter(prefix="/models", tags=["Model Information"])


@router.get("", response_model=ModelListResponse, summary="List all trained models")
async def list_models():
    """Return metadata and metrics for all trained models."""
    models = []

    # Scan pretrained directory for model files
    if MODEL_DIR.exists():
        for filename in sorted(os.listdir(MODEL_DIR)):
            if filename.endswith("_model.joblib"):
                model_id = filename.replace("_model.joblib", "")
                metrics = load_metrics(model_id) or {}

                models.append(ModelInfo(
                    model_id=model_id,
                    task_type=metrics.get("task_type", "unknown"),
                    model_type=metrics.get("model_type", "unknown"),
                    trained_at=metrics.get("trained_at"),
                    metrics=metrics,
                ))

    return ModelListResponse(success=True, models=models)


@router.get("/{model_id}", summary="Get detailed metrics for a specific model")
async def get_model_detail(model_id: str):
    """Return full metrics for a specific model."""
    metrics = load_metrics(model_id)
    if metrics is None:
        return {"success": False, "error": f"Model not found: {model_id}"}

    return {"success": True, "model_id": model_id, "metrics": metrics}


@router.get("/report/training", summary="Get full training report")
async def get_training_report():
    """Return the comprehensive training report from the last pretrain run."""
    report_path = MODEL_DIR / "training_report.json"
    if not report_path.exists():
        return {
            "success": False,
            "error": "No training report found. Run `python -m app.ml.pretrain` first.",
        }

    with open(report_path) as f:
        report = json.load(f)

    return {"success": True, "report": report}
