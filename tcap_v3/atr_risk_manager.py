"""
TCAP v3 ATR-Based Risk Manager
Implements volatility-based stop losses using Average True Range (ATR)
"""

import logging
import requests
from typing import Tuple, List, Optional
from datetime import datetime, timedelta
from config import TcapConfig

class ATRRiskManager:
    """
    ATR-Based Risk Management System
    Calculates dynamic stop losses based on market volatility
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = TcapConfig.ATR_STOP_LOSS
        
    def calculate_atr_stop_loss(self, symbol: str, entry_price: float, position_side: str) -> Tuple[float, str]:
        """
        Calculate ATR-based stop loss
        
        Args:
            symbol: Trading pair symbol
            entry_price: Entry price for the position
            position_side: 'LONG' or 'SHORT'
            
        Returns:
            Tuple of (stop_loss_price, reasoning)
        """
        try:
            # Get ATR value
            atr_value = self._calculate_atr(symbol)
            if atr_value == 0:
                return self._fallback_stop_loss(entry_price, position_side), "Fallback SL (no ATR data)"
            
            # Determine volatility level
            volatility_level = self._assess_volatility(atr_value)
            
            # Get appropriate ATR multiplier
            atr_multiplier = self._get_atr_multiplier(volatility_level)
            
            # Calculate stop loss
            if position_side == "LONG":
                stop_loss = entry_price - (atr_value * atr_multiplier)
            else:  # SHORT
                stop_loss = entry_price + (atr_value * atr_multiplier)
            
            # Apply min/max limits
            stop_loss = self._apply_stop_loss_limits(entry_price, stop_loss, position_side)
            
            # Calculate stop loss percentage
            sl_pct = abs(stop_loss - entry_price) / entry_price * 100
            
            reasoning = f"ATR-based SL: {volatility_level} vol, {atr_multiplier}x ATR, {sl_pct:.1f}%"
            
            self.logger.info(f"ATR Stop Loss for {symbol}: {reasoning}")
            
            return stop_loss, reasoning
            
        except Exception as e:
            self.logger.error(f"Error calculating ATR stop loss for {symbol}: {e}")
            return self._fallback_stop_loss(entry_price, position_side), "Error - fallback SL"
    
    def _calculate_atr(self, symbol: str, period: int = None) -> float:
        """Calculate Average True Range for the symbol"""
        try:
            if period is None:
                period = self.config['atr_period']
            
            # Get recent kline data
            klines = self._get_kline_data(symbol, "1h", period + 1)
            if len(klines) < period + 1:
                return 0
            
            true_ranges = []
            
            for i in range(1, len(klines)):
                high = float(klines[i][2])
                low = float(klines[i][3])
                prev_close = float(klines[i-1][4])
                
                # True Range = max(high-low, |high-prev_close|, |low-prev_close|)
                tr1 = high - low
                tr2 = abs(high - prev_close)
                tr3 = abs(low - prev_close)
                
                true_range = max(tr1, tr2, tr3)
                true_ranges.append(true_range)
            
            # Calculate ATR (Simple Moving Average of True Ranges)
            if len(true_ranges) >= period:
                atr = sum(true_ranges[-period:]) / period
            else:
                atr = sum(true_ranges) / len(true_ranges)
            
            return atr
            
        except Exception as e:
            self.logger.error(f"Error calculating ATR for {symbol}: {e}")
            return 0
    
    def _get_kline_data(self, symbol: str, interval: str, limit: int) -> List:
        """Get kline data from Binance API"""
        try:
            url = "https://fapi.binance.com/fapi/v1/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get kline data: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error fetching kline data for {symbol}: {e}")
            return []
    
    def _assess_volatility(self, atr_value: float) -> str:
        """Assess volatility level based on ATR"""
        # Convert ATR to percentage (approximate)
        atr_percentage = atr_value  # Assuming ATR is already in price terms
        
        if atr_percentage < self.config['volatility_threshold_low']:
            return "low"
        elif atr_percentage > self.config['volatility_threshold_high']:
            return "high"
        else:
            return "medium"
    
    def _get_atr_multiplier(self, volatility_level: str) -> float:
        """Get ATR multiplier based on volatility level"""
        multipliers = {
            "low": self.config['atr_multiplier_low_vol'],
            "medium": self.config['atr_multiplier_default'],
            "high": self.config['atr_multiplier_high_vol']
        }
        return multipliers.get(volatility_level, self.config['atr_multiplier_default'])
    
    def _apply_stop_loss_limits(self, entry_price: float, calculated_sl: float, position_side: str) -> float:
        """Apply minimum and maximum stop loss limits"""
        # Calculate percentage difference
        sl_pct = abs(calculated_sl - entry_price) / entry_price
        
        # Apply limits
        min_sl_pct = self.config['min_stop_loss_pct']
        max_sl_pct = self.config['max_stop_loss_pct']
        
        if sl_pct < min_sl_pct:
            # Stop loss too tight, widen it
            if position_side == "LONG":
                return entry_price * (1 - min_sl_pct)
            else:
                return entry_price * (1 + min_sl_pct)
        elif sl_pct > max_sl_pct:
            # Stop loss too wide, tighten it
            if position_side == "LONG":
                return entry_price * (1 - max_sl_pct)
            else:
                return entry_price * (1 + max_sl_pct)
        
        return calculated_sl
    
    def _fallback_stop_loss(self, entry_price: float, position_side: str) -> float:
        """Fallback stop loss when ATR calculation fails"""
        fallback_pct = 0.08  # 8% fallback
        
        if position_side == "LONG":
            return entry_price * (1 - fallback_pct)
        else:
            return entry_price * (1 + fallback_pct)
    
    def get_volatility_info(self, symbol: str) -> dict:
        """Get detailed volatility information for a symbol"""
        try:
            atr = self._calculate_atr(symbol)
            volatility_level = self._assess_volatility(atr)
            multiplier = self._get_atr_multiplier(volatility_level)
            
            return {
                'atr_value': atr,
                'volatility_level': volatility_level,
                'atr_multiplier': multiplier,
                'recommended_sl_pct': atr * multiplier
            }
            
        except Exception as e:
            self.logger.error(f"Error getting volatility info for {symbol}: {e}")
            return {
                'atr_value': 0,
                'volatility_level': 'unknown',
                'atr_multiplier': self.config['atr_multiplier_default'],
                'recommended_sl_pct': 0.08
            }
