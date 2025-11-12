// frontend/src/services/api/dashboardService.js
import api from './api';

export const dashboardService = {
  async getDashboardOverview() {
    try {
      const response = await api.get('/opportunities/');
      return this.transformBackendData(response.data);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      throw error;
    }
  },

  async getSystemStatus() {
    try {
      const response = await api.get('/system/status/');
      return response.data;
    } catch (error) {
      console.error('Failed to load system status:', error);
      throw error;
    }
  },

  async getPerformance() {
    try {
      const response = await api.get('/performance/');
      return response.data;
    } catch (error) {
      console.error('Failed to load performance data:', error);
      throw error;
    }
  },

  // Transform backend data to frontend format
  transformBackendData(backendData) {
    const opportunities = backendData.opportunities?.map(opp => ({
      id: `opp-${Date.now()}-${Math.random()}`,
      symbol: opp.triangle?.join(' → ') || 'Triangular Arbitrage',
      profit_percentage: opp.profit_percentage || 0,
      status: 'active',
      timestamp: opp.timestamp,
      steps: opp.steps || [],
      prices: opp.prices || {},
      triangle: opp.triangle || []
    })) || [];

    const stats = {
      total_opportunities: backendData.count || 0,
      active_opportunities: backendData.count || 0,
      market_coverage: backendData.market_data?.total_symbols || 0,
      triangle_efficiency: backendData.engine_status?.total_triangles || 0,
      success_rate: 0, // Calculate from actual trades
      total_profit: 0, // From trade history
      using_mock_data: backendData.using_sample_data || false
    };

    // Generate profit history from opportunities
    const profit_history = this.generateProfitHistory(opportunities);

    return {
      opportunities,
      stats,
      profit_history,
      system_status: backendData.system_status,
      market_stats: backendData.market_data,
      engine_stats: backendData.engine_status,
      using_mock_data: backendData.using_sample_data || false
    };
  },

  generateProfitHistory(opportunities) {
    const history = [];
    const today = new Date();
    
    // Generate 7 days of profit history based on opportunities
    for (let i = 6; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      
      // Simulate profit based on number of opportunities that day
      const dayOpportunities = opportunities.filter(opp => {
        const oppDate = new Date(opp.timestamp);
        return oppDate.toDateString() === date.toDateString();
      });
      
      const dailyProfit = dayOpportunities.reduce((sum, opp) => {
        return sum + (opp.profit_percentage * 10); // Simulate $10 per trade
      }, 0);
      
      history.push({
        date: date.toISOString().split('T')[0],
        profit: Math.max(0, dailyProfit)
      });
    }
    
    return history;
  },

  // Real-time updates via polling
  subscribeToOpportunities(callback, interval = 10000) {
    const fetchData = async () => {
      try {
        const data = await this.getDashboardOverview();
        callback(data.opportunities);
      } catch (error) {
        console.error('Real-time update failed:', error);
      }
    };

    // Initial fetch
    fetchData();
    
    // Set up interval
    const intervalId = setInterval(fetchData, interval);
    
    // Return cleanup function
    return () => clearInterval(intervalId);
  }
};

export default dashboardService;