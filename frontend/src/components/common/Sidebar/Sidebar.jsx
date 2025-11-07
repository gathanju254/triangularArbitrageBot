// frontend/src/components/common/Sidebar/Sidebar.jsx
import React from 'react';
import { NavLink, useNavigate, useLocation } from 'react-router-dom';
import { 
  LogoutOutlined, 
  DashboardOutlined, 
  BarChartOutlined, 
  SwapOutlined,
  SettingOutlined,
  UserOutlined 
} from '@ant-design/icons';
import { useAuth } from '../../../context/AuthContext';
import './Sidebar.css';

const TradeIcon = () => <SwapOutlined />;

const Sidebar = ({ collapsed, mobileOpen, onMobileClose }) => {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
      description: 'Overview and quick stats'
    },
    {
      key: '/trading',
      icon: <TradeIcon />,
      label: 'Trading',
      description: 'Manual and automated trading'
    },
    {
      key: '/analytics',
      icon: <BarChartOutlined />,
      label: 'Analytics',
      description: 'Performance metrics and insights'
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: 'Settings',
      description: 'Platform configuration'
    },
    {
      key: '/profile',
      icon: <UserOutlined />,
      label: 'Profile',
      description: 'Account management'
    },
  ];

  const handleLinkClick = () => {
    if (mobileOpen && onMobileClose) {
      onMobileClose();
    }
  };

  const handleLogout = () => {
    if (mobileOpen && onMobileClose) {
      onMobileClose();
    }
    logout();
    navigate('/login');
  };

  // Get current active item for tooltip/description
  const getActiveItemDescription = () => {
    const activeItem = menuItems.find(item => location.pathname === item.key);
    return activeItem ? activeItem.description : '';
  };

  return (
    <>
      {mobileOpen && (
        <div 
          className={`overlay ${mobileOpen ? 'mobile-open' : ''}`}
          onClick={onMobileClose}
          aria-hidden="true"
        />
      )}
      
      <aside className={`sidebar ${collapsed ? 'collapsed' : ''} ${mobileOpen ? 'mobile-open' : ''}`}>
        <div className="sidebar-logo">
          <div className="logo-content">
            <span className="logo-emoji" role="img" aria-label="logo">💰</span>
            <span className="logo-text">TAB Trading</span>
          </div>
        </div>

        {/* Navigation section */}
        <nav className="sidebar-nav" aria-label="Main navigation">
          <div className="nav-section">
            <div className="nav-section-label">Trading</div>
            <ul>
              {menuItems.slice(0, 3).map((item) => (
                <li key={item.key}>
                  <NavLink
                    to={item.key}
                    className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                    onClick={handleLinkClick}
                    aria-current={location.pathname === item.key ? 'page' : undefined}
                    title={item.description}
                  >
                    <span className="nav-icon" role="img" aria-label={item.label.toLowerCase()}>
                      {item.icon}
                    </span>
                    <span className="nav-label">{item.label}</span>
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>

          <div className="nav-section">
            <div className="nav-section-label">Account</div>
            <ul>
              {menuItems.slice(3).map((item) => (
                <li key={item.key}>
                  <NavLink
                    to={item.key}
                    className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                    onClick={handleLinkClick}
                    aria-current={location.pathname === item.key ? 'page' : undefined}
                    title={item.description}
                  >
                    <span className="nav-icon" role="img" aria-label={item.label.toLowerCase()}>
                      {item.icon}
                    </span>
                    <span className="nav-label">{item.label}</span>
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        </nav>

        {/* Active page description - only show when not collapsed */}
        {!collapsed && getActiveItemDescription() && (
          <div className="active-page-info">
            <div className="active-page-description">
              {getActiveItemDescription()}
            </div>
          </div>
        )}

        <div className="sidebar-footer">
          <button 
            className="logout-button"
            onClick={handleLogout}
            aria-label="Logout"
            title="Logout from your account"
          >
            <LogoutOutlined className="logout-icon" />
            <span className="logout-text">Logout</span>
          </button>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;