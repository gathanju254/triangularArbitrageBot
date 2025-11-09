// frontend/src/components/settings/TradingConfig/TradingConfig.jsx
import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Switch,
  Select,
  InputNumber,
  Button,
  Typography,
  Alert,
  Space,
  Divider,
  Row,
  Col,
  Tag,
  message,
  Collapse,
  Slider
} from 'antd';
import {
  SaveOutlined,
  RocketOutlined,
  SafetyOutlined,
  NotificationOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { settingsService } from '../../../services/api/settingsService';
import './TradingConfig.css';

const { Title, Text } = Typography;
const { Option } = Select;
const { Panel } = Collapse;

const TradingConfig = ({ onSettingsChange }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadTradingConfig();
  }, []);

  const loadTradingConfig = async () => {
    setLoading(true);
    try {
      const config = await settingsService.getTradingConfig();
      if (config) {
        form.setFieldsValue({
          auto_trading: config.auto_trading || false,
          trading_mode: config.trading_mode || 'manual',
          max_concurrent_trades: config.max_concurrent_trades || 3,
          min_trade_amount: config.min_trade_amount || 10,
          stop_loss_enabled: config.stop_loss_enabled !== false, // default true
          take_profit_enabled: config.take_profit_enabled !== false,
          stop_loss_percent: config.stop_loss_percent || 2,
          take_profit_percent: config.take_profit_percent || 5,
          email_notifications: config.email_notifications !== false,
          push_notifications: config.push_notifications || false,
          trading_alerts: config.trading_alerts !== false,
          risk_alerts: config.risk_alerts !== false,
          slippage_tolerance: config.slippage_tolerance || 0.1,
        });
      }
    } catch (error) {
      console.error('Failed to load trading configuration:', error);
      message.error('Failed to load trading configuration: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (values) => {
    setSaving(true);
    try {
      await settingsService.updateTradingConfig(values);
      message.success('Trading configuration saved successfully');
      onSettingsChange(false);
    } catch (error) {
      console.error('Failed to save trading configuration:', error);
      message.error('Failed to save configuration: ' + error.message);
    } finally {
      setSaving(false);
    }
  };

  const handleValuesChange = () => {
    onSettingsChange(true);
  };

  const handleReset = () => {
    form.resetFields();
    onSettingsChange(true);
  };

  return (
    <div className="trading-config-container">
      <div className="trading-config-header">
        <Title level={3}>Trading Configuration</Title>
        <Text type="secondary">
          Configure your trading strategies, risk management, and notification preferences
        </Text>
      </div>

      <Alert
        message="Configuration Impact"
        description="Changes to these settings will affect how the arbitrage bot operates and manages your trades."
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
        initialValues={{
          auto_trading: false,
          trading_mode: 'manual',
          max_concurrent_trades: 3,
          min_trade_amount: 10,
          stop_loss_enabled: true,
          take_profit_enabled: true,
          stop_loss_percent: 2,
          take_profit_percent: 5,
          email_notifications: true,
          push_notifications: false,
          trading_alerts: true,
          risk_alerts: true,
          slippage_tolerance: 0.1,
        }}
      >
        <Collapse defaultActiveKey={['trading-mode', 'risk-management', 'notifications']} ghost>
          {/* Trading Mode Panel */}
          <Panel 
            header={
              <Space>
                <RocketOutlined />
                <Text strong>Trading Mode & Strategy</Text>
              </Space>
            } 
            key="trading-mode"
          >
            <Card className="config-section-card">
              <Row gutter={[24, 16]}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="auto_trading"
                    label="Auto Trading"
                    valuePropName="checked"
                    tooltip="Enable fully automated trading without manual confirmation"
                  >
                    <Switch 
                      checkedChildren="Enabled" 
                      unCheckedChildren="Disabled" 
                    />
                  </Form.Item>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    name="trading_mode"
                    label="Trading Mode"
                    tooltip="Select how trades are executed"
                  >
                    <Select>
                      <Option value="manual">Manual Confirmation</Option>
                      <Option value="semi-auto">Semi-Auto (Confirm large trades)</Option>
                      <Option value="full-auto">Full Auto (No confirmation)</Option>
                    </Select>
                  </Form.Item>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    name="max_concurrent_trades"
                    label="Max Concurrent Trades"
                    tooltip="Maximum number of trades to execute simultaneously"
                    rules={[{ required: true, message: 'Please enter maximum concurrent trades' }]}
                  >
                    <InputNumber
                      min={1}
                      max={10}
                      style={{ width: '100%' }}
                    />
                  </Form.Item>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    name="min_trade_amount"
                    label="Minimum Trade Amount ($)"
                    tooltip="Minimum amount for a single trade"
                    rules={[{ required: true, message: 'Please enter minimum trade amount' }]}
                  >
                    <InputNumber
                      min={1}
                      max={10000}
                      style={{ width: '100%' }}
                      formatter={value => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                      parser={value => value.replace(/\$\s?|(,*)/g, '')}
                    />
                  </Form.Item>
                </Col>

                <Col xs={24}>
                  <Form.Item
                    name="slippage_tolerance"
                    label="Slippage Tolerance (%)"
                    tooltip="Maximum allowed price slippage for trades"
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
          </Panel>

          {/* Risk Management Panel */}
          <Panel 
            header={
              <Space>
                <SafetyOutlined />
                <Text strong>Risk Management</Text>
              </Space>
            } 
            key="risk-management"
          >
            <Card className="config-section-card">
              <Row gutter={[24, 16]}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="stop_loss_enabled"
                    label="Stop Loss"
                    valuePropName="checked"
                    tooltip="Automatically sell if losses exceed threshold"
                  >
                    <Switch 
                      checkedChildren="Enabled" 
                      unCheckedChildren="Disabled" 
                    />
                  </Form.Item>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    name="take_profit_enabled"
                    label="Take Profit"
                    valuePropName="checked"
                    tooltip="Automatically take profits at target percentage"
                  >
                    <Switch 
                      checkedChildren="Enabled" 
                      unCheckedChildren="Disabled" 
                    />
                  </Form.Item>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    name="stop_loss_percent"
                    label="Stop Loss (%)"
                    tooltip="Sell if price drops by this percentage"
                    rules={[{ required: true, message: 'Please enter stop loss percentage' }]}
                  >
                    <InputNumber
                      min={0.1}
                      max={50}
                      step={0.1}
                      style={{ width: '100%' }}
                      formatter={value => `${value}%`}
                      parser={value => value.replace('%', '')}
                    />
                  </Form.Item>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    name="take_profit_percent"
                    label="Take Profit (%)"
                    tooltip="Sell when profit reaches this percentage"
                    rules={[{ required: true, message: 'Please enter take profit percentage' }]}
                  >
                    <InputNumber
                      min={0.1}
                      max={100}
                      step={0.1}
                      style={{ width: '100%' }}
                      formatter={value => `${value}%`}
                      parser={value => value.replace('%', '')}
                    />
                  </Form.Item>
                </Col>
              </Row>
            </Card>
          </Panel>

          {/* Notifications Panel */}
          <Panel 
            header={
              <Space>
                <NotificationOutlined />
                <Text strong>Notifications & Alerts</Text>
              </Space>
            } 
            key="notifications"
          >
            <Card className="config-section-card">
              <Row gutter={[24, 16]}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="email_notifications"
                    label="Email Notifications"
                    valuePropName="checked"
                    tooltip="Receive trade notifications via email"
                  >
                    <Switch 
                      checkedChildren="Enabled" 
                      unCheckedChildren="Disabled" 
                    />
                  </Form.Item>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    name="push_notifications"
                    label="Push Notifications"
                    valuePropName="checked"
                    tooltip="Receive browser push notifications"
                  >
                    <Switch 
                      checkedChildren="Enabled" 
                      unCheckedChildren="Disabled" 
                    />
                  </Form.Item>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    name="trading_alerts"
                    label="Trading Alerts"
                    valuePropName="checked"
                    tooltip="Alert for new trading opportunities"
                  >
                    <Switch 
                      checkedChildren="Enabled" 
                      unCheckedChildren="Disabled" 
                    />
                  </Form.Item>
                </Col>

                <Col xs={24} md={12}>
                  <Form.Item
                    name="risk_alerts"
                    label="Risk Alerts"
                    valuePropName="checked"
                    tooltip="Alert for risk management events"
                  >
                    <Switch 
                      checkedChildren="Enabled" 
                      unCheckedChildren="Disabled" 
                    />
                  </Form.Item>
                </Col>
              </Row>
            </Card>
          </Panel>
        </Collapse>

        <Divider />

        <div className="config-actions" style={{ textAlign: 'right', marginTop: 24 }}>
          <Space>
            <Button 
              icon={<ReloadOutlined />}
              onClick={loadTradingConfig}
              disabled={loading}
            >
              Reload
            </Button>
            <Button 
              onClick={handleReset}
              disabled={loading}
            >
              Reset to Defaults
            </Button>
            <Button 
              type="primary" 
              icon={<SaveOutlined />} 
              htmlType="submit"
              loading={saving}
              size="large"
            >
              Save Configuration
            </Button>
          </Space>
        </div>
      </Form>
    </div>
  );
};

export default TradingConfig;