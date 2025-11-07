// frontend/src/constants/routes.js

export const ROUTES = {
  // ===== MAIN ROUTES =====
  HOME: '/dashboard',
  DASHBOARD: '/dashboard',
  TRADING: '/trading',
  ANALYTICS: '/analytics',
  SETTINGS: '/settings',
  PROFILE: '/profile',
  
  // ===== AUTH ROUTES =====
  LOGIN: '/login',
  REGISTER: '/register',
  FORGOT_PASSWORD: '/forgot-password',
  RESET_PASSWORD: '/reset-password',
  LOGOUT: '/logout',
  
  // ===== API & DOCS =====
  API_DOCS: '/docs',
  API_STATUS: '/status',
  
  // ===== TRADING SUB-ROUTES =====
  TRADING_MANUAL: '/trading/manual',
  TRADING_AUTO: '/trading/auto',
  TRADING_OPPORTUNITIES: '/trading/opportunities',
  TRADING_HISTORY: '/trading/history',
  TRADING_STRATEGIES: '/trading/strategies',
  
  // ===== SETTINGS SUB-ROUTES =====
  SETTINGS_EXCHANGES: '/settings/exchanges',
  SETTINGS_API_KEYS: '/settings/api-keys',
  SETTINGS_TRADING: '/settings/trading',
  SETTINGS_NOTIFICATIONS: '/settings/notifications',
  SETTINGS_SECURITY: '/settings/security',
  
  // ===== ANALYTICS SUB-ROUTES =====
  ANALYTICS_PERFORMANCE: '/analytics/performance',
  ANALYTICS_PROFIT_LOSS: '/analytics/profit-loss',
  ANALYTICS_MARKET_DATA: '/analytics/market-data',
};

// ===== ROUTE GROUPS =====
export const ROUTE_GROUPS = {
  // Public routes (no auth required)
  PUBLIC: [
    ROUTES.LOGIN,
    ROUTES.REGISTER,
    ROUTES.FORGOT_PASSWORD,
    ROUTES.RESET_PASSWORD,
    ROUTES.API_DOCS,
    ROUTES.API_STATUS,
  ],
  
  // Protected routes (auth required)
  PROTECTED: [
    ROUTES.DASHBOARD,
    ROUTES.TRADING,
    ROUTES.ANALYTICS,
    ROUTES.SETTINGS,
    ROUTES.PROFILE,
    ROUTES.TRADING_MANUAL,
    ROUTES.TRADING_AUTO,
    ROUTES.TRADING_OPPORTUNITIES,
    ROUTES.SETTINGS_EXCHANGES,
    ROUTES.SETTINGS_API_KEYS,
    ROUTES.SETTINGS_TRADING,
  ],
  
  // Trading related routes
  TRADING: [
    ROUTES.TRADING,
    ROUTES.TRADING_MANUAL,
    ROUTES.TRADING_AUTO,
    ROUTES.TRADING_OPPORTUNITIES,
    ROUTES.TRADING_HISTORY,
    ROUTES.TRADING_STRATEGIES,
  ],
  
  // Settings related routes
  SETTINGS: [
    ROUTES.SETTINGS,
    ROUTES.SETTINGS_EXCHANGES,
    ROUTES.SETTINGS_API_KEYS,
    ROUTES.SETTINGS_TRADING,
    ROUTES.SETTINGS_NOTIFICATIONS,
    ROUTES.SETTINGS_SECURITY,
  ],
  
  // Analytics related routes
  ANALYTICS: [
    ROUTES.ANALYTICS,
    ROUTES.ANALYTICS_PERFORMANCE,
    ROUTES.ANALYTICS_PROFIT_LOSS,
    ROUTES.ANALYTICS_MARKET_DATA,
  ],
};

// ===== ROUTE UTILITIES =====
export const routeWithParams = (route, params = {}) => {
  let path = route;
  Object.keys(params).forEach(k => {
    path = path.replace(`:${k}`, encodeURIComponent(params[k]));
  });
  return path;
};

export const getRoute = (key, params = {}) => {
  const route = ROUTES[key];
  if (!route) {
    console.warn(`Route ${key} not found`);
    return ROUTES.HOME;
  }
  return routeWithParams(route, params);
};

export const isPublicRoute = (pathname) => {
  return ROUTE_GROUPS.PUBLIC.some(route => 
    pathname === route || pathname.startsWith(route + '/')
  );
};

export const isProtectedRoute = (pathname) => {
  return ROUTE_GROUPS.PROTECTED.some(route => 
    pathname === route || pathname.startsWith(route + '/')
  );
};

export const isTradingRoute = (pathname) => {
  return ROUTE_GROUPS.TRADING.some(route => 
    pathname === route || pathname.startsWith(route + '/')
  );
};

export const isSettingsRoute = (pathname) => {
  return ROUTE_GROUPS.SETTINGS.some(route => 
    pathname === route || pathname.startsWith(route + '/')
  );
};

export const isAnalyticsRoute = (pathname) => {
  return ROUTE_GROUPS.ANALYTICS.some(route => 
    pathname === route || pathname.startsWith(route + '/')
  );
};

// ===== NAVIGATION HELPERS =====
export const getParentRoute = (pathname) => {
  if (isTradingRoute(pathname)) return ROUTES.TRADING;
  if (isSettingsRoute(pathname)) return ROUTES.SETTINGS;
  if (isAnalyticsRoute(pathname)) return ROUTES.ANALYTICS;
  return ROUTES.DASHBOARD;
};

export const getBreadcrumbItems = (pathname) => {
  const items = [{ title: 'Home', path: ROUTES.HOME }];
  
  if (isTradingRoute(pathname)) {
    items.push({ title: 'Trading', path: ROUTES.TRADING });
  } else if (isSettingsRoute(pathname)) {
    items.push({ title: 'Settings', path: ROUTES.SETTINGS });
  } else if (isAnalyticsRoute(pathname)) {
    items.push({ title: 'Analytics', path: ROUTES.ANALYTICS });
  }
  
  // Add current page if it's not the main category
  const currentRoute = Object.values(ROUTES).find(route => route === pathname);
  if (currentRoute && currentRoute !== getParentRoute(pathname)) {
    const routeName = Object.keys(ROUTES).find(key => ROUTES[key] === currentRoute);
    items.push({ 
      title: routeName ? routeName.replace(/_/g, ' ') : 'Current', 
      path: currentRoute 
    });
  }
  
  return items;
};

export default ROUTES;