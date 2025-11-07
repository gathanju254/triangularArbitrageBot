// frontend/src/utils/errorHandler.js


export class ApiError extends Error {
  constructor(message, status, code, originalError) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.originalError = originalError;
  }
}

export const handleApiError = (error, fallbackData = undefined) => {
  // If it's already a handled error, just return/rethrow
  if (error instanceof ApiError) {
    if (fallbackData !== undefined) return fallbackData;
    throw error;
  }

  const response = error.response;
  
  if (response?.status === 401) {
    // Clear auth and redirect
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    if (!window.location.pathname.includes('/login')) {
      window.location.href = '/login';
    }
    throw new ApiError('Authentication required', 401, 'UNAUTHORIZED', error);
    
  } else if (response?.status === 403) {
    throw new ApiError('Access forbidden', 403, 'FORBIDDEN', error);
    
  } else if (response?.status === 404) {
    throw new ApiError('Resource not found', 404, 'NOT_FOUND', error);
    
  } else if (response?.status >= 500) {
    console.error('Server error:', error);
    if (fallbackData !== undefined) return fallbackData;
    throw new ApiError('Server error occurred', response.status, 'SERVER_ERROR', error);
    
  } else if (error.code === 'ECONNABORTED') {
    console.error('Request timeout:', error);
    if (fallbackData !== undefined) return fallbackData;
    throw new ApiError('Request timeout', 408, 'TIMEOUT', error);
    
  } else if (!error.response) {
    console.error('Network error:', error);
    if (fallbackData !== undefined) return fallbackData;
    throw new ApiError('Network error - cannot reach server', 0, 'NETWORK_ERROR', error);
    
  } else {
    console.warn('API error:', error);
    if (fallbackData !== undefined) return fallbackData;
    throw new ApiError(
      error.response?.data?.message || 'Unknown error occurred',
      error.response?.status || 500,
      error.response?.data?.code || 'UNKNOWN_ERROR',
      error
    );
  }
};

// Utility for service functions
export const withErrorHandling = (apiCall, fallbackData = undefined) => {
  return async (...args) => {
    try {
      const response = await apiCall(...args);
      return response;
    } catch (error) {
      return handleApiError(error, fallbackData);
    }
  };
};