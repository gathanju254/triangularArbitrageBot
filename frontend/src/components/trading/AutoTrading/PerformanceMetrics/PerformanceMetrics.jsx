// frontend/src/components/trading/AutoTrading/AutoTrading.jsx
import React, { useState, useEffect } from 'react';
import { Card, Switch, Slider, InputNumber, Row, Col, Statistic, Alert, message } from 'antd';
import { PlayCircleOutlined, PauseCircleOutlined } from '@ant-design/icons';
import { tradingService } from '../../../services/api/tradingService';
import './AutoTrading.css';

const AutoTrading = () => {
  const [isActive, setIsActive] = useState(false);
  const [minProfit, setMinProfit] = useState(0.5);
  const [maxTradeSize, setMaxTradeSize] = useState(1000);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(false);
  const [lastAction, setLastAction] = useState(null);

  // Load initial auto trading status on component mount
  useEffect(() => {
    const loadAutoTradingStatus = async () => {
      try {
        const status = await tradingService.getAutoTradingStatus();
        setIsActive(status.active);
        if (status.settings) {
          setMinProfit(status.settings.min_profit_threshold || 0.5);
          setMaxTradeSize(status.settings.max_trade_size || 1000);
        }
        // Load stats if active
        if (status.active && status.activity) {
          setStats(status.activity);
        }
      } catch (error) {
        console.error('Failed to load auto trading status:', error);
        message.error('Failed to load auto trading status');
      }
    };

    loadAutoTradingStatus();
  }, []);

  const toggleAutoTrading = async (checked) => {
    setLoading(true);
    setLastAction(checked ? 'start' : 'stop');
    
    try {
      let result;
      if (checked) {
        // Start auto trading with simplified data
        result = await tradingService.startAutoTrading({ 
          min_profit_threshold: minProfit, 
          max_trade_size: maxTradeSize
        });
      } else {
        // Stop auto trading  
        result = await tradingService.stopAutoTrading();
      }
      
      if (result.success || result.auto_trading !== undefined) {
        setIsActive(checked);
        message.success(`Auto trading ${checked ? 'started' : 'stopped'} successfully`);
        
        // Refresh status to get updated stats
        const status = await tradingService.getAutoTradingStatus();
        if (status.activity) {
          setStats(status.activity);
        }
      } else {
        throw new Error(result.message || `Failed to ${checked ? 'start' : 'stop'} auto trading`);
      }
    } catch (error) {
      console.error('Auto trading operation failed:', error);
      // Revert state on error
      setIsActive(!checked);
      message.error(`Auto trading operation failed: ${error.message}`);
    } finally {
      setLoading(false);
      setLastAction(null);
    }
  };

  // Separate effect for updating settings when auto trading is active
  useEffect(() => {
    const updateSettings = async () => {
      if (isActive && lastAction !== 'stop') {
        try {
          await tradingService.startAutoTrading({ 
            min_profit_threshold: minProfit, 
            max_trade_size: maxTradeSize
          });
          console.log('Auto trading settings updated');
        } catch (error) {
          console.error('Failed to update auto trading settings:', error);
        }
      }
    };

    // Debounce settings updates to avoid too many API calls
    const timeoutId = setTimeout(updateSettings, 1000);
    return () => clearTimeout(timeoutId);
  }, [minProfit, maxTradeSize, isActive, lastAction]);

  return (
    <Card title="Auto Trading" className="auto-trading" loading={loading}>
      <Alert
        message="Auto Trading Mode"
        description="Automatically execute profitable arbitrage opportunities based on your settings."
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Statistic
            title="Auto Trading Status"
            value={isActive ? 'Active' : 'Inactive'}
            valueStyle={{ 
              color: isActive ? '#3f8600' : '#cf1322',
              fontWeight: 'bold'
            }}
          />
        </Col>
        <Col span={12}>
          <div style={{ textAlign: 'right' }}>
            <Switch
              checkedChildren={<PlayCircleOutlined />}
              unCheckedChildren={<PauseCircleOutlined />}
              checked={isActive}
              onChange={toggleAutoTrading}
              size="default"
              loading={loading}
              style={{ 
                transform: 'scale(1.2)',
                marginTop: '8px'
              }}
            />
          </div>
        </Col>
      </Row>

      <div className="settings-section">
        <h4>Trading Settings</h4>
        
        <div className="setting-item">
          <label>Minimum Profit Threshold (%)</label>
          <Slider
            min={0.1}
            max={5}
            step={0.1}
            value={minProfit}
            onChange={setMinProfit}
            tooltip={{ 
              formatter: (value) => `${value}%`,
              placement: 'bottom'
            }}
            disabled={!isActive || loading}
          />
          <InputNumber
            min={0.1}
            max={5}
            step={0.1}
            value={minProfit}
            onChange={setMinProfit}
            formatter={value => `${value}%`}
            parser={value => value.replace('%', '')}
            style={{ width: '100%', marginTop: 8 }}
            disabled={!isActive || loading}
          />
        </div>

        <div className="setting-item">
          <label>Maximum Trade Size (USD)</label>
          <Slider
            min={100}
            max={10000}
            step={100}
            value={maxTradeSize}
            onChange={setMaxTradeSize}
            tooltip={{ 
              formatter: (value) => `$${value.toLocaleString()}`,
              placement: 'bottom'
            }}
            disabled={!isActive || loading}
          />
          <InputNumber
            min={100}
            max={10000}
            step={100}
            value={maxTradeSize}
            onChange={setMaxTradeSize}
            formatter={value => `$${value.toLocaleString()}`}
            parser={value => value.replace(/\$\s?|(,*)/g, '')}
            style={{ width: '100%', marginTop: 8 }}
            disabled={!isActive || loading}
          />
        </div>

        {!isActive && (
          <Alert
            message="Settings disabled"
            description="Auto trading must be active to modify settings. Turn on auto trading to adjust these values."
            type="warning"
            showIcon
            style={{ marginTop: 16 }}
          />
        )}
      </div>

      {isActive && (
        <div className="activity-section" style={{ marginTop: 24 }}>
          <h4>Current Activity</h4>
          <Row gutter={16}>
            <Col span={8}>
              <Statistic
                title="Trades Today"
                value={stats.trades_today || 0}
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="Daily P&L"
                value={stats.daily_pnl || 0}
                precision={2}
                prefix="$"
                valueStyle={{ 
                  color: (stats.daily_pnl || 0) >= 0 ? '#3f8600' : '#cf1322' 
                }}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="Status"
                value={stats.trading_enabled ? 'Enabled' : 'Disabled'}
                valueStyle={{ 
                  color: stats.trading_enabled ? '#3f8600' : '#cf1322' 
                }}
              />
            </Col>
          </Row>
        </div>
      )}
    </Card>
  );
};

export default AutoTrading;