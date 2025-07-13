"""
TCAP v3 Trade Logger
Logs every completed trade with detailed information
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class CompletedTrade:
    """Data structure for a completed trade"""
    trade_id: str
    symbol: str
    side: str  # LONG or SHORT
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: float
    position_size_usdt: float
    exit_reason: str  # TAKE_PROFIT_1, TAKE_PROFIT_2, STOP_LOSS, etc.
    profit_loss: float
    profit_loss_percent: float
    duration_seconds: int
    fees: float
    net_profit: float
    confidence: float
    technical_reason: str
    market_conditions: str

class TradeLogger:
    """Logs completed trades to various formats"""
    
    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = logs_dir
        self.ensure_logs_directory()
        
        # Setup detailed trade logger
        self.trade_logger = logging.getLogger('trade_logger')
        self.trade_logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.trade_logger.handlers[:]:
            self.trade_logger.removeHandler(handler)
        
        # Create trade-specific log file with UTF-8 encoding
        trade_log_file = os.path.join(self.logs_dir, f"completed_trades_{datetime.now().strftime('%Y%m%d')}.log")
        trade_handler = logging.FileHandler(trade_log_file, encoding='utf-8')
        trade_formatter = logging.Formatter('%(asctime)s | TRADE | %(message)s')
        trade_handler.setFormatter(trade_formatter)
        self.trade_logger.addHandler(trade_handler)
        
        # JSON log file for structured data
        self.json_log_file = os.path.join(self.logs_dir, f"trades_{datetime.now().strftime('%Y%m%d')}.json")
        
        # CSV log file for easy analysis
        self.csv_log_file = os.path.join(self.logs_dir, f"trades_{datetime.now().strftime('%Y%m%d')}.csv")
        self.ensure_csv_header()
        
    def ensure_logs_directory(self):
        """Create logs directory if it doesn't exist"""
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir)
    
    def ensure_csv_header(self):
        """Ensure CSV file has proper header"""
        if not os.path.exists(self.csv_log_file):
            header = "timestamp,trade_id,symbol,side,entry_time,exit_time,entry_price,exit_price,quantity,position_size_usdt,exit_reason,profit_loss,profit_loss_percent,duration_seconds,fees,net_profit,confidence,technical_reason,market_conditions\n"
            with open(self.csv_log_file, 'w') as f:
                f.write(header)
    
    def log_completed_trade(self, trade: CompletedTrade):
        """Log a completed trade to all formats"""
        try:
            # 1. Detailed text log
            self._log_detailed_text(trade)
            
            # 2. JSON log for structured data
            self._log_json(trade)
            
            # 3. CSV log for analysis
            self._log_csv(trade)
            
            # 4. Console summary
            self._log_console_summary(trade)
            
        except Exception as e:
            logging.error(f"ERROR: Failed to log completed trade {trade.trade_id}: {e}")
    
    def _log_detailed_text(self, trade: CompletedTrade):
        """Log detailed text format"""
        profit_symbol = "[PROFIT]" if trade.profit_loss > 0 else "[LOSS]"
        
        detailed_log = f"""
===============================================================================
{profit_symbol} TRADE COMPLETED: {trade.trade_id}
===============================================================================
Symbol: {trade.symbol}
Side: {trade.side}
Entry Time: {trade.entry_time.strftime('%Y-%m-%d %H:%M:%S')}
Exit Time: {trade.exit_time.strftime('%Y-%m-%d %H:%M:%S')}
Duration: {trade.duration_seconds // 60}m {trade.duration_seconds % 60}s

PRICES:
  Entry Price: ${trade.entry_price:.6f}
  Exit Price: ${trade.exit_price:.6f}
  Price Change: {((trade.exit_price - trade.entry_price) / trade.entry_price * 100):+.2f}%

POSITION:
  Quantity: {trade.quantity:,.2f} {trade.symbol.replace('USDT', '')}
  Position Size: ${trade.position_size_usdt:,.2f}
  Exit Reason: {trade.exit_reason}

PROFIT/LOSS:
  Gross P&L: ${trade.profit_loss:+,.2f} ({trade.profit_loss_percent:+.2f}%)
  Fees: ${trade.fees:,.2f}
  Net P&L: ${trade.net_profit:+,.2f}

ANALYSIS:
  Signal Confidence: {trade.confidence:.1%}
  Technical Reason: {trade.technical_reason}
  Market Conditions: {trade.market_conditions}
===============================================================================
"""
        self.trade_logger.info(detailed_log.strip())
    
    def _log_json(self, trade: CompletedTrade):
        """Log to JSON file for structured analysis"""
        try:
            # Convert trade to dict and handle datetime serialization
            trade_dict = asdict(trade)
            trade_dict['entry_time'] = trade.entry_time.isoformat()
            trade_dict['exit_time'] = trade.exit_time.isoformat()
            trade_dict['timestamp'] = datetime.now().isoformat()
            
            # Append to JSON file (one object per line for easy parsing)
            with open(self.json_log_file, 'a') as f:
                f.write(json.dumps(trade_dict) + '\n')
                
        except Exception as e:
            logging.error(f"ERROR: Failed to write JSON trade log: {e}")
    
    def _log_csv(self, trade: CompletedTrade):
        """Log to CSV file for spreadsheet analysis"""
        try:
            csv_line = f"{datetime.now().isoformat()},{trade.trade_id},{trade.symbol},{trade.side},{trade.entry_time.isoformat()},{trade.exit_time.isoformat()},{trade.entry_price},{trade.exit_price},{trade.quantity},{trade.position_size_usdt},{trade.exit_reason},{trade.profit_loss},{trade.profit_loss_percent},{trade.duration_seconds},{trade.fees},{trade.net_profit},{trade.confidence},{trade.technical_reason.replace(',', ';')},{trade.market_conditions.replace(',', ';')}\n"
            
            with open(self.csv_log_file, 'a') as f:
                f.write(csv_line)
                
        except Exception as e:
            logging.error(f"ERROR: Failed to write CSV trade log: {e}")
    
    def _log_console_summary(self, trade: CompletedTrade):
        """Log summary to console"""
        profit_emoji = "[PROFIT]" if trade.profit_loss > 0 else "[LOSS]"
        direction = "[LONG]" if trade.side == "LONG" else "[SHORT]"
        
        summary = f"{profit_emoji} TRADE COMPLETE: {direction} {trade.symbol} | {trade.exit_reason} | ${trade.net_profit:+.2f} ({trade.profit_loss_percent:+.1f}%) | {trade.duration_seconds//60}m{trade.duration_seconds%60}s"
        
        # Use main logger for console output
        main_logger = logging.getLogger('__main__')
        if trade.profit_loss > 0:
            main_logger.info(f"PROFIT: {summary}")
        else:
            main_logger.warning(f"LOSS: {summary}")
    
    def get_daily_summary(self) -> Dict[str, Any]:
        """Get summary of today's completed trades"""
        try:
            if not os.path.exists(self.json_log_file):
                return {"total_trades": 0, "total_profit": 0, "win_rate": 0}
            
            trades = []
            with open(self.json_log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        trades.append(json.loads(line))
            
            if not trades:
                return {"total_trades": 0, "total_profit": 0, "win_rate": 0}
            
            total_trades = len(trades)
            winning_trades = sum(1 for trade in trades if trade['net_profit'] > 0)
            total_profit = sum(trade['net_profit'] for trade in trades)
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            
            return {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": total_trades - winning_trades,
                "total_profit": total_profit,
                "win_rate": win_rate,
                "avg_profit_per_trade": total_profit / total_trades if total_trades > 0 else 0
            }
            
        except Exception as e:
            logging.error(f"ERROR: Failed to generate daily summary: {e}")
            return {"total_trades": 0, "total_profit": 0, "win_rate": 0, "error": str(e)}

# Example usage
if __name__ == "__main__":
    # Test the trade logger
    logger = TradeLogger()
    
    test_trade = CompletedTrade(
        trade_id="TCAP_20250713_001",
        symbol="MAVIAUSDT",
        side="LONG",
        entry_time=datetime.now(),
        exit_time=datetime.now(),
        entry_price=0.1770,
        exit_price=0.1787,
        quantity=28280.55,
        position_size_usdt=5000.0,
        exit_reason="TAKE_PROFIT_1",
        profit_loss=48.27,
        profit_loss_percent=1.0,
        duration_seconds=420,
        fees=2.50,
        net_profit=45.77,
        confidence=0.65,
        technical_reason="RSI oversold + MACD bullish crossover",
        market_conditions="Strong uptrend with high volume"
    )
    
    logger.log_completed_trade(test_trade)
    print("Test trade logged successfully!")
