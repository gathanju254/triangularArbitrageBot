# backend/arbitrage_bot/utils/helpers.py
import logging
from typing import Dict, Any
import json

def calculate_profit_percentage(initial: float, final: float) -> float:
    """Calculate profit percentage"""
    return ((final - initial) / initial) * 100

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('arbitrage_bot.log'),
            logging.StreamHandler()
        ]
    )

def safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def load_config(config_path: str) -> Dict:
    """Load configuration from JSON file"""
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}