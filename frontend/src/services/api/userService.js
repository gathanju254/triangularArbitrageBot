// frontend/src/services/api/userService.js
import api from "./api";

export const userService = {
  /** ================================
   * ✅ USER AUTH & REGISTRATION
   * ================================ */
  async register(userData) {
    try {
      console.log("📝 Attempting registration with data:", {
        username: userData.username,
        email: userData.email,
        hasPassword: !!userData.password
      });

      // Convert camelCase to snake_case for Django
      const formattedData = {
        username: userData.username,
        email: userData.email,
        phone: userData.phone,
        first_name: userData.firstName,    // Convert to snake_case
        last_name: userData.lastName,      // Convert to snake_case
        password: userData.password,
        password_confirm: userData.confirmPassword  // Convert to snake_case
      };

      console.log("🔄 Sending formatted data to server:", {
        username: formattedData.username,
        email: formattedData.email,
        has_first_name: !!formattedData.first_name,
        has_last_name: !!formattedData.last_name,
        has_phone: !!formattedData.phone
      });

      const response = await api.post("/users/register/", formattedData);

      // Store tokens received upon successful registration
      if (response.data.access) {
        localStorage.setItem("access_token", response.data.access);
        localStorage.setItem("refresh_token", response.data.refresh);
      }

      console.log("✅ Registration successful");
      return response.data;
    } catch (error) {
      console.error("❌ Registration failed:", error);

      // Enhanced error handling
      if (error?.response?.status === 400) {
        const errorData = error.response.data;
        
        // Handle different error formats
        if (errorData.details) {
          // New format with details object
          const firstError = Object.values(errorData.details)[0];
          throw new Error(firstError || "Invalid registration data");
        } else if (errorData.error) {
          // Direct error message
          throw new Error(errorData.error);
        } else {
          // Field-specific errors
          const errorMsg =
            errorData.username?.[0] ||
            errorData.email?.[0] ||
            errorData.password?.[0] ||
            "Invalid registration data";
          throw new Error(errorMsg);
        }
      } else if (error?.response?.status === 409) {
        throw new Error("User already exists with this email or username");
      } else if (error?.response?.status === 404) {
        throw new Error("Registration endpoint not found");
      } else if (!error?.response) {
        throw new Error("Network error - cannot reach server");
      } else {
        throw new Error("Registration failed. Please try again.");
      }
    }
  },

  /** ================================
   * ✅ PROFILE
   * ================================ */
  async getUserProfile() {
    try {
      const response = await api.get("/users/profile/");
      console.log("✅ User profile loaded");
      return response.data;
    } catch (error) {
      console.error("❌ Failed to fetch user profile:", error);

      if (error.response?.status === 401) {
        throw new Error("Authentication required");
      } else if (error.response?.status === 404) {
        throw new Error("User profile not found");
      } else {
        throw new Error("Failed to load user profile");
      }
    }
  },

  async updateUserProfile(profileData) {
    try {
      const response = await api.put("/users/update_profile/", profileData);
      console.log("✅ Profile updated successfully");
      return response.data;
    } catch (error) {
      console.error("❌ Failed to update user profile:", error);

      if (error.response?.status === 400) {
        const errorMsg = error.response.data?.email?.[0] || "Invalid profile data";
        throw new Error(errorMsg);
      } else if (error.response?.status === 401) {
        throw new Error("Authentication required");
      } else {
        throw new Error("Failed to update profile");
      }
    }
  },

  /** ================================
   * ✅ PASSWORD MANAGEMENT
   * ================================ */
  async changePassword(passwordData) {
    try {
      const response = await api.put("/users/change-password/", passwordData);
      console.log("✅ Password changed successfully");
      return response.data;
    } catch (error) {
      console.error("❌ Failed to change password:", error);

      if (error.response?.status === 400) {
        const errorMsg =
          error.response.data?.new_password?.[0] ||
          error.response.data?.old_password?.[0] ||
          "Invalid password data";

        throw new Error(errorMsg);
      } else if (error.response?.status === 401) {
        throw new Error("Authentication required");
      } else {
        throw new Error("Failed to change password");
      }
    }
  },

  /** ================================
   * ✅ API KEYS MANAGEMENT
   * ================================ */
  // frontend/src/services/api/userService.js
async getApiKeys() {
  try {
    const response = await api.get("/users/api-keys/");
    console.log("✅ API keys loaded:", response.data);
    
    // Handle different response structures
    if (response.data && Array.isArray(response.data.api_keys)) {
      return { api_keys: response.data.api_keys };
    } else if (Array.isArray(response.data)) {
      return { api_keys: response.data };
    } else if (response.data && response.data.api_keys === undefined) {
      // If api_keys key doesn't exist but we have data, wrap it
      return { api_keys: [response.data] };
    } else {
      console.warn("Unexpected API keys response structure:", response.data);
      return { api_keys: [] };
    }
  } catch (error) {
    console.error("❌ Failed to fetch API keys:", error);
    
    if (error.response?.status === 401) {
      throw new Error("Authentication required");
    } else if (error.response?.status === 404) {
      // If endpoint not found, return empty array
      console.warn("API keys endpoint not found, returning empty array");
      return { api_keys: [] };
    } else {
      // For other errors, return empty array instead of throwing
      console.error("API keys fetch failed, returning empty array:", error.message);
      return { api_keys: [] };
    }
  }
},

/** ================================
 * ✅ API KEY VALIDATION
 * ================================ */
async validateApiKey(apiKeyId) {
  try {
    console.log(`🔍 Validating API key: ${apiKeyId}`);
    
    const response = await api.post(`/users/api-keys/${apiKeyId}/validate/`);
    console.log("✅ API key validation completed", response.data);
    return response.data;
  } catch (error) {
    console.error("❌ Failed to validate API key:", error);
    
    // Enhanced null-safe error handling
    if (!error) {
      throw new Error("Unknown error occurred during API key validation");
    }
    
    // Handle null response safely
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data || {};
      
      if (status === 400) {
        throw new Error(data.message || data.error || "API key validation failed");
      } else if (status === 401) {
        throw new Error("Authentication required - please log in again");
      } else if (status === 404) {
        throw new Error("API key not found");
      } else if (status === 500) {
        throw new Error("Server error during validation");
      } else {
        throw new Error(data.message || data.error || `Validation failed with status ${status}`);
      }
    } else if (error.request) {
      // Network error
      throw new Error("Network error - cannot reach server");
    } else {
      // Other errors
      throw new Error(error.message || "Failed to validate API key");
    }
  }
},

