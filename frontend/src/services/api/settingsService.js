// frontend/src/services/api/settingsService.js
import api from './api';

// Enhanced response handler
const handleResponse = (response) => {
  if (response.status >= 200 && response.status < 300) {
    return response.data;
  }
  throw new Error(`HTTP error! status: ${response.status}`);
};

// Enhanced error handler with better logging and null safety
const handleError = (error, operation) => {
  console.error(`❌ ${operation} failed:`, error);
  
  // Handle null/undefined error
  if (!error) {
    throw new Error(`Unknown error occurred while ${operation}`);
  }
  
  // Handle axios response errors
  if (error.response) {
    const errorData = error.response.data;
    const errorMessage = errorData.detail || errorData.error || errorData.message || `Failed to ${operation}`;
    
    const enhancedError = new Error(errorMessage);
    enhancedError.response = error.response;
    enhancedError.status = error.response.status;
    enhancedError.data = errorData;
    
    throw enhancedError;
  } 
  // Handle network errors
  else if (error.request) {
    throw new Error(`Network error: Unable to connect to server while ${operation}`);
  } 
  // Handle other errors with null-safe message access
  else {
    const errorMsg = error.message || `Unknown error occurred while ${operation}`;
    throw new Error(`Error ${operation}: ${errorMsg}`);
  }
};

// Development fallback data for the new settings structure
const getDevelopmentFallbackData = (operation) => {
  if (import.meta.env.DEV) {
    console.log(`🏗️ Using development fallback data for: ${operation}`);
    
    switch (operation) {
      case 'user-settings':
        return {
          trading: {
            trading_mode: 'manual',
            max_concurrent_trades: 3,
            min_trade_amount: 10.00,
            slippage_tolerance: 0.1,
            auto_trading: false
          },
          risk: {
            risk_tolerance: 'medium',
            max_daily_loss: 1000.00,
            max_position_size: 5000.00,
            max_drawdown: 20.0,
            stop_loss_enabled: true,
            take_profit_enabled: true,
            stop_loss_percent: 2.0,
            take_profit_percent: 5.0
          },
          notifications: {
            email_notifications: true,
            push_notifications: false,
            trading_alerts: true,
            risk_alerts: true
          },
          exchanges: {
            preferred_exchanges: ['binance', 'kraken'],
            min_profit_threshold: 0.3,
            enabled_exchanges: ['binance', 'kraken']
          },
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        };
      case 'trading-settings':
        return {
          trading_mode: 'manual',
          max_concurrent_trades: 3,
          min_trade_amount: 10.00,
          slippage_tolerance: 0.1,
          auto_trading: false
        };
      case 'risk-settings':
        return {
          risk_tolerance: 'medium',
          max_daily_loss: 1000.00,
          max_position_size: 5000.00,
          max_drawdown: 20.0,
          stop_loss_enabled: true,
          take_profit_enabled: true,
          stop_loss_percent: 2.0,
          take_profit_percent: 5.0
        };
      case 'notification-settings':
        return {
          email_notifications: true,
          push_notifications: false,
          trading_alerts: true,
          risk_alerts: true
        };
      case 'exchange-settings':
        return {
          preferred_exchanges: ['binance', 'kraken'],
          min_profit_threshold: 0.3,
          enabled_exchanges: ['binance', 'kraken']
        };
      case 'bot-config':
        return {
          base_balance: 1000.00,
          trade_size_fraction: 0.01,
          auto_restart: true,
          trading_enabled: false,
          enabled_exchanges: ['binance', 'kraken'],
          health_check_interval: 300,
          data_retention_days: 30
        };
      case 'api-keys':
        return [
          {
            id: 1,
            exchange: 'binance',
            label: 'Main Binance Account',
            api_key: 'binance_api_key_123',
            secret_key: 'binance_secret_456',
            is_active: true,
            is_validated: true,
            created_at: '2024-01-15T10:30:00Z'
          },
          {
            id: 2,
            exchange: 'kraken',
            label: 'Kraken Trading',
            api_key: 'kraken_api_key_789',
            secret_key: 'kraken_secret_012',
            is_active: true,
            is_validated: false,
            created_at: '2024-01-20T14:45:00Z'
          }
        ];
      default:
        return null;
    }
  }
  return null;
};

