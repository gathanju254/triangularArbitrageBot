// frontend/src/components/trading/AutoTrading/PerformanceMetrics/PerformanceMetrics.jsx
import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Select,
  Space,
  Tooltip,
  Progress
} from 'antd';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import {
  RiseOutlined,
  FallOutlined,
  DollarOutlined,
  TrophyOutlined,
  SafetyOutlined,
  SwapOutlined,
  RocketOutlined
} from '@ant-design/icons';
import './PerformanceMetrics.css';

const { Option } = Select;

const PerformanceMetrics = () => {
  const [timeRange, setTimeRange] = useState('24h');
  const [performanceData, setPerformanceData] = useState({});

  // Mock performance data focused on arbitrage
  useEffect(() => {
    const mockData = {
      summary: {
        totalProfit: 1250.75,
        totalTrades: 45,
        successRate: 78.5,
        sharpeRatio: 1.8,
        avgProfitPerTrade: 27.8,
        activeOpportunities: 3
      },
      hourlyPerformance: Array.from({ length: 24 }, (_, i) => ({
        hour: `${i}:00`,
        profit: Math.random() * 100 - 20,
        trades: Math.floor(Math.random() * 5) + 1
      })),
      exchangePerformance: [
        { exchange: 'Binance', profit: 650, trades: 18, successRate: 82 },
        { exchange: 'OKX', profit: 320, trades: 12, successRate: 75 },
        { exchange: 'Kraken', profit: 180, trades: 8, successRate: 70 },
        { exchange: 'Coinbase', profit: 100, trades: 7, successRate: 68 }
      ],
      strategyPerformance: [
        { strategy: 'Triangular Arbitrage', profit: 850, trades: 25, successRate: 85 },
        { strategy: 'Cross-Exchange', profit: 400, trades: 20, successRate: 72 }
      ],
      recentTrades: [
        { 
          id: 1, 
          type: 'Triangular', 
          path: 'BTC → ETH → USDT → BTC',
          profit: 45.23, 
          timestamp: '2024-01-15 14:30:00', 
          status: 'success',
          exchanges: ['Binance', 'OKX']
        },
        { 
          id: 2, 
          type: 'Cross-Exchange', 
          path: 'BTC/USDT',
          profit: 32.50, 
          timestamp: '2024-01-15 13:15:00', 
          status: 'success',
          exchanges: ['Binance', 'Kraken']
        },
        { 
          id: 3, 
          type: 'Triangular', 
          path: 'ETH → SOL → USDT → ETH',
          profit: 78.91, 
          timestamp: '2024-01-15 12:00:00', 
          status: 'success',
          exchanges: ['OKX', 'Coinbase']
        },
        { 
          id: 4, 
          type: 'Cross-Exchange', 
          path: 'SOL/USDT',
          profit: -12.45, 
          timestamp: '2024-01-15 11:30:00', 
          status: 'failed',
          exchanges: ['Kraken', 'Binance']
        }
      ]
    };
    setPerformanceData(mockData);
  }, [timeRange]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  };

  const formatPercentage = (value) => {
    return `${value.toFixed(1)}%`;
  };

  const summaryMetrics = [
    {
      key: 'totalProfit',
      title: 'Total Profit',
      value: performanceData.summary?.totalProfit || 0,
      formatter: formatCurrency,
      icon: <DollarOutlined />,
      color: '#52c41a',
      description: 'Cumulative profit from arbitrage trades'
    },
    {
      key: 'successRate',
      title: 'Success Rate',
      value: performanceData.summary?.successRate || 0,
      formatter: formatPercentage,
      icon: <TrophyOutlined />,
      color: '#1890ff',
      description: 'Percentage of profitable trades'
    },
    {
      key: 'avgProfitPerTrade',
      title: 'Avg Profit/Trade',
      value: performanceData.summary?.avgProfitPerTrade || 0,
      formatter: formatCurrency,
      icon: <SwapOutlined />,
      color: '#faad14',
      description: 'Average profit per executed trade'
    },
    {
      key: 'activeOpportunities',
      title: 'Active Opportunities',
      value: performanceData.summary?.activeOpportunities || 0,
      formatter: (value) => value,
      icon: <RocketOutlined />,
      color: '#722ed1',
      description: 'Current arbitrage opportunities'
    }
  ];

  const tradeColumns = [
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      width: 120,
      render: (type) => (
        <Tag color={type === 'Triangular' ? 'blue' : 'purple'}>
          {type}
        </Tag>
      )
    },
    {
      title: 'Trade Path',
      dataIndex: 'path',
      key: 'path',
      render: (path) => (
        <Tooltip title={path}>
          <span className="trade-path">{path}</span>
        </Tooltip>
      )
    },
    {
      title: 'Exchanges',
      dataIndex: 'exchanges',
      key: 'exchanges',
      render: (exchanges) => (
        <Space size={4}>
          {exchanges.map((exchange, index) => (
            <Tag key={index} color="cyan" size="small">
              {exchange}
            </Tag>
          ))}
        </Space>
      )
    },
    {
      title: 'Profit/Loss',
      dataIndex: 'profit',
      key: 'profit',
      width: 100,
      render: (profit) => (
        <span className={profit >= 0 ? 'profit-positive' : 'profit-negative'}>
          {formatCurrency(profit)}
        </span>
      )
    },
    {
      title: 'Time',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 120,
      render: (text) => new Date(text).toLocaleTimeString()
    }
  ];

  const exchangeColors = ['#1890ff', '#52c41a', '#faad14', '#722ed1', '#ff4d4f'];
  const strategyColors = ['#1890ff', '#52c41a'];

  return (
    <div className="performance-metrics">
      {/* Time Range Selector */}
      <div className="metrics-header">
        <Space size="middle">
          <span className="time-range-label">Time Range:</span>
          <Select value={timeRange} onChange={setTimeRange} size="small">
            <Option value="1h">1 Hour</Option>
            <Option value="24h">24 Hours</Option>
            <Option value="7d">7 Days</Option>
            <Option value="30d">30 Days</Option>
          </Select>
        </Space>
      </div>

      {/* Summary Metrics */}
      <Row gutter={[16, 16]} className="summary-metrics">
        {summaryMetrics.map(metric => (
          <Col xs={24} sm={12} lg={6} key={metric.key}>
            <Card className="metric-card" size="small">
              <div className="metric-content">
                <div className="metric-icon" style={{ color: metric.color }}>
                  {metric.icon}
                </div>
                <div className="metric-info">
                  <div className="metric-title">{metric.title}</div>
                  <div className="metric-value" style={{ color: metric.color }}>
                    {metric.formatter(metric.value)}
                  </div>
                  <div className="metric-description">
                    {metric.description}
                  </div>
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      {/* Charts Section */}
      <Row gutter={[16, 16]} className="charts-section">
        <Col xs={24} lg={12}>
          <Card 
            title="Profit Trend (Last 24h)" 
            className="chart-card"
            size="small"
          >
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={performanceData.hourlyPerformance}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="hour" />
                  <YAxis />
                  <RechartsTooltip 
                    formatter={(value) => [formatCurrency(value), 'Profit']}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="profit" 
                    stroke="#1890ff" 
                    fill="#1890ff" 
                    fillOpacity={0.3}
                    name="Hourly Profit"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} lg={12}>
          <Card 
            title="Exchange Performance" 
            className="chart-card"
            size="small"
          >
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={performanceData.exchangePerformance}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="exchange" />
                  <YAxis />
                  <RechartsTooltip formatter={(value) => formatCurrency(value)} />
                  <Bar 
                    dataKey="profit" 
                    name="Profit" 
                    fill="#52c41a"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Strategy Performance */}
      <Card 
        title="Strategy Performance" 
        className="strategy-card"
        size="small"
      >
        <Row gutter={[16, 16]}>
          {performanceData.strategyPerformance?.map((strategy, index) => (
            <Col xs={24} md={12} key={strategy.strategy}>
              <div className="strategy-item">
                <div className="strategy-header">
                  <span className="strategy-name">{strategy.strategy}</span>
                  <span className="strategy-profit" style={{ color: strategyColors[index] }}>
                    {formatCurrency(strategy.profit)}
                  </span>
                </div>
                <div className="strategy-details">
                  <span>Trades: {strategy.trades}</span>
                  <span>Success: {strategy.successRate}%</span>
                </div>
                <Progress 
                  percent={strategy.successRate} 
                  size="small" 
                  strokeColor={strategyColors[index]}
                  showInfo={false}
                />
              </div>
            </Col>
          ))}
        </Row>
      </Card>

      {/* Recent Trades */}
      <Card 
        title="Recent Arbitrage Trades" 
        className="trades-card"
        size="small"
      >
        <Table
          dataSource={performanceData.recentTrades}
          columns={tradeColumns}
          pagination={false}
          size="small"
          scroll={{ y: 200 }}
          rowKey="id"
          className="trades-table"
        />
      </Card>

      {/* Quick Stats */}
      <Card 
        title="Performance Summary" 
        className="stats-card"
        size="small"
      >
        <Row gutter={[16, 16]}>
          <Col xs={12} sm={6}>
            <Statistic
              title="Best Exchange"
              value="Binance"
              prefix={<RiseOutlined />}
              valueStyle={{ color: '#52c41a', fontSize: '14px' }}
            />
          </Col>
          <Col xs={12} sm={6}>
            <Statistic
              title="Most Profitable"
              value="Triangular"
              valueStyle={{ color: '#1890ff', fontSize: '14px' }}
            />
          </Col>
          <Col xs={12} sm={6}>
            <Statistic
              title="Avg Execution Time"
              value="1.2s"
              valueStyle={{ color: '#faad14', fontSize: '14px' }}
            />
          </Col>
          <Col xs={12} sm={6}>
            <Statistic
              title="Active Bots"
              value={performanceData.summary?.activeOpportunities || 0}
              valueStyle={{ color: '#722ed1', fontSize: '14px' }}
            />
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default PerformanceMetrics;