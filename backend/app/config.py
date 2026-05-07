"""Application configuration — all paths and settings."""
import os
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
MODEL_DIR = BASE_DIR / "app" / "ml" / "pretrained"
DATABASE_PATH = BASE_DIR / "moleculeai.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

# ── CORS ──────────────────────────────────────────────────────────

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "").split(",") if os.environ.get("ALLOWED_ORIGINS") else [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
]

# ── Morgan Fingerprint ────────────────────────────────────────────

MORGAN_RADIUS = int(os.environ.get("MORGAN_RADIUS", "2"))
MORGAN_NBITS = int(os.environ.get("MORGAN_NBITS", "2048"))

# ── LLM Configuration (Phase 6) ──────────────────────────────────

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
LLM_MODEL = os.environ.get("LLM_MODEL", "gpt-4o-mini")

# ── Environment ───────────────────────────────────────────────────

ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"

# ── Ensure directories exist ──────────────────────────────────────

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)
