// src/utils/api.js
// src/utils/api.js
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 10000,
});

// Request interceptor
api.interceptors.request.use(
    (config) => {
        console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
        return config;
    },
    (error) => {
        console.error('Request error:', error);
        return Promise.reject(error);
    }
);

// Response interceptor
api.interceptors.response.use(
    (response) => {
        return response.data;
    },
    (error) => {
        console.error('Response error:', error);
        return Promise.reject(error);
    }
);

export const arbitrageAPI = {
    // System control
    getSystemStatus: () => api.get('/system-status/'),
    controlSystem: (action) => api.post('/system-control/', { action }),
    
    // Opportunities
    getOpportunities: () => api.get('/get-opportunities/'),
    
    // Performance
    getPerformance: () => api.get('/get-performance/'),
    
    // Trading
    executeTrade: (triangle, amount, exchange = 'binance') => 
        api.post('/execute-trade/', { triangle, amount, exchange }),
    getTradeHistory: () => api.get('/get-trade-history/'),
    
    // Settings
    updateSettings: (settings) => api.post('/update-settings/', { settings }),
    getSettings: () => api.get('/get-settings/'),
    
    // Health check
    healthCheck: () => api.get('/health-check/'),
};

export default api;