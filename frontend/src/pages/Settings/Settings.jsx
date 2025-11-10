// frontend/src/pages/Settings/Settings.jsx - Enhanced Version
import React, { useState } from 'react';
import { Tabs, Card, Typography, Alert, Spin } from 'antd';
import { 
  SettingOutlined, 
  KeyOutlined, 
  SafetyOutlined,
  SwapOutlined,
  BankOutlined
} from '@ant-design/icons';
import ApiKeys from '../../components/settings/ApiKeys/ApiKeys';
import ExchangeSettings from '../../components/settings/ExchangeSettings/ExchangeSettings';
import TradingConfig from '../../components/settings/TradingConfig/TradingConfig';
import './Settings.css';

const { Title } = Typography;
const { TabPane } = Tabs;

const Settings = () => {
  const [activeTab, setActiveTab] = useState('api-keys');
  const [settingsChanged, setSettingsChanged] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleTabChange = (key) => {
    if (settingsChanged) {
      const confirmChange = window.confirm(
        'You have unsaved changes. Are you sure you want to switch tabs?'
      );
      if (!confirmChange) return;
    }
    setActiveTab(key);
    setSettingsChanged(false);
  };

  const handleSettingsChange = (changed) => {
    setSettingsChanged(changed);
  };

  // Simulate loading state (you can replace this with actual loading logic)
  const simulateLoading = () => {
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  };

  const handleTabClick = (key) => {
    if (key !== activeTab) {
      simulateLoading();
    }
  };

  return (
    <div className="settings-page">
      <div className="settings-header">
        <Title level={2}>Settings & Configuration</Title>
        <div className="settings-subtitle">
          Configure your trading preferences, API keys, and exchange connections
        </div>
      </div>

      {settingsChanged && (
        <Alert
          message="Unsaved Changes"
          description="You have unsaved changes. Please save or cancel before switching tabs."
          type="warning"
          showIcon
          closable
          className="settings-alert"
          style={{ marginBottom: 16 }}
        />
      )}

      <Card 
        className="settings-card"
        loading={loading}
      >
        {loading ? (
          <div className="settings-loading">
            <Spin size="large" tip="Loading settings..." />
          </div>
        ) : (
          <Tabs
            activeKey={activeTab}
            onChange={handleTabChange}
            onTabClick={handleTabClick}
            type="card"
            className="settings-tabs"
          >
            <TabPane
              tab={
                <span className="settings-tab-label">
                  <KeyOutlined />
                  API Keys
                </span>
              }
              key="api-keys"
            >
              <div className="settings-tab-content">
                <ApiKeys onSettingsChange={handleSettingsChange} />
              </div>
            </TabPane>

            <TabPane
              tab={
                <span className="settings-tab-label">
                  <SwapOutlined />
                  Exchange Settings
                </span>
              }
              key="exchange-settings"
            >
              <div className="settings-tab-content">
                <ExchangeSettings onSettingsChange={handleSettingsChange} />
              </div>
            </TabPane>

            <TabPane
              tab={
                <span className="settings-tab-label">
                  <SafetyOutlined />
                  Trading Configuration
                </span>
              }
              key="trading-config"
            >
              <div className="settings-tab-content">
                <TradingConfig onSettingsChange={handleSettingsChange} />
              </div>
            </TabPane>
          </Tabs>
        )}
      </Card>
    </div>
  );
};

export default Settings;