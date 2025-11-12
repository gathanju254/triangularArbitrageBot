// frontend/src/pages/Dashboard/Dashboard.jsx
import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Typography, Alert, Button, Space } from 'antd';
import { RocketOutlined, LineChartOutlined, SyncOutlined } from '@ant-design/icons';
import { dashboardService } from '../../services/api/dashboardService';
import { ArbitrageLoader, DataLoader } from '../../components/common/LoadingSpinner/LoadingSpinner';
import StatsCards from '../../components/dashboard/StatsCards/StatsCards';
import OpportunitiesTable from '../../components/dashboard/OpportunitiesTable/OpportunitiesTable';
import ProfitChart from '../../components/dashboard/ProfitChart/ProfitChart';
import './Dashboard.css';

const { Title, Text } = Typography;

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    loadDashboardData();
    
    // Set up polling for real-time updates
    const interval = setInterval(() => {
      setRefreshing(true);
      loadDashboardData().finally(() => setRefreshing(false));
    }, 15000); // Update every 15 seconds
    
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      const data = await dashboardService.getDashboardOverview();
      setDashboardData(data);
      setError(null);
      setLastUpdate(new Date());
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setError('Failed to load dashboard data. Please check if the backend server is running.');
      // You could fall back to mock data here if needed
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleManualRefresh = () => {
    setRefreshing(true);
    loadDashboardData();
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

  const { 
    stats, 
    opportunities, 
    profit_history, 
    system_status,
    market_stats,
    engine_stats,
    using_mock_data 
  } = dashboardData || {};

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <Space direction="vertical" size="small" style={{ width: '100%' }}>
          <Space>
            <Title level={2} style={{ margin: 0 }}>Arbitrage Dashboard</Title>
            <Button 
              icon={<SyncOutlined spin={refreshing} />} 
              onClick={handleManualRefresh}
              size="small"
              disabled={refreshing}
            >
              Refresh
            </Button>
          </Space>
          <div className="dashboard-subtitle">
            Real-time triangular arbitrage opportunities across multiple exchanges
            {lastUpdate && (
              <span className="dashboard-update-time">
                • Last update: {lastUpdate.toLocaleTimeString()}
              </span>
            )}
          </div>
        </Space>
      </div>

      {error && (
        <Alert
          message="Connection Error"
          description={error}
          type="error"
          showIcon
          closable
          className="dashboard-alert"
        />
      )}

      {using_mock_data && (
        <Alert
          message="Demo Mode Active"
          description="Currently displaying sample data. Connect to live exchanges for real trading."
          type="info"
          showIcon
          closable
          className="dashboard-alert"
        />
      )}

      {/* System Status Overview */}
      <Card size="small" className="dashboard-status-overview">
        <Row gutter={16}>
          <Col span={6}>
            <div className="status-item">
              <Text type="secondary">System Status</Text>
              <div>
                <Text strong style={{ color: system_status === 'running' ? '#52c41a' : '#ff4d4f' }}>
                  {system_status?.toUpperCase() || 'UNKNOWN'}
                </Text>
              </div>
            </div>
          </Col>
          <Col span={6}>
            <div className="status-item">
              <Text type="secondary">Market Symbols</Text>
              <div><Text strong>{market_stats?.total_symbols || 0}</Text></div>
            </div>
          </Col>
          <Col span={6}>
            <div className="status-item">
              <Text type="secondary">Triangles</Text>
              <div><Text strong>{engine_stats?.total_triangles || 0}</Text></div>
            </div>
          </Col>
          <Col span={6}>
            <div className="status-item">
              <Text type="secondary">Profit Threshold</Text>
              <div>
                <Text strong>{engine_stats?.min_profit_threshold || 0.2}%</Text>
              </div>
            </div>
          </Col>
        </Row>
      </Card>

      {/* Key Statistics */}
      <StatsCards stats={stats} loading={loading || refreshing} />

      <Row gutter={[16, 16]} className="dashboard-main-content">
        <Col xs={24} lg={12}>
          <Card 
            title={
              <Space>
                <RocketOutlined className="dashboard-card-icon" />
                Active Opportunities
                {opportunities?.length > 0 && (
                  <span className="opportunity-count-badge">
                    {opportunities.length}
                  </span>
                )}
              </Space>
            }
            loading={loading}
            className="dashboard-opportunities-card"
            extra={
              <Space>
                {refreshing && <DataLoader size="small" text="" />}
                <Button 
                  size="small" 
                  icon={<SyncOutlined />}
                  onClick={handleManualRefresh}
                >
                  Refresh
                </Button>
              </Space>
            }
          >
            <OpportunitiesTable 
              opportunities={opportunities} 
              showAll={false}
              maxRows={8}
            />
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card 
            title={
              <Space>
                <LineChartOutlined className="dashboard-card-icon" />
                Profit History (7 Days)
              </Space>
            }
            loading={loading}
            className="dashboard-chart-card"
          >
            <ProfitChart data={profit_history} />
          </Card>
        </Col>
      </Row>

      {/* Additional Info Cards */}
      <Row gutter={[16, 16]} className="dashboard-info-row">
        <Col xs={24} md={12}>
          <Card 
            title="Recent Activity"
            size="small"
            className="dashboard-activity-card"
          >
            {opportunities?.slice(0, 3).map((opp, index) => (
              <div key={index} className="activity-item">
                <div className="activity-type">
                  <Text strong>Opportunity Found</Text>
                </div>
                <div className="activity-details">
                  <Text type="secondary">{opp.triangle?.join(' → ')}</Text>
                </div>
                <div className="activity-profit">
                  <Text 
                    strong 
                    style={{ color: opp.profit_percentage > 0 ? '#52c41a' : '#ff4d4f' }}
                  >
                    {opp.profit_percentage.toFixed(2)}%
                  </Text>
                </div>
              </div>
            ))}
            {(!opportunities || opportunities.length === 0) && (
              <Text type="secondary">No recent activity</Text>
            )}
          </Card>
        </Col>
        
        <Col xs={24} md={12}>
          <Card 
            title="Exchange Status"
            size="small"
            className="dashboard-exchange-card"
          >
            <div className="exchange-status-item">
              <span className="exchange-name">Binance</span>
              <span className="exchange-status connected">Connected</span>
            </div>
            <div className="exchange-status-item">
              <span className="exchange-name">OKX</span>
              <span className="exchange-status connected">Connected</span>
            </div>
            <div className="exchange-status-item">
              <span className="exchange-name">Market Data</span>
              <span className="exchange-status connected">
                {market_stats?.recent_symbols || 0} symbols
              </span>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;