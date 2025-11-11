// frontend/src/pages/Trading/Trading.jsx
import React, { useState } from 'react';
import {
  Card,
  Typography,
  Tabs,
  Row,
  Col,
  Space,
  Alert,
  Switch,
  Tag,
  Statistic
} from 'antd';
import {
  RocketOutlined,
  SettingOutlined,
  BarChartOutlined,
  DollarOutlined,
  SafetyCertificateOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined
} from '@ant-design/icons';

// Import trading components
import ManualTrading from '../../components/trading/ManualTrading/ManualTrading';
import StrategyConfig from '../../components/trading/AutoTrading/StrategyConfig/StrategyConfig';
import BotControls from '../../components/trading/AutoTrading/BotControls/BotControls';
import PerformanceMetrics from '../../components/trading/AutoTrading/PerformanceMetrics/PerformanceMetrics';
import TradingViewer from '../../components/trading/shared/TradingViewer/TradingViewer';
import MarketData from '../../components/trading/shared/MarketData/MarketData';

import './Trading.css';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

const Trading = () => {
  const [activeTab, setActiveTab] = useState('manual');
  const [autoTradingEnabled, setAutoTradingEnabled] = useState(false);
  const [tradingStatus, setTradingStatus] = useState('stopped');

  // Mock data for demonstration
  const tradingStats = {
    totalTrades: 45,
    successRate: 78.5,
    currentProfit: 1250.75,
    activePositions: 3
  };

  const handleAutoTradingToggle = (checked) => {
    setAutoTradingEnabled(checked);
    setTradingStatus(checked ? 'running' : 'stopped');
  };

  const handleBotStatusChange = (status) => {
    setTradingStatus(status);
    setAutoTradingEnabled(status === 'running');
  };

  const renderTradingStatus = () => {
    const statusConfig = {
      running: { color: 'green', text: 'Running', icon: <PlayCircleOutlined /> },
      stopped: { color: 'red', text: 'Stopped', icon: <PauseCircleOutlined /> },
      paused: { color: 'orange', text: 'Paused', icon: <PauseCircleOutlined /> }
    };

    const config = statusConfig[tradingStatus] || statusConfig.stopped;

    return (
      <Tag 
        color={config.color} 
        icon={config.icon}
        style={{ fontSize: '12px', padding: '4px 8px' }}
      >
        {config.text}
      </Tag>
    );
  };

  return (
    <div className="trading-page">
      {/* Header Section */}
      <div className="trading-header">
        <div className="trading-header-content">
          <Title level={2}>Trading Dashboard</Title>
          <div className="trading-subtitle">
            Manage manual and automated trading strategies
          </div>
        </div>
        <div className="trading-controls">
          <Space size="middle">
            <div className="trading-status">
              <Text strong>Auto Trading:</Text>
              <Switch
                checked={autoTradingEnabled}
                onChange={handleAutoTradingToggle}
                checkedChildren="ON"
                unCheckedChildren="OFF"
              />
              {renderTradingStatus()}
            </div>
          </Space>
        </div>
      </div>

      {/* Trading Statistics */}
      <Row gutter={[16, 16]} className="trading-stats-row">
        <Col xs={24} sm={12} lg={6}>
          <Card className="trading-stat-card">
            <Statistic
              title="Total Trades"
              value={tradingStats.totalTrades}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="trading-stat-card">
            <Statistic
              title="Success Rate"
              value={tradingStats.successRate}
              suffix="%"
              prefix={<SafetyCertificateOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="trading-stat-card">
            <Statistic
              title="Current Profit"
              value={tradingStats.currentProfit}
              prefix={<DollarOutlined />}
              precision={2}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card className="trading-stat-card">
            <Statistic
              title="Active Positions"
              value={tradingStats.activePositions}
              prefix={<RocketOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Auto Trading Alert */}
      {autoTradingEnabled && (
        <Alert
          message="Auto Trading Active"
          description="Automated trading strategies are currently running. Monitor performance and be ready to intervene if needed."
          type="info"
          showIcon
          closable
          className="trading-alert"
        />
      )}

      {/* Main Trading Interface */}
      <Card className="trading-main-card">
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          type="card"
          className="trading-tabs"
        >
          {/* Manual Trading Tab */}
          <TabPane
            tab={
              <span>
                <SettingOutlined />
                Manual Trading
              </span>
            }
            key="manual"
          >
            <div className="trading-tab-content">
              {/* Manual Trading takes full width */}
              <ManualTrading />
            </div>
          </TabPane>

          {/* Auto Trading Tab */}
          <TabPane
            tab={
              <span>
                <RocketOutlined />
                Auto Trading
              </span>
            }
            key="auto"
          >
            <div className="trading-tab-content auto-trading-content">
              {/* Bot Controls - Full Width */}
              <div className="bot-controls-fullwidth">
                <BotControls 
                  onStatusChange={handleBotStatusChange}
                  initialStatus={tradingStatus}
                />
              </div>

              {/* Strategy Configuration - Full Width */}
              <div className="strategy-config-fullwidth" style={{ marginTop: 24 }}>
                <Card 
                  title="Strategy Configuration" 
                  className="strategy-config-card"
                >
                  <StrategyConfig />
                </Card>
              </div>
              
              {/* Performance Metrics - Full Width */}
              <div style={{ marginTop: 24 }}>
                <Card 
                  title="Performance Metrics" 
                  className="performance-metrics-card"
                >
                  <PerformanceMetrics />
                </Card>
              </div>
            </div>
          </TabPane>

          {/* Trading Charts Tab */}
          <TabPane
            tab={
              <span>
                <BarChartOutlined />
                Charts & Analysis
              </span>
            }
            key="charts"
          >
            <div className="trading-tab-content">
              <Card 
                title="Advanced Charting" 
                className="charting-card"
              >
                <TradingViewer />
              </Card>
            </div>
          </TabPane>

          {/* Market Analysis Tab */}
          <TabPane
            tab={
              <span>
                <BarChartOutlined />
                Market Overview
              </span>
            }
            key="market"
          >
            <div className="trading-tab-content">
              <Card 
                title="Comprehensive Market Data" 
                className="market-overview-card"
              >
                <MarketData />
              </Card>
            </div>
          </TabPane>
        </Tabs>
      </Card>

      {/* Quick Actions Panel */}
      <Card 
        title="Quick Actions" 
        className="quick-actions-card"
        style={{ marginTop: 24 }}
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8}>
            <Card 
              size="small" 
              className="action-card"
              hoverable
              onClick={() => setActiveTab('manual')}
            >
              <div className="action-content">
                <DollarOutlined className="action-icon" />
                <div className="action-text">
                  <Text strong>Place Order</Text>
                  <Text type="secondary" className="action-description">
                    Quick trade execution
                  </Text>
                </div>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card 
              size="small" 
              className="action-card"
              hoverable
              onClick={() => setActiveTab('auto')}
            >
              <div className="action-content">
                <RocketOutlined className="action-icon" />
                <div className="action-text">
                  <Text strong>Bot Controls</Text>
                  <Text type="secondary" className="action-description">
                    Manage auto trading
                  </Text>
                </div>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={8}>
            <Card 
              size="small" 
              className="action-card"
              hoverable
              onClick={() => setActiveTab('charts')}
            >
              <div className="action-content">
                <BarChartOutlined className="action-icon" />
                <div className="action-text">
                  <Text strong>View Charts</Text>
                  <Text type="secondary" className="action-description">
                    Technical analysis
                  </Text>
                </div>
              </div>
            </Card>
          </Col>
        </Row>
      </Card>

      {/* Status Summary */}
      <Card 
        title="Trading Status Summary" 
        className="status-summary-card"
        style={{ marginTop: 24 }}
      >
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <div className="status-item">
              <div className="status-label">Manual Trading</div>
              <Tag color="green">Available</Tag>
            </div>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <div className="status-item">
              <div className="status-label">Auto Trading</div>
              <Tag color={autoTradingEnabled ? 'green' : 'red'}>
                {autoTradingEnabled ? 'Active' : 'Inactive'}
              </Tag>
            </div>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <div className="status-item">
              <div className="status-label">API Connections</div>
              <Tag color="green">3/3 Connected</Tag>
            </div>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <div className="status-item">
              <div className="status-label">Market Data</div>
              <Tag color="green">Live</Tag>
            </div>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default Trading;