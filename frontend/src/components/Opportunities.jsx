// frontend/src/components/Opportunities.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { arbitrageAPI } from '../utils/api';

const Opportunities = () => {
    const [opportunities, setOpportunities] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [sortConfig, setSortConfig] = useState({ key: 'profit_percentage', direction: 'desc' });
    const [minProfitFilter, setMinProfitFilter] = useState(0);
    const [lastUpdated, setLastUpdated] = useState(null);
    const [viewMode, setViewMode] = useState('table'); // 'table' or 'card'

    // Memoized fetch function
    const fetchOpportunities = useCallback(async () => {
        try {
            setError(null);
            const data = await arbitrageAPI.getOpportunities();
            
            setOpportunities(data.opportunities || []);
            setLastUpdated(new Date());
            
            if (isLoading) setIsLoading(false);
        } catch (error) {
            console.error('Error fetching opportunities:', error);
            setError(`Failed to fetch opportunities: ${error.message}`);
            if (isLoading) setIsLoading(false);
        }
    }, [isLoading]);

    useEffect(() => {
        fetchOpportunities();
        const interval = setInterval(fetchOpportunities, 5000);
        return () => clearInterval(interval);
    }, [fetchOpportunities]);

    // Filter and sort opportunities
    const processedOpportunities = useMemo(() => {
        let filtered = opportunities.filter(opp => 
            opp.profit_percentage >= minProfitFilter
        );

        filtered.sort((a, b) => {
            const aValue = a[sortConfig.key];
            const bValue = b[sortConfig.key];
            
            if (aValue < bValue) {
                return sortConfig.direction === 'asc' ? -1 : 1;
            }
            if (aValue > bValue) {
                return sortConfig.direction === 'asc' ? 1 : -1;
            }
            return 0;
        });

        return filtered;
    }, [opportunities, minProfitFilter, sortConfig]);

    const handleSort = (key) => {
        setSortConfig(current => ({
            key,
            direction: current.key === key && current.direction === 'asc' ? 'desc' : 'asc'
        }));
    };

    const getProfitColor = (profit) => {
        if (profit >= 2.0) return 'from-green-500 to-emerald-600 text-white';
        if (profit >= 1.0) return 'from-green-400 to-green-600 text-white';
        if (profit >= 0.5) return 'from-yellow-400 to-yellow-600 text-gray-900';
        if (profit >= 0.2) return 'from-orange-400 to-orange-500 text-white';
        return 'from-red-400 to-red-500 text-white';
    };

    const getProfitBadge = (profit) => {
        if (profit >= 2.0) return '🔥 Excellent';
        if (profit >= 1.0) return '⭐ Great';
        if (profit >= 0.5) return '👍 Good';
        if (profit >= 0.2) return '📈 Fair';
        return '📉 Low';
    };

    const getProfitIcon = (profit) => {
        if (profit >= 2.0) return '🚀';
        if (profit >= 1.0) return '⭐';
        if (profit >= 0.5) return '📊';
        if (profit >= 0.2) return '↗️';
        return '↘️';
    };

    const formatTimestamp = (timestamp) => {
        try {
            const date = new Date(timestamp);
            const now = new Date();
            const diffMs = now - date;
            const diffSecs = Math.floor(diffMs / 1000);
            
            if (diffSecs < 60) return `${diffSecs}s ago`;
            if (diffSecs < 3600) return `${Math.floor(diffSecs / 60)}m ago`;
            return date.toLocaleTimeString();
        } catch (e) {
            return 'Unknown';
        }
    };

    const SortIcon = ({ columnKey }) => {
        if (sortConfig.key !== columnKey) {
            return <span className="text-gray-400">↕</span>;
        }
        return sortConfig.direction === 'asc' ? '↑' : '↓';
    };

    // Card View Component
    const OpportunityCard = ({ opp, index }) => (
        <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-4 hover:shadow-xl transition-all duration-300 hover:scale-[1.02]">
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
                <div className="flex items-center space-x-2 flex-1 min-w-0">
                    <div className={`w-3 h-8 bg-gradient-to-b ${getProfitColor(opp.profit_percentage)} rounded-full`}></div>
                    <div className="min-w-0 flex-1">
                        <h3 className="text-sm font-semibold text-gray-900 font-mono truncate">
                            {opp.triangle?.join(' → ') || 'N/A'}
                        </h3>
                        <p className="text-xs text-gray-500">Triangular path</p>
                    </div>
                </div>
                <div className={`px-2 py-1 rounded-full text-xs font-medium bg-gradient-to-r ${getProfitColor(opp.profit_percentage)}`}>
                    {getProfitIcon(opp.profit_percentage)}
                </div>
            </div>

            {/* Profit Section */}
            <div className="mb-3">
                <div className={`inline-flex items-center px-3 py-2 rounded-lg bg-gradient-to-r ${getProfitColor(opp.profit_percentage)} shadow-md`}>
                    <span className="text-lg font-bold font-mono mr-2">
                        {opp.profit_percentage?.toFixed(4)}%
                    </span>
                    <span className="text-xs font-medium opacity-90">
                        {getProfitBadge(opp.profit_percentage)}
                    </span>
                </div>
            </div>

            {/* Prices */}
            <div className="space-y-2 mb-3">
                {Object.entries(opp.prices || {}).slice(0, 3).map(([pair, price]) => (
                    <div key={pair} className="flex justify-between items-center text-sm">
                        <span className="font-medium text-gray-700 font-mono text-xs truncate flex-1">
                            {pair}
                        </span>
                        <span className="text-gray-600 font-mono text-xs ml-2">
                            {typeof price === 'number' ? price.toFixed(6) : price}
                        </span>
                    </div>
                ))}
            </div>

            {/* Footer */}
            <div className="flex justify-between items-center pt-2 border-t border-gray-100">
                <span className="text-xs text-gray-500">
                    {formatTimestamp(opp.timestamp)}
                </span>
                <span className="text-xs text-gray-400">
                    {opp.timestamp ? new Date(opp.timestamp).toLocaleDateString() : 'N/A'}
                </span>
            </div>
        </div>
    );

    // Loading State
    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center py-12">
                <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mb-4"></div>
                <p className="text-gray-600 text-lg">Scanning for opportunities...</p>
                <p className="text-gray-400 text-sm mt-2">Monitoring markets in real-time</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header Section */}
            <div className="bg-gradient-to-r from-blue-600 to-purple-700 rounded-2xl p-6 text-white">
                <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
                    <div>
                        <h1 className="text-2xl lg:text-3xl font-bold mb-2">Trading Opportunities</h1>
                        <p className="text-blue-100 opacity-90">Real-time arbitrage opportunities across exchanges</p>
                    </div>
                    
                    {/* Stats and Controls */}
                    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 w-full lg:w-auto">
                        {/* Last Updated */}
                        {lastUpdated && (
                            <div className="bg-white/20 backdrop-blur-sm px-3 py-2 rounded-lg">
                                <div className="text-blue-100 text-sm">Last updated</div>
                                <div className="text-white font-medium">{lastUpdated.toLocaleTimeString()}</div>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Controls Bar */}
            <div className="bg-white rounded-xl shadow-lg border border-gray-200 p-4">
                <div className="flex flex-col lg:flex-row gap-4 justify-between items-start lg:items-center">
                    {/* View Toggle */}
                    <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-700">View:</span>
                        <div className="flex bg-gray-100 rounded-lg p-1">
                            <button
                                onClick={() => setViewMode('table')}
                                className={`px-3 py-1 rounded-md text-sm font-medium transition-all ${
                                    viewMode === 'table' 
                                        ? 'bg-white shadow-sm text-blue-600' 
                                        : 'text-gray-600 hover:text-gray-900'
                                }`}
                            >
                                Table
                            </button>
                            <button
                                onClick={() => setViewMode('card')}
                                className={`px-3 py-1 rounded-md text-sm font-medium transition-all ${
                                    viewMode === 'card' 
                                        ? 'bg-white shadow-sm text-blue-600' 
                                        : 'text-gray-600 hover:text-gray-900'
                                }`}
                            >
                                Cards
                            </button>
                        </div>
                    </div>

                    {/* Profit Filter */}
                    <div className="flex items-center gap-3">
                        <label htmlFor="profitFilter" className="text-sm font-medium text-gray-700 whitespace-nowrap">
                            Min Profit:
                        </label>
                        <select
                            id="profitFilter"
                            value={minProfitFilter}
                            onChange={(e) => setMinProfitFilter(parseFloat(e.target.value))}
                            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white"
                        >
                            <option value={0}>All Opportunities</option>
                            <option value={0.2}>0.2%+ Profit</option>
                            <option value={0.5}>0.5%+ Profit</option>
                            <option value={1.0}>1.0%+ Profit</option>
                            <option value={2.0}>2.0%+ Profit</option>
                        </select>
                    </div>

                    {/* Results Count */}
                    <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-2">
                        <div className="text-blue-800 font-medium text-sm">
                            <span className="hidden sm:inline">Found </span>
                            {processedOpportunities.length} opportunity{processedOpportunities.length !== 1 ? 'ies' : ''}
                            <span className="text-blue-600 text-xs ml-2 hidden sm:inline">
                                (of {opportunities.length} total)
                            </span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Error Banner */}
            {error && (
                <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-center justify-between">
                    <div className="flex items-center">
                        <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center mr-3">
                            <svg className="w-4 h-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                            </svg>
                        </div>
                        <div>
                            <span className="text-red-800 font-medium block">Connection Issue</span>
                            <span className="text-red-600 text-sm">{error}</span>
                        </div>
                    </div>
                    <button
                        onClick={() => setError(null)}
                        className="text-red-400 hover:text-red-600 p-1"
                    >
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                        </svg>
                    </button>
                </div>
            )}

            {/* Opportunities Display */}
            {processedOpportunities.length === 0 ? (
                <div className="text-center py-16 bg-white rounded-2xl shadow-sm border border-gray-200">
                    <div className="w-20 h-20 bg-gradient-to-br from-blue-100 to-purple-100 rounded-full flex items-center justify-center mx-auto mb-6">
                        <span className="text-3xl">🔍</span>
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-3">No opportunities found</h3>
                    <p className="text-gray-600 max-w-md mx-auto mb-6">
                        {minProfitFilter > 0 
                            ? `No opportunities meet your ${minProfitFilter}% profit filter. Try adjusting the filter to see more results.`
                            : 'The system is actively monitoring markets. New opportunities will appear here when detected.'}
                    </p>
                    {minProfitFilter > 0 && (
                        <button
                            onClick={() => setMinProfitFilter(0)}
                            className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
                        >
                            Show All Opportunities
                        </button>
                    )}
                </div>
            ) : viewMode === 'table' ? (
                /* Table View */
                <div className="bg-white shadow-xl rounded-2xl border border-gray-200 overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    {[
                                        { key: 'triangle', label: 'Trading Pair' },
                                        { key: 'profit_percentage', label: 'Profit %' },
                                        { key: 'prices', label: 'Exchange Prices' },
                                        { key: 'timestamp', label: 'Last Updated' }
                                    ].map(({ key, label }) => (
                                        <th
                                            key={key}
                                            className="px-4 lg:px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
                                            onClick={() => handleSort(key)}
                                        >
                                            <div className="flex items-center gap-1">
                                                {label}
                                                <SortIcon columnKey={key} />
                                            </div>
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {processedOpportunities.map((opp, index) => (
                                    <tr 
                                        key={index} 
                                        className="hover:bg-gray-50 transition-colors duration-150 group"
                                    >
                                        {/* Trading Pair */}
                                        <td className="px-4 lg:px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center space-x-3">
                                                <div className={`w-2 h-10 bg-gradient-to-b ${getProfitColor(opp.profit_percentage)} rounded-full group-hover:scale-110 transition-transform`}></div>
                                                <div className="min-w-0">
                                                    <div className="text-sm font-semibold text-gray-900 font-mono truncate max-w-[150px] lg:max-w-none">
                                                        {opp.triangle?.join(' → ') || 'N/A'}
                                                    </div>
                                                    <div className="text-xs text-gray-500 flex items-center gap-1">
                                                        <span>Triangular path</span>
                                                        <span className={`text-xs ${getProfitColor(opp.profit_percentage).split(' ')[0]} font-medium`}>
                                                            {getProfitIcon(opp.profit_percentage)}
                                                        </span>
                                                    </div>
                                                </div>
                                            </div>
                                        </td>

                                        {/* Profit Percentage */}
                                        <td className="px-4 lg:px-6 py-4 whitespace-nowrap">
                                            <div className={`inline-flex flex-col items-center px-3 py-2 rounded-xl bg-gradient-to-r ${getProfitColor(opp.profit_percentage)} shadow-sm transition-all group-hover:scale-105`}>
                                                <div className="text-base font-bold font-mono">
                                                    {opp.profit_percentage?.toFixed(4)}%
                                                </div>
                                                <div className="text-xs font-medium opacity-90 mt-1">
                                                    {getProfitBadge(opp.profit_percentage)}
                                                </div>
                                            </div>
                                        </td>

                                        {/* Exchange Prices */}
                                        <td className="px-4 lg:px-6 py-4">
                                            <div className="space-y-2 min-w-0">
                                                {Object.entries(opp.prices || {}).map(([pair, price]) => (
                                                    <div key={pair} className="flex justify-between items-center text-sm group-hover:text-gray-900 transition-colors">
                                                        <span className="font-medium text-gray-700 font-mono text-xs truncate max-w-[100px] lg:max-w-[120px]">
                                                            {pair}
                                                        </span>
                                                        <span className="text-gray-600 font-mono text-xs ml-2">
                                                            {typeof price === 'number' ? price.toFixed(6) : price}
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>
                                        </td>

                                        {/* Timestamp */}
                                        <td className="px-4 lg:px-6 py-4 whitespace-nowrap">
                                            <div className="flex flex-col">
                                                <span className="text-sm font-medium text-gray-900">
                                                    {formatTimestamp(opp.timestamp)}
                                                </span>
                                                <span className="text-xs text-gray-500">
                                                    {opp.timestamp ? new Date(opp.timestamp).toLocaleDateString() : 'N/A'}
                                                </span>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Table Footer */}
                    <div className="bg-gray-50 px-4 lg:px-6 py-3 border-t border-gray-200">
                        <div className="flex flex-col sm:flex-row justify-between items-center gap-2 text-sm text-gray-600">
                            <span>
                                Showing {processedOpportunities.length} of {opportunities.length} opportunities
                            </span>
                            <span className="text-xs sm:text-sm">
                                Sorted by {sortConfig.key.replace('_', ' ')} ({sortConfig.direction})
                            </span>
                        </div>
                    </div>
                </div>
            ) : (
                /* Card View */
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 lg:gap-6">
                    {processedOpportunities.map((opp, index) => (
                        <OpportunityCard key={index} opp={opp} index={index} />
                    ))}
                </div>
            )}

            {/* Help Text */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-100 border border-blue-200 rounded-2xl p-6">
                <div className="flex items-start">
                    <div className="flex-shrink-0 mt-1">
                        <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                            <span className="text-white text-lg">💡</span>
                        </div>
                    </div>
                    <div className="ml-4">
                        <h4 className="text-lg font-semibold text-blue-900">How Arbitrage Opportunities Work</h4>
                        <p className="text-blue-800 mt-2 leading-relaxed">
                            The system continuously monitors price differences across trading pairs to identify profitable triangular paths. 
                            Each opportunity represents a potential profit after accounting for trading fees and market spreads. 
                            Higher percentage values indicate more profitable opportunities.
                        </p>
                        <div className="mt-3 flex flex-wrap gap-2">
                            <span className="px-3 py-1 bg-blue-200 text-blue-800 rounded-full text-xs font-medium">Real-time Data</span>
                            <span className="px-3 py-1 bg-green-200 text-green-800 rounded-full text-xs font-medium">Auto-refresh</span>
                            <span className="px-3 py-1 bg-purple-200 text-purple-800 rounded-full text-xs font-medium">Multi-exchange</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Opportunities;