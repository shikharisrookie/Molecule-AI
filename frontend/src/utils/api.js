import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
});

// ── Predictions ──────────────────────────────────────────────────

export async function predictMolecule(smiles) {
  const { data } = await api.post('/predict', { smiles });
  return data;
}

export async function predictBatch(smilesList) {
  const { data } = await api.post('/predict/batch', { smiles_list: smilesList });
  return data;
}

// ── Molecule Info ────────────────────────────────────────────────

export async function getMoleculeInfo(smiles) {
  const { data } = await api.post('/molecule-info', { smiles });
  return data;
}

// ── Dataset Upload & Training ────────────────────────────────────

export async function uploadDataset(file) {
  const formData = new FormData();
  formData.append('file', file);
  const { data } = await api.post('/upload-dataset', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function trainModel(datasetId, modelType = 'xgboost', targetColumn = 'activity_label') {
  const { data } = await api.post('/train', {
    dataset_id: datasetId,
    model_type: modelType,
    target_column: targetColumn,
    smiles_column: 'smiles',
  });
  return data;
}

// ── History & Export ─────────────────────────────────────────────

export async function getHistory(limit = 50, offset = 0) {
  const { data } = await api.get('/history', { params: { limit, offset } });
  return data;
}

export async function getExampleMolecules() {
  const { data } = await api.get('/example-molecules');
  return data;
}

export async function exportHistory(format = 'csv') {
  const response = await api.get(`/export/${format}`, { responseType: 'blob' });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `moleculeai_predictions.${format}`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

// ── Similarity Search ────────────────────────────────────────────

export async function searchSimilar(smiles, topK = 10, minSimilarity = 0.1) {
  const { data } = await api.post('/similarity', {
    smiles,
    top_k: topK,
    min_similarity: minSimilarity,
  });
  return data;
}

// ── Model Information ────────────────────────────────────────────

export async function getModels() {
  const { data } = await api.get('/models');
  return data;
}

export async function getModelMetrics(modelId) {
  const { data } = await api.get(`/models/${modelId}`);
  return data;
}

export async function getTrainingReport() {
  const { data } = await api.get('/models/report/training');
  return data;
}

// ── AI Chat ──────────────────────────────────────────────────────

export async function chatWithAI(message, contextSmiles = null, history = []) {
  const { data } = await api.post('/chat', {
    message,
    context_smiles: contextSmiles,
    history,
  });
  return data;
}

// ── Health Check ─────────────────────────────────────────────────

export async function healthCheck() {
  const { data } = await api.get('/health');
  return data;
}

export default api;
