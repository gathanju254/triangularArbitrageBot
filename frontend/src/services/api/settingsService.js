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

// Development fallback data
const getDevelopmentFallbackData = (operation) => {
  if (process.env.NODE_ENV === 'development') {
    console.log(`🏗️ Using development fallback data for: ${operation}`);
    
    switch (operation) {
      case 'exchange-settings':
        return [
          { name: 'binance', enabled: true, tradingEnabled: true, maxTradeSize: 1000, minProfitThreshold: 0.5 },
          { name: 'kucoin', enabled: true, tradingEnabled: true, maxTradeSize: 1000, minProfitThreshold: 0.5 },
          { name: 'coinbase', enabled: false, tradingEnabled: false, maxTradeSize: 1000, minProfitThreshold: 0.5 },
          { name: 'kraken', enabled: false, tradingEnabled: false, maxTradeSize: 1000, minProfitThreshold: 0.5 },
          { name: 'huobi', enabled: false, tradingEnabled: false, maxTradeSize: 1000, minProfitThreshold: 0.5 },
        ];
      default:
        return null;
    }
  }
  return null;
};

export const settingsService = {
  // =============================================
  // EXCHANGE SETTINGS MANAGEMENT
  // =============================================
  
  async getExchangeSettings() {
    try {
      console.log('🔄 Fetching exchange settings...');
      const response = await api.get('/exchanges/configured/');
      const data = handleResponse(response);
      
      // Ensure we return the exchanges array in expected format
      if (data && data.exchanges) {
        console.log(`✅ Loaded ${data.exchanges.length} exchange settings`);
        return data.exchanges;
      } else if (Array.isArray(data)) {
        console.log(`✅ Loaded ${data.length} exchange settings (direct array)`);
        return data;
      } else {
        console.warn('Unexpected response format, returning empty array');
        return [];
      }
    } catch (error) {
      console.error('Failed to fetch exchange settings:', error);
      
      // Return development fallback data
      const fallbackData = getDevelopmentFallbackData('exchange-settings');
      if (fallbackData) {
        return fallbackData;
      }
      
      handleError(error, 'fetch exchange settings');
    }
  },

  async updateExchangeSettings(exchangeSettings) {
    try {
      console.log('💾 Saving exchange settings to backend:', exchangeSettings);
      
      // Ensure we're sending the data in the correct format
      const payload = {
        exchanges: exchangeSettings
      };
      
      const response = await api.put('/exchanges/settings/', payload);
      const result = handleResponse(response);
      console.log('✅ Exchange settings saved successfully');
      return result;
    } catch (error) {
      handleError(error, 'update exchange settings');
    }
  },

  // =============================================
  // API KEYS MANAGEMENT
  // =============================================

  async getApiKeys() {
    try {
      console.log('🔑 Fetching API keys...');
      const response = await api.get('/settings/api-keys/');
      const data = handleResponse(response);
      console.log(`✅ Loaded ${Array.isArray(data) ? data.length : 'unknown'} API keys`);
      return data;
    } catch (error) {
      handleError(error, 'fetch API keys');
    }
  },

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

      const response = await api.post('/settings/api-keys/', payload);
      const result = handleResponse(response);
      console.log('✅ API key added successfully');
      return result;
    } catch (error) {
      handleError(error, 'add API key');
    }
  },

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

      const response = await api.put(`/settings/api-keys/${id}/`, updateData);
      const result = handleResponse(response);
      console.log('✅ API key updated successfully');
      return result;
    } catch (error) {
      handleError(error, 'update API key');
    }
  },

  async deleteApiKey(id) {
    try {
      console.log('🗑️ Deleting API key:', id);
      await api.delete(`/settings/api-keys/${id}/`);
      console.log('✅ API key deleted successfully');
    } catch (error) {
      handleError(error, 'delete API key');
    }
  },

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

        const response = await api.post('/exchanges/validate-api-key/', payload);
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
  },

  // =============================================
  // TRADING CONFIGURATION
  // =============================================

  async getTradingConfig() {
    try {
      console.log('⚙️ Fetching trading configuration...');
      const response = await api.get('/settings/trading-config/');
      const data = handleResponse(response);
      console.log('✅ Trading configuration loaded');
      return data;
    } catch (error) {
      handleError(error, 'fetch trading config');
    }
  },

  async updateTradingConfig(configData) {
    try {
      console.log('💾 Saving trading configuration...');
      const response = await api.put('/settings/trading-config/', configData);
      const result = handleResponse(response);
      console.log('✅ Trading configuration saved successfully');
      return result;
    } catch (error) {
      handleError(error, 'update trading config');
    }
  },

  // =============================================
  // EXCHANGE OPERATIONS
  // =============================================

  async getExchangeBalances() {
    try {
      console.log('💰 Fetching exchange balances...');
      const response = await api.get('/exchanges/operations/balances/');
      const data = handleResponse(response);
      console.log('✅ Exchange balances loaded');
      return data;
    } catch (error) {
      handleError(error, 'fetch exchange balances');
    }
  },

  async testExchangeConnectivity() {
    try {
      console.log('🌐 Testing exchange connectivity...');
      const response = await api.get('/exchanges/operations/connectivity/');
      const data = handleResponse(response);
      console.log(`✅ Connectivity test completed for ${Array.isArray(data) ? data.length : 'unknown'} exchanges`);
      return data;
    } catch (error) {
      handleError(error, 'test exchange connectivity');
    }
  },

  // =============================================
  // MARKET DATA OPERATIONS
  // =============================================

  async getMarketData(symbol = null, exchangeId = null, hours = 24) {
    try {
      console.log('📊 Fetching market data...');
      const params = { hours };
      if (symbol) params.symbol = symbol;
      if (exchangeId) params.exchange_id = exchangeId;
      
      const response = await api.get('/exchanges/market-data/', { params });
      const data = handleResponse(response);
      console.log(`✅ Market data loaded (${Array.isArray(data) ? data.length : 'unknown'} records)`);
      return data;
    } catch (error) {
      handleError(error, 'fetch market data');
    }
  },

  async getLatestMarketData() {
    try {
      console.log('📈 Fetching latest market data...');
      const response = await api.get('/exchanges/market-data/latest/');
      const data = handleResponse(response);
      console.log(`✅ Latest market data loaded (${Array.isArray(data) ? data.length : 'unknown'} symbols)`);
      return data;
    } catch (error) {
      handleError(error, 'fetch latest market data');
    }
  },

  async getTickerData(symbol, exchangeId = null) {
    try {
      console.log(`📈 Fetching ticker data for ${symbol}...`);
      const params = { symbol };
      if (exchangeId) params.exchange_id = exchangeId;
      
      const response = await api.get('/exchanges/market-data/tickers/', { params });
      const data = handleResponse(response);
      console.log(`✅ Ticker data loaded for ${symbol}`);
      return data;
    } catch (error) {
      handleError(error, 'fetch ticker data');
    }
  },

  async getOrderBook(symbol, exchangeId) {
    try {
      console.log(`📖 Fetching order book for ${symbol}...`);
      const response = await api.get('/exchanges/market-data/orderbook/', {
        params: { symbol, exchange_id: exchangeId }
      });
      const data = handleResponse(response);
      console.log(`✅ Order book loaded for ${symbol}`);
      return data;
    } catch (error) {
      handleError(error, 'fetch order book');
    }
  },

  // =============================================
  // EXCHANGE INFORMATION
  // =============================================

  async getAllExchanges() {
    try {
      console.log('🏦 Fetching all exchanges...');
      const response = await api.get('/exchanges/');
      const data = handleResponse(response);
      console.log(`✅ Loaded ${Array.isArray(data) ? data.length : 'unknown'} exchanges`);
      return data;
    } catch (error) {
      handleError(error, 'fetch all exchanges');
    }
  },

  async getExchangeStatus(exchangeId) {
    try {
      console.log(`🔍 Fetching status for exchange ${exchangeId}...`);
      const response = await api.get(`/exchanges/${exchangeId}/status/`);
      const data = handleResponse(response);
      console.log(`✅ Exchange status loaded`);
      return data;
    } catch (error) {
      handleError(error, 'fetch exchange status');
    }
  },

  async getExchangeTradingPairs(exchangeId) {
    try {
      console.log(`💱 Fetching trading pairs for exchange ${exchangeId}...`);
      const response = await api.get(`/exchanges/${exchangeId}/trading_pairs/`);
      const data = handleResponse(response);
      console.log(`✅ Loaded ${Array.isArray(data) ? data.length : 'unknown'} trading pairs`);
      return data;
    } catch (error) {
      handleError(error, 'fetch trading pairs');
    }
  },

  async getSupportedPairs() {
    try {
      console.log('🔗 Fetching supported trading pairs...');
      const response = await api.get('/exchanges/supported_pairs/');
      const data = handleResponse(response);
      console.log(`✅ Loaded ${Array.isArray(data) ? data.length : 'unknown'} supported pairs`);
      return data;
    } catch (error) {
      handleError(error, 'fetch supported pairs');
    }
  },

  // =============================================
  // USER PREFERENCES (Legacy - for backward compatibility)
  // =============================================

  async getUserPreferences() {
    try {
      console.log('👤 Fetching user preferences...');
      const response = await api.get('/settings/user-preferences/');
      const data = handleResponse(response);
      console.log('✅ User preferences loaded');
      return data;
    } catch (error) {
      handleError(error, 'fetch user preferences');
    }
  },

  async updateUserPreferences(preferencesData) {
    try {
      console.log('💾 Saving user preferences...');
      const response = await api.put('/settings/user-preferences/', preferencesData);
      const result = handleResponse(response);
      console.log('✅ User preferences saved successfully');
      return result;
    } catch (error) {
      handleError(error, 'update user preferences');
    }
  },

  // =============================================
  // ADDITIONAL EXCHANGE OPERATIONS
  // =============================================

  async syncMarketData() {
    try {
      console.log('🔄 Syncing market data...');
      const response = await api.post('/exchanges/operations/sync-market-data/');
      const result = handleResponse(response);
      console.log('✅ Market data sync initiated');
      return result;
    } catch (error) {
      handleError(error, 'sync market data');
    }
  },

  async getAllBalances() {
    try {
      console.log('💰 Fetching all balances...');
      const response = await api.get('/exchanges/operations/balances/');
      const data = handleResponse(response);
      console.log('✅ All balances loaded');
      return data;
    } catch (error) {
      handleError(error, 'fetch all balances');
    }
  }
};

export default settingsService;