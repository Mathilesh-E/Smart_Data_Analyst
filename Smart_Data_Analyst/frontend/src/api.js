import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

export const getHealth = () => api.get('/health');
export const getBenchmarks = () => api.get('/benchmarks');
export const loadBenchmark = (id) => {
  const form = new FormData();
  form.append('benchmark_id', id);
  return api.post('/load-benchmark', form);
};
export const uploadFile = (file, sheet) => {
  const form = new FormData();
  form.append('file', file);
  if (sheet) form.append('sheet', sheet);
  return api.post('/upload', form);
};
export const getDataset = () => api.get('/dataset');
export const applyCleaning = (action, params = {}) => api.post('/clean', { action, params });
export const resetDataset = () => api.post('/reset');
export const getEDA = () => api.get('/eda');
export const runStatistics = (payload) => api.post('/statistics', payload);
export const runClustering = (features, n_clusters = 3) => api.post('/cluster', { features, n_clusters });
export const runAnomaly = (features, contamination = 0.05) => api.post('/anomaly', { features, contamination });
export const runTimeSeries = (date_col, val_col, freq = 'W') => api.post('/time-series', { date_col, val_col, freq });
export const trainML = (target_col, feature_cols, task_type) => api.post('/train-ml', { target_col, feature_cols, task_type });

// A-Z Advanced Analytics
export const generatePivotTable = (payload) => api.post('/pivot-table', payload);
export const transformColumn = (payload) => api.post('/transform-column', payload);
export const testNormality = (column) => api.post('/normality-test', { column });

export const getExportUrl = (type) => `${API_BASE}/export/${type}`;
export default api;
