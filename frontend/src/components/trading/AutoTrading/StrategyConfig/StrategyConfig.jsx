// frontend/src/components/trading/AutoTrading/StrategyConfig/StrategyConfig.jsx
import React, { useState } from 'react';
import {
  Card,
  Form,
  InputNumber,
  Select,
  Switch,
  Slider,
  Button,
  Row,
  Col,
  Alert,
  Space,
  Tabs,
  Typography,
  Divider
} from 'antd';
import {
  SaveOutlined,
  ThunderboltOutlined,
  SafetyOutlined
} from '@ant-design/icons';
import './StrategyConfig.css';

const { Option } = Select;
const { TabPane } = Tabs;
const { Text, Title } = Typography;

const StrategyConfig = () => {
  const [form] = Form.useForm();
  const [activeTab, setActiveTab] = useState('triangular');

  // Available exchanges
  const availableExchanges = [
    { id: 'binance', name: 'Binance', status: 'connected' },
    { id: 'kraken', name: 'Kraken', status: 'connected' },
    { id: 'kucoin', name: 'KuCoin', status: 'connected' },
    { id: 'coinbase', name: 'Coinbase', status: 'disconnected' },
    { id: 'huobi', name: 'Huobi', status: 'connected' },
    { id: 'okx', name: 'OKX', status: 'connected' }
  ];

  // Popular triangular arbitrage pairs
  const triangularPairs = [
    'BTC/USDT → ETH/BTC → ETH/USDT',
    'ETH/USDT → SOL/ETH → SOL/USDT',
    'ADA/USDT → XRP/ADA → XRP/USDT',
    'DOT/USDT → LINK/DOT → LINK/USDT',
    'BNB/USDT → ADA/BNB → ADA/USDT'
  ];

  const onFinish = (values) => {
    console.log('Arbitrage strategy configuration saved:', values);
    // Save to backend
  };

  const renderTriangularConfig = () => (
    <>
      <Alert
        message="Triangular Arbitrage"
        description="Quick internal trades between three currency pairs on the same exchange"
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />
      
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Form.Item
            label="Min Profit Threshold"
            name="triangularMinProfit"
            tooltip="Minimum profit percentage to execute triangular arbitrage"
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
            label="Max Trade Size ($)"
            name="triangularMaxSize"
          >
            <InputNumber
              style={{ width: '100%' }}
              min={10}
              max={5000}
              step={100}
              formatter={value => `$ ${value}`}
              parser={value => value.replace('$ ', '')}
            />
          </Form.Item>
        </Col>
      </Row>

      <Form.Item
        label="Arbitrage Pairs"
        name="triangularPairs"
        tooltip="Select currency pairs for triangular arbitrage"
      >
        <Select mode="multiple" placeholder="Choose arbitrage pairs">
          {triangularPairs.map(pair => (
            <Option key={pair} value={pair}>
              {pair}
            </Option>
          ))}
        </Select>
      </Form.Item>

      <Form.Item
        label="Execution Speed"
        name="triangularSpeed"
        initialValue={2}
      >
        <Slider
          min={1}
          max={3}
          marks={{
            1: 'Safe',
            2: 'Balanced', 
            3: 'Fast'
          }}
        />
      </Form.Item>
    </>
  );

  const renderCrossExchangeConfig = () => (
    <>
      <Alert
        message="Cross-Exchange Arbitrage"
        description="Buy low on one exchange, sell high on another"
        type="warning"
        showIcon
        style={{ marginBottom: 16 }}
      />
      
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Form.Item
            label="Min Profit Threshold"
            name="crossMinProfit"
            tooltip="Minimum profit percentage for cross-exchange arbitrage"
          >
            <InputNumber
              style={{ width: '100%' }}
              min={0.5}
              max={10}
              step={0.5}
              formatter={value => `${value}%`}
              parser={value => value.replace('%', '')}
            />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            label="Max Trade Size ($)"
            name="crossMaxSize"
          >
            <InputNumber
              style={{ width: '100%' }}
              min={50}
              max={10000}
              step={500}
              formatter={value => `$ ${value}`}
              parser={value => value.replace('$ ', '')}
            />
          </Form.Item>
        </Col>
      </Row>

      <Form.Item
        label="Buy Exchanges"
        name="buyExchanges"
        tooltip="Exchanges to monitor for buying opportunities"
      >
        <Select mode="multiple" placeholder="Select buy exchanges">
          {availableExchanges.map(exchange => (
            <Option key={exchange.id} value={exchange.id}>
              {exchange.name}
            </Option>
          ))}
        </Select>
      </Form.Item>

      <Form.Item
        label="Sell Exchanges"
        name="sellExchanges"
        tooltip="Exchanges to monitor for selling opportunities"
      >
        <Select mode="multiple" placeholder="Select sell exchanges">
          {availableExchanges.map(exchange => (
            <Option key={exchange.id} value={exchange.id}>
              {exchange.name}
            </Option>
          ))}
        </Select>
      </Form.Item>
    </>
  );

  const renderRiskManagement = () => (
    <>
      <Alert
        message="Risk Management"
        description="Protect your capital with these safety settings"
        type="error"
        showIcon
        style={{ marginBottom: 16 }}
      />
      
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Form.Item
            label="Daily Loss Limit ($)"
            name="dailyLossLimit"
          >
            <InputNumber
              style={{ width: '100%' }}
              min={10}
              max={2000}
              step={50}
              formatter={value => `$ ${value}`}
              parser={value => value.replace('$ ', '')}
            />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            label="Max Concurrent Trades"
            name="maxConcurrentTrades"
          >
            <InputNumber
              style={{ width: '100%' }}
              min={1}
              max={10}
            />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Form.Item
            label="Max Slippage %"
            name="maxSlippage"
          >
            <InputNumber
              style={{ width: '100%' }}
              min={0.1}
              max={2}
              step={0.1}
              formatter={value => `${value}%`}
              parser={value => value.replace('%', '')}
            />
          </Form.Item>
        </Col>
        <Col span={12}>
          <Form.Item
            label="Cooldown (seconds)"
            name="cooldown"
            tooltip="Wait time between trades"
          >
            <InputNumber
              style={{ width: '100%' }}
              min={1}
              max={60}
            />
          </Form.Item>
        </Col>
      </Row>

      <Form.Item
        label="Circuit Breaker"
        name="circuitBreaker"
        valuePropName="checked"
        tooltip="Automatically stop trading if losses exceed threshold"
      >
        <Switch checkedChildren="Enabled" unCheckedChildren="Disabled" />
      </Form.Item>
    </>
  );

  return (
    <div className="strategy-config">
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        className="strategy-form"
        initialValues={{
          triangularMinProfit: 0.5,
          triangularMaxSize: 1000,
          triangularSpeed: 2,
          triangularPairs: triangularPairs.slice(0, 2),
          
          crossMinProfit: 1.5,
          crossMaxSize: 2000,
          buyExchanges: ['binance', 'kucoin'],
          sellExchanges: ['kraken', 'okx'],
          
          dailyLossLimit: 200,
          maxConcurrentTrades: 3,
          maxSlippage: 0.3,
          cooldown: 5,
          circuitBreaker: true
        }}
      >
        <Card 
          title={
            <Space>
              <ThunderboltOutlined />
              <span>Arbitrage Strategy Configuration</span>
            </Space>
          }
          className="config-card"
          extra={
            <Button icon={<SaveOutlined />} type="primary" htmlType="submit">
              Save Configuration
            </Button>
          }
        >
          <Tabs 
            activeKey={activeTab} 
            onChange={setActiveTab}
            type="card"
          >
            <TabPane 
              tab={
                <Space>
                  <ThunderboltOutlined />
                  Triangular Arbitrage
                </Space>
              } 
              key="triangular"
            >
              {renderTriangularConfig()}
            </TabPane>

            <TabPane 
              tab={
                <Space>
                  <ThunderboltOutlined />
                  Cross-Exchange
                </Space>
              } 
              key="cross"
            >
              {renderCrossExchangeConfig()}
            </TabPane>

            <TabPane 
              tab={
                <Space>
                  <SafetyOutlined />
                  Risk Management
                </Space>
              } 
              key="risk"
            >
              {renderRiskManagement()}
            </TabPane>
          </Tabs>

          <Divider />
          
          <div className="quick-stats">
            <Title level={5}>Active Exchanges</Title>
            <Space wrap>
              {availableExchanges.filter(e => e.status === 'connected').map(exchange => (
                <Text key={exchange.id} type="success">
                  {exchange.name}
                </Text>
              ))}
            </Space>
          </div>
        </Card>
      </Form>
    </div>
  );
};

export default StrategyConfig;