// frontend/src/services/api/analyticsService.js
import api from './api';

// Mock data for development
const mockPerformanceData = {
  total_profit: 1250.75,
  total_trades: 45,
  win_rate: 67.8,
  success_rate: 87.5,
  avg_profit_per_trade: 27.79,
  sharpe_ratio: 1.8,
  max_drawdown: 8.5,
};

const mockProfitHistory = Array.from({ length: 30 }, (_, i) => ({
  date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  profit: 50 + Math.random() * 100 - 50, // Random profit between -50 and +150
}));

export const analyticsService = {
  async getPerformanceSummary(period = '30d') {
    try {
      const response = await api.get(`/analytics/performance/summary/?period=${period}`);
      return response.data;
    } catch (error) {
      console.warn('Analytics API not available, using mock data');
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 500));
      return mockPerformanceData;
    }
  },

  async getProfitHistory(period = '30d') {
    try {
      const response = await api.get(`/analytics/profit/history/?period=${period}`);
      return response.data;
    } catch (error) {
      console.warn('Profit history API not available, using mock data');
      await new Promise(resolve => setTimeout(resolve, 500));
      return mockProfitHistory;
    }
  },

  async getTradingStatistics() {
    try {
      const response = await api.get('/analytics/statistics/');
      return response.data;
    } catch (error) {
      console.warn('Trading statistics API not available');
      throw error;
    }
  },

  async getPortfolioAnalytics() {
    try {
      const response = await api.get('/analytics/portfolio/');
      return response.data;
    } catch (error) {
      console.warn('Portfolio analytics API not available');
      throw error;
    }
  },

  async exportAnalyticsData(format = 'csv') {
    try {
      const response = await api.get(`/analytics/export/?format=${format}`);
      return response.data;
    } catch (error) {
      console.warn('Export API not available');
      throw error;
    }
  },
};

export default analyticsService;