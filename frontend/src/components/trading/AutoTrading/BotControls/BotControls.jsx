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
  Tooltip,
  notification,
  Badge
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  RocketOutlined,
  DollarOutlined,
  SafetyOutlined,
  ThunderboltOutlined,
  ArrowsAltOutlined,
  SyncOutlined
} from '@ant-design/icons';
import './BotControls.css';

const BotControls = ({ onStatusChange, initialStatus = 'stopped' }) => {
  const [botStatus, setBotStatus] = useState(initialStatus);
  const [uptime, setUptime] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  // Focused arbitrage statistics
  const [botStats, setBotStats] = useState({
    triangularTrades: 12,
    crossExchangeTrades: 8,
    totalProfit: 1250.75,
    successRate: 78.5,
    activeOpportunities: 3,
    scannedPairs: 45
  });

  const [exchangeStatus, setExchangeStatus] = useState({
    binance: { connected: true, latency: 45 },
    okx: { connected: true, latency: 52 },
    kucoin: { connected: true, latency: 68 },
    coinbase: { connected: true, latency: 38 },
    kraken: { connected: true, latency: 61 },
    huobi: { connected: true, latency: 72 }
  });

  useEffect(() => {
    let interval;
    if (botStatus === 'running') {
      interval = setInterval(() => {
        setUptime(prev => prev + 1);
        // Simulate real-time updates
        updateBotStats();
      }, 3000);
    }
    return () => clearInterval(interval);
  }, [botStatus]);

  const updateBotStats = () => {
    if (botStatus === 'running') {
      setBotStats(prev => ({
        ...prev,
        triangularTrades: prev.triangularTrades + Math.floor(Math.random() * 2),
        crossExchangeTrades: prev.crossExchangeTrades + Math.floor(Math.random()),
        totalProfit: prev.totalProfit + (Math.random() * 10 - 2),
        activeOpportunities: Math.max(0, prev.activeOpportunities + (Math.random() > 0.7 ? 1 : -1)),
        scannedPairs: prev.scannedPairs + Math.floor(Math.random() * 5)
      }));
    }
  };

  const handleStart = async () => {
    setIsLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 800));
      setBotStatus('running');
      onStatusChange?.('running');
      notification.success({
        message: 'Arbitrage Bot Started',
        description: 'Scanning for triangular and cross-exchange arbitrage opportunities.',
        placement: 'bottomRight'
      });
    } catch (error) {
      notification.error({
        message: 'Start Failed',
        description: 'Failed to start the arbitrage bot.',
        placement: 'bottomRight'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handlePause = async () => {
    setIsLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      setBotStatus('paused');
      onStatusChange?.('paused');
      notification.warning({
        message: 'Bot Paused',
        description: 'Arbitrage scanning paused. No new trades will be executed.',
        placement: 'bottomRight'
      });
    } catch (error) {
      notification.error({
        message: 'Pause Failed',
        description: 'Failed to pause the bot.',
        placement: 'bottomRight'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleStop = async () => {
    setIsLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 500));
      setBotStatus('stopped');
      setUptime(0);
      onStatusChange?.('stopped');
      notification.info({
        message: 'Bot Stopped',
        description: 'Arbitrage bot stopped and all positions closed.',
        placement: 'bottomRight'
      });
    } catch (error) {
      notification.error({
        message: 'Stop Failed',
        description: 'Failed to stop the bot.',
        placement: 'bottomRight'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const formatUptime = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusConfig = (status) => {
    const configs = {
      running: { 
        color: 'green', 
        text: 'Running', 
        icon: <PlayCircleOutlined />,
        badge: 'processing'
      },
      paused: { 
        color: 'orange', 
        text: 'Paused', 
        icon: <PauseCircleOutlined />,
        badge: 'warning'
      },
      stopped: { 
        color: 'red', 
        text: 'Stopped', 
        icon: <StopOutlined />,
        badge: 'default'
      }
    };
    return configs[status] || configs.stopped;
  };

  const getLatencyColor = (latency) => {
    if (latency < 50) return 'green';
    if (latency < 100) return 'orange';
    return 'red';
  };

  const statusConfig = getStatusConfig(botStatus);

  return (
    <div className="bot-controls">
      <Card 
        title={
          <Space>
            <RocketOutlined className="bot-icon" />
            <span>Arbitrage Bot Controller</span>
            <Badge status={statusConfig.badge} text={statusConfig.text} />
          </Space>
        }
        className="bot-controls-card"
        loading={isLoading}
        extra={
          <Tag color={statusConfig.color} icon={statusConfig.icon}>
            {statusConfig.text}
          </Tag>
        }
      >
        {/* Status Alert */}
        {botStatus === 'running' && (
          <Alert
            message="Active Arbitrage Scanning"
            description={
              <Space direction="vertical" size="small">
                <div>• Triangular arbitrage: BTC → ETH → USDT → BTC</div>
                <div>• Cross-exchange: Buy low on one exchange, sell high on another</div>
                <div>• Monitoring 6 exchanges with real-time price data</div>
              </Space>
            }
            type="success"
            showIcon
            className="bot-status-alert"
          />
        )}

        {/* Control Buttons */}
        <div className="control-buttons-section">
          <Space size="middle" wrap style={{ justifyContent: 'center', width: '100%' }}>
            <Tooltip title="Start arbitrage scanning">
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={handleStart}
                disabled={botStatus === 'running' || isLoading}
                className="start-button"
                size="large"
              >
                Start Bot
              </Button>
            </Tooltip>
            
            <Tooltip title="Pause trading (keep scanning)">
              <Button
                icon={<PauseCircleOutlined />}
                onClick={handlePause}
                disabled={botStatus !== 'running' || isLoading}
                className="pause-button"
                size="large"
              >
                Pause
              </Button>
            </Tooltip>
            
            <Tooltip title="Stop completely">
              <Button
                danger
                icon={<StopOutlined />}
                onClick={handleStop}
                disabled={botStatus === 'stopped' || isLoading}
                className="stop-button"
                size="large"
              >
                Stop
              </Button>
            </Tooltip>
          </Space>
        </div>

        {/* Arbitrage Statistics */}
        <div className="stats-section">
          <div className="section-header">
            <ThunderboltOutlined />
            <span>Arbitrage Performance</span>
          </div>
          <Row gutter={[16, 16]} className="bot-stats">
            <Col xs={12} sm={8}>
              <Statistic
                title="Uptime"
                value={formatUptime(uptime)}
                valueStyle={{ 
                  color: botStatus === 'running' ? '#52c41a' : '#8c8c8c',
                  fontFamily: 'monospace',
                  fontSize: '14px'
                }}
              />
            </Col>
            <Col xs={12} sm={8}>
              <Statistic
                title="Triangular Trades"
                value={botStats.triangularTrades}
                prefix={<SyncOutlined />}
                valueStyle={{ color: '#1890ff', fontSize: '16px' }}
              />
            </Col>
            <Col xs={12} sm={8}>
              <Statistic
                title="Cross-Exchange"
                value={botStats.crossExchangeTrades}
                prefix={<ArrowsAltOutlined />}
                valueStyle={{ color: '#722ed1', fontSize: '16px' }}
              />
            </Col>
            <Col xs={12} sm={8}>
              <Statistic
                title="Success Rate"
                value={botStats.successRate}
                suffix="%"
                valueStyle={{ 
                  color: botStats.successRate >= 70 ? '#52c41a' : '#faad14',
                  fontSize: '16px'
                }}
                precision={1}
              />
            </Col>
            <Col xs={12} sm={8}>
              <Statistic
                title="Total Profit"
                value={botStats.totalProfit}
                prefix="$"
                valueStyle={{ 
                  color: botStats.totalProfit >= 0 ? '#52c41a' : '#ff4d4f',
                  fontSize: '16px'
                }}
                precision={2}
              />
            </Col>
            <Col xs={12} sm={8}>
              <Statistic
                title="Active Opportunities"
                value={botStats.activeOpportunities}
                valueStyle={{ color: '#fa8c16', fontSize: '16px' }}
              />
            </Col>
          </Row>
        </div>

        {/* Exchange Status */}
        <div className="status-section">
          <div className="section-header">
            <SafetyOutlined />
            <span>Exchange Connections</span>
          </div>
          <div className="exchange-status-grid">
            {Object.entries(exchangeStatus).map(([exchange, data]) => (
              <Tooltip 
                key={exchange} 
                title={`${exchange.toUpperCase()} - ${data.latency}ms latency`}
              >
                <div className="exchange-item">
                  <span className="exchange-name">{exchange.toUpperCase()}</span>
                  <div className="exchange-indicator">
                    <div 
                      className={`status-dot ${data.connected ? 'connected' : 'disconnected'}`}
                    />
                    <span className="latency" style={{ color: getLatencyColor(data.latency) }}>
                      {data.latency}ms
                    </span>
                  </div>
                </div>
              </Tooltip>
            ))}
          </div>
        </div>

        {/* Quick Stats Bar */}
        <div className="quick-stats-bar">
          <Space size="large" split={<div className="stat-divider">|</div>}>
            <span className="quick-stat">
              <strong>{botStats.scannedPairs}</strong> pairs scanned
            </span>
            <span className="quick-stat">
              <strong>{Object.values(exchangeStatus).filter(e => e.connected).length}</strong> exchanges active
            </span>
            <span className="quick-stat">
              <strong>{botStats.activeOpportunities}</strong> opportunities
            </span>
          </Space>
        </div>
      </Card>
    </div>
  );
};

export default BotControls;