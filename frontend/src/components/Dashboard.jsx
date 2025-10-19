// frontend/src/components/Dashboard.jsx
import React, { useState, useEffect, useCallback } from 'react';
import Opportunities from './Opportunities.jsx';
import Trading from './Trading.jsx';
import Settings from './Settings.jsx';
import { arbitrageAPI } from '../utils/api';

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
    const [tradingMode, setTradingMode] = useState('neutral'); // 'neutral', 'demo', 'real'
    const [riskMetrics, setRiskMetrics] = useState(null);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const [monitoringStatus, setMonitoringStatus] = useState('stopped');
    const [settings, setSettings] = useState({
        minProfitThreshold: 0.2,
        maxPositionSize: 1000,
        baseBalance: 1000,
        tradeSizeFraction: 0.01,
        maxDailyLoss: 100,
        enabledExchanges: ['binance'],
        tradingEnabled: false
    });

    // Settings validation function
    const validateSettings = (settings) => {
        const errors = [];
        
        if (settings.maxPositionSize < 2) {
            errors.push('Maximum position size must be at least $2');
        }
        
        if (settings.tradeSizeFraction <= 0 || settings.tradeSizeFraction > 1) {
            errors.push('Trade size fraction must be between 0.01 and 1.00 (1% to 100%)');
        }
        
        const calculatedTradeSize = settings.baseBalance * settings.tradeSizeFraction;
        if (calculatedTradeSize > settings.maxPositionSize) {
            errors.push(`Calculated trade size ($${calculatedTradeSize.toFixed(2)}) exceeds maximum position size ($${settings.maxPositionSize})`);
        }
        
        if (calculatedTradeSize < 2) {
            errors.push(`Calculated trade size ($${calculatedTradeSize.toFixed(2)}) is below minimum trade amount ($2)`);
        }
        
        return errors;
    };

    // Enhanced trade amount calculation
    const computeTradeAmount = () => {
        const base = Number(settings.baseBalance || 1000);
        const fraction = Number(settings.tradeSizeFraction || 0.01);
        const maxPosition = Number(settings.maxPositionSize || 100);
        
        let amount = base * fraction;
        
        // Ensure amount is within limits
        amount = Math.max(2, Math.min(amount, maxPosition)); // At least $2, at most maxPosition
        amount = Math.round(amount * 100) / 100; // Round to 2 decimal places
        
        console.log(`Trade amount calculation: $${base} * ${fraction*100}% = $${amount} (max: $${maxPosition})`);
        
        return amount;
    };

    // Memoized fetch functions
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

    const fetchRiskMetrics = useCallback(async () => {
        try {
            const data = await arbitrageAPI.getRiskMetrics();
            setRiskMetrics(data.risk_metrics || data);
        } catch (err) {
            console.debug('Risk metrics not available yet:', err);
        }
    }, []);

    const fetchSettings = useCallback(async () => {
        try {
            const data = await arbitrageAPI.getSettings();
            const s = data.settings || {};
            setSettings(prev => ({
                ...prev,
                minProfitThreshold: s.minProfitThreshold ?? prev.minProfitThreshold,
                maxPositionSize: s.maxPositionSize ?? prev.maxPositionSize,
                baseBalance: s.baseBalance ?? prev.baseBalance,
                tradeSizeFraction: s.tradeSizeFraction ?? prev.tradeSizeFraction,
                maxDailyLoss: s.maxDailyLoss ?? prev.maxDailyLoss,
                enabledExchanges: s.enabledExchanges ?? prev.enabledExchanges,
                tradingEnabled: s.tradingEnabled ?? prev.tradingEnabled
            }));
        } catch (err) {
            console.debug('Could not fetch settings:', err);
        }
    }, []);

    const fetchAllData = useCallback(async () => {
        await Promise.all([fetchSystemStatus(), fetchPerformance(), fetchRiskMetrics(), fetchSettings()]);
    }, [fetchSystemStatus, fetchPerformance, fetchRiskMetrics, fetchSettings]);

    // Trading Mode Handler
    const handleTradingModeChange = (mode) => {
        setTradingMode(mode);
        if (mode === 'neutral') {
            setError('⚠️ Please select a trading mode to start the bot');
        } else {
            setError(null);
        }
    };

    // Start Trading Monitor
    const startTradingMonitor = async () => {
        if (tradingMode === 'neutral') {
            setError('⚠️ Please select a trading mode first');
            return;
        }

        // Validate settings before starting
        const validationErrors = validateSettings(settings);
        if (validationErrors.length > 0) {
            setError(`❌ Settings validation failed: ${validationErrors.join(', ')}`);
            return;
        }

        try {
            setMonitoringStatus('starting');
            setIsLoading(true);
            setError(null);

            // Start the system (market data etc)
            const systemResponse = await arbitrageAPI.controlSystem('start');
            setSystemStatus(systemResponse.status);

            if (tradingMode === 'real') {
                // Enable real trading runtime flag on server
                await arbitrageAPI.enableRealTrading();
                setError('✅ Real trading enabled! Starting monitor...');
            } else {
                // Ensure real trading is disabled for demo mode
                await arbitrageAPI.disableRealTrading();
                setError('✅ Demo trading enabled! Starting monitor...');
            }

            // Start the background trading monitor thread on server
            const resp = await arbitrageAPI.startTradingMonitor();
            if (resp.status === 'success') {
                setMonitoringStatus('running');
                setError(`✅ Trading monitor started successfully! ${tradingMode === 'real' ? 'Real trading is now active.' : 'Demo mode is now active.'}`);
            } else {
                setMonitoringStatus('stopped');
                setError(`❌ Failed to start monitor: ${resp.message || JSON.stringify(resp)}`);
            }

            // Refresh all data
            await fetchAllData();
        } catch (error) {
            console.error('Failed to start trading monitor:', error);
            setError(`❌ Failed to start trading monitor: ${error.message || error}`);
            setMonitoringStatus('stopped');
        } finally {
            setIsLoading(false);
        }
    };

    // Stop Trading Monitor
    const stopTradingMonitor = async () => {
        try {
            setMonitoringStatus('stopping');
            setIsLoading(true);
            setError(null);

            // Stop the background monitor thread on server
            const resp = await arbitrageAPI.stopTradingMonitor();
            if (resp.status === 'success') {
                // Stop market data collection as well
                await arbitrageAPI.controlSystem('stop');
                await arbitrageAPI.disableRealTrading();
                setTradingMode('neutral');
                setMonitoringStatus('stopped');
                setError('🛑 Trading monitor stopped successfully.');
            } else {
                setError(`❌ Failed to stop monitor: ${resp.message || JSON.stringify(resp)}`);
            }

            // Refresh data
            await fetchAllData();
        } catch (error) {
            console.error('Failed to stop trading monitor:', error);
            setError(`❌ Failed to stop trading monitor: ${error.message || error}`);
        } finally {
            setIsLoading(false);
        }
    };

    // Execute Demo Trade
    const executeDemoTrade = async () => {
        try {
            setIsLoading(true);
            setError(null);

            const amount = computeTradeAmount();
            const triangle = ['BTC/USDT', 'BNB/BTC', 'BNB/USDT'];
            const result = await arbitrageAPI.executeTrade(triangle, amount, 'binance');

            if (result.status === 'executed') {
                setError(`✅ Demo trade executed! Profit: $${(result.profit || 0).toFixed(4)}`);
            } else {
                setError(`❌ Demo trade failed: ${result.error || 'Unknown error'}`);
            }

            setTimeout(fetchAllData, 800);
        } catch (error) {
            console.error('Demo trade error', error);
            setError(`❌ Demo trade error: ${error.message || error}`);
        } finally {
            setIsLoading(false);
        }
    };

    // Execute Real Trade
    const executeRealTrade = async () => {
        try {
            if (tradingMode !== 'real') {
                setError('⚠️ Please enable real trading mode first.');
                return;
            }

            setIsLoading(true);
            setError(null);

            const amount = computeTradeAmount();
            const triangle = ['BTC/USDT', 'ETH/BTC', 'ETH/USDT'];
            const result = await arbitrageAPI.executeTrade(triangle, amount, 'binance');

            if (result.status === 'executed') {
                setError(`✅ Real trade executed! Profit: $${(result.profit || 0).toFixed(4)}`);
            } else {
                setError(`❌ Real trade failed: ${result.error || 'Unknown error'}`);
            }

            setTimeout(fetchAllData, 1000);
        } catch (error) {
            console.error('Real trade error', error);
            setError(`❌ Real trade error: ${error.message || error}`);
        } finally {
            setIsLoading(false);
        }
    };

    // initial fetch + poll
    useEffect(() => {
        fetchAllData();
        const interval = setInterval(fetchAllData, 5000);
        return () => clearInterval(interval);
    }, [fetchAllData, fetchSettings]);

    const formatCurrency = (value) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value);
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'running': return 'bg-green-100 text-green-800 border-green-200';
            case 'stopped': return 'bg-red-100 text-red-800 border-red-200';
            case 'starting': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
            case 'stopping': return 'bg-orange-100 text-orange-800 border-orange-200';
            default: return 'bg-gray-100 text-gray-800 border-gray-200';
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'running': return '🟢';
            case 'stopped': return '🔴';
            case 'starting': return '🟡';
            case 'stopping': return '🟠';
            default: return '⚪';
        }
    };

    // Enhanced Control Buttons Component - Mobile Optimized
    const ControlButtons = () => (
        <div className="w-full">
            {/* Mobile Layout - Stacked */}
            <div className="lg:hidden space-y-4">
                {/* Trading Mode Selector - Mobile */}
                <div className="bg-white rounded-xl shadow-lg p-3 border border-gray-200">
                    <label className="block text-sm font-medium text-gray-700 text-center mb-2">
                        Trading Mode
                    </label>
                    <div className="flex space-x-2">
                        <button
                            onClick={() => handleTradingModeChange('neutral')}
                            className={`flex-1 px-2 py-2 rounded-lg font-medium text-xs transition-all duration-200 ${
                                tradingMode === 'neutral'
                                    ? 'bg-gray-600 text-white shadow-md'
                                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                            }`}
                        >
                            ⚪ Neutral
                        </button>
                        <button
                            onClick={() => handleTradingModeChange('demo')}
                            className={`flex-1 px-2 py-2 rounded-lg font-medium text-xs transition-all duration-200 ${
                                tradingMode === 'demo'
                                    ? 'bg-blue-600 text-white shadow-md'
                                    : 'bg-blue-200 text-blue-700 hover:bg-blue-300'
                            }`}
                        >
                            🧪 Demo
                        </button>
                        <button
                            onClick={() => handleTradingModeChange('real')}
                            className={`flex-1 px-2 py-2 rounded-lg font-medium text-xs transition-all duration-200 ${
                                tradingMode === 'real'
                                    ? 'bg-yellow-600 text-white shadow-md'
                                    : 'bg-yellow-200 text-yellow-700 hover:bg-yellow-300'
                            }`}
                        >
                            ⚡ Real
                        </button>
                    </div>
                </div>

                {/* Main Control Button - Mobile */}
                <button
                    onClick={monitoringStatus === 'running' ? stopTradingMonitor : startTradingMonitor}
                    disabled={isLoading || monitoringStatus === 'starting' || monitoringStatus === 'stopping' || tradingMode === 'neutral'}
                    className={`w-full py-3 rounded-lg font-medium transition-all duration-200 ${
                        monitoringStatus === 'running'
                            ? 'bg-red-600 hover:bg-red-700 text-white shadow-lg'
                            : tradingMode === 'neutral'
                            ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                            : tradingMode === 'demo'
                            ? 'bg-green-600 hover:bg-green-700 text-white shadow-lg'
                            : 'bg-yellow-600 hover:bg-yellow-700 text-white shadow-lg'
                    } ${isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:shadow-xl'}`}
                >
                    {isLoading ? (
                        <span className="flex items-center justify-center">
                            <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            {monitoringStatus === 'starting' ? 'Starting...' : 
                             monitoringStatus === 'stopping' ? 'Stopping...' : 'Processing'}
                        </span>
                    ) : (
                        <span className="flex items-center justify-center">
                            {monitoringStatus === 'running' ? (
                                <>
                                    <span className="mr-2">🛑</span>
                                    Stop Bot
                                </>
                            ) : (
                                <>
                                    <span className="mr-2">🚀</span>
                                    {tradingMode === 'neutral' ? 'Select Mode' : `Start ${tradingMode === 'real' ? 'Real' : 'Demo'} Bot`}
                                </>
                            )}
                        </span>
                    )}
                </button>

                {/* Quick Action Buttons - Mobile */}
                <div className="flex gap-2">
                    <button
                        onClick={executeDemoTrade}
                        disabled={isLoading || monitoringStatus !== 'running'}
                        className={`flex-1 px-3 py-2 rounded-lg font-medium text-xs transition-colors flex items-center justify-center ${
                            monitoringStatus === 'running'
                                ? 'bg-blue-600 text-white hover:bg-blue-700'
                                : 'bg-gray-400 text-white cursor-not-allowed'
                        } disabled:opacity-50 disabled:cursor-not-allowed`}
                    >
                        <span className="mr-1">🧪</span>
                        Demo Trade
                    </button>

                    <button
                        onClick={executeRealTrade}
                        disabled={isLoading || monitoringStatus !== 'running' || tradingMode !== 'real'}
                        className={`flex-1 px-3 py-2 rounded-lg font-medium text-xs transition-colors flex items-center justify-center ${
                            tradingMode === 'real' && monitoringStatus === 'running'
                                ? 'bg-yellow-600 text-white hover:bg-yellow-700'
                                : 'bg-gray-400 text-white cursor-not-allowed'
                        } disabled:opacity-50 disabled:cursor-not-allowed`}
                    >
                        <span className="mr-1">⚡</span>
                        Real Trade
                    </button>
                </div>

                {/* Status Indicators - Mobile */}
                <div className="flex justify-between items-center">
                    <div className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(monitoringStatus)}`}>
                        <span className="mr-1">{getStatusIcon(monitoringStatus)}</span>
                        {monitoringStatus.charAt(0).toUpperCase() + monitoringStatus.slice(1)}
                    </div>

                    <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                        tradingMode === 'real' 
                            ? 'bg-yellow-100 text-yellow-800 border border-yellow-200' 
                            : tradingMode === 'demo'
                            ? 'bg-blue-100 text-blue-800 border border-blue-200'
                            : 'bg-gray-100 text-gray-800 border border-gray-200'
                    }`}>
                        {tradingMode === 'real' ? '💰 Real' : 
                         tradingMode === 'demo' ? '🧪 Demo' : '⚪ Neutral'}
                    </div>
                </div>

                {lastUpdated && (
                    <div className="text-xs text-gray-500 text-center">
                        Updated: {lastUpdated.toLocaleTimeString()}
                    </div>
                )}
            </div>

            {/* Desktop Layout - Horizontal */}
            <div className="hidden lg:flex flex-col sm:flex-row items-center space-y-4 sm:space-y-0 sm:space-x-4">
                {/* Trading Mode Selector */}
                <div className="bg-white rounded-xl shadow-lg p-4 border border-gray-200">
                    <div className="flex flex-col space-y-3">
                        <label className="text-sm font-medium text-gray-700 text-center">
                            Trading Mode
                        </label>
                        <div className="flex space-x-2">
                            <button
                                onClick={() => handleTradingModeChange('neutral')}
                                className={`flex-1 px-3 py-2 rounded-lg font-medium text-sm transition-all duration-200 ${
                                    tradingMode === 'neutral'
                                        ? 'bg-gray-600 text-white shadow-md'
                                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                                }`}
                            >
                                ⚪ Neutral
                            </button>
                            <button
                                onClick={() => handleTradingModeChange('demo')}
                                className={`flex-1 px-3 py-2 rounded-lg font-medium text-sm transition-all duration-200 ${
                                    tradingMode === 'demo'
                                        ? 'bg-blue-600 text-white shadow-md'
                                        : 'bg-blue-200 text-blue-700 hover:bg-blue-300'
                                }`}
                            >
                                🧪 Demo
                            </button>
                            <button
                                onClick={() => handleTradingModeChange('real')}
                                className={`flex-1 px-3 py-2 rounded-lg font-medium text-sm transition-all duration-200 ${
                                    tradingMode === 'real'
                                        ? 'bg-yellow-600 text-white shadow-md'
                                        : 'bg-yellow-200 text-yellow-700 hover:bg-yellow-300'
                                }`}
                            >
                                ⚡ Real
                            </button>
                        </div>
                    </div>
                </div>

                {/* Main Control Group */}
                <div className="flex flex-col space-y-3">
                    {/* Start/Stop Monitor Button */}
                    <button
                        onClick={monitoringStatus === 'running' ? stopTradingMonitor : startTradingMonitor}
                        disabled={isLoading || monitoringStatus === 'starting' || monitoringStatus === 'stopping' || tradingMode === 'neutral'}
                        className={`px-6 py-3 rounded-lg font-medium transition-all duration-200 min-w-[160px] ${
                            monitoringStatus === 'running'
                                ? 'bg-red-600 hover:bg-red-700 text-white shadow-lg'
                                : tradingMode === 'neutral'
                                ? 'bg-gray-400 text-gray-200 cursor-not-allowed'
                                : tradingMode === 'demo'
                                ? 'bg-green-600 hover:bg-green-700 text-white shadow-lg'
                                : 'bg-yellow-600 hover:bg-yellow-700 text-white shadow-lg'
                        } ${isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:shadow-xl transform hover:scale-105'}`}
                    >
                        {isLoading ? (
                            <span className="flex items-center justify-center">
                                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                {monitoringStatus === 'starting' ? 'Starting...' : 
                                 monitoringStatus === 'stopping' ? 'Stopping...' : 'Processing'}
                            </span>
                        ) : (
                            <span className="flex items-center justify-center">
                                {monitoringStatus === 'running' ? (
                                    <>
                                        <span className="mr-2">🛑</span>
                                        Stop Bot
                                    </>
                                ) : (
                                    <>
                                        <span className="mr-2">🚀</span>
                                        {tradingMode === 'neutral' ? 'Select Mode' : `Start ${tradingMode === 'real' ? 'Real' : 'Demo'} Bot`}
                                    </>
                                )}
                            </span>
                        )}
                    </button>

                    {/* Quick Action Buttons */}
                    <div className="flex gap-2">
                        <button
                            onClick={executeDemoTrade}
                            disabled={isLoading || monitoringStatus !== 'running'}
                            className={`px-3 py-2 rounded-lg font-medium text-sm transition-colors flex items-center ${
                                monitoringStatus === 'running'
                                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                                    : 'bg-gray-400 text-white cursor-not-allowed'
                            } disabled:opacity-50 disabled:cursor-not-allowed`}
                        >
                            <span className="mr-2">🧪</span>
                            Demo Trade
                        </button>

                        <button
                            onClick={executeRealTrade}
                            disabled={isLoading || monitoringStatus !== 'running' || tradingMode !== 'real'}
                            className={`px-3 py-2 rounded-lg font-medium text-sm transition-colors flex items-center ${
                                tradingMode === 'real' && monitoringStatus === 'running'
                                    ? 'bg-yellow-600 text-white hover:bg-yellow-700'
                                    : 'bg-gray-400 text-white cursor-not-allowed'
                            } disabled:opacity-50 disabled:cursor-not-allowed`}
                        >
                            <span className="mr-2">⚡</span>
                            Real Trade
                        </button>
                    </div>
                </div>

                {/* Status Indicators */}
                <div className="flex flex-col items-center space-y-2">
                    {lastUpdated && (
                        <div className="text-sm text-gray-500">
                            Updated: {lastUpdated.toLocaleTimeString()}
                        </div>
                    )}

                    <div className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(monitoringStatus)}`}>
                        <span className="mr-1">{getStatusIcon(monitoringStatus)}</span>
                        {monitoringStatus.charAt(0).toUpperCase() + monitoringStatus.slice(1)}
                    </div>

                    <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                        tradingMode === 'real' 
                            ? 'bg-yellow-100 text-yellow-800 border border-yellow-200' 
                            : tradingMode === 'demo'
                            ? 'bg-blue-100 text-blue-800 border border-blue-200'
                            : 'bg-gray-100 text-gray-800 border border-gray-200'
                    }`}>
                        {tradingMode === 'real' ? '💰 Real Funds' : 
                         tradingMode === 'demo' ? '🧪 Demo Mode' : '⚪ Select Mode'}
                    </div>
                </div>
            </div>
        </div>
    );

    // Performance Metrics Component - Mobile Optimized
    const PerformanceMetrics = () => (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4 mb-6">
            <MetricCard
                title="Total Profit"
                value={formatCurrency(performance.totalProfit)}
                subtitle={`Today: ${formatCurrency(performance.dailyProfit)}`}
                subtitleColor={performance.dailyProfit >= 0 ? 'text-green-600' : 'text-red-600'}
                icon="💰"
                gradient="from-blue-500 to-blue-600"
                trend={performance.dailyProfit >= 0 ? 'up' : 'down'}
            />
            
            <MetricCard
                title="Trades Today"
                value={performance.tradesToday?.toLocaleString() || '0'}
                subtitle={`Success: ${performance.successRate?.toFixed(1) || '0'}%`}
                subtitleColor="text-green-600"
                icon="📊"
                gradient="from-green-500 to-green-600"
            />
            
            <MetricCard
                title="Active Opportunities"
                value={performance.activeOpportunities?.toLocaleString() || '0'}
                subtitle="Real-time"
                subtitleColor="text-gray-500"
                icon="⚡"
                gradient="from-purple-500 to-purple-600"
            />
            
            <MetricCard
                title="Weekly Profit"
                value={formatCurrency(performance.weeklyProfit || 0)}
                subtitle={`Monthly: ${formatCurrency(performance.monthlyProfit)}`}
                subtitleColor={performance.weeklyProfit >= 0 ? 'text-green-600' : 'text-red-600'}
                icon="📈"
                gradient="from-orange-500 to-orange-600"
                trend={performance.weeklyProfit >= 0 ? 'up' : 'down'}
            />
        </div>
    );

    // Risk Metrics Component - Mobile Optimized
    const RiskMetricsPanel = () => (
        riskMetrics && (
            <div className="mb-6 bg-white rounded-xl shadow-lg p-4 lg:p-6 border border-gray-100">
                <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2 lg:mb-0">Risk Management</h3>
                    <div className="text-sm text-gray-500">
                        Updated: {lastUpdated?.toLocaleTimeString() || 'Never'}
                    </div>
                </div>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
                    <RiskMetric
                        label="Current Balance"
                        value={riskMetrics.current_balance ? formatCurrency(riskMetrics.current_balance) : '—'}
                        icon="💳"
                    />
                    <RiskMetric
                        label="Peak Balance"
                        value={riskMetrics.peak_balance ? formatCurrency(riskMetrics.peak_balance) : '—'}
                        icon="📊"
                    />
                    <RiskMetric
                        label="Daily P&L"
                        value={riskMetrics.daily_pnl ? formatCurrency(riskMetrics.daily_pnl) : '—'}
                        isProfit={riskMetrics.daily_pnl >= 0}
                        icon={riskMetrics.daily_pnl >= 0 ? '📈' : '📉'}
                    />
                    <RiskMetric
                        label="Remaining Loss"
                        value={riskMetrics.max_daily_loss_remaining ? formatCurrency(riskMetrics.max_daily_loss_remaining) : '—'}
                        icon="🛡️"
                    />
                </div>
                
                {/* Additional Risk Info */}
                <div className="mt-4 grid grid-cols-3 gap-3 lg:gap-4 text-sm">
                    <div className="text-center">
                        <span className="text-gray-500 text-xs lg:text-sm">Total Trades:</span>
                        <div className="font-semibold text-gray-900 text-sm lg:text-base">{riskMetrics.total_trades || 0}</div>
                    </div>
                    <div className="text-center">
                        <span className="text-gray-500 text-xs lg:text-sm">Success Rate:</span>
                        <div className="font-semibold text-green-600 text-sm lg:text-base">{riskMetrics.success_rate?.toFixed(1) || '0'}%</div>
                    </div>
                    <div className="text-center">
                        <span className="text-gray-500 text-xs lg:text-sm">Drawdown:</span>
                        <div className="font-semibold text-gray-900 text-sm lg:text-base">{riskMetrics.drawdown_percentage?.toFixed(1) || '0'}%</div>
                    </div>
                </div>
            </div>
        )
    );

    // Navigation Tabs Component - Mobile Optimized
    const NavigationTabs = ({ activeTab, setActiveTab }) => {
        const tabs = [
            { id: 'opportunities', name: 'Opportunities', icon: '🔍', mobileIcon: '🔍' },
            { id: 'trading', name: 'Trading', icon: '📊', mobileIcon: '📊' },
            { id: 'settings', name: 'Settings', icon: '⚙️', mobileIcon: '⚙️' }
        ];

        return (
            <>
                {/* Desktop Tabs */}
                <div className="hidden lg:block border-b border-gray-200 bg-gray-50">
                    <nav className="flex -mb-px">
                        {tabs.map((tab) => (
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

                {/* Mobile Tabs */}
                <div className="lg:hidden bg-white border-b border-gray-200">
                    <nav className="flex">
                        {tabs.map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`flex-1 py-3 px-2 text-center border-b-2 font-medium text-xs transition-all duration-200 ${
                                    activeTab === tab.id
                                        ? 'border-blue-500 text-blue-600'
                                        : 'border-transparent text-gray-500 hover:text-gray-700'
                                }`}
                            >
                                <div className="flex flex-col items-center space-y-1">
                                    <span className="text-base">{tab.mobileIcon}</span>
                                    <span className="text-xs">{tab.name}</span>
                                </div>
                            </button>
                        ))}
                    </nav>
                </div>
            </>
        );
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
            {/* Header */}
            <header className="bg-white shadow-lg border-b border-gray-200 sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8">
                    <div className="flex flex-col lg:flex-row lg:justify-between lg:items-center py-3 lg:py-4 space-y-3 lg:space-y-0">
                        {/* Logo and Title */}
                        <div className="flex items-center space-x-3 justify-center lg:justify-start">
                            <div className="flex-shrink-0">
                                <div className="w-8 h-8 lg:w-10 lg:h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                                    <span className="text-white font-bold text-xs lg:text-sm">Δ</span>
                                </div>
                            </div>
                            <div className="text-center lg:text-left">
                                <h1 className="text-lg lg:text-xl font-bold text-gray-900">
                                    Arbitrage Bot
                                </h1>
                                <p className="text-gray-600 text-xs lg:text-sm hidden lg:block">Real-time trading system</p>
                            </div>
                        </div>
                        
                        {/* Controls */}
                        <div className="w-full lg:w-auto">
                            <ControlButtons />
                        </div>
                    </div>
                </div>
            </header>

            {/* Error/Success Banner */}
            {error && (
                <div className="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 pt-3 lg:pt-4">
                    <div className={`p-3 lg:p-4 rounded-lg border-2 flex items-center justify-between ${
                        error.includes('✅') || error.includes('successfully')
                            ? 'bg-green-50 border-green-200 text-green-800'
                            : error.includes('⚠️')
                            ? 'bg-yellow-50 border-yellow-200 text-yellow-800'
                            : 'bg-red-50 border-red-200 text-red-800'
                    }`}>
                        <div className="flex items-center flex-1 min-w-0">
                            <span className="text-lg mr-2 lg:mr-3 flex-shrink-0">
                                {error.includes('✅') ? '✅' : 
                                 error.includes('⚠️') ? '⚠️' : '❌'}
                            </span>
                            <span className="font-medium text-sm lg:text-base truncate">{error}</span>
                        </div>
                        <button
                            onClick={() => setError(null)}
                            className="text-gray-400 hover:text-gray-600 p-1 flex-shrink-0 ml-2"
                        >
                            <svg className="w-4 h-4 lg:w-5 lg:h-5" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                            </svg>
                        </button>
                    </div>
                </div>
            )}

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-3 sm:px-4 lg:px-8 py-4 lg:py-6">
                {/* Performance Metrics */}
                <PerformanceMetrics />

                {/* Risk Metrics */}
                <RiskMetricsPanel />

                {/* Content Area */}
                <div className="bg-white shadow-xl rounded-xl lg:rounded-2xl border border-gray-100 overflow-hidden">
                    {/* Pass activeTab and setActiveTab as props */}
                    <NavigationTabs activeTab={activeTab} setActiveTab={setActiveTab} />
                    
                    <div className="p-3 lg:p-4 xl:p-6 bg-gradient-to-br from-gray-50 to-white min-h-[400px] lg:min-h-[500px]">
                        {activeTab === 'opportunities' && <Opportunities />}
                        {activeTab === 'trading' && <Trading />}
                        {activeTab === 'settings' && <Settings />}
                    </div>
                </div>
            </main>
        </div>
    );
};

