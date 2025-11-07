// frontend/src/services/api/arbitrageService.js
import api from './api';

// Mock data for development
const mockOpportunities = [
  {
    id: 1,
    symbol: 'BTC/USDT',
    buyExchange: 'binance',
    sellExchange: 'kucoin',
    buyPrice: 44950.00,
    sellPrice: 45020.00,
    profit: 70.00,
    profitPercentage: 0.16,
    status: 'active'
  },
  {
    id: 2,
    symbol: 'ETH/USDT',
    buyExchange: 'coinbase',
    sellExchange: 'kraken',
    buyPrice: 2520.00,
    sellPrice: 2535.00,
    profit: 15.00,
    profitPercentage: 0.59,
    status: 'active'
  },
  {
    id: 3,
    symbol: 'ADA/USDT',
    buyExchange: 'huobi',
    sellExchange: 'binance',
    buyPrice: 0.48,
    sellPrice: 0.475,
    profit: -0.05,
    profitPercentage: -1.04,
    status: 'inactive'
  },
  {
    id: 4,
    symbol: 'SOL/USDT',
    buyExchange: 'kucoin',
    sellExchange: 'coinbase',
    buyPrice: 95.50,
    sellPrice: 96.20,
    profit: 0.70,
    profitPercentage: 0.73,
    status: 'active'
  },
  {
    id: 5,
    symbol: 'DOT/USDT',
    buyExchange: 'kraken',
    sellExchange: 'huobi',
    buyPrice: 6.85,
    sellPrice: 6.92,
    profit: 0.07,
    profitPercentage: 1.02,
    status: 'active'
  }
];

// Mock data generators
const getMockOpportunities = (params = {}) => {
  let filteredOpportunities = [...mockOpportunities];
  
  if (params.min_profit) {
    filteredOpportunities = filteredOpportunities.filter(
      opp => opp.profitPercentage >= parseFloat(params.min_profit)
    );
  }
  
  if (params.symbol) {
    filteredOpportunities = filteredOpportunities.filter(
      opp => opp.symbol.toLowerCase().includes(params.symbol.toLowerCase())
    );
  }
  
  return filteredOpportunities;
};

const getMockStats = () => ({
  total_opportunities: 156,
  successful_trades: 89,
  total_profit: '2450.75',
  success_rate: '87.5',
  avg_profit_per_trade: '27.53'
});

const generateMockProfitHistory = (days) => {
  const history = [];
  let baseProfit = 100;
  for (let i = days; i > 0; i--) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    const profit = baseProfit + (Math.random() * 50 - 25);
    baseProfit = profit;
    history.push({
      date: date.toISOString().split('T')[0],
      profit: Math.max(0, parseFloat(profit.toFixed(2)))
    });
  }
  return history;
};

const generateMockTradeHistory = () => {
  const statuses = ['completed', 'pending', 'failed', 'cancelled'];
  const trades = [];
  
  for (let i = 0; i < 10; i++) {
    const opportunity = mockOpportunities[i % mockOpportunities.length];
    trades.push({
      id: i + 1,
      opportunity: opportunity,
      amount: (Math.random() * 1000 + 100).toFixed(2),
      status: statuses[Math.floor(Math.random() * statuses.length)],
      actual_profit: (Math.random() * 50).toFixed(2),
      created_at: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString()
    });
  }
  
  return trades;
};

const generateMockDashboardOverview = () => {
  const recentOpportunities = mockOpportunities
    .filter(opp => opp.status === 'active')
    .slice(0, 5);
  
  const recentTrades = generateMockTradeHistory().slice(0, 3);
  
  const stats = getMockStats();
  
  return {
    recent_opportunities: recentOpportunities,
    recent_trades: recentTrades,
    stats: stats
  };
};

const getMockTradeResponse = (opportunityId) => ({
  id: Math.random().toString(36).substr(2, 9),
  opportunity: opportunityId,
  status: 'completed',
  actual_profit: '25.50',
  message: 'Trade executed successfully (mock)',
  executed_at: new Date().toISOString()
});

