// frontend/src/components/trading/ManualTrading/ManualTrading.jsx
import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  InputNumber,
  Select,
  Button,
  Row,
  Col,
  Typography,
  Tag,
  Alert,
  Space,
  Statistic,
  Divider,
  message,
  Radio,
  Progress
} from 'antd';
import {
  RocketOutlined,
  ArrowRightOutlined,
  CalculatorOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  SwapOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';
import './ManualTrading.css';

const { Title, Text } = Typography;
const { Option } = Select;

const ManualTrading = () => {
  const [form] = Form.useForm();
  const [calculating, setCalculating] = useState(false);
  const [estimatedProfit, setEstimatedProfit] = useState(0);
  const [tradingActive, setTradingActive] = useState(false);
  const [arbitrageType, setArbitrageType] = useState('triangular');
  const [currentOpportunities, setCurrentOpportunities] = useState([]);

  // Triangular arbitrage opportunities
  const triangularOpportunities = [
    {
      id: 'btc-eth-usdt',
      name: 'BTC → ETH → USDT → BTC',
      path: ['BTC/USDT', 'ETH/BTC', 'ETH/USDT'],
      profit: 0.8,
      risk: 'Low',
      volume: 'High',
      executionTime: 1200
    },
    {
      id: 'eth-btc-usdt',
      name: 'ETH → BTC → USDT → ETH', 
      path: ['ETH/USDT', 'BTC/ETH', 'BTC/USDT'],
      profit: 0.6,
      risk: 'Low',
      volume: 'High',
      executionTime: 1100
    },
    {
      id: 'sol-eth-btc',
      name: 'SOL → ETH → BTC → SOL',
      path: ['SOL/USDT', 'ETH/SOL', 'BTC/ETH', 'BTC/SOL'],
      profit: 1.2,
      risk: 'Medium',
      volume: 'Medium',
      executionTime: 1500
    }
  ];

  // Cross-exchange arbitrage opportunities
  const crossExchangeOpportunities = [
    {
      id: 'btc-binance-kraken',
      name: 'BTC: Binance → Kraken',
      path: ['Binance: BTC/USDT', 'Kraken: BTC/USDT'],
      profit: 1.5,
      risk: 'Medium',
      volume: 'Very High',
      executionTime: 1800
    },
    {
      id: 'eth-coinbase-okx',
      name: 'ETH: Coinbase → OKX',
      path: ['Coinbase: ETH/USDT', 'OKX: ETH/USDT'],
      profit: 2.1,
      risk: 'Medium',
      volume: 'High',
      executionTime: 2000
    },
    {
      id: 'sol-kucoin-binance',
      name: 'SOL: KuCoin → Binance',
      path: ['KuCoin: SOL/USDT', 'Binance: SOL/USDT'],
      profit: 1.8,
      risk: 'High',
      volume: 'Medium',
      executionTime: 2200
    }
  ];

  // Available exchanges with status
  const exchanges = [
    { value: 'binance', label: 'Binance', status: 'connected', fee: 0.1 },
    { value: 'kraken', label: 'Kraken', status: 'connected', fee: 0.16 },
    { value: 'coinbase', label: 'Coinbase', status: 'connected', fee: 0.2 },
    { value: 'okx', label: 'OKX', status: 'connected', fee: 0.1 },
    { value: 'kucoin', label: 'KuCoin', status: 'connected', fee: 0.1 },
    { value: 'huobi', label: 'Huobi', status: 'connected', fee: 0.15 }
  ];

  useEffect(() => {
    setCurrentOpportunities(
      arbitrageType === 'triangular' ? triangularOpportunities : crossExchangeOpportunities
    );
  }, [arbitrageType]);

  const calculateArbitrage = (values = null) => {
    setCalculating(true);
    const formValues = values || form.getFieldsValue();
    const amount = formValues.amount || 0;
    const selectedStrategy = formValues.strategy;
    
    setTimeout(() => {
      if (selectedStrategy && amount > 0) {
        const currentStrategies = arbitrageType === 'triangular' ? triangularOpportunities : crossExchangeOpportunities;
        const selectedPair = currentStrategies.find(p => p.id === selectedStrategy);
        
        if (selectedPair) {
          const baseProfit = (selectedPair.profit / 100) * amount;
          const fees = amount * 0.002;
          const netProfit = baseProfit - fees;
          setEstimatedProfit(netProfit);
        }
      } else {
        setEstimatedProfit(0);
      }
      setCalculating(false);
    }, 800);
  };

  const onValuesChange = (changedValues, allValues) => {
    if (changedValues.amount || changedValues.strategy) {
      calculateArbitrage(allValues);
    }
  };

  const executeArbitrage = async (values) => {
    try {
      setTradingActive(true);
      await new Promise(resolve => setTimeout(resolve, 2000));
      message.success(`Arbitrage executed! Profit: $${estimatedProfit.toFixed(2)}`);
      form.resetFields();
      setEstimatedProfit(0);
    } catch (error) {
      message.error('Arbitrage execution failed. Please try again.');
    } finally {
      setTradingActive(false);
    }
  };

  const onFinish = async (values) => {
    if (estimatedProfit <= 0) {
      message.warning('No profitable arbitrage opportunity found.');
      return;
    }
    await executeArbitrage(values);
  };

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'Low': return 'green';
      case 'Medium': return 'orange';
      case 'High': return 'red';
      default: return 'blue';
    }
  };

  const handleArbitrageTypeChange = (e) => {
    setArbitrageType(e.target.value);
    form.setFieldsValue({ strategy: undefined });
    setEstimatedProfit(0);
  };

  const handleRecalculate = () => {
    const values = form.getFieldsValue();
    if (values.amount && values.strategy) {
      calculateArbitrage(values);
    } else {
      message.info('Please select a strategy and enter amount first');
    }
  };

  const getSelectedStrategy = () => {
    const currentStrategies = arbitrageType === 'triangular' ? triangularOpportunities : crossExchangeOpportunities;
    return currentStrategies.find(p => p.id === form.getFieldValue('strategy'));
  };

  return (
    <div className="manual-trading">
      <Row gutter={[24, 24]}>
        {/* Arbitrage Configuration */}
        <Col xs={24} lg={16}>
          <Card 
            title={
              <Space size="small">
                <ThunderboltOutlined />
                <Text className="card-title-text">Quick Arbitrage</Text>
                <Tag color="green" className="live-badge">
                  LIVE
                </Tag>
              </Space>
            }
            className="arbitrage-form-card"
            extra={
              <div className="trading-status">
                {tradingActive ? (
                  <Tag icon={<PlayCircleOutlined />} color="green">
                    Executing
                  </Tag>
                ) : (
                  <Tag icon={<PauseCircleOutlined />} color="default">
                    Ready
                  </Tag>
                )}
              </div>
            }
          >
            <Form
              form={form}
              layout="vertical"
              onFinish={onFinish}
              onValuesChange={onValuesChange}
            >
              {/* Arbitrage Type Selection */}
              <div className="arbitrage-type-section">
                <Text strong className="section-label">Arbitrage Type</Text>
                <Radio.Group 
                  value={arbitrageType} 
                  onChange={handleArbitrageTypeChange}
                  buttonStyle="solid"
                  className="arbitrage-type-selector"
                >
                  <Radio.Button value="triangular">
                    <SwapOutlined /> Triangular
                  </Radio.Button>
                  <Radio.Button value="cross-exchange">
                    <SwapOutlined /> Cross-Exchange
                  </Radio.Button>
                </Radio.Group>
              </div>

              <Divider />

              {/* Strategy and Amount */}
              <Row gutter={[16, 16]}>
                <Col xs={24} md={12}>
                  <Form.Item
                    label="Select Opportunity"
                    name="strategy"
                    rules={[{ required: true, message: 'Please select arbitrage opportunity' }]}
                  >
                    <Select 
                      placeholder={`Select ${arbitrageType} opportunity`}
                      className="arbitrage-strategy-select"
                      showSearch
                      optionFilterProp="children"
                      dropdownStyle={{ minWidth: '400px' }}
                    >
                      {currentOpportunities.map(opportunity => (
                        <Option key={opportunity.id} value={opportunity.id}>
                          <div className="strategy-option">
                            <Text strong className="strategy-name">{opportunity.name}</Text>
                            <div className="strategy-meta">
                              <Tag color={getRiskColor(opportunity.risk)} size="small">
                                {opportunity.risk}
                              </Tag>
                              <Text className="profit-text" style={{ color: opportunity.profit > 1 ? '#52c41a' : '#faad14' }}>
                                {opportunity.profit}% profit
                              </Text>
                            </div>
                          </div>
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
                
                <Col xs={24} md={12}>
                  <Form.Item
                    label="Investment Amount (USDT)"
                    name="amount"
                    rules={[{ required: true, message: 'Please enter amount' }]}
                  >
                    <InputNumber
                      placeholder="Enter amount in USDT"
                      min={10}
                      max={100000}
                      style={{ width: '100%' }}
                      formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                      parser={value => value.replace(/\$\s?|(,*)/g, '')}
                    />
                  </Form.Item>
                </Col>
              </Row>

              {/* Exchange Selection - Only for Cross-Exchange */}
              {arbitrageType === 'cross-exchange' && (
                <Row gutter={[16, 16]}>
                  <Col xs={24} md={12}>
                    <Form.Item
                      label="Buy Exchange"
                      name="buyExchange"
                      initialValue="binance"
                    >
                      <Select placeholder="Select exchange to buy from">
                        {exchanges.map(exchange => (
                          <Option key={exchange.value} value={exchange.value}>
                            <Space>
                              <span>{exchange.label}</span>
                              <Tag color="green" size="small">{exchange.fee}% fee</Tag>
                            </Space>
                          </Option>
                        ))}
                      </Select>
                    </Form.Item>
                  </Col>
                  
                  <Col xs={24} md={12}>
                    <Form.Item
                      label="Sell Exchange"
                      name="sellExchange"
                      initialValue="kraken"
                    >
                      <Select placeholder="Select exchange to sell on">
                        {exchanges.map(exchange => (
                          <Option key={exchange.value} value={exchange.value}>
                            <Space>
                              <span>{exchange.label}</span>
                              <Tag color="blue" size="small">{exchange.fee}% fee</Tag>
                            </Space>
                          </Option>
                        ))}
                      </Select>
                    </Form.Item>
                  </Col>
                </Row>
              )}

              {/* Profit Calculation */}
              {(form.getFieldValue('amount') && form.getFieldValue('strategy')) && (
                <div className="profit-calculation-section">
                  <Card title="Profit Estimate" className="profit-card">
                    <Row gutter={[16, 16]}>
                      <Col xs={12} md={8}>
                        <Statistic
                          title="Net Profit"
                          value={estimatedProfit}
                          precision={2}
                          prefix="$"
                          valueStyle={{
                            color: estimatedProfit > 0 ? '#52c41a' : '#ff4d4f',
                          }}
                          loading={calculating}
                        />
                      </Col>
                      <Col xs={12} md={8}>
                        <Statistic
                          title="Return %"
                          value={((estimatedProfit / (form.getFieldValue('amount') || 1)) * 100) || 0}
                          precision={3}
                          suffix="%"
                          valueStyle={{
                            color: estimatedProfit > 0 ? '#52c41a' : '#ff4d4f',
                          }}
                        />
                      </Col>
                      <Col xs={24} md={8}>
                        <div className="execution-info">
                          <Text type="secondary">Execution Time</Text>
                          <Text strong>{getSelectedStrategy()?.executionTime}ms</Text>
                          <Progress 
                            percent={75} 
                            size="small" 
                            status="active"
                            strokeColor={{
                              '0%': '#108ee9',
                              '100%': '#87d068',
                            }}
                          />
                        </div>
                      </Col>
                    </Row>
                  </Card>
                </div>
              )}

              {/* Action Buttons */}
              <div className="action-buttons">
                <Space size="middle">
                  <Button 
                    type="primary" 
                    htmlType="submit"
                    icon={<RocketOutlined />}
                    loading={tradingActive}
                    disabled={estimatedProfit <= 0 || calculating || !form.getFieldValue('amount') || !form.getFieldValue('strategy')}
                    className="execute-btn"
                    size="large"
                  >
                    Execute Arbitrage
                  </Button>
                  <Button 
                    icon={<CalculatorOutlined />}
                    onClick={handleRecalculate}
                    loading={calculating}
                    disabled={!form.getFieldValue('amount') || !form.getFieldValue('strategy')}
                  >
                    Recalculate
                  </Button>
                  <Button 
                    icon={<ReloadOutlined />}
                    onClick={() => {
                      form.resetFields();
                      setEstimatedProfit(0);
                    }}
                  >
                    Reset
                  </Button>
                </Space>
              </div>

              {/* Info Alert */}
              {!form.getFieldValue('amount') || !form.getFieldValue('strategy') ? (
                <Alert
                  message="Setup Required"
                  description="Select an arbitrage opportunity and enter investment amount to calculate profits."
                  type="info"
                  showIcon
                  style={{ marginTop: 16 }}
                />
              ) : estimatedProfit <= 0 && (
                <Alert
                  message="Not Profitable"
                  description="This opportunity doesn't show profitable returns with current parameters."
                  type="warning"
                  showIcon
                  style={{ marginTop: 16 }}
                />
              )}
            </Form>
          </Card>
        </Col>

        {/* Arbitrage Info & Status */}
        <Col xs={24} lg={8}>
          <Card 
            title="Opportunity Details"
            className="arbitrage-info-card"
          >
            <div className="info-content">
              {/* Selected Path */}
              <div className="info-section">
                <Text strong>Selected Path:</Text>
                <div className="path-display">
                  {getSelectedStrategy() ? (
                    <Space direction="vertical" size={4} style={{ width: '100%' }}>
                      {getSelectedStrategy().path.map((step, index) => (
                        <div key={index} className="path-step">
                          <Text className="path-text">{step}</Text>
                          {index < getSelectedStrategy().path.length - 1 && (
                            <ArrowRightOutlined className="path-arrow" />
                          )}
                        </div>
                      ))}
                    </Space>
                  ) : (
                    <Text type="secondary" className="no-selection">
                      Select an opportunity to view trading path
                    </Text>
                  )}
                </div>
              </div>

              <Divider />

              {/* Exchange Status */}
              <div className="info-section">
                <Text strong>Exchange Status:</Text>
                <div className="exchange-status">
                  {exchanges.map(exchange => (
                    <div key={exchange.value} className="exchange-item">
                      <Text>{exchange.label}</Text>
                      <Tag color="green" size="small">
                        {exchange.status}
                      </Tag>
                    </div>
                  ))}
                </div>
              </div>

              <Divider />

              {/* Risk Management */}
              <div className="info-section">
                <Text strong>Safety Limits:</Text>
                <div className="risk-items">
                  <div className="risk-item">
                    <Text>Max Slippage</Text>
                    <Tag color="orange">1.0%</Tag>
                  </div>
                  <div className="risk-item">
                    <Text>Min Profit</Text>
                    <Tag color="green">0.3%</Tag>
                  </div>
                  <div className="risk-item">
                    <Text>Timeout</Text>
                    <Tag color="blue">5s</Tag>
                  </div>
                  <div className="risk-item">
                    <Text>Max Investment</Text>
                    <Tag color="purple">$10k</Tag>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default ManualTrading;