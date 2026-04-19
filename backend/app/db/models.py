"""SQLAlchemy models for the database."""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.sql import func
from app.db.database import Base


class PredictionHistory(Base):
    """Stores prediction history for molecules."""
    __tablename__ = "prediction_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    smiles = Column(String(500), nullable=False, index=True)
    canonical_smiles = Column(String(500), nullable=False)
    prediction_data = Column(Text, nullable=False)  # JSON string
    drug_likeness_score = Column(Float)
    toxicity_score = Column(Float)
    activity_probability = Column(Float)
    verdict = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UploadedDataset(Base):
    """Tracks uploaded datasets."""
    __tablename__ = "uploaded_datasets"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dataset_id = Column(String(100), unique=True, nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    num_rows = Column(Integer)
    num_columns = Column(Integer)
    columns = Column(Text)  # JSON string of column names
    created_at = Column(DateTime(timezone=True), server_default=func.now())
