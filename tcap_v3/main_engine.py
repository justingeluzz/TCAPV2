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
        
        # Engine state
        self.is_running = False
        self.is_paused = False
        self.start_time = None
        self.total_trades = 0
        self.successful_trades = 0
        
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
        """Process new trading signals"""
        try:
            # Get market candidates from scanner
            candidates = self.market_scanner.get_latest_candidates()
            if not candidates:
                return
            
            self.logger.info(f"Processing {len(candidates)} market candidates...")
            
            # Generate signals for candidates
            signals = []
            for candidate in candidates:
                try:
                    # Get technical analysis data
                    tech_data = await self.technical_analyzer.analyze_symbol(candidate.symbol, candidate)
                    if not tech_data:
                        continue
                    
                    # Generate signal
                    signal = await self.signal_generator.generate_signal(candidate, tech_data)
                    if signal:
                        signals.append(signal)
                        
                except Exception as e:
                    self.logger.warning(f"WARNING: Error processing {candidate.symbol}: {e}")
            
            # Execute signals
            for signal in signals:
                await self._execute_signal(signal)
                
        except Exception as e:
            self.logger.error(f"ERROR: Error processing new signals: {e}")

    async def _execute_signal(self, signal: TradingSignal):
        """Execute a trading signal"""
        try:
            self.logger.info(f"Processing {signal.signal_type} signal for {signal.symbol}")
            
            # Check if we can afford this position
            position_size = self.risk_manager.calculate_position_size(
                signal, self.current_capital
            )
            
            if position_size <= 0:
                return
            
            # Execute the order
            order_result = await self.order_executor.execute_signal(signal, position_size)
            if not order_result.success:
                self.logger.error(f"ERROR: Failed to execute order: {order_result.error_message}")
                return
            
            # Create position tracking
            position = self.risk_manager.create_position(signal, order_result)
            if not position:
                self.logger.error(f"ERROR: Failed to create position for {signal.symbol}")
                return
            
            self.logger.info(f"Position opened: {signal.signal_type} {signal.symbol}")
            self.total_trades += 1
            
            # Set up exit orders
            await self._setup_exit_orders(position)
            
        except Exception as e:
            self.logger.error(f"ERROR: Error executing signal for {signal.symbol}: {e}")

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
        """Update all open positions"""
        try:
            for symbol, position in list(self.risk_manager.positions.items()):
                # Get current price
                current_price = await self.order_executor.get_current_price(symbol)
                if current_price is None:
                    continue
                
                # Update position
                self.risk_manager.update_position_price(symbol, current_price)
                
                # Check for exit signals
                if self.risk_manager.should_exit_position(symbol):
                    await self._handle_position_exit(position)
                    
        except Exception as e:
            self.logger.error(f"ERROR: Error updating positions: {e}")

    async def _handle_position_exit(self, position: Position):
        """Handle position exit"""
        try:
            # Determine exit reason and percentage
            exit_percentage = 1.0  # Full exit for now
            reason = "technical_signal"
            
            # Close position
            close_result = await self.order_executor.close_position(
                position, exit_percentage, reason
            )
            
            if close_result.success:
                # Update position tracking
                realized_pnl = self.risk_manager.close_position(
                    position.symbol, reason, exit_percentage
                )
                
                # Update capital
                self.current_capital += realized_pnl
                
                if realized_pnl > 0:
                    self.successful_trades += 1
                    self.logger.info(f"Take profit hit: {position.symbol} - PnL: ${realized_pnl:.2f}")
                else:
                    self.logger.info(f"Stop loss hit: {position.symbol} - PnL: ${realized_pnl:.2f}")
                    
        except Exception as e:
            self.logger.error(f"ERROR: Error handling exit signal for {position.symbol}: {e}")

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
