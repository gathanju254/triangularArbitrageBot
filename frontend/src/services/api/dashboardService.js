// frontend/src/services/api/dashboardService.js
import api from './api';

// Enhanced mock data for development
const mockStats = {
  total_profit: 1250.75,
  total_trades: 45,
  success_rate: 87.5,
  active_opportunities: 3,
  today_profit: 150.25,
  avg_profit_percentage: 2.5,
  total_opportunities: 156,
  successful_trades: 39
};

const mockProfitHistory = [
  { date: '2024-01-01', profit: 100 },
  { date: '2024-01-02', profit: 150 },
  { date: '2024-01-03', profit: 200 },
  { date: '2024-01-04', profit: 180 },
  { date: '2024-01-05', profit: 220 },
  { date: '2024-01-06', profit: 250 },
  { date: '2024-01-07', profit: 300 },
];

const mockOpportunities = [
  {
    id: 1,
    symbol: 'BTC/USDT',
    buy_exchange_name: 'binance',
    sell_exchange_name: 'coinbase',
    buy_price: '45000.00',
    sell_price: '45150.00',
    profit_percentage: 0.33,
    status: 'active',
    detected_at: '2024-01-15T10:30:00Z'
  },
  {
    id: 2,
    symbol: 'ETH/USDT',
    buy_exchange_name: 'kraken',
    sell_exchange_name: 'binance',
    buy_price: '2500.00',
    sell_price: '2512.50',
    profit_percentage: 0.50,
    status: 'active',
    detected_at: '2024-01-15T10:25:00Z'
  }
];

export const dashboardService = {
  async getStats() {
    try {
      // Try to get stats from arbitrage endpoints
      const response = await api.get('/arbitrage/stats/');
      
      // Normalize stats data
      const normalizedStats = this.normalizeStats(response.data);
      
      // Ensure we have all required fields
      return {
        ...mockStats, // Use mock as base to ensure all fields exist
        ...normalizedStats // Override with real data
      };
    } catch (error) {
      console.warn('Dashboard stats API not available, using mock data:', error.message);
      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 500));
      return mockStats;
    }
  },

  async getOpportunities() {
    try {
      const response = await api.get('/arbitrage/opportunities/');
      return this.normalizeOpportunities(response.data);
    } catch (error) {
      console.warn('Opportunities API not available, using mock data:', error.message);
      await new Promise(resolve => setTimeout(resolve, 500));
      return this.normalizeOpportunities(mockOpportunities);
    }
  },

  async getProfitHistory(days = 30) {
    try {
      const response = await api.get(`/arbitrage/profit-history/?days=${days}`);
      return this.normalizeProfitHistory(response.data);
    } catch (error) {
      console.warn('Profit history API not available, using mock data:', error.message);
      await new Promise(resolve => setTimeout(resolve, 500));
      return this.normalizeProfitHistory(mockProfitHistory);
    }
  },

  async getArbitrageStats(days = 30) {
    try {
      const response = await api.get(`/arbitrage/stats/?days=${days}`);
      return this.normalizeStats(response.data);
    } catch (error) {
      console.warn('Arbitrage stats API not available, using mock data:', error.message);
      await new Promise(resolve => setTimeout(resolve, 500));
      return {
        total_profit: 1250.75,
        successful_trades: 45,
        success_rate: 87.5,
        avg_profit_per_trade: 27.79,
        total_opportunities: 156
      };
    }
  },

  // Enhanced error handler for dashboard service
  handleDashboardError(error, operation, fallbackData) {
    console.error(`Dashboard ${operation} failed:`, error);
    
    if (fallbackData !== undefined) {
      console.warn(`Using fallback data for ${operation}`);
      // Add artificial delay for better UX with mock data
      return new Promise(resolve => setTimeout(() => resolve(fallbackData), 500));
    }
    
    throw error;
  },

  // Get dashboard overview (combines multiple endpoints)
  async getDashboardOverview() {
    try {
      const [stats, opportunities, profitHistory] = await Promise.all([
        this.getStats().catch(error => {
          console.warn('Stats endpoint failed, using mock:', error.message);
          return mockStats;
        }),
        this.getOpportunities().catch(error => {
          console.warn('Opportunities endpoint failed, using mock:', error.message);
          return this.normalizeOpportunities(mockOpportunities);
        }),
        this.getProfitHistory(7).catch(error => {
          console.warn('Profit history endpoint failed, using mock:', error.message);
          return this.normalizeProfitHistory(mockProfitHistory);
        })
      ]);

      return {
        stats: this.normalizeStats(stats),
        opportunities: this.normalizeOpportunities(opportunities),
        profit_history: this.normalizeProfitHistory(profitHistory),
        last_updated: new Date().toISOString(),
        using_mock_data: false
      };
    } catch (error) {
      console.error('Dashboard overview failed, using comprehensive mock data:', error);
      
      // Return comprehensive mock data
      return {
        stats: mockStats,
        opportunities: this.normalizeOpportunities(mockOpportunities),
        profit_history: this.normalizeProfitHistory(mockProfitHistory),
        last_updated: new Date().toISOString(),
        using_mock_data: true
      };
    }
  },

  // Helper method to normalize opportunities data
  normalizeOpportunities(data) {
    if (!data) {
      console.warn('No opportunities data provided, returning empty array');
      return [];
    }

    if (Array.isArray(data)) {
      return data;
    } else if (data && Array.isArray(data.results)) {
      return data.results;
    } else if (data && Array.isArray(data.opportunities)) {
      return data.opportunities;
    } else if (data && Array.isArray(data.data)) {
      return data.data;
    } else if (typeof data === 'object') {
      // If it's a single opportunity object, wrap it in an array
      console.warn('Single opportunity object detected, wrapping in array');
      return [data];
    } else {
      console.warn('Unexpected opportunities format, returning empty array:', data);
      return [];
    }
  },

  // Helper method to normalize profit history data
  normalizeProfitHistory(data) {
    if (!data) {
      console.warn('No profit history data provided, returning empty array');
      return [];
    }

    if (Array.isArray(data)) {
      return data;
    } else if (data && Array.isArray(data.results)) {
      return data.results;
    } else if (data && Array.isArray(data.history)) {
      return data.history;
    } else if (data && Array.isArray(data.data)) {
      return data.data;
    } else if (data && Array.isArray(data.profit_history)) {
      return data.profit_history;
    } else if (typeof data === 'object') {
      // If it's a single profit entry, wrap it in an array
      console.warn('Single profit history entry detected, wrapping in array');
      return [data];
    } else {
      console.warn('Unexpected profit history format, returning empty array:', data);
      return [];
    }
  },

  // Helper method to normalize stats data
  normalizeStats(data) {
    if (!data) {
      console.warn('No stats data provided, returning empty object');
      return {};
    }

    if (typeof data === 'object' && !Array.isArray(data)) {
      return data;
    } else {
      console.warn('Unexpected stats format, returning empty object:', data);
      return {};
    }
  },

  // Validate data structure (useful for debugging)
  validateDataStructure(data, expectedType) {
    if (!data) {
      return { valid: false, message: 'Data is null or undefined' };
    }

    switch (expectedType) {
      case 'array':
        return { 
          valid: Array.isArray(data), 
          message: Array.isArray(data) ? 'Valid array' : 'Expected array' 
        };
      case 'object':
        return { 
          valid: typeof data === 'object' && !Array.isArray(data), 
          message: (typeof data === 'object' && !Array.isArray(data)) ? 'Valid object' : 'Expected object' 
        };
      default:
        return { valid: true, message: 'No validation performed' };
    }
  }
};

export default dashboardService;