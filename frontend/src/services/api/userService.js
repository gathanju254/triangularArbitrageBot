// frontend/src/services/api/userService.js
import api from './api';

export const userService = {
  // User registration
  async register(userData) {
    try {
      const response = await api.post('/users/register/', userData);
      
      if (response.data.access) {
        localStorage.setItem('access_token', response.data.access);
        localStorage.setItem('refresh_token', response.data.refresh);
      }
      
      console.log('✅ Registration successful');
      return response.data;
    } catch (error) {
      console.error('❌ Registration failed:', error);
      
      // Provide specific error messages
      if (error.response?.status === 400) {
        const errorMsg = error.response.data?.username?.[0] || 
                        error.response.data?.email?.[0] || 
                        error.response.data?.password?.[0] ||
                        'Invalid registration data';
        throw new Error(errorMsg);
      } else if (error.response?.status === 409) {
        throw new Error('User already exists with this email or username');
      } else if (!error.response) {
        throw new Error('Network error - cannot reach server');
      } else {
        throw new Error('Registration failed. Please try again.');
      }
    }
  },

  // Get user profile
  async getUserProfile() {
    try {
      const response = await api.get('/users/profile/');
      console.log('✅ User profile loaded');
      return response.data;
    } catch (error) {
      console.error('❌ Failed to fetch user profile:', error);
      
      if (error.response?.status === 401) {
        throw new Error('Authentication required');
      } else if (error.response?.status === 404) {
        throw new Error('User profile not found');
      } else {
        throw new Error('Failed to load user profile');
      }
    }
  },

  // Update user profile
  async updateUserProfile(profileData) {
    try {
      const response = await api.put('/users/profile/', profileData);
      console.log('✅ Profile updated successfully');
      return response.data;
    } catch (error) {
      console.error('❌ Failed to update user profile:', error);
      
      if (error.response?.status === 400) {
        const errorMsg = error.response.data?.email?.[0] || 
                        'Invalid profile data';
        throw new Error(errorMsg);
      } else if (error.response?.status === 401) {
        throw new Error('Authentication required');
      } else {
        throw new Error('Failed to update profile');
      }
    }
  },

  // Change password
  async changePassword(passwordData) {
    try {
      const response = await api.put('/users/change-password/', passwordData);
      console.log('✅ Password changed successfully');
      return response.data;
    } catch (error) {
      console.error('❌ Failed to change password:', error);
      
      if (error.response?.status === 400) {
        const errorMsg = error.response.data?.old_password?.[0] || 
                        error.response.data?.new_password?.[0] ||
                        'Invalid password data';
        throw new Error(errorMsg);
      } else if (error.response?.status === 401) {
        throw new Error('Authentication required');
      } else {
        throw new Error('Failed to change password');
      }
    }
  },

  // Get API keys
  async getApiKeys() {
    try {
      const response = await api.get('/users/api-keys/');
      console.log('✅ API keys loaded');
      return response.data;
    } catch (error) {
      console.error('❌ Failed to fetch API keys:', error);
      
      if (error.response?.status === 401) {
        throw new Error('Authentication required');
      } else {
        throw new Error('Failed to load API keys');
      }
    }
  },

  // Add API key
  async addApiKey(apiKeyData) {
    try {
      const response = await api.post('/users/api-keys/', apiKeyData);
      console.log('✅ API key added successfully');
      return response.data;
    } catch (error) {
      console.error('❌ Failed to add API key:', error);
      
      if (error.response?.status === 400) {
        throw new Error('Invalid API key data');
      } else if (error.response?.status === 401) {
        throw new Error('Authentication required');
      } else {
        throw new Error('Failed to add API key');
      }
    }
  },

  // Update API key
  async updateApiKey(id, apiKeyData) {
    try {
      const response = await api.put(`/users/api-keys/${id}/`, apiKeyData);
      console.log('✅ API key updated successfully');
      return response.data;
    } catch (error) {
      console.error('❌ Failed to update API key:', error);
      
      if (error.response?.status === 404) {
        throw new Error('API key not found');
      } else if (error.response?.status === 401) {
        throw new Error('Authentication required');
      } else {
        throw new Error('Failed to update API key');
      }
    }
  },

  // Delete API key
  async deleteApiKey(id) {
    try {
      await api.delete(`/users/api-keys/${id}/`);
      console.log('✅ API key deleted successfully');
    } catch (error) {
      console.error('❌ Failed to delete API key:', error);
      
      if (error.response?.status === 404) {
        throw new Error('API key not found');
      } else if (error.response?.status === 401) {
        throw new Error('Authentication required');
      } else {
        throw new Error('Failed to delete API key');
      }
    }
  },

  // Verify email (if implemented in backend)
  async verifyEmail(token) {
    try {
      const response = await api.post('/users/verify-email/', { token });
      console.log('✅ Email verified successfully');
      return response.data;
    } catch (error) {
      console.error('❌ Email verification failed:', error);
      
      if (error.response?.status === 400) {
        throw new Error('Invalid verification token');
      } else {
        throw new Error('Email verification failed');
      }
    }
  },

  // Request password reset
  async requestPasswordReset(email) {
    try {
      const response = await api.post('/users/password-reset/', { email });
      console.log('✅ Password reset email sent');
      return response.data;
    } catch (error) {
      console.error('❌ Password reset request failed:', error);
      
      if (error.response?.status === 404) {
        throw new Error('No user found with this email');
      } else {
        throw new Error('Failed to send password reset email');
      }
    }
  },

  // Confirm password reset
  async confirmPasswordReset(uid, token, newPassword) {
    try {
      const response = await api.post('/users/password-reset-confirm/', {
        uid,
        token,
        new_password: newPassword
      });
      console.log('✅ Password reset successful');
      return response.data;
    } catch (error) {
      console.error('❌ Password reset confirmation failed:', error);
      
      if (error.response?.status === 400) {
        throw new Error('Invalid reset token or password');
      } else {
        throw new Error('Password reset failed');
      }
    }
  },

  // Get user preferences/settings
  async getUserPreferences() {
    try {
      const response = await api.get('/users/preferences/');
      console.log('✅ User preferences loaded');
      return response.data;
    } catch (error) {
      console.error('❌ Failed to fetch user preferences:', error);
      throw new Error('Failed to load user preferences');
    }
  },

  // Update user preferences/settings
  async updateUserPreferences(preferencesData) {
    try {
      const response = await api.put('/users/preferences/', preferencesData);
      console.log('✅ User preferences updated');
      return response.data;
    } catch (error) {
      console.error('❌ Failed to update user preferences:', error);
      throw new Error('Failed to update preferences');
    }
  }
};