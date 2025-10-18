// frontend/src/components/Trading.jsx
import React, { useState, useEffect } from 'react';
import { arbitrageAPI } from '../utils/api';

const Trading = () => {
    const [tradeHistory, setTradeHistory] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [executionMessage, setExecutionMessage] = useState('');
    const [activeTab, setActiveTab] = useState('history');
    const [stats, setStats] = useState({
        totalTrades: 0,
        totalProfit: 0,
        successRate: 0,
        todayTrades: 0
    });

    useEffect(() => {
        fetchTradeHistory();
    }, []);

    const fetchTradeHistory = async () => {
        try {
            const data = await arbitrageAPI.getTradeHistory();
            setTradeHistory(data.trades || []);
            
            // Calculate stats
            if (data.trades && data.trades.length > 0) {
                const totalTrades = data.trades.length;
                const totalProfit = data.trades.reduce((sum, trade) => sum + (trade.profit || 0), 0);
                const successfulTrades = data.trades.filter(trade => trade.status === 'executed').length;
                const today = new Date().toDateString();
                const todayTrades = data.trades.filter(trade => {
                    const tradeDate = new Date(trade.timestamp).toDateString();
                    return tradeDate === today;
                }).length;

                setStats({
                    totalTrades,
                    totalProfit,
                    successRate: (successfulTrades / totalTrades) * 100,
                    todayTrades
                });
            }
        } catch (error) {
            console.error('Error fetching trade history:', error);
        }
    };

    const executeDemoTrade = async () => {
        setIsLoading(true);
        setExecutionMessage('');
        
        try {
            const sampleTriangle = ['BTC/USDT', 'ETH/BTC', 'ETH/USDT'];
            const amount = 100;
            
            const result = await arbitrageAPI.executeTrade(sampleTriangle, amount);
            
            if (result.status === 'executed') {
                setExecutionMessage(`✅ Trade executed successfully! Profit: $${result.profit.toFixed(2)}`);
            } else {
                setExecutionMessage(`❌ Trade failed: ${result.error}`);
            }
            
            fetchTradeHistory();
        } catch (error) {
            setExecutionMessage(`❌ Error executing trade: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'executed': return 'bg-green-100 text-green-800 border-green-200';
            case 'failed': return 'bg-red-100 text-red-800 border-red-200';
            case 'pending': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
            default: return 'bg-gray-100 text-gray-800 border-gray-200';
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'executed': return '✅';
            case 'failed': return '❌';
            case 'pending': return '⏳';
            default: return '❓';
        }
    };

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value);
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
                <div>
                    <h2 className="text-2xl lg:text-3xl font-bold text-gray-900">Trading Dashboard</h2>
                    <p className="text-gray-600 mt-1">Execute trades and monitor trading history</p>
                </div>
                
                {/* Quick Stats */}
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 w-full lg:w-auto">
                    <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-200">
                        <p className="text-xs text-gray-500">Total Trades</p>
                        <p className="text-lg font-bold text-gray-900">{stats.totalTrades}</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-200">
                        <p className="text-xs text-gray-500">Total Profit</p>
                        <p className={`text-lg font-bold ${stats.totalProfit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {formatCurrency(stats.totalProfit)}
                        </p>
                    </div>
                    <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-200">
                        <p className="text-xs text-gray-500">Success Rate</p>
                        <p className="text-lg font-bold text-blue-600">{stats.successRate.toFixed(1)}%</p>
                    </div>
                    <div className="bg-white rounded-lg p-3 shadow-sm border border-gray-200">
                        <p className="text-xs text-gray-500">Today</p>
                        <p className="text-lg font-bold text-purple-600">{stats.todayTrades}</p>
                    </div>
                </div>
            </div>

            {/* Navigation Tabs */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                <div className="border-b border-gray-200">
                    <nav className="flex -mb-px">
                        {[
                            { id: 'history', name: 'Trade History', icon: '📊' },
                            { id: 'execute', name: 'Execute Trade', icon: '⚡' }
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`flex-1 py-4 px-4 text-center border-b-2 font-medium text-sm transition-all duration-200 ${
                                    activeTab === tab.id
                                        ? 'border-blue-500 text-blue-600 bg-blue-50'
                                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                }`}
                            >
                                <span className="mr-2">{tab.icon}</span>
                                <span className="hidden sm:inline">{tab.name}</span>
                                <span className="sm:hidden">{tab.icon}</span>
                            </button>
                        ))}
                    </nav>
                </div>

                <div className="p-4 lg:p-6">
                    {/* Trade Execution Tab */}
                    {activeTab === 'execute' && (
                        <div className="space-y-6">
                            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl p-6 border border-blue-200">
                                <h3 className="text-xl font-semibold text-gray-900 mb-2">Demo Trade Execution</h3>
                                <p className="text-gray-600 mb-4">
                                    Execute a simulated triangular arbitrage trade for demonstration purposes.
                                </p>
                                
                                <div className="bg-white rounded-lg p-4 mb-4 border border-gray-200">
                                    <h4 className="font-medium text-gray-900 mb-2">Trade Details</h4>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                        <div>
                                            <span className="text-gray-500">Triangle:</span>
                                            <div className="font-mono text-gray-900 mt-1">BTC/USDT → ETH/BTC → ETH/USDT</div>
                                        </div>
                                        <div>
                                            <span className="text-gray-500">Amount:</span>
                                            <div className="font-mono text-gray-900 mt-1">$100.00</div>
                                        </div>
                                    </div>
                                </div>

                                <div className="flex flex-col sm:flex-row items-center gap-4">
                                    <button
                                        onClick={executeDemoTrade}
                                        disabled={isLoading}
                                        className={`px-6 py-3 bg-blue-600 text-white rounded-lg font-medium shadow-lg transition-all duration-200 flex items-center justify-center min-w-[160px] ${
                                            isLoading 
                                                ? 'opacity-50 cursor-not-allowed' 
                                                : 'hover:bg-blue-700 hover:shadow-xl transform hover:scale-105'
                                        }`}
                                    >
                                        {isLoading ? (
                                            <>
                                                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                </svg>
                                               
                                            </>
                                        ) : (
                                            <>
                                                <span className="mr-2">⚡</span>
                                                Execute Trade
                                            </>
                                        )}
                                    </button>
                                    
                                    <div className="text-sm text-gray-600 text-center sm:text-left">
                                        This will simulate a triangular arbitrage trade with real-time profit calculation
                                    </div>
                                </div>
                                
                                {executionMessage && (
                                    <div className={`mt-4 p-4 rounded-lg border-2 ${
                                        executionMessage.includes('✅') 
                                            ? 'bg-green-50 border-green-200 text-green-800' 
                                            : 'bg-red-50 border-red-200 text-red-800'
                                    }`}>
                                        <div className="flex items-center">
                                            <span className="text-lg mr-2">
                                                {executionMessage.includes('✅') ? '✅' : '❌'}
                                            </span>
                                            <span className="font-medium">{executionMessage.replace(/[✅❌]/g, '').trim()}</span>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Help Information */}
                            <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
                                <div className="flex items-start">
                                    <span className="text-yellow-500 text-lg mr-3">💡</span>
                                    <div>
                                        <h4 className="font-medium text-yellow-800">How It Works</h4>
                                        <p className="text-yellow-700 text-sm mt-1">
                                            Triangular arbitrage involves executing three trades across different currency pairs to profit from price discrepancies.
                                            The system automatically calculates the optimal path and potential profit.
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Trade History Tab */}
                    {activeTab === 'history' && (
                        <div className="space-y-4">
                            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                                <h3 className="text-xl font-semibold text-gray-900">Trade History</h3>
                                <button
                                    onClick={fetchTradeHistory}
                                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors flex items-center"
                                >
                                    <span className="mr-2">🔄</span>
                                    Refresh
                                </button>
                            </div>

                            {tradeHistory.length === 0 ? (
                                <div className="text-center py-12 bg-white rounded-xl border-2 border-dashed border-gray-300">
                                    <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                        <span className="text-2xl">📊</span>
                                    </div>
                                    <h3 className="text-lg font-medium text-gray-900 mb-2">No trades yet</h3>
                                    <p className="text-gray-600 max-w-md mx-auto">
                                        Execute your first trade to see the history here.
                                    </p>
                                </div>
                            ) : (
                                <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                                    {/* Mobile View - Cards */}
                                    <div className="lg:hidden space-y-3 p-4">
                                        {tradeHistory.map((trade) => (
                                            <div key={trade.id} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                                                <div className="flex justify-between items-start mb-3">
                                                    <div>
                                                        <span className="text-xs text-gray-500">ID:</span>
                                                        <div className="font-mono text-sm font-medium text-gray-900">
                                                            {String(trade.id).slice(0, 8)}...
                                                        </div>
                                                    </div>
                                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(trade.status)}`}>
                                                        <span className="mr-1">{getStatusIcon(trade.status)}</span>
                                                        {trade.status || 'unknown'}
                                                    </span>
                                                </div>
                                                
                                                <div className="space-y-2">
                                                    <div>
                                                        <span className="text-xs text-gray-500">Triangle:</span>
                                                        <div className="text-sm font-medium text-gray-900 truncate">
                                                            {(trade.triangle && Array.isArray(trade.triangle)) 
                                                                ? trade.triangle.join(' → ') 
                                                                : (trade.triangle || 'N/A')}
                                                        </div>
                                                    </div>
                                                    
                                                    <div className="grid grid-cols-2 gap-4">
                                                        <div>
                                                            <span className="text-xs text-gray-500">Amount:</span>
                                                            <div className="text-sm font-medium text-gray-900">
                                                                {formatCurrency(trade.entry_amount || trade.amount || 0)}
                                                            </div>
                                                        </div>
                                                        <div>
                                                            <span className="text-xs text-gray-500">Profit:</span>
                                                            <div className={`text-sm font-bold ${Number(trade.profit || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                                                                {formatCurrency(trade.profit || 0)}
                                                            </div>
                                                        </div>
                                                    </div>
                                                    
                                                    <div>
                                                        <span className="text-xs text-gray-500">Time:</span>
                                                        <div className="text-sm text-gray-900">
                                                            {(() => {
                                                                const ts = trade.timestamp;
                                                                let date = null;
                                                                try {
                                                                    if (typeof ts === 'string') {
                                                                        date = new Date(ts);
                                                                    } else if (typeof ts === 'number') {
                                                                        date = new Date(ts < 1e12 ? ts * 1000 : ts);
                                                                    }
                                                                } catch (err) {
                                                                    date = null;
                                                                }
                                                                return date && !isNaN(date.getTime()) 
                                                                    ? date.toLocaleString() 
                                                                    : '—';
                                                            })()}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>

                                    {/* Desktop View - Table */}
                                    <div className="hidden lg:block overflow-x-auto">
                                        <table className="min-w-full divide-y divide-gray-200">
                                            <thead className="bg-gray-50">
                                                <tr>
                                                    {[
                                                        { key: 'id', label: 'Trade ID', className: 'w-24' },
                                                        { key: 'triangle', label: 'Triangle', className: 'w-48' },
                                                        { key: 'amount', label: 'Amount', className: 'w-24' },
                                                        { key: 'profit', label: 'Profit', className: 'w-24' },
                                                        { key: 'status', label: 'Status', className: 'w-20' },
                                                        { key: 'time', label: 'Time', className: 'w-40' }
                                                    ].map(({ key, label, className }) => (
                                                        <th
                                                            key={key}
                                                            className={`px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${className}`}
                                                        >
                                                            {label}
                                                        </th>
                                                    ))}
                                                </tr>
                                            </thead>
                                            <tbody className="bg-white divide-y divide-gray-200">
                                                {tradeHistory.map((trade) => (
                                                    <tr key={trade.id} className="hover:bg-gray-50 transition-colors">
                                                        <td className="px-4 py-3 whitespace-nowrap text-sm font-mono text-gray-900">
                                                            {String(trade.id).slice(0, 8)}...
                                                        </td>
                                                        <td className="px-4 py-3 text-sm text-gray-900 max-w-xs truncate">
                                                            {(trade.triangle && Array.isArray(trade.triangle)) 
                                                                ? trade.triangle.join(' → ') 
                                                                : (trade.triangle || 'N/A')}
                                                        </td>
                                                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-900">
                                                            {formatCurrency(trade.entry_amount || trade.amount || 0)}
                                                        </td>
                                                        <td className="px-4 py-3 whitespace-nowrap text-sm font-bold">
                                                            <span className={Number(trade.profit || 0) >= 0 ? 'text-green-600' : 'text-red-600'}>
                                                                {formatCurrency(trade.profit || 0)}
                                                            </span>
                                                        </td>
                                                        <td className="px-4 py-3 whitespace-nowrap">
                                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(trade.status)}`}>
                                                                <span className="mr-1">{getStatusIcon(trade.status)}</span>
                                                                {trade.status || 'unknown'}
                                                            </span>
                                                        </td>
                                                        <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500">
                                                            {(() => {
                                                                const ts = trade.timestamp;
                                                                let date = null;
                                                                try {
                                                                    if (typeof ts === 'string') {
                                                                        date = new Date(ts);
                                                                    } else if (typeof ts === 'number') {
                                                                        date = new Date(ts < 1e12 ? ts * 1000 : ts);
                                                                    }
                                                                } catch (err) {
                                                                    date = null;
                                                                }
                                                                // FIX: use toLocaleString (not toLocaleLocaleString)
                                                                return date && !isNaN(date.getTime()) 
                                                                    ? date.toLocaleString() 
                                                                    : '—';
                                                            })()}
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>

                                    {/* Footer */}
                                    <div className="bg-gray-50 px-4 py-3 border-t border-gray-200">
                                        <div className="flex justify-between items-center text-sm text-gray-600">
                                            <span>
                                                Showing {tradeHistory.length} trade{tradeHistory.length !== 1 ? 's' : ''}
                                            </span>
                                            <span className="hidden sm:inline">
                                                Last updated: {new Date().toLocaleTimeString()}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Trading;