class SettingsService {
  // ==================== USER SETTINGS ====================
  
  async getUserSettings() {
    try {
      console.log('⚙️ Fetching user settings...');
      const response = await api.get('/users/settings/');
      const data = handleResponse(response);
      console.log('✅ User settings loaded successfully');
      return data;
    } catch (error) {
      console.error('Failed to fetch user settings:', error);
      
      // Return development fallback data
      const fallbackData = getDevelopmentFallbackData('user-settings');
      if (fallbackData) {
        console.log('🔄 Using development fallback for user settings');
        return fallbackData;
      }
      
      throw this.handleError(error, 'fetch user settings');
    }
  }

  // ==================== TRADING SETTINGS ====================
  
  async getTradingSettings() {
    try {
      console.log('📈 Fetching trading settings...');
      const response = await api.get('/users/settings/trading/');
      const data = handleResponse(response);
      console.log('✅ Trading settings loaded successfully');
      return data;
    } catch (error) {
      console.error('Failed to fetch trading settings:', error);
      
      // Return development fallback data
      const fallbackData = getDevelopmentFallbackData('trading-settings');
      if (fallbackData) {
        console.log('🔄 Using development fallback for trading settings');
        return fallbackData;
      }
      
      throw this.handleError(error, 'fetch trading settings');
    }
  }

  async updateTradingSettings(settings) {
    try {
      console.log('💾 Saving trading settings:', settings);
      
      // Transform frontend-friendly keys to backend format if needed
      const payload = {
        trading_mode: settings.trading_mode,
        max_concurrent_trades: settings.max_concurrent_trades,
        min_trade_amount: parseFloat(settings.min_trade_amount),
        slippage_tolerance: parseFloat(settings.slippage_tolerance)
      };
      
      const response = await api.put('/users/settings/trading/', payload);
      const result = handleResponse(response);
      console.log('✅ Trading settings saved successfully');
      return result;
    } catch (error) {
      console.error('Failed to update trading settings:', error);
      throw this.handleError(error, 'update trading settings');
    }
  }

  // ==================== RISK SETTINGS ====================
  
  async getRiskSettings() {
    try {
      console.log('🛡️ Fetching risk settings...');
      const response = await api.get('/users/settings/risk/');
      const data = handleResponse(response);
      console.log('✅ Risk settings loaded successfully');
      return data;
    } catch (error) {
      console.error('Failed to fetch risk settings:', error);
      
      // Return development fallback data
      const fallbackData = getDevelopmentFallbackData('risk-settings');
      if (fallbackData) {
        console.log('🔄 Using development fallback for risk settings');
        return fallbackData;
      }
      
      throw this.handleError(error, 'fetch risk settings');
    }
  }

  async updateRiskSettings(settings) {
    try {
      console.log('💾 Saving risk settings:', settings);
      
      const payload = {
        risk_tolerance: settings.risk_tolerance,
        max_daily_loss: parseFloat(settings.max_daily_loss),
        max_position_size: parseFloat(settings.max_position_size),
        max_drawdown: parseFloat(settings.max_drawdown),
        stop_loss_enabled: settings.stop_loss_enabled,
        take_profit_enabled: settings.take_profit_enabled,
        stop_loss_percent: parseFloat(settings.stop_loss_percent),
        take_profit_percent: parseFloat(settings.take_profit_percent)
      };
      
      const response = await api.put('/users/settings/risk/', payload);
      const result = handleResponse(response);
      console.log('✅ Risk settings saved successfully');
      return result;
    } catch (error) {
      console.error('Failed to update risk settings:', error);
      throw this.handleError(error, 'update risk settings');
    }
  }

  // ==================== NOTIFICATION SETTINGS ====================
  