const getMockCancelResponse = () => ({
  status: 'Trade cancelled',
  message: 'Trade cancelled successfully (mock)'
});

// Enhanced error handler for arbitrage service
const handleArbitrageError = (error, fallbackData = null, operation = 'API operation') => {
  console.warn(`Arbitrage ${operation} failed, ${fallbackData ? 'using mock data' : 'no fallback available'}:`, error.message);
  
  if (fallbackData !== undefined) {
    // Add artificial delay for better UX with mock data
    return new Promise(resolve => setTimeout(() => resolve(fallbackData), 500));
  }
  
  throw error;
};

export const arbitrageService = {
  async getOpportunities(params = {}) {
    try {
      const response = await api.get('/arbitrage/opportunities/', { params });
      return response.data;
    } catch (error) {
      return handleArbitrageError(error, getMockOpportunities(params), 'opportunities fetch');
    }
  },

  async getOpportunity(id) {
    try {
      const response = await api.get(`/arbitrage/opportunities/${id}/`);
      return response.data;
    } catch (error) {
      const opportunity = getMockOpportunities().find(opp => opp.id === parseInt(id)) || null;
      return handleArbitrageError(error, opportunity, 'opportunity fetch');
    }
  },

  async executeTrade(opportunityId, tradeData = {}) {
    try {
      const response = await api.post('/arbitrage/trades/', {
        opportunity: opportunityId,
        amount: tradeData.amount || 100,
        ...tradeData
      });
      return response.data;
    } catch (error) {
      // For trade execution, we might want to use mock in development but not in production
      if (process.env.NODE_ENV === 'development') {
        return handleArbitrageError(error, getMockTradeResponse(opportunityId), 'trade execution');
      } else {
        // In production, don't use fallback for critical operations
        throw error;
      }
    }
  },

  async getArbitrageStats(days = 30) {
    try {
      const response = await api.get(`/arbitrage/stats/?days=${days}`);
      return response.data;
    } catch (error) {
      return handleArbitrageError(error, getMockStats(), 'stats fetch');
    }
  },

  async getProfitHistory(days = 30) {
    try {
      const response = await api.get(`/arbitrage/profit-history/?days=${days}`);
      return response.data;
    } catch (error) {
      return handleArbitrageError(error, generateMockProfitHistory(days), 'profit history fetch');
    }
  },

  async getTradeHistory() {
    try {
      const response = await api.get('/arbitrage/trades/');
      return response.data;
    } catch (error) {
      return handleArbitrageError(error, generateMockTradeHistory(), 'trade history fetch');
    }
  },

  async cancelTrade(tradeId) {
    try {
      const response = await api.post(`/arbitrage/trades/${tradeId}/cancel/`);
      return response.data;
    } catch (error) {
      // For cancellation, use mock in development only
      if (process.env.NODE_ENV === 'development') {
        return handleArbitrageError(error, getMockCancelResponse(), 'trade cancellation');
      } else {
        throw error;
      }
    }
  },

  async getDashboardOverview() {
    try {
      const response = await api.get('/arbitrage/dashboard/overview/');
      return response.data;
    } catch (error) {
      return handleArbitrageError(error, generateMockDashboardOverview(), 'dashboard overview fetch');
    }
  },

  // Real-time updates via WebSocket (placeholder for future implementation)
  subscribeToOpportunities(callback) {
    console.log('Subscribing to real-time opportunities (mock)');
    // Simulate real-time updates
    const interval = setInterval(() => {
      const randomOpportunity = {
        ...mockOpportunities[Math.floor(Math.random() * mockOpportunities.length)],
        id: Date.now(),
        profitPercentage: (Math.random() * 2).toFixed(2),
        status: Math.random() > 0.3 ? 'active' : 'inactive'
      };
      callback(randomOpportunity);
    }, 5000);

    return () => clearInterval(interval);
  },

  // Export mock generators for testing
  _mockGenerators: {
    getMockOpportunities,
    getMockStats,
    generateMockProfitHistory,
    generateMockTradeHistory,
    generateMockDashboardOverview
  }
};

export default arbitrageService;