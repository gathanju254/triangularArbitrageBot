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

    const response = await api.post("/users/register/", userData);

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
      // Fixed: Remove duplicate /api/ in the URL
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
      // Fixed: Remove duplicate /api/ in the URL
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
      // Fixed: Remove duplicate /api/ in the URL
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
  async getApiKeys() {
    try {
      // Fixed: Remove duplicate /api/ in the URL
      const response = await api.get("/users/api-keys/");
      console.log("✅ API keys loaded");
      return response.data;
    } catch (error) {
      console.error("❌ Failed to fetch API keys:", error);

      if (error.response?.status === 401) {
        throw new Error("Authentication required");
      } else {
        throw new Error("Failed to load API keys");
      }
    }
  },

  async addApiKey(apiKeyData) {
    try {
      // Fixed: Remove duplicate /api/ in the URL
      const response = await api.post("/users/api-keys/", apiKeyData);
      console.log("✅ API key added successfully");
      return response.data;
    } catch (error) {
      console.error("❌ Failed to add API key:", error);

      if (error.response?.status === 400) {
        throw new Error("Invalid API key data");
      } else if (error.response?.status === 401) {
        throw new Error("Authentication required");
      } else {
        throw new Error("Failed to add API key");
      }
    }
  },

  async updateApiKey(id, apiKeyData) {
    try {
      // Fixed: Remove duplicate /api/ in the URL
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
      // Fixed: Remove duplicate /api/ in the URL
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
      // Fixed: Remove duplicate /api/ in the URL
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
      // Fixed: Remove duplicate /api/ in the URL
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