// frontend/src/hooks/useApiKeys.js
import { useState, useCallback } from 'react';
import { message } from 'antd';
import { settingsService } from '../services/api/settingsService';

export const useApiKeys = () => {
  const [keys, setKeys] = useState([]);
  const [loading, setLoading] = useState(false);
  const [validating, setValidating] = useState(false);
  const [stats, setStats] = useState(null);

  const loadApiKeys = useCallback(async () => {
    setLoading(true);
    try {
      const response = await settingsService.getApiKeys();
      setKeys(response.api_keys || response || []);
      
      // Extract statistics if available
      if (response.statistics) {
        setStats(response.statistics);
      }
    } catch (error) {
      message.error('Failed to load API keys');
      console.error('Error loading API keys:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const addApiKey = useCallback(async (apiKeyData) => {
    try {
      const newKey = await settingsService.addApiKey(apiKeyData);
      setKeys(prev => [...prev, newKey]);
      await loadApiKeys(); // Reload to get updated stats
      return newKey;
    } catch (error) {
      throw error;
    }
  }, [loadApiKeys]);

  const updateApiKey = useCallback(async (id, updateData) => {
    try {
      const updatedKey = await settingsService.updateApiKey(id, updateData);
      setKeys(prev => prev.map(key => 
        key.id === id ? { ...key, ...updatedKey } : key
      ));
      await loadApiKeys(); // Reload to get updated stats
      return updatedKey;
    } catch (error) {
      throw error;
    }
  }, [loadApiKeys]);

  const updateApiKeyPermissions = useCallback(async (id, permissionsData) => {
    try {
      const updatedKey = await settingsService.updateApiKeyPermissions(id, permissionsData);
      setKeys(prev => prev.map(key => 
        key.id === id ? { ...key, ...updatedKey } : key
      ));
      return updatedKey;
    } catch (error) {
      throw error;
    }
  }, []);

  const deleteApiKey = useCallback(async (id) => {
    try {
      await settingsService.deleteApiKey(id);
      setKeys(prev => prev.filter(key => key.id !== id));
      await loadApiKeys(); // Reload to get updated stats
    } catch (error) {
      throw error;
    }
  }, [loadApiKeys]);

  const validateApiKey = useCallback(async (id) => {
    setValidating(true);
    try {
      const result = await settingsService.validateApiKey(id);
      
      // Update the key's validation status
      setKeys(prev => prev.map(key => 
        key.id === id ? { 
          ...key, 
          is_validated: result.connected,
          last_validated: new Date().toISOString()
        } : key
      ));
      
      return result;
    } catch (error) {
      throw error;
    } finally {
      setValidating(false);
    }
  }, []);

  const getApiKeyUsageStats = useCallback(async (id) => {
    try {
      const stats = await settingsService.getApiKeyUsageStats(id);
      return stats;
    } catch (error) {
      throw error;
    }
  }, []);

  const exportApiKeys = useCallback(async () => {
    try {
      const data = await settingsService.exportApiKeys();
      
      // Create and download file
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `api-keys-export-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      message.success('API keys exported successfully');
    } catch (error) {
      message.error('Failed to export API keys');
      console.error('Error exporting API keys:', error);
    }
  }, []);

  const bulkUpdateApiKeys = useCallback(async (updates) => {
    try {
      const result = await settingsService.bulkUpdateApiKeys(updates);
      await loadApiKeys(); // Reload to get updated data
      return result;
    } catch (error) {
      throw error;
    }
  }, [loadApiKeys]);

  const getApiKeyStats = useCallback(async () => {
    try {
      const stats = await settingsService.getApiKeyStats();
      setStats(stats);
      return stats;
    } catch (error) {
      console.error('Error loading API key stats:', error);
      return null;
    }
  }, []);

  return {
    // State
    keys,
    loading,
    validating,
    stats,
    
    // Actions
    loadApiKeys,
    addApiKey,
    updateApiKey,
    updateApiKeyPermissions,
    deleteApiKey,
    validateApiKey,
    getApiKeyUsageStats,
    exportApiKeys,
    bulkUpdateApiKeys,
    getApiKeyStats,
  };
};