// frontend/src/App.jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, App as AntdApp } from 'antd';
import ErrorBoundary from './components/common/ErrorBoundary/ErrorBoundary';
import MainLayout from './components/layout/MainLayout';
import Dashboard from './pages/Dashboard/Dashboard';
import Trading from './pages/Trading/Trading';
import Analytics from './pages/Analytics/Analytics';
import Settings from './pages/Settings/Settings';
import Profile from './pages/Profile/Profile';
import Login from './pages/Login/Login';
import Register from './pages/Register/Register';
import { AuthProvider, useAuth } from './context/AuthContext';
import { PageLoader, ArbitrageLoader } from './components/common/LoadingSpinner/LoadingSpinner';
import { ROUTES } from './constants/routes';
import './App.css';

// 🔒 Protects routes that require authentication
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-container">
        <ArbitrageLoader text="Loading your trading dashboard..." />
      </div>
    );
  }

  return user ? children : <Navigate to={ROUTES.LOGIN} replace />;
}

// 🔒 Redirects authenticated users away from auth pages
function PublicRoute({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="loading-container">
        <PageLoader text="Loading..." />
      </div>
    );
  }

  return !user ? children : <Navigate to={ROUTES.DASHBOARD} replace />;
}

// 🧭 Layout wrapper for protected routes
function AppLayout() {
  return (
    <MainLayout>
      <ErrorBoundary>
        <Routes>
          <Route path={ROUTES.DASHBOARD} element={<Dashboard />} />
          <Route path={ROUTES.TRADING} element={<Trading />} />
          <Route path={ROUTES.ANALYTICS} element={<Analytics />} />
          <Route path={ROUTES.SETTINGS} element={<Settings />} />
          <Route path={ROUTES.PROFILE} element={<Profile />} />
          
          {/* Trading sub-routes */}
          <Route 
            path={ROUTES.TRADING_MANUAL} 
            element={<Navigate to={ROUTES.TRADING} replace />} 
          />
          <Route 
            path={ROUTES.TRADING_AUTO} 
            element={<Navigate to={ROUTES.TRADING} replace />} 
          />
          <Route 
            path={ROUTES.TRADING_OPPORTUNITIES} 
            element={<Navigate to={ROUTES.TRADING} replace />} 
          />
          
          {/* Settings sub-routes */}
          <Route 
            path={ROUTES.SETTINGS_EXCHANGES} 
            element={<Navigate to={ROUTES.SETTINGS} replace />} 
          />
          <Route 
            path={ROUTES.SETTINGS_API_KEYS} 
            element={<Navigate to={ROUTES.SETTINGS} replace />} 
          />
          <Route 
            path={ROUTES.SETTINGS_TRADING} 
            element={<Navigate to={ROUTES.SETTINGS} replace />} 
          />
          
          {/* Redirects for convenience */}
          <Route path="/" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
          <Route path="/home" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
          <Route path="/trade" element={<Navigate to={ROUTES.TRADING} replace />} />
          <Route path="/analysis" element={<Navigate to={ROUTES.ANALYTICS} replace />} />
          <Route path="/account" element={<Navigate to={ROUTES.PROFILE} replace />} />
          
          {/* Catch-all route */}
          <Route path="*" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
        </Routes>
      </ErrorBoundary>
    </MainLayout>
  );
}

// 🚀 Main App Entry Point
function AppContent() {
  // Debug environment variables
  console.log('Environment Variables:', {
    VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
    MODE: import.meta.env.MODE,
    PROD: import.meta.env.PROD,
    DEV: import.meta.env.DEV
  });

  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1890ff',
          borderRadius: 6,
          colorBgContainer: '#ffffff',
          colorBgLayout: '#f5f7fa',
        },
        components: {
          Layout: {
            bodyBg: '#f5f7fa',
            headerBg: '#ffffff',
            siderBg: '#001529',
          },
        },
      }}
    >
      <Router>
        <AuthProvider>
          <div className="App">
            <Routes>
              {/* Public routes - redirect to dashboard if already authenticated */}
              <Route 
                path={ROUTES.LOGIN} 
                element={
                  <PublicRoute>
                    <Login />
                  </PublicRoute>
                } 
              />
              <Route 
                path={ROUTES.REGISTER} 
                element={
                  <PublicRoute>
                    <Register />
                  </PublicRoute>
                } 
              />
              
              {/* Additional auth routes */}
              <Route 
                path={ROUTES.FORGOT_PASSWORD} 
                element={
                  <PublicRoute>
                    <div>Forgot Password Page - Coming Soon</div>
                  </PublicRoute>
                } 
              />
              <Route 
                path={ROUTES.RESET_PASSWORD} 
                element={
                  <PublicRoute>
                    <div>Reset Password Page - Coming Soon</div>
                  </PublicRoute>
                } 
              />
              
              {/* Info pages */}
              <Route 
                path={ROUTES.API_DOCS} 
                element={<div>API Documentation - Coming Soon</div>} 
              />
              <Route 
                path={ROUTES.API_STATUS} 
                element={<div>API Status - Coming Soon</div>} 
              />
              
              {/* Protected routes - require authentication */}
              <Route
                path="/*"
                element={
                  <ProtectedRoute>
                    <AppLayout />
                  </ProtectedRoute>
                }
              />

              {/* Root path redirect */}
              <Route path="/" element={<Navigate to={ROUTES.DASHBOARD} replace />} />
            </Routes>
          </div>
        </AuthProvider>
      </Router>
    </ConfigProvider>
  );
}

// 🎯 Root App component wrapped with AntdApp to fix message warnings
function App() {
  return (
    <AntdApp>
      <AppContent />
    </AntdApp>
  );
}

export default App;