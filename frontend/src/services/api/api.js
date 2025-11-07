// frontend/src/services/api/api.js
import axios from 'axios';

// Use Vite environment variable with proper fallbacks
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://tudollar-backend.onrender.com/api';

console.log('API Base URL:', API_BASE_URL); // Debug log

// Track if refresh is in progress to prevent multiple simultaneous refresh attempts
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Create axios instance with enhanced configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000, // Increased timeout for better reliability
  headers: {
    'Content-Type': 'application/json',
  },
});

// === Enhanced Error Handler ===
const handleApiError = (error, fallbackData = null) => {
  if (error.response?.status === 401) {
    // Redirect to login
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    if (!window.location.pathname.includes('/login')) {
      window.location.href = '/login';
    }
    throw new Error('Authentication required');
  } else if (error.response?.status >= 500) {
    console.error('Server error:', error);
    if (fallbackData !== undefined) return fallbackData;
    throw new Error('Server error occurred');
  } else if (error.code === 'ECONNABORTED') {
    console.error('Request timeout:', error);
    if (fallbackData !== undefined) return fallbackData;
    throw new Error('Request timeout');
  } else if (!error.response) {
    console.error('Network error:', error);
    if (fallbackData !== undefined) return fallbackData;
    throw new Error('Network error - cannot reach server');
  } else {
    console.warn('API error, using fallback data:', error);
    if (fallbackData !== undefined) return fallbackData;
    throw error;
  }
};

// === ENHANCED REQUEST INTERCEPTOR ===
// Adds JWT access token if present and handles authentication
api.interceptors.request.use(
  (config) => {
    try {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers = config.headers || {};
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (e) {
      // ignore localStorage issues during SSR/tests
      console.warn('Could not read access_token for request interceptor', e);
    }
    return config;
  },
  (error) => {
    console.error('❌ Request Interceptor Error:', error);
    return Promise.reject(error);
  }
);

// === ENHANCED RESPONSE INTERCEPTOR ===
// Automatically refresh token or redirect to login if expired
api.interceptors.response.use(
  (response) => {
    // Log successful responses for debugging (remove in production)
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    
    console.error(`❌ API Error: ${error.response?.status} ${error.config?.url}`, error.response?.data);

    // Token expired or unauthorized
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // If refresh is already in progress, queue the request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return api(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }

      console.log('🔄 Attempting token refresh...');
      originalRequest._retry = true;
      isRefreshing = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          // Use the auth service refresh endpoint
          const refreshResponse = await axios.post(`${API_BASE_URL}/users/token/refresh/`, {
            refresh: refreshToken,
          });

          // Save new access token
          const newAccessToken = refreshResponse.data.access;
          localStorage.setItem('access_token', newAccessToken);

          // Update the header and retry the original request
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          
          // Process any queued requests
          processQueue(null, newAccessToken);
          isRefreshing = false;
          
          console.log('✅ Token refreshed successfully');
          return api(originalRequest);
        } else {
          throw new Error('No refresh token available');
        }
      } catch (refreshError) {
        console.error('❌ Token refresh failed:', refreshError);
        
        // Process queued requests with error
        processQueue(refreshError, null);
        isRefreshing = false;
        
        // Clear tokens and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        
        // Only redirect if not already on login page
        const isLoginPage = window.location.pathname.includes('/login');
        const isAuthRoute = window.location.pathname.includes('/auth');
        
        if (!isLoginPage && !isAuthRoute) {
          console.warn('Token refresh failed, redirecting to login');
          window.location.href = '/login';
        }
        
        return Promise.reject(refreshError);
      }
    }

    // Handle other common errors with enhanced error handler
    if (error.response?.status === 403) {
      console.error('❌ Access forbidden');
      return Promise.reject(handleApiError(error));
    } else if (error.response?.status === 404) {
      console.error('❌ Resource not found');
      return Promise.reject(handleApiError(error));
    } else if (error.response?.status === 429) {
      console.error('❌ Rate limit exceeded');
      return Promise.reject(handleApiError(error, 'Rate limit exceeded. Please try again later.'));
    } else if (error.response?.status === 500) {
      console.error('❌ Server error');
      return Promise.reject(handleApiError(error));
    } else if (error.code === 'ECONNABORTED') {
      console.error('❌ Request timeout');
      return Promise.reject(handleApiError(error));
    } else if (!error.response) {
      console.error('❌ Network error - no response from server');
      return Promise.reject(handleApiError(error));
    }

    // For all other errors, use the enhanced error handler
    return Promise.reject(handleApiError(error));
  }
);

