"""Data service — handles dataset operations."""
import os
import uuid
import json
import pandas as pd
from typing import Optional, Dict, Any, List
from app.config import UPLOADS_DIR, DATA_DIR


def save_uploaded_file(file_content: bytes, filename: str) -> Dict[str, Any]:
    """Save an uploaded CSV file and return metadata."""
    dataset_id = str(uuid.uuid4())[:8]
    safe_filename = f"{dataset_id}_{filename}"
    filepath = os.path.join(UPLOADS_DIR, safe_filename)

    with open(filepath, "wb") as f:
        f.write(file_content)

    # Parse and validate
    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        os.remove(filepath)
        raise ValueError(f"Could not parse CSV file: {str(e)}")

    if df.empty:
        os.remove(filepath)
        raise ValueError("The uploaded file is empty.")

    preview = df.head(5).to_dict(orient="records")

    return {
        "dataset_id": dataset_id,
        "filename": filename,
        "filepath": filepath,
        "num_rows": len(df),
        "num_columns": len(df.columns),
        "columns": list(df.columns),
        "preview": preview,
    }


def load_dataset(dataset_id: str) -> Optional[pd.DataFrame]:
    """Load a dataset by ID from the uploads directory."""
    for fname in os.listdir(UPLOADS_DIR):
        if fname.startswith(dataset_id):
            filepath = os.path.join(UPLOADS_DIR, fname)
            return pd.read_csv(filepath)
    
    # Check if it's the sample dataset
    sample_path = os.path.join(DATA_DIR, "sample_dataset.csv")
    if dataset_id == "sample" and os.path.exists(sample_path):
        return pd.read_csv(sample_path)

    return None


def get_sample_dataset_path() -> str:
    """Get path to the pre-loaded sample dataset."""
    return os.path.join(DATA_DIR, "sample_dataset.csv")