async addApiKey(apiKeyData) {
  try {
    console.log("🔑 Adding API key for:", apiKeyData.exchange);

    // Enhanced validation for OKX and other exchanges
    const exchangeLower = apiKeyData.exchange.toLowerCase();
    
    // OKX requires passphrase
    if (exchangeLower === 'okx' && !apiKeyData.passphrase?.trim()) {
      throw new Error('OKX requires a passphrase for API authentication');
    }

    // Coinbase and KuCoin also require passphrase
    if ((exchangeLower === 'coinbase' || exchangeLower === 'kucoin') && !apiKeyData.passphrase?.trim()) {
      throw new Error(`${apiKeyData.exchange} requires a passphrase for API authentication`);
    }

    // Validate required fields
    if (!apiKeyData.api_key?.trim()) {
      throw new Error('API key is required');
    }
    if (!apiKeyData.secret_key?.trim()) {
      throw new Error('Secret key is required');
    }

    // Validate API key format (basic checks)
    if (apiKeyData.api_key.trim().length < 20) {
      throw new Error('API key appears to be too short');
    }
    if (apiKeyData.secret_key.trim().length < 20) {
      throw new Error('Secret key appears to be too short');
    }

    const payload = {
      exchange: apiKeyData.exchange,
      label: apiKeyData.label || '',
      api_key: apiKeyData.api_key.trim(),
      secret_key: apiKeyData.secret_key.trim(),
      passphrase: apiKeyData.passphrase ? apiKeyData.passphrase.trim() : '',
      is_active: apiKeyData.is_active !== undefined ? apiKeyData.is_active : true,
      permissions: ['read', 'trade'] // Default permissions for new keys
    };

    console.log("📤 Sending API key payload:", {
      exchange: payload.exchange,
      label: payload.label,
      has_api_key: !!payload.api_key,
      has_secret: !!payload.secret_key,
      has_passphrase: !!payload.passphrase,
      is_active: payload.is_active,
      permissions: payload.permissions
    });

    const response = await api.post("/users/api-keys/", payload);
    
    // Handle different response structures
    let result;
    if (response.data && typeof response.data === 'object') {
      // If response is already the API key object
      if (response.data.id) {
        result = response.data;
      } 
      // If response has api_key nested
      else if (response.data.api_key) {
        result = response.data.api_key;
      }
      // If response has data field
      else if (response.data.data) {
        result = response.data.data;
      }
      // Use as-is
      else {
        result = response.data;
      }
    } else {
      result = response.data;
    }

    console.log("✅ API key added successfully:", {
      id: result.id,
      exchange: result.exchange,
      label: result.label,
      is_active: result.is_active,
      is_validated: result.is_validated
    });

    return result;

  } catch (error) {
    console.error("❌ Failed to add API key:", error);

    // Enhanced error handling with detailed messages
    if (error?.response?.status === 400) {
      const errorData = error.response.data;
      
      console.log("🔍 Error response details:", errorData);
      
      // Handle different error formats
      if (errorData.details) {
        // New format with details object
        const firstError = Object.values(errorData.details)[0];
        throw new Error(firstError || "Invalid API key data");
      } else if (errorData.error) {
        // Direct error message
        throw new Error(errorData.error);
      } else if (typeof errorData === 'string') {
        // String error
        throw new Error(errorData);
      } else if (errorData.passphrase) {
        // Field-specific error for passphrase
        throw new Error(errorData.passphrase);
      } else if (errorData.api_key) {
        // Field-specific error for API key
        throw new Error(errorData.api_key);
      } else if (errorData.secret_key) {
        // Field-specific error for secret key
        throw new Error(errorData.secret_key);
      } else if (errorData.exchange) {
        // Field-specific error for exchange
        throw new Error(errorData.exchange);
      } else if (errorData.non_field_errors) {
        // Non-field errors
        throw new Error(Array.isArray(errorData.non_field_errors) 
          ? errorData.non_field_errors[0] 
          : errorData.non_field_errors
        );
      } else {
        // Generic field errors
        const errorMsg =
          errorData.exchange?.[0] ||
          errorData.api_key?.[0] ||
          errorData.secret_key?.[0] ||
          errorData.passphrase?.[0] ||
          "Invalid API key data. Please check your credentials.";
        throw new Error(errorMsg);
      }
    } else if (error?.response?.status === 409) {
      throw new Error("API key already exists for this exchange");
    } else if (error?.response?.status === 401) {
      throw new Error("Authentication required - please log in again");
    } else if (error?.response?.status === 403) {
      throw new Error("Permission denied - you cannot add API keys");
    } else if (error?.response?.status === 404) {
      throw new Error("API endpoint not found - please check server configuration");
    } else if (!error?.response) {
      // Network errors
      if (error.code === 'ECONNABORTED') {
        throw new Error("Request timeout - server is not responding");
      } else if (error.message?.includes('Network Error')) {
        throw new Error("Network error - cannot reach server");
      } else {
        throw new Error("Network error - please check your connection");
      }
    } else {
      // Other server errors
      throw new Error(error.message || "Failed to add API key. Please try again.");
    }
  }
},

  async updateApiKey(id, apiKeyData) {
    try {
      const response = await api.put(`/users/api-keys/${id}/`, apiKeyData);
      console.log("✅ API key updated successfully");
      return response.data;
    } catch (error) {
      console.error("❌ Failed to update API key:", error);

      if (error.response?.status === 404) {
        throw new Error("API key not found");
      } else if (error.response?.status === 401) {
        throw new Error("Authentication required");
      } else {
        throw new Error("Failed to update API key");
      }
    }
  },

  async deleteApiKey(id) {
    try {
      await api.delete(`/users/api-keys/${id}/`);
      console.log("✅ API key deleted successfully");
    } catch (error) {
      console.error("❌ Failed to delete API key:", error);

      if (error.response?.status === 404) {
        throw new Error("API key not found");
      } else if (error.response?.status === 401) {
        throw new Error("Authentication required");
      } else {
        throw new Error("Failed to delete API key");
      }
    }
  },

  /** ================================
   * ✅ EMAIL VERIFICATION
   * ================================ */
  async verifyEmail(token) {
    try {
      const response = await api.post("/users/verify-email/", { token });
      console.log("✅ Email verified successfully");
      return response.data;
    } catch (error) {
      console.error("❌ Email verification failed:", error);

      if (error.response?.status === 400) {
        throw new Error("Invalid verification token");
      } else {
        throw new Error("Email verification failed");
      }
    }
  },

  /** ================================
   * ✅ PASSWORD RESET
   * ================================ */
  async requestPasswordReset(email) {
    try {
      const response = await api.post("/users/reset-password/", { email });
      console.log("✅ Password reset email sent");
      return response.data;
    } catch (error) {
      console.error("❌ Password reset request failed:", error);

      if (error.response?.status === 404) {
        throw new Error("No user found with this email");
      } else {
        throw new Error("Failed to send password reset email");
      }
    }
  },

  async confirmPasswordReset(uid, token, newPassword) {
    try {
      const response = await api.post("/users/reset-password/confirm/", {
        uid,
        token,
        new_password: newPassword,
      });
      console.log("✅ Password reset successful");
      return response.data;
    } catch (error) {
      console.error("❌ Password reset confirmation failed:", error);

      if (error.response?.status === 400) {
        throw new Error("Invalid reset token or password");
      } else {
        throw new Error("Password reset failed");
      }
    }
  },

  /** ================================
   * ✅ USER PREFERENCES / SETTINGS
   * ================================ */
  async getUserPreferences() {
    try {
      const response = await api.get("/users/preferences/");
      console.log("✅ User preferences loaded");
      return response.data;
    } catch (error) {
      console.error("❌ Failed to fetch user preferences:", error);
      throw new Error("Failed to load user preferences");
    }
  },

  async updateUserPreferences(preferencesData) {
    try {
      const response = await api.put("/users/preferences/", preferencesData);
      console.log("✅ User preferences updated");
      return response.data;
    } catch (error) {
      console.error("❌ Failed to update user preferences:", error);
      throw new Error("Failed to update preferences");
    }
  },
};

export default userService;