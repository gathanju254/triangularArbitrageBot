// frontend/src/components/dashboard/OpportunitiesTable/OpportunitiesTable.jsx
import React from 'react';
import { Table, Tag, Space, Typography, Tooltip, Badge } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, InfoCircleOutlined } from '@ant-design/icons';
import './OpportunitiesTable.css';

const { Text } = Typography;

const OpportunitiesTable = ({ opportunities = [], maxRows = 5, showAll = false }) => {
  const columns = [
    {
      title: 'Triangle Path',
      dataIndex: 'triangle',
      key: 'triangle',
      width: 200,
      render: (triangle) => (
        <Tooltip title={triangle?.join(' → ')}>
          <Text strong style={{ fontSize: '12px' }}>
            {triangle?.map(pair => pair.split('/')[0]).join(' → ')}
          </Text>
        </Tooltip>
      ),
    },
    {
      title: 'Profit %',
      dataIndex: 'profit_percentage',
      key: 'profit_percentage',
      width: 120,
      render: (percentage, record) => {
        const profitValue = typeof percentage === 'number' ? percentage : 0;
        const isPositive = profitValue > 0;
        const isHighProfit = profitValue > 1.0;
        
        return (
          <Space>
            {isPositive ? 
              <ArrowUpOutlined style={{ color: '#52c41a' }} /> : 
              <ArrowDownOutlined style={{ color: '#ff4d4f' }} />
            }
            <Badge 
              count={isHighProfit ? "HIGH" : null} 
              size="small" 
              style={{ 
                backgroundColor: isHighProfit ? '#ff4d4f' : 'transparent',
                marginRight: isHighProfit ? 8 : 0
              }}
            >
              <Text 
                strong 
                style={{ 
                  color: isPositive ? '#52c41a' : '#ff4d4f',
                  fontSize: '14px'
                }}
              >
                {profitValue.toFixed(2)}%
              </Text>
            </Badge>
          </Space>
        );
      },
      sorter: (a, b) => a.profit_percentage - b.profit_percentage,
    },
    {
      title: 'Prices',
      key: 'prices',
      width: 150,
      render: (_, record) => (
        <Space direction="vertical" size={0}>
          {record.prices && Object.entries(record.prices).slice(0, 2).map(([pair, price]) => (
            <div key={pair} className="price-row">
              <Text type="secondary" style={{ fontSize: '10px' }}>
                {pair}: {typeof price === 'number' ? price.toFixed(6) : price}
              </Text>
            </div>
          ))}
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
        
        const config = statusConfig[status] || { color: 'default', text: 'ACTIVE' };
        
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
          <Tooltip title="Real triangular arbitrage opportunities">
            <InfoCircleOutlined style={{ color: '#999', fontSize: '12px' }} />
          </Tooltip>
        </Space>
      ),
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Space>
          <Tag 
            color="blue" 
            className="action-tag"
            style={{ cursor: 'pointer' }}
            onClick={() => {
              console.log('Opportunity details:', record);
              // You can implement a modal or detailed view here
            }}
          >
            Details
          </Tag>
        </Space>
      ),
    },
  ];

  // Process data with proper keys and formatting
  const processedData = opportunities
    .slice(0, showAll ? opportunities.length : maxRows)
    .map((opp, index) => ({
      key: opp.id || `opp-${index}-${Date.now()}`,
      ...opp,
      profit_percentage: opp.profit_percentage || 0,
      status: opp.status || 'active',
    }));

  if (processedData.length === 0) {
    return (
      <div className="opportunities-empty">
        <Text type="secondary">No active arbitrage opportunities found</Text>
        <div style={{ marginTop: 8 }}>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            The system is scanning for triangular arbitrage opportunities...
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
        scroll={{ y: 400 }}
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