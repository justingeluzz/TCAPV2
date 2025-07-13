"""
TCAP v3 Risk Manager
Handles position sizing, stop losses, take profits, and overall risk management
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import asyncio

from config import TcapConfig
from signal_generator import TradingSignal

# Import OrderResult for position creation
try:
    from order_executor import OrderResult
except ImportError:
    # Fallback if circular import
    OrderResult = None

@dataclass
class Position:
    """Active trading position"""
    symbol: str
    side: str  # 'LONG' or 'SHORT'
    entry_price: float
    current_price: float
    quantity: float
    leverage: int
    unrealized_pnl: float
    unrealized_pnl_percent: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    entry_time: datetime
    position_size_usdt: float
    margin_used: float
    
    # Risk metrics
    risk_amount: float  # Max loss if stop hit
    reward_potential_1: float  # Profit if TP1 hit
    reward_potential_2: float  # Profit if TP2 hit
    
    # Status
    status: str = "OPEN"  # OPEN, PARTIAL_PROFIT, CLOSED
    partial_profit_taken: bool = False

@dataclass
class RiskMetrics:
    """Current portfolio risk metrics"""
    total_capital: float
    available_capital: float
    used_margin: float
    total_unrealized_pnl: float
    daily_pnl: float
    weekly_pnl: float
    open_positions: int
    total_risk_amount: float  # Total potential loss from all positions
    
    # Risk ratios
    margin_utilization: float  # Used margin / Total capital
    risk_exposure: float  # Total risk / Total capital
    
    # Daily limits
    daily_loss_limit: float
    daily_losses_today: float
    trading_halted: bool = False

class RiskManager:
    """
    TCAP v3 Risk Management System
    Manages all aspects of trading risk including position sizing, stops, and limits
    """
    
    def __init__(self):
        self.config = TcapConfig()
        self.logger = logging.getLogger(__name__)
        
        # Risk tracking
        self.positions: Dict[str, Position] = {}
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.weekly_pnl = 0.0
        self.last_reset_date = datetime.now().date()
        
        # Safety flags
        self.trading_halted = False
        self.emergency_stop = False
        self.manual_override = False
        
    def validate_signal(self, signal: TradingSignal) -> Tuple[bool, str]:
        """Validate if a trading signal meets risk management criteria"""
        try:
            # Check if trading is halted
            if self.trading_halted or self.emergency_stop:
                return False, "Trading is currently halted"
            
            # Check daily limits
            if not self._check_daily_limits():
                return False, "Daily trading limits reached"
            
            # Check position limits
            if len(self.positions) >= self.config.TRADING_CONFIG['max_open_positions']:
                return False, f"Maximum {self.config.TRADING_CONFIG['max_open_positions']} positions already open"
            
            # Check if symbol already has position
            if signal.symbol in self.positions:
                return False, f"Position already exists for {signal.symbol}"
            
            # Check position size limits
            if not self._validate_position_size(signal):
                return False, "Position size exceeds limits"
            
            # Check margin requirements
            if not self._check_margin_availability(signal):
                return False, "Insufficient margin available"
            
            # Check risk exposure
            if not self._check_risk_exposure(signal):
                return False, "Total risk exposure would exceed limits"
            
            # Check correlation limits
            if not self._check_correlation_limits(signal):
                return False, "Too many correlated positions"
            
            return True, "Signal validated successfully"
            
        except Exception as e:
            self.logger.error(f"ERROR: Error validating signal: {e}")
            return False, f"Validation error: {e}"
    
    def calculate_position_details(self, signal: TradingSignal, current_capital: float) -> Dict:
        """Calculate detailed position parameters"""
        try:
            # Calculate quantity based on position size and leverage
            notional_value = signal.position_size * signal.leverage
            quantity = notional_value / signal.entry_price
            
            # Calculate margin required
            margin_required = signal.position_size  # 1:1 for USDT margin
            
            # Calculate risk amounts
            if signal.signal_type == "LONG":
                risk_amount = abs(signal.entry_price - signal.stop_loss) * quantity
                reward_1 = abs(signal.take_profit_1 - signal.entry_price) * quantity
                reward_2 = abs(signal.take_profit_2 - signal.entry_price) * quantity
            else:  # SHORT
                risk_amount = abs(signal.stop_loss - signal.entry_price) * quantity
                reward_1 = abs(signal.entry_price - signal.take_profit_1) * quantity
                reward_2 = abs(signal.entry_price - signal.take_profit_2) * quantity
            
            # Calculate risk/reward ratios
            risk_reward_1 = reward_1 / risk_amount if risk_amount > 0 else 0
            risk_reward_2 = reward_2 / risk_amount if risk_amount > 0 else 0
            
            return {
                'quantity': quantity,
                'notional_value': notional_value,
                'margin_required': margin_required,
                'risk_amount': risk_amount,
                'reward_potential_1': reward_1,
                'reward_potential_2': reward_2,
                'risk_reward_1': risk_reward_1,
                'risk_reward_2': risk_reward_2,
                'risk_percent': (risk_amount / current_capital) * 100
            }
            
        except Exception as e:
            self.logger.error(f"ERROR: Error calculating position details: {e}")
            return {}
    
    def create_position(self, signal: TradingSignal, order_result) -> Optional[Position]:
        """Create a new position from a validated signal and order result"""
        try:
            # Calculate basic position details
            position_size_usdt = signal.position_size
            margin_required = position_size_usdt / signal.leverage
            risk_amount = position_size_usdt * 0.08  # 8% max loss
            reward_potential_1 = position_size_usdt * 0.01  # 1% target (LOWERED FOR TESTING)
            reward_potential_2 = position_size_usdt * 0.02  # 2% target (LOWERED FOR TESTING)
            
            # Use order result data for accurate position creation
            entry_price = order_result.filled_price if order_result.filled_price else signal.entry_price
            quantity = order_result.filled_quantity if order_result.filled_quantity else (position_size_usdt * signal.leverage) / entry_price
            entry_time = order_result.timestamp if order_result.timestamp else datetime.now()
            
            position = Position(
                symbol=signal.symbol,
                side=signal.signal_type,
                entry_price=entry_price,
                current_price=entry_price,
                quantity=quantity,
                leverage=signal.leverage,
                unrealized_pnl=0.0,
                unrealized_pnl_percent=0.0,
                stop_loss=signal.stop_loss,
                take_profit_1=signal.take_profit_1,
                take_profit_2=signal.take_profit_2,
                entry_time=entry_time,
                position_size_usdt=position_size_usdt,
                margin_used=margin_required,
                risk_amount=risk_amount,
                reward_potential_1=reward_potential_1,
                reward_potential_2=reward_potential_2
            )
            
            # Add to positions
            self.positions[signal.symbol] = position
            self.daily_trades += 1
            
            self.logger.info(f"SUCCESS: Created position: {signal.signal_type} {signal.symbol}")
            self.logger.info(f"   Entry: ${entry_price:.4f}")
            self.logger.info(f"   Quantity: {quantity:.4f}")
            self.logger.info(f"   Risk: ${risk_amount:.2f} (8.0%)")
            self.logger.info(f"   R:R Ratio: 1:3.8 / 1:8.8")
            
            return position
            
        except Exception as e:
            self.logger.error(f"ERROR: Error creating position: {e}")
            return None
    
    def update_position(self, symbol: str, current_price: float) -> Optional[Position]:
        """Update position with current market price"""
        try:
            if symbol not in self.positions:
                return None
            
            position = self.positions[symbol]
            position.current_price = current_price
            
            # Calculate unrealized PnL
            if position.side == "LONG":
                pnl = (current_price - position.entry_price) * position.quantity
            else:  # SHORT
                pnl = (position.entry_price - current_price) * position.quantity
            
            position.unrealized_pnl = pnl
            position.unrealized_pnl_percent = (pnl / position.position_size_usdt) * 100
            
            return position
            
        except Exception as e:
            self.logger.error(f"ERROR: Error updating position {symbol}: {e}")
            return None
    
    def update_position_price(self, symbol: str, current_price: float) -> Optional[Position]:
        """Update position price - alias for update_position for compatibility"""
        return self.update_position(symbol, current_price)

    def check_exit_conditions(self, position: Position) -> List[str]:
        """Check if position should be closed based on stop loss or take profit"""
        exit_signals = []
        
        try:
            current_price = position.current_price
            
            if position.side == "LONG":
                # Stop loss check
                if current_price <= position.stop_loss:
                    exit_signals.append("STOP_LOSS")
                
                # Take profit checks
                if not position.partial_profit_taken and current_price >= position.take_profit_1:
                    exit_signals.append("TAKE_PROFIT_1")
                
                if current_price >= position.take_profit_2:
                    exit_signals.append("TAKE_PROFIT_2")
                    
            else:  # SHORT
                # Stop loss check
                if current_price >= position.stop_loss:
                    exit_signals.append("STOP_LOSS")
                
                # Take profit checks
                if not position.partial_profit_taken and current_price <= position.take_profit_1:
                    exit_signals.append("TAKE_PROFIT_1")
                
                if current_price <= position.take_profit_2:
                    exit_signals.append("TAKE_PROFIT_2")
            
            return exit_signals
            
        except Exception as e:
            self.logger.error(f"ERROR: Error checking exit conditions for {position.symbol}: {e}")
            return []

    def should_exit_position(self, symbol: str) -> bool:
        """Check if a position should be exited based on current conditions"""
        try:
            if symbol not in self.positions:
                return False
            
            position = self.positions[symbol]
            exit_conditions = self.check_exit_conditions(position)
            
            # Return True if any exit condition is met
            return len(exit_conditions) > 0
            
        except Exception as e:
            self.logger.error(f"ERROR: Error checking if position {symbol} should exit: {e}")
            return False
    
    def close_position(self, symbol: str, reason: str, percentage: float = 1.0) -> Optional[float]:
        """Close position (partially or fully) and return realized PnL"""
        try:
            if symbol not in self.positions:
                return None
            
            position = self.positions[symbol]
            
            # Calculate realized PnL for the percentage being closed
            realized_pnl = position.unrealized_pnl * percentage
            
            self.logger.info(f"PROFIT: Closing {percentage*100:.0f}% of {position.side} {symbol}")
            self.logger.info(f"   Reason: {reason}")
            self.logger.info(f"   Entry: ${position.entry_price:.4f}")
            self.logger.info(f"   Exit: ${position.current_price:.4f}")
            self.logger.info(f"   PnL: ${realized_pnl:.2f} ({position.unrealized_pnl_percent*percentage:.1f}%)")
            
            # Update daily PnL
            self.daily_pnl += realized_pnl
            
            # Handle partial vs full close
            if percentage >= 1.0:
                # Full close - remove position
                del self.positions[symbol]
            else:
                # Partial close - update position
                if reason == "TAKE_PROFIT_1":
                    position.partial_profit_taken = True
                    position.status = "PARTIAL_PROFIT"
                
                # Reduce position size
                position.quantity *= (1 - percentage)
                position.position_size_usdt *= (1 - percentage)
                position.margin_used *= (1 - percentage)
                
                # Update stop loss for remaining position (trailing stop)
                if reason == "TAKE_PROFIT_1" and position.side == "LONG":
                    # Move stop loss to break-even plus small buffer
                    new_stop = position.entry_price * 1.02  # 2% above entry
                    position.stop_loss = max(position.stop_loss, new_stop)
            
            return realized_pnl
            
        except Exception as e:
            self.logger.error(f"ERROR: Error closing position {symbol}: {e}")
            return None
    
    def get_risk_metrics(self, total_capital: float) -> RiskMetrics:
        """Get current portfolio risk metrics"""
        try:
            # Calculate totals
            used_margin = sum(pos.margin_used for pos in self.positions.values())
            total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
            total_risk_amount = sum(pos.risk_amount for pos in self.positions.values())
            
            # Calculate portfolio drawdown
            portfolio_value = total_capital + total_unrealized_pnl
            portfolio_drawdown = max(0, (total_capital - portfolio_value) / total_capital)
            
            # Create risk metrics object
            risk_metrics = RiskMetrics(
                total_capital=total_capital,
                available_capital=total_capital - used_margin,
                used_margin=used_margin,
                total_unrealized_pnl=total_unrealized_pnl,
                daily_pnl=self.daily_pnl,
                weekly_pnl=self.weekly_pnl,
                open_positions=len(self.positions),
                total_risk_amount=total_risk_amount,
                margin_utilization=used_margin / total_capital if total_capital > 0 else 0,
                risk_exposure=total_risk_amount / total_capital if total_capital > 0 else 0,
                daily_loss_limit=self.config.TRADING_CONFIG['daily_loss_limit'],
                daily_losses_today=abs(min(0, self.daily_pnl)),
                trading_halted=self.trading_halted
            )
            
            # Add portfolio_drawdown as attribute
            risk_metrics.portfolio_drawdown = portfolio_drawdown
            
            return risk_metrics
            
        except Exception as e:
            self.logger.error(f"ERROR: Error calculating risk metrics: {e}")
            # Return safe defaults
            risk_metrics = RiskMetrics(
                total_capital=total_capital,
                available_capital=total_capital,
                used_margin=0,
                total_unrealized_pnl=0,
                daily_pnl=self.daily_pnl,
                weekly_pnl=self.weekly_pnl,
                open_positions=0,
                total_risk_amount=0,
                margin_utilization=0,
                risk_exposure=0,
                daily_loss_limit=self.config.TRADING_CONFIG['daily_loss_limit'],
                daily_losses_today=0,
                trading_halted=self.trading_halted
            )
            risk_metrics.portfolio_drawdown = 0
            return risk_metrics

    def emergency_stop_all(self) -> bool:
        """Emergency stop - close all positions immediately"""
        try:
            self.logger.warning("ALERT: EMERGENCY STOP ACTIVATED - Closing all positions")
            self.emergency_stop = True
            self.trading_halted = True
            
            total_pnl = 0.0
            positions_closed = 0
            
            for symbol in list(self.positions.keys()):
                pnl = self.close_position(symbol, "EMERGENCY_STOP", 1.0)
                if pnl is not None:
                    total_pnl += pnl
                    positions_closed += 1
            
            self.logger.warning(f"ALERT: Emergency stop completed: {positions_closed} positions closed, PnL: ${total_pnl:.2f}")
            return True
            
        except Exception as e:
            self.logger.error(f"ERROR: Error in emergency stop: {e}")
            return False
    
    def _check_daily_limits(self) -> bool:
        """Check if daily trading limits are reached"""
        try:
            # Check daily reset first
            self._check_daily_reset()
            
            # Check daily loss limit
            daily_loss = abs(min(0, self.daily_pnl))
            if daily_loss >= self.config.TRADING_CONFIG['daily_loss_limit']:
                self.trading_halted = True
                self.logger.warning(f" Daily loss limit reached: ${daily_loss:.2f}")
                return False
            
            # Check maximum trades per day
            max_trades = self.config.SCANNING_CONFIG.get('max_trades_per_day', 10)
            if self.daily_trades >= max_trades:
                self.logger.warning(f" Daily trade limit reached: {self.daily_trades}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"ERROR: Error checking daily limits: {e}")
            return False
    
    def _validate_position_size(self, signal: TradingSignal) -> bool:
        """Validate position size is within limits"""
        try:
            max_position = self.config.TRADING_CONFIG['starting_capital'] * self.config.TRADING_CONFIG['max_position_size']
            return signal.position_size <= max_position
        except:
            return False
    
    def _check_margin_availability(self, signal: TradingSignal) -> bool:
        """Check if enough margin is available"""
        try:
            current_capital = self.config.TRADING_CONFIG['starting_capital']
            used_margin = sum(pos.margin_used for pos in self.positions.values())
            available_margin = current_capital - used_margin
            
            return signal.position_size <= available_margin
        except:
            return False
    
    def _check_risk_exposure(self, signal: TradingSignal) -> bool:
        """Check if total risk exposure would exceed limits"""
        try:
            current_capital = self.config.TRADING_CONFIG['starting_capital']
            details = self.calculate_position_details(signal, current_capital)
            
            current_risk = sum(pos.risk_amount for pos in self.positions.values())
            new_total_risk = current_risk + details.get('risk_amount', 0)
            
            # Maximum 25% of capital at risk
            max_risk = current_capital * 0.25
            
            return new_total_risk <= max_risk
        except:
            return False
    
    def _check_correlation_limits(self, signal: TradingSignal) -> bool:
        """Check correlation limits (simplified - same sector check)"""
        try:
            # Simple implementation - limit positions in similar tokens
            similar_tokens = 0
            base_token = signal.symbol.replace('USDT', '')
            
            for pos in self.positions.values():
                pos_base = pos.symbol.replace('USDT', '')
                # Simple correlation check (can be improved)
                if any(token in base_token for token in ['BTC', 'ETH']) and any(token in pos_base for token in ['BTC', 'ETH']):
                    similar_tokens += 1
            
            return similar_tokens < 2  # Max 2 similar positions
        except:
            return True
    
    def _check_daily_reset(self):
        """Check if daily counters need to be reset"""
        today = datetime.now().date()
        if today > self.last_reset_date:
            # Reset daily counters
            self.weekly_pnl += self.daily_pnl
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.trading_halted = False  # Reset daily halt
            self.last_reset_date = today
            
            self.logger.info(f" Daily reset completed for {today}")

    def calculate_position_size(self, signal: TradingSignal, current_capital: float) -> float:
        """Calculate the position size in USDT for a trading signal"""
        try:
            # Base position size from signal
            base_size = signal.position_size
            
            # Adjust based on confidence
            confidence_multiplier = signal.confidence  # Use confidence as multiplier
            
            # Apply capital constraints
            max_position = current_capital * self.config.TRADING_CONFIG['max_position_size']
            typical_position = current_capital * self.config.TRADING_CONFIG['typical_position_size']
            
            # Calculate final position size
            position_size = min(base_size * confidence_multiplier, typical_position)
            position_size = min(position_size, max_position)
            
            # Minimum position size
            min_position = 50  # $50 minimum
            position_size = max(position_size, min_position)
            
            return position_size
            
        except Exception as e:
            self.logger.error(f"Error calculating position size: {e}")
            return 0.0

# Example usage
def main():
    """Test risk management"""
    risk_manager = RiskManager()
    
    # Test signal validation
    from signal_generator import TradingSignal
    
    test_signal = TradingSignal(
        symbol="BTCUSDT",
        signal_type="LONG",
        confidence=0.75,
        entry_price=45000.0,
        stop_loss=42000.0,
        take_profit_1=58500.0,
        take_profit_2=76500.0,
        position_size=500.0,
        leverage=3,
        price_change_24h=25.0,
        volume_ratio=4.5,
        rsi=55.0,
        macd_bullish=True,
        pullback_percent=8.0,
        near_support=True,
        signal_time=datetime.now(),
        reason="Test signal"
    )
    
    # Validate signal
    is_valid, reason = risk_manager.validate_signal(test_signal)
    print(f"Signal validation: {is_valid} - {reason}")
    
    if is_valid:
        # Create position
        position = risk_manager.create_position(test_signal, 5000.0)
        
        if position:
            # Get risk metrics
            metrics = risk_manager.get_risk_metrics(5000.0)
            print(f"Risk metrics: {metrics}")

if __name__ == "__main__":
    main()
