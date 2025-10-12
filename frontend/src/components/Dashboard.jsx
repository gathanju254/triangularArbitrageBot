// frontend/src/components/Dashboard.jsx
import React, { useState, useEffect, useCallback } from 'react';
import Opportunities from './Opportunities.jsx';
import Trading from './Trading.jsx';
import Settings from './Settings.jsx';
import { arbitrageAPI } from '../utils/api';  // Import the API

const Dashboard = () => {
    const [activeTab, setActiveTab] = useState('opportunities');
    const [systemStatus, setSystemStatus] = useState('stopped');
    const [isLoading, setIsLoading] = useState(false);
    const [lastUpdated, setLastUpdated] = useState(null);
    const [error, setError] = useState(null);
    const [performance, setPerformance] = useState({
        totalProfit: 0,
        tradesToday: 0,
        activeOpportunities: 0,
        successRate: 0,
        dailyProfit: 0,
        weeklyProfit: 0,
        monthlyProfit: 0
    });

    // Memoized fetch functions to prevent unnecessary re-renders
    const fetchSystemStatus = useCallback(async () => {
        try {
            setError(null);
            const data = await arbitrageAPI.getSystemStatus();
            setSystemStatus(data.status);
        } catch (error) {
            console.error('Error fetching system status:', error);
            setError('Failed to fetch system status');
        }
    }, []);

    const fetchPerformance = useCallback(async () => {
        try {
            setError(null);
            const data = await arbitrageAPI.getPerformance();
            setPerformance(prev => ({
                ...prev,
                ...data
            }));
            setLastUpdated(new Date());
        } catch (error) {
            console.error('Error fetching performance:', error);
            setError('Failed to fetch performance data');
        }
    }, []);

    const fetchAllData = useCallback(async () => {
        await Promise.all([fetchSystemStatus(), fetchPerformance()]);
    }, [fetchSystemStatus, fetchPerformance]);

    useEffect(() => {
        // Initial data fetch
        fetchAllData();
        
        // Set up periodic updates with cleanup
        const interval = setInterval(fetchAllData, 5000);
        
        return () => clearInterval(interval);
    }, [fetchAllData]);

    const toggleSystem = async () => {
        try {
            setIsLoading(true);
            setError(null);
            
            const action = systemStatus === 'running' ? 'stop' : 'start';
            const data = await arbitrageAPI.controlSystem(action);
            setSystemStatus(data.status);
            
            // Refresh data after state change
            setTimeout(fetchAllData, 1000);
        } catch (error) {
            console.error('Error toggling system:', error);
            const errorMessage = `Failed to ${systemStatus === 'running' ? 'stop' : 'start'} system: ${error.message}`;
            setError(errorMessage);
            alert(errorMessage);
        } finally {
            setIsLoading(false);
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

    const formatPercentage = (value) => {
        return `${(value * 100).toFixed(1)}%`;
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'running': return 'bg-green-100 text-green-800 border-green-200';
            case 'stopped': return 'bg-red-100 text-red-800 border-red-200';
            case 'paused': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
            case 'error': return 'bg-orange-100 text-orange-800 border-orange-200';
            default: return 'bg-gray-100 text-gray-800 border-gray-200';
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'running': return '🟢';
            case 'stopped': return '🔴';
            case 'paused': return '🟡';
            case 'error': return '🟠';
            default: return '⚪';
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-200">
            {/* Header */}
            <header className="bg-white shadow-lg border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center py-6">
                        <div className="flex items-center space-x-4">
                            <div className="flex-shrink-0">
                                <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                                    <span className="text-white font-bold text-lg">Δ</span>
                                </div>
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold text-gray-900">
                                    Triangular Arbitrage Bot
                                </h1>
                                <p className="text-gray-600 mt-1">Real-time arbitrage opportunity detection & trading</p>
                            </div>
                        </div>
                        
                        <div className="flex items-center space-x-4">
                            {/* Last Updated */}
                            {lastUpdated && (
                                <div className="text-sm text-gray-500 hidden md:block">
                                    Last updated: {lastUpdated.toLocaleTimeString()}
                                </div>
                            )}
                            
                            {/* System Status */}
                            <div className={`px-4 py-2 rounded-full text-sm font-medium border ${getStatusColor(systemStatus)}`}>
                                <span className="mr-2">{getStatusIcon(systemStatus)}</span>
                                {systemStatus.charAt(0).toUpperCase() + systemStatus.slice(1)}
                            </div>
                            
                            {/* Toggle Button */}
                            <button
                                onClick={toggleSystem}
                                disabled={isLoading}
                                className={`px-6 py-2 rounded-md font-medium transition-all duration-200 ${
                                    systemStatus === 'running'
                                        ? 'bg-red-600 hover:bg-red-700 text-white shadow-lg transform hover:scale-105'
                                        : 'bg-green-600 hover:bg-green-700 text-white shadow-lg transform hover:scale-105'
                                } ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
                            >
                                {isLoading ? (
                                    <span className="flex items-center">
                                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                        </svg>
                                        Processing...
                                    </span>
                                ) : (
                                    systemStatus === 'running' ? 'Stop Bot' : 'Start Bot'
                                )}
                            </button>
                        </div>
                    </div>
                </div>
            </header>

            {/* Error Banner */}
            {error && (
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4">
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center justify-between">
                        <div className="flex items-center">
                            <svg className="w-5 h-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                            </svg>
                            <span className="text-red-800 font-medium">{error}</span>
                        </div>
                        <button
                            onClick={() => setError(null)}
                            className="text-red-400 hover:text-red-600"
                        >
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                            </svg>
                        </button>
                    </div>
                </div>
            )}

            {/* Performance Metrics */}
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                    {/* Total Profit */}
                    <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100 hover:shadow-xl transition-shadow duration-200">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Total Profit</p>
                                <p className="text-2xl font-bold text-gray-900 mt-1">
                                    {formatCurrency(performance.totalProfit)}
                                </p>
                                {performance.dailyProfit !== undefined && (
                                    <p className={`text-sm mt-1 ${
                                        performance.dailyProfit >= 0 ? 'text-green-600' : 'text-red-600'
                                    }`}>
                                        Today: {formatCurrency(performance.dailyProfit)}
                                    </p>
                                )}
                            </div>
                            <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-blue-600 rounded-full flex items-center justify-center shadow-lg">
                                <span className="text-white font-bold text-lg">$</span>
                            </div>
                        </div>
                    </div>
                    
                    {/* Trades Today */}
                    <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100 hover:shadow-xl transition-shadow duration-200">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Trades Today</p>
                                <p className="text-2xl font-bold text-gray-900 mt-1">
                                    {performance.tradesToday?.toLocaleString() || 0}
                                </p>
                                {performance.successRate !== undefined && (
                                    <p className="text-sm text-green-600 mt-1">
                                        Success: {formatPercentage(performance.successRate)}
                                    </p>
                                )}
                            </div>
                            <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-green-600 rounded-full flex items-center justify-center shadow-lg">
                                <span className="text-white font-bold text-lg">↯</span>
                            </div>
                        </div>
                    </div>
                    
                    {/* Active Opportunities */}
                    <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100 hover:shadow-xl transition-shadow duration-200">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Active Opportunities</p>
                                <p className="text-2xl font-bold text-gray-900 mt-1">
                                    {performance.activeOpportunities?.toLocaleString() || 0}
                                </p>
                                <p className="text-sm text-gray-500 mt-1">Real-time monitoring</p>
                            </div>
                            <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-purple-600 rounded-full flex items-center justify-center shadow-lg">
                                <span className="text-white font-bold text-lg">⚡</span>
                            </div>
                        </div>
                    </div>

                    {/* Additional Metrics */}
                    <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-100 hover:shadow-xl transition-shadow duration-200">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Weekly Performance</p>
                                <p className="text-2xl font-bold text-gray-900 mt-1">
                                    {formatCurrency(performance.weeklyProfit || 0)}
                                </p>
                                {performance.monthlyProfit !== undefined && (
                                    <p className="text-sm text-gray-500 mt-1">
                                        Monthly: {formatCurrency(performance.monthlyProfit)}
                                    </p>
                                )}
                            </div>
                            <div className="w-12 h-12 bg-gradient-to-r from-orange-500 to-orange-600 rounded-full flex items-center justify-center shadow-lg">
                                <span className="text-white font-bold text-lg">📈</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Navigation Tabs */}
                <div className="bg-white shadow-xl rounded-2xl border border-gray-100 overflow-hidden">
                    <div className="border-b border-gray-200 bg-gray-50">
                        <nav className="flex -mb-px">
                            {[
                                { id: 'opportunities', name: 'Trading Opportunities', icon: '🔍' },
                                { id: 'trading', name: 'Trading History', icon: '📊' },
                                { id: 'settings', name: 'Settings', icon: '⚙️' }
                            ].map((tab) => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id)}
                                    className={`flex-1 py-4 px-6 text-center border-b-2 font-medium text-sm transition-all duration-200 ${
                                        activeTab === tab.id
                                            ? 'border-blue-500 text-blue-600 bg-white shadow-sm'
                                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                    }`}
                                >
                                    <span className="mr-2">{tab.icon}</span>
                                    {tab.name}
                                </button>
                            ))}
                        </nav>
                    </div>
                    
                    <div className="p-6 bg-gradient-to-br from-gray-50 to-white">
                        {activeTab === 'opportunities' && <Opportunities />}
                        {activeTab === 'trading' && <Trading />}
                        {activeTab === 'settings' && <Settings />}
                    </div>
                </div>
            </div>

            {/* Footer */}
            <footer className="bg-white border-t border-gray-200 mt-12">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
                    <div className="flex justify-between items-center text-sm text-gray-500">
                        <div>
                            Triangular Arbitrage Bot v1.0 • Real-time Trading System
                        </div>
                        <div>
                            {lastUpdated && `Last update: ${lastUpdated.toLocaleString()}`}
                        </div>
                    </div>
                </div>
            </footer>
        </div>
    );
};

export default Dashboard;