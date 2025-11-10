// frontend/src/components/trading/AutoTrading/BotControls/BotControls.jsx
import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Space,
  Statistic,
  Row,
  Col,
  Tag,
  Alert,
  Progress,
  Switch,
  Tooltip,
  Modal
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  SettingOutlined,
  RocketOutlined,
  DollarOutlined,
  SafetyOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import './BotControls.css';

const BotControls = ({ onStatusChange, initialStatus = 'stopped' }) => {
  const [botStatus, setBotStatus] = useState(initialStatus);
  const [uptime, setUptime] = useState(0);
  const [isEmergencyModalVisible, setIsEmergencyModalVisible] = useState(false);

  // Mock bot statistics
  const [botStats, setBotStats] = useState({
    tradesExecuted: 0,
    currentProfit: 0,
    successRate: 0,
    activeStrategies: 0
  });

  useEffect(() => {
    let interval;
    if (botStatus === 'running') {
      interval = setInterval(() => {
        setUptime(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [botStatus]);

  const handleStart = () => {
    setBotStatus('running');
    onStatusChange?.('running');
  };

  const handlePause = () => {
    setBotStatus('paused');
    onStatusChange?.('paused');
  };

  const handleStop = () => {
    setIsEmergencyModalVisible(true);
  };

  const confirmStop = () => {
    setBotStatus('stopped');
    setUptime(0);
    onStatusChange?.('stopped');
    setIsEmergencyModalVisible(false);
  };

  const formatUptime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusConfig = (status) => {
    const configs = {
      running: { color: 'green', text: 'Running', icon: <PlayCircleOutlined /> },
      paused: { color: 'orange', text: 'Paused', icon: <PauseCircleOutlined /> },
      stopped: { color: 'red', text: 'Stopped', icon: <StopOutlined /> }
    };
    return configs[status] || configs.stopped;
  };

  const statusConfig = getStatusConfig(botStatus);

  return (
    <div className="bot-controls">
      <Card 
        title={
          <Space>
            <RocketOutlined />
            Bot Controls
            <Tag color={statusConfig.color} icon={statusConfig.icon}>
              {statusConfig.text}
            </Tag>
          </Space>
        }
        className="bot-controls-card"
        extra={
          <Tooltip title="Bot Settings">
            <Button type="text" icon={<SettingOutlined />} />
          </Tooltip>
        }
      >
        {/* Status Alert */}
        {botStatus === 'running' && (
          <Alert
            message="Bot is actively trading"
            description="Monitor performance and be prepared to intervene if necessary."
            type="success"
            showIcon
            closable
            className="bot-status-alert"
          />
        )}

        {botStatus === 'paused' && (
          <Alert
            message="Trading is paused"
            description="No new trades will be executed until resumed."
            type="warning"
            showIcon
            closable
            className="bot-status-alert"
          />
        )}

        {/* Control Buttons */}
        <div className="control-buttons">
          <Space size="middle">
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={handleStart}
              disabled={botStatus === 'running'}
              className="start-button"
            >
              Start
            </Button>
            <Button
              icon={<PauseCircleOutlined />}
              onClick={handlePause}
              disabled={botStatus !== 'running'}
              className="pause-button"
            >
              Pause
            </Button>
            <Button
              danger
              icon={<StopOutlined />}
              onClick={handleStop}
              disabled={botStatus === 'stopped'}
              className="stop-button"
            >
              Emergency Stop
            </Button>
          </Space>
        </div>

        {/* Bot Statistics */}
        <Row gutter={[16, 16]} className="bot-stats">
          <Col xs={12} sm={6}>
            <Statistic
              title="Uptime"
              value={formatUptime(uptime)}
              prefix={<InfoCircleOutlined />}
              className="bot-stat"
            />
          </Col>
          <Col xs={12} sm={6}>
            <Statistic
              title="Trades Executed"
              value={botStats.tradesExecuted}
              prefix={<DollarOutlined />}
              className="bot-stat"
            />
          </Col>
          <Col xs={12} sm={6}>
            <Statistic
              title="Success Rate"
              value={botStats.successRate}
              suffix="%"
              prefix={<SafetyOutlined />}
              className="bot-stat"
            />
          </Col>
          <Col xs={12} sm={6}>
            <Statistic
              title="Active Strategies"
              value={botStats.activeStrategies}
              prefix={<RocketOutlined />}
              className="bot-stat"
            />
          </Col>
        </Row>

        {/* Performance Progress */}
        <div className="performance-section">
          <div className="performance-header">
            <span>Performance Metrics</span>
            <Tag color="blue">Live</Tag>
          </div>
          <div className="progress-bars">
            <div className="progress-item">
              <span>Strategy Efficiency</span>
              <Progress percent={75} size="small" status="active" />
            </div>
            <div className="progress-item">
              <span>Risk Management</span>
              <Progress percent={90} size="small" status="active" />
            </div>
            <div className="progress-item">
              <span>Market Adaptation</span>
              <Progress percent={60} size="small" status="active" />
            </div>
          </div>
        </div>

        {/* Quick Settings */}
        <div className="quick-settings">
          <div className="settings-header">
            <span>Quick Settings</span>
          </div>
          <Row gutter={[16, 16]}>
            <Col span={12}>
              <div className="setting-item">
                <span>Auto Restart</span>
                <Switch size="small" defaultChecked />
              </div>
            </Col>
            <Col span={12}>
              <div className="setting-item">
                <span>Risk Limits</span>
                <Switch size="small" defaultChecked />
              </div>
            </Col>
            <Col span={12}>
              <div className="setting-item">
                <span>Email Alerts</span>
                <Switch size="small" defaultChecked />
              </div>
            </Col>
            <Col span={12}>
              <div className="setting-item">
                <span>API Monitoring</span>
                <Switch size="small" defaultChecked />
              </div>
            </Col>
          </Row>
        </div>
      </Card>

      {/* Emergency Stop Modal */}
      <Modal
        title="Emergency Stop Confirmation"
        open={isEmergencyModalVisible}
        onOk={confirmStop}
        onCancel={() => setIsEmergencyModalVisible(false)}
        okText="Stop Bot"
        cancelText="Cancel"
        okType="danger"
      >
        <Alert
          message="Warning: Emergency Stop"
          description="This will immediately stop all trading activities and close any open positions. This action cannot be undone."
          type="error"
          showIcon
        />
        <div style={{ marginTop: 16 }}>
          <p><strong>Are you sure you want to stop the trading bot?</strong></p>
          <ul>
            <li>All active strategies will be terminated</li>
            <li>Open positions may be closed at market prices</li>
            <li>Bot statistics will be reset</li>
          </ul>
        </div>
      </Modal>
    </div>
  );
};

export default BotControls;