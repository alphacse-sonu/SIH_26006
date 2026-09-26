import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Freight API
export const freightApi = {
  getRates: (params) => api.get('/freight/rates', { params }),
  getHistory: (params) => api.get('/freight/history', { params }),
  getTrends: (params) => api.get('/freight/trends', { params }),
}

// Ports API
export const portsApi = {
  getAll: (params) => api.get('/ports/', { params }),
  getIndianEastCoast: () => api.get('/ports/indian-east-coast'),
  getLoadingPorts: (country) => api.get('/ports/loading-ports', { params: { country } }),
  getPort: (id) => api.get(`/ports/${id}`),
  getConstraints: (id) => api.get(`/ports/${id}/constraints`),
  checkVesselCompatibility: (portId, params) => 
    api.get(`/ports/${portId}/vessel-compatibility`, { params }),
}

// Vessels API
export const vesselsApi = {
  getTypes: () => api.get('/vessels/types'),
  getType: (name) => api.get(`/vessels/types/${name}`),
  getAll: (params) => api.get('/vessels/', { params }),
  optimize: (data) => api.post('/vessels/optimize', data),
}

// Predictions API
export const predictionsApi = {
  forecastFreight: (data) => api.post('/predictions/freight-forecast', data),
  analyzeMarketEntry: (data) => api.post('/predictions/market-entry', data),
  assessRisk: (params) => api.post('/predictions/risk-assessment', null, { params }),
  getHistory: (params) => api.get('/predictions/history', { params }),
  getPrediction: (id) => api.get(`/predictions/${id}`),
}

// Analytics API
export const analyticsApi = {
  getDashboard: () => api.get('/analytics/dashboard'),
  getMarketOverview: (days) => api.get('/analytics/market-overview', { params: { days } }),
  getRouteAnalytics: (originId, destId, days) => 
    api.get(`/analytics/route/${originId}/${destId}`, { params: { days } }),
  getCongestion: (region) => api.get('/analytics/congestion', { params: { region } }),
  getSeasonalAnalysis: (params) => api.get('/analytics/seasonal', { params }),
}

export default api
