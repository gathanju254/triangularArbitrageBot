// frontend/src/components/settings/ExchangeSettings/ExchangeSettings.jsx
import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Switch,
  Select,
  Slider,
  InputNumber,
  Button,
  Typography,
  Alert,
  Space,
  Divider,
  Row,
  Col,
  Tag,
  message
} from 'antd';
import {
  SaveOutlined,
  ReloadOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import { userService } from '../../../services/api/userService';
import './ExchangeSettings.css';

const { Title, Text } = Typography;
const { Option } = Select;

const ExchangeSettings = ({ onSettingsChange }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [userProfile, setUserProfile] = useState(null);

  const EXCHANGE_OPTIONS = [
    { value: 'binance', label: 'Binance', enabled: true },
    { value: 'coinbase', label: 'Coinbase', enabled: false },
    { value: 'kraken', label: 'Kraken', enabled: true },
    { value: 'kucoin', label: 'KuCoin', enabled: false },
    { value: 'okx', label: 'OKX', enabled: true },
    { value: 'huobi', label: 'Huobi', enabled: false },
    { value: 'bybit', label: 'Bybit', enabled: true }
  ];

  useEffect(() => {
    loadUserProfile();
  }, []);

  const loadUserProfile = async () => {
    setLoading(true);
    try {
      const profile = await userService.getUserProfile();
      setUserProfile(profile);
      
      // Set form values from profile
      if (profile?.profile) {
        form.setFieldsValue({
          preferred_exchanges: profile.profile.preferred_exchanges || ['binance', 'kraken'],
          risk_tolerance: profile.profile.risk_tolerance || 'medium',
          max_daily_loss: profile.profile.max_daily_loss || 1000,
          max_position_size: profile.profile.max_position_size || 5000
        });
      }
    } catch (error) {
      message.error('Failed to load user profile: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (values) => {
    setSaving(true);
    try {
      await userService.updateUserProfile({
        profile: values
      });
      message.success('Exchange settings saved successfully');
      onSettingsChange(false);
    } catch (error) {
      message.error('Failed to save settings: ' + error.message);
    } finally {
      setSaving(false);
    }
  };

  const handleValuesChange = () => {
    onSettingsChange(true);
  };

  const riskToleranceMarks = {
    low: 'Low',
    medium: 'Medium',
    high: 'High'
  };

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'low': return 'green';
      case 'medium': return 'orange';
      case 'high': return 'red';
      default: return 'blue';
    }
  };

  return (
    <div className="exchange-settings-container">
      <div className="exchange-settings-header">
        <Title level={3}>Exchange Configuration</Title>
        <Text type="secondary">
          Configure your preferred exchanges and trading parameters
        </Text>
      </div>

      <Alert
        message="Trading Configuration"
        description="These settings affect how the arbitrage bot selects and executes trades across your connected exchanges."
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSave}
        onValuesChange={handleValuesChange}
        disabled={loading}
      >
        <Row gutter={[24, 24]}>
          <Col xs={24} lg={12}>
            <Card title="Preferred Exchanges" className="settings-card">
              <Form.Item
                name="preferred_exchanges"
                label="Active Exchanges"
                tooltip="Select exchanges you want the bot to monitor and trade on"
              >
                <Select
                  mode="multiple"
                  placeholder="Select exchanges"
                  style={{ width: '100%' }}
                >
                  {EXCHANGE_OPTIONS.map(exchange => (
                    <Option 
                      key={exchange.value} 
                      value={exchange.value}
                      disabled={!exchange.enabled}
                    >
                      <Space>
                        {exchange.label}
                        {exchange.enabled ? (
                          <Tag color="green" size="small">Connected</Tag>
                        ) : (
                          <Tag color="red" size="small">No API Key</Tag>
                        )}
                      </Space>
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              <Divider />

              <Text type="secondary">
                <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                Green tags indicate exchanges with valid API keys
              </Text>
            </Card>
          </Col>

          <Col xs={24} lg={12}>
            <Card title="Risk Management" className="settings-card">
              <Form.Item
                name="risk_tolerance"
                label="Risk Tolerance"
                tooltip="Determines how aggressive the trading strategy will be"
              >
                <Select>
                  <Option value="low">
                    <Tag color="green">Low Risk</Tag> - Conservative trading
                  </Option>
                  <Option value="medium">
                    <Tag color="orange">Medium Risk</Tag> - Balanced approach
                  </Option>
                  <Option value="high">
                    <Tag color="red">High Risk</Tag> - Aggressive trading
                  </Option>
                </Select>
              </Form.Item>

              <Form.Item
                name="max_daily_loss"
                label="Maximum Daily Loss ($)"
                tooltip="Maximum amount you're willing to lose in a single day"
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={10}
                  max={10000}
                  step={100}
                  formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                  parser={value => value.replace(/\$\s?|(,*)/g, '')}
                />
              </Form.Item>

              <Form.Item
                name="max_position_size"
                label="Maximum Position Size ($)"
                tooltip="Maximum amount to invest in a single trade"
              >
                <InputNumber
                  style={{ width: '100%' }}
                  min={10}
                  max={50000}
                  step={500}
                  formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                  parser={value => value.replace(/\$\s?|(,*)/g, '')}
                />
              </Form.Item>
            </Card>
          </Col>
        </Row>

        <Card title="Trading Parameters" className="settings-card" style={{ marginTop: 24 }}>
          <Row gutter={[24, 24]}>
            <Col xs={24} md={12}>
              <Form.Item
                name="min_profit_threshold"
                label="Minimum Profit Threshold (%)"
                tooltip="Minimum profit percentage required to execute a trade"
                initialValue={0.5}
              >
                <Slider
                  min={0.1}
                  max={5}
                  step={0.1}
                  marks={{
                    0.1: '0.1%',
                    1: '1%',
                    2: '2%',
                    3: '3%',
                    4: '4%',
                    5: '5%'
                  }}
                />
              </Form.Item>
            </Col>

            <Col xs={24} md={12}>
              <Form.Item
                name="max_slippage"
                label="Maximum Slippage (%)"
                tooltip="Maximum allowed price slippage for trades"
                initialValue={1.0}
              >
                <Slider
                  min={0.1}
                  max={5}
                  step={0.1}
                  marks={{
                    0.1: '0.1%',
                    1: '1%',
                    2: '2%',
                    3: '3%',
                    4: '4%',
                    5: '5%'
                  }}
                />
              </Form.Item>
            </Col>
          </Row>
        </Card>

        <div className="settings-actions" style={{ marginTop: 24, textAlign: 'right' }}>
          <Space>
            <Button 
              icon={<ReloadOutlined />} 
              onClick={loadUserProfile}
              disabled={loading}
            >
              Reload
            </Button>
            <Button 
              type="primary" 
              icon={<SaveOutlined />} 
              htmlType="submit"
              loading={saving}
            >
              Save Settings
            </Button>
          </Space>
        </div>
      </Form>
    </div>
  );
};

export default ExchangeSettings;