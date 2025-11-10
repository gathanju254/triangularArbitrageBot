// frontend/src/pages/Dashboard/Dashboard.jsx
import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Typography, Alert } from 'antd';
import { RocketOutlined, LineChartOutlined } from '@ant-design/icons';
import { dashboardService } from '../../services/api/dashboardService';
import { ArbitrageLoader, DataLoader } from '../../components/common/LoadingSpinner/LoadingSpinner';
import StatsCards from '../../components/dashboard/StatsCards/StatsCards';
import OpportunitiesTable from '../../components/dashboard/OpportunitiesTable/OpportunitiesTable';
import ProfitChart from '../../components/dashboard/ProfitChart/ProfitChart';
import './Dashboard.css';

const { Title } = Typography;

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadDashboardData();
    
    // Set up polling for real-time updates
    const interval = setInterval(() => {
      setRefreshing(true);
      loadDashboardData().finally(() => setRefreshing(false));
    }, 30000); // Update every 30 seconds
    
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      const data = await dashboardService.getDashboardOverview();
      setDashboardData(data);
      setError(null);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setError('Failed to load dashboard data. Using demo data.');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !dashboardData) {
    return (
      <div className="dashboard-loading">
        <ArbitrageLoader 
          text="Scanning arbitrage opportunities..." 
          fullScreen={false}
        />
      </div>
    );
  }

  const { stats, opportunities, profit_history, using_mock_data } = dashboardData || {};

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <Title level={2}>Trading Dashboard</Title>
        <div className="dashboard-subtitle">
          Real-time triangular arbitrage opportunities and performance metrics
          {refreshing && (
            <span className="dashboard-refresh-indicator">
              • Refreshing...
            </span>
          )}
        </div>
      </div>

      {error && (
        <Alert
          message={error}
          type="warning"
          showIcon
          closable
          className="dashboard-alert"
        />
      )}

      {using_mock_data && (
        <Alert
          message="Demo Mode"
          description="Currently displaying demo data. Connect to backend for live trading data."
          type="info"
          showIcon
          closable
          className="dashboard-alert"
        />
      )}

      {/* Key Statistics */}
      <StatsCards stats={stats} loading={loading || refreshing} />

      <Row gutter={[16, 16]} className="dashboard-main-content">
        <Col xs={24} lg={16}>
          <Card 
            title={
              <span className="dashboard-card-title">
                <LineChartOutlined className="dashboard-card-icon" />
                Profit History (7 Days)
              </span>
            }
            loading={loading}
            className="dashboard-chart-card"
            extra={
              refreshing && <DataLoader size="small" text="" />
            }
          >
            <ProfitChart data={profit_history} />
          </Card>
        </Col>
        
        <Col xs={24} lg={8}>
          <Card 
            title={
              <span className="dashboard-card-title">
                <RocketOutlined className="dashboard-card-icon" />
                Active Opportunities
                {refreshing && (
                  <DataLoader size="small" text="" className="dashboard-card-loader" />
                )}
              </span>
            }
            loading={loading}
            className="dashboard-opportunities-card"
          >
            <OpportunitiesTable opportunities={opportunities} />
          </Card>
        </Col>
      </Row>

      {/* Quick Actions */}
      <Row gutter={[16, 16]} className="dashboard-actions-row">
        <Col xs={24} md={8}>
          <Card 
            title="Quick Start"
            className="dashboard-quick-actions-card"
            actions={[
              <span key="trading" className="dashboard-action-item">Go to Trading</span>,
              <span key="settings" className="dashboard-action-item">Configure Settings</span>,
              <span key="analytics" className="dashboard-action-item">View Analytics</span>
            ]}
          >
            <p className="dashboard-card-description">
              Start trading immediately or configure your arbitrage strategies.
            </p>
          </Card>
        </Col>
        
        <Col xs={24} md={8}>
          <Card 
            title="System Status"
            className="dashboard-status-card"
          >
            <div className="dashboard-status-item">
              <span className="dashboard-status-label">API Connection:</span>
              <span className="dashboard-status-value dashboard-status-connected">Connected</span>
            </div>
            <div className="dashboard-status-item">
              <span className="dashboard-status-label">Data Feed:</span>
              <span className="dashboard-status-value dashboard-status-connected">Live</span>
            </div>
            <div className="dashboard-status-item">
              <span className="dashboard-status-label">Last Update:</span>
              <span className="dashboard-status-value">
                {new Date().toLocaleTimeString()}
              </span>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} md={8}>
          <Card 
            title="Recent Activity"
            className="dashboard-activity-card"
          >
            <div className="dashboard-activity-item">
              <div className="dashboard-activity-type">Opportunity Found</div>
              <div className="dashboard-activity-time">2 minutes ago</div>
            </div>
            <div className="dashboard-activity-item">
              <div className="dashboard-activity-type">Trade Executed</div>
              <div className="dashboard-activity-time">5 minutes ago</div>
            </div>
            <div className="dashboard-activity-item">
              <div className="dashboard-activity-type">Balance Updated</div>
              <div className="dashboard-activity-time">10 minutes ago</div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;