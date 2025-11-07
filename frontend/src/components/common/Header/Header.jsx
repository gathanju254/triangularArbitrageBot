// frontend/src/components/common/Header/Header.jsx
import React, { useMemo } from 'react';
import { Layout, Dropdown, Avatar, Button, Space, Breadcrumb, Typography, Badge } from 'antd';
import { 
  UserOutlined, 
  LogoutOutlined, 
  SettingOutlined,
  MenuOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  WalletOutlined
} from '@ant-design/icons';
import { useAuth } from '../../../context/AuthContext';
import { useNavigate, useLocation } from 'react-router-dom';
import { ROUTES } from '../../../constants/routes';
import { MESSAGES } from '../../../constants/messages';
import NotificationBell from '../NotificationBell/NotificationBell';
import './Header.css';

const { Header: AntHeader } = Layout;
const { Text } = Typography;

const Header = ({ collapsed, onCollapse, mobileOpen, onMobileToggle }) => {
  const { user, userProfile, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate(ROUTES.LOGIN);
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Profile',
      onClick: () => navigate(ROUTES.PROFILE)
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: 'Settings',
      onClick: () => navigate(ROUTES.SETTINGS)
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      onClick: handleLogout
    }
  ];

  // Use route constants for breadcrumbs and titles
  const { pageTitle, breadcrumbItems } = useMemo(() => {
    const routeTitles = {
      [ROUTES.DASHBOARD]: 'Dashboard',
      [ROUTES.TRADING]: 'Trading',
      [ROUTES.ANALYTICS]: 'Anlytics',
      [ROUTES.SETTINGS]: 'Settings',
      [ROUTES.PROFILE]: 'Profile',
    };

    const currentPath = location.pathname;
    const title = routeTitles[currentPath] || 'Dashboard';

    const items = [
      { title: 'Home' },
      { title }
    ];

    return { pageTitle: title, breadcrumbItems: items };
  }, [location.pathname]);

  // Enhanced balance display with better formatting
  const displayBalance = useMemo(() => {
    const getFromLocalUser = () => {
      try {
        const stored = localStorage.getItem('user');
        if (!stored) return null;
        const parsed = JSON.parse(stored);
        return parsed?.balance ?? parsed?.total_balance ?? parsed?.account_balance ?? null;
      } catch {
        return null;
      }
    };

    // Try several sources for balance
    let balance = userProfile?.balance ??
                  userProfile?.total_balance ??
                  userProfile?.account_balance ??
                  user?.balance ??
                  getFromLocalUser();

    if (balance === undefined || balance === null) return null;

    // If string, strip currency symbols and thousands separators
    if (typeof balance === 'string') {
      balance = balance.replace(/[^0-9.-]+/g, '');
    }

    const numericBalance = typeof balance === 'number' ? balance : parseFloat(balance);
    if (isNaN(numericBalance)) return null;

    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(numericBalance);
  }, [userProfile, user]);

  // Enhanced user display name with safe email access
  const displayName = useMemo(() => {
    const emailPrefix = userProfile?.email ? String(userProfile.email).split('@')[0] : null;
    return userProfile?.first_name ||
           userProfile?.username ||
           user?.username ||
           emailPrefix ||
           'Trader';
  }, [user?.username, userProfile?.first_name, userProfile?.username, userProfile?.email]);

  // User email for display
  const displayEmail = useMemo(() => {
    return userProfile?.email || user?.email;
  }, [user?.email, userProfile?.email]);

  // User role or status badge
  const userStatus = useMemo(() => {
    return userProfile?.role || userProfile?.account_type || 'Standard';
  }, [userProfile?.role, userProfile?.account_type]);

  return (
    <AntHeader className={`app-header ${collapsed ? 'collapsed' : ''}`}>
      <div className="header-left">
        {/* Mobile Toggle Button */}
        <Button
          type="text"
          icon={<MenuOutlined />}
          onClick={onMobileToggle}
          className="sidebar-toggle mobile-toggle"
          aria-label="Toggle mobile sidebar"
        />
        
        {/* Desktop Toggle Button */}
        <Button
          type="text"
          icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={onCollapse}
          className="sidebar-toggle desktop-toggle"
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        />
        
        <div className="header-content">
          <h1 className="page-title">{pageTitle}</h1>
          <Breadcrumb 
            items={breadcrumbItems}
            separator="/"
            className="breadcrumb"
          />
        </div>
      </div>

      <div className="header-right">
        <Space align="center" size="middle">
          {/* Notification Bell */}
          <NotificationBell />
          
          {/* User Balance Display - More Prominent */}
          {displayBalance && (
            <Badge 
              count={userStatus} 
              size="small" 
              style={{ backgroundColor: '#52c41a' }}
              offset={[-5, 5]}
            >
              <div className="user-balance-card">
                <WalletOutlined className="balance-icon" />
                <div className="balance-info">
                  <span className="balance-label">Balance</span>
                  <span className="balance-amount">
                    {displayBalance}
                  </span>
                </div>
              </div>
            </Badge>
          )}
          
          {/* User Menu Dropdown */}
          <Dropdown 
            menu={{ items: userMenuItems }} 
            placement="bottomRight"
            trigger={['click']}
            overlayClassName="user-dropdown-menu"
            getPopupContainer={trigger => trigger.parentNode}
          >
            <Button type="text" className="user-menu-trigger">
              <Space>
                <Avatar 
                  size="small" 
                  icon={<UserOutlined />}
                  src={userProfile?.avatar}
                  className="user-avatar"
                  alt="User avatar"
                />
                <div className="user-info">
                  <span className="username">
                    {displayName}
                  </span>
                  {displayEmail && (
                    <span className="user-email">{displayEmail}</span>
                  )}
                </div>
              </Space>
            </Button>
          </Dropdown>
        </Space>
      </div>
    </AntHeader>
  );
};

export default Header;