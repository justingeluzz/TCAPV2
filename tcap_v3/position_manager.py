"""
TCAP v3 Position Manager
Manages maximum 3 open positions with profit optimization
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio

@dataclass
class OpenPosition:
    """Represents an open trading position"""
    trade_id: str
    symbol: str
    side: str  # 'LONG' or 'SHORT'
    entry_time: datetime
    entry_price: float
    current_price: float
    position_size: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    confidence_score: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    
    # Performance tracking
    max_profit_seen: float = 0.0
    max_drawdown_seen: float = 0.0
    hold_duration_minutes: int = 0
    
    def update_current_price(self, new_price: float):
        """Update current price and calculate new P&L"""
        self.current_price = new_price
        
        if self.side == "LONG":
            self.unrealized_pnl = (new_price - self.entry_price) * self.position_size / self.entry_price
            self.unrealized_pnl_pct = (new_price - self.entry_price) / self.entry_price * 100
        else:  # SHORT
            self.unrealized_pnl = (self.entry_price - new_price) * self.position_size / self.entry_price
            self.unrealized_pnl_pct = (self.entry_price - new_price) / self.entry_price * 100
        
        # Update max profit/drawdown tracking
        if self.unrealized_pnl > self.max_profit_seen:
            self.max_profit_seen = self.unrealized_pnl
        
        if self.unrealized_pnl < self.max_drawdown_seen:
            self.max_drawdown_seen = self.unrealized_pnl
        
        # Update hold duration
        duration = datetime.now() - self.entry_time
        self.hold_duration_minutes = int(duration.total_seconds() / 60)

class PositionManager:
    """
    Manages maximum 3 open positions with profit optimization
    Ensures only the most profitable opportunities are held
    """
    
    def __init__(self, max_positions: int = 3):
        self.logger = logging.getLogger(__name__)
        self.max_positions = max_positions
        self.open_positions: List[OpenPosition] = []
        
        # Performance tracking
        self.total_positions_opened = 0
        self.positions_closed_for_better = 0
        self.avg_profit_of_replaced_positions = 0.0
    
    def can_open_new_position(self) -> bool:
        """Check if we can open a new position"""
        return len(self.open_positions) < self.max_positions
    
    def should_replace_position(self, new_signal_confidence: float, new_potential_profit: float) -> Tuple[bool, Optional[str]]:
        """
        Determine if we should close an existing position for a better opportunity
        
        Args:
            new_signal_confidence: Confidence score of new signal (0-100)
            new_potential_profit: Estimated profit potential of new signal
            
        Returns:
            Tuple of (should_replace, position_id_to_replace)
        """
        try:
            if len(self.open_positions) < self.max_positions:
                return False, None
            
            # Find the weakest position to potentially replace
            weakest_position = self._find_weakest_position()
            if not weakest_position:
                return False, None
            
            # Decision criteria for replacement
            should_replace = False
            replacement_reasons = []
            
            # 1. Confidence comparison
            confidence_difference = new_signal_confidence - weakest_position.confidence_score
            if confidence_difference >= 10:  # At least 10% better confidence
                should_replace = True
                replacement_reasons.append(f"confidence +{confidence_difference:.1f}%")
            
            # 2. Potential profit comparison
            current_potential = self._calculate_remaining_potential(weakest_position)
            if new_potential_profit > current_potential * 1.5:  # 50% better potential
                should_replace = True
                replacement_reasons.append(f"potential +{((new_potential_profit/current_potential-1)*100):.1f}%")
            
            # 3. Position performance analysis
            if weakest_position.unrealized_pnl_pct < -2:  # Position losing 2%+
                if new_signal_confidence >= 70:  # Strong new signal
                    should_replace = True
                    replacement_reasons.append("cutting loss for strong signal")
            
            # 4. Time-based considerations
            if weakest_position.hold_duration_minutes >= 240:  # Held for 4+ hours
                if weakest_position.unrealized_pnl_pct < 5:  # Less than 5% profit
                    if new_signal_confidence >= 65:
                        should_replace = True
                        replacement_reasons.append("stagnant position replacement")
            
            # 5. Risk-adjusted considerations
            if weakest_position.unrealized_pnl_pct < 0:  # Currently losing
                distance_to_stop = abs(weakest_position.current_price - weakest_position.stop_loss) / weakest_position.current_price * 100
                if distance_to_stop < 3:  # Close to stop loss
                    should_replace = True
                    replacement_reasons.append("near stop loss")
            
            if should_replace:
                reason_text = ", ".join(replacement_reasons)
                self.logger.info(f"Position replacement recommended: {weakest_position.symbol} ({reason_text})")
                return True, weakest_position.trade_id
            
            return False, None
            
        except Exception as e:
            self.logger.error(f"Error in position replacement analysis: {e}")
            return False, None
    
    def add_position(self, position: OpenPosition) -> bool:
        """
        Add a new position to the portfolio
        
        Args:
            position: OpenPosition object to add
            
        Returns:
            True if position was added successfully
        """
        try:
            if len(self.open_positions) >= self.max_positions:
                self.logger.warning(f"Cannot add position - maximum {self.max_positions} positions reached")
                return False
            
            self.open_positions.append(position)
            self.total_positions_opened += 1
            
            self.logger.info(f"Position added: {position.symbol} {position.side}")
            self.logger.info(f"  Entry: {position.entry_price:.6f}, Size: PHP {position.position_size:.0f}")
            self.logger.info(f"  Confidence: {position.confidence_score:.1f}%")
            self.logger.info(f"  Open Positions: {len(self.open_positions)}/{self.max_positions}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding position: {e}")
            return False
    
    def remove_position(self, trade_id: str, exit_reason: str = "manual") -> Optional[OpenPosition]:
        """
        Remove a position from the portfolio
        
        Args:
            trade_id: ID of position to remove
            exit_reason: Reason for position exit
            
        Returns:
            The removed position object, or None if not found
        """
        try:
            for i, position in enumerate(self.open_positions):
                if position.trade_id == trade_id:
                    removed_position = self.open_positions.pop(i)
                    
                    # Track replacement statistics
                    if exit_reason == "replaced_for_better":
                        self.positions_closed_for_better += 1
                        if removed_position.unrealized_pnl > 0:
                            self.avg_profit_of_replaced_positions = (
                                (self.avg_profit_of_replaced_positions * (self.positions_closed_for_better - 1) + 
                                 removed_position.unrealized_pnl) / self.positions_closed_for_better
                            )
                    
                    self.logger.info(f"Position removed: {removed_position.symbol} ({exit_reason})")
                    self.logger.info(f"  Final P&L: PHP {removed_position.unrealized_pnl:.2f} ({removed_position.unrealized_pnl_pct:+.2f}%)")
                    self.logger.info(f"  Hold Duration: {removed_position.hold_duration_minutes} minutes")
                    self.logger.info(f"  Remaining Positions: {len(self.open_positions)}")
                    
                    return removed_position
            
            self.logger.warning(f"Position {trade_id} not found for removal")
            return None
            
        except Exception as e:
            self.logger.error(f"Error removing position {trade_id}: {e}")
            return None
    
    def update_all_positions(self, price_data: Dict[str, float]):
        """
        Update all positions with current market prices
        
        Args:
            price_data: Dictionary of symbol -> current_price
        """
        try:
            for position in self.open_positions:
                if position.symbol in price_data:
                    position.update_current_price(price_data[position.symbol])
            
        except Exception as e:
            self.logger.error(f"Error updating positions: {e}")
    
    def get_portfolio_summary(self) -> Dict:
        """Get comprehensive portfolio summary"""
        try:
            if not self.open_positions:
                return {
                    "open_positions": 0,
                    "total_unrealized_pnl": 0,
                    "total_unrealized_pnl_pct": 0,
                    "best_performer": None,
                    "worst_performer": None,
                    "avg_confidence": 0,
                    "positions": []
                }
            
            total_pnl = sum(pos.unrealized_pnl for pos in self.open_positions)
            total_size = sum(pos.position_size for pos in self.open_positions)
            avg_pnl_pct = total_pnl / total_size * 100 if total_size > 0 else 0
            
            # Find best and worst performers
            best_performer = max(self.open_positions, key=lambda p: p.unrealized_pnl_pct)
            worst_performer = min(self.open_positions, key=lambda p: p.unrealized_pnl_pct)
            
            avg_confidence = sum(pos.confidence_score for pos in self.open_positions) / len(self.open_positions)
            
            return {
                "open_positions": len(self.open_positions),
                "total_unrealized_pnl": total_pnl,
                "total_unrealized_pnl_pct": avg_pnl_pct,
                "best_performer": {
                    "symbol": best_performer.symbol,
                    "pnl_pct": best_performer.unrealized_pnl_pct,
                    "pnl": best_performer.unrealized_pnl
                },
                "worst_performer": {
                    "symbol": worst_performer.symbol,
                    "pnl_pct": worst_performer.unrealized_pnl_pct,
                    "pnl": worst_performer.unrealized_pnl
                },
                "avg_confidence": avg_confidence,
                "positions": [
                    {
                        "symbol": pos.symbol,
                        "side": pos.side,
                        "entry_price": pos.entry_price,
                        "current_price": pos.current_price,
                        "pnl": pos.unrealized_pnl,
                        "pnl_pct": pos.unrealized_pnl_pct,
                        "confidence": pos.confidence_score,
                        "duration_minutes": pos.hold_duration_minutes
                    }
                    for pos in self.open_positions
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error generating portfolio summary: {e}")
            return {"error": f"Summary generation failed: {e}"}
    
    def _find_weakest_position(self) -> Optional[OpenPosition]:
        """Find the weakest position for potential replacement"""
        if not self.open_positions:
            return None
        
        # Score positions based on multiple factors
        scored_positions = []
        
        for position in self.open_positions:
            score = 0
            
            # Performance score (40% weight)
            performance_score = position.unrealized_pnl_pct * 0.4
            score += performance_score
            
            # Confidence score (30% weight)
            confidence_score = (position.confidence_score - 50) * 0.3  # Normalize around 50%
            score += confidence_score
            
            # Time factor (20% weight) - penalize stagnant positions
            time_penalty = min(position.hold_duration_minutes / 60, 4) * -2  # Max 4 hours penalty
            score += time_penalty * 0.2
            
            # Potential remaining (10% weight)
            remaining_potential = self._calculate_remaining_potential(position)
            potential_score = remaining_potential * 0.1
            score += potential_score
            
            scored_positions.append((position, score))
        
        # Return position with lowest score
        weakest = min(scored_positions, key=lambda x: x[1])
        return weakest[0]
    
    def _calculate_remaining_potential(self, position: OpenPosition) -> float:
        """Calculate remaining profit potential for a position"""
        try:
            if position.side == "LONG":
                # Distance to first take profit
                tp1_potential = (position.take_profit_1 - position.current_price) / position.current_price * 100
                # Distance to second take profit
                tp2_potential = (position.take_profit_2 - position.current_price) / position.current_price * 100
            else:  # SHORT
                tp1_potential = (position.current_price - position.take_profit_1) / position.current_price * 100
                tp2_potential = (position.current_price - position.take_profit_2) / position.current_price * 100
            
            # Weighted average potential (30% to TP1, 70% to TP2)
            remaining_potential = (tp1_potential * 0.3 + tp2_potential * 0.7)
            
            return max(0, remaining_potential)  # Can't be negative
            
        except Exception as e:
            self.logger.error(f"Error calculating remaining potential: {e}")
            return 0
    
    def get_position_rankings(self) -> List[Dict]:
        """Get positions ranked by performance and potential"""
        try:
            rankings = []
            
            for position in self.open_positions:
                remaining_potential = self._calculate_remaining_potential(position)
                
                # Calculate overall ranking score
                ranking_score = (
                    position.unrealized_pnl_pct * 0.3 +  # Current performance
                    position.confidence_score * 0.25 +   # Signal confidence
                    remaining_potential * 0.25 +         # Remaining potential
                    (position.max_profit_seen * 0.2)     # Historical performance
                )
                
                rankings.append({
                    "rank": 0,  # Will be set after sorting
                    "trade_id": position.trade_id,
                    "symbol": position.symbol,
                    "ranking_score": ranking_score,
                    "current_pnl_pct": position.unrealized_pnl_pct,
                    "confidence": position.confidence_score,
                    "remaining_potential": remaining_potential,
                    "max_profit_seen": position.max_profit_seen,
                    "hold_duration": position.hold_duration_minutes
                })
            
            # Sort by ranking score (highest first)
            rankings.sort(key=lambda x: x["ranking_score"], reverse=True)
            
            # Assign ranks
            for i, ranking in enumerate(rankings):
                ranking["rank"] = i + 1
            
            return rankings
            
        except Exception as e:
            self.logger.error(f"Error generating position rankings: {e}")
            return []
    
    def get_replacement_statistics(self) -> Dict:
        """Get statistics about position replacements"""
        return {
            "total_positions_opened": self.total_positions_opened,
            "positions_closed_for_better": self.positions_closed_for_better,
            "replacement_rate": (self.positions_closed_for_better / self.total_positions_opened * 100) if self.total_positions_opened > 0 else 0,
            "avg_profit_of_replaced": self.avg_profit_of_replaced_positions
        }
