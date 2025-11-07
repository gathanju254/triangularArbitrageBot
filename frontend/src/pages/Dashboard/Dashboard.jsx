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
            <span style={{ marginLeft: 8, color: '#1890ff' }}>
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
          style={{ marginBottom: 16 }}
        />
      )}

      {using_mock_data && (
        <Alert
          message="Demo Mode"
          description="Currently displaying demo data. Connect to backend for live trading data."
          type="info"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Key Statistics */}
      <StatsCards stats={stats} loading={loading || refreshing} />

      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={16}>
          <Card 
            title={
              <span>
                <LineChartOutlined style={{ marginRight: 8 }} />
                Profit History (7 Days)
              </span>
            }
            loading={loading}
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
              <span>
                <RocketOutlined style={{ marginRight: 8 }} />
                Active Opportunities
                {refreshing && (
                  <DataLoader size="small" text="" style={{ marginLeft: 8 }} />
                )}
              </span>
            }
            loading={loading}
          >
            <OpportunitiesTable opportunities={opportunities} />
          </Card>
        </Col>
      </Row>

      {/* Quick Actions */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} md={8}>
          <Card 
            title="Quick Start"
            className="quick-actions-card"
            actions={[
              <span key="trading">Go to Trading</span>,
              <span key="settings">Configure Settings</span>,
              <span key="analytics">View Analytics</span>
            ]}
          >
            <p>Start trading immediately or configure your arbitrage strategies.</p>
          </Card>
        </Col>
        
        <Col xs={24} md={8}>
          <Card 
            title="System Status"
            className="status-card"
          >
            <div className="status-item">
              <span className="status-label">API Connection:</span>
              <span className="status-value connected">Connected</span>
            </div>
            <div className="status-item">
              <span className="status-label">Data Feed:</span>
              <span className="status-value connected">Live</span>
            </div>
            <div className="status-item">
              <span className="status-label">Last Update:</span>
              <span className="status-value">
                {new Date().toLocaleTimeString()}
              </span>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} md={8}>
          <Card 
            title="Recent Activity"
            className="activity-card"
          >
            <div className="activity-item">
              <div className="activity-type">Opportunity Found</div>
              <div className="activity-time">2 minutes ago</div>
            </div>
            <div className="activity-item">
              <div className="activity-type">Trade Executed</div>
              <div className="activity-time">5 minutes ago</div>
            </div>
            <div className="activity-item">
              <div className="activity-type">Balance Updated</div>
              <div className="activity-time">10 minutes ago</div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;