  async getNotificationSettings() {
    try {
      console.log('🔔 Fetching notification settings...');
      const response = await api.get('/users/settings/notifications/');
      const data = handleResponse(response);
      console.log('✅ Notification settings loaded successfully');
      return data;
    } catch (error) {
      console.error('Failed to fetch notification settings:', error);
      
      // Return development fallback data
      const fallbackData = getDevelopmentFallbackData('notification-settings');
      if (fallbackData) {
        console.log('🔄 Using development fallback for notification settings');
        return fallbackData;
      }
      
      throw this.handleError(error, 'fetch notification settings');
    }
  }

  async updateNotificationSettings(settings) {
    try {
      console.log('💾 Saving notification settings:', settings);
      
      const payload = {
        email_notifications: settings.email_notifications,
        push_notifications: settings.push_notifications,
        trading_alerts: settings.trading_alerts,
        risk_alerts: settings.risk_alerts
      };
      
      const response = await api.put('/users/settings/notifications/', payload);
      const result = handleResponse(response);
      console.log('✅ Notification settings saved successfully');
      return result;
    } catch (error) {
      console.error('Failed to update notification settings:', error);
      throw this.handleError(error, 'update notification settings');
    }
  }

  // ==================== EXCHANGE SETTINGS ====================
  
  async getExchangeSettings() {
    try {
      console.log('🏦 Fetching exchange settings...');
      const response = await api.get('/users/settings/exchanges/');
      const data = handleResponse(response);
      console.log('✅ Exchange settings loaded successfully');
      return data;
    } catch (error) {
      console.error('Failed to fetch exchange settings:', error);
      
      // Return development fallback data
      const fallbackData = getDevelopmentFallbackData('exchange-settings');
      if (fallbackData) {
        console.log('🔄 Using development fallback for exchange settings');
        return fallbackData;
      }
      
      throw this.handleError(error, 'fetch exchange settings');
    }
  }

  async updateExchangeSettings(settings) {
    try {
      console.log('💾 Saving exchange settings:', settings);
      
      const payload = {
        preferred_exchanges: settings.preferred_exchanges,
        min_profit_threshold: parseFloat(settings.min_profit_threshold),
        enabled_exchanges: settings.enabled_exchanges
      };
      
      const response = await api.put('/users/settings/exchanges/', payload);
      const result = handleResponse(response);
      console.log('✅ Exchange settings saved successfully');
      return result;
    } catch (error) {
      console.error('Failed to update exchange settings:', error);
      throw this.handleError(error, 'update exchange settings');
    }
  }

  // ==================== BOT CONFIGURATION ====================
  
  async getBotConfiguration() {
    try {
      console.log('🤖 Fetching bot configuration...');
      const response = await api.get('/users/bot-config/');
      const data = handleResponse(response);
      console.log('✅ Bot configuration loaded successfully');
      return data;
    } catch (error) {
      console.error('Failed to fetch bot configuration:', error);
      
      // Return development fallback data
      const fallbackData = getDevelopmentFallbackData('bot-config');
      if (fallbackData) {
        console.log('🔄 Using development fallback for bot configuration');
        return fallbackData;
      }
      
      throw this.handleError(error, 'fetch bot configuration');
    }
  }

  async updateBotConfiguration(config) {
    try {
      console.log('💾 Saving bot configuration:', config);
      
      const payload = {
        base_balance: parseFloat(config.base_balance),
        trade_size_fraction: parseFloat(config.trade_size_fraction),
        auto_restart: config.auto_restart,
        trading_enabled: config.trading_enabled,
        enabled_exchanges: config.enabled_exchanges,
        health_check_interval: parseInt(config.health_check_interval),
        data_retention_days: parseInt(config.data_retention_days)
      };
      
      const response = await api.put('/users/bot-config/', payload);
      const result = handleResponse(response);
      console.log('✅ Bot configuration saved successfully');
      return result;
    } catch (error) {
      console.error('Failed to update bot configuration:', error);
      throw this.handleError(error, 'update bot configuration');
    }
  }

  // ==================== API KEYS MANAGEMENT ====================

