// src/components/Settings.jsx
import React, { useState, useEffect } from 'react';
import { arbitrageAPI } from '../utils/api';

const Settings = () => {
    const [settings, setSettings] = useState({
        minProfitThreshold: 0.2,
        maxPositionSize: 1000,
        maxDailyLoss: 100,
        baseBalance: 1000,
        tradeSizeFraction: 0.01, // NEW: Configurable trade size fraction
        enabledExchanges: ['binance'],
        tradingEnabled: false,
        maxDrawdown: 10,
        slippageTolerance: 0.1,
        autoRestart: true
    });
    
    const [isSaving, setIsSaving] = useState(false);
    const [saveMessage, setSaveMessage] = useState('');
    const [activeSection, setActiveSection] = useState('trading');

    useEffect(() => {
        fetchSettings();
    }, []);

    const fetchSettings = async () => {
        try {
            const data = await arbitrageAPI.getSettings();
            if (data && data.settings) {
                // Normalize backend keys -> frontend state
                const s = data.settings;
                setSettings(prev => ({
                    ...prev,
                    minProfitThreshold: s.minProfitThreshold ?? prev.minProfitThreshold,
                    maxPositionSize: s.maxPositionSize ?? prev.maxPositionSize,
                    maxDailyLoss: s.maxDailyLoss ?? prev.maxDailyLoss,
                    baseBalance: s.baseBalance ?? prev.baseBalance,
                    tradeSizeFraction: s.tradeSizeFraction ?? prev.tradeSizeFraction, // NEW
                    maxDrawdown: s.maxDrawdown ?? prev.maxDrawdown,
                    tradingEnabled: s.tradingEnabled ?? prev.tradingEnabled,
                    enabledExchanges: s.enabledExchanges ?? prev.enabledExchanges
                }));
            }
        } catch (error) {
            console.error('Error fetching settings:', error);
        }
    };

    const handleSave = async () => {
        setIsSaving(true);
        setSaveMessage('');

        try {
            // Prepare payload matching backend expected keys
            const payload = {
                minProfitThreshold: Number(settings.minProfitThreshold),
                maxPositionSize: Number(settings.maxPositionSize),
                maxDailyLoss: Number(settings.maxDailyLoss),
                baseBalance: Number(settings.baseBalance),
                tradeSizeFraction: Number(settings.tradeSizeFraction), // NEW
                maxDrawdown: Number(settings.maxDrawdown),
                // Optional toggles / arrays
                enabledExchanges: settings.enabledExchanges,
                tradingEnabled: settings.tradingEnabled,
                slippageTolerance: Number(settings.slippageTolerance),
                autoRestart: Boolean(settings.autoRestart)
            };

            const resp = await arbitrageAPI.updateSettings(payload);
            setSaveMessage('Settings saved successfully!');
            // Refresh settings
            setTimeout(() => setSaveMessage(''), 3000);
        } catch (error) {
            setSaveMessage('Error saving settings: ' + (error.message || error));
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

    const resetToDefaults = () => {
        setSettings({
            minProfitThreshold: 0.2,
            maxPositionSize: 1000,
            maxDailyLoss: 100,
            baseBalance: 1000,
            tradeSizeFraction: 0.01, // NEW
            enabledExchanges: ['binance'],
            tradingEnabled: false,
            maxDrawdown: 10,
            slippageTolerance: 0.1,
            autoRestart: true
        });
    };

    // Settings sections configuration
    const sections = {
        trading: {
            title: 'Trading Configuration',
            icon: '⚡',
            fields: [
                {
                    key: 'minProfitThreshold',
                    label: 'Minimum Profit Threshold (%)',
                    type: 'number',
                    step: 0.01,
                    min: 0.01,
                    max: 5,
                    description: 'Minimum profit percentage required to execute a trade'
                },
                {
                    key: 'maxPositionSize',
                    label: 'Maximum Position Size ($)',
                    type: 'number',
                    step: 10,
                    min: 10,
                    max: 10000,
                    description: 'Maximum amount to risk per trade'
                },
                {
                    key: 'baseBalance',
                    label: 'Starting Balance ($)',
                    type: 'number',
                    step: 1,
                    min: 100,
                    max: 100000,
                    description: 'Starting balance used for risk calculations'
                },
                // NEW: Trade size fraction field
                {
                    key: 'tradeSizeFraction',
                    label: 'Trade Size Fraction (%)',
                    type: 'number',
                    step: 0.01,
                    min: 0.01,
                    max: 10,
                    description: 'Percentage of base balance to use per trade (e.g., 1% = 0.01)'
                }
            ]
        },
        risk: {
            title: 'Risk Management',
            icon: '🛡️',
            fields: [
                {
                    key: 'maxDailyLoss',
                    label: 'Maximum Daily Loss ($)',
                    type: 'number',
                    step: 10,
                    min: 10,
                    max: 5000,
                    description: 'Stop trading if daily loss exceeds this amount'
                },
                {
                    key: 'maxDrawdown',
                    label: 'Maximum Drawdown (%)',
                    type: 'number',
                    step: 1,
                    min: 1,
                    max: 50,
                    description: 'Maximum allowed portfolio drawdown'
                },
                {
                    key: 'slippageTolerance',
                    label: 'Slippage Tolerance (%)',
                    type: 'number',
                    step: 0.01,
                    min: 0.01,
                    max: 1,
                    description: 'Maximum allowed price slippage per trade'
                }
            ]
        },
        exchanges: {
            title: 'Exchanges & Automation',
            icon: '🌐',
            fields: [
                {
                    key: 'enabledExchanges',
                    label: 'Enabled Exchanges',
                    type: 'checkboxes',
                    options: [
                        { value: 'binance', label: 'Binance' },
                        { value: 'kraken', label: 'Kraken' },
                        { value: 'coinbase', label: 'Coinbase' },
                        { value: 'kucoin', label: 'KuCoin' }
                    ],
                    description: 'Select exchanges to monitor for opportunities'
                },
                {
                    key: 'tradingEnabled',
                    label: 'Enable Automated Trading',
                    type: 'toggle',
                    description: 'Allow the system to execute trades automatically'
                },
                {
                    key: 'autoRestart',
                    label: 'Auto-Restart on Error',
                    type: 'toggle',
                    description: 'Automatically restart trading after connection errors'
                }
            ]
        }
    };

    /* renderField: minimal controls for number/toggle/checkboxes */
    const renderField = (field) => {
        switch (field.type) {
            case 'number':
                return (
                    <div key={field.key}>
                        <label className="block text-sm font-medium text-gray-700 mb-2">{field.label}</label>
                        <input
                            type="number"
                            step={field.step || 1}
                            min={field.min}
                            max={field.max}
                            value={settings[field.key]}
                            onChange={(e) => handleInputChange(field.key, e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                        {field.description && <p className="mt-1 text-xs text-gray-500">{field.description}</p>}
                    </div>
                );
            case 'checkboxes':
                return (
                    <div key={field.key}>
                        <label className="block text-sm font-medium text-gray-700 mb-2">{field.label}</label>
                        <div className="flex flex-wrap gap-2">
                            {field.options.map(opt => (
                                <label key={opt.value} className="inline-flex items-center space-x-2">
                                    <input
                                        type="checkbox"
                                        checked={settings.enabledExchanges.includes(opt.value)}
                                        onChange={() => handleExchangeToggle(opt.value)}
                                        className="form-checkbox"
                                    />
                                    <span className="text-sm">{opt.label}</span>
                                </label>
                            ))}
                        </div>
                        {field.description && <p className="mt-1 text-xs text-gray-500">{field.description}</p>}
                    </div>
                );
            case 'toggle':
                return (
                    <div key={field.key} className="flex items-center justify-between">
                        <div>
                            <label className="text-sm font-medium text-gray-700">{field.label}</label>
                            {field.description && <p className="text-xs text-gray-500">{field.description}</p>}
                        </div>
                        <div>
                            <input
                                type="checkbox"
                                checked={settings[field.key]}
                                onChange={(e) => handleInputChange(field.key, e.target.checked)}
                                className="form-toggle"
                            />
                        </div>
                    </div>
                );
            default:
                return null;
        }
    };

    return (
        <div className="max-w-6xl mx-auto">
            <div className="flex flex-col lg:flex-row gap-6">
                {/* Mobile Navigation - Horizontal Scroll */}
                <div className="lg:hidden overflow-x-auto">
                    <div className="flex space-x-2 pb-2">
                        {Object.entries(sections).map(([key, section]) => (
                            <button
                                key={key}
                                onClick={() => setActiveSection(key)}
                                className={`flex-shrink-0 px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                                    activeSection === key
                                        ? 'bg-blue-600 text-white shadow-lg'
                                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                            >
                                <span className="mr-2">{section.icon}</span>
                                {section.title.split(' ')[0]}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Desktop Navigation - Vertical */}
                <div className="hidden lg:block w-64 flex-shrink-0">
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 sticky top-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-4">Settings</h3>
                        <nav className="space-y-2">
                            {Object.entries(sections).map(([key, section]) => (
                                <button
                                    key={key}
                                    onClick={() => setActiveSection(key)}
                                    className={`w-full text-left px-4 py-3 rounded-lg font-medium transition-all duration-200 ${
                                        activeSection === key
                                            ? 'bg-blue-50 text-blue-700 border border-blue-200 shadow-sm'
                                            : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                                    }`}
                                >
                                    <div className="flex items-center">
                                        <span className="text-lg mr-3">{section.icon}</span>
                                        <span>{section.title}</span>
                                    </div>
                                </button>
                            ))}
                        </nav>
                    </div>
                </div>

                {/* Settings Content */}
                <div className="flex-1">
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
                        {/* Header */}
                        <div className="px-6 py-4 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-white">
                            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
                                <div>
                                    <h2 className="text-2xl font-bold text-gray-900">
                                        {sections[activeSection].icon} {sections[activeSection].title}
                                    </h2>
                                    <p className="text-gray-600 mt-1">
                                        Configure your trading preferences and risk parameters
                                    </p>
                                </div>
                                
                                {/* Mobile Section Indicator */}
                                <div className="lg:hidden mt-2 sm:mt-0">
                                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                                        {sections[activeSection].title}
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Settings Form */}
                        <div className="p-6">
                            <div className="space-y-6">
                                {sections[activeSection].fields.map(renderField)}
                            </div>

                            {/* Action Buttons */}
                            <div className="mt-8 pt-6 border-t border-gray-200">
                                <div className="flex flex-col sm:flex-row gap-3 justify-between items-center">
                                    <div className="flex-1">
                                        {saveMessage && (
                                            <div className={`inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium ${
                                                saveMessage.includes('successfully') 
                                                    ? 'bg-green-100 text-green-800 border border-green-200' 
                                                    : 'bg-red-100 text-red-800 border border-red-200'
                                            }`}>
                                                {saveMessage.includes('successfully') ? '✅' : '❌'} {saveMessage}
                                            </div>
                                        )}
                                    </div>
                                    
                                    <div className="flex gap-3">
                                        <button
                                            onClick={resetToDefaults}
                                            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                                        >
                                            Reset Defaults
                                        </button>
                                        
                                        <button
                                            onClick={handleSave}
                                            disabled={isSaving}
                                            className={`px-6 py-2 bg-blue-600 text-white rounded-lg font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                                                isSaving 
                                                    ? 'opacity-50 cursor-not-allowed' 
                                                    : 'hover:bg-blue-700 shadow-lg hover:shadow-xl transform hover:scale-105'
                                            }`}
                                        >
                                            {isSaving ? (
                                                <span className="flex items-center">
                                                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                                    </svg>
                                                    Saving...
                                                </span>
                                            ) : (
                                                'Save Settings'
                                            )}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Quick Stats */}
                    <div className="mt-6 grid grid-cols-1 sm:grid-cols-3 gap-4">
                        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                            <div className="text-sm font-medium text-blue-800">Profit Threshold</div>
                            <div className="text-2xl font-bold text-blue-900">{settings.minProfitThreshold}%</div>
                        </div>
                        <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                            <div className="text-sm font-medium text-green-800">Position Size</div>
                            <div className="text-2xl font-bold text-green-900">${settings.maxPositionSize}</div>
                        </div>
                        <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                            <div className="text-sm font-medium text-purple-800">Daily Loss Limit</div>
                            <div className="text-2xl font-bold text-purple-900">${settings.maxDailyLoss}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Settings;