from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
MODEL_DIR = BASE_DIR / "app" / "ml" / "pretrained"
DATABASE_PATH = BASE_DIR / "moleculeai.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

MORGAN_RADIUS = 2
MORGAN_NBITS = 2048

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)