// === ADDITIONAL AUTH UTILITY FUNCTIONS ===

/**
 * Check if user is authenticated
 */
export const isAuthenticated = () => {
  const token = localStorage.getItem('access_token');
  if (!token) return false;

  // Optional: Check token expiration
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const isExpired = payload.exp * 1000 < Date.now();
    return !isExpired;
  } catch {
    return false;
  }
};

/**
 * Get current user from localStorage
 */
export const getCurrentUser = () => {
  try {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  } catch {
    return null;
  }
};

/**
 * Clear all auth data
 */
export const clearAuthData = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('user');
};

/**
 * Set auth data after login
 */
export const setAuthData = (data) => {
  if (data.access) {
    localStorage.setItem('access_token', data.access);
  }
  if (data.refresh) {
    localStorage.setItem('refresh_token', data.refresh);
  }
  if (data.user) {
    localStorage.setItem('user', JSON.stringify(data.user));
  }
};

/**
 * Check if we're on a public route (no auth required)
 */
export const isPublicRoute = () => {
  const publicRoutes = [
    '/login',
    '/register',
    '/forgot-password',
    '/reset-password',
    '/auth'
  ];
  return publicRoutes.some(route => 
    window.location.pathname.includes(route)
  );
};

/**
 * Check if token is about to expire (within 5 minutes)
 */
export const isTokenExpiringSoon = () => {
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
};

/**
 * Check if token is about to expire (milliseconds version for intervals)
 */
export const isTokenExpiringSoonMs = () => {
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
};

/**
 * Proactively refresh token if it's about to expire
 */
export const proactiveTokenRefresh = async () => {
  if (!isTokenExpiringSoon() || isRefreshing) {
    return;
  }

  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) {
    console.warn('No refresh token available for proactive refresh');
    return;
  }

  console.log('🔄 Proactively refreshing token...');
  isRefreshing = true;

  try {
    const response = await axios.post(`${API_BASE_URL}/users/token/refresh/`, {
      refresh: refreshToken,
    });

    const newAccessToken = response.data.access;
    localStorage.setItem('access_token', newAccessToken);
    console.log('✅ Token proactively refreshed');
    
    // Process any queued requests
    processQueue(null, newAccessToken);
  } catch (error) {
    console.error('❌ Proactive token refresh failed:', error);
    processQueue(error, null);
    
    // Don't clear tokens here - let the next 401 trigger the logout
  } finally {
    isRefreshing = false;
  }
};

/**
 * Setup proactive token refresh interval
 */
export const setupTokenRefreshInterval = () => {
  // Check every minute if token needs refresh
  return setInterval(() => {
    if (isAuthenticated() && !isRefreshing) {
      proactiveTokenRefresh();
    }
  }, 60 * 1000); // 1 minute
};

// Utility function to check if token refresh is in progress
export const isTokenRefreshInProgress = () => isRefreshing;

// Utility function to manually clear the request queue
export const clearFailedQueue = () => {
  failedQueue = [];
};

/**
 * Make authenticated API call with automatic token refresh
 */
export const authenticatedApiCall = async (method, url, data = null, options = {}) => {
  try {
    const config = {
      method,
      url,
      ...options
    };

    if (data) {
      if (method.toLowerCase() === 'get') {
        config.params = data;
      } else {
        config.data = data;
      }
    }

    const response = await api(config);
    return response.data;
  } catch (error) {
    console.error(`API call failed: ${method} ${url}`, error);
    throw error;
  }
};

/**
 * Convenience methods for common HTTP verbs
 */
export const apiClient = {
  get: (url, params = {}, options = {}) => 
    authenticatedApiCall('get', url, params, options),
  
  post: (url, data = {}, options = {}) => 
    authenticatedApiCall('post', url, data, options),
  
  put: (url, data = {}, options = {}) => 
    authenticatedApiCall('put', url, data, options),
  
  patch: (url, data = {}, options = {}) => 
    authenticatedApiCall('patch', url, data, options),
  
  delete: (url, data = {}, options = {}) => 
    authenticatedApiCall('delete', url, data, options),
};

export default api;