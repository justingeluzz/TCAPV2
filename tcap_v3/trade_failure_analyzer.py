"""
TCAP v3 Trade Failure Analysis System
Logs trade reasons and performs post-mortem analysis for continuous improvement
"""

import logging
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class TradeAnalysis:
    """Complete trade analysis record"""
    trade_id: str
    symbol: str
    side: str  # 'LONG' or 'SHORT'
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    
    # Entry reasons
    entry_reasons: List[str]
    signal_confidence: float
    rsi_at_entry: float
    macd_signal_at_entry: str
    volume_ratio_at_entry: float
    price_momentum_24h: float
    
    # Exit analysis
    exit_reason: str = ""
    exit_type: str = ""  # 'PROFIT', 'STOP_LOSS', 'MANUAL', 'TIME_BASED'
    profit_loss: float = 0.0
    profit_loss_pct: float = 0.0
    hold_duration_minutes: int = 0
    
    # Failure analysis (if applicable)
    failure_category: str = ""
    failure_reason: str = ""
    market_condition_at_exit: str = ""
    volatility_spike: bool = False
    
    # Performance metrics
    max_profit_during_trade: float = 0.0
    max_loss_during_trade: float = 0.0
    
class TradeFailureAnalyzer:
    """
    Trade Failure Analysis System
    Tracks trade performance and identifies improvement opportunities
    """
    
    def __init__(self, log_directory: str = "logs/trade_analysis"):
        self.logger = logging.getLogger(__name__)
        self.log_dir = Path(log_directory)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize log files
        self.trade_log_file = self.log_dir / f"trade_analysis_{datetime.now().strftime('%Y%m%d')}.csv"
        self.failure_log_file = self.log_dir / f"failure_analysis_{datetime.now().strftime('%Y%m%d')}.json"
        
        self._initialize_csv_headers()
    
    def log_trade_entry(self, trade_data: Dict) -> str:
        """
        Log trade entry with all reasoning
        
        Args:
            trade_data: Dictionary containing trade entry information
            
        Returns:
            trade_id for tracking
        """
        try:
            trade_id = f"T{datetime.now().strftime('%Y%m%d_%H%M%S')}_{trade_data['symbol']}"
            
            # Create trade analysis record
            analysis = TradeAnalysis(
                trade_id=trade_id,
                symbol=trade_data['symbol'],
                side=trade_data['side'],
                entry_time=datetime.now(),
                exit_time=None,
                entry_price=trade_data['entry_price'],
                exit_price=None,
                entry_reasons=trade_data.get('entry_reasons', []),
                signal_confidence=trade_data.get('confidence', 0),
                rsi_at_entry=trade_data.get('rsi', 0),
                macd_signal_at_entry=trade_data.get('macd_signal', 'unknown'),
                volume_ratio_at_entry=trade_data.get('volume_ratio', 0),
                price_momentum_24h=trade_data.get('price_change_24h', 0)
            )
            
            # Log entry reasons
            entry_reason_text = " + ".join(analysis.entry_reasons)
            self.logger.info(f"TRADE ENTRY [{trade_id}]: {analysis.symbol} {analysis.side}")
            self.logger.info(f"  Entry Price: {analysis.entry_price:.6f}")
            self.logger.info(f"  Confidence: {analysis.signal_confidence:.1f}%")
            self.logger.info(f"  Reasons: {entry_reason_text}")
            self.logger.info(f"  Technical: RSI={analysis.rsi_at_entry:.1f}, MACD={analysis.macd_signal_at_entry}, Vol={analysis.volume_ratio_at_entry:.1f}x")
            
            # Store in memory for later completion
            self._store_trade_analysis(analysis)
            
            return trade_id
            
        except Exception as e:
            self.logger.error(f"Error logging trade entry: {e}")
            return ""
    
    def log_trade_exit(self, trade_id: str, exit_data: Dict):
        """
        Log trade exit and perform failure analysis
        
        Args:
            trade_id: Trade identifier from entry
            exit_data: Dictionary containing exit information
        """
        try:
            # Retrieve trade analysis
            analysis = self._get_trade_analysis(trade_id)
            if not analysis:
                self.logger.warning(f"Trade analysis not found for {trade_id}")
                return
            
            # Update exit information
            analysis.exit_time = datetime.now()
            analysis.exit_price = exit_data.get('exit_price', 0)
            analysis.exit_reason = exit_data.get('exit_reason', 'unknown')
            analysis.exit_type = exit_data.get('exit_type', 'unknown')
            analysis.profit_loss = exit_data.get('profit_loss', 0)
            analysis.profit_loss_pct = exit_data.get('profit_loss_pct', 0)
            
            # Calculate hold duration
            if analysis.exit_time and analysis.entry_time:
                duration = analysis.exit_time - analysis.entry_time
                analysis.hold_duration_minutes = int(duration.total_seconds() / 60)
            
            # Perform failure analysis if it's a losing trade
            if analysis.profit_loss < 0:
                self._perform_failure_analysis(analysis, exit_data)
            
            # Log exit summary
            self._log_trade_completion(analysis)
            
            # Save to CSV
            self._save_trade_to_csv(analysis)
            
            # Update failure statistics
            self._update_failure_statistics(analysis)
            
        except Exception as e:
            self.logger.error(f"Error logging trade exit for {trade_id}: {e}")
    
    def _perform_failure_analysis(self, analysis: TradeAnalysis, exit_data: Dict):
        """Analyze why a trade failed"""
        try:
            # Determine failure category
            if analysis.exit_type == "STOP_LOSS":
                # Analyze stop loss reasons
                volatility_info = exit_data.get('volatility_info', {})
                market_condition = exit_data.get('market_condition', 'normal')
                
                if volatility_info.get('volatility_spike', False):
                    analysis.failure_category = "VOLATILITY_SPIKE"
                    analysis.failure_reason = f"Stop loss hit during {volatility_info.get('volatility_level', 'high')} volatility spike"
                    analysis.volatility_spike = True
                elif market_condition == "crash":
                    analysis.failure_category = "MARKET_CRASH"
                    analysis.failure_reason = "Stop loss hit during market-wide crash"
                elif analysis.rsi_at_entry > 60:
                    analysis.failure_category = "ENTRY_TOO_LATE"
                    analysis.failure_reason = f"Entered too late with RSI {analysis.rsi_at_entry:.1f} (overbought)"
                elif "MACD" in analysis.entry_reasons[0] if analysis.entry_reasons else "":
                    analysis.failure_category = "MACD_FAKEOUT"
                    analysis.failure_reason = "MACD signal failed to follow through"
                else:
                    analysis.failure_category = "NORMAL_STOP_LOSS"
                    analysis.failure_reason = "Standard stop loss execution"
            
            elif analysis.exit_type == "TIME_BASED":
                analysis.failure_category = "NO_MOMENTUM"
                analysis.failure_reason = "Trade failed to gain momentum within time limit"
            
            analysis.market_condition_at_exit = exit_data.get('market_condition', 'normal')
            
        except Exception as e:
            self.logger.error(f"Error in failure analysis: {e}")
    
    def _log_trade_completion(self, analysis: TradeAnalysis):
        """Log comprehensive trade completion summary"""
        status = "PROFIT" if analysis.profit_loss > 0 else "LOSS"
        
        self.logger.info(f"TRADE EXIT [{analysis.trade_id}]: {analysis.symbol} {status}")
        self.logger.info(f"  Entry: {analysis.entry_price:.6f} @ {analysis.entry_time.strftime('%H:%M:%S')}")
        self.logger.info(f"  Exit: {analysis.exit_price:.6f} @ {analysis.exit_time.strftime('%H:%M:%S')}")
        self.logger.info(f"  P&L: PHP {analysis.profit_loss:.2f} ({analysis.profit_loss_pct:+.2f}%)")
        self.logger.info(f"  Duration: {analysis.hold_duration_minutes} minutes")
        self.logger.info(f"  Exit Reason: {analysis.exit_reason}")
        
        if analysis.failure_category:
            self.logger.warning(f"  Failure Analysis: {analysis.failure_category} - {analysis.failure_reason}")
    
    def _save_trade_to_csv(self, analysis: TradeAnalysis):
        """Save trade analysis to CSV file"""
        try:
            with open(self.trade_log_file, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                row = [
                    analysis.trade_id,
                    analysis.symbol,
                    analysis.side,
                    analysis.entry_time.isoformat(),
                    analysis.exit_time.isoformat() if analysis.exit_time else "",
                    analysis.entry_price,
                    analysis.exit_price or 0,
                    analysis.profit_loss,
                    analysis.profit_loss_pct,
                    analysis.hold_duration_minutes,
                    analysis.signal_confidence,
                    "; ".join(analysis.entry_reasons),
                    analysis.exit_reason,
                    analysis.exit_type,
                    analysis.failure_category,
                    analysis.failure_reason,
                    analysis.rsi_at_entry,
                    analysis.macd_signal_at_entry,
                    analysis.volume_ratio_at_entry,
                    analysis.volatility_spike
                ]
                
                writer.writerow(row)
                
        except Exception as e:
            self.logger.error(f"Error saving trade to CSV: {e}")
    
    def _initialize_csv_headers(self):
        """Initialize CSV file with headers"""
        headers = [
            "trade_id", "symbol", "side", "entry_time", "exit_time",
            "entry_price", "exit_price", "profit_loss", "profit_loss_pct",
            "hold_duration_minutes", "signal_confidence", "entry_reasons",
            "exit_reason", "exit_type", "failure_category", "failure_reason",
            "rsi_at_entry", "macd_signal_at_entry", "volume_ratio_at_entry",
            "volatility_spike"
        ]
        
        if not self.trade_log_file.exists():
            try:
                with open(self.trade_log_file, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow(headers)
            except Exception as e:
                self.logger.error(f"Error creating CSV headers: {e}")
    
    def _store_trade_analysis(self, analysis: TradeAnalysis):
        """Store trade analysis in memory for completion"""
        # This would be implemented with a database or in-memory store
        # For now, just log it
        pass
    
    def _get_trade_analysis(self, trade_id: str) -> Optional[TradeAnalysis]:
        """Retrieve stored trade analysis"""
        # This would retrieve from database or memory store
        # For now, return None (would need proper implementation)
        return None
    
    def _update_failure_statistics(self, analysis: TradeAnalysis):
        """Update failure statistics for strategy improvement"""
        try:
            stats_file = self.log_dir / "failure_statistics.json"
            
            # Load existing stats
            if stats_file.exists():
                with open(stats_file, 'r') as f:
                    stats = json.load(f)
            else:
                stats = {
                    "total_trades": 0,
                    "failed_trades": 0,
                    "failure_categories": {},
                    "common_failure_reasons": {},
                    "rsi_failure_analysis": {"high_rsi_failures": 0, "low_rsi_failures": 0},
                    "macd_fakeouts": 0,
                    "volatility_spike_losses": 0
                }
            
            # Update statistics
            stats["total_trades"] += 1
            
            if analysis.profit_loss < 0:
                stats["failed_trades"] += 1
                
                # Track failure categories
                if analysis.failure_category:
                    category = analysis.failure_category
                    stats["failure_categories"][category] = stats["failure_categories"].get(category, 0) + 1
                
                # Track common reasons
                if analysis.failure_reason:
                    reason = analysis.failure_reason
                    stats["common_failure_reasons"][reason] = stats["common_failure_reasons"].get(reason, 0) + 1
                
                # RSI analysis
                if analysis.rsi_at_entry > 60:
                    stats["rsi_failure_analysis"]["high_rsi_failures"] += 1
                elif analysis.rsi_at_entry < 40:
                    stats["rsi_failure_analysis"]["low_rsi_failures"] += 1
                
                # MACD fakeouts
                if analysis.failure_category == "MACD_FAKEOUT":
                    stats["macd_fakeouts"] += 1
                
                # Volatility spikes
                if analysis.volatility_spike:
                    stats["volatility_spike_losses"] += 1
            
            # Save updated stats
            with open(stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error updating failure statistics: {e}")
    
    def generate_performance_report(self) -> Dict:
        """Generate performance and failure analysis report"""
        try:
            stats_file = self.log_dir / "failure_statistics.json"
            
            if not stats_file.exists():
                return {"error": "No statistics available"}
            
            with open(stats_file, 'r') as f:
                stats = json.load(f)
            
            total_trades = stats.get("total_trades", 0)
            failed_trades = stats.get("failed_trades", 0)
            
            if total_trades == 0:
                return {"error": "No trades recorded"}
            
            win_rate = ((total_trades - failed_trades) / total_trades) * 100
            
            report = {
                "summary": {
                    "total_trades": total_trades,
                    "successful_trades": total_trades - failed_trades,
                    "failed_trades": failed_trades,
                    "win_rate": f"{win_rate:.1f}%"
                },
                "failure_analysis": {
                    "top_failure_categories": sorted(stats.get("failure_categories", {}).items(), 
                                                   key=lambda x: x[1], reverse=True)[:5],
                    "common_failure_reasons": sorted(stats.get("common_failure_reasons", {}).items(), 
                                                   key=lambda x: x[1], reverse=True)[:5],
                    "rsi_insights": stats.get("rsi_failure_analysis", {}),
                    "macd_fakeouts": stats.get("macd_fakeouts", 0),
                    "volatility_related_losses": stats.get("volatility_spike_losses", 0)
                },
                "recommendations": self._generate_recommendations(stats)
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating performance report: {e}")
            return {"error": f"Report generation failed: {e}"}
    
    def _generate_recommendations(self, stats: Dict) -> List[str]:
        """Generate improvement recommendations based on failure analysis"""
        recommendations = []
        
        try:
            total_trades = stats.get("total_trades", 0)
            if total_trades < 10:
                return ["Insufficient data for recommendations (need at least 10 trades)"]
            
            # RSI-based recommendations
            rsi_stats = stats.get("rsi_failure_analysis", {})
            high_rsi_failures = rsi_stats.get("high_rsi_failures", 0)
            if high_rsi_failures > total_trades * 0.3:
                recommendations.append("Consider lowering RSI upper threshold (too many late entries)")
            
            # MACD recommendations
            macd_fakeouts = stats.get("macd_fakeouts", 0)
            if macd_fakeouts > total_trades * 0.2:
                recommendations.append("Strengthen MACD confirmation requirements (high fakeout rate)")
            
            # Volatility recommendations
            volatility_losses = stats.get("volatility_spike_losses", 0)
            if volatility_losses > total_trades * 0.25:
                recommendations.append("Implement wider stop losses during high volatility periods")
            
            # Failure category analysis
            failure_categories = stats.get("failure_categories", {})
            if failure_categories.get("ENTRY_TOO_LATE", 0) > total_trades * 0.2:
                recommendations.append("Improve entry timing - consider earlier entry signals")
            
            if not recommendations:
                recommendations.append("Strategy performance is within acceptable parameters")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return ["Error generating recommendations"]
