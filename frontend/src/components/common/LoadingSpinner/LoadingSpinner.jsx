// frontend/src/components/common/LoadingSpinner/LoadingSpinner.jsx
import React from 'react';
import { Spin, Typography } from 'antd';
import { LoadingOutlined, RocketOutlined, ThunderboltOutlined, FundOutlined } from '@ant-design/icons';
import './LoadingSpinner.css';

const { Text } = Typography;

const LoadingSpinner = ({ 
  size = 'large', 
  text = 'Loading...', 
  type = 'default',
  fullScreen = false,
  overlay = false,
  delay = 0
}) => {
  const [showSpinner, setShowSpinner] = React.useState(delay === 0);

  React.useEffect(() => {
    if (delay > 0) {
      const timer = setTimeout(() => setShowSpinner(true), delay);
      return () => clearTimeout(timer);
    }
  }, [delay]);

  const getCustomIcon = () => {
    const baseStyle = { fontSize: getIconSize(), color: '#1890ff' };
    
    switch (type) {
      case 'trading':
        return <ThunderboltOutlined style={baseStyle} />;
      case 'arbitrage':
        return <RocketOutlined style={baseStyle} />;
      case 'finance':
        return <FundOutlined style={baseStyle} />;
      default:
        return <LoadingOutlined style={baseStyle} />;
    }
  };

  const getIconSize = () => {
    switch (size) {
      case 'small': return 20;
      case 'default': return 24;
      case 'large': return 32;
      default: return 24;
    }
  };

  const getSpinSize = () => {
    if (type !== 'default') return size;
    return size;
  };

  if (!showSpinner) return null;

  return (
    <div className={`loading-spinner ${size} ${type} ${fullScreen ? 'full-screen' : ''} ${overlay ? 'overlay' : ''}`}>
      <div className="spinner-content">
        <Spin 
          indicator={getCustomIcon()} 
          size={getSpinSize()}
          className="custom-spin"
        />
        {text && (
          <Text className="loading-text" type="secondary">
            {text}
          </Text>
        )}
      </div>
      
      {/* Optional progress bar for longer operations */}
      {type === 'arbitrage' && (
        <div className="loading-progress">
          <div className="progress-track">
            <div className="progress-bar" />
          </div>
        </div>
      )}
    </div>
  );
};

// Additional specialized loading components
export const PageLoader = ({ text = 'Loading page...' }) => (
  <LoadingSpinner 
    size="large" 
    text={text} 
    fullScreen 
    type="default" 
  />
);

export const TradingLoader = ({ text = 'Analyzing markets...' }) => (
  <LoadingSpinner 
    size="large" 
    text={text} 
    type="trading" 
  />
);

export const ArbitrageLoader = ({ text = 'Scanning arbitrage opportunities...' }) => (
  <LoadingSpinner 
    size="large" 
    text={text} 
    type="arbitrage" 
    delay={300}
  />
);

export const DataLoader = ({ text = 'Loading data...' }) => (
  <LoadingSpinner 
    size="default" 
    text={text} 
    type="finance" 
  />
);

export default LoadingSpinner;