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
    
    # Trading Parameters - ORIGINAL SAFE SETTINGS (PHP 5,000)
    TRADING_CONFIG = {
        'starting_capital': 5000,   # PHP 5,000 starting capital
        'max_position_size': 0.12,  # 12% of capital (PHP 600 per trade)
        'typical_position_size': 0.10,  # 10% of capital (PHP 500 per trade)
        'small_cap_position_size': 0.06,  # 6% for risky trades (PHP 300)
        'max_leverage': 5,
        'max_open_positions': 3,    # OPTIMIZED: 3 max positions for better profit management
        'daily_loss_limit': 250,    # PHP 250 daily loss limit (5% of capital)
        'weekly_loss_limit': 750,   # PHP 750 weekly loss limit (15% of capital)
    }
    
    # Detection Criteria - ORIGINAL CONSERVATIVE SETTINGS
    LONG_CRITERIA = {
        'price_gain_24h_min': 10,  # RELAXED: 10% minimum gain (was 15%)
        'price_gain_24h_max': 50,  # 50% maximum gain
        'price_gain_1h_min': 2,    # ORIGINAL: 2% recent acceleration (was 0.5%)
        'price_gain_1h_max': 12,   # 12% recent acceleration
        'volume_multiplier': 2,     # RELAXED: 2x average volume (was 3x)
        'rsi_min': 40,             # ORIGINAL: 40 RSI min (was 30)
        'rsi_max': 70,             # ORIGINAL: 70 RSI max (was 80)
        'market_cap_min': 25_000_000,  # RELAXED: $25M minimum (was $50M)
        'volume_24h_min': 2_000_000,   # RELAXED: $2M minimum volume (was $5M)
        'volume_24h_max': 5_000_000,   # NEW: $5M maximum volume (quality filter)
        'pullback_min': 5,         # ORIGINAL: 5% minimum pullback (was 1%)
        'pullback_max': 15,        # ORIGINAL: 15% maximum pullback (was 25%)
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
    
    # Risk Management - REALISTIC CRYPTO TRADING SETTINGS
    RISK_PARAMS = {
        'stop_loss_min': 0.04,  # 4% - balanced minimum
        'stop_loss_max': 0.05,  # 5% - your suggested balanced risk
        'take_profit_1': 0.08,  # 8% - book early gains in fast moves
        'take_profit_2': 0.20,  # 20% - reward when trend continues
        'trailing_stop_buffer': 0.02,  # 2% trailing buffer (reduced from 15%)
        'max_correlation_exposure': 0.30,  # 30% max in same sector
    }
    
    # Scanning Configuration - OPTIMIZED FOR REALISTIC TARGETS
    SCANNING_CONFIG = {
        'scan_interval': 180,  # 3 minutes - faster scanning for 8%/20% targets
        'position_monitor_interval': 30,  # 30 seconds
        'technical_update_interval': 60,  # 1 minute
        'risk_check_interval': 10,  # 10 seconds
        'max_pairs_to_scan': 200,  # More pairs for better opportunities
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
    
    # Enhanced Signal Filtering Configuration - COMPENSATED FOR RELAXED FILTERS
    SIGNAL_FILTERING = {
        # RSI Optimization - Tighter for relaxed market filters
        'rsi_trend_continuation_min': 47,  # Slightly tighter (was 45)
        'rsi_trend_continuation_max': 53,  # Slightly tighter (was 55)
        'rsi_reversal_oversold': 30,       # For reversal signals (oversold)
        'rsi_reversal_overbought': 70,     # For reversal signals (overbought)
        'rsi_optimal_long_min': 47,        # Tighter sweet spot for LONG entries
        'rsi_optimal_long_max': 53,        # Tighter sweet spot for LONG entries
        
        # MACD Enhancement - Stricter requirements
        'require_macd_above_zero': True,   # Favor crossovers above 0 line
        'macd_histogram_confirmation': True,  # Require histogram confirmation
        'macd_signal_strength_min': 0.002,   # INCREASED: Minimum MACD signal strength (was 0.001)
        
        # Volume Divergence Detection - Enhanced
        'volume_divergence_enabled': True,
        'volume_divergence_threshold': 0.25,  # STRICTER: 25% volume decline (was 30%)
        'volume_consistency_periods': 4,     # STRICTER: Check last 4 periods (was 3)
        
        # NEW: Quality compensation for relaxed filters
        'small_cap_confidence_penalty': 5,   # -5% confidence for <$30M market cap
        'low_volume_confidence_penalty': 3,  # -3% confidence for <2.5x volume ratio
        'moderate_gain_confidence_penalty': 2,  # -2% confidence for <12% daily gain
    }
    
    # ATR-Based Stop Loss Configuration
    ATR_STOP_LOSS = {
        'atr_multiplier_default': 1.5,      # Default: SL = Entry - (1.5 * ATR)
        'atr_multiplier_low_vol': 1.2,      # Tighter SL during low volatility
        'atr_multiplier_high_vol': 2.0,     # Wider SL during high volatility
        'atr_period': 14,                   # ATR calculation period
        'volatility_threshold_low': 0.03,   # <3% daily volatility = low
        'volatility_threshold_high': 0.08,  # >8% daily volatility = high
        'min_stop_loss_pct': 0.04,         # Minimum 4% stop loss
        'max_stop_loss_pct': 0.15,         # Maximum 15% stop loss
    }
    
    # Trade Failure Analysis Configuration
    TRADE_ANALYSIS = {
        'log_entry_reasons': True,          # Log why each trade was taken
        'log_exit_reasons': True,           # Log why each trade was closed
        'failure_analysis_enabled': True,   # Enable post-mortem analysis
        'track_signal_components': True,    # Track individual signal components
        'performance_review_interval': 24,  # Review performance every 24 hours
    }
    
    # Position Management for Top 3 Trades
    POSITION_MANAGEMENT = {
        'max_positions': 3,                 # Maximum 3 open positions
        'profit_ranking_enabled': True,    # Rank positions by profitability
        'close_weakest_for_better': True,  # Close worst performer for better signal
        'profit_threshold_replacement': 0.02,  # Replace if new signal >2% better potential
        'min_hold_time_minutes': 30,       # Minimum hold time before replacement
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
            'signal_filtering': cls.SIGNAL_FILTERING,
            'atr_stop_loss': cls.ATR_STOP_LOSS,
            'trade_analysis': cls.TRADE_ANALYSIS,
            'position_management': cls.POSITION_MANAGEMENT,
        }
    
    @classmethod
    def validate_api_keys(cls) -> bool:
        """Validate that API keys are configured"""
        return bool(cls.BINANCE_API_KEY and cls.BINANCE_SECRET_KEY)
