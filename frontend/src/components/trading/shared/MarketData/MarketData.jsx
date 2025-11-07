// frontend/src/components/trading/TradeHistory/TradeHistory.jsx
import React, { useState, useEffect } from 'react';
import { Table, Tag, Space, Alert, Button } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { tradingService } from '../../../services/api/tradingService';
import './TradeHistory.css';

const TradeHistory = () => {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadTradeHistory();
  }, []);

  const loadTradeHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const history = await tradingService.getTradeHistory();
      
      // Ensure we have a proper array
      let tradeData = [];
      
      if (Array.isArray(history)) {
        tradeData = history;
      } else if (history && Array.isArray(history.results)) {
        // Handle paginated response
        tradeData = history.results;
      } else if (history && Array.isArray(history.data)) {
        // Handle data property
        tradeData = history.data;
      } else if (history && typeof history === 'object') {
        // Handle object response - extract array from it
        const possibleArrayKeys = ['data', 'trades', 'orders', 'items', 'results'];
        for (const key of possibleArrayKeys) {
          if (Array.isArray(history[key])) {
            tradeData = history[key];
            break;
          }
        }
        
        // If no array found but object has values, try to use it as single item
        if (tradeData.length === 0 && Object.keys(history).length > 0) {
          tradeData = [history];
        }
      }
      
      // Ensure each item has a unique key and required fields
      const processedTrades = tradeData.map((trade, index) => ({
        ...trade,
        key: trade.id || trade.order_id || `trade-${index}`,
        // Ensure all required fields exist with fallbacks
        timestamp: trade.timestamp || trade.created_at || trade.executed_at || new Date().toISOString(),
        symbol: trade.symbol || 'N/A',
        side: trade.side || 'buy',
        amount: trade.amount || trade.filled_amount || '0',
        price: trade.price || trade.average_price || '0',
        profit: trade.profit || trade.actual_profit || '0',
        status: trade.status || 'completed'
      }));
      
      setTrades(processedTrades);
      
    } catch (error) {
      console.error('Failed to load trade history:', error);
      setError(error.message || 'Failed to load trade history');
      setTrades([]); // Ensure empty array on error
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    loadTradeHistory();
  };

  const columns = [
    {
      title: 'Date',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (timestamp) => {
        if (!timestamp) return 'N/A';
        try {
          return new Date(timestamp).toLocaleString();
        } catch {
          return 'Invalid Date';
        }
      },
      width: 180,
      sorter: (a, b) => new Date(a.timestamp || 0) - new Date(b.timestamp || 0),
    },
    {
      title: 'Symbol',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 100,
      render: (symbol) => symbol || 'N/A',
      filters: [
        { text: 'BTC/USDT', value: 'BTC/USDT' },
        { text: 'ETH/USDT', value: 'ETH/USDT' },
        { text: 'ADA/USDT', value: 'ADA/USDT' },
      ],
      onFilter: (value, record) => record.symbol === value,
    },
    {
      title: 'Side',
      dataIndex: 'side',
      key: 'side',
      render: (side) => (
        <Tag color={side === 'buy' ? 'green' : side === 'sell' ? 'red' : 'default'}>
          {(side || 'buy').toUpperCase()}
        </Tag>
      ),
      width: 80,
      filters: [
        { text: 'BUY', value: 'buy' },
        { text: 'SELL', value: 'sell' },
      ],
      onFilter: (value, record) => record.side === value,
    },
    {
      title: 'Amount',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount) => {
        try {
          return parseFloat(amount || 0).toFixed(8);
        } catch {
          return '0.00000000';
        }
      },
      width: 120,
      sorter: (a, b) => parseFloat(a.amount || 0) - parseFloat(b.amount || 0),
    },
    {
      title: 'Price',
      dataIndex: 'price',
      key: 'price',
      render: (price) => {
        try {
          return `$${parseFloat(price || 0).toFixed(2)}`;
        } catch {
          return '$0.00';
        }
      },
      width: 100,
      sorter: (a, b) => parseFloat(a.price || 0) - parseFloat(b.price || 0),
    },
    {
      title: 'Profit/Loss',
      dataIndex: 'profit',
      key: 'profit',
      render: (profit) => {
        try {
          const profitNum = parseFloat(profit || 0);
          return (
            <span style={{ 
              color: profitNum >= 0 ? '#3f8600' : '#cf1322',
              fontWeight: profitNum !== 0 ? '500' : 'normal'
            }}>
              ${Math.abs(profitNum).toFixed(2)}
              {profitNum !== 0 && (
                <span style={{ fontSize: '12px', marginLeft: '4px' }}>
                  {profitNum >= 0 ? '↑' : '↓'}
                </span>
              )}
            </span>
          );
        } catch {
          return <span style={{ color: '#cf1322' }}>$0.00</span>;
        }
      },
      width: 120,
      sorter: (a, b) => parseFloat(a.profit || 0) - parseFloat(b.profit || 0),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const statusColor = {
          'completed': 'green',
          'filled': 'green',
          'pending': 'orange',
          'open': 'blue',
          'cancelled': 'gray',
          'failed': 'red',
          'partial': 'purple'
        };
        
        return (
          <Tag color={statusColor[status] || 'default'}>
            {(status || 'unknown').toUpperCase()}
          </Tag>
        );
      },
      width: 100,
      filters: [
        { text: 'COMPLETED', value: 'completed' },
        { text: 'PENDING', value: 'pending' },
        { text: 'FAILED', value: 'failed' },
        { text: 'CANCELLED', value: 'cancelled' },
      ],
      onFilter: (value, record) => record.status === value,
    },
    {
      title: 'Exchange',
      dataIndex: ['exchange', 'name'],
      key: 'exchange',
      width: 100,
      render: (exchangeName) => exchangeName || 'N/A',
      filters: [
        { text: 'Binance', value: 'binance' },
        { text: 'KuCoin', value: 'kucoin' },
        { text: 'Coinbase', value: 'coinbase' },
      ],
      onFilter: (value, record) => record.exchange?.name === value,
    },
  ];

  return (
    <div className="trade-history">
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0 }}>Trade History</h2>
        <Button 
          icon={<ReloadOutlined />} 
          onClick={handleRetry}
          loading={loading}
        >
          Refresh
        </Button>
      </div>

      {error && (
        <Alert
          message="Error Loading Trade History"
          description={
            <div>
              <p>{error}</p>
              <Button type="primary" size="small" onClick={handleRetry}>
                Try Again
              </Button>
            </div>
          }
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
          closable
          onClose={() => setError(null)}
        />
      )}
      
      <Table
        columns={columns}
        dataSource={trades}
        rowKey="key"
        loading={loading}
        pagination={{ 
          pageSize: 10,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => 
            `${range[0]}-${range[1]} of ${total} trades`,
          pageSizeOptions: ['10', '20', '50', '100']
        }}
        scroll={{ x: 1000 }}
        size="middle"
        locale={{
          emptyText: loading ? 'Loading trades...' : 'No trade history found'
        }}
        onChange={(pagination, filters, sorter) => {
          console.log('Table changed:', { pagination, filters, sorter });
        }}
      />
    </div>
  );
};

export default TradeHistory;