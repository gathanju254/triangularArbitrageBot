// frontend/src/components/trading/shared/TradingViewer/TradingViewer.jsx
import React, { useState, useEffect } from 'react';
import {
  Card,
  Select,
  Row,
  Col,
  Typography,
  Button,
  Space,
  Tooltip,
  Switch,
  Divider,
  Tag,
  Timeline,
  Statistic,
  Progress,
  Alert
} from 'antd';
import {
  LineChartOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  RocketOutlined,
  SwapOutlined,
  DollarOutlined
} from '@ant-design/icons';
import './TradingViewer.css';

const { Title, Text } = Typography;
const { Option } = Select;

const TradingViewer = () => {
  const [selectedArbitrage, setSelectedArbitrage] = useState('triangular');
  const [isLive, setIsLive] = useState(false);
  const [opportunities, setOpportunities] = useState([]);
  const [activeTrades, setActiveTrades] = useState([]);

  const arbitrageTypes = [
    { value: 'triangular', label: 'Triangular Arbitrage', icon: <SwapOutlined /> },
    { value: 'cross-exchange', label: 'Cross-Exchange', icon: <RocketOutlined /> }
  ];

  const exchanges = ['Binance', 'OKX', 'KuCoin', 'Coinbase', 'Kraken', 'Huobi'];

  // Mock triangular arbitrage opportunities
  const triangularOpportunities = [
    {
      id: 1,
      path: 'BTC → ETH → USDT → BTC',
      profit: 1.25,
      volume: 15000,
      timeframe: '15s',
      exchanges: ['Binance'],
      status: 'high'
    },
    {
      id: 2,
      path: 'ETH → SOL → USDT → ETH',
      profit: 0.89,
      volume: 8500,
      timeframe: '12s',
      exchanges: ['OKX', 'Binance'],
      status: 'medium'
    },
    {
      id: 3,
      path: 'SOL → ADA → USDT → SOL',
      profit: 2.15,
      volume: 3200,
      timeframe: '18s',
      exchanges: ['KuCoin'],
      status: 'high'
    }
  ];

  // Mock cross-exchange opportunities
  const crossExchangeOpportunities = [
    {
      id: 1,
      pair: 'BTC/USDT',
      buyExchange: 'Binance',
      sellExchange: 'OKX',
      priceDiff: 45.50,
      spread: 0.12,
      volume: 25000,
      status: 'high'
    },
    {
      id: 2,
      pair: 'ETH/USDT',
      buyExchange: 'Coinbase',
      sellExchange: 'Kraken',
      priceDiff: 12.30,
      spread: 0.08,
      volume: 18000,
      status: 'medium'
    },
    {
      id: 3,
      pair: 'SOL/USDT',
      buyExchange: 'Huobi',
      sellExchange: 'KuCoin',
      priceDiff: 3.45,
      spread: 0.15,
      volume: 9500,
      status: 'low'
    }
  ];

  useEffect(() => {
    setOpportunities(selectedArbitrage === 'triangular' ? triangularOpportunities : crossExchangeOpportunities);
    
    // Mock active trades
    setActiveTrades([
      {
        id: 1,
        type: 'triangular',
        path: 'BTC → ETH → USDT → BTC',
        profit: 0.75,
        status: 'executing',
        progress: 65,
        exchanges: ['Binance']
      },
      {
        id: 2,
        type: 'cross-exchange',
        pair: 'ETH/USDT',
        action: 'Buy on Coinbase → Sell on Kraken',
        profit: 0.42,
        status: 'completed',
        progress: 100,
        exchanges: ['Coinbase', 'Kraken']
      }
    ]);
  }, [selectedArbitrage]);

  const getProfitColor = (profit) => {
    if (profit > 2) return '#52c41a';
    if (profit > 1) return '#faad14';
    return '#ff4d4f';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'high': return 'green';
      case 'medium': return 'orange';
      case 'low': return 'red';
      default: return 'blue';
    }
  };

  const renderTriangularOpportunity = (opp) => (
    <Card key={opp.id} size="small" className="opportunity-card">
      <Row gutter={[8, 8]} align="middle">
        <Col span={24}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div className="opportunity-header">
              <Text strong>{opp.path}</Text>
              <Tag color={getStatusColor(opp.status)}>
                {opp.profit}% Profit
              </Tag>
            </div>
            
            <div className="opportunity-details">
              <Space size="large">
                <Text type="secondary">Volume: ${opp.volume.toLocaleString()}</Text>
                <Text type="secondary">Cycle: {opp.timeframe}</Text>
              </Space>
            </div>

            <div className="exchange-tags">
              {opp.exchanges.map(exchange => (
                <Tag key={exchange} color="blue" size="small">
                  {exchange}
                </Tag>
              ))}
            </div>

            <Button type="primary" size="small" block>
              Execute Trade
            </Button>
          </Space>
        </Col>
      </Row>
    </Card>
  );

  const renderCrossExchangeOpportunity = (opp) => (
    <Card key={opp.id} size="small" className="opportunity-card">
      <Row gutter={[8, 8]} align="middle">
        <Col span={24}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div className="opportunity-header">
              <Text strong>{opp.pair}</Text>
              <Tag color={getStatusColor(opp.status)}>
                ${opp.priceDiff} Diff
              </Tag>
            </div>
            
            <div className="exchange-flow">
              <Space>
                <Text type="secondary">Buy:</Text>
                <Tag color="green">{opp.buyExchange}</Tag>
                <Text type="secondary">→ Sell:</Text>
                <Tag color="red">{opp.sellExchange}</Tag>
              </Space>
            </div>

            <div className="opportunity-details">
              <Space size="large">
                <Text type="secondary">Spread: {opp.spread}%</Text>
                <Text type="secondary">Volume: ${opp.volume.toLocaleString()}</Text>
              </Space>
            </div>

            <Button type="primary" size="small" block>
              Execute Arbitrage
            </Button>
          </Space>
        </Col>
      </Row>
    </Card>
  );

  return (
    <div className="arbitrage-viewer">
      {/* Header Controls */}
      <Card className="controls-card">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} md={12}>
            <Space size="large">
              <Text strong>Arbitrage Type:</Text>
              <Select
                value={selectedArbitrage}
                onChange={setSelectedArbitrage}
                className="arbitrage-select"
                style={{ width: 200 }}
              >
                {arbitrageTypes.map(type => (
                  <Option key={type.value} value={type.value}>
                    <Space>
                      {type.icon}
                      {type.label}
                    </Space>
                  </Option>
                ))}
              </Select>
            </Space>
          </Col>

          <Col xs={24} md={12}>
            <Space size="middle" className="live-controls">
              <Switch
                checked={isLive}
                onChange={setIsLive}
                checkedChildren="Live"
                unCheckedChildren="Paused"
              />
              <Tooltip title={isLive ? 'Pause scanning' : 'Start live scanning'}>
                <Button
                  type={isLive ? 'primary' : 'default'}
                  icon={isLive ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                  onClick={() => setIsLive(!isLive)}
                >
                  {isLive ? 'Live' : 'Paused'}
                </Button>
              </Tooltip>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Main Content */}
      <Row gutter={[16, 16]}>
        {/* Opportunities Panel */}
        <Col xs={24} lg={16}>
          <Card 
            title={
              <Space>
                <DollarOutlined />
                {selectedArbitrage === 'triangular' ? 'Triangular Arbitrage Opportunities' : 'Cross-Exchange Opportunities'}
              </Space>
            }
            className="opportunities-panel"
          >
            <div className="opportunities-grid">
              {opportunities.map(opp => 
                selectedArbitrage === 'triangular' 
                  ? renderTriangularOpportunity(opp)
                  : renderCrossExchangeOpportunity(opp)
              )}
            </div>

            {opportunities.length === 0 && (
              <div className="no-opportunities">
                <LineChartOutlined className="no-data-icon" />
                <Text type="secondary">No arbitrage opportunities found</Text>
                <Text type="secondary" className="no-data-subtitle">
                  {isLive ? 'Scanning markets...' : 'Start live scanning to find opportunities'}
                </Text>
              </div>
            )}
          </Card>
        </Col>

        {/* Active Trades & Stats */}
        <Col xs={24} lg={8}>
          {/* Active Trades */}
          <Card 
            title="Active Trades" 
            className="active-trades-panel"
          >
            {activeTrades.length > 0 ? (
              <Space direction="vertical" style={{ width: '100%' }}>
                {activeTrades.map(trade => (
                  <Card key={trade.id} size="small" className="active-trade-card">
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <div className="trade-header">
                        <Text strong>
                          {trade.type === 'triangular' ? trade.path : trade.pair}
                        </Text>
                        <Tag color={trade.status === 'completed' ? 'green' : 'blue'}>
                          {trade.status}
                        </Tag>
                      </div>
                      
                      {trade.type === 'cross-exchange' && (
                        <Text type="secondary" className="trade-action">
                          {trade.action}
                        </Text>
                      )}

                      <div className="trade-progress">
                        <Progress 
                          percent={trade.progress} 
                          size="small" 
                          status={trade.status === 'completed' ? 'success' : 'active'}
                        />
                      </div>

                      <div className="trade-profit">
                        <Text strong style={{ color: getProfitColor(trade.profit) }}>
                          +{trade.profit}%
                        </Text>
                        <div className="exchange-tags">
                          {trade.exchanges.map(exchange => (
                            <Tag key={exchange} color="blue" size="small">
                              {exchange}
                            </Tag>
                          ))}
                        </div>
                      </div>
                    </Space>
                  </Card>
                ))}
              </Space>
            ) : (
              <div className="no-active-trades">
                <Text type="secondary">No active trades</Text>
              </div>
            )}
          </Card>

          {/* Quick Stats */}
          <Card 
            title="Quick Stats" 
            className="stats-panel"
            style={{ marginTop: 16 }}
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              <Statistic
                title="Total Opportunities"
                value={opportunities.length}
                prefix={<RocketOutlined />}
              />
              <Statistic
                title="Best Profit"
                value={Math.max(...opportunities.map(o => o.profit))}
                suffix="%"
                valueStyle={{ color: getProfitColor(Math.max(...opportunities.map(o => o.profit))) }}
              />
              <Statistic
                title="Active Trades"
                value={activeTrades.length}
                prefix={<SwapOutlined />}
              />
            </Space>
          </Card>

          {/* Recent Activity */}
          <Card 
            title="Recent Activity" 
            className="activity-panel"
            style={{ marginTop: 16 }}
          >
            <Timeline
              items={[
                {
                  color: 'green',
                  children: (
                    <Space direction="vertical" size={0}>
                      <Text strong>Triangular Arbitrage</Text>
                      <Text type="secondary">BTC → ETH → USDT → BTC completed</Text>
                      <Text type="secondary" className="activity-profit">+1.25% profit</Text>
                    </Space>
                  ),
                },
                {
                  color: 'blue',
                  children: (
                    <Space direction="vertical" size={0}>
                      <Text strong>Cross-Exchange</Text>
                      <Text type="secondary">ETH arbitrage Binance → OKX</Text>
                      <Text type="secondary" className="activity-profit">+0.89% profit</Text>
                    </Space>
                  ),
                },
                {
                  color: 'orange',
                  children: (
                    <Space direction="vertical" size={0}>
                      <Text strong>Opportunity Found</Text>
                      <Text type="secondary">New triangular path detected</Text>
                    </Space>
                  ),
                },
              ]}
            />
          </Card>
        </Col>
      </Row>

      {/* Status Footer */}
      {isLive && (
        <Alert
          message="Live Scanning Active"
          description={`Scanning ${exchanges.length} exchanges for ${selectedArbitrage} arbitrage opportunities`}
          type="info"
          showIcon
          className="status-alert"
        />
      )}
    </div>
  );
};

export default TradingViewer;