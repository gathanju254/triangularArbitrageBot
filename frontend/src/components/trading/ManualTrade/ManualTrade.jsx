// frontend/src/components/trading/ManualTrade/ManualTrade.jsx
import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  Select, 
  Button, 
  InputNumber, 
  message, 
  Row, 
  Col,
  Divider,
  Alert,
  Statistic
} from 'antd';
import { 
  DollarOutlined, 
  ShoppingCartOutlined, 
  ShoppingOutlined,
  InfoCircleOutlined 
} from '@ant-design/icons';
import { tradingService } from '../../../services/api/tradingService';
import './ManualTrade.css';

const { Option } = Select;

const ManualTrade = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [orderType, setOrderType] = useState('market');
  const [estimatedCost, setEstimatedCost] = useState(0);
  const [availableExchanges, setAvailableExchanges] = useState([]);
  const [exchangeInfo, setExchangeInfo] = useState(null);

  // Load available exchanges on component mount
  useEffect(() => {
    loadExchangeInfo();
  }, []);

  const loadExchangeInfo = async () => {
    try {
      // Mock exchange data - in real app, fetch from API
      const exchanges = [
        { id: 1, name: 'Binance', status: 'online', fees: 0.1 },
        { id: 2, name: 'KuCoin', status: 'online', fees: 0.1 },
        { id: 3, name: 'Coinbase', status: 'online', fees: 0.5 }
      ];
      setAvailableExchanges(exchanges);
    } catch (error) {
      console.error('Error loading exchange info:', error);
    }
  };

  // Calculate estimated cost when amount or price changes
  const calculateEstimatedCost = (amount, price, side, orderType) => {
    if (!amount || !price) return 0;
    
    const baseCost = amount * price;
    if (orderType === 'market') {
      // Market orders might have slight price variation
      return side === 'buy' ? baseCost * 1.002 : baseCost * 0.998;
    }
    return baseCost;
  };

  const onFormValuesChange = (changedValues, allValues) => {
    if (changedValues.orderType) {
      setOrderType(changedValues.orderType);
    }

    // Calculate estimated cost
    if (allValues.amount && allValues.price && allValues.side && allValues.orderType) {
      const cost = calculateEstimatedCost(
        allValues.amount, 
        allValues.price, 
        allValues.side, 
        allValues.orderType
      );
      setEstimatedCost(cost);
    }

    // Reset price field when switching to market orders
    if (changedValues.orderType === 'market') {
      form.setFieldsValue({ price: undefined });
    }
  };

  const onFinish = async (values) => {
    setLoading(true);
    try {
      // Format data for backend
      const tradeData = {
        symbol: values.symbol,
        side: values.side,
        amount: values.amount,
        exchange: values.exchange || 1, // Use selected exchange or default
        order_type: values.orderType
      };

      // Add price for limit orders
      if (values.orderType === 'limit' && values.price) {
        tradeData.price = values.price;
      }

      console.log('Placing trade:', tradeData);
      
      let result;
      if (values.orderType === 'limit') {
        result = await tradingService.placeLimitOrder(tradeData);
      } else {
        result = await tradingService.placeManualTrade(tradeData);
      }

      if (result.success) {
        message.success(result.message || 'Trade placed successfully!');
        form.resetFields();
        setEstimatedCost(0);
      } else {
        message.error(result.message || 'Failed to place trade');
      }
    } catch (error) {
      console.error('Trade execution error:', error);
      const errorMessage = error.response?.data?.error || 
                          error.response?.data?.message || 
                          error.message || 
                          'Failed to place trade';
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const quickAmounts = [100, 500, 1000, 5000];

  const handleQuickAmount = (amount) => {
    const currentPrice = form.getFieldValue('price');
    if (currentPrice && amount) {
      const calculatedAmount = amount / currentPrice;
      form.setFieldsValue({ amount: parseFloat(calculatedAmount.toFixed(8)) });
    }
  };

  return (
    <Card 
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <ShoppingCartOutlined />
          <span>Manual Trading</span>
        </div>
      } 
      className="manual-trade"
      extra={
        <Button 
          type="link" 
          icon={<InfoCircleOutlined />}
          onClick={() => message.info('Place manual buy/sell orders on supported exchanges')}
        >
          Help
        </Button>
      }
    >
      <Alert
        message="Manual Trading"
        description="Place instant buy or sell orders. Market orders execute immediately at current price, limit orders at your specified price."
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
        onValuesChange={onFormValuesChange}
        initialValues={{
          orderType: 'market',
          side: 'buy',
          exchange: 1
        }}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="symbol"
              label="Trading Pair"
              rules={[{ required: true, message: 'Please select trading pair' }]}
            >
              <Select placeholder="Select trading pair" size="large">
                <Option value="BTC/USDT">BTC/USDT</Option>
                <Option value="ETH/USDT">ETH/USDT</Option>
                <Option value="ADA/USDT">ADA/USDT</Option>
                <Option value="SOL/USDT">SOL/USDT</Option>
                <Option value="DOT/USDT">DOT/USDT</Option>
                <Option value="BNB/USDT">BNB/USDT</Option>
                <Option value="XRP/USDT">XRP/USDT</Option>
              </Select>
            </Form.Item>
          </Col>

          <Col span={12}>
            <Form.Item
              name="exchange"
              label="Exchange"
              rules={[{ required: true, message: 'Please select exchange' }]}
            >
              <Select placeholder="Select exchange" size="large">
                {availableExchanges.map(exchange => (
                  <Option key={exchange.id} value={exchange.id}>
                    {exchange.name} ({exchange.fees}% fees)
                  </Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="side"
              label="Order Side"
              rules={[{ required: true, message: 'Please select side' }]}
            >
              <Select size="large">
                <Option value="buy">
                  <span style={{ color: '#52c41a' }}>
                    <ShoppingCartOutlined /> Buy
                  </span>
                </Option>
                <Option value="sell">
                  <span style={{ color: '#ff4d4f' }}>
                    <ShoppingOutlined /> Sell
                  </span>
                </Option>
              </Select>
            </Form.Item>
          </Col>

          <Col span={12}>
            <Form.Item
              name="orderType"
              label="Order Type"
              rules={[{ required: true, message: 'Please select order type' }]}
            >
              <Select size="large">
                <Option value="market">Market Order (Instant)</Option>
                <Option value="limit">Limit Order (Price Specific)</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="amount"
              label="Amount (Crypto)"
              rules={[{ required: true, message: 'Please enter amount' }]}
              extra="Enter the cryptocurrency amount you want to buy/sell"
            >
              <InputNumber
                style={{ width: '100%' }}
                min={0.00000001}
                step={0.00000001}
                precision={8}
                placeholder="0.00000000"
                size="large"
                addonAfter={
                  <Form.Item name="amount" noStyle>
                    <Select style={{ width: 80 }} defaultValue="crypto" disabled>
                      <Option value="crypto">Units</Option>
                    </Select>
                  </Form.Item>
                }
              />
            </Form.Item>

            {/* Quick Amount Buttons */}
            <div style={{ marginBottom: 16, textAlign: 'center' }}>
              <span style={{ marginRight: 8, fontSize: 12, color: '#666' }}>Quick USD:</span>
              {quickAmounts.map(amount => (
                <Button
                  key={amount}
                  size="small"
                  type="dashed"
                  style={{ margin: '0 4px 4px 0' }}
                  onClick={() => handleQuickAmount(amount)}
                >
                  ${amount}
                </Button>
              ))}
            </div>
          </Col>

          <Col span={12}>
            <Form.Item
              name="price"
              label={`Price (USD) ${orderType === 'market' ? '- Market Price' : ''}`}
              dependencies={['orderType']}
              rules={[
                ({ getFieldValue }) => ({
                  required: getFieldValue('orderType') === 'limit',
                  message: 'Price is required for limit orders',
                }),
              ]}
              extra={orderType === 'market' ? 'Market orders use current best price' : 'Set your desired execution price'}
            >
              <InputNumber
                style={{ width: '100%' }}
                min={0.00000001}
                step={0.00000001}
                precision={8}
                placeholder={orderType === 'market' ? 'Market Price' : '0.00000000'}
                size="large"
                disabled={orderType === 'market'}
                addonAfter={<DollarOutlined />}
              />
            </Form.Item>
          </Col>
        </Row>

        {/* Estimated Cost Display */}
        {estimatedCost > 0 && (
          <div style={{ marginBottom: 16, padding: '12px 16px', background: '#f0f8ff', borderRadius: 6 }}>
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="Estimated Cost"
                  value={estimatedCost}
                  precision={2}
                  prefix="$"
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="Order Type"
                  value={orderType === 'market' ? 'Market' : 'Limit'}
                  valueStyle={{ color: orderType === 'market' ? '#52c41a' : '#1890ff' }}
                />
              </Col>
            </Row>
          </div>
        )}

        <Divider />

        <Form.Item>
          <Button 
            type="primary" 
            htmlType="submit" 
            loading={loading} 
            block 
            size="large"
            style={{
              height: 48,
              fontSize: 16,
              fontWeight: 'bold',
              background: 'linear-gradient(135deg, #1890ff 0%, #096dd9 100%)',
              border: 'none'
            }}
          >
            {loading ? 'Placing Order...' : `Place ${orderType === 'market' ? 'Market' : 'Limit'} Order`}
          </Button>
        </Form.Item>

        {/* Order Summary */}
        <Alert
          message="Order Summary"
          description={
            <div>
              <p><strong>Market Orders:</strong> Execute immediately at best available price</p>
              <p><strong>Limit Orders:</strong> Execute only at your specified price or better</p>
              <p><strong>Fees:</strong> 0.1% per trade (varies by exchange)</p>
            </div>
          }
          type="warning"
          showIcon
        />
      </Form>
    </Card>
  );
};

export default ManualTrade;