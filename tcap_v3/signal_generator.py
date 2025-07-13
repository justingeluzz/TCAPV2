"""
TCAP v3 Signal Generator
Combines market scanning and technical analysis to generate trading signals
"""

import asyncio
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import json

from config import TcapConfig
from market_scanner import MarketScanner, MarketData
from technical_analyzer import TechnicalAnalyzer, TechnicalSignals

@dataclass
class TradingSignal:
    """Complete trading signal with all analysis data"""
    symbol: str
    signal_type: str  # 'LONG' or 'SHORT'
    confidence: float  # 0.0 to 1.0
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    position_size: float  # In USDT
    leverage: int
    
    # Market data
    price_change_24h: float
    volume_ratio: float
    
    # Technical data
    rsi: float
    macd_bullish: bool
    pullback_percent: float
    near_support: bool
    
    # Meta data with defaults (must come after non-default fields)
    market_cap: Optional[float] = None
    signal_time: datetime = None
    bitcoin_trend: str = "neutral"
    market_context: str = "normal"
    reason: str = ""

class SignalGenerator:
    """
    TCAP v3 Signal Generator
    Combines all analysis to generate actionable trading signals
    """
    
    def __init__(self):
        self.config = TcapConfig()
        self.market_scanner = MarketScanner()
        self.technical_analyzer = TechnicalAnalyzer()
        self.logger = logging.getLogger(__name__)
        
        self.signals_generated = 0
        self.last_bitcoin_check = None
        self.bitcoin_trend = "neutral"
        
    async def start_generator(self):
        """Initialize the signal generator without starting the loop"""
        try:
            self.logger.info("TARGET: Starting TCAP v3 Signal Generator...")
            
            # Just initialize, don't start the blocking loop
            # The main engine will handle calling generate_signals() periodically
            self.logger.info("Signal generator initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"ERROR: Error starting signal generator: {e}")
            return False

    async def start_signal_generation(self):
        """Start the signal generation loop"""
        self.logger.info("TARGET: Starting TCAP v3 Signal Generator...")
        
        try:
            # Start market scanner
            scanner_task = asyncio.create_task(self.market_scanner.start_scanner())
            
            # Wait for first scan to complete
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                self.logger.info("Signal generator startup cancelled")
                return
            
            # Start signal generation loop
            while self.market_scanner.is_running:
                signals = await self.generate_signals()
                
                if signals:
                    await self.process_signals(signals)
                
                # Wait before next signal generation
                try:
                    await asyncio.sleep(self.config.SCANNING_CONFIG['scan_interval'])
                except asyncio.CancelledError:
                    self.logger.info("Signal generator cancelled - shutting down")
                    break
                
        except asyncio.CancelledError:
            self.logger.info("Signal generator cancelled - shutting down gracefully")
        except Exception as e:
            self.logger.error(f"ERROR: Signal generator error: {e}")
        finally:
            await self.market_scanner.stop_scanner()
            await self.technical_analyzer.close_session()
    
    async def generate_signals(self) -> List[TradingSignal]:
        """Generate trading signals from current market data"""
        try:
            self.logger.info("SCAN: Generating trading signals...")
            
            # Check Bitcoin trend for market context
            await self.update_bitcoin_trend()
            
            # Get candidates from market scanner
            candidates = self.market_scanner.get_top_gainers(50)  # Top 50 gainers
            
            if not candidates:
                self.logger.info("STATS: No candidates found in current scan")
                return []
            
            signals = []
            
            # Analyze each candidate
            for candidate in candidates:
                try:
                    # Perform technical analysis
                    technical_signals = await self.technical_analyzer.analyze_symbol(
                        candidate.symbol, candidate
                    )
                    
                    if not technical_signals:
                        continue
                    
                    # Generate long signal
                    long_signal = await self.evaluate_long_signal(candidate, technical_signals)
                    if long_signal:
                        signals.append(long_signal)
                    
                    # Generate short signal (if conditions are extreme)
                    short_signal = await self.evaluate_short_signal(candidate, technical_signals)
                    if short_signal:
                        signals.append(short_signal)
                        
                except Exception as e:
                    self.logger.warning(f"WARNING: Error analyzing {candidate.symbol}: {e}")
                    continue
            
            # Sort signals by confidence
            signals.sort(key=lambda x: x.confidence, reverse=True)
            
            self.logger.info(f"TARGET: Generated {len(signals)} trading signals")
            return signals[:5]  # Return top 5 signals
            
        except Exception as e:
            self.logger.error(f"ERROR: Error generating signals: {e}")
            return []
    
    async def evaluate_long_signal(self, market_data: MarketData, tech_signals: TechnicalSignals) -> Optional[TradingSignal]:
        """Evaluate if market data qualifies for a long signal"""
        try:
            # Check if passes technical criteria
            if not self.technical_analyzer.passes_long_criteria(tech_signals, market_data):
                return None
            
            # Check Bitcoin trend (must be bullish or neutral)
            if self.bitcoin_trend == "bearish":
                return None
            
            # Calculate confidence score
            confidence = self.calculate_long_confidence(market_data, tech_signals)
            
            # Minimum confidence threshold - DISABLED FOR TESTING
            if confidence < 0.01:  # 1% minimum confidence (VERY LOW for testing)
                return None
            
            # Calculate position sizing
            position_size = self.calculate_position_size(market_data, "LONG", confidence)
            leverage = self.calculate_leverage(market_data, "LONG")
            
            # Calculate entry and exit prices
            entry_price = market_data.price
            stop_loss = entry_price * (1 - self.config.RISK_PARAMS['stop_loss_max'])  # -8% max
            take_profit_1 = entry_price * (1 + self.config.RISK_PARAMS['take_profit_1'])  # +1% (UPDATED FOR TESTING)
            take_profit_2 = entry_price * (1 + self.config.RISK_PARAMS['take_profit_2'])  # +2% (UPDATED FOR TESTING)
            
            # Generate reason
            reason = self.generate_long_reason(market_data, tech_signals)
            
            return TradingSignal(
                symbol=market_data.symbol,
                signal_type="LONG",
                confidence=confidence,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit_1=take_profit_1,
                take_profit_2=take_profit_2,
                position_size=position_size,
                leverage=leverage,
                price_change_24h=market_data.price_change_percent_24h,
                volume_ratio=tech_signals.volume_ratio,
                rsi=tech_signals.rsi_14,
                macd_bullish=tech_signals.macd_bullish,
                pullback_percent=tech_signals.pullback_percent or 0,
                near_support=tech_signals.near_support,
                market_cap=market_data.market_cap,
                signal_time=datetime.now(),
                bitcoin_trend=self.bitcoin_trend,
                market_context="normal",
                reason=reason
            )
            
        except Exception as e:
            self.logger.error(f"ERROR: Error evaluating long signal for {market_data.symbol}: {e}")
            return None
    
    async def evaluate_short_signal(self, market_data: MarketData, tech_signals: TechnicalSignals) -> Optional[TradingSignal]:
        """Evaluate if market data qualifies for a short signal"""
        try:
            # Check if passes technical criteria
            if not self.technical_analyzer.passes_short_criteria(tech_signals, market_data):
                return None
            
            # Additional filters for short trades (more conservative)
            if market_data.price_change_percent_24h < 80:  # Must be extremely overextended
                return None
            
            # Calculate confidence score
            confidence = self.calculate_short_confidence(market_data, tech_signals)
            
            # Higher confidence threshold for shorts - LOWERED FOR TESTING
            if confidence < 0.45:  # 45% minimum confidence for shorts (lowered from 75%)
                return None
            
            # Calculate position sizing (smaller for shorts)
            position_size = self.calculate_position_size(market_data, "SHORT", confidence)
            leverage = min(3, self.calculate_leverage(market_data, "SHORT"))  # Max 3x for shorts
            
            # Calculate entry and exit prices
            entry_price = market_data.price
            stop_loss = entry_price * (1 + self.config.RISK_PARAMS['stop_loss_max'])  # +8% for shorts
            take_profit_1 = entry_price * (1 - self.config.RISK_PARAMS['take_profit_1'])  # -1% first target (UPDATED)
            take_profit_2 = entry_price * (1 - self.config.RISK_PARAMS['take_profit_2'])  # -2% second target (UPDATED)
            
            # Generate reason
            reason = self.generate_short_reason(market_data, tech_signals)
            
            return TradingSignal(
                symbol=market_data.symbol,
                signal_type="SHORT",
                confidence=confidence,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit_1=take_profit_1,
                take_profit_2=take_profit_2,
                position_size=position_size,
                leverage=leverage,
                price_change_24h=market_data.price_change_percent_24h,
                volume_ratio=tech_signals.volume_ratio,
                rsi=tech_signals.rsi_14,
                macd_bullish=tech_signals.macd_bullish,
                pullback_percent=tech_signals.pullback_percent or 0,
                near_support=tech_signals.near_support,
                market_cap=market_data.market_cap,
                signal_time=datetime.now(),
                bitcoin_trend=self.bitcoin_trend,
                market_context="overheated",
                reason=reason
            )
            
        except Exception as e:
            self.logger.error(f"ERROR: Error evaluating short signal for {market_data.symbol}: {e}")
            return None
    
    def calculate_long_confidence(self, market_data: MarketData, tech_signals: TechnicalSignals) -> float:
        """Calculate confidence score for long signals (0.0 to 1.0)"""
        try:
            confidence = 0.0
            
            # Price movement score (15-40% range, peak at 25%)
            price_gain = market_data.price_change_percent_24h
            if 20 <= price_gain <= 30:
                confidence += 0.25  # Perfect range
            elif 15 <= price_gain <= 40:
                confidence += 0.15  # Good range
            
            # RSI score (ideal 50-65)
            rsi = tech_signals.rsi_14
            if 50 <= rsi <= 65:
                confidence += 0.20
            elif 40 <= rsi <= 70:
                confidence += 0.10
            
            # Volume score
            if tech_signals.volume_ratio >= 5:
                confidence += 0.20  # Excellent volume
            elif tech_signals.volume_ratio >= 3:
                confidence += 0.15  # Good volume
            
            # Technical indicators
            if tech_signals.macd_bullish:
                confidence += 0.15
            
            if tech_signals.price_above_ema20:
                confidence += 0.10
            
            # Pullback timing
            if tech_signals.pullback_percent and 5 <= tech_signals.pullback_percent <= 15:
                confidence += 0.15
            
            # Support level proximity
            if tech_signals.near_support:
                confidence += 0.10
            
            # Bitcoin trend bonus
            if self.bitcoin_trend == "bullish":
                confidence += 0.05
            
            return min(1.0, confidence)  # Cap at 1.0
            
        except Exception as e:
            self.logger.error(f"ERROR: Error calculating long confidence: {e}")
            return 0.0
    
    def calculate_short_confidence(self, market_data: MarketData, tech_signals: TechnicalSignals) -> float:
        """Calculate confidence score for short signals (0.0 to 1.0)"""
        try:
            confidence = 0.0
            
            # Extreme price movement (higher = better for shorts)
            price_gain = market_data.price_change_percent_24h
            if price_gain >= 100:
                confidence += 0.30
            elif price_gain >= 80:
                confidence += 0.20
            
            # Extreme RSI
            if tech_signals.rsi_14 >= 90:
                confidence += 0.25
            elif tech_signals.rsi_14 >= 85:
                confidence += 0.15
            
            # Volume declining
            if tech_signals.volume_ratio < 2:
                confidence += 0.20
            
            # MACD bearish
            if not tech_signals.macd_bullish:
                confidence += 0.15
            
            # No strong support nearby
            if not tech_signals.near_support:
                confidence += 0.10
            
            return min(1.0, confidence)
            
        except Exception as e:
            self.logger.error(f"ERROR: Error calculating short confidence: {e}")
            return 0.0
    
    def calculate_position_size(self, market_data: MarketData, signal_type: str, confidence: float) -> float:
        """Calculate position size in USDT"""
        try:
            base_capital = self.config.TRADING_CONFIG['starting_capital']
            
            if signal_type == "LONG":
                # Base position size 8-12% of capital
                base_percentage = 0.08 + (0.04 * confidence)  # 8% to 12% based on confidence
                position_size = base_capital * base_percentage
            else:  # SHORT
                # Smaller positions for shorts
                base_percentage = 0.05 + (0.03 * confidence)  # 5% to 8% based on confidence
                position_size = base_capital * base_percentage * self.config.SHORT_CRITERIA['position_size_multiplier']
            
            # Apply maximum position size limit
            max_position = base_capital * self.config.TRADING_CONFIG['max_position_size']
            position_size = min(position_size, max_position)
            
            return round(position_size, 2)
            
        except Exception as e:
            self.logger.error(f"ERROR: Error calculating position size: {e}")
            return 0.0
    
    def calculate_leverage(self, market_data: MarketData, signal_type: str) -> int:
        """Calculate appropriate leverage"""
        try:
            # Base leverage on volatility and confidence
            base_leverage = 3
            
            # Adjust based on 24h price change
            price_volatility = abs(market_data.price_change_percent_24h)
            
            if price_volatility > 50:
                leverage = 2  # Lower leverage for high volatility
            elif price_volatility > 30:
                leverage = 3
            else:
                leverage = 4
            
            # Cap at maximum allowed leverage
            max_leverage = self.config.TRADING_CONFIG['max_leverage']
            leverage = min(leverage, max_leverage)
            
            # Lower leverage for shorts
            if signal_type == "SHORT":
                leverage = min(leverage, 3)
            
            return leverage
            
        except Exception as e:
            self.logger.error(f"ERROR: Error calculating leverage: {e}")
            return 2  # Conservative default
    
    def generate_long_reason(self, market_data: MarketData, tech_signals: TechnicalSignals) -> str:
        """Generate human-readable reason for long signal"""
        reasons = []
        
        reasons.append(f"+{market_data.price_change_percent_24h:.1f}% daily gain")
        
        if tech_signals.pullback_percent:
            reasons.append(f"{tech_signals.pullback_percent:.1f}% pullback from high")
        
        reasons.append(f"RSI {tech_signals.rsi_14:.0f}")
        
        if tech_signals.macd_bullish:
            reasons.append("MACD bullish")
        
        if tech_signals.volume_ratio >= 3:
            reasons.append(f"{tech_signals.volume_ratio:.1f}x volume")
        
        if tech_signals.near_support:
            reasons.append("near support")
        
        return " | ".join(reasons)
    
    def generate_short_reason(self, market_data: MarketData, tech_signals: TechnicalSignals) -> str:
        """Generate human-readable reason for short signal"""
        reasons = []
        
        reasons.append(f"+{market_data.price_change_percent_24h:.0f}% overextended")
        reasons.append(f"RSI {tech_signals.rsi_14:.0f}")
        
        if tech_signals.volume_ratio < 2:
            reasons.append("volume declining")
        
        if not tech_signals.macd_bullish:
            reasons.append("MACD bearish")
        
        reasons.append("mean reversion play")
        
        return " | ".join(reasons)
    
    async def update_bitcoin_trend(self):
        """Update Bitcoin trend analysis for market context"""
        try:
            # Get Bitcoin data
            btc_data = self.market_scanner.market_data.get('BTCUSDT')
            
            if btc_data:
                # Simple trend analysis based on 24h performance
                if btc_data.price_change_percent_24h > 2:
                    self.bitcoin_trend = "bullish"
                elif btc_data.price_change_percent_24h < -5:
                    self.bitcoin_trend = "bearish"
                else:
                    self.bitcoin_trend = "neutral"
                
                self.last_bitcoin_check = datetime.now()
                
        except Exception as e:
            self.logger.warning(f"WARNING: Error updating Bitcoin trend: {e}")
            self.bitcoin_trend = "neutral"
    
    async def process_signals(self, signals: List[TradingSignal]):
        """Process and log generated signals"""
        try:
            for signal in signals:
                self.signals_generated += 1
                
                self.logger.info(f"TARGET: Signal #{self.signals_generated}: {signal.signal_type} {signal.symbol}")
                self.logger.info(f"   Confidence: {signal.confidence:.1%}")
                self.logger.info(f"   Entry: ${signal.entry_price:.4f}")
                self.logger.info(f"   Stop Loss: ${signal.stop_loss:.4f}")
                self.logger.info(f"   Take Profit: ${signal.take_profit_1:.4f} / ${signal.take_profit_2:.4f}")
                self.logger.info(f"   Position Size: ${signal.position_size:.0f} ({signal.leverage}x)")
                self.logger.info(f"   Reason: {signal.reason}")
                
                # Here we would integrate with the order executor
                # For now, just log the signals
                
        except Exception as e:
            self.logger.error(f"ERROR: Error processing signals: {e}")
    
    async def generate_signal(self, market_data: MarketData, technical_signals: TechnicalSignals) -> Optional[TradingSignal]:
        """Generate a single trading signal for a specific market candidate"""
        try:
            self.logger.debug(f"SIGNAL_DEBUG: Analyzing {market_data.symbol}")
            self.logger.debug(f"  Price gain 24h: {market_data.price_change_24h:.2f}%")
            self.logger.debug(f"  Volume ratio: {market_data.volume_24h/1000000:.1f}M")
            
            # Check for LONG opportunity first
            long_signal = await self.evaluate_long_signal(market_data, technical_signals)
            if long_signal:
                self.logger.info(f"SIGNAL: Generated LONG signal for {market_data.symbol} (confidence: {long_signal.confidence:.0%})")
                return long_signal
            else:
                self.logger.debug(f"  LONG rejected for {market_data.symbol}")
            
            # Check for SHORT opportunity
            short_signal = await self.evaluate_short_signal(market_data, technical_signals)
            if short_signal:
                self.logger.info(f"SIGNAL: Generated SHORT signal for {market_data.symbol} (confidence: {short_signal.confidence:.0%})")
                return short_signal
            else:
                self.logger.debug(f"  SHORT rejected for {market_data.symbol}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"ERROR: Error generating signal for {market_data.symbol}: {e}")
            return None

# Example usage
async def main():
    """Test signal generation"""
    generator = SignalGenerator()
    
    try:
        # Run signal generation for a short time
        task = asyncio.create_task(generator.start_signal_generation())
        
        # Let it run for 2 minutes
        await asyncio.sleep(120)
        
        # Stop the scanner
        await generator.market_scanner.stop_scanner()
        
    except Exception as e:
        print(f"ERROR: Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
