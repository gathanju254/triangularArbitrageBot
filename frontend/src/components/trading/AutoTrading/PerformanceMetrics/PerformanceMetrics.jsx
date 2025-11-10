// frontend/src/components/trading/AutoTrading/PerformanceMetrics/PerformanceMetrics.jsx
import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Table,
  Tag,
  Select,
  DatePicker,
  Space,
  Tooltip
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
  BarChartOutlined,
  CalendarOutlined
} from '@ant-design/icons';
import './PerformanceMetrics.css';

const { Option } = Select;
const { RangePicker } = DatePicker;

const PerformanceMetrics = () => {
  const [timeRange, setTimeRange] = useState('7d');
  const [performanceData, setPerformanceData] = useState({});

  // Mock performance data
  useEffect(() => {
    const mockData = {
      summary: {
        totalProfit: 1250.75,
        totalTrades: 45,
        winRate: 78.5,
        sharpeRatio: 1.8,
        maxDrawdown: 8.2,
        profitFactor: 2.1
      },
      dailyPerformance: Array.from({ length: 30 }, (_, i) => ({
        date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
        profit: Math.random() * 200 - 50,
        trades: Math.floor(Math.random() * 10) + 1
      })),
      strategyPerformance: [
        { name: 'Arbitrage', profit: 850, trades: 25, successRate: 85 },
        { name: 'Mean Reversion', profit: 320, trades: 12, successRate: 72 },
        { name: 'Momentum', profit: 180, trades: 8, successRate: 65 }
      ],
      recentTrades: [
        { id: 1, pair: 'BTC/USDT', profit: 45.23, timestamp: '2024-01-15 14:30:00', status: 'win' },
        { id: 2, pair: 'ETH/USDT', profit: -12.50, timestamp: '2024-01-15 13:15:00', status: 'loss' },
        { id: 3, pair: 'SOL/USDT', profit: 78.91, timestamp: '2024-01-15 12:00:00', status: 'win' },
        { id: 4, pair: 'ADA/USDT', profit: 23.45, timestamp: '2024-01-15 11:30:00', status: 'win' }
      ]
    };
    setPerformanceData(mockData);
  }, [timeRange]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
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
      color: '#52c41a'
    },
    {
      key: 'winRate',
      title: 'Win Rate',
      value: performanceData.summary?.winRate || 0,
      formatter: formatPercentage,
      icon: <TrophyOutlined />,
      color: '#1890ff'
    },
    {
      key: 'sharpeRatio',
      title: 'Sharpe Ratio',
      value: performanceData.summary?.sharpeRatio || 0,
      formatter: (value) => value.toFixed(2),
      icon: <BarChartOutlined />,
      color: '#faad14'
    },
    {
      key: 'maxDrawdown',
      title: 'Max Drawdown',
      value: performanceData.summary?.maxDrawdown || 0,
      formatter: formatPercentage,
      icon: <SafetyOutlined />,
      color: '#ff4d4f'
    }
  ];

  const tradeColumns = [
    {
      title: 'Trade Pair',
      dataIndex: 'pair',
      key: 'pair',
      render: (text) => <strong>{text}</strong>
    },
    {
      title: 'Profit/Loss',
      dataIndex: 'profit',
      key: 'profit',
      render: (profit) => (
        <span className={profit >= 0 ? 'profit-positive' : 'profit-negative'}>
          {formatCurrency(profit)}
        </span>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={status === 'win' ? 'green' : 'red'}>
          {status.toUpperCase()}
        </Tag>
      )
    },
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (text) => new Date(text).toLocaleString()
    }
  ];

  const strategyColors = ['#1890ff', '#52c41a', '#faad14', '#722ed1'];

  return (
    <div className="performance-metrics">
      {/* Controls */}
      <Card className="metrics-controls-card">
        <div className="metrics-controls">
          <Space size="middle">
            <span>Time Range:</span>
            <Select value={timeRange} onChange={setTimeRange} style={{ width: 120 }}>
              <Option value="24h">24 Hours</Option>
              <Option value="7d">7 Days</Option>
              <Option value="30d">30 Days</Option>
              <Option value="90d">90 Days</Option>
            </Select>
            <RangePicker />
          </Space>
        </div>
      </Card>

      {/* Summary Metrics */}
      <Row gutter={[16, 16]} className="summary-metrics">
        {summaryMetrics.map(metric => (
          <Col xs={24} sm={12} lg={6} key={metric.key}>
            <Card className="metric-card">
              <div className="metric-content">
                <div className="metric-icon" style={{ color: metric.color }}>
                  {metric.icon}
                </div>
                <div className="metric-info">
                  <div className="metric-title">{metric.title}</div>
                  <div className="metric-value" style={{ color: metric.color }}>
                    {metric.formatter(metric.value)}
                  </div>
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      {/* Charts Section */}
      <Row gutter={[16, 16]} className="charts-section">
        <Col xs={24} lg={16}>
          <Card title="Profit & Loss Trend" className="chart-card">
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={performanceData.dailyPerformance}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <RechartsTooltip 
                    formatter={(value) => [formatCurrency(value), 'Profit']}
                  />
                  <Legend />
                  <Area 
                    type="monotone" 
                    dataKey="profit" 
                    stroke="#1890ff" 
                    fill="#1890ff" 
                    fillOpacity={0.3}
                    name="Daily Profit"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="Strategy Distribution" className="chart-card">
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={performanceData.strategyPerformance}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="profit"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {performanceData.strategyPerformance?.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={strategyColors[index % strategyColors.length]} />
                    ))}
                  </Pie>
                  <RechartsTooltip formatter={(value) => formatCurrency(value)} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Additional Metrics */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="Strategy Performance" className="metrics-card">
            <div className="strategy-performance">
              {performanceData.strategyPerformance?.map((strategy, index) => (
                <div key={strategy.name} className="strategy-item">
                  <div className="strategy-header">
                    <span className="strategy-name">{strategy.name}</span>
                    <Tag color={strategyColors[index]}>{formatCurrency(strategy.profit)}</Tag>
                  </div>
                  <div className="strategy-details">
                    <span>Trades: {strategy.trades}</span>
                    <span>Success: {strategy.successRate}%</span>
                  </div>
                  <Progress 
                    percent={strategy.successRate} 
                    size="small" 
                    strokeColor={strategyColors[index]}
                  />
                </div>
              ))}
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Recent Trades" className="metrics-card">
            <Table
              dataSource={performanceData.recentTrades}
              columns={tradeColumns}
              pagination={false}
              size="small"
              scroll={{ y: 200 }}
              rowKey="id"
            />
          </Card>
        </Col>
      </Row>

      {/* Risk Metrics */}
      <Card title="Risk Analysis" className="risk-metrics-card">
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8}>
            <div className="risk-metric">
              <div className="risk-label">Volatility</div>
              <div className="risk-value">12.5%</div>
              <Progress percent={45} status="active" />
            </div>
          </Col>
          <Col xs={24} sm={8}>
            <div className="risk-metric">
              <div className="risk-label">Value at Risk</div>
              <div className="risk-value">{formatCurrency(250)}</div>
              <Progress percent={30} status="active" />
            </div>
          </Col>
          <Col xs={24} sm={8}>
            <div className="risk-metric">
              <div className="risk-label">Correlation</div>
              <div className="risk-value">0.65</div>
              <Progress percent={65} status="active" />
            </div>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default PerformanceMetrics;