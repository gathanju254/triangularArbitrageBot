// frontend/src/components/Opportunities.js
// frontend/src/components/Opportunities.jsx
import React, { useState, useEffect, useCallback, useMemo } from 'react';

const Opportunities = () => {
    const [opportunities, setOpportunities] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [sortConfig, setSortConfig] = useState({ key: 'profit_percentage', direction: 'desc' });
    const [minProfitFilter, setMinProfitFilter] = useState(0);
    const [lastUpdated, setLastUpdated] = useState(null);

    // Memoized fetch function
    const fetchOpportunities = useCallback(async () => {
        try {
            setError(null);
            const response = await fetch('/api/opportunities/');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            setOpportunities(data.opportunities || []);
            setLastUpdated(new Date());
            
            if (isLoading) setIsLoading(false);
        } catch (error) {
            console.error('Error fetching opportunities:', error);
            setError('Failed to fetch opportunities');
            if (isLoading) setIsLoading(false);
        }
    }, [isLoading]);

    useEffect(() => {
        fetchOpportunities();
        const interval = setInterval(fetchOpportunities, 2000);
        return () => clearInterval(interval);
    }, [fetchOpportunities]);

    // Filter and sort opportunities
    const processedOpportunities = useMemo(() => {
        let filtered = opportunities.filter(opp => 
            opp.profit_percentage >= minProfitFilter
        );

        // Sort opportunities
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
        if (profit >= 2.0) return 'text-green-700 bg-green-50 border-green-200';
        if (profit >= 1.0) return 'text-green-600 bg-green-25 border-green-100';
        if (profit >= 0.5) return 'text-yellow-600 bg-yellow-50 border-yellow-100';
        if (profit >= 0.2) return 'text-orange-600 bg-orange-50 border-orange-100';
        return 'text-red-600 bg-red-50 border-red-100';
    };

    const getProfitBadge = (profit) => {
        if (profit >= 2.0) return '🔥 Excellent';
        if (profit >= 1.0) return '⭐ Great';
        if (profit >= 0.5) return '👍 Good';
        if (profit >= 0.2) return '📈 Fair';
        return '📉 Low';
    };

    const formatTimestamp = (timestamp) => {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffSecs = Math.floor(diffMs / 1000);
        
        if (diffSecs < 60) return `${diffSecs}s ago`;
        if (diffSecs < 3600) return `${Math.floor(diffSecs / 60)}m ago`;
        return date.toLocaleTimeString();
    };

    const SortIcon = ({ columnKey }) => {
        if (sortConfig.key !== columnKey) {
            return <span className="text-gray-400">↕</span>;
        }
        return sortConfig.direction === 'asc' ? '↑' : '↓';
    };

    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
                <p className="text-gray-600">Loading opportunities...</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header Section */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h2 className="text-3xl font-bold text-gray-900">Trading Opportunities</h2>
                    <p className="text-gray-600 mt-1">Real-time arbitrage opportunities across exchanges</p>
                </div>
                
                {/* Stats and Filters */}
                <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
                    {/* Last Updated */}
                    {lastUpdated && (
                        <div className="text-sm text-gray-500 bg-gray-50 px-3 py-1 rounded-full">
                            Updated: {lastUpdated.toLocaleTimeString()}
                        </div>
                    )}
                    
                    {/* Profit Filter */}
                    <div className="flex items-center gap-2">
                        <label htmlFor="profitFilter" className="text-sm font-medium text-gray-700 whitespace-nowrap">
                            Min Profit:
                        </label>
                        <select
                            id="profitFilter"
                            value={minProfitFilter}
                            onChange={(e) => setMinProfitFilter(parseFloat(e.target.value))}
                            className="border border-gray-300 rounded-md px-3 py-1 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                            <option value={0}>All</option>
                            <option value={0.2}>0.2%+</option>
                            <option value={0.5}>0.5%+</option>
                            <option value={1.0}>1.0%+</option>
                            <option value={2.0}>2.0%+</option>
                        </select>
                    </div>
                </div>
            </div>

            {/* Error Banner */}
            {error && (
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
            )}

            {/* Opportunities Count */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center justify-between">
                    <div>
                        <span className="text-blue-800 font-medium">
                            {processedOpportunities.length} opportunity{processedOpportunities.length !== 1 ? 'ies' : ''} found
                        </span>
                        <span className="text-blue-600 text-sm ml-2">
                            (Filtered from {opportunities.length} total)
                        </span>
                    </div>
                    {minProfitFilter > 0 && (
                        <button
                            onClick={() => setMinProfitFilter(0)}
                            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                        >
                            Clear filter
                        </button>
                    )}
                </div>
            </div>

            {/* Opportunities Table */}
            {processedOpportunities.length === 0 ? (
                <div className="text-center py-12 bg-white rounded-xl shadow-sm border border-gray-200">
                    <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <span className="text-2xl">🔍</span>
                    </div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No opportunities found</h3>
                    <p className="text-gray-600 max-w-md mx-auto">
                        {minProfitFilter > 0 
                            ? `No opportunities found with minimum ${minProfitFilter}% profit. Try lowering the filter.`
                            : 'No arbitrage opportunities are currently available. The system is monitoring the markets.'}
                    </p>
                </div>
            ) : (
                <div className="bg-white shadow-xl rounded-xl border border-gray-200 overflow-hidden">
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
                                            className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 transition-colors"
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
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center space-x-2">
                                                <div className="w-2 h-8 bg-gradient-to-b from-blue-500 to-purple-600 rounded-full group-hover:from-blue-600 group-hover:to-purple-700 transition-colors"></div>
                                                <div>
                                                    <div className="text-sm font-semibold text-gray-900 font-mono">
                                                        {opp.triangle?.join(' → ') || 'N/A'}
                                                    </div>
                                                    <div className="text-xs text-gray-500">
                                                        Triangular path
                                                    </div>
                                                </div>
                                            </div>
                                        </td>

                                        {/* Profit Percentage */}
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className={`inline-flex flex-col px-3 py-2 rounded-lg border-2 ${getProfitColor(opp.profit_percentage)} transition-all group-hover:scale-105`}>
                                                <div className="text-lg font-bold font-mono">
                                                    {opp.profit_percentage?.toFixed(4) || '0.0000'}%
                                                </div>
                                                <div className="text-xs font-medium opacity-80">
                                                    {getProfitBadge(opp.profit_percentage)}
                                                </div>
                                            </div>
                                        </td>

                                        {/* Exchange Prices */}
                                        <td className="px-6 py-4">
                                            <div className="space-y-1 min-w-0">
                                                {Object.entries(opp.prices || {}).map(([pair, price]) => (
                                                    <div key={pair} className="flex justify-between items-center text-sm group-hover:text-gray-900 transition-colors">
                                                        <span className="font-medium text-gray-700 font-mono truncate max-w-[120px]">
                                                            {pair}
                                                        </span>
                                                        <span className="text-gray-600 font-mono ml-2">
                                                            {typeof price === 'number' ? price.toFixed(6) : price}
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>
                                        </td>

                                        {/* Timestamp */}
                                        <td className="px-6 py-4 whitespace-nowrap">
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
                    <div className="bg-gray-50 px-6 py-3 border-t border-gray-200">
                        <div className="flex justify-between items-center text-sm text-gray-600">
                            <span>
                                Showing {processedOpportunities.length} of {opportunities.length} opportunities
                            </span>
                            <span>
                                Sorted by {sortConfig.key.replace('_', ' ')} ({sortConfig.direction})
                            </span>
                        </div>
                    </div>
                </div>
            )}

            {/* Help Text */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-start">
                    <div className="flex-shrink-0 mt-1">
                        <span className="text-blue-500 text-lg">💡</span>
                    </div>
                    <div className="ml-3">
                        <h4 className="text-sm font-medium text-blue-900">How it works</h4>
                        <p className="text-sm text-blue-700 mt-1">
                            This table shows real-time triangular arbitrage opportunities. The system continuously monitors
                            price differences across trading pairs to identify profitable trading paths. Opportunities are
                            automatically sorted by profitability.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Opportunities;