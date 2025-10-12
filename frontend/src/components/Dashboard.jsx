// frontend/src/components/Dashboard.jsx
import React, { useState, useEffect } from 'react';
import Opportunities from './Opportunities.jsx';
import Trading from './Trading.jsx';
import Settings from './Settings.jsx';

const Dashboard = () => {
    const [activeTab, setActiveTab] = useState('opportunities');
    const [systemStatus, setSystemStatus] = useState('stopped');
    const [performance, setPerformance] = useState({
        totalProfit: 0,
        tradesToday: 0,
        activeOpportunities: 0
    });

    useEffect(() => {
        // Fetch initial data
        fetchSystemStatus();
        fetchPerformance();
        
        // Set up periodic updates
        const interval = setInterval(() => {
            fetchSystemStatus();
            fetchPerformance();
        }, 5000);
        
        return () => clearInterval(interval);
    }, []);

    const fetchSystemStatus = async () => {
        try {
            const response = await fetch('http://localhost:8000/api/system/status/')
            const data = await response.json();
            setSystemStatus(data.status);
        } catch (error) {
            console.error('Error fetching system status:', error);
        }
    };

    const fetchPerformance = async () => {
        try {
            const response = await fetch('/api/performance/');
            const data = await response.json();
            setPerformance(data);
        } catch (error) {
            console.error('Error fetching performance:', error);
        }
    };

    const toggleSystem = async () => {
        try {
            const action = systemStatus === 'running' ? 'stop' : 'start';
            const response = await fetch('/api/system/control/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ action }),
            });
            const data = await response.json();
            setSystemStatus(data.status);
        } catch (error) {
            console.error('Error toggling system:', error);
        }
    };

    return (
        <div className="min-h-screen bg-gray-100">
            {/* Header */}
            <header className="bg-white shadow">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center py-6">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900">
                                Triangular Arbitrage Bot
                            </h1>
                            <p className="text-gray-600">Real-time arbitrage opportunity detection</p>
                        </div>
                        <div className="flex items-center space-x-4">
                            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                                systemStatus === 'running' 
                                    ? 'bg-green-100 text-green-800' 
                                    : 'bg-red-100 text-red-800'
                            }`}>
                                {systemStatus === 'running' ? 'Running' : 'Stopped'}
                            </div>
                            <button
                                onClick={toggleSystem}
                                className={`px-4 py-2 rounded-md font-medium ${
                                    systemStatus === 'running'
                                        ? 'bg-red-600 hover:bg-red-700 text-white'
                                        : 'bg-green-600 hover:bg-green-700 text-white'
                                }`}
                            >
                                {systemStatus === 'running' ? 'Stop Bot' : 'Start Bot'}
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            {/* Performance Metrics */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-white rounded-lg shadow p-6">
                        <div className="flex items-center">
                            <div className="flex-shrink-0">
                                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                                    <span className="text-white font-bold">$</span>
                                </div>
                            </div>
                            <div className="ml-4">
                                <p className="text-sm font-medium text-gray-500">Total Profit</p>
                                <p className="text-2xl font-semibold text-gray-900">
                                    ${performance.totalProfit.toFixed(2)}
                                </p>
                            </div>
                        </div>
                    </div>
                    
                    <div className="bg-white rounded-lg shadow p-6">
                        <div className="flex items-center">
                            <div className="flex-shrink-0">
                                <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                                    <span className="text-white font-bold">↯</span>
                                </div>
                            </div>
                            <div className="ml-4">
                                <p className="text-sm font-medium text-gray-500">Trades Today</p>
                                <p className="text-2xl font-semibold text-gray-900">
                                    {performance.tradesToday}
                                </p>
                            </div>
                        </div>
                    </div>
                    
                    <div className="bg-white rounded-lg shadow p-6">
                        <div className="flex items-center">
                            <div className="flex-shrink-0">
                                <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
                                    <span className="text-white font-bold">⚡</span>
                                </div>
                            </div>
                            <div className="ml-4">
                                <p className="text-sm font-medium text-gray-500">Active Opportunities</p>
                                <p className="text-2xl font-semibold text-gray-900">
                                    {performance.activeOpportunities}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Navigation Tabs */}
                <div className="bg-white shadow rounded-lg">
                    <div className="border-b border-gray-200">
                        <nav className="flex -mb-px">
                            {[
                                { id: 'opportunities', name: 'Opportunities' },
                                { id: 'trading', name: 'Trading' },
                                { id: 'settings', name: 'Settings' }
                            ].map((tab) => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id)}
                                    className={`py-4 px-6 text-center border-b-2 font-medium text-sm ${
                                        activeTab === tab.id
                                            ? 'border-blue-500 text-blue-600'
                                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                    }`}
                                >
                                    {tab.name}
                                </button>
                            ))}
                        </nav>
                    </div>
                    
                    <div className="p-6">
                        {activeTab === 'opportunities' && <Opportunities />}
                        {activeTab === 'trading' && <Trading />}
                        {activeTab === 'settings' && <Settings />}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;