  async getApiKeys() {
    try {
      console.log('🔑 Fetching API keys...');
      const response = await api.get('/users/api-keys/');
      const data = handleResponse(response);
      
      // Handle different response structures
      let keysArray = [];
      if (Array.isArray(data)) {
        keysArray = data;
      } else if (data && Array.isArray(data.api_keys)) {
        keysArray = data.api_keys;
      } else if (data && Array.isArray(data.data)) {
        keysArray = data.data;
      } else if (data && typeof data === 'object') {
        keysArray = data.api_keys || data.data || [];
      }
      
      console.log(`✅ Loaded ${keysArray.length} API keys`);
      return keysArray;
    } catch (error) {
      console.error('Failed to fetch API keys:', error);
      
      // Return empty array instead of throwing to prevent table errors
      const fallbackData = getDevelopmentFallbackData('api-keys');
      if (fallbackData) {
        console.log('🔄 Using development fallback for API keys');
        return fallbackData;
      }
      
      console.warn('Returning empty array for API keys due to error');
      return [];
    }
  }

  async addApiKey(apiKeyData) {
    try {
      console.log('🔑 Adding API key for:', apiKeyData.exchange);
      
      // Validate required fields
      if (!apiKeyData.api_key?.trim() || !apiKeyData.secret_key?.trim()) {
        throw new Error('API key and secret key are required');
      }

      const payload = {
        exchange: apiKeyData.exchange,
        label: apiKeyData.label || '',
        api_key: apiKeyData.api_key.trim(),
        secret_key: apiKeyData.secret_key.trim(),
        passphrase: apiKeyData.passphrase ? apiKeyData.passphrase.trim() : '',
        is_active: true
      };

      const response = await api.post('/users/api-keys/', payload);
      const result = handleResponse(response);
      console.log('✅ API key added successfully');
      return result;
    } catch (error) {
      console.error('Failed to add API key:', error);
      throw this.handleError(error, 'add API key');
    }
  }

  async updateApiKey(id, apiKeyData) {
    try {
      console.log('🔄 Updating API key:', id);
      
      // Only send fields that are actually being updated
      const updateData = {};
      Object.keys(apiKeyData).forEach(key => {
        if (apiKeyData[key] !== undefined && apiKeyData[key] !== '') {
          updateData[key] = apiKeyData[key];
        }
      });

      const response = await api.put(`/users/api-keys/${id}/`, updateData);
      const result = handleResponse(response);
      console.log('✅ API key updated successfully');
      return result;
    } catch (error) {
      console.error('Failed to update API key:', error);
      throw this.handleError(error, 'update API key');
    }
  }

  async deleteApiKey(id) {
    try {
      console.log('🗑️ Deleting API key:', id);
      await api.delete(`/users/api-keys/${id}/`);
      console.log('✅ API key deleted successfully');
    } catch (error) {
      console.error('Failed to delete API key:', error);
      throw this.handleError(error, 'delete API key');
    }
  }

  async validateApiKey(exchange, apiKey, secretKey, passphrase = null) {
    try {
      console.log(`🔍 Validating API key for ${exchange}...`);

      const payload = {
        exchange: exchange,
        api_key: apiKey,
        secret_key: secretKey,
        ...(passphrase && { passphrase })
      };

      console.log('📤 Sending validation payload:', {
        ...payload,
        api_key: '***',
        secret_key: '***',
        passphrase: passphrase ? '***' : undefined
      });

      const response = await api.post('/users/api-keys/validate/', payload);
      const result = handleResponse(response);

      // Normalize error message if backend returned details but no top-level error
      const normalizedError = result.error ||
        (result.details && (result.details.errors ? (Array.isArray(result.details.errors) ? result.details.errors.join('; ') : result.details.errors) : result.details.error)) ||
        null;

      return {
        valid: !!result.valid,
        permissions: result.permissions || [],
        account_type: result.account_type || 'Standard',
        message: result.message || (result.valid ? 'Validation successful' : 'Validation failed'),
        error: normalizedError,
        details: result.details || {},
        timestamp: result.timestamp || new Date().toISOString()
      };

    } catch (error) {
      console.error('❌ API key validation error:', error);
      throw new Error(
        error.response?.data?.error ||
        error.response?.data?.message ||
        `Failed to validate API key for ${exchange}`
      );
    }
  }

