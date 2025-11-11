// frontend/src/components/trading/shared/MarketData/MarketData.jsx
import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Tag,
  Typography,
  Input,
  Select,
  Row,
  Col,
  Statistic,
  Space,
  Badge,
  Progress
} from 'antd';
import {
  RiseOutlined,
  LineChartOutlined,
  SearchOutlined,
  SwapOutlined,
  ThunderboltOutlined,
  ClockCircleOutlined,
  ArrowRightOutlined
} from '@ant-design/icons';
import './MarketData.css';

const { Title, Text } = Typography;
const { Option } = Select;
const { Search } = Input;

const MarketData = () => {
  const [arbitrageData, setArbitrageData] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [searchText, setSearchText] = useState('');
  const [selectedType, setSelectedType] = useState('all');
  const [loading, setLoading] = useState(true);

  // Mock triangular and cross-exchange arbitrage data
  const initialArbitrageData = [
    {
      key: '1',
      type: 'triangular',
      path: 'BTC → ETH → USDT → BTC',
      profit: 2.45,
      volume: 2856341,
      timeframe: '15s',
      exchanges: ['binance', 'kraken', 'coinbase'],
      status: 'high',
      timestamp: '2024-01-15 14:30:00'
    },
    {
      key: '2',
      type: 'cross-exchange',
      path: 'ETH/USDT',
      profit: 1.23,
      volume: 1456321,
      timeframe: '30s',
      buyExchange: 'kucoin',
      sellExchange: 'binance',
      status: 'active',
      timestamp: '2024-01-15 14:28:00'
    },
    {
      key: '3',
      type: 'triangular',
      path: 'SOL → ADA → USDT → SOL',
      profit: 3.67,
      volume: 856321,
      timeframe: '20s',
      exchanges: ['okx', 'huobi', 'binance'],
      status: 'high',
      timestamp: '2024-01-15 14:25:00'
    },
    {
      key: '4',
      type: 'cross-exchange',
      path: 'ADA/USDT',
      profit: 0.89,
      volume: 356214,
      timeframe: '45s',
      buyExchange: 'coinbase',
      sellExchange: 'kraken',
      status: 'medium',
      timestamp: '2024-01-15 14:22:00'
    },
    {
      key: '5',
      type: 'triangular',
      path: 'DOT → BTC → USDT → DOT',
      profit: 1.34,
      volume: 256398,
      timeframe: '25s',
      exchanges: ['okx', 'binance', 'kucoin'],
      status: 'active',
      timestamp: '2024-01-15 14:20:00'
    }
  ];

  useEffect(() => {
    // Simulate API loading
    setLoading(true);
    setTimeout(() => {
      setArbitrageData(initialArbitrageData);
      setFilteredData(initialArbitrageData);
      setLoading(false);
    }, 500);
  }, []);

  useEffect(() => {
    filterData();
  }, [searchText, selectedType, arbitrageData]);

  const filterData = () => {
    let filtered = [...arbitrageData]; // Create a copy to avoid mutation

    if (searchText) {
      filtered = filtered.filter(item =>
        item.path?.toLowerCase().includes(searchText.toLowerCase())
      );
    }

    if (selectedType !== 'all') {
      filtered = filtered.filter(item => item.type === selectedType);
    }

    setFilteredData(filtered);
  };

  const getProfitColor = (profit) => {
    if (profit >= 2) return '#52c41a';
    if (profit >= 1) return '#faad14';
    return '#ff4d4f';
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'high': return 'red';
      case 'medium': return 'orange';
      case 'active': return 'green';
      default: return 'blue';
    }
  };

  const formatVolume = (volume) => {
    if (!volume) return '$0';
    if (volume >= 1000000) {
      return `$${(volume / 1000000).toFixed(1)}M`;
    }
    return `$${(volume / 1000).toFixed(1)}K`;
  };

  // Safe string conversion with null checking
  const safeToUpperCase = (str) => {
    return str?.toUpperCase() || '';
  };

  const renderExchanges = (record) => {
    if (!record) return null;

    if (record.type === 'triangular') {
      return (
        <div className="exchanges">
          {record.exchanges?.map((exchange, index) => (
            <Tag key={index} size="small" color="blue">
              {safeToUpperCase(exchange)}
            </Tag>
          )) || <Text type="secondary">No exchanges</Text>}
        </div>
      );
    } else {
      return (
        <div className="exchanges">
          <Tag size="small" color="green">
            BUY: {safeToUpperCase(record.buyExchange)}
          </Tag>
          <ArrowRightOutlined style={{ fontSize: '10px', margin: '0 4px', color: '#666' }} />
          <Tag size="small" color="red">
            SELL: {safeToUpperCase(record.sellExchange)}
          </Tag>
        </div>
      );
    }
  };

  const columns = [
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      width: 100,
      render: (type) => (
        <Tag 
          color={type === 'triangular' ? 'blue' : 'purple'}
          style={{ fontWeight: '600', fontSize: '11px' }}
        >
          {type === 'triangular' ? 'TRI' : 'X-CHANGE'}
        </Tag>
      ),
    },
    {
      title: 'Trading Path',
      dataIndex: 'path',
      key: 'path',
      render: (path, record) => (
        <Space direction="vertical" size={4}>
          <Text strong className="path-text">{path || 'Unknown Path'}</Text>
          {renderExchanges(record)}
        </Space>
      ),
    },
    {
      title: 'Profit',
      dataIndex: 'profit',
      key: 'profit',
      width: 80,
      render: (profit) => (
        <Text strong style={{ 
          color: getProfitColor(profit || 0), 
          fontSize: '13px',
          fontFamily: 'monospace'
        }}>
          +{(profit || 0).toFixed(2)}%
        </Text>
      ),
      sorter: (a, b) => (a.profit || 0) - (b.profit || 0),
    },
    {
      title: 'Volume',
      dataIndex: 'volume',
      key: 'volume',
      width: 90,
      render: (volume) => (
        <Text type="secondary" style={{ fontSize: '12px' }}>
          {formatVolume(volume)}
        </Text>
      ),
    },
    {
      title: 'Time',
      dataIndex: 'timeframe',
      key: 'timeframe',
      width: 70,
      render: (timeframe) => (
        <Tag 
          icon={<ClockCircleOutlined />} 
          size="small"
          style={{ fontSize: '10px', padding: '0 6px' }}
        >
          {timeframe || 'N/A'}
        </Tag>
      ),
    },
  ];

  const arbitrageStats = {
    totalOpportunities: filteredData.length,
    activeOpportunities: filteredData.filter(item => 
      item.status === 'active' || item.status === 'high'
    ).length,
    avgProfit: filteredData.length > 0 
      ? filteredData.reduce((sum, item) => sum + (item.profit || 0), 0) / filteredData.length 
      : 0,
    triangularCount: filteredData.filter(item => item.type === 'triangular').length
  };

  return (
    <div className="arbitrage-market-data">
      {/* Arbitrage Overview */}
      <Row gutter={[12, 12]} className="arbitrage-overview">
        <Col xs={12} sm={6}>
          <Card className="arbitrage-stat-card" size="small">
            <Statistic
              title="Opportunities"
              value={arbitrageStats.totalOpportunities}
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#1890ff', fontSize: '20px' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card className="arbitrage-stat-card" size="small">
            <Statistic
              title="Active"
              value={arbitrageStats.activeOpportunities}
              valueStyle={{ color: '#52c41a', fontSize: '20px' }}
            />
            <Progress 
              percent={
                arbitrageStats.totalOpportunities > 0 
                  ? (arbitrageStats.activeOpportunities / arbitrageStats.totalOpportunities) * 100 
                  : 0
              } 
              showInfo={false}
              size="small"
              strokeColor="#52c41a"
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card className="arbitrage-stat-card" size="small">
            <Statistic
              title="Avg Profit"
              value={arbitrageStats.avgProfit.toFixed(2)}
              suffix="%"
              valueStyle={{ color: '#faad14', fontSize: '20px' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card className="arbitrage-stat-card" size="small">
            <Statistic
              title="Triangular"
              value={arbitrageStats.triangularCount}
              valueStyle={{ color: '#722ed1', fontSize: '20px' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Arbitrage Opportunities Table */}
      <Card 
        title={
          <Space size="small">
            <SwapOutlined />
            <Text strong>Arbitrage Opportunities</Text>
          </Space>
        }
        className="arbitrage-table-card"
        size="small"
        extra={
          <Space size="small">
            <Search
              placeholder="Search paths..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: 140 }}
              size="small"
              prefix={<SearchOutlined />}
            />
            <Select
              value={selectedType}
              onChange={setSelectedType}
              style={{ width: 120 }}
              size="small"
              placeholder="Type"
            >
              <Option value="all">All</Option>
              <Option value="triangular">Triangular</Option>
              <Option value="cross-exchange">Cross-Exchange</Option>
            </Select>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={filteredData}
          pagination={false}
          scroll={{ x: 600 }}
          size="small"
          className="arbitrage-data-table"
          loading={loading}
          rowClassName={(record) => `opportunity-row ${record.status || 'unknown'}`}
          locale={{
            emptyText: loading ? 'Loading opportunities...' : 'No arbitrage opportunities found'
          }}
        />
        
        <div className="arbitrage-data-footer">
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {filteredData.length} opportunities • Auto-refresh 5s
          </Text>
          <Badge 
            status="processing" 
            text="Live" 
            className="live-badge"
          />
        </div>
      </Card>
    </div>
  );
};

export default MarketData;