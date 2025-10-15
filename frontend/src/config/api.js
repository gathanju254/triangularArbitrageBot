// src/config/api.js
export const API_CONFIG = {
    baseURL: 'http://localhost:8000/api',
    endpoints: {
        systemStatus: '/system/status/',
        systemControl: '/system/control/',
        opportunities: '/opportunities/',
        performance: '/performance/',
        executeTrade: '/trading/execute/',
        tradeHistory: '/trading/history/',
        settings: '/settings/',
        updateSettings: '/settings/update/',
        health: '/health/',
        resetSystem: '/reset_system/'
    }
};