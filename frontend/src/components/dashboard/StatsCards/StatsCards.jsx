// frontend/src/components/dashboard/StatsCards/StatsCards.jsx - Enhanced Version
import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Tooltip } from 'antd';
import { 
  DollarOutlined, 
  SwapOutlined, 
  RocketOutlined, 
  LineChartOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import './StatsCards.css';

const StatsCards = ({ stats, loading }) => {
  const [previousStats, setPreviousStats] = useState({});
  const [changedValues, setChangedValues] = useState({});

  const defaultStats = {
    total_profit: 0,
    total_trades: 0,
    success_rate: 0,
    active_opportunities: 0,
    today_profit: 0,
    avg_profit_percentage: 0
  };

  const currentStats = stats || defaultStats;

  // Detect value changes for animations
  useEffect(() => {
    if (stats) {
      const changes = {};
      Object.keys(stats).forEach(key => {
        if (previousStats[key] !== undefined && stats[key] !== previousStats[key]) {
          changes[key] = true;
        }
      });
      setChangedValues(changes);
      setPreviousStats(stats);
    }
  }, [stats, previousStats]);

  const statCards = [
    {
      key: 'total_profit',
      title: 'Total Profit',
      value: currentStats.total_profit,
      precision: 2,
      prefix: '$',
      icon: <DollarOutlined />,
      color: '#52c41a',
      trend: currentStats.today_profit > 0 ? 'up' : currentStats.today_profit < 0 ? 'down' : null,
      trendValue: currentStats.today_profit,
      description: 'Cumulative profit from all trades',
      variant: 'profit'
    },
    {
      key: 'total_trades',
      title: 'Total Trades',
      value: currentStats.total_trades,
      precision: 0,
      icon: <SwapOutlined />,
      color: '#1890ff',
      description: 'Number of completed trades',
      variant: 'trades'
    },
    {
      key: 'success_rate',
      title: 'Success Rate',
      value: currentStats.success_rate,
      precision: 1,
      suffix: '%',
      icon: <LineChartOutlined />,
      color: '#faad14',
      description: 'Percentage of profitable trades',
      variant: 'success'
    },
    {
      key: 'active_opportunities',
      title: 'Active Opportunities',
      value: currentStats.active_opportunities,
      precision: 0,
      icon: <RocketOutlined />,
      color: '#722ed1',
      description: 'Current arbitrage opportunities detected',
      variant: 'opportunities'
    }
  ];

  const formatTrend = (trend, value) => {
    if (!trend || value === 0) return null;
    
    const TrendIcon = trend === 'up' ? ArrowUpOutlined : ArrowDownOutlined;
    const trendClass = trend === 'up' ? 'stats-card-trend-up' : 'stats-card-trend-down';
    
    return (
      <span className={`stats-card-trend ${trendClass}`}>
        <TrendIcon /> ${Math.abs(value).toFixed(2)} today
      </span>
    );
  };

  const formatValue = (value, precision, prefix = '', suffix = '') => {
    if (typeof value !== 'number') return '0';
    
    const formatted = value.toLocaleString(undefined, {
      minimumFractionDigits: precision,
      maximumFractionDigits: precision
    });
    
    return `${prefix}${formatted}${suffix}`;
  };

  const getCardVariantClass = (variant) => {
    switch (variant) {
      case 'profit':
        return 'stats-card-profit';
      case 'trades':
        return 'stats-card-trades';
      case 'success':
        return 'stats-card-success';
      case 'opportunities':
        return 'stats-card-opportunities';
      default:
        return '';
    }
  };

  return (
    <Row gutter={[16, 16]} className="stats-cards-grid">
      {statCards.map((stat) => (
        <Col xs={24} sm={12} lg={6} key={stat.key}>
          <Card 
            className={`stats-card ${getCardVariantClass(stat.variant)} ${
              changedValues[stat.key] ? 'stats-card-highlighted' : ''
            }`}
            loading={loading}
          >
            <div className="stats-card-content">
              <div className="stats-card-info">
                <div className="stats-card-header">
                  <div className="stats-card-title">
                    {stat.title}
                    {stat.description && (
                      <Tooltip title={stat.description}>
                        <InfoCircleOutlined className="stats-card-info-icon" />
                      </Tooltip>
                    )}
                  </div>
                </div>
                <div 
                  className={`stats-card-value ${changedValues[stat.key] ? 'changed' : ''}`}
                  style={{ color: stat.color }}
                >
                  {formatValue(stat.value, stat.precision, stat.prefix, stat.suffix)}
                </div>
                <div className="stats-card-footer">
                  {formatTrend(stat.trend, stat.trendValue)}
                </div>
              </div>
              <div className="stats-card-icon" style={{ color: stat.color }}>
                {stat.icon}
              </div>
            </div>
          </Card>
        </Col>
      ))}
    </Row>
  );
};

export default StatsCards;