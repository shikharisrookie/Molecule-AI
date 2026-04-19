"""Upload router — /upload-dataset endpoint."""
import json
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.models.schemas import UploadResponse
from app.services.data_service import save_uploaded_file
from app.db.database import get_db
from app.db.models import UploadedDataset

router = APIRouter(prefix="/upload-dataset", tags=["Dataset Upload"])


@router.post("", response_model=UploadResponse, summary="Upload a CSV dataset")
async def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Upload a CSV file containing molecular data.
    
    The CSV should have at minimum:
    - A column with SMILES strings
    - A column with activity labels (0/1) for training
    
    Returns dataset metadata including column names and a preview.
    """
    if not file.filename.endswith(".csv"):
        return UploadResponse(
            success=False,
            error="Only CSV files are supported. Please upload a .csv file."
        )

    try:
        content = await file.read()
        if len(content) > 50 * 1024 * 1024:  # 50MB limit
            return UploadResponse(
                success=False,
                error="File too large. Maximum size is 50MB."
            )

        metadata = save_uploaded_file(content, file.filename)

        # Save to database
        db_entry = UploadedDataset(
            dataset_id=metadata["dataset_id"],
            filename=metadata["filename"],
            filepath=metadata["filepath"],
            num_rows=metadata["num_rows"],
            num_columns=metadata["num_columns"],
            columns=json.dumps(metadata["columns"]),
        )
        db.add(db_entry)
        db.commit()

        return UploadResponse(success=True, **metadata)
    except ValueError as e:
        return UploadResponse(success=False, error=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
