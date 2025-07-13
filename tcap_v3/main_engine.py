"""
TCAP v3 Main Trading Engine
Orchestrates all components for fully automated trading
NO EMOJIS - Windows compatible
"""

import asyncio
import logging
import sys
import signal
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import threading
from threading import Timer

# Import TCAP v3 components
from config import TcapConfig
from market_scanner import MarketScanner
from technical_analyzer import TechnicalAnalyzer
from signal_generator import SignalGenerator, TradingSignal
from risk_manager import RiskManager, Position
from order_executor import OrderExecutor
from trade_logger import TradeLogger, CompletedTrade
from atr_risk_manager import ATRRiskManager
from trade_failure_analyzer import TradeFailureAnalyzer
from position_manager import PositionManager, OpenPosition

class TcapEngine:
    """
    TCAP v3 Main Trading Engine
    Orchestrates all trading components for fully automated operation
    """
    
    def __init__(self):
        self.config = TcapConfig()
        
        # Initialize components
        self.market_scanner = MarketScanner()
        self.technical_analyzer = TechnicalAnalyzer()
        self.signal_generator = SignalGenerator()
        self.risk_manager = RiskManager()
        self.order_executor = OrderExecutor()
        self.trade_logger = TradeLogger()  # Add trade logger
        
        # Initialize enhanced components
        self.atr_risk_manager = ATRRiskManager()
        self.trade_analyzer = TradeFailureAnalyzer()
        self.position_manager = PositionManager(max_positions=3)
        
        # Engine state
        self.is_running = False
        self.is_paused = False
        self.start_time = None
        self.total_trades = 0
        self.successful_trades = 0
        
        # Enhanced tracking
        self.current_signals = []
        self.signal_confidence_threshold = 58  # Optimized for realistic 8%/20% targets
        self.last_performance_review = datetime.now()
        self.daily_trade_count = 0
        self.last_reset_date = datetime.now().date()
        
        # Continuous monitoring (like TCAP v2)
        self.continuous_update = True
        self.update_thread = None
        
        # Setup logging
        self._setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Performance tracking
        self.initial_capital = self.config.TRADING_CONFIG['starting_capital']
        self.current_capital = self.initial_capital
        
    def _setup_logging(self):
        """Setup comprehensive logging"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(name)s | %(levelname)s | %(message)s'
        )
        
        # File handler for all logs
        file_handler = logging.FileHandler(
            log_dir / f"tcap_v3_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(detailed_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(detailed_formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)

    def start_continuous_monitoring(self):
        """Start continuous background monitoring like TCAP v2"""
        self.logger.info("Starting continuous monitoring...")
        # Delay initial start by 5 seconds to allow components to initialize
        self.update_thread = Timer(5.0, self.continuous_update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
    
    def continuous_update_loop(self):
        """Continuously update and process trading logic in background"""
        if self.continuous_update and self.is_running:
            try:
                self.logger.info("Auto-updating trading system...")
                
                # Run the trading logic synchronously in the timer thread
                import asyncio
                
                # Get or create event loop for this thread
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_closed():
                        raise RuntimeError("Loop is closed")
                except RuntimeError:
                    # Create new event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                try:
                    # Run trading operations
                    loop.run_until_complete(self._process_continuous_cycle())
                except Exception as e:
                    self.logger.error(f"Error in trading operations: {e}")
                # Don't close the loop - keep it for reuse
                    
                self.logger.info("Continuous update cycle completed")
                
            except Exception as e:
                self.logger.error(f"Error in continuous update: {e}")
                # Don't stop on errors - keep running for resilience
            
            # Schedule next update in 15 seconds if still running (faster for testing)
            if self.continuous_update and self.is_running:
                try:
                    self.update_thread = Timer(15.0, self.continuous_update_loop)
                    self.update_thread.daemon = True
                    self.update_thread.start()
                except Exception as e:
                    self.logger.error(f"Error scheduling next update: {e}")
                    # Try to restart monitoring after a delay
                    self.update_thread = Timer(30.0, self.continuous_update_loop)
                    self.update_thread.daemon = True
                    self.update_thread.start()
    
    async def _process_continuous_cycle(self):
        """Process one complete trading cycle"""
        try:
            # Run market scan
            if hasattr(self.market_scanner, 'scan_all_markets'):
                await self.market_scanner.scan_all_markets()
            
            # Update positions
            await self._update_positions()
            
            # Process new signals every cycle
            if not self.is_paused:
                await self._process_new_signals()
            
            # Perform risk checks
            await self._perform_risk_checks()
            
        except Exception as e:
            self.logger.error(f"Error in continuous cycle: {e}")

    def stop_continuous_monitoring(self):
        """Stop continuous monitoring"""
        self.logger.info("Stopping continuous monitoring...")
        self.continuous_update = False
        if self.update_thread:
            self.update_thread.cancel()
            self.logger.info("Continuous monitoring stopped")

    async def start_trading(self) -> bool:
        """Start the automated trading system"""
        try:
            self.logger.info("Starting TCAP v3 Automated Trading System")
            self.logger.info("=" * 60)
            
            # Display configuration
            self._log_startup_info()
            
            # Initialize components
            if not await self._initialize_components():
                return False
            
            # Start continuous monitoring (like TCAP v2)
            self.is_running = True
            self.start_time = datetime.now()
            
            self.logger.info("Starting continuous monitoring system...")
            self.start_continuous_monitoring()
            
            # Keep the main thread alive
            self.logger.info("TCAP v3 is now running continuously in the background")
            self.logger.info("Press Ctrl+C to stop the system")
            
            # Keep main thread alive while continuous monitoring runs
            try:
                # Run indefinitely until manually stopped
                health_check_counter = 0
                while self.is_running:
                    try:
                        await asyncio.sleep(60)  # Check every minute
                    except asyncio.CancelledError:
                        self.logger.info("Main loop sleep cancelled - shutting down")
                        self.is_running = False
                        break
                    
                    health_check_counter += 1
                    
                    # Log status every hour
                    current_time = datetime.now()
                    if current_time.minute == 0 and current_time.second < 60:
                        await self._log_system_status()
                    
                    # Perform health check every 10 minutes
                    if health_check_counter >= 10:
                        await self._perform_system_health_check()
                        health_check_counter = 0
                    
                    # Log daily summary and perform maintenance at midnight
                    if current_time.hour == 0 and current_time.minute == 0 and current_time.second < 60:
                        await self._log_daily_summary()
                        await self._perform_maintenance()
                        
            except (KeyboardInterrupt, asyncio.CancelledError):
                self.logger.info("Received stop signal from user")
                self.is_running = False
            
            return True
            
        except Exception as e:
            self.logger.error(f"ERROR: Fatal error starting trading system: {e}")
            return False
        finally:
            await self._cleanup()
    
    async def stop_trading(self):
        """Stop the trading system gracefully"""
        self.logger.info("Stopping TCAP v3 Trading System...")
        self.is_running = False
        
        # Stop continuous monitoring
        self.stop_continuous_monitoring()

    def pause_trading(self):
        """Pause trading but keep monitoring"""
        self.logger.info("Pausing trading...")
        self.is_paused = True

    def resume_trading(self):
        """Resume trading"""
        self.logger.info("Resuming trading...")
        self.is_paused = False

    async def _initialize_components(self) -> bool:
        """Initialize all trading components"""
        try:
            self.logger.info("Initializing trading components...")
            
            # Initialize order executor
            if not await self.order_executor.start_executor():
                self.logger.error("ERROR: Failed to initialize order executor")
                return False
            
            # Get initial balance
            balance = await self.order_executor.get_account_balance()
            if balance is not None:
                self.current_capital = balance
                self.logger.info(f"Current account balance: ${balance:.2f}")
            
            # Initialize market scanner
            await self.market_scanner.start_scanner()
            
            # Initialize signal generator
            await self.signal_generator.start_generator()
            
            self.logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"ERROR: Error initializing components: {e}")
            return False

    async def _process_new_signals(self):
        """Enhanced signal processing with 3-position limit and profit optimization"""
        try:
            # Get market candidates from scanner
            candidates = self.market_scanner.get_latest_candidates()
            if not candidates:
                return
            
            self.logger.info(f"Processing {len(candidates)} market candidates...")
            
            # Generate signals for candidates using enhanced filtering
            signals = []
            for candidate in candidates:
                try:
                    # Get technical analysis data
                    tech_data = await self.technical_analyzer.analyze_symbol(candidate.symbol, candidate)
                    if not tech_data:
                        continue
                    
                    # Generate signal with enhanced evaluation
                    signal = await self.signal_generator.generate_enhanced_signal(candidate, tech_data)
                    if signal and signal.confidence >= self.signal_confidence_threshold:
                        signals.append(signal)
                        
                except Exception as e:
                    self.logger.warning(f"WARNING: Error processing {candidate.symbol}: {e}")
            
            # Sort signals by confidence and potential profit
            signals.sort(key=lambda s: (s.confidence, self._estimate_signal_potential(s)), reverse=True)
            
            self.logger.info(f"Generated {len(signals)} high-quality signals (>={self.signal_confidence_threshold}% confidence)")
            
            # Process signals with position management
            for signal in signals:
                if await self._should_execute_signal(signal):
                    await self._execute_enhanced_signal(signal)
                
        except Exception as e:
            self.logger.error(f"ERROR: Error processing new signals: {e}")

    async def _should_execute_signal(self, signal: TradingSignal) -> bool:
        """Determine if signal should be executed considering position limits"""
        try:
            # Check if we can open new position
            if self.position_manager.can_open_new_position():
                return True
            
            # Check if we should replace an existing position
            estimated_potential = self._estimate_signal_potential(signal)
            should_replace, position_to_replace = self.position_manager.should_replace_position(
                signal.confidence, estimated_potential
            )
            
            if should_replace and position_to_replace:
                self.logger.info(f"Replacing position {position_to_replace} with {signal.symbol} signal")
                
                # Close the existing position
                removed_position = self.position_manager.remove_position(position_to_replace, "replaced_for_better")
                if removed_position:
                    # Close the actual trade
                    await self._close_position_for_replacement(removed_position)
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error determining signal execution: {e}")
            return False

    async def _execute_enhanced_signal(self, signal: TradingSignal):
        """Execute a trading signal with enhanced features"""
        try:
            self.logger.info(f"Executing {signal.signal_type} signal for {signal.symbol}")
            self.logger.info(f"  Confidence: {signal.confidence:.1f}%")
            self.logger.info(f"  Reason: {signal.reason}")
            
            # Calculate position size with enhanced risk management
            position_size = self.risk_manager.calculate_position_size(
                signal, self.current_capital
            )
            
            if position_size <= 0:
                self.logger.warning(f"Position size too small for {signal.symbol}")
                return
            
            # Calculate ATR-based stop loss
            atr_stop_loss, atr_reasoning = self.atr_risk_manager.calculate_atr_stop_loss(
                signal.symbol, signal.entry_price, signal.signal_type
            )
            
            # Update signal with ATR stop loss
            signal.stop_loss = atr_stop_loss
            
            # Log trade entry reasoning
            trade_entry_data = {
                'symbol': signal.symbol,
                'side': signal.signal_type,
                'entry_price': signal.entry_price,
                'confidence': signal.confidence,
                'entry_reasons': signal.reason.split(' + '),
                'rsi': getattr(signal, 'rsi', 0),
                'macd_signal': 'bullish' if getattr(signal, 'macd_bullish', False) else 'bearish',
                'volume_ratio': getattr(signal, 'volume_ratio', 0),
                'price_change_24h': getattr(signal, 'price_change_24h', 0),
                'stop_loss_reasoning': atr_reasoning
            }
            
            trade_id = self.trade_analyzer.log_trade_entry(trade_entry_data)
            
            # Execute the order
            order_result = await self.order_executor.execute_signal(signal, position_size)
            if not order_result.success:
                self.logger.error(f"ERROR: Failed to execute order: {order_result.error_message}")
                return
            
            # Create position for tracking
            position = self.risk_manager.create_position(signal, order_result)
            if not position:
                self.logger.error(f"ERROR: Failed to create position for {signal.symbol}")
                return
            
            # Add to position manager
            open_position = OpenPosition(
                trade_id=trade_id,
                symbol=signal.symbol,
                side=signal.signal_type,
                entry_time=datetime.now(),
                entry_price=signal.entry_price,
                current_price=signal.entry_price,
                position_size=position_size,
                unrealized_pnl=0.0,
                unrealized_pnl_pct=0.0,
                confidence_score=signal.confidence,
                stop_loss=signal.stop_loss,
                take_profit_1=signal.take_profit_1,
                take_profit_2=signal.take_profit_2
            )
            
            if self.position_manager.add_position(open_position):
                self.logger.info(f"Position opened successfully: {signal.signal_type} {signal.symbol}")
                self.logger.info(f"  Entry: {signal.entry_price:.6f}, Size: PHP {position_size:.0f}")
                self.logger.info(f"  Stop Loss: {signal.stop_loss:.6f} ({atr_reasoning})")
                self.logger.info(f"  Take Profits: {signal.take_profit_1:.6f}, {signal.take_profit_2:.6f}")
                
                self.total_trades += 1
                self.daily_trade_count += 1
                
                # Set up exit orders
                await self._setup_exit_orders(position)
                
                # Log successful trade opening
                completed_trade = CompletedTrade(
                    trade_id=trade_id,
                    symbol=signal.symbol,
                    side=signal.signal_type,
                    entry_time=datetime.now(),
                    entry_price=signal.entry_price,
                    exit_time=None,
                    exit_price=None,
                    quantity=position_size / signal.entry_price,
                    profit_loss=0,
                    profit_loss_pct=0,
                    exit_reason="OPENED",
                    confidence=signal.confidence,
                    stop_loss=signal.stop_loss,
                    take_profit_1=signal.take_profit_1,
                    take_profit_2=signal.take_profit_2
                )
                
                await self.trade_logger.log_trade(completed_trade)
            
        except Exception as e:
            self.logger.error(f"ERROR: Error executing enhanced signal for {signal.symbol}: {e}")

    def _estimate_signal_potential(self, signal: TradingSignal) -> float:
        """Estimate profit potential of a signal"""
        try:
            # Calculate potential profit to first and second take profit levels
            if signal.signal_type == "LONG":
                tp1_potential = (signal.take_profit_1 - signal.entry_price) / signal.entry_price * 100
                tp2_potential = (signal.take_profit_2 - signal.entry_price) / signal.entry_price * 100
            else:  # SHORT
                tp1_potential = (signal.entry_price - signal.take_profit_1) / signal.entry_price * 100
                tp2_potential = (signal.entry_price - signal.take_profit_2) / signal.entry_price * 100
            
            # Weighted average (30% to TP1, 70% to TP2)
            estimated_potential = (tp1_potential * 0.3 + tp2_potential * 0.7)
            
            return max(0, estimated_potential)
            
        except Exception as e:
            self.logger.error(f"Error estimating signal potential: {e}")
            return 0

    async def _close_position_for_replacement(self, position: OpenPosition):
        """Close a position to make room for a better opportunity"""
        try:
            self.logger.info(f"Closing position {position.symbol} for replacement")
            
            # Execute market close order
            close_result = await self.order_executor.close_position_market(position.symbol, position.side)
            
            if close_result.success:
                # Log trade exit
                exit_data = {
                    'exit_price': position.current_price,
                    'exit_reason': 'Replaced for better opportunity',
                    'exit_type': 'MANUAL',
                    'profit_loss': position.unrealized_pnl,
                    'profit_loss_pct': position.unrealized_pnl_pct,
                    'market_condition': 'replacement'
                }
                
                self.trade_analyzer.log_trade_exit(position.trade_id, exit_data)
                
                self.logger.info(f"Position {position.symbol} closed successfully")
                self.logger.info(f"  Final P&L: PHP {position.unrealized_pnl:.2f} ({position.unrealized_pnl_pct:+.2f}%)")
            else:
                self.logger.error(f"Failed to close position {position.symbol} for replacement")
                
        except Exception as e:
            self.logger.error(f"Error closing position for replacement: {e}")

    async def _setup_exit_orders(self, position: Position):
        """Set up stop loss and take profit orders"""
        try:
            # Place stop loss
            if position.stop_loss:
                await self.order_executor.place_stop_loss(position)
                self.logger.info(f"Stop loss placed for {position.symbol}")
            
            # Place take profit orders
            if position.take_profit_1:
                # Use half quantity for first take profit
                tp1_quantity = position.quantity * 0.5
                await self.order_executor.place_take_profit(position, position.take_profit_1, tp1_quantity)
                self.logger.info(f"Take profit 1 placed for {position.symbol}")
                
        except Exception as e:
            self.logger.error(f"ERROR: Error setting up exit orders for {position.symbol}: {e}")

    async def _update_positions(self):
        """Enhanced position monitoring with profit optimization"""
        try:
            # Get current market prices for all open positions
            if not self.position_manager.open_positions:
                return
            
            symbols = [pos.symbol for pos in self.position_manager.open_positions]
            price_data = await self.market_scanner.get_current_prices(symbols)
            
            # Update all positions with current prices
            self.position_manager.update_all_positions(price_data)
            
            # Check for exit conditions
            for position in self.position_manager.open_positions.copy():  # Copy to avoid modification during iteration
                await self._check_position_exit_conditions(position)
            
            # Log portfolio summary every 10 minutes
            if datetime.now().minute % 10 == 0:
                self._log_portfolio_summary()
            
            # Daily performance review
            if datetime.now() - self.last_performance_review > timedelta(hours=24):
                await self._perform_daily_performance_review()
                self.last_performance_review = datetime.now()
            
            # Reset daily trade count at midnight
            current_date = datetime.now().date()
            if current_date != self.last_reset_date:
                self.daily_trade_count = 0
                self.last_reset_date = current_date
                
        except Exception as e:
            self.logger.error(f"Error updating positions: {e}")

    async def _check_position_exit_conditions(self, position: OpenPosition):
        """Check if position should be closed based on various conditions"""
        try:
            current_price = position.current_price
            
            # Stop loss check
            if position.side == "LONG" and current_price <= position.stop_loss:
                await self._close_position(position, "STOP_LOSS", "Stop loss triggered")
                return
            elif position.side == "SHORT" and current_price >= position.stop_loss:
                await self._close_position(position, "STOP_LOSS", "Stop loss triggered")
                return
            
            # Take profit checks
            if position.side == "LONG":
                if current_price >= position.take_profit_2:
                    await self._close_position(position, "TAKE_PROFIT", "Take profit 2 reached")
                    return
                elif current_price >= position.take_profit_1 and position.unrealized_pnl_pct >= 15:
                    # Close 50% at TP1 if significant profit
                    await self._partial_close_position(position, 0.5, "PARTIAL_PROFIT", "Take profit 1 reached")
            else:  # SHORT
                if current_price <= position.take_profit_2:
                    await self._close_position(position, "TAKE_PROFIT", "Take profit 2 reached")
                    return
                elif current_price <= position.take_profit_1 and position.unrealized_pnl_pct >= 15:
                    await self._partial_close_position(position, 0.5, "PARTIAL_PROFIT", "Take profit 1 reached")
            
            # Time-based exit (positions open too long without significant profit)
            if position.hold_duration_minutes >= 480:  # 8 hours
                if position.unrealized_pnl_pct < 5:  # Less than 5% profit
                    await self._close_position(position, "TIME_BASED", "Position held too long without profit")
                    return
            
            # Trailing stop logic for profitable positions
            if position.unrealized_pnl_pct >= 10:  # Position is 10%+ profitable
                await self._check_trailing_stop(position)
                
        except Exception as e:
            self.logger.error(f"Error checking exit conditions for {position.symbol}: {e}")

    async def _close_position(self, position: OpenPosition, exit_type: str, reason: str):
        """Close a position completely"""
        try:
            self.logger.info(f"Closing position {position.symbol}: {reason}")
            
            # Execute market close order
            close_result = await self.order_executor.close_position_market(position.symbol, position.side)
            
            if close_result.success:
                # Calculate final metrics
                final_pnl = position.unrealized_pnl
                final_pnl_pct = position.unrealized_pnl_pct
                
                # Log trade exit for analysis
                exit_data = {
                    'exit_price': position.current_price,
                    'exit_reason': reason,
                    'exit_type': exit_type,
                    'profit_loss': final_pnl,
                    'profit_loss_pct': final_pnl_pct,
                    'market_condition': 'normal',  # Could be enhanced with market condition detection
                    'volatility_info': self.atr_risk_manager.get_volatility_info(position.symbol)
                }
                
                self.trade_analyzer.log_trade_exit(position.trade_id, exit_data)
                
                # Remove from position manager
                self.position_manager.remove_position(position.trade_id, exit_type.lower())
                
                # Update statistics
                if final_pnl > 0:
                    self.successful_trades += 1
                
                # Update capital
                self.current_capital += final_pnl
                
                # Log trade completion
                completed_trade = CompletedTrade(
                    trade_id=position.trade_id,
                    symbol=position.symbol,
                    side=position.side,
                    entry_time=position.entry_time,
                    entry_price=position.entry_price,
                    exit_time=datetime.now(),
                    exit_price=position.current_price,
                    quantity=position.position_size / position.entry_price,
                    profit_loss=final_pnl,
                    profit_loss_pct=final_pnl_pct,
                    exit_reason=reason,
                    confidence=position.confidence_score,
                    stop_loss=position.stop_loss,
                    take_profit_1=position.take_profit_1,
                    take_profit_2=position.take_profit_2
                )
                
                await self.trade_logger.log_trade(completed_trade)
                
                self.logger.info(f"Position {position.symbol} closed successfully")
                self.logger.info(f"  Final P&L: PHP {final_pnl:.2f} ({final_pnl_pct:+.2f}%)")
                self.logger.info(f"  Hold Duration: {position.hold_duration_minutes} minutes")
                self.logger.info(f"  New Capital: PHP {self.current_capital:.2f}")
                
            else:
                self.logger.error(f"Failed to close position {position.symbol}: {close_result.error_message}")
                
        except Exception as e:
            self.logger.error(f"Error closing position {position.symbol}: {e}")

    async def _partial_close_position(self, position: OpenPosition, close_percentage: float, exit_type: str, reason: str):
        """Close part of a position"""
        try:
            self.logger.info(f"Partially closing {close_percentage*100:.0f}% of {position.symbol}: {reason}")
            
            # Calculate partial size
            close_size = position.position_size * close_percentage
            
            # Execute partial close
            close_result = await self.order_executor.close_partial_position(position.symbol, position.side, close_size)
            
            if close_result.success:
                # Update position size
                partial_pnl = position.unrealized_pnl * close_percentage
                position.position_size *= (1 - close_percentage)
                
                # Update capital
                self.current_capital += partial_pnl
                
                self.logger.info(f"Partial close successful: PHP {partial_pnl:.2f} profit realized")
                
        except Exception as e:
            self.logger.error(f"Error partially closing position {position.symbol}: {e}")

    async def _check_trailing_stop(self, position: OpenPosition):
        """Implement trailing stop for profitable positions"""
        try:
            # Simple trailing stop: move stop loss to break-even + 2% once position is 10%+ profitable
            if position.unrealized_pnl_pct >= 10:
                if position.side == "LONG":
                    new_stop = position.entry_price * 1.02  # 2% above entry
                    if new_stop > position.stop_loss:
                        position.stop_loss = new_stop
                        self.logger.info(f"Trailing stop updated for {position.symbol}: {new_stop:.6f}")
                else:  # SHORT
                    new_stop = position.entry_price * 0.98  # 2% below entry
                    if new_stop < position.stop_loss:
                        position.stop_loss = new_stop
                        self.logger.info(f"Trailing stop updated for {position.symbol}: {new_stop:.6f}")
                        
        except Exception as e:
            self.logger.error(f"Error updating trailing stop for {position.symbol}: {e}")

    def _log_portfolio_summary(self):
        """Log comprehensive portfolio summary"""
        try:
            summary = self.position_manager.get_portfolio_summary()
            
            if summary['open_positions'] == 0:
                self.logger.info("Portfolio Status: No open positions")
                return
            
            self.logger.info("=" * 60)
            self.logger.info("PORTFOLIO SUMMARY")
            self.logger.info("=" * 60)
            self.logger.info(f"Open Positions: {summary['open_positions']}/3")
            self.logger.info(f"Total Unrealized P&L: PHP {summary['total_unrealized_pnl']:.2f} ({summary['total_unrealized_pnl_pct']:+.2f}%)")
            self.logger.info(f"Average Confidence: {summary['avg_confidence']:.1f}%")
            
            if summary['best_performer']:
                best = summary['best_performer']
                self.logger.info(f"Best Performer: {best['symbol']} ({best['pnl_pct']:+.2f}%)")
            
            if summary['worst_performer']:
                worst = summary['worst_performer']
                self.logger.info(f"Worst Performer: {worst['symbol']} ({worst['pnl_pct']:+.2f}%)")
            
            self.logger.info("Individual Positions:")
            for pos in summary['positions']:
                self.logger.info(f"  {pos['symbol']} {pos['side']}: PHP {pos['pnl']:.2f} ({pos['pnl_pct']:+.2f}%) | {pos['duration_minutes']}min | {pos['confidence']:.0f}%")
            
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"Error logging portfolio summary: {e}")

    async def _perform_daily_performance_review(self):
        """Perform comprehensive daily performance analysis"""
        try:
            self.logger.info("=" * 60)
            self.logger.info("DAILY PERFORMANCE REVIEW")
            self.logger.info("=" * 60)
            
            # Generate failure analysis report
            performance_report = self.trade_analyzer.generate_performance_report()
            
            if 'error' not in performance_report:
                summary = performance_report.get('summary', {})
                self.logger.info(f"Trades Today: {self.daily_trade_count}")
                self.logger.info(f"Total Trades: {summary.get('total_trades', 0)}")
                self.logger.info(f"Win Rate: {summary.get('win_rate', 'N/A')}")
                self.logger.info(f"Successful Trades: {summary.get('successful_trades', 0)}")
                
                # Log top failure categories
                failure_analysis = performance_report.get('failure_analysis', {})
                top_failures = failure_analysis.get('top_failure_categories', [])
                if top_failures:
                    self.logger.info("Top Failure Categories:")
                    for category, count in top_failures[:3]:
                        self.logger.info(f"  {category}: {count} occurrences")
                
                # Log recommendations
                recommendations = performance_report.get('recommendations', [])
                if recommendations:
                    self.logger.info("Strategy Recommendations:")
                    for rec in recommendations[:3]:
                        self.logger.info(f"  - {rec}")
            
            # Position manager statistics
            replacement_stats = self.position_manager.get_replacement_statistics()
            self.logger.info(f"Position Replacements: {replacement_stats['positions_closed_for_better']}")
            self.logger.info(f"Replacement Rate: {replacement_stats['replacement_rate']:.1f}%")
            
            # Current capital and performance
            win_rate = (self.successful_trades / self.total_trades * 100) if self.total_trades > 0 else 0
            self.logger.info(f"Current Capital: PHP {self.current_capital:.2f}")
            self.logger.info(f"Overall Win Rate: {win_rate:.1f}%")
            
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"Error in daily performance review: {e}")

    async def _perform_risk_checks(self):
        """Perform comprehensive risk management checks"""
        try:
            risk_metrics = self.risk_manager.get_risk_metrics(self.current_capital)
            
            # Check daily loss limit
            if risk_metrics.daily_pnl < -self.config.TRADING_CONFIG['daily_loss_limit']:
                self.logger.warning("ALERT: Daily loss limit reached - halting trading")
                self.is_paused = True
                
            # Check for market crash indicators
            if risk_metrics.portfolio_drawdown > 0.15:  # 15% drawdown
                self.logger.warning("ALERT: Market crash detected - emergency stop")
                await self._emergency_shutdown()
                
        except Exception as e:
            self.logger.error(f"ERROR: Error in risk checks: {e}")

    async def _emergency_shutdown(self):
        """Emergency shutdown procedure"""
        try:
            self.logger.warning("ALERT: EMERGENCY SHUTDOWN INITIATED")
            
            # Pause all new trading
            self.is_paused = True
            
            # Close all positions
            for symbol in list(self.risk_manager.positions.keys()):
                position = self.risk_manager.positions[symbol]
                await self.order_executor.close_position(position, 1.0, "emergency")
                self.risk_manager.close_position(symbol, "EMERGENCY", 1.0)
            
            self.logger.warning("ALERT: Emergency shutdown completed")
            
        except Exception as e:
            self.logger.error(f"ERROR: Error in emergency shutdown: {e}")

    async def _perform_system_health_check(self):
        """Perform system health checks for long-term operation"""
        try:
            # Check if all components are still responsive
            health_status = {
                'market_scanner': False,
                'order_executor': False,
                'risk_manager': True,  # Always available locally
                'continuous_monitoring': self.continuous_update and self.update_thread is not None
            }
            
            # Test market scanner
            try:
                candidates = self.market_scanner.get_latest_candidates()
                health_status['market_scanner'] = True
            except Exception as e:
                self.logger.warning(f"Market scanner health check failed: {e}")
                # Try to restart scanner
                await self.market_scanner.start_scanner()
            
            # Test order executor
            try:
                balance = await self.order_executor.get_account_balance()
                health_status['order_executor'] = balance is not None
            except Exception as e:
                self.logger.warning(f"Order executor health check failed: {e}")
                # Try to reinitialize
                await self.order_executor.start_executor()
            
            # Restart continuous monitoring if it died
            if not health_status['continuous_monitoring']:
                self.logger.warning("Continuous monitoring stopped - restarting...")
                self.start_continuous_monitoring()
            
            # Log health status
            failed_components = [k for k, v in health_status.items() if not v]
            if failed_components:
                self.logger.warning(f"Health check failed for: {', '.join(failed_components)}")
            else:
                self.logger.info("All systems healthy")
                
        except Exception as e:
            self.logger.error(f"Error in system health check: {e}")

    async def _perform_maintenance(self):
        """Perform routine maintenance for long-term operation"""
        try:
            self.logger.info("Performing routine system maintenance...")
            
            # Clear old log entries to prevent memory buildup
            import gc
            gc.collect()
            
            # Rotate log files if they get too large
            log_dir = Path("logs")
            for log_file in log_dir.glob("*.log"):
                if log_file.stat().st_size > 50 * 1024 * 1024:  # 50MB
                    # Archive large log files
                    archive_name = log_file.with_suffix(f".{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
                    log_file.rename(archive_name)
                    self.logger.info(f"Archived large log file: {archive_name}")
            
            # Check disk space
            import shutil
            free_space = shutil.disk_usage(".").free / (1024**3)  # GB
            if free_space < 1.0:  # Less than 1GB
                self.logger.warning(f"Low disk space: {free_space:.2f}GB remaining")
            
            # Cleanup old temporary files
            temp_files = list(Path(".").glob("*.tmp"))
            for temp_file in temp_files:
                try:
                    temp_file.unlink()
                except:
                    pass
            
            self.logger.info("System maintenance completed")
            
        except Exception as e:
            self.logger.error(f"Error during system maintenance: {e}")

    async def _log_daily_summary(self):
        """Log comprehensive daily summary for long-term tracking"""
        try:
            risk_metrics = self.risk_manager.get_risk_metrics(self.current_capital)
            runtime = datetime.now() - self.start_time if self.start_time else timedelta(0)
            
            # Get trade summary from trade logger
            trade_summary = self.trade_logger.get_daily_summary()
            
            self.logger.info("=" * 80)
            self.logger.info("TCAP v3 DAILY SUMMARY")
            self.logger.info("=" * 80)
            self.logger.info(f"   Date: {datetime.now().strftime('%Y-%m-%d')}")
            self.logger.info(f"   Total Runtime: {runtime}")
            self.logger.info(f"   Starting Capital: ${self.initial_capital:.2f}")
            self.logger.info(f"   Current Capital: ${self.current_capital:.2f}")
            self.logger.info(f"   Daily PnL: ${risk_metrics.daily_pnl:+.2f}")
            self.logger.info(f"   Total Return: {((self.current_capital - self.initial_capital) / self.initial_capital) * 100:+.2f}%")
            self.logger.info(f"   Total Trades: {self.total_trades}")
            self.logger.info(f"   Successful Trades: {self.successful_trades}")
            self.logger.info(f"   Success Rate: {(self.successful_trades/max(1,self.total_trades))*100:.1f}%")
            self.logger.info(f"   Open Positions: {risk_metrics.open_positions}")
            
            # Add detailed trade statistics
            if trade_summary['total_trades'] > 0:
                self.logger.info("   --- COMPLETED TRADES BREAKDOWN ---")
                self.logger.info(f"   Completed Trades: {trade_summary['total_trades']}")
                self.logger.info(f"   Winning Trades: {trade_summary['winning_trades']}")
                self.logger.info(f"   Losing Trades: {trade_summary['losing_trades']}")
                self.logger.info(f"   Completion Win Rate: {trade_summary['win_rate']:.1f}%")
                self.logger.info(f"   Total Completed P&L: ${trade_summary['total_profit']:+.2f}")
                self.logger.info(f"   Avg P&L per Completed Trade: ${trade_summary['avg_profit_per_trade']:+.2f}")
            
            self.logger.info("=" * 80)
            
            # Reset daily counters if needed
            self.risk_manager.reset_daily_metrics()
            
        except Exception as e:
            self.logger.error(f"ERROR: Error logging daily summary: {e}")

    async def _log_system_status(self):
        """Log comprehensive system status"""
        try:
            risk_metrics = self.risk_manager.get_risk_metrics(self.current_capital)
            
            self.logger.info("TCAP v3 System Status:")
            self.logger.info(f"   Runtime: {datetime.now() - self.start_time}")
            self.logger.info(f"   Capital: ${self.current_capital:.2f} (${risk_metrics.daily_pnl:+.2f} today)")
            self.logger.info(f"   Positions: {risk_metrics.open_positions}")
            self.logger.info(f"   Success Rate: {(self.successful_trades/max(1,self.total_trades))*100:.1f}%")
            self.logger.info(f"   Total Trades: {self.total_trades}")
            
        except Exception as e:
            self.logger.error(f"ERROR: Error logging system status: {e}")

    def _log_startup_info(self):
        """Log startup configuration and information"""
        self.logger.info(f"Starting Capital: ${self.initial_capital:,.2f}")
        self.logger.info(f"Target (12 months): ${self.initial_capital * 8.93:,.2f}")
        self.logger.info(f"Max Position Size: {self.config.TRADING_CONFIG['max_position_size']:.0%}")
        self.logger.info(f"Daily Loss Limit: ${self.config.TRADING_CONFIG['daily_loss_limit']}")
        self.logger.info(f"Max Leverage: {self.config.TRADING_CONFIG['max_leverage']}x")
        self.logger.info(f"Paper Trading: {'YES' if self.order_executor.paper_trading else 'NO'}")
        self.logger.info("=" * 60)
    
    async def _cleanup(self):
        """Cleanup resources when shutting down"""
        try:
            self.logger.info("Cleaning up resources...")
            
            # Stop continuous monitoring
            self.stop_continuous_monitoring()
            
            await self.market_scanner.stop_scanner()
            await self.technical_analyzer.close_session()
            await self.order_executor.close_session()
            
            # Log final statistics
            runtime = datetime.now() - self.start_time if self.start_time else timedelta(0)
            final_capital = self.current_capital
            total_return = ((final_capital - self.initial_capital) / self.initial_capital) * 100
            
            self.logger.info("Final Statistics:")
            self.logger.info(f"   Runtime: {runtime}")
            self.logger.info(f"   Initial Capital: ${self.initial_capital:.2f}")
            self.logger.info(f"   Final Capital: ${final_capital:.2f}")
            self.logger.info(f"   Total Return: {total_return:+.2f}%")
            self.logger.info(f"   Total Trades: {self.total_trades}")
            self.logger.info(f"   Successful Trades: {self.successful_trades}")
            
            self.logger.info("TCAP v3 shutdown complete")
            
        except Exception as e:
            self.logger.error(f"ERROR: Error during cleanup: {e}")

# Main execution
async def main():
    """Main entry point for TCAP v3"""
    engine = TcapEngine()
    
    def signal_handler():
        """Handle shutdown signals"""
        print("\nShutdown requested by user")
        engine.is_running = False
    
    # Set up signal handlers for graceful shutdown
    if sys.platform != 'win32':
        signal.signal(signal.SIGINT, lambda s, f: signal_handler())
        signal.signal(signal.SIGTERM, lambda s, f: signal_handler())
    
    try:
        # Check for required API keys in paper trading mode
        if not engine.config.SAFETY_CONFIG.get('paper_trading', True):
            if not os.getenv('BINANCE_API_KEY') or not os.getenv('BINANCE_SECRET_KEY'):
                print("ERROR: Binance API keys not configured!")
                print("For live trading, set BINANCE_API_KEY and BINANCE_SECRET_KEY environment variables")
                print("For paper trading, ensure PAPER_TRADING=true in .env file")
                return
        
        # Start trading system
        await engine.start_trading()
        
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"ERROR: Fatal error: {e}")
    finally:
        # Always ensure proper cleanup
        try:
            await engine.stop_trading()
        except Exception as e:
            print(f"Warning: Error during shutdown: {e}")

if __name__ == "__main__":
    print("Starting TCAP v3 - Automated Cryptocurrency Trading System")
    print("=" * 60)
    
    # Run the trading engine with proper exception handling
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSystem interrupted by user")
    except Exception as e:
        print(f"ERROR: System error: {e}")
    finally:
        print("TCAP v3 shutdown complete")
