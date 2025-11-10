// frontend/src/pages/Analytics/Analytics.jsx
import React, { useState, useEffect } from 'react';
import {
  Card,
  Typography,
  Button,
  Select,
  Row,
  Col,
  Table,
  Tag,
  Tooltip,
  Spin,
  Skeleton
} from 'antd';
import {
  LineChart,
  Line,
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
  Cell,
  AreaChart,
  Area
} from 'recharts';
import {
  DownloadOutlined,
  ReloadOutlined,
  RiseOutlined,
  FallOutlined,
  DollarOutlined,
  TrophyOutlined,
  SafetyCertificateOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import { analyticsService } from '../../services/api/analyticsService';
import './Analytics.css';

const { Title, Text } = Typography;
const { Option } = Select;

const Analytics = () => {
  const [loading, setLoading] = useState(true);
  const [performanceData, setPerformanceData] = useState(null);
  const [profitHistory, setProfitHistory] = useState([]);
  const [period, setPeriod] = useState('30d');
  const [exportLoading, setExportLoading] = useState(false);

  useEffect(() => {
    loadAnalyticsData();
  }, [period]);

  const loadAnalyticsData = async () => {
    try {
      setLoading(true);
      const [performance, history] = await Promise.all([
        analyticsService.getPerformanceSummary(period),
        analyticsService.getProfitHistory(period)
      ]);
      setPerformanceData(performance);
      setProfitHistory(history);
    } catch (error) {
      console.error('Failed to load analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    try {
      setExportLoading(true);
      await analyticsService.exportAnalyticsData(format);
      // In a real app, this would trigger a download
      console.log(`Exporting analytics data as ${format}`);
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setExportLoading(false);
    }
  };

  const getTrendIcon = (value) => {
    if (value > 0) return <RiseOutlined className="analytics-trend-positive" />;
    if (value < 0) return <FallOutlined className="analytics-trend-negative" />;
    return <BarChartOutlined className="analytics-trend-neutral" />;
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(value);
  };

  const formatPercentage = (value) => {
    return `${value.toFixed(1)}%`;
  };

  // Performance metrics cards
  const performanceMetrics = [
    {
      key: 'total_profit',
      title: 'Total Profit',
      value: performanceData?.total_profit || 0,
      formatter: formatCurrency,
      icon: <DollarOutlined />,
      color: '#52c41a',
      description: 'Cumulative profit from all trades'
    },
    {
      key: 'win_rate',
      title: 'Win Rate',
      value: performanceData?.win_rate || 0,
      formatter: formatPercentage,
      icon: <TrophyOutlined />,
      color: '#1890ff',
      description: 'Percentage of profitable trades'
    },
    {
      key: 'success_rate',
      title: 'Success Rate',
      value: performanceData?.success_rate || 0,
      formatter: formatPercentage,
      icon: <SafetyCertificateOutlined />,
      color: '#722ed1',
      description: 'Overall strategy success rate'
    },
    {
      key: 'sharpe_ratio',
      title: 'Sharpe Ratio',
      value: performanceData?.sharpe_ratio || 0,
      formatter: (value) => value.toFixed(2),
      icon: <BarChartOutlined />,
      color: '#fa8c16',
      description: 'Risk-adjusted returns'
    }
  ];

  // Trading statistics
  const tradingStats = [
    {
      key: 'total_trades',
      label: 'Total Trades',
      value: performanceData?.total_trades || 0
    },
    {
      key: 'avg_profit',
      label: 'Avg Profit/Trade',
      value: performanceData?.avg_profit_per_trade || 0,
      formatter: formatCurrency
    },
    {
      key: 'max_drawdown',
      label: 'Max Drawdown',
      value: performanceData?.max_drawdown || 0,
      formatter: formatPercentage
    },
    {
      key: 'profit_factor',
      label: 'Profit Factor',
      value: 2.1, // This would come from API
      formatter: (value) => value.toFixed(2)
    }
  ];

  // Mock recent trades data
  const recentTrades = [
    {
      id: 1,
      pair: 'BTC/USDT',
      exchange: 'Binance',
      profit: 45.23,
      timestamp: '2024-01-15 14:30:00',
      status: 'completed'
    },
    {
      id: 2,
      pair: 'ETH/USDT',
      exchange: 'Kraken',
      profit: -12.50,
      timestamp: '2024-01-15 13:15:00',
      status: 'completed'
    },
    {
      id: 3,
      pair: 'SOL/USDT',
      exchange: 'Coinbase',
      profit: 78.91,
      timestamp: '2024-01-15 12:00:00',
      status: 'completed'
    },
    {
      id: 4,
      pair: 'ADA/USDT',
      exchange: 'Binance',
      profit: 23.45,
      timestamp: '2024-01-15 11:30:00',
      status: 'completed'
    },
    {
      id: 5,
      pair: 'DOT/USDT',
      exchange: 'Kraken',
      profit: 15.67,
      timestamp: '2024-01-15 10:45:00',
      status: 'completed'
    }
  ];

  const columns = [
    {
      title: 'Trade Pair',
      dataIndex: 'pair',
      key: 'pair',
      render: (text) => <Text strong>{text}</Text>
    },
    {
      title: 'Exchange',
      dataIndex: 'exchange',
      key: 'exchange',
      render: (text) => <Tag color="blue">{text}</Tag>
    },
    {
      title: 'Profit/Loss',
      dataIndex: 'profit',
      key: 'profit',
      render: (profit) => (
        <Text 
          className={profit >= 0 ? 'analytics-trade-profit-positive' : 'analytics-trade-profit-negative'}
        >
          {formatCurrency(profit)}
        </Text>
      )
    },
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (text) => new Date(text).toLocaleString()
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={status === 'completed' ? 'green' : 'orange'}>
          {status.toUpperCase()}
        </Tag>
      )
    }
  ];

  if (loading) {
    return (
      <div className="analytics-page">
        <div className="analytics-header">
          <Skeleton active paragraph={{ rows: 1 }} />
        </div>
        <div className="analytics-skeleton">
          <Row gutter={[16, 16]}>
            {[1, 2, 3, 4].map(item => (
              <Col xs={24} sm={12} lg={6} key={item}>
                <Card>
                  <Skeleton active />
                </Card>
              </Col>
            ))}
          </Row>
          <div className="analytics-skeleton-chart">
            <Spin size="large" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="analytics-page">
      <div className="analytics-header">
        <Title level={2}>Trading Analytics</Title>
        <div className="analytics-subtitle">
          Comprehensive performance metrics and trading insights
        </div>
      </div>

      {/* Controls */}
      <div className="analytics-controls">
        <div className="analytics-period-selector">
          <Text strong>Period:</Text>
          <Select value={period} onChange={setPeriod} style={{ width: 120 }}>
            <Option value="7d">Last 7 Days</Option>
            <Option value="30d">Last 30 Days</Option>
            <Option value="90d">Last 90 Days</Option>
            <Option value="1y">Last Year</Option>
          </Select>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={loadAnalyticsData}
            loading={loading}
          >
            Refresh
          </Button>
        </div>

        <div className="analytics-export-actions">
          <Button 
            icon={<DownloadOutlined />}
            onClick={() => handleExport('csv')}
            loading={exportLoading}
          >
            Export CSV
          </Button>
          <Button 
            icon={<DownloadOutlined />}
            onClick={() => handleExport('pdf')}
            loading={exportLoading}
          >
            Export PDF
          </Button>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="analytics-metrics-grid">
        {performanceMetrics.map(metric => (
          <Card key={metric.key} className="analytics-metric-card">
            <div className="analytics-metric-header">
              <div className="analytics-metric-title">{metric.title}</div>
              <div className="analytics-metric-trend">
                {getTrendIcon(metric.value)}
                <Text>+5.2%</Text>
              </div>
            </div>
            <div className="analytics-metric-value" style={{ color: metric.color }}>
              {metric.formatter ? metric.formatter(metric.value) : metric.value}
            </div>
            <div className="analytics-metric-description">
              {metric.description}
            </div>
          </Card>
        ))}
      </div>

      {/* Charts Section */}
      <div className="analytics-charts-section">
        {/* Profit Chart */}
        <Card className="analytics-chart-card">
          <div className="analytics-chart-header">
            <Title level={4} className="analytics-chart-title">Profit & Loss History</Title>
            <div className="analytics-chart-actions">
              <Tooltip title="Daily view">
                <Button size="small">D</Button>
              </Tooltip>
              <Tooltip title="Weekly view">
                <Button size="small">W</Button>
              </Tooltip>
              <Tooltip title="Monthly view">
                <Button size="small">M</Button>
              </Tooltip>
            </div>
          </div>
          <div className="analytics-chart-container">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={profitHistory}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => new Date(value).toLocaleDateString()}
                />
                <YAxis 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `$${value}`}
                />
                <RechartsTooltip 
                  formatter={(value) => [formatCurrency(value), 'Profit']}
                  labelFormatter={(label) => `Date: ${new Date(label).toLocaleDateString()}`}
                />
                <Legend />
                <Area 
                  type="monotone" 
                  dataKey="profit" 
                  stroke="#1890ff" 
                  fill="#1890ff" 
                  fillOpacity={0.3}
                  name="Profit/Loss"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* Trading Statistics */}
        <Card className="analytics-chart-card">
          <div className="analytics-chart-header">
            <Title level={4} className="analytics-chart-title">Trading Statistics</Title>
          </div>
          <div className="analytics-stats-grid">
            {tradingStats.map(stat => (
              <div key={stat.key} className="analytics-stat-item">
                <div className="analytics-stat-value">
                  {stat.formatter ? stat.formatter(stat.value) : stat.value}
                </div>
                <div className="analytics-stat-label">{stat.label}</div>
              </div>
            ))}
          </div>
          
          {/* Risk Metrics */}
          <div style={{ marginTop: 24 }}>
            <Title level={5}>Risk Metrics</Title>
            <div className="analytics-risk-metrics">
              <div className="analytics-risk-metric analytics-risk-metric-success">
                <div className="analytics-risk-value">
                  {performanceData?.sharpe_ratio?.toFixed(2) || '0.00'}
                </div>
                <div className="analytics-risk-label">Sharpe Ratio</div>
              </div>
              <div className="analytics-risk-metric analytics-risk-metric-warning">
                <div className="analytics-risk-value">
                  {formatPercentage(performanceData?.max_drawdown || 0)}
                </div>
                <div className="analytics-risk-label">Max Drawdown</div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Recent Trades */}
      <Card className="analytics-trades-section">
        <div className="analytics-chart-header">
          <Title level={4}>Recent Trades</Title>
          <Button type="link" size="small">
            View All Trades
          </Button>
        </div>
        <div className="analytics-trades-table">
          <Table
            dataSource={recentTrades}
            columns={columns}
            pagination={false}
            size="small"
            scroll={{ x: 600 }}
            rowKey="id"
          />
        </div>
      </Card>

      {/* Additional Analytics Sections */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={12}>
          <Card title="Exchange Performance">
            <div className="analytics-chart-container" style={{ height: 200 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={[
                  { exchange: 'Binance', profit: 850, trades: 25 },
                  { exchange: 'Kraken', profit: 320, trades: 12 },
                  { exchange: 'Coinbase', profit: 180, trades: 8 }
                ]}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="exchange" />
                  <YAxis />
                  <RechartsTooltip />
                  <Legend />
                  <Bar dataKey="profit" fill="#1890ff" name="Profit ($)" />
                  <Bar dataKey="trades" fill="#52c41a" name="Trades" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} lg={12}>
          <Card title="Trade Distribution">
            <div className="analytics-chart-container" style={{ height: 200 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Profitable', value: 67, color: '#52c41a' },
                      { name: 'Break-even', value: 15, color: '#faad14' },
                      { name: 'Loss', value: 18, color: '#ff4d4f' }
                    ]}
                    cx="50%"
                    cy="50%"
                    outerRadius={60}
                    dataKey="value"
                    label
                  >
                    {[
                      { name: 'Profitable', value: 67, color: '#52c41a' },
                      { name: 'Break-even', value: 15, color: '#faad14' },
                      { name: 'Loss', value: 18, color: '#ff4d4f' }
                    ].map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Analytics;