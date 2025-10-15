// src/utils/api.js
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

// Create axios instance with default configuration
const api = axios.create({
    baseURL: API_BASE_URL,
    timeout: 15000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor
api.interceptors.request.use(
    (config) => {
        const timestamp = new Date().toISOString();
        console.log(`🚀 [${timestamp}] Making ${config.method?.toUpperCase()} request to ${config.url}`);
        
        // Log request data for POST/PUT requests
        if (['post', 'put', 'patch'].includes(config.method?.toLowerCase()) && config.data) {
            console.log('📦 Request data:', config.data);
        }
        
        return config;
    },
    (error) => {
        console.error('❌ Request interceptor error:', error);
        return Promise.reject(error);
    }
);

// Response interceptor
api.interceptors.response.use(
    (response) => {
        const timestamp = new Date().toISOString();
        console.log(`✅ [${timestamp}] Response received from ${response.config.url}`, {
            status: response.status,
            statusText: response.statusText,
            data: response.data
        });
        
        // Return the data directly for easier consumption
        return response.data;
    },
    (error) => {
        const timestamp = new Date().toISOString();
        
        // Enhanced error logging
        if (error.response) {
            // Server responded with error status
            console.error(`❌ [${timestamp}] API Error Response:`, {
                url: error.config?.url,
                method: error.config?.method?.toUpperCase(),
                status: error.response.status,
                statusText: error.response.statusText,
                data: error.response.data
            });
        } else if (error.request) {
            // Request made but no response received
            console.error(`❌ [${timestamp}] Network Error: No response received from server`, {
                url: error.config?.url,
                method: error.config?.method?.toUpperCase()
            });
        } else {
            // Something else happened
            console.error(`❌ [${timestamp}] Request Setup Error:`, error.message);
        }
        
        // Create a standardized error object
        const apiError = {
            message: error.response?.data?.message || error.response?.data?.error || error.message || 'Unknown API error',
            status: error.response?.status,
            code: error.response?.data?.code,
            timestamp: new Date().toISOString(),
            url: error.config?.url
        };
        
        return Promise.reject(apiError);
    }
);

export const arbitrageAPI = {
    // System control
    getSystemStatus: () => api.get('/system/status/'),
    controlSystem: (action) => api.post('/system/control/', { action }),
    
    // Opportunities
    getOpportunities: () => api.get('/opportunities/'),
    
    // Performance
    getPerformance: () => api.get('/performance/'),
    
    // Trading (fixed endpoint)
    executeTrade: (triangle, amount, exchange = 'binance') => 
        api.post('/trading/execute/', { triangle, amount, exchange }),
    getTradeHistory: () => api.get('/trading/history/'),
    
    // Settings (fixed endpoint)
    updateSettings: (settings) => api.post('/settings/update/', { settings }),
    getSettings: () => api.get('/settings/'),
    
    // Health check (fixed endpoint)
    healthCheck: () => api.get('/health/'),
    
    // System management
    resetSystem: () => api.post('/reset_system/'),
};

// Utility functions for API calls
export const apiUtils = {
    // Generic GET request
    get: (url, config = {}) => api.get(url, config),
    
    // Generic POST request
    post: (url, data = {}, config = {}) => api.post(url, data, config),
    
    // Generic PUT request
    put: (url, data = {}, config = {}) => api.put(url, data, config),
    
    // Generic DELETE request
    delete: (url, config = {}) => api.delete(url, config),
    
    // Check if API server is reachable
    checkServerConnection: async () => {
        try {
            const response = await api.get('/health_check/');
            return {
                connected: true,
                status: response.status,
                data: response.data
            };
        } catch (error) {
            return {
                connected: false,
                error: error.message
            };
        }
    },
    
    // Retry mechanism for failed requests
    retry: async (apiCall, maxRetries = 3, delay = 1000) => {
        let lastError;
        
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                const result = await apiCall();
                console.log(`✅ Request succeeded on attempt ${attempt}`);
                return result;
            } catch (error) {
                lastError = error;
                console.warn(`⚠️ Request failed on attempt ${attempt}:`, error.message);
                
                if (attempt < maxRetries) {
                    console.log(`⏳ Retrying in ${delay}ms...`);
                    await new Promise(resolve => setTimeout(resolve, delay));
                    // Exponential backoff
                    delay *= 2;
                }
            }
        }
        
        console.error(`❌ All ${maxRetries} attempts failed`);
        throw lastError;
    }
};

// API status monitor
export const apiMonitor = {
    isOnline: true,
    lastCheck: null,
    
    checkStatus: async () => {
        try {
            const startTime = Date.now();
            await api.get('/health_check/');
            const responseTime = Date.now() - startTime;
            
            apiMonitor.isOnline = true;
            apiMonitor.lastCheck = new Date().toISOString();
            apiMonitor.responseTime = responseTime;
            
            console.log(`🌐 API Status: Online (${responseTime}ms)`);
            return { online: true, responseTime };
        } catch (error) {
            apiMonitor.isOnline = false;
            apiMonitor.lastCheck = new Date().toISOString();
            
            console.warn('🌐 API Status: Offline');
            return { online: false, error: error.message };
        }
    },
    
    startMonitoring: (interval = 30000) => {
        console.log(`🔍 Starting API monitoring every ${interval}ms`);
        
        // Initial check
        apiMonitor.checkStatus();
        
        // Periodic checks
        const monitorInterval = setInterval(apiMonitor.checkStatus, interval);
        
        return {
            stop: () => {
                clearInterval(monitorInterval);
                console.log('🔍 Stopped API monitoring');
            }
        };
    }
};

// Export the axios instance for direct use if needed
export { api };

export default {
    arbitrageAPI,
    apiUtils,
    apiMonitor,
    api
};