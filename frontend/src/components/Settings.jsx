// src/components/Settings.js
import React, { useState, useEffect } from 'react';
import { arbitrageAPI } from '../utils/api';

const Settings = () => {
    const [settings, setSettings] = useState({
        minProfitThreshold: 0.2,
        maxPositionSize: 1000,
        maxDailyLoss: 100,
        enabledExchanges: ['binance'],
        tradingEnabled: false
    });
    const [isSaving, setIsSaving] = useState(false);
    const [saveMessage, setSaveMessage] = useState('');

    useEffect(() => {
        fetchSettings();
    }, []);

    const fetchSettings = async () => {
        try {
            const data = await arbitrageAPI.getSettings();
            if (data.settings) {
                setSettings(data.settings);
            }
        } catch (error) {
            console.error('Error fetching settings:', error);
        }
    };

    const handleSave = async () => {
        setIsSaving(true);
        setSaveMessage('');
        
        try {
            await arbitrageAPI.updateSettings(settings);
            setSaveMessage('Settings saved successfully!');
        } catch (error) {
            setSaveMessage('Error saving settings: ' + error.message);
        } finally {
            setIsSaving(false);
        }
    };

    const handleInputChange = (key, value) => {
        setSettings(prev => ({
            ...prev,
            [key]: value
        }));
    };

    const handleExchangeToggle = (exchange) => {
        setSettings(prev => {
            const enabledExchanges = prev.enabledExchanges.includes(exchange)
                ? prev.enabledExchanges.filter(e => e !== exchange)
                : [...prev.enabledExchanges, exchange];
            
            return {
                ...prev,
                enabledExchanges
            };
        });
    };

    return (
        <div>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Settings</h2>
            
            <div className="bg-white shadow rounded-lg">
                <div className="px-6 py-4 border-b border-gray-200">
                    <h3 className="text-lg font-medium text-gray-900">Trading Configuration</h3>
                </div>
                
                <div className="p-6 space-y-6">
                    {/* Minimum Profit Threshold */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Minimum Profit Threshold (%)
                        </label>
                        <input
                            type="number"
                            step="0.01"
                            value={settings.minProfitThreshold}
                            onChange={(e) => handleInputChange('minProfitThreshold', parseFloat(e.target.value))}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <p className="mt-1 text-sm text-gray-500">
                            Minimum profit percentage required to execute a trade
                        </p>
                    </div>

                    {/* Maximum Position Size */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Maximum Position Size ($)
                        </label>
                        <input
                            type="number"
                            step="10"
                            value={settings.maxPositionSize}
                            onChange={(e) => handleInputChange('maxPositionSize', parseFloat(e.target.value))}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <p className="mt-1 text-sm text-gray-500">
                            Maximum amount to risk per trade
                        </p>
                    </div>

                    {/* Maximum Daily Loss */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Maximum Daily Loss ($)
                        </label>
                        <input
                            type="number"
                            step="10"
                            value={settings.maxDailyLoss}
                            onChange={(e) => handleInputChange('maxDailyLoss', parseFloat(e.target.value))}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        <p className="mt-1 text-sm text-gray-500">
                            Stop trading if daily loss exceeds this amount
                        </p>
                    </div>

                    {/* Enabled Exchanges */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Enabled Exchanges
                        </label>
                        <div className="space-y-2">
                            {['binance', 'kraken'].map((exchange) => (
                                <div key={exchange} className="flex items-center">
                                    <input
                                        type="checkbox"
                                        id={`exchange-${exchange}`}
                                        checked={settings.enabledExchanges.includes(exchange)}
                                        onChange={() => handleExchangeToggle(exchange)}
                                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                                    />
                                    <label htmlFor={`exchange-${exchange}`} className="ml-2 block text-sm text-gray-700 capitalize">
                                        {exchange}
                                    </label>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Trading Enabled */}
                    <div className="flex items-center">
                        <input
                            type="checkbox"
                            id="trading-enabled"
                            checked={settings.tradingEnabled}
                            onChange={(e) => handleInputChange('tradingEnabled', e.target.checked)}
                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <label htmlFor="trading-enabled" className="ml-2 block text-sm font-medium text-gray-700">
                            Enable Automated Trading
                        </label>
                    </div>

                    {/* Save Button */}
                    <div className="flex items-center justify-between pt-4 border-t border-gray-200">
                        <div>
                            {saveMessage && (
                                <p className={`text-sm ${
                                    saveMessage.includes('successfully') 
                                        ? 'text-green-600' 
                                        : 'text-red-600'
                                }`}>
                                    {saveMessage}
                                </p>
                            )}
                        </div>
                        <button
                            onClick={handleSave}
                            disabled={isSaving}
                            className={`px-4 py-2 bg-blue-600 text-white rounded-md font-medium ${
                                isSaving ? 'opacity-50 cursor-not-allowed' : 'hover:bg-blue-700'
                            }`}
                        >
                            {isSaving ? 'Saving...' : 'Save Settings'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Settings;