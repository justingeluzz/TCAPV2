# TCAP v3 Configuration
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class TcapConfig:
    """TCAP v3 Configuration Settings"""
    
    # Binance API Configuration
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
    BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY', '')
    BINANCE_BASE_URL = 'https://fapi.binance.com'
    
    # Trading Parameters
    TRADING_CONFIG = {
        'starting_capital': 50000,  # $50,000 for testing
        'max_position_size': 0.12,  # 12% of capital
        'typical_position_size': 0.10,  # 10% of capital
        'small_cap_position_size': 0.06,  # 6% for risky trades
        'max_leverage': 5,
        'max_open_positions': 6,  # Increased positions
        'daily_loss_limit': 2500,  # $2,500
        'weekly_loss_limit': 7500,  # $7,500
    }
    
    # Detection Criteria - RELAXED FOR TESTING
    LONG_CRITERIA = {
        'price_gain_24h_min': 3,   # 3% minimum gain (lowered from 8% for more signals)
        'price_gain_24h_max': 50,  # 50% maximum gain
        'price_gain_1h_min': 0.5,  # 0.5% recent acceleration (lowered from 1%)
        'price_gain_1h_max': 12,   # 12% recent acceleration
        'volume_multiplier': 1.5,  # 1.5x average volume (lowered from 2x)
        'rsi_min': 30,             # 30 RSI min (lowered from 35)
        'rsi_max': 80,             # 80 RSI max (increased from 75)
        'market_cap_min': 10_000_000,  # $10M minimum (lowered from $20M)
        'volume_24h_min': 1_000_000,   # $1M minimum volume (lowered from $2M)
        'pullback_min': 1,         # 1% minimum pullback (lowered from 3%)
        'pullback_max': 25,        # 25% maximum pullback (increased from 20%)
    }
    
    SHORT_CRITERIA = {
        'price_gain_24h_min': 80,  # 80%+ overextended
        'price_gain_4h_min': 30,   # 30%+ parabolic move
        'rsi_min': 85,             # Extremely overbought
        'volume_declining': True,   # Buying exhaustion
        'position_size_multiplier': 0.7,  # Smaller positions for shorts
    }
    
    # Technical Analysis Parameters
    TECHNICAL_PARAMS = {
        'rsi_period': 14,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'ema_short': 20,
        'ema_long': 50,
        'volume_sma_period': 20,
        'support_resistance_lookback': 24,  # hours
    }
    
    # Risk Management
    RISK_PARAMS = {
        'stop_loss_min': 0.06,  # 6%
        'stop_loss_max': 0.08,  # 8%
        'take_profit_1': 0.01,  # 1% first target (LOWERED FOR TESTING)
        'take_profit_2': 0.02,  # 2% second target (LOWERED FOR TESTING)
        'trailing_stop_buffer': 0.15,  # 15% trailing buffer
        'max_correlation_exposure': 0.30,  # 30% max in same sector
    }
    
    # Scanning Configuration - FASTER SCANNING
    SCANNING_CONFIG = {
        'scan_interval': 120,  # 2 minutes (faster from 5 minutes)
        'position_monitor_interval': 30,  # 30 seconds
        'technical_update_interval': 60,  # 1 minute
        'risk_check_interval': 10,  # 10 seconds
        'max_pairs_to_scan': 250,  # Scan up to 250 pairs
    }
    
    # Safety Features
    SAFETY_CONFIG = {
        'market_crash_threshold': -0.10,  # -10% BTC drop halt
        'api_retry_attempts': 3,
        'api_retry_delay': 5,  # seconds
        'emergency_stop_enabled': True,
        'paper_trading_mode': os.getenv('PAPER_TRADING', 'true').lower() == 'true',  # Read from .env
    }
    
    # Database Configuration
    DATABASE_CONFIG = {
        'db_path': 'tcap_v3.sqlite',
        'backup_interval': 3600,  # 1 hour
        'log_level': 'INFO',
        'max_log_files': 10,
    }
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get complete configuration dictionary"""
        return {
            'trading': cls.TRADING_CONFIG,
            'long_criteria': cls.LONG_CRITERIA,
            'short_criteria': cls.SHORT_CRITERIA,
            'technical': cls.TECHNICAL_PARAMS,
            'risk': cls.RISK_PARAMS,
            'scanning': cls.SCANNING_CONFIG,
            'safety': cls.SAFETY_CONFIG,
            'database': cls.DATABASE_CONFIG,
        }
    
    @classmethod
    def validate_api_keys(cls) -> bool:
        """Validate that API keys are configured"""
        return bool(cls.BINANCE_API_KEY and cls.BINANCE_SECRET_KEY)
