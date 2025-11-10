// frontend/src/components/trading/shared/TradingViewer/TradingViewer.jsx
import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Select,
  Row,
  Col,
  Typography,
  Button,
  Space,
  Tooltip,
  Slider,
  Switch,
  Divider,
  Segmented,
  Timeline,
  Statistic,
  Tag
} from 'antd';
import {
  LineChartOutlined,
  BarChartOutlined,
  AreaChartOutlined,
  SettingOutlined,
  ExpandOutlined,
  DownloadOutlined,
  ShareAltOutlined,
  BellOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined
} from '@ant-design/icons';
import './TradingViewer.css';

const { Title, Text } = Typography;
const { Option } = Select;

const TradingViewer = () => {
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [timeframe, setTimeframe] = useState('1h');
  const [chartType, setChartType] = useState('candlestick');
  const [isPlaying, setIsPlaying] = useState(false);
  const [indicators, setIndicators] = useState(['sma', 'volume']);
  const [drawingTool, setDrawingTool] = useState(null);
  const [chartData, setChartData] = useState([]);
  const chartRef = useRef(null);

  const tradingPairs = [
    { value: 'BTCUSDT', label: 'BTC/USDT', price: 43250.75, change: 2.45 },
    { value: 'ETHUSDT', label: 'ETH/USDT', price: 2580.30, change: -1.23 },
    { value: 'SOLUSDT', label: 'SOL/USDT', price: 98.45, change: 5.67 },
    { value: 'ADAUSDT', label: 'ADA/USDT', price: 0.52, change: -0.89 },
    { value: 'DOTUSDT', label: 'DOT/USDT', price: 7.23, change: 1.34 }
  ];

  const timeframes = [
    { value: '1m', label: '1m' },
    { value: '5m', label: '5m' },
    { value: '15m', label: '15m' },
    { value: '1h', label: '1h' },
    { value: '4h', label: '4h' },
    { value: '1d', label: '1d' },
    { value: '1w', label: '1w' }
  ];

  const chartTypes = [
    { value: 'candlestick', label: 'Candlestick', icon: <BarChartOutlined /> },
    { value: 'line', label: 'Line', icon: <LineChartOutlined /> },
    { value: 'area', label: 'Area', icon: <AreaChartOutlined /> },
    { value: 'heikin-ashi', label: 'Heikin Ashi', icon: <BarChartOutlined /> }
  ];

  const technicalIndicators = [
    { value: 'sma', label: 'SMA', enabled: true },
    { value: 'ema', label: 'EMA', enabled: false },
    { value: 'rsi', label: 'RSI', enabled: false },
    { value: 'macd', label: 'MACD', enabled: false },
    { value: 'bollinger', label: 'Bollinger Bands', enabled: false },
    { value: 'volume', label: 'Volume', enabled: true }
  ];

  const drawingTools = [
    { value: 'trendline', label: 'Trend Line' },
    { value: 'horizontal', label: 'Horizontal Line' },
    { value: 'fibonacci', label: 'Fibonacci' },
    { value: 'rectangle', label: 'Rectangle' },
    { value: 'ellipse', label: 'Ellipse' }
  ];

  // Mock chart data
  useEffect(() => {
    generateChartData();
    const interval = setInterval(() => {
      if (isPlaying) {
        updateChartData();
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [isPlaying, selectedSymbol, timeframe]);

  const generateChartData = () => {
    const data = [];
    const basePrice = tradingPairs.find(p => p.value === selectedSymbol)?.price || 100;
    
    for (let i = 0; i < 50; i++) {
      const open = basePrice + (Math.random() - 0.5) * basePrice * 0.02;
      const close = open + (Math.random() - 0.5) * basePrice * 0.01;
      const high = Math.max(open, close) + Math.random() * basePrice * 0.005;
      const low = Math.min(open, close) - Math.random() * basePrice * 0.005;
      const volume = Math.random() * 1000 + 500;

      data.push({
        time: i,
        open,
        high,
        low,
        close,
        volume
      });
    }
    
    setChartData(data);
  };

  const updateChartData = () => {
    if (chartData.length > 0) {
      const lastCandle = chartData[chartData.length - 1];
      const newCandle = {
        time: lastCandle.time + 1,
        open: lastCandle.close,
        close: lastCandle.close + (Math.random() - 0.5) * lastCandle.close * 0.01,
        high: 0,
        low: 0,
        volume: Math.random() * 1000 + 500
      };
      
      newCandle.high = Math.max(newCandle.open, newCandle.close) + Math.random() * newCandle.close * 0.005;
      newCandle.low = Math.min(newCandle.open, newCandle.close) - Math.random() * newCandle.close * 0.005;

      setChartData(prev => [...prev.slice(1), newCandle]);
    }
  };

  const toggleIndicator = (indicator) => {
    setIndicators(prev => 
      prev.includes(indicator) 
        ? prev.filter(i => i !== indicator)
        : [...prev, indicator]
    );
  };

  const togglePlay = () => {
    setIsPlaying(!isPlaying);
  };

  const getCurrentPriceInfo = () => {
    const pair = tradingPairs.find(p => p.value === selectedSymbol);
    return pair || { price: 0, change: 0 };
  };

  const currentPriceInfo = getCurrentPriceInfo();

  return (
    <div className="trading-viewer">
      {/* Chart Header */}
      <Card className="chart-header-card">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} md={8}>
            <Space size="large">
              <Select
                value={selectedSymbol}
                onChange={setSelectedSymbol}
                className="symbol-select"
                dropdownMatchSelectWidth={200}
              >
                {tradingPairs.map(pair => (
                  <Option key={pair.value} value={pair.value}>
                    <Space>
                      <Text strong>{pair.label}</Text>
                      <Tag color={pair.change >= 0 ? 'green' : 'red'}>
                        {pair.change >= 0 ? '+' : ''}{pair.change}%
                      </Tag>
                    </Space>
                  </Option>
                ))}
              </Select>

              <Segmented
                value={timeframe}
                onChange={setTimeframe}
                options={timeframes}
                size="small"
              />
            </Space>
          </Col>

          <Col xs={24} md={8} className="price-display">
            <Space direction="vertical" size={0} align="center">
              <Title level={3} style={{ margin: 0, color: currentPriceInfo.change >= 0 ? '#52c41a' : '#ff4d4f' }}>
                ${currentPriceInfo.price.toLocaleString()}
              </Title>
              <Text type={currentPriceInfo.change >= 0 ? 'success' : 'danger'}>
                {currentPriceInfo.change >= 0 ? '+' : ''}{currentPriceInfo.change}%
              </Text>
            </Space>
          </Col>

          <Col xs={24} md={8}>
            <Space size="middle" className="chart-controls">
              <Segmented
                value={chartType}
                onChange={setChartType}
                options={chartTypes.map(type => ({
                  value: type.value,
                  label: (
                    <Tooltip title={type.label}>
                      {type.icon}
                    </Tooltip>
                  )
                }))}
                size="small"
              />

              <Tooltip title={isPlaying ? 'Pause' : 'Play'}>
                <Button
                  type="text"
                  icon={isPlaying ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                  onClick={togglePlay}
                  className={isPlaying ? 'playing' : ''}
                />
              </Tooltip>

              <Tooltip title="Settings">
                <Button type="text" icon={<SettingOutlined />} />
              </Tooltip>

              <Tooltip title="Fullscreen">
                <Button type="text" icon={<ExpandOutlined />} />
              </Tooltip>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Main Chart Area */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={18}>
          <Card className="chart-container-card">
            <div className="chart-wrapper">
              {/* Mock Chart Visualization */}
              <div className="mock-chart" ref={chartRef}>
                <div className="chart-placeholder">
                  <LineChartOutlined className="chart-placeholder-icon" />
                  <Title level={4} type="secondary">
                    Advanced Chart Visualization
                  </Title>
                  <Text type="secondary">
                    {selectedSymbol} - {timeframe} - {chartType}
                  </Text>
                  <div className="chart-grid">
                    {chartData.map((candle, index) => (
                      <div
                        key={index}
                        className={`candle ${candle.close >= candle.open ? 'up' : 'down'}`}
                        style={{
                          left: `${(index / chartData.length) * 100}%`,
                          height: `${Math.abs(candle.high - candle.low) / 2}%`,
                          bottom: `${Math.min(candle.open, candle.close)}%`
                        }}
                      />
                    ))}
                  </div>
                </div>
              </div>

              {/* Indicators Legend */}
              {indicators.length > 0 && (
                <div className="indicators-legend">
                  <Space size="small">
                    <Text type="secondary">Indicators:</Text>
                    {indicators.map(indicator => (
                      <Tag key={indicator} color="blue" size="small">
                        {technicalIndicators.find(i => i.value === indicator)?.label}
                      </Tag>
                    ))}
                  </Space>
                </div>
              )}
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={6}>
          {/* Technical Indicators Panel */}
          <Card 
            title="Technical Indicators" 
            size="small"
            className="indicators-panel"
          >
            <Space direction="vertical" style={{ width: '100%' }}>
              {technicalIndicators.map(indicator => (
                <div key={indicator.value} className="indicator-item">
                  <Switch
                    size="small"
                    checked={indicators.includes(indicator.value)}
                    onChange={() => toggleIndicator(indicator.value)}
                  />
                  <Text>{indicator.label}</Text>
                </div>
              ))}
            </Space>

            <Divider />

            <Title level={5}>Drawing Tools</Title>
            <Space direction="vertical" style={{ width: '100%' }}>
              {drawingTools.map(tool => (
                <Button
                  key={tool.value}
                  type={drawingTool === tool.value ? 'primary' : 'default'}
                  size="small"
                  block
                  onClick={() => setDrawingTool(tool.value)}
                >
                  {tool.label}
                </Button>
              ))}
            </Space>
          </Card>

          {/* Recent Activity */}
          <Card 
            title="Recent Activity" 
            size="small"
            className="activity-panel"
            style={{ marginTop: 16 }}
          >
            <Timeline
              items={[
                {
                  color: 'green',
                  children: (
                    <Space direction="vertical" size={0}>
                      <Text strong>Price Alert</Text>
                      <Text type="secondary">BTC broke resistance at $43,000</Text>
                    </Space>
                  ),
                },
                {
                  color: 'blue',
                  children: (
                    <Space direction="vertical" size={0}>
                      <Text strong>Pattern Detected</Text>
                      <Text type="secondary">Bullish engulfing on 1H</Text>
                    </Space>
                  ),
                },
                {
                  color: 'orange',
                  children: (
                    <Space direction="vertical" size={0}>
                      <Text strong>Volume Spike</Text>
                      <Text type="secondary">Unusual volume detected</Text>
                    </Space>
                  ),
                },
              ]}
            />
          </Card>
        </Col>
      </Row>

      {/* Chart Footer */}
      <Card size="small" className="chart-footer">
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={8}>
            <Space>
              <Text type="secondary">Drawing:</Text>
              <Text>{drawingTool || 'None'}</Text>
            </Space>
          </Col>
          <Col xs={24} sm={8} className="footer-center">
            <Space>
              <Button type="text" icon={<DownloadOutlined />} size="small">
                Export
              </Button>
              <Button type="text" icon={<ShareAltOutlined />} size="small">
                Share
              </Button>
              <Button type="text" icon={<BellOutlined />} size="small">
                Alert
              </Button>
            </Space>
          </Col>
          <Col xs={24} sm={8} className="footer-right">
            <Text type="secondary">
              Data: Live • Updated: Just now
            </Text>
          </Col>
        </Row>
      </Card>
    </div>
  );
};

export default TradingViewer;