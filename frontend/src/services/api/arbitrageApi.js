// frontend/src/services/api/arbitrageApi.js
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const arbitrageApi = axios.create({
  baseURL: `${API_BASE_URL}/arbitrage`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
arbitrageApi.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const arbitrageService = {
  // Opportunities
  getOpportunities: () => arbitrageApi.get('/opportunities/'),
  getOpportunity: (id) => arbitrageApi.get(`/opportunities/${id}/`),
  
  // Trading
  executeTrade: (opportunityId, data) => 
    arbitrageApi.post(`/opportunities/${opportunityId}/execute/`, data),
  
  // Analytics
  getArbitrageStats: () => arbitrageApi.get('/stats/'),
  getProfitHistory: (days = 30) => 
    arbitrageApi.get(`/profit-history/?days=${days}`),
};

export default arbitrageService;