// frontend/src/pages/Settings/Settings.jsx
import React, { useState } from 'react';
import { Tabs, Card, Typography, Alert } from 'antd';
import { 
  SettingOutlined, 
  KeyOutlined, 
  SafetyOutlined,
  SwapOutlined, // Use SwapOutlined instead of ExchangeOutlined
  BankOutlined   // Alternative option
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
          style={{ marginBottom: 16 }}
        />
      )}

      <Card className="settings-card">
        <Tabs
          activeKey={activeTab}
          onChange={handleTabChange}
          type="card"
          className="settings-tabs"
        >
          <TabPane
            tab={
              <span>
                <KeyOutlined />
                API Keys
              </span>
            }
            key="api-keys"
          >
            <ApiKeys onSettingsChange={handleSettingsChange} />
          </TabPane>

          <TabPane
            tab={
              <span>
                <SwapOutlined /> {/* Changed from ExchangeOutlined to SwapOutlined */}
                Exchange Settings
              </span>
            }
            key="exchange-settings"
          >
            <ExchangeSettings onSettingsChange={handleSettingsChange} />
          </TabPane>

          <TabPane
            tab={
              <span>
                <SafetyOutlined />
                Trading Configuration
              </span>
            }
            key="trading-config"
          >
            <TradingConfig onSettingsChange={handleSettingsChange} />
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default Settings;