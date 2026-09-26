import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 120000, // 2 min timeout for ML model training
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred';
    console.error('API Error:', message);
    return Promise.reject(new Error(message));
  }
);

export const getRoutes = () => api.get('/routes');
export const getVessels = () => api.get('/vessels');
export const getPorts = () => api.get('/ports');
export const getHealth = () => api.get('/health');
export const recommendVessel = (data) => api.post('/recommend-vessel', data);

export const predictRates = (data) => api.post('/predict-rates', data);
export const calculateCost = (data) => api.post('/calculate-cost', data);
export const lighteringAnalysis = (data) => api.post('/lightering-analysis', data);
export const charterDecision = (data) => api.post('/charter-decision', data);
export const fullAnalysis = (data) => api.post('/full-analysis', data);

export default api;
