"""
TCAP v3 Technical Analyzer
Calculates RSI, MACD, volume analysis, and other technical indicators
"""

import numpy as np
import pandas as pd
import logging
import requests
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta

from config import TcapConfig
from market_scanner import MarketData

@dataclass
class TechnicalSignals:
    """Technical analysis results for a trading pair"""
    symbol: str
    rsi_14: float
    macd_line: float
    macd_signal: float
    macd_histogram: float
    macd_bullish: bool
    ema_20: float
    ema_50: float
    price_above_ema20: bool
    volume_ratio: float  # Current volume vs 20-day average
    volume_increasing: bool
    support_level: Optional[float] = None
    resistance_level: Optional[float] = None
    near_support: bool = False
    pullback_percent: Optional[float] = None
    analysis_time: datetime = None

class TechnicalAnalyzer:
    """
    TCAP v3 Technical Analysis Engine
    Calculates technical indicators for trading decisions
    """
    
    def __init__(self):
        self.config = TcapConfig()
        self.session: Optional[requests.Session] = None
        self.logger = logging.getLogger(__name__)
        
    async def analyze_symbol(self, symbol: str, market_data: MarketData) -> Optional[TechnicalSignals]:
        """Perform complete technical analysis on a symbol"""
        try:
            # Get historical kline data
            kline_data = await self.get_kline_data(symbol, '1h', 100)  # 100 hours of data
            if not kline_data:
                return None
            
            # Convert to pandas DataFrame
            df = self.klines_to_dataframe(kline_data)
            if df.empty:
                return None
            
            # Calculate technical indicators
            rsi = self.calculate_rsi(df['close'], self.config.TECHNICAL_PARAMS['rsi_period'])
            macd_line, macd_signal, macd_hist = self.calculate_macd(
                df['close'],
                self.config.TECHNICAL_PARAMS['macd_fast'],
                self.config.TECHNICAL_PARAMS['macd_slow'],
                self.config.TECHNICAL_PARAMS['macd_signal']
            )
            
            # Calculate EMAs
            ema_20 = self.calculate_ema(df['close'], self.config.TECHNICAL_PARAMS['ema_short'])
            ema_50 = self.calculate_ema(df['close'], self.config.TECHNICAL_PARAMS['ema_long'])
            
            # Volume analysis
            volume_sma = self.calculate_sma(df['volume'], self.config.TECHNICAL_PARAMS['volume_sma_period'])
            current_volume = df['volume'].iloc[-1]
            volume_ratio = current_volume / volume_sma.iloc[-1] if volume_sma.iloc[-1] > 0 else 0
            
            # Support/Resistance levels
            support, resistance = self.find_support_resistance(df)
            
            # Current values
            current_price = df['close'].iloc[-1]
            current_rsi = rsi.iloc[-1] if not rsi.empty else 50
            current_macd_line = macd_line.iloc[-1] if not macd_line.empty else 0
            current_macd_signal = macd_signal.iloc[-1] if not macd_signal.empty else 0
            current_macd_hist = macd_hist.iloc[-1] if not macd_hist.empty else 0
            current_ema_20 = ema_20.iloc[-1] if not ema_20.empty else current_price
            current_ema_50 = ema_50.iloc[-1] if not ema_50.empty else current_price
            
            # Analysis
            macd_bullish = current_macd_line > current_macd_signal and current_macd_hist > 0
            price_above_ema20 = current_price > current_ema_20 * 1.02  # 2% buffer
            volume_increasing = volume_ratio > self.config.LONG_CRITERIA['volume_multiplier']
            
            # Check if near support
            near_support = False
            if support:
                support_distance = abs(current_price - support) / current_price
                near_support = support_distance <= 0.02  # Within 2%
            
            # Calculate pullback from recent high
            recent_high = df['high'].tail(24).max()  # 24-hour high
            pullback_percent = (recent_high - current_price) / recent_high * 100
            
            return TechnicalSignals(
                symbol=symbol,
                rsi_14=current_rsi,
                macd_line=current_macd_line,
                macd_signal=current_macd_signal,
                macd_histogram=current_macd_hist,
                macd_bullish=macd_bullish,
                ema_20=current_ema_20,
                ema_50=current_ema_50,
                price_above_ema20=price_above_ema20,
                volume_ratio=volume_ratio,
                volume_increasing=volume_increasing,
                support_level=support,
                resistance_level=resistance,
                near_support=near_support,
                pullback_percent=pullback_percent,
                analysis_time=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"ERROR: Error analyzing {symbol}: {e}")
            return None
    
    async def get_kline_data(self, symbol: str, interval: str, limit: int) -> List[List]:
        """Get historical kline/candlestick data"""
        try:
            # Ensure we have a valid session for the current event loop
            await self._ensure_session()
            
            url = f"{self.config.BINANCE_BASE_URL}/fapi/v1/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            # Use asyncio.to_thread to run sync request in thread pool
            response = await asyncio.to_thread(self.session.get, url, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                self.logger.warning(f"WARNING: Failed to get kline data for {symbol}: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"ERROR: Error getting kline data for {symbol}: {e}")
            # Reset session on error
            await self._reset_session()
            return []
    
    async def _ensure_session(self):
        """Ensure we have a valid requests session"""
        try:
            # Check if session exists
            if self.session is None:
                # Create new requests session (thread-safe)
                self.session = requests.Session()
            
        except Exception as e:
            self.logger.error(f"ERROR: Error creating session: {e}")
            
    async def _reset_session(self):
        """Reset the requests session"""
        try:
            if self.session:
                self.session.close()
        except:
            pass
        finally:
            self.session = None
            
    async def _reset_session(self):
        """Reset the aiohttp session"""
        try:
            if self.session and not self.session.closed:
                await self.session.close()
        except:
            pass
        finally:
            self.session = None
    
    def klines_to_dataframe(self, klines: List[List]) -> pd.DataFrame:
        """Convert kline data to pandas DataFrame"""
        try:
            if not klines:
                return pd.DataFrame()
            
            df = pd.DataFrame(klines, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'count', 'taker_buy_volume',
                'taker_buy_quote_volume', 'ignore'
            ])
            
            # Convert to appropriate data types
            numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'quote_volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Convert timestamps
            df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
            
            return df
            
        except Exception as e:
            self.logger.error(f"ERROR: Error converting klines to DataFrame: {e}")
            return pd.DataFrame()
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.fillna(50)  # Fill NaN with neutral RSI
            
        except Exception as e:
            self.logger.error(f"ERROR: Error calculating RSI: {e}")
            return pd.Series([50] * len(prices))
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        try:
            ema_fast = self.calculate_ema(prices, fast)
            ema_slow = self.calculate_ema(prices, slow)
            
            macd_line = ema_fast - ema_slow
            macd_signal = self.calculate_ema(macd_line, signal)
            macd_histogram = macd_line - macd_signal
            
            return macd_line, macd_signal, macd_histogram
            
        except Exception as e:
            self.logger.error(f"ERROR: Error calculating MACD: {e}")
            return pd.Series([0] * len(prices)), pd.Series([0] * len(prices)), pd.Series([0] * len(prices))
    
    def calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average"""
        try:
            return prices.ewm(span=period, adjust=False).mean()
        except Exception as e:
            self.logger.error(f"ERROR: Error calculating EMA: {e}")
            return prices  # Return original prices if calculation fails
    
    def calculate_sma(self, prices: pd.Series, period: int) -> pd.Series:
        """Calculate Simple Moving Average"""
        try:
            return prices.rolling(window=period).mean()
        except Exception as e:
            self.logger.error(f"ERROR: Error calculating SMA: {e}")
            return prices
    
    def find_support_resistance(self, df: pd.DataFrame, lookback_hours: int = 24) -> Tuple[Optional[float], Optional[float]]:
        """Find support and resistance levels"""
        try:
            if len(df) < lookback_hours:
                return None, None
            
            # Use recent data for support/resistance
            recent_df = df.tail(lookback_hours)
            
            # Find local minima (support) and maxima (resistance)
            highs = recent_df['high'].values
            lows = recent_df['low'].values
            
            # Simple approach: use recent significant levels
            support = np.percentile(lows, 20)  # 20th percentile of lows
            resistance = np.percentile(highs, 80)  # 80th percentile of highs
            
            return support, resistance
            
        except Exception as e:
            self.logger.error(f"ERROR: Error finding support/resistance: {e}")
            return None, None
    
    def passes_long_criteria(self, signals: TechnicalSignals, market_data: MarketData) -> bool:
        """Check if technical signals meet long entry criteria"""
        try:
            criteria = self.config.LONG_CRITERIA
            
            # RSI check (40-70 range)
            if not (criteria['rsi_min'] <= signals.rsi_14 <= criteria['rsi_max']):
                return False
            
            # MACD bullish signal
            if not signals.macd_bullish:
                return False
            
            # Price above EMA20
            if not signals.price_above_ema20:
                return False
            
            # Volume confirmation
            if signals.volume_ratio < criteria['volume_multiplier']:
                return False
            
            # Pullback detection (5-15% from recent high)
            if signals.pullback_percent is not None:
                if not (criteria['pullback_min'] <= signals.pullback_percent <= criteria['pullback_max']):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"ERROR: Error checking long criteria for {signals.symbol}: {e}")
            return False
    
    def passes_short_criteria(self, signals: TechnicalSignals, market_data: MarketData) -> bool:
        """Check if technical signals meet short entry criteria"""
        try:
            criteria = self.config.SHORT_CRITERIA
            
            # Extreme overbought RSI
            if signals.rsi_14 < criteria['rsi_min']:
                return False
            
            # Price gain requirements
            if market_data.price_change_percent_24h < criteria['price_gain_24h_min']:
                return False
            
            # Volume declining (less than 2x average)
            if signals.volume_ratio > 2.0:
                return False
            
            # MACD showing weakness
            if signals.macd_bullish:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"ERROR: Error checking short criteria for {signals.symbol}: {e}")
            return False
    
    async def close_session(self):
        """Close the requests session"""
        await self._reset_session()

# Example usage
async def main():
    """Test technical analysis"""
    analyzer = TechnicalAnalyzer()
    
    try:
        # Test with a sample symbol
        from market_scanner import MarketData
        
        sample_data = MarketData(
            symbol="BTCUSDT",
            price=45000.0,
            price_change_24h=2000.0,
            price_change_percent_24h=4.65,
            price_change_1h=100.0,
            price_change_percent_1h=0.22,
            volume_24h=50000.0,
            volume_usdt_24h=2250000000.0,
            high_24h=46000.0,
            low_24h=43500.0,
            open_24h=43000.0,
            last_updated=datetime.now()
        )
        
        signals = await analyzer.analyze_symbol("BTCUSDT", sample_data)
        
        if signals:
            print(f"STATS: Technical Analysis for {signals.symbol}:")
            print(f"   RSI (14): {signals.rsi_14:.1f}")
            print(f"   MACD Bullish: {signals.macd_bullish}")
            print(f"   Above EMA20: {signals.price_above_ema20}")
            print(f"   Volume Ratio: {signals.volume_ratio:.1f}x")
            print(f"   Pullback: {signals.pullback_percent:.1f}%")
            print(f"   Near Support: {signals.near_support}")
            
            # Check criteria
            long_valid = analyzer.passes_long_criteria(signals, sample_data)
            short_valid = analyzer.passes_short_criteria(signals, sample_data)
            
            print(f"\nTARGET: Trading Signals:")
            print(f"   Long Entry Valid: {long_valid}")
            print(f"   Short Entry Valid: {short_valid}")
        
    except Exception as e:
        print(f"ERROR: Error: {e}")
    finally:
        await analyzer.close_session()

if __name__ == "__main__":
    asyncio.run(main())
