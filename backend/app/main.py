"""FastAPI main application — MoleculeAI Backend."""
import json
import csv
import io
from fastapi import FastAPI, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.config import ALLOWED_ORIGINS
from app.db.database import init_db, get_db
from app.db.models import PredictionHistory
from app.routers import predict, molecule, upload, train

# ─── App Setup ────────────────────────────────────────────────────

app = FastAPI(
    title="MoleculeAI API",
    description=(
        "AI-powered drug discovery platform API. "
        "Predict drug-likeness, toxicity, and biological activity of molecules "
        "using machine learning models trained on molecular fingerprints."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Startup Event ────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    """Initialize database and load models on startup."""
    init_db()
    # Pre-load the default model (if it exists)
    from app.services.ml_service import get_model
    get_model("default")


# ─── Mount Routers ────────────────────────────────────────────────

app.include_router(predict.router)
app.include_router(molecule.router)
app.include_router(upload.router)
app.include_router(train.router)


# ─── Additional Endpoints ─────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "app": "MoleculeAI API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/history", tags=["History"], summary="Get prediction history")
async def get_history(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Retrieve past prediction history."""
    total = db.query(PredictionHistory).count()
    entries = (
        db.query(PredictionHistory)
        .order_by(PredictionHistory.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    history = []
    for entry in entries:
        history.append({
            "id": entry.id,
            "smiles": entry.smiles,
            "prediction_data": json.loads(entry.prediction_data),
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
        })

    return {"success": True, "history": history, "total": total}


@app.get("/export/{format}", tags=["Export"], summary="Export prediction history")
async def export_history(
    format: str,
    db: Session = Depends(get_db),
):
    """Export prediction history as CSV."""
    if format not in ("csv",):
        return {"success": False, "error": "Supported formats: csv"}

    entries = (
        db.query(PredictionHistory)
        .order_by(PredictionHistory.created_at.desc())
        .all()
    )

    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "SMILES", "Canonical SMILES", "Drug-Likeness Score",
            "Toxicity Score", "Activity Probability", "Verdict", "Date"
        ])
        for entry in entries:
            writer.writerow([
                entry.smiles,
                entry.canonical_smiles,
                entry.drug_likeness_score,
                entry.toxicity_score,
                entry.activity_probability,
                entry.verdict,
                entry.created_at.isoformat() if entry.created_at else "",
            ])
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=moleculeai_predictions.csv"},
        )


@app.get("/example-molecules", tags=["Examples"], summary="Get example molecules")
async def get_examples():
    """Return a list of well-known molecules for quick testing."""
    return {
        "examples": [
            {"name": "Aspirin", "smiles": "CC(=O)OC1=CC=CC=C1C(=O)O", "description": "Common pain reliever and anti-inflammatory"},
            {"name": "Caffeine", "smiles": "CN1C=NC2=C1C(=O)N(C(=O)N2C)C", "description": "Stimulant found in coffee and tea"},
            {"name": "Ibuprofen", "smiles": "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O", "description": "Nonsteroidal anti-inflammatory drug (NSAID)"},
            {"name": "Penicillin V", "smiles": "CC1(C)SC2C(NC(=O)COC3=CC=CC=C3)C(=O)N2C1C(=O)O", "description": "Antibiotic for bacterial infections"},
            {"name": "Metformin", "smiles": "CN(C)C(=N)NC(=N)N", "description": "First-line medication for type 2 diabetes"},
            {"name": "Paracetamol", "smiles": "CC(=O)NC1=CC=C(O)C=C1", "description": "Also known as Acetaminophen — pain and fever reducer"},
            {"name": "Dopamine", "smiles": "NCCc1ccc(O)c(O)c1", "description": "Neurotransmitter involved in reward and movement"},
            {"name": "Cholesterol", "smiles": "CC(C)CCCC(C)C1CCC2C1(CCC3C2CC=C4C3(CCC(C4)O)C)C", "description": "Essential lipid molecule found in cell membranes"},
        ]
    }
