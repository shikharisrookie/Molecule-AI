import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

export async function predictMolecule(smiles) {
  const { data } = await api.post('/predict', { smiles });
  return data;
}

export async function predictBatch(smilesList) {
  const { data } = await api.post('/predict/batch', { smiles_list: smilesList });
  return data;
}

export async function getMoleculeInfo(smiles) {
  const { data } = await api.post('/molecule-info', { smiles });
  return data;
}

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

export default api;
