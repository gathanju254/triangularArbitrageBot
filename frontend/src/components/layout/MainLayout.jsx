// frontend/src/components/layout/MainLayout.jsx
import React, { useState, useEffect } from 'react';
import { Layout } from 'antd';
import { useLocation } from 'react-router-dom';
import Sidebar from '../common/Sidebar/Sidebar';
import Header from '../common/Header/Header';
import './MainLayout.css';

const { Content } = Layout;

const MainLayout = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();

  // Close mobile sidebar when route changes
  useEffect(() => {
    setMobileOpen(false);
  }, [location]);

  const handleCollapse = () => {
    setCollapsed(!collapsed);
  };

  const handleMobileToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleMobileClose = () => {
    setMobileOpen(false);
  };

  return (
    <Layout className="main-layout">
      <Sidebar 
        collapsed={collapsed}
        mobileOpen={mobileOpen}
        onMobileClose={handleMobileClose}
      />
      
      <Layout className={`site-layout ${collapsed ? 'collapsed' : ''}`}>
        <Header 
          collapsed={collapsed}
          onCollapse={handleCollapse}
          mobileOpen={mobileOpen}
          onMobileToggle={handleMobileToggle}
        />
        
        <Content className="site-layout-content">
          <div className="content-wrapper">
            {children}
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;