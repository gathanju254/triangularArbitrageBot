// frontend/src/components/dashboard/OpportunitiesTable/OpportunitiesTable.jsx
import React from 'react';
import { Table, Tag, Space, Typography, Tooltip } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, InfoCircleOutlined } from '@ant-design/icons';
import './OpportunitiesTable.css';

const { Text } = Typography;

const OpportunitiesTable = ({ opportunities = [], maxRows = 5, showAll = false }) => {
  const columns = [
    {
      title: 'Symbol',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 100,
      render: (symbol) => <Text strong>{symbol}</Text>,
    },
    {
      title: 'Profit %',
      dataIndex: 'profit_percentage',
      key: 'profit_percentage',
      width: 120,
      render: (percentage) => {
        const profitValue = typeof percentage === 'number' ? percentage : 0;
        const isPositive = profitValue > 0;
        
        return (
          <Space>
            {isPositive ? 
              <ArrowUpOutlined style={{ color: '#52c41a' }} /> : 
              <ArrowDownOutlined style={{ color: '#ff4d4f' }} />
            }
            <Text 
              strong 
              style={{ 
                color: isPositive ? '#52c41a' : '#ff4d4f',
                fontSize: '14px'
              }}
            >
              {profitValue.toFixed(2)}%
            </Text>
          </Space>
        );
      },
    },
    {
      title: 'Exchanges',
      key: 'exchanges',
      width: 150,
      render: (_, record) => (
        <Space direction="vertical" size={2}>
          <div className="exchange-row">
            <Tag color="blue" className="exchange-tag">
              {record.buy_exchange_name || 'Unknown'}
            </Tag>
          </div>
          <div className="exchange-row">
            <Tag color="green" className="exchange-tag">
              {record.sell_exchange_name || 'Unknown'}
            </Tag>
          </div>
        </Space>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => {
        const statusConfig = {
          active: { color: 'green', text: 'ACTIVE' },
          expired: { color: 'orange', text: 'EXPIRED' },
          executed: { color: 'blue', text: 'EXECUTED' },
          cancelled: { color: 'red', text: 'CANCELLED' }
        };
        
        const config = statusConfig[status] || { color: 'default', text: status?.toUpperCase() || 'UNKNOWN' };
        
        return (
          <Tag color={config.color} className="status-tag">
            {config.text}
          </Tag>
        );
      },
    },
    {
      title: (
        <Space size={4}>
          Actions
          <Tooltip title="Click on opportunities to view details">
            <InfoCircleOutlined style={{ color: '#999', fontSize: '12px' }} />
          </Tooltip>
        </Space>
      ),
      key: 'actions',
      width: 80,
      render: (_, record) => (
        <Space>
          <Tag 
            color="gold" 
            className="action-tag"
            style={{ cursor: 'pointer' }}
            onClick={() => console.log('View details:', record)}
          >
            View
          </Tag>
        </Space>
      ),
    },
  ];

  // Process data with proper keys and formatting
  const processedData = opportunities
    .slice(0, showAll ? opportunities.length : maxRows)
    .map((opp, index) => ({
      key: opp.id || `opp-${index}`,
      symbol: opp.symbol || 'N/A',
      profit_percentage: opp.profit_percentage || 0,
      buy_exchange_name: opp.buy_exchange_name || 'Unknown',
      sell_exchange_name: opp.sell_exchange_name || 'Unknown',
      status: opp.status || 'active',
      buy_price: opp.buy_price,
      sell_price: opp.sell_price,
      detected_at: opp.detected_at,
    }));

  if (processedData.length === 0) {
    return (
      <div className="opportunities-empty">
        <Text type="secondary">No active arbitrage opportunities found</Text>
        <div style={{ marginTop: 8 }}>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            New opportunities will appear here when detected
          </Text>
        </div>
      </div>
    );
  }

  return (
    <div className="opportunities-container">
      <Table
        columns={columns}
        dataSource={processedData}
        pagination={false}
        size="small"
        scroll={{ y: 240 }}
        className="opportunities-table"
        onRow={(record) => ({
          onClick: () => console.log('Opportunity clicked:', record),
          style: { cursor: 'pointer' }
        })}
      />
      
      {!showAll && opportunities.length > maxRows && (
        <div className="more-opportunities">
          <Text type="secondary">
            +{opportunities.length - maxRows} more opportunities available
          </Text>
        </div>
      )}
      
      <div className="opportunities-summary">
        <Text type="secondary" style={{ fontSize: '12px' }}>
          Showing {processedData.length} of {opportunities.length} opportunities
          {processedData.some(opp => opp.profit_percentage > 1) && (
            <span style={{ color: '#52c41a', marginLeft: 8 }}>
              • High-profit opportunities available
            </span>
          )}
        </Text>
      </div>
    </div>
  );
};

export default OpportunitiesTable;