  // ==================== EXCHANGE OPERATIONS ====================

  async getExchangeBalances() {
    try {
      console.log('💰 Fetching exchange balances...');
      const response = await api.get('/exchanges/operations/balances/');
      const data = handleResponse(response);
      console.log('✅ Exchange balances loaded');
      return data;
    } catch (error) {
      console.error('Failed to fetch exchange balances:', error);
      throw this.handleError(error, 'fetch exchange balances');
    }
  }

  async testExchangeConnectivity() {
    try {
      console.log('🌐 Testing exchange connectivity...');
      const response = await api.get('/exchanges/operations/connectivity/');
      const data = handleResponse(response);
      console.log(`✅ Connectivity test completed for ${Array.isArray(data) ? data.length : 'unknown'} exchanges`);
      return data;
    } catch (error) {
      console.error('Failed to test exchange connectivity:', error);
      throw this.handleError(error, 'test exchange connectivity');
    }
  }

  // ==================== UTILITY METHODS ====================
  
  async resetSettings() {
    try {
      console.log('🔄 Resetting settings to defaults...');
      const response = await api.post('/users/settings/reset/');
      const result = handleResponse(response);
      console.log('✅ Settings reset to defaults successfully');
      return result;
    } catch (error) {
      console.error('Failed to reset settings:', error);
      throw this.handleError(error, 'reset settings');
    }
  }

  async exportSettings() {
    try {
      console.log('📤 Exporting settings...');
      const response = await api.get('/users/settings/export/');
      const data = handleResponse(response);
      console.log('✅ Settings exported successfully');
      return data;
    } catch (error) {
      console.error('Failed to export settings:', error);
      throw this.handleError(error, 'export settings');
    }
  }

  // ==================== COMPATIBILITY METHODS ====================
  // These methods maintain backward compatibility with existing code

  async getTradingConfig() {
    // Alias for getTradingSettings for backward compatibility
    return this.getTradingSettings();
  }

  async updateTradingConfig(configData) {
    // Alias for updateTradingSettings for backward compatibility
    return this.updateTradingSettings(configData);
  }

  async getUserPreferences() {
    // Alias for getUserSettings for backward compatibility
    const settings = await this.getUserSettings();
    return {
      ...settings.trading,
      ...settings.risk,
      ...settings.notifications,
      ...settings.exchanges
    };
  }

  async updateUserPreferences(preferencesData) {
    // Update all settings categories from legacy format
    // This is a best-effort mapping for backward compatibility
    const updates = {};
    
    // Map legacy fields to new structure
    if (preferencesData.auto_trading !== undefined) {
      updates.trading_mode = preferencesData.auto_trading ? 'full_auto' : 'manual';
    }
    if (preferencesData.max_concurrent_trades !== undefined) {
      updates.max_concurrent_trades = preferencesData.max_concurrent_trades;
    }
    if (preferencesData.min_trade_amount !== undefined) {
      updates.min_trade_amount = preferencesData.min_trade_amount;
    }
    if (preferencesData.slippage_tolerance !== undefined) {
      updates.slippage_tolerance = preferencesData.slippage_tolerance;
    }
    
    // Update trading settings with mapped data
    if (Object.keys(updates).length > 0) {
      await this.updateTradingSettings(updates);
    }
    
    return { message: 'Preferences updated via compatibility layer' };
  }

  // ==================== ERROR HANDLER ====================

  handleError(error, operation) {
    if (error.response?.data?.error) {
      return new Error(error.response.data.error);
    } else if (error.response?.data?.detail) {
      return new Error(error.response.data.detail);
    } else if (error.response?.data?.message) {
      return new Error(error.response.data.message);
    } else if (error.message) {
      return new Error(`Failed to ${operation}: ${error.message}`);
    } else {
      return new Error(`Failed to ${operation}`);
    }
  }
}

export const settingsService = new SettingsService();
export default settingsService;