<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" />
  <img src="https://img.shields.io/badge/XGBoost-FF6600?style=for-the-badge&logo=xgboost&logoColor=white" />
</p>

# Molecule-AI

> **AI-Powered Drug Discovery Platform** — Analyze molecules, predict drug properties, and accelerate pharmaceutical research using machine learning.

## Overview

**Molecule-AI** is a full-stack AI platform for computational drug discovery. Input any molecule via SMILES notation and get instant AI-powered predictions for activity, toxicity, solubility, and more — powered by 4 XGBoost models trained on MoleculeNet benchmarks.

## Key Features

- **Multi-Model Prediction** — BBB penetration, toxicity (12 endpoints), solubility, BACE-1 inhibition
- **Molecular Analysis** — LogP, TPSA, MW, QED, Lipinski violations via RDKit
- **Similarity Search** — Find similar FDA-approved drugs using Tanimoto similarity (225+ drug library)
- **AI Chemistry Chat** — Rule-based KB (20+ topics) + OpenAI LLM fallback
- **3D Visualization** — Interactive molecular structures via 3Dmol.js
- **Model Transparency** — View training metrics, ROC-AUC scores, dataset provenance
- **Batch Processing** — Upload CSVs with thousands of molecules
- **Dark Mode** — Full light/dark theme support

## Model Performance

Trained on [MoleculeNet](https://moleculenet.org/) benchmarks with scaffold splitting:

| Model | Dataset | Metric | Score | Molecules |
|-------|---------|--------|-------|-----------|
| Activity (BBBP) | BBBP | ROC-AUC | **0.917** | 2,050 |
| Toxicity (Tox21) | Tox21 | Mean AUC | **0.848** | 7,831 |
| Solubility (ESOL) | ESOL | RMSE | **0.894** | 1,128 |
| Inhibition (BACE) | BACE | ROC-AUC | **0.876** | 1,513 |

## Tech Stack

**Backend**: FastAPI, XGBoost, scikit-learn, RDKit, OpenAI API, SQLAlchemy  
**Frontend**: React 19, Vite, Tailwind CSS, Recharts, 3Dmol.js, Lucide  
**Deployment**: Render (backend) + Vercel (frontend)

## Quick Start

```bash
# Clone
git clone https://github.com/shikharisrookie/Molecule-AI.git
cd Molecule-AI

# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env          # Edit with your OPENAI_API_KEY
python run.py                 # http://localhost:8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev                   # http://localhost:5173
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /predict | Predict drug properties |
| POST | /similarity | Find similar approved drugs |
| POST | /chat | AI chemistry Q&A |
| GET | /models | List trained models with metrics |
| GET | /health | System health check |
| POST | /upload-dataset | Upload custom training data |
| POST | /train | Train model on uploaded data |

Full docs at `/docs` (Swagger UI).

## Deployment

**Backend (Render)**: Root dir `backend`, build `chmod +x build.sh && ./build.sh`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`  
**Frontend (Vercel)**: Root dir `frontend`, env `VITE_API_URL=https://your-render-url.onrender.com`

## Author

**Shikhar Kar** — [@shikharisrookie](https://github.com/shikharisrookie)

## License

MIT License
