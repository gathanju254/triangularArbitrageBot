// frontend/src/components/trading/AutoTrading/StrategyConfig/StrategyConfig.jsx
import React, { useState } from 'react';
import {
  Card,
  Form,
  Input,
  InputNumber,
  Select,
  Switch,
  Slider,
  Button,
  Row,
  Col,
  Divider,
  Tag,
  Alert,
  Space,
  Tabs,
  Collapse,
  Tooltip
} from 'antd';
import {
  SaveOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  DeleteOutlined,
  CopyOutlined,
  InfoCircleOutlined,
  PlusOutlined
} from '@ant-design/icons';
import './StrategyConfig.css';

const { Option } = Select;
const { TabPane } = Tabs;
const { Panel } = Collapse;

const StrategyConfig = () => {
  const [form] = Form.useForm();
  const [activeStrategy, setActiveStrategy] = useState('arbitrage');
  const [strategies, setStrategies] = useState([
    { id: 'arbitrage', name: 'Triangular Arbitrage', status: 'active', type: 'arbitrage' },
    { id: 'mean-reversion', name: 'Mean Reversion', status: 'paused', type: 'statistical' },
    { id: 'momentum', name: 'Momentum Trading', status: 'inactive', type: 'trend' }
  ]);

  const strategyTypes = [
    { value: 'arbitrage', label: 'Arbitrage', description: 'Exploit price differences across exchanges' },
    { value: 'mean-reversion', label: 'Mean Reversion', description: 'Trade based on statistical mean reversion' },
    { value: 'momentum', label: 'Momentum', description: 'Follow market trends and momentum' },
    { value: 'market-making', label: 'Market Making', description: 'Provide liquidity and capture spreads' }
  ];

  const onFinish = (values) => {
    console.log('Strategy configuration saved:', values);
    // Here you would typically save to backend
  };

  const handleStrategyStatusChange = (strategyId, newStatus) => {
    setStrategies(prev => prev.map(strategy => 
      strategy.id === strategyId ? { ...strategy, status: newStatus } : strategy
    ));
  };

  const handleAddStrategy = () => {
    const newStrategy = {
      id: `strategy-${Date.now()}`,
      name: 'New Strategy',
      status: 'inactive',
      type: 'arbitrage'
    };
    setStrategies(prev => [...prev, newStrategy]);
    setActiveStrategy(newStrategy.id);
  };

  const getStatusConfig = (status) => {
    const configs = {
      active: { color: 'green', text: 'Active' },
      paused: { color: 'orange', text: 'Paused' },
      inactive: { color: 'red', text: 'Inactive' }
    };
    return configs[status] || configs.inactive;
  };

  const renderStrategyControls = (strategy) => {
    const statusConfig = getStatusConfig(strategy.status);
    
    return (
      <Space>
        <Tag color={statusConfig.color}>{statusConfig.text}</Tag>
        {strategy.status === 'active' && (
          <Button 
            size="small" 
            icon={<PauseCircleOutlined />}
            onClick={() => handleStrategyStatusChange(strategy.id, 'paused')}
          >
            Pause
          </Button>
        )}
        {strategy.status === 'paused' && (
          <Button 
            size="small" 
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={() => handleStrategyStatusChange(strategy.id, 'active')}
          >
            Resume
          </Button>
        )}
        {strategy.status === 'inactive' && (
          <Button 
            size="small" 
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={() => handleStrategyStatusChange(strategy.id, 'active')}
          >
            Activate
          </Button>
        )}
        <Button size="small" icon={<CopyOutlined />}>
          Clone
        </Button>
        <Button size="small" danger icon={<DeleteOutlined />}>
          Delete
        </Button>
      </Space>
    );
  };

  return (
    <div className="strategy-config">
      <Row gutter={[24, 24]}>
        {/* Strategy List */}
        <Col xs={24} lg={8}>
          <Card 
            title="Strategies" 
            extra={
              <Button 
                type="primary" 
                icon={<PlusOutlined />}
                onClick={handleAddStrategy}
              >
                Add Strategy
              </Button>
            }
            className="strategies-list-card"
          >
            <div className="strategies-list">
              {strategies.map(strategy => (
                <div 
                  key={strategy.id}
                  className={`strategy-item ${activeStrategy === strategy.id ? 'active' : ''}`}
                  onClick={() => setActiveStrategy(strategy.id)}
                >
                  <div className="strategy-info">
                    <div className="strategy-name">{strategy.name}</div>
                    <div className="strategy-type">
                      <Tag>{strategy.type}</Tag>
                    </div>
                  </div>
                  {renderStrategyControls(strategy)}
                </div>
              ))}
            </div>
          </Card>
        </Col>

        {/* Strategy Configuration */}
        <Col xs={24} lg={16}>
          <Card 
            title="Strategy Configuration"
            className="config-card"
            extra={
              <Space>
                <Button icon={<SaveOutlined />} type="primary">
                  Save Configuration
                </Button>
              </Space>
            }
          >
            <Form
              form={form}
              layout="vertical"
              onFinish={onFinish}
              className="strategy-form"
            >
              <Tabs defaultActiveKey="basic">
                <TabPane tab="Basic Settings" key="basic">
                  <Row gutter={[16, 16]}>
                    <Col span={12}>
                      <Form.Item
                        label="Strategy Name"
                        name="name"
                        rules={[{ required: true, message: 'Please enter strategy name' }]}
                      >
                        <Input placeholder="Enter strategy name" />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        label="Strategy Type"
                        name="type"
                        rules={[{ required: true, message: 'Please select strategy type' }]}
                      >
                        <Select placeholder="Select strategy type">
                          {strategyTypes.map(type => (
                            <Option key={type.value} value={type.value}>
                              <div>
                                <div>{type.label}</div>
                                <div style={{ fontSize: '12px', color: '#666' }}>
                                  {type.description}
                                </div>
                              </div>
                            </Option>
                          ))}
                        </Select>
                      </Form.Item>
                    </Col>
                  </Row>

                  <Form.Item
                    label="Description"
                    name="description"
                  >
                    <Input.TextArea 
                      rows={3} 
                      placeholder="Describe your trading strategy..."
                    />
                  </Form.Item>

                  <Row gutter={[16, 16]}>
                    <Col span={12}>
                      <Form.Item
                        label="Base Currency"
                        name="baseCurrency"
                        initialValue="USDT"
                      >
                        <Select>
                          <Option value="USDT">USDT</Option>
                          <Option value="USD">USD</Option>
                          <Option value="BTC">BTC</Option>
                          <Option value="ETH">ETH</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        label="Trading Pairs"
                        name="tradingPairs"
                        initialValue={['BTC/USDT', 'ETH/USDT']}
                      >
                        <Select mode="tags" placeholder="Select trading pairs">
                          <Option value="BTC/USDT">BTC/USDT</Option>
                          <Option value="ETH/USDT">ETH/USDT</Option>
                          <Option value="SOL/USDT">SOL/USDT</Option>
                          <Option value="ADA/USDT">ADA/USDT</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                  </Row>
                </TabPane>

                <TabPane tab="Risk Management" key="risk">
                  <Alert
                    message="Risk Management Settings"
                    description="Configure risk parameters to protect your capital"
                    type="info"
                    showIcon
                    style={{ marginBottom: 16 }}
                  />
                  
                  <Row gutter={[16, 16]}>
                    <Col span={12}>
                      <Form.Item
                        label={
                          <span>
                            Maximum Position Size 
                            <Tooltip title="Maximum amount to invest in a single trade">
                              <InfoCircleOutlined style={{ marginLeft: 8 }} />
                            </Tooltip>
                          </span>
                        }
                        name="maxPositionSize"
                        initialValue={1000}
                      >
                        <InputNumber
                          style={{ width: '100%' }}
                          min={10}
                          max={10000}
                          formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                          parser={value => value.replace(/\$\s?|(,*)/g, '')}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        label="Daily Loss Limit"
                        name="dailyLossLimit"
                        initialValue={500}
                      >
                        <InputNumber
                          style={{ width: '100%' }}
                          min={10}
                          max={5000}
                          formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                          parser={value => value.replace(/\$\s?|(,*)/g, '')}
                        />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Form.Item
                    label="Maximum Drawdown"
                    name="maxDrawdown"
                    initialValue={15}
                  >
                    <Slider
                      min={1}
                      max={50}
                      marks={{
                        1: '1%',
                        25: '25%',
                        50: '50%'
                      }}
                    />
                  </Form.Item>

                  <Row gutter={[16, 16]}>
                    <Col span={12}>
                      <Form.Item
                        label="Stop Loss"
                        name="stopLoss"
                        initialValue={5}
                      >
                        <InputNumber
                          style={{ width: '100%' }}
                          min={0.1}
                          max={20}
                          step={0.1}
                          formatter={value => `${value}%`}
                          parser={value => value.replace('%', '')}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        label="Take Profit"
                        name="takeProfit"
                        initialValue={10}
                      >
                        <InputNumber
                          style={{ width: '100%' }}
                          min={0.1}
                          max={50}
                          step={0.1}
                          formatter={value => `${value}%`}
                          parser={value => value.replace('%', '')}
                        />
                      </Form.Item>
                    </Col>
                  </Row>
                </TabPane>

                <TabPane tab="Trading Parameters" key="trading">
                  <Row gutter={[16, 16]}>
                    <Col span={12}>
                      <Form.Item
                        label="Minimum Profit Threshold"
                        name="minProfitThreshold"
                        initialValue={0.3}
                      >
                        <InputNumber
                          style={{ width: '100%' }}
                          min={0.1}
                          max={5}
                          step={0.1}
                          formatter={value => `${value}%`}
                          parser={value => value.replace('%', '')}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        label="Maximum Slippage"
                        name="maxSlippage"
                        initialValue={0.5}
                      >
                        <InputNumber
                          style={{ width: '100%' }}
                          min={0.1}
                          max={5}
                          step={0.1}
                          formatter={value => `${value}%`}
                          parser={value => value.replace('%', '')}
                        />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Row gutter={[16, 16]}>
                    <Col span={12}>
                      <Form.Item
                        label="Order Size"
                        name="orderSize"
                        initialValue={100}
                      >
                        <InputNumber
                          style={{ width: '100%' }}
                          min={10}
                          max={1000}
                          formatter={value => `$ ${value}`}
                          parser={value => value.replace('$ ', '')}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item
                        label="Maximum Orders per Hour"
                        name="maxOrdersPerHour"
                        initialValue={10}
                      >
                        <InputNumber
                          style={{ width: '100%' }}
                          min={1}
                          max={100}
                        />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Form.Item
                    label="Trading Hours"
                    name="tradingHours"
                  >
                    <Select mode="multiple" placeholder="Select trading hours">
                      <Option value="00:00-06:00">Night (00:00-06:00)</Option>
                      <Option value="06:00-12:00">Morning (06:00-12:00)</Option>
                      <Option value="12:00-18:00">Afternoon (12:00-18:00)</Option>
                      <Option value="18:00-24:00">Evening (18:00-24:00)</Option>
                    </Select>
                  </Form.Item>
                </TabPane>

                <TabPane tab="Advanced" key="advanced">
                  <Collapse ghost>
                    <Panel header="API Settings" key="api">
                      <Form.Item
                        label="API Rate Limit"
                        name="apiRateLimit"
                        initialValue={60}
                      >
                        <InputNumber
                          style={{ width: '100%' }}
                          min={10}
                          max={300}
                          formatter={value => `${value} requests/min`}
                        />
                      </Form.Item>
                    </Panel>
                    <Panel header="Execution Settings" key="execution">
                      <Form.Item
                        label="Order Type"
                        name="orderType"
                        initialValue="market"
                      >
                        <Select>
                          <Option value="market">Market Order</Option>
                          <Option value="limit">Limit Order</Option>
                          <Option value="stop">Stop Order</Option>
                        </Select>
                      </Form.Item>
                    </Panel>
                    <Panel header="Monitoring" key="monitoring">
                      <Form.Item
                        label="Health Check Interval"
                        name="healthCheckInterval"
                        initialValue={30}
                      >
                        <InputNumber
                          style={{ width: '100%' }}
                          min={5}
                          max={300}
                          formatter={value => `${value} seconds`}
                        />
                      </Form.Item>
                    </Panel>
                  </Collapse>
                </TabPane>
              </Tabs>

              <Divider />

              <Form.Item>
                <Space>
                  <Button type="primary" htmlType="submit" icon={<SaveOutlined />}>
                    Save Configuration
                  </Button>
                  <Button>Test Strategy</Button>
                  <Button type="dashed">Reset to Defaults</Button>
                </Space>
              </Form.Item>
            </Form>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default StrategyConfig;