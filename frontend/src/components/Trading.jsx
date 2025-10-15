// frontend/src/components/Trading.jsx
import React, { useState, useEffect } from 'react';
import { arbitrageAPI } from '../utils/api';

const Trading = () => {
    const [tradeHistory, setTradeHistory] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [executionMessage, setExecutionMessage] = useState('');

    useEffect(() => {
        fetchTradeHistory();
    }, []);

    const fetchTradeHistory = async () => {
        try {
            const data = await arbitrageAPI.getTradeHistory();
            setTradeHistory(data.trades || []);
        } catch (error) {
            console.error('Error fetching trade history:', error);
        }
    };

    const executeDemoTrade = async () => {
        setIsLoading(true);
        setExecutionMessage('');
        
        try {
            // For demo purposes, use a sample triangle
            const sampleTriangle = ['BTC/USDT', 'ETH/BTC', 'ETH/USDT'];
            const amount = 100; // $100
            
            const result = await arbitrageAPI.executeTrade(sampleTriangle, amount);
            
            if (result.status === 'executed') {
                setExecutionMessage(`Trade executed successfully! Profit: $${result.profit.toFixed(2)}`);
            } else {
                setExecutionMessage(`Trade failed: ${result.error}`);
            }
            
            // Refresh trade history
            fetchTradeHistory();
        } catch (error) {
            setExecutionMessage(`Error executing trade: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'executed': return 'bg-green-100 text-green-800';
            case 'failed': return 'bg-red-100 text-red-800';
            case 'pending': return 'bg-yellow-100 text-yellow-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    return (
        <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Trading</h2>
            
            {/* Demo Trade Execution */}
            <div className="bg-white shadow rounded-lg p-6 mb-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Demo Trade Execution</h3>
                <div className="flex items-center space-x-4">
                    <button
                        onClick={executeDemoTrade}
                        disabled={isLoading}
                        className={`px-4 py-2 bg-blue-600 text-white rounded-md font-medium ${
                            isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-blue-700'
                        }`}
                    >
                        {isLoading ? 'Executing...' : 'Execute Demo Trade'}
                    </button>
                    <span className="text-sm text-gray-600">
                        This will execute a simulated trade for demonstration purposes.
                    </span>
                </div>
                
                {executionMessage && (
                    <div className={`mt-4 p-3 rounded-md ${
                        executionMessage.includes('successfully') 
                            ? 'bg-green-100 text-green-700' 
                            : 'bg-red-100 text-red-700'
                    }`}>
                        {executionMessage}
                    </div>
                )}
            </div>

            {/* Trade History */}
            <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Trade History</h3>
                
                {tradeHistory.length === 0 ? (
                    <div className="text-center py-8 bg-white shadow rounded-lg">
                        <p className="text-gray-500">No trades executed yet.</p>
                    </div>
                ) : (
                    <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
                        <table className="min-w-full divide-y divide-gray-300">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Trade ID
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Triangle
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Amount
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Profit
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Status
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Time
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {tradeHistory.map((trade) => (
                                    <tr key={trade.id} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                            {trade.id.slice(0, 8)}...
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {trade.triangle.join(' → ')}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            ${trade.entry_amount.toFixed(2)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                            <span className={trade.profit >= 0 ? 'text-green-600' : 'text-red-600'}>
                                                ${trade.profit.toFixed(2)}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(trade.status)}`}>
                                                {trade.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {new Date(trade.timestamp).toLocaleString()}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Trading;