// frontend/src/context/AuthContext.jsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { authService } from '../services/api/authService';
import { userService } from '../services/api/userService';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  // Initialize auth state and set up token refresh interval
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const token = localStorage.getItem('access_token');
        if (token) {
          const currentUser = authService.getCurrentUser();
          setUser(currentUser);
          
          // Load user profile
          try {
            const profileData = await userService.getUserProfile();
            setUserProfile(profileData);
          } catch (profileError) {
            console.warn('Could not load user profile:', profileError);
          }

          // Check if token needs refresh
          if (authService.isTokenExpiringSoon()) {
            try {
              await authService.refreshToken();
              const freshUser = authService.getCurrentUser();
              setUser(freshUser);
            } catch (error) {
              console.error('Failed to refresh token on init:', error);
              logout();
            }
          }
        }
      } catch (error) {
        console.error('Auth check failed:', error);
        localStorage.removeItem('access_token');
      } finally {
        setLoading(false);
      }
    };

    initializeAuth();

    // Set up periodic token refresh check (every minute)
    const interval = setInterval(() => {
       if (authService.isTokenExpiringSoonMs() && authService.isAuthenticated()) {
        console.log('🔄 Periodic token refresh check...');
        authService.refreshToken().catch(error => {
          console.error('Periodic token refresh failed:', error);
        });
      }
    }, 60000);

    return () => clearInterval(interval);
  }, []);

  // Login handler
  const login = async (username, password) => {
    try {
      setLoading(true);
      const response = await authService.login(username, password);
      const currentUser = authService.getCurrentUser();
      
      // Fetch user profile after login
      try {
        const profile = await userService.getUserProfile();
        setUserProfile(profile);
      } catch (profileError) {
        console.warn('Could not load user profile after login:', profileError);
      }
      
      setUser(currentUser);
      return response;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Registration handler
  const register = async (userData) => {
    try {
      setLoading(true);
      const response = await userService.register(userData);
      return response;
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  // Update user profile
  const updateProfile = async (profileData) => {
    try {
      const updatedProfile = await userService.updateUserProfile(profileData);
      setUserProfile(updatedProfile);
      
      // Also update user basic info if included
      if (profileData.first_name || profileData.last_name || profileData.email) {
        setUser(prev => ({ ...prev, ...profileData }));
      }
      
      return updatedProfile;
    } catch (error) {
      console.error('Profile update failed:', error);
      throw error;
    }
  };

  // Change password
  const changePassword = async (passwordData) => {
    try {
      await userService.changePassword(passwordData);
    } catch (error) {
      console.error('Password change failed:', error);
      throw error;
    }
  };

  // Check authentication status
  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('access_token');
      if (token) {
        const userData = await authService.getCurrentUser();
        setUser(userData);
        
        // Load user profile
        try {
          const profileData = await userService.getUserProfile();
          setUserProfile(profileData);
        } catch (profileError) {
          console.warn('Could not load user profile:', profileError);
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('access_token');
    }
  };

  // Logout handler
  const logout = () => {
    setLoading(true);
    authService.logout();
    setUser(null);
    setUserProfile(null);
    setLoading(false);
  };

  const value = {
    user,
    userProfile,
    loading,
    login,
    register,
    logout,
    updateProfile,
    changePassword,
    checkAuth,
    isAuthenticated: !!user,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};