// frontend/src/components/Opportunities.js
import React, { useState, useEffect } from 'react';

const Opportunities = () => {
    const [opportunities, setOpportunities] = useState([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetchOpportunities();
        const interval = setInterval(fetchOpportunities, 2000);
        return () => clearInterval(interval);
    }, []);

    const fetchOpportunities = async () => {
        try {
            const response = await fetch('/api/opportunities/');
            const data = await response.json();
            setOpportunities(data.opportunities || []);
            setIsLoading(false);
        } catch (error) {
            console.error('Error fetching opportunities:', error);
            setIsLoading(false);
        }
    };

    const getProfitColor = (profit) => {
        if (profit > 1) return 'text-green-600';
        if (profit > 0.5) return 'text-yellow-600';
        return 'text-red-600';
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    return (
        <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Arbitrage Opportunities</h2>
            
            {opportunities.length === 0 ? (
                <div className="text-center py-8">
                    <p className="text-gray-500">No arbitrage opportunities found at the moment.</p>
                </div>
            ) : (
                <div className="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
                    <table className="min-w-full divide-y divide-gray-300">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Triangle
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Profit %
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Prices
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                    Timestamp
                                </th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {opportunities.map((opp, index) => (
                                <tr key={index} className="hover:bg-gray-50">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-medium text-gray-900">
                                            {opp.triangle.join(' → ')}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className={`text-sm font-bold ${getProfitColor(opp.profit_percentage)}`}>
                                            {opp.profit_percentage.toFixed(4)}%
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm text-gray-500">
                                            {Object.entries(opp.prices).map(([pair, price]) => (
                                                <div key={pair}>
                                                    {pair}: {price.toFixed(6)}
                                                </div>
                                            ))}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                        {new Date(opp.timestamp).toLocaleTimeString()}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

export default Opportunities;