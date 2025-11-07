// frontend/src/services/api/authService.js
import api from './api';

export const authService = {
  async login(username, password) {
    try {
      const response = await api.post('/users/login/', {
        username,
        password
      });
      
      if (response.data.access) {
        localStorage.setItem('access_token', response.data.access);
        localStorage.setItem('refresh_token', response.data.refresh);
        
        // Also store token expiry time if provided
        if (response.data.access_expires) {
          localStorage.setItem('access_token_expires', response.data.access_expires);
        }
      }
      
      console.log('✅ Login successful');
      return response.data;
    } catch (error) {
      console.error('❌ Login failed:', error);
      
      // Provide consistent error messages
      if (error.response?.status === 401) {
        throw new Error(error.response.data?.error || 'Invalid username or password');
      } else if (error.response?.status === 400) {
        throw new Error(error.response.data?.error || 'Invalid login data');
      } else if (!error.response) {
        throw new Error('Network error - cannot reach server');
      } else {
        throw new Error(error.response.data?.error || 'Login failed');
      }
    }
  },

  async logout() {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        // Ask server to blacklist the refresh token before clearing client storage
        await api.post('/users/logout/', { refresh_token: refreshToken });
      } else {
        // Fallback: try to call logout without body (server may accept Authorization header)
        await api.post('/users/logout/', {}).catch(() => {});
      }
    } catch (error) {
      console.warn('Logout endpoint not available or failed:', error);
    } finally {
      // Always clear local storage
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('access_token_expires');
      console.log('✅ Logout successful');
    }
  },

  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    try {
      const response = await api.post('/users/token/refresh/', {
        refresh: refreshToken,
      });
      
      localStorage.setItem('access_token', response.data.access);
      console.log('✅ Token refreshed successfully');
      return response.data;
    } catch (error) {
      console.error('❌ Token refresh failed:', error);
      
      // Provide specific error messages for token refresh
      if (error.response?.status === 401) {
        throw new Error('Session expired. Please log in again.');
      } else if (error.response?.status === 400) {
        throw new Error('Invalid refresh token');
      } else if (!error.response) {
        throw new Error('Network error during token refresh');
      } else {
        throw new Error('Token refresh failed');
      }
    }
  },

  getCurrentUser() {
    const token = localStorage.getItem('access_token');
    if (!token) return null;
    
    try {
      // Decode JWT token to get user info
      const payload = JSON.parse(atob(token.split('.')[1]));
      
      // Check if token is expired
      const currentTime = Date.now() / 1000;
      if (payload.exp && payload.exp < currentTime) {
        console.warn('⚠️ Token expired');
        this.logout();
        return null;
      }
      
      // RETURN ALL USER FIELDS NEEDED FOR PROFILE
      return {
        id: payload.user_id,
        username: payload.username,
        email: payload.email,
        first_name: payload.first_name,
        last_name: payload.last_name,
        // Add any other fields your JWT token contains
      };
    } catch (error) {
      console.error('❌ Error decoding token:', error);
      return null;
    }
  },

  // Helper method to check if user is authenticated
  isAuthenticated() {
    const user = this.getCurrentUser();
    return !!user && !this.isTokenExpiringSoon();
  },

  // Check if token is about to expire (within 5 minutes)
  isTokenExpiringSoon() {
    const token = localStorage.getItem('access_token');
    if (!token) return true;
    
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const currentTime = Date.now() / 1000;
      const timeUntilExpiry = payload.exp - currentTime;
      
      return timeUntilExpiry < 300; // 5 minutes in seconds
    } catch (error) {
      return true;
    }
  },

  // Additional helper method for token expiry in milliseconds (for intervals)
  isTokenExpiringSoonMs() {
    const token = localStorage.getItem('access_token');
    if (!token) return true;
    
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      const exp = payload.exp * 1000; // Convert to milliseconds
      const now = Date.now();
      const bufferTime = 5 * 60 * 1000; // 5 minutes buffer
      
      return (exp - now) < bufferTime;
    } catch (error) {
      return true;
    }
  },

  // Get stored tokens (useful for API calls)
  getTokens() {
    return {
      access: localStorage.getItem('access_token'),
      refresh: localStorage.getItem('refresh_token')
    };
  },

  // Clear all authentication data
  clearAuth() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('access_token_expires');
    console.log('✅ Authentication data cleared');
  }
};