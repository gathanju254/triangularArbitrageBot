// frontend/src/constants/trading.js

export const ORDER_TYPES = {
  MARKET: 'market',
  LIMIT: 'limit',
  STOP: 'stop',
  STOP_LIMIT: 'stop_limit',
};

export const ORDER_SIDES = {
  BUY: 'buy',
  SELL: 'sell',
};

export const ORDER_STATUS = {
  PENDING: 'pending',
  OPEN: 'open',
  CLOSED: 'closed',
  CANCELLED: 'cancelled',
  EXPIRED: 'expired',
  REJECTED: 'rejected',
  PARTIALLY_FILLED: 'partially_filled',
  FILLED: 'filled',
};

export const STRATEGY_TYPES = {
  MANUAL: 'manual',
  AUTO: 'auto',
  SEMI_AUTO: 'semi_auto',
  ARBITRAGE: 'arbitrage',
  GRID: 'grid',
  DCA: 'dca',
};

export const TRADING_PAIRS = [
  'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT',
  'XRP/USDT', 'DOT/USDT', 'DOGE/USDT', 'MATIC/USDT', 'LTC/USDT',
  'AVAX/USDT', 'LINK/USDT', 'ATOM/USDT', 'UNI/USDT', 'XLM/USDT'
];

export const DEFAULT_TRADING_CONFIG = {
  strategy_type: STRATEGY_TYPES.MANUAL,
  is_active: false,
  min_profit_threshold: 0.5,
  max_trade_size: 1000,
  max_daily_trades: 10,
  max_position_size: 5000,
  allowed_exchanges: ['binance', 'kucoin'],
  allowed_pairs: ['BTC/USDT', 'ETH/USDT'],
  use_market_orders: true,
  max_slippage: 1.0, // percent
  timeout_seconds: 30,
  enable_stop_loss: true,
  stop_loss_percentage: 5.0,
  take_profit_percentage: 10.0,
  test_mode: true,
  risk_level: 'medium', // low, medium, high
};

export const RISK_LEVELS = {
  LOW: {
    max_trade_size: 500,
    max_daily_trades: 5,
    max_position_size: 2500,
    stop_loss_percentage: 2.0,
  },
  MEDIUM: {
    max_trade_size: 1000,
    max_daily_trades: 10,
    max_position_size: 5000,
    stop_loss_percentage: 5.0,
  },
  HIGH: {
    max_trade_size: 2000,
    max_daily_trades: 20,
    max_position_size: 10000,
    stop_loss_percentage: 10.0,
  },
};

export const getRiskConfig = (riskLevel) => {
  return RISK_LEVELS[riskLevel.toUpperCase()] || RISK_LEVELS.MEDIUM;
};

export const isValidTradingPair = (pair) => {
  return TRADING_PAIRS.includes(pair);
};

export const calculatePositionSize = (balance, riskPercentage = 2) => {
  return (balance * riskPercentage) / 100;
};

export default {
  ORDER_TYPES,
  ORDER_SIDES,
  ORDER_STATUS,
  STRATEGY_TYPES,
  TRADING_PAIRS,
  DEFAULT_TRADING_CONFIG,
  RISK_LEVELS,
  getRiskConfig,
  isValidTradingPair,
  calculatePositionSize,
};