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
  Progress,
  Tooltip,
  Space,
  Badge
} from 'antd';
import {
  RiseOutlined,
  FallOutlined,
  LineChartOutlined,
  DollarOutlined,
  SearchOutlined,
  StarOutlined,
  EyeOutlined
} from '@ant-design/icons';
import './MarketData.css';

const { Title, Text } = Typography;
const { Option } = Select;
const { Search } = Input;

const MarketData = () => {
  const [marketData, setMarketData] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [searchText, setSearchText] = useState('');
  const [selectedExchange, setSelectedExchange] = useState('all');
  const [watchlist, setWatchlist] = useState(new Set(['BTCUSDT', 'ETHUSDT']));

  // Mock market data
  const initialMarketData = [
    {
      key: '1',
      symbol: 'BTCUSDT',
      name: 'Bitcoin',
      price: 43250.75,
      change: 2.45,
      changePercent: 2.45,
      volume: 2856341200,
      high: 43500.00,
      low: 42800.50,
      exchange: 'binance',
      sparkline: [43000, 43100, 43200, 43150, 43250]
    },
    {
      key: '2',
      symbol: 'ETHUSDT',
      name: 'Ethereum',
      price: 2580.30,
      change: -1.23,
      changePercent: -1.23,
      volume: 1456321800,
      high: 2620.00,
      low: 2560.50,
      exchange: 'binance',
      sparkline: [2600, 2590, 2580, 2570, 2580]
    },
    {
      key: '3',
      symbol: 'SOLUSDT',
      name: 'Solana',
      price: 98.45,
      change: 5.67,
      changePercent: 5.67,
      volume: 856321400,
      high: 99.00,
      low: 92.50,
      exchange: 'kraken',
      sparkline: [93, 94, 95, 96, 98]
    },
    {
      key: '4',
      symbol: 'ADAUSDT',
      name: 'Cardano',
      price: 0.52,
      change: -0.89,
      changePercent: -0.89,
      volume: 356214700,
      high: 0.53,
      low: 0.51,
      exchange: 'coinbase',
      sparkline: [0.53, 0.525, 0.52, 0.515, 0.52]
    },
    {
      key: '5',
      symbol: 'DOTUSDT',
      name: 'Polkadot',
      price: 7.23,
      change: 1.34,
      changePercent: 1.34,
      volume: 256398100,
      high: 7.30,
      low: 7.10,
      exchange: 'okx',
      sparkline: [7.15, 7.18, 7.20, 7.22, 7.23]
    }
  ];

  useEffect(() => {
    setMarketData(initialMarketData);
    setFilteredData(initialMarketData);
  }, []);

  useEffect(() => {
    filterData();
  }, [searchText, selectedExchange, marketData]);

  const filterData = () => {
    let filtered = marketData;

    if (searchText) {
      filtered = filtered.filter(item =>
        item.symbol.toLowerCase().includes(searchText.toLowerCase()) ||
        item.name.toLowerCase().includes(searchText.toLowerCase())
      );
    }

    if (selectedExchange !== 'all') {
      filtered = filtered.filter(item => item.exchange === selectedExchange);
    }

    setFilteredData(filtered);
  };

  const toggleWatchlist = (symbol) => {
    const newWatchlist = new Set(watchlist);
    if (newWatchlist.has(symbol)) {
      newWatchlist.delete(symbol);
    } else {
      newWatchlist.add(symbol);
    }
    setWatchlist(newWatchlist);
  };

  const formatVolume = (volume) => {
    if (volume >= 1000000000) {
      return `$${(volume / 1000000000).toFixed(2)}B`;
    }
    if (volume >= 1000000) {
      return `$${(volume / 1000000).toFixed(2)}M`;
    }
    return `$${(volume / 1000).toFixed(2)}K`;
  };

  const columns = [
    {
      title: 'Pair',
      dataIndex: 'symbol',
      key: 'symbol',
      fixed: 'left',
      render: (symbol, record) => (
        <Space>
          <Tooltip title={watchlist.has(symbol) ? 'Remove from watchlist' : 'Add to watchlist'}>
            <StarOutlined 
              className={`watchlist-icon ${watchlist.has(symbol) ? 'active' : ''}`}
              onClick={() => toggleWatchlist(symbol)}
            />
          </Tooltip>
          <div className="symbol-info">
            <Text strong>{symbol}</Text>
            <div className="asset-name">{record.name}</div>
          </div>
        </Space>
      ),
    },
    {
      title: 'Price',
      dataIndex: 'price',
      key: 'price',
      render: (price, record) => (
        <Space direction="vertical" size={0}>
          <Text strong className="price-value">
            ${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </Text>
          <div className="price-change">
            {record.change >= 0 ? (
              <RiseOutlined className="price-up" />
            ) : (
              <FallOutlined className="price-down" />
            )}
            <Text className={record.change >= 0 ? 'price-up' : 'price-down'}>
              {record.change >= 0 ? '+' : ''}{record.change}%
            </Text>
          </div>
        </Space>
      ),
      sorter: (a, b) => a.price - b.price,
    },
    {
      title: '24h Change',
      dataIndex: 'changePercent',
      key: 'changePercent',
      render: (changePercent) => (
        <Tag color={changePercent >= 0 ? 'green' : 'red'}>
          {changePercent >= 0 ? '+' : ''}{changePercent}%
        </Tag>
      ),
      sorter: (a, b) => a.changePercent - b.changePercent,
    },
    {
      title: '24h Volume',
      dataIndex: 'volume',
      key: 'volume',
      render: (volume) => (
        <Text>{formatVolume(volume)}</Text>
      ),
      sorter: (a, b) => a.volume - b.volume,
    },
    {
      title: '24h High/Low',
      key: 'highLow',
      render: (record) => (
        <Space direction="vertical" size={0}>
          <Text type="secondary" className="high-low-text">
            H: ${record.high.toLocaleString()}
          </Text>
          <Text type="secondary" className="high-low-text">
            L: ${record.low.toLocaleString()}
          </Text>
        </Space>
      ),
    },
    {
      title: 'Exchange',
      dataIndex: 'exchange',
      key: 'exchange',
      render: (exchange) => (
        <Tag color="blue" className="exchange-tag">
          {exchange.toUpperCase()}
        </Tag>
      ),
      filters: [
        { text: 'Binance', value: 'binance' },
        { text: 'Kraken', value: 'kraken' },
        { text: 'Coinbase', value: 'coinbase' },
        { text: 'OKX', value: 'okx' },
      ],
      onFilter: (value, record) => record.exchange === value,
    },
    {
      title: 'Actions',
      key: 'actions',
      fixed: 'right',
      render: (record) => (
        <Space>
          <Tooltip title="View Details">
            <EyeOutlined className="action-icon" />
          </Tooltip>
          <Tooltip title="Trade">
            <DollarOutlined className="action-icon trade-icon" />
          </Tooltip>
        </Space>
      ),
    },
  ];

  const marketStats = {
    totalMarketCap: 1650000000000,
    totalVolume: 85632000000,
    btcDominance: 42.5,
    activeCurrencies: 12560
  };

  return (
    <div className="market-data">
      {/* Market Overview */}
      <Row gutter={[16, 16]} className="market-overview">
        <Col xs={24} sm={6}>
          <Card className="market-stat-card">
            <Statistic
              title="Total Market Cap"
              value={marketStats.totalMarketCap}
              formatter={value => `$${(value / 1000000000000).toFixed(2)}T`}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card className="market-stat-card">
            <Statistic
              title="24h Volume"
              value={marketStats.totalVolume}
              formatter={value => `$${(value / 1000000000).toFixed(2)}B`}
              prefix={<LineChartOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card className="market-stat-card">
            <Statistic
              title="BTC Dominance"
              value={marketStats.btcDominance}
              suffix="%"
              valueStyle={{ color: '#faad14' }}
            />
            <Progress 
              percent={marketStats.btcDominance} 
              showInfo={false}
              strokeColor="#faad14"
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card className="market-stat-card">
            <Statistic
              title="Active Currencies"
              value={marketStats.activeCurrencies}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Market Data Table */}
      <Card 
        title={
          <Space>
            <LineChartOutlined />
            Real-time Market Data
          </Space>
        }
        className="market-data-table-card"
        extra={
          <Space>
            <Search
              placeholder="Search pairs..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: 200 }}
              prefix={<SearchOutlined />}
            />
            <Select
              value={selectedExchange}
              onChange={setSelectedExchange}
              style={{ width: 120 }}
              placeholder="Exchange"
            >
              <Option value="all">All Exchanges</Option>
              <Option value="binance">Binance</Option>
              <Option value="kraken">Kraken</Option>
              <Option value="coinbase">Coinbase</Option>
              <Option value="okx">OKX</Option>
            </Select>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={filteredData}
          pagination={false}
          scroll={{ x: 800 }}
          size="small"
          className="market-data-table"
          rowClassName={(record) => watchlist.has(record.symbol) ? 'watchlist-row' : ''}
        />
        
        <div className="market-data-footer">
          <Text type="secondary">
            Showing {filteredData.length} of {marketData.length} trading pairs
          </Text>
          <Badge 
            status="processing" 
            text="Live Data" 
            className="live-badge"
          />
        </div>
      </Card>
    </div>
  );
};

export default MarketData;