// Enhanced Metric Card Component - Mobile Optimized
const MetricCard = ({ title, value, subtitle, subtitleColor, icon, gradient, trend }) => (
    <div className="bg-white rounded-lg lg:rounded-xl shadow-lg p-3 lg:p-4 border border-gray-100 hover:shadow-xl transition-all duration-300 group">
        <div className="flex items-center justify-between">
            <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wide truncate">
                    {title}
                </p>
                <div className="flex items-center space-x-1 lg:space-x-2 mt-1">
                    <p className="text-base lg:text-xl font-bold text-gray-900 truncate">
                        {value}
                    </p>
                    {trend && (
                        <span className={`text-xs lg:text-sm ${trend === 'up' ? 'text-green-500' : 'text-red-500'}`}>
                            {trend === 'up' ? '↗' : '↘'}
                        </span>
                    )}
                </div>
                {subtitle && (
                    <p className={`text-xs mt-1 truncate ${subtitleColor}`}>
                        {subtitle}
                    </p>
                )}
            </div>
            <div className={`w-8 h-8 lg:w-12 lg:h-12 bg-gradient-to-r ${gradient} rounded-full flex items-center justify-center shadow-lg flex-shrink-0 ml-2 lg:ml-3 group-hover:scale-110 transition-transform`}>
                <span className="text-white text-sm lg:text-lg">{icon}</span>
            </div>
        </div>
    </div>
);

// Enhanced Risk Metric Component - Mobile Optimized
const RiskMetric = ({ label, value, isProfit, icon }) => (
    <div className="text-center p-2 lg:p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
        <div className="text-xl lg:text-2xl mb-1 lg:mb-2">{icon}</div>
        <p className="text-xs lg:text-sm text-gray-500 mb-1">{label}</p>
        <p className={`text-sm lg:text-lg font-bold ${isProfit !== undefined ? (isProfit ? 'text-green-600' : 'text-red-600') : 'text-gray-900'}`}>
            {value}
        </p>
    </div>
);

export default Dashboard;