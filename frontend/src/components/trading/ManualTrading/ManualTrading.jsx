// frontend/src/components/trading/ManualTrade/ManualTrade.jsx
import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  InputNumber,
  Select,
  Button,
  Row,
  Col,
  Divider,
  Typography,
  Tag,
  Alert,
  Space,
  Statistic,
  Switch,
  Tooltip
} from 'antd';
import {
  DollarOutlined,
  PercentageOutlined,
  CalculatorOutlined,
  RocketOutlined,
  SafetyOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import './ManualTrading.css';

const { Title, Text } = Typography;
const { Option } = Select;

const ManualTrading = () => {
  const [form] = Form.useForm();
  const [orderType, setOrderType] = useState('market');
  const [side, setSide] = useState('buy');
  const [calculating, setCalculating] = useState(false);
  const [estimatedCost, setEstimatedCost] = useState(0);
  const [availableBalance, setAvailableBalance] = useState(10000);

  // Mock market data
  const marketData = {
    BTCUSDT: { price: 43250.75, change: 2.45 },
    ETHUSDT: { price: 2580.30, change: -1.23 },
    SOLUSDT: { price: 98.45, change: 5.67 }
  };

  const tradingPairs = [
    { value: 'BTCUSDT', label: 'BTC/USDT' },
    { value: 'ETHUSDT', label: 'ETH/USDT' },
    { value: 'SOLUSDT', label: 'SOL/USDT' },
    { value: 'ADAUSDT', label: 'ADA/USDT' },
    { value: 'DOTUSDT', label: 'DOT/USDT' }
  ];

  const exchanges = [
    { value: 'binance', label: 'Binance' },
    { value: 'kraken', label: 'Kraken' },
    { value: 'coinbase', label: 'Coinbase' },
    { value: 'okx', label: 'OKX' }
  ];

  useEffect(() => {
    // Calculate estimated cost when form values change
    const subscription = form.watch((values) => {
      if (values.symbol && values.quantity && marketData[values.symbol]) {
        calculateEstimatedCost(values);
      }
    });
    return () => subscription.unsubscribe();
  }, [form]);

  const calculateEstimatedCost = (values) => {
    setCalculating(true);
    const currentPrice = marketData[values.symbol]?.price || 0;
    const quantity = values.quantity || 0;
    
    setTimeout(() => {
      const cost = currentPrice * quantity;
      setEstimatedCost(cost);
      setCalculating(false);
    }, 300);
  };

  const onOrderTypeChange = (value) => {
    setOrderType(value);
  };

  const onSideChange = (value) => {
    setSide(value);
  };

  const onFinish = async (values) => {
    console.log('Order submitted:', values);
    // Here you would integrate with your trading API
    // await tradingService.placeOrder(values);
    
    // Mock success
    Alert.success(`Order placed successfully! ${values.side.toUpperCase()} ${values.quantity} ${values.symbol}`);
    form.resetFields();
    setEstimatedCost(0);
  };

  const getCurrentPrice = (symbol) => {
    return marketData[symbol]?.price || 0;
  };

  const getPriceChange = (symbol) => {
    const change = marketData[symbol]?.change || 0;
    return {
      value: change,
      isPositive: change > 0
    };
  };

  return (
    <div className="manual-trading">
      <Row gutter={[24, 24]}>
        {/* Order Form */}
        <Col xs={24} lg={16}>
          <Card 
            title={
              <Space>
                <RocketOutlined />
                Place New Order
              </Space>
            }
            className="order-form-card"
          >
            <Form
              form={form}
              layout="vertical"
              onFinish={onFinish}
              initialValues={{
                symbol: 'BTCUSDT',
                side: 'buy',
                orderType: 'market',
                quantity: 0.1,
                exchange: 'binance'
              }}
            >
              <Row gutter={16}>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="Trading Pair"
                    name="symbol"
                    rules={[{ required: true, message: 'Please select a trading pair' }]}
                  >
                    <Select 
                      placeholder="Select trading pair"
                      className="trading-pair-select"
                    >
                      {tradingPairs.map(pair => (
                        <Option key={pair.value} value={pair.value}>
                          <Space>
                            <span>{pair.label}</span>
                            <Tag color={getPriceChange(pair.value).isPositive ? 'green' : 'red'}>
                              {getPriceChange(pair.value).value}%
                            </Tag>
                            <Text type="secondary">
                              ${getCurrentPrice(pair.value).toLocaleString()}
                            </Text>
                          </Space>
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
                
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="Exchange"
                    name="exchange"
                    rules={[{ required: true, message: 'Please select an exchange' }]}
                  >
                    <Select placeholder="Select exchange">
                      {exchanges.map(exchange => (
                        <Option key={exchange.value} value={exchange.value}>
                          {exchange.label}
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={16}>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="Order Side"
                    name="side"
                    rules={[{ required: true, message: 'Please select order side' }]}
                  >
                    <Select onChange={onSideChange}>
                      <Option value="buy">
                        <Space>
                          <span style={{ color: '#52c41a' }}>BUY</span>
                          <Text type="secondary">Purchase assets</Text>
                        </Space>
                      </Option>
                      <Option value="sell">
                        <Space>
                          <span style={{ color: '#ff4d4f' }}>SELL</span>
                          <Text type="secondary">Sell assets</Text>
                        </Space>
                      </Option>
                    </Select>
                  </Form.Item>
                </Col>
                
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="Order Type"
                    name="orderType"
                    rules={[{ required: true, message: 'Please select order type' }]}
                  >
                    <Select onChange={onOrderTypeChange}>
                      <Option value="market">Market Order</Option>
                      <Option value="limit">Limit Order</Option>
                      <Option value="stop">Stop Order</Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              {orderType !== 'market' && (
                <Row gutter={16}>
                  <Col xs={24} sm={12}>
                    <Form.Item
                      label="Price"
                      name="price"
                      rules={[{ required: true, message: 'Please enter price' }]}
                    >
                      <InputNumber
                        placeholder="Enter price"
                        min={0}
                        step={0.01}
                        style={{ width: '100%' }}
                        prefix={<DollarOutlined />}
                      />
                    </Form.Item>
                  </Col>
                </Row>
              )}

              <Row gutter={16}>
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="Quantity"
                    name="quantity"
                    rules={[{ required: true, message: 'Please enter quantity' }]}
                  >
                    <InputNumber
                      placeholder="Enter quantity"
                      min={0}
                      step={0.0001}
                      style={{ width: '100%' }}
                      onChange={() => calculateEstimatedCost(form.getFieldsValue())}
                    />
                  </Form.Item>
                </Col>
                
                <Col xs={24} sm={12}>
                  <Form.Item
                    label="Total Cost"
                    className="estimated-cost"
                  >
                    <div className="cost-display">
                      <Statistic
                        value={estimatedCost}
                        precision={2}
                        prefix="$"
                        loading={calculating}
                        valueStyle={{
                          color: side === 'buy' ? '#52c41a' : '#ff4d4f',
                          fontSize: '18px'
                        }}
                      />
                      {estimatedCost > availableBalance && (
                        <Alert
                          message="Insufficient balance"
                          type="warning"
                          showIcon
                          size="small"
                          style={{ marginTop: 8 }}
                        />
                      )}
                    </div>
                  </Form.Item>
                </Col>
              </Row>

              <Divider />

              <Form.Item>
                <Space size="large">
                  <Button 
                    type="primary" 
                    htmlType="submit"
                    icon={<RocketOutlined />}
                    size="large"
                    disabled={estimatedCost > availableBalance}
                    className="submit-order-btn"
                  >
                    Place {side.toUpperCase()} Order
                  </Button>
                  <Button 
                    htmlType="button" 
                    onClick={() => form.resetFields()}
                    size="large"
                  >
                    Reset
                  </Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>
        </Col>

        {/* Trading Info Panel */}
        <Col xs={24} lg={8}>
          <Card 
            title={
              <Space>
                <InfoCircleOutlined />
                Trading Information
              </Space>
            }
            className="trading-info-card"
          >
            <div className="info-section">
              <Title level={5}>Available Balance</Title>
              <Statistic
                value={availableBalance}
                precision={2}
                prefix="$"
                valueStyle={{ color: '#1890ff' }}
              />
            </div>

            <Divider />

            <div className="info-section">
              <Title level={5}>Current Prices</Title>
              {Object.entries(marketData).map(([symbol, data]) => (
                <div key={symbol} className="price-item">
                  <Text strong>{symbol}</Text>
                  <Space>
                    <Text>${data.price.toLocaleString()}</Text>
                    <Tag color={data.change > 0 ? 'green' : 'red'}>
                      {data.change > 0 ? '+' : ''}{data.change}%
                    </Tag>
                  </Space>
                </div>
              ))}
            </div>

            <Divider />

            <div className="info-section">
              <Title level={5}>Risk Management</Title>
              <div className="risk-item">
                <Text>Max Position Size</Text>
                <Text strong>$2,000</Text>
              </div>
              <div className="risk-item">
                <Text>Daily Loss Limit</Text>
                <Text strong>$500</Text>
              </div>
              <div className="risk-item">
                <Text>Leverage</Text>
                <Text strong>1x</Text>
              </div>
            </div>

            <Divider />

            <div className="info-section">
              <Space direction="vertical" style={{ width: '100%' }}>
                <div className="setting-item">
                  <Text>Post Only</Text>
                  <Switch size="small" />
                </div>
                <div className="setting-item">
                  <Text>Reduce Only</Text>
                  <Switch size="small" />
                </div>
                <div className="setting-item">
                  <Text>Iceberg Order</Text>
                  <Switch size="small" />
                </div>
              </Space>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default ManualTrading;