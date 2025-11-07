// frontend/src/components/dashboard/ProfitChart/ProfitChart.jsx
import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Typography, Card } from 'antd';
import { RiseOutlined, FallOutlined } from '@ant-design/icons';
import './ProfitChart.css';

const { Text, Title } = Typography;

const ProfitChart = ({ data = [], title = "Profit History", timeframe = "7D" }) => {
  // Process chart data
  const chartData = React.useMemo(() => {
    return data.map((item, index) => ({
      date: item.date ? new Date(item.date).toLocaleDateString() : `Day ${index + 1}`,
      profit: item.profit || 0,
      cumulative: item.cumulative || 0,
    }));
  }, [data]);

  // Calculate stats
  const stats = React.useMemo(() => {
    if (chartData.length === 0) return null;
    
    const profits = chartData.map(item => item.profit);
    const totalProfit = profits.reduce((sum, profit) => sum + profit, 0);
    const avgProfit = totalProfit / profits.length;
    const maxProfit = Math.max(...profits);
    const minProfit = Math.min(...profits);
    const positiveDays = profits.filter(profit => profit > 0).length;
    const successRate = (positiveDays / profits.length) * 100;

    return {
      totalProfit,
      avgProfit,
      maxProfit,
      minProfit,
      successRate,
      positiveDays,
      totalDays: profits.length
    };
  }, [chartData]);

  // Custom tooltip component
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="custom-tooltip">
          <p className="label">{`Date: ${label}`}</p>
          {payload.map((entry, index) => (
            <p key={index} className="tooltip-item" style={{ color: entry.color }}>
              {`${entry.dataKey}: $${entry.value.toFixed(2)}`}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  // Render empty state
  if (chartData.length === 0) {
    return (
      <Card 
        title={
          <div className="chart-header">
            <Title level={4}>{title}</Title>
            <Text type="secondary">{timeframe}</Text>
          </div>
        }
        className="profit-chart-card"
      >
        <div className="profit-chart-empty">
          <Text type="secondary">No profit data available for the selected period</Text>
        </div>
      </Card>
    );
  }

  return (
    <Card 
      title={
        <div className="chart-header">
          <Title level={4}>{title}</Title>
          <div className="chart-timeframe">
            <Text type="secondary">{timeframe}</Text>
            {stats && (
              <Text 
                strong 
                style={{ 
                  color: stats.totalProfit >= 0 ? '#52c41a' : '#ff4d4f',
                  marginLeft: '8px'
                }}
              >
                {stats.totalProfit >= 0 ? <RiseOutlined /> : <FallOutlined />}
                ${Math.abs(stats.totalProfit).toFixed(2)}
              </Text>
            )}
          </div>
        </div>
      }
      className="profit-chart-card"
      extra={
        stats && (
          <div className="chart-stats">
            <Text type="secondary">
              Success: {stats.successRate.toFixed(1)}% • 
              Avg: ${stats.avgProfit.toFixed(2)}
            </Text>
          </div>
        )
      }
    >
      <div className="profit-chart">
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 11 }}
              angle={-45}
              textAnchor="end"
              height={60}
              interval="preserveStartEnd"
            />
            <YAxis 
              tick={{ fontSize: 11 }}
              tickFormatter={(value) => `$${value}`}
              width={80}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="profit" 
              name="Daily Profit"
              stroke="#1890ff" 
              strokeWidth={2}
              dot={{ fill: '#1890ff', strokeWidth: 2, r: 3 }}
              activeDot={{ r: 5, fill: '#1890ff', stroke: '#fff', strokeWidth: 2 }}
            />
            <Line 
              type="monotone" 
              dataKey="cumulative" 
              name="Cumulative"
              stroke="#52c41a" 
              strokeWidth={1.5}
              strokeDasharray="3 3"
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      {/* Stats summary */}
      {stats && (
        <div className="profit-stats-summary">
          <div className="stat-item">
            <Text type="secondary">Total Profit</Text>
            <Text strong style={{ color: stats.totalProfit >= 0 ? '#52c41a' : '#ff4d4f' }}>
              ${stats.totalProfit.toFixed(2)}
            </Text>
          </div>
          <div className="stat-item">
            <Text type="secondary">Best Day</Text>
            <Text strong style={{ color: '#52c41a' }}>
              ${stats.maxProfit.toFixed(2)}
            </Text>
          </div>
          <div className="stat-item">
            <Text type="secondary">Worst Day</Text>
            <Text strong style={{ color: '#ff4d4f' }}>
              ${stats.minProfit.toFixed(2)}
            </Text>
          </div>
          <div className="stat-item">
            <Text type="secondary">Success Rate</Text>
            <Text strong>
              {stats.successRate.toFixed(1)}%
            </Text>
          </div>
        </div>
      )}
    </Card>
  );
};

export default ProfitChart;