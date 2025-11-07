// frontend/src/constants/exchanges.js

export const EXCHANGES = [
  { 
    id: 1, 
    code: 'binance',  
    name: 'Binance',  
    requires_passphrase: false, 
    default_enabled: true, 
    fees: 0.1, 
    icon: '🏦',
    description: 'World\'s largest crypto exchange',
    supported_features: ['spot', 'futures', 'margin'],
    countries: ['Global'],
    rating: 4.8
  },
  { 
    id: 2, 
    code: 'kucoin',   
    name: 'KuCoin',   
    requires_passphrase: true,  
    default_enabled: true, 
    fees: 0.1, 
    icon: '💎',
    description: 'People\'s exchange with wide altcoin selection',
    supported_features: ['spot', 'futures'],
    countries: ['Global'],
    rating: 4.3
  },
  { 
    id: 3, 
    code: 'coinbase', 
    name: 'Coinbase', 
    requires_passphrase: true,  
    default_enabled: false, 
    fees: 0.5, 
    icon: '🏛️',
    description: 'US-based regulated exchange',
    supported_features: ['spot'],
    countries: ['US', 'Europe'],
    rating: 4.5
  },
  { 
    id: 4, 
    code: 'kraken',   
    name: 'Kraken',   
    requires_passphrase: false, 
    default_enabled: false, 
    fees: 0.26, 
    icon: '🐙',
    description: 'Professional trading platform',
    supported_features: ['spot', 'futures', 'margin'],
    countries: ['Global'],
    rating: 4.6
  },
  { 
    id: 5, 
    code: 'huobi',    
    name: 'Huobi',    
    requires_passphrase: false, 
    default_enabled: false, 
    fees: 0.2, 
    icon: '🔥',
    description: 'Leading Asian exchange',
    supported_features: ['spot', 'futures'],
    countries: ['Asia'],
    rating: 4.2
  },
  { 
    id: 6, 
    code: 'okx',    
    name: 'OKX',    
    requires_passphrase: true, 
    default_enabled: false, 
    fees: 0.08, 
    icon: '🚀',
    description: 'Leading global crypto exchange with advanced trading',
    supported_features: ['spot', 'futures', 'options', 'margin'],
    countries: ['Global'],
    rating: 4.4
  }
];

export const getExchangeByCode = (code) => 
  EXCHANGES.find(e => String(e.code).toLowerCase() === String(code).toLowerCase()) || null;

export const getExchangeById = (id) => 
  EXCHANGES.find(e => e.id === parseInt(id)) || null;

export const getEnabledExchanges = () => 
  EXCHANGES.filter(e => e.default_enabled);

export const getExchangeDescription = (code) => {
  const exchange = getExchangeByCode(code);
  return exchange ? exchange.description : 'Cryptocurrency exchange';
};

export const EXCHANGE_CODES = EXCHANGES.map(e => e.code);

export default EXCHANGES;