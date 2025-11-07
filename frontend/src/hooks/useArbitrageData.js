// frontend/src/hooks/useArbitrageData.js

import { useState, useEffect, useCallback } from 'react';
import { arbitrageService } from '../services/api/arbitrageService';
import { useWebSocket } from './useWebSocket';

export const useArbitrageData = (autoRefresh = true) => {
  const [opportunities, setOpportunities] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Load initial data
  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [opportunitiesData, statsData] = await Promise.all([
        arbitrageService.getOpportunities(),
        arbitrageService.getArbitrageStats()
      ]);
      
      setOpportunities(opportunitiesData);
      setStats(statsData);
    } catch (err) {
      setError(err.message);
      console.error('Failed to load arbitrage data:', err);
      
      // Even if there's an error, we might have fallback data from the service
      // The service already returns mock data as fallback, so we can use what we have
      if (opportunities.length === 0 && stats && Object.keys(stats).length === 0) {
        // If no data is loaded at all, try to get basic mock data
        try {
          const mockOpportunities = await arbitrageService.getOpportunities();
          const mockStats = await arbitrageService.getArbitrageStats();
          setOpportunities(mockOpportunities);
          setStats(mockStats);
        } catch (mockErr) {
          // If even mock data fails, ensure we have empty states
          setOpportunities([]);
          setStats({});
        }
      }
    } finally {
      setLoading(false);
    }
  }, [opportunities.length, stats]);

  // Real-time updates via WebSocket
  const handleWebSocketMessage = useCallback((data) => {
    if (data.type === 'new_opportunity') {
      setOpportunities(prev => [data.opportunity, ...prev.slice(0, 49)]);
    } else if (data.type === 'opportunity_update') {
      setOpportunities(prev => 
        prev.map(opp => 
          opp.id === data.opportunity.id ? data.opportunity : opp
        )
      );
    } else if (data.type === 'trade_update') {
      // Refresh stats when trades update
      loadData();
    } else if (data.type === 'stats_update') {
      // Update stats directly from WebSocket
      setStats(prev => ({ ...prev, ...data.stats }));
    }
  }, [loadData]);

  const { isConnected } = useWebSocket(
    'ws://localhost:8000/ws/arbitrage/',
    handleWebSocketMessage
  );

  useEffect(() => {
    loadData();

    if (autoRefresh) {
      const interval = setInterval(loadData, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [loadData, autoRefresh]);

  const executeTrade = async (opportunityId, tradeData) => {
    try {
      setError(null);
      const result = await arbitrageService.executeTrade(opportunityId, tradeData);
      
      // Refresh data after successful trade execution
      await loadData();
      return result;
    } catch (err) {
      setError(err.message);
      console.error('Trade execution failed:', err);
      throw err;
    }
  };

  const refreshData = useCallback(() => {
    return loadData();
  }, [loadData]);

  const getOpportunityById = useCallback((id) => {
    return opportunities.find(opp => opp.id === id) || null;
  }, [opportunities]);

  const getActiveOpportunities = useCallback(() => {
    return opportunities.filter(opp => opp.status === 'active');
  }, [opportunities]);

  const getOpportunitiesBySymbol = useCallback((symbol) => {
    return opportunities.filter(opp => 
      opp.symbol.toLowerCase().includes(symbol.toLowerCase())
    );
  }, [opportunities]);

  return {
    // Data
    opportunities,
    stats,
    
    // Filtered data helpers
    activeOpportunities: getActiveOpportunities(),
    getOpportunityById,
    getOpportunitiesBySymbol,
    
    // State
    loading,
    error,
    
    // Actions
    executeTrade,
    refreshData,
    
    // Connection status
    isWebSocketConnected: isConnected,
    
    // Metadata
    totalOpportunities: opportunities.length,
    activeOpportunitiesCount: getActiveOpportunities().length
  };
};