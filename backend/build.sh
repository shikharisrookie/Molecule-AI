#!/usr/bin/env bash
# Render build script for MoleculeAI Backend
set -o errexit

echo "=== Installing Python dependencies ==="
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Creating required directories ==="
mkdir -p app/ml/pretrained data/uploads data/datasets

echo "=== Checking pre-trained models ==="
if [ -f "app/ml/pretrained/activity_bbbp_model.joblib" ]; then
    echo "Pre-trained models found - skipping training"
else
    echo "No pre-trained models found - running pretrain..."
    python -m app.ml.pretrain
fi

echo "=== Build complete ==="
