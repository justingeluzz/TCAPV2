"""
TCAP v3 Order Executor
Handles automatic order placement, execution, and monitoring via Binance API
"""

import asyncio
import aiohttp
import hmac
import hashlib
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
from urllib.parse import urlencode

from config import TcapConfig
from signal_generator import TradingSignal
from risk_manager import Position

@dataclass
class OrderResult:
    """Result of order execution"""
    success: bool
    order_id: Optional[str] = None
    filled_price: Optional[float] = None
    filled_quantity: Optional[float] = None
    error_message: Optional[str] = None
    timestamp: datetime = None

@dataclass
class OrderStatus:
    """Order status information"""
    order_id: str
    symbol: str
    side: str  # BUY/SELL
    type: str  # LIMIT/MARKET/STOP
    status: str  # NEW/FILLED/CANCELLED
    quantity: float
    filled_quantity: float
    price: float
    average_price: Optional[float] = None
    time_in_force: str = "GTC"
    update_time: datetime = None

class OrderExecutor:
    """
    TCAP v3 Order Execution Engine
    Handles automatic order placement and management via Binance Futures API
    """
    
    def __init__(self):
        self.config = TcapConfig()
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(__name__)
        
        # Order tracking
        self.active_orders: Dict[str, OrderStatus] = {}
        self.executed_orders: List[OrderStatus] = []
        
        # API rate limiting
        self.request_count = 0
        self.last_request_time = time.time()
        
        # Safety flags
        self.paper_trading = self.config.SAFETY_CONFIG['paper_trading_mode']
        self.orders_enabled = True
        
    async def start_executor(self):
        """Initialize the order executor"""
        try:
            self.logger.info("Starting TCAP v3 Order Executor...")
            
            # Validate API keys
            if not self.config.validate_api_keys() and not self.paper_trading:
                self.logger.error("ERROR: Binance API keys not configured")
                return False
            
            # Create session
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
            # Test connection
            if not self.paper_trading:
                account_info = await self.get_account_info()
                if account_info:
                    self.logger.info("SUCCESS: Binance API connection established")
                else:
                    self.logger.error("ERROR: Failed to connect to Binance API")
                    return False
            else:
                self.logger.info("Paper trading mode enabled")
            
            return True
            
        except Exception as e:
            self.logger.error(f"ERROR: Error starting order executor: {e}")
            return False
    
    async def execute_signal(self, signal: TradingSignal, position_size: float = None) -> OrderResult:
        """Execute a trading signal by placing market entry order"""
        try:
            self.logger.info(f"EXEC: Executing {signal.signal_type} signal for {signal.symbol}")
            
            if not self.orders_enabled:
                return OrderResult(False, error_message="Order execution is disabled")
            
            # Determine order side
            side = "BUY" if signal.signal_type == "LONG" else "SELL"
            
            # Use provided position_size or fall back to signal's position_size
            final_position_size = position_size if position_size is not None else signal.position_size
            
            # Calculate quantity
            notional_value = final_position_size * signal.leverage
            quantity = notional_value / signal.entry_price
            
            # Round quantity to valid precision
            quantity = await self._round_quantity(signal.symbol, quantity)
            
            if self.paper_trading:
                # Simulate order execution
                return await self._simulate_order(signal, side, quantity)
            else:
                # Execute real order
                return await self._place_market_order(signal.symbol, side, quantity, signal.leverage)
                
        except Exception as e:
            self.logger.error(f"ERROR: Error executing signal for {signal.symbol}: {e}")
            return OrderResult(False, error_message=str(e))
    
    async def place_stop_loss(self, position: Position) -> OrderResult:
        """Place stop loss order for a position"""
        try:
            self.logger.info(f"GUARD: Placing stop loss for {position.symbol} at ${position.stop_loss:.4f}")
            
            # Determine order side (opposite of position)
            side = "SELL" if position.side == "LONG" else "BUY"
            
            if self.paper_trading:
                return OrderResult(True, order_id=f"SL_{position.symbol}_{int(time.time())}")
            else:
                return await self._place_stop_order(
                    position.symbol, 
                    side, 
                    position.quantity, 
                    position.stop_loss
                )
                
        except Exception as e:
            self.logger.error(f"ERROR: Error placing stop loss for {position.symbol}: {e}")
            return OrderResult(False, error_message=str(e))
    
    async def place_take_profit(self, position: Position, target_price: float, quantity: float) -> OrderResult:
        """Place take profit order"""
        try:
            self.logger.info(f"TARGET: Placing take profit for {position.symbol} at ${target_price:.4f}")
            
            # Determine order side (opposite of position)
            side = "SELL" if position.side == "LONG" else "BUY"
            
            if self.paper_trading:
                return OrderResult(True, order_id=f"TP_{position.symbol}_{int(time.time())}")
            else:
                return await self._place_limit_order(
                    position.symbol,
                    side,
                    quantity,
                    target_price
                )
                
        except Exception as e:
            self.logger.error(f"ERROR: Error placing take profit for {position.symbol}: {e}")
            return OrderResult(False, error_message=str(e))
    
    async def close_position(self, position: Position, percentage: float = 1.0, reason: str = "manual") -> OrderResult:
        """Close position (market order)"""
        try:
            quantity_to_close = position.quantity * percentage
            quantity_to_close = await self._round_quantity(position.symbol, quantity_to_close)
            
            self.logger.info(f"PROFIT: Closing {percentage*100:.0f}% of {position.symbol} position ({reason})")
            
            # Determine order side (opposite of position)
            side = "SELL" if position.side == "LONG" else "BUY"
            
            if self.paper_trading:
                return await self._simulate_close(position, quantity_to_close, reason)
            else:
                return await self._place_market_order(
                    position.symbol,
                    side,
                    quantity_to_close,
                    1  # No leverage for closing
                )
                
        except Exception as e:
            self.logger.error(f"ERROR: Error closing position {position.symbol}: {e}")
            return OrderResult(False, error_message=str(e))
    
    async def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancel an active order"""
        try:
            if self.paper_trading:
                if order_id in self.active_orders:
                    del self.active_orders[order_id]
                return True
            else:
                return await self._cancel_binance_order(symbol, order_id)
                
        except Exception as e:
            self.logger.error(f"ERROR: Error canceling order {order_id}: {e}")
            return False
    
    async def get_account_balance(self) -> Optional[float]:
        """Get current account balance"""
        try:
            if self.paper_trading:
                # Return paper trading balance
                return float(self.config.TRADING_CONFIG['starting_capital'])
            else:
                # Get real account balance from Binance
                account_info = await self.get_account_info()
                if account_info and 'assets' in account_info:
                    # Find USDT balance
                    for asset in account_info['assets']:
                        if asset['asset'] == 'USDT':
                            return float(asset['walletBalance'])
                    
                    # If no USDT found, return 0
                    return 0.0
                else:
                    self.logger.error("ERROR: Failed to get account info")
                    return None
                    
        except Exception as e:
            self.logger.error(f"ERROR: Failed to get account balance: {str(e)}")
            return None

    async def get_account_info(self) -> Optional[Dict]:
        """Get account information from Binance"""
        try:
            if self.paper_trading:
                return {
                    'totalWalletBalance': str(self.config.TRADING_CONFIG['starting_capital']),
                    'availableBalance': str(self.config.TRADING_CONFIG['starting_capital']),
                    'totalMarginBalance': str(self.config.TRADING_CONFIG['starting_capital'])
                }
            
            endpoint = "/fapi/v2/account"
            params = {'timestamp': self._get_timestamp()}
            
            response = await self._signed_request('GET', endpoint, params)
            
            if response:
                return response
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"ERROR: Error getting account info: {e}")
            return None
    
    async def get_position_info(self, symbol: str) -> Optional[Dict]:
        """Get position information for a symbol"""
        try:
            if self.paper_trading:
                return None
            
            endpoint = "/fapi/v2/positionRisk"
            params = {
                'symbol': symbol,
                'timestamp': self._get_timestamp()
            }
            
            response = await self._signed_request('GET', endpoint, params)
            
            if response and isinstance(response, list) and len(response) > 0:
                return response[0]
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"ERROR: Error getting position info for {symbol}: {e}")
            return None
    
    async def _place_market_order(self, symbol: str, side: str, quantity: float, leverage: int) -> OrderResult:
        """Place a market order on Binance"""
        try:
            # Set leverage first
            await self._set_leverage(symbol, leverage)
            
            endpoint = "/fapi/v1/order"
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'MARKET',
                'quantity': str(quantity),
                'timestamp': self._get_timestamp()
            }
            
            response = await self._signed_request('POST', endpoint, params)
            
            if response and response.get('status') == 'FILLED':
                return OrderResult(
                    success=True,
                    order_id=str(response.get('orderId')),
                    filled_price=float(response.get('avgPrice', response.get('price', 0))),
                    filled_quantity=float(response.get('executedQty', 0)),
                    timestamp=datetime.now()
                )
            else:
                error_msg = response.get('msg', 'Unknown error') if response else 'No response'
                return OrderResult(False, error_message=error_msg)
                
        except Exception as e:
            self.logger.error(f"ERROR: Error placing market order: {e}")
            return OrderResult(False, error_message=str(e))
    
    async def _place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> OrderResult:
        """Place a limit order on Binance"""
        try:
            endpoint = "/fapi/v1/order"
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'LIMIT',
                'quantity': str(quantity),
                'price': str(price),
                'timeInForce': 'GTC',
                'timestamp': self._get_timestamp()
            }
            
            response = await self._signed_request('POST', endpoint, params)
            
            if response and response.get('orderId'):
                return OrderResult(
                    success=True,
                    order_id=str(response.get('orderId')),
                    filled_price=float(response.get('price', 0)),
                    filled_quantity=0.0,  # Limit orders start unfilled
                    timestamp=datetime.now()
                )
            else:
                error_msg = response.get('msg', 'Unknown error') if response else 'No response'
                return OrderResult(False, error_message=error_msg)
                
        except Exception as e:
            self.logger.error(f"ERROR: Error placing limit order: {e}")
            return OrderResult(False, error_message=str(e))
    
    async def _place_stop_order(self, symbol: str, side: str, quantity: float, stop_price: float) -> OrderResult:
        """Place a stop market order on Binance"""
        try:
            endpoint = "/fapi/v1/order"
            params = {
                'symbol': symbol,
                'side': side,
                'type': 'STOP_MARKET',
                'quantity': str(quantity),
                'stopPrice': str(stop_price),
                'timestamp': self._get_timestamp()
            }
            
            response = await self._signed_request('POST', endpoint, params)
            
            if response and response.get('orderId'):
                return OrderResult(
                    success=True,
                    order_id=str(response.get('orderId')),
                    timestamp=datetime.now()
                )
            else:
                error_msg = response.get('msg', 'Unknown error') if response else 'No response'
                return OrderResult(False, error_message=error_msg)
                
        except Exception as e:
            self.logger.error(f"ERROR: Error placing stop order: {e}")
            return OrderResult(False, error_message=str(e))
    
    async def _set_leverage(self, symbol: str, leverage: int) -> bool:
        """Set leverage for a symbol"""
        try:
            endpoint = "/fapi/v1/leverage"
            params = {
                'symbol': symbol,
                'leverage': leverage,
                'timestamp': self._get_timestamp()
            }
            
            response = await self._signed_request('POST', endpoint, params)
            return response is not None
            
        except Exception as e:
            self.logger.warning(f"WARNING: Error setting leverage for {symbol}: {e}")
            return False
    
    async def _cancel_binance_order(self, symbol: str, order_id: str) -> bool:
        """Cancel order on Binance"""
        try:
            endpoint = "/fapi/v1/order"
            params = {
                'symbol': symbol,
                'orderId': order_id,
                'timestamp': self._get_timestamp()
            }
            
            response = await self._signed_request('DELETE', endpoint, params)
            return response is not None
            
        except Exception as e:
            self.logger.error(f"ERROR: Error canceling order: {e}")
            return False
    
    async def _signed_request(self, method: str, endpoint: str, params: Dict) -> Optional[Dict]:
        """Make a signed request to Binance API"""
        try:
            if not self.session:
                return None
            
            # Add signature
            query_string = urlencode(params)
            signature = hmac.new(
                self.config.BINANCE_SECRET_KEY.encode('utf-8'),
                query_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            params['signature'] = signature
            
            # Prepare headers
            headers = {
                'X-MBX-APIKEY': self.config.BINANCE_API_KEY,
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            url = self.config.BINANCE_BASE_URL + endpoint
            
            # Rate limiting
            await self._rate_limit()
            
            # Make request
            if method == 'GET':
                async with self.session.get(url, params=params, headers=headers) as response:
                    return await self._handle_response(response)
            elif method == 'POST':
                async with self.session.post(url, data=params, headers=headers) as response:
                    return await self._handle_response(response)
            elif method == 'DELETE':
                async with self.session.delete(url, params=params, headers=headers) as response:
                    return await self._handle_response(response)
            
            return None
            
        except Exception as e:
            self.logger.error(f"ERROR: Error in signed request: {e}")
            return None
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Optional[Dict]:
        """Handle API response"""
        try:
            if response.status == 200:
                return await response.json()
            else:
                error_text = await response.text()
                self.logger.error(f"ERROR: API Error {response.status}: {error_text}")
                return None
                
        except Exception as e:
            self.logger.error(f"ERROR: Error handling response: {e}")
            return None
    
    async def _rate_limit(self):
        """Simple rate limiting to avoid API limits"""
        current_time = time.time()
        
        # Reset counter every minute
        if current_time - self.last_request_time > 60:
            self.request_count = 0
            self.last_request_time = current_time
        
        # Limit to 1000 requests per minute (safe buffer)
        if self.request_count >= 1000:
            wait_time = 60 - (current_time - self.last_request_time)
            if wait_time > 0:
                try:
                    await asyncio.sleep(wait_time)
                except asyncio.CancelledError:
                    # If cancelled during rate limiting, just continue
                    pass
                self.request_count = 0
                self.last_request_time = time.time()
        
        self.request_count += 1
    
    async def _round_quantity(self, symbol: str, quantity: float) -> float:
        """Round quantity to valid precision for the symbol"""
        try:
            # Simplified rounding - should get actual symbol info from exchange
            if 'BTC' in symbol:
                return round(quantity, 3)  # 3 decimal places for BTC
            else:
                return round(quantity, 2)  # 2 decimal places for most alts
                
        except Exception as e:
            self.logger.warning(f"WARNING: Error rounding quantity for {symbol}: {e}")
            return round(quantity, 3)  # Safe default
    
    def _get_timestamp(self) -> int:
        """Get current timestamp in milliseconds"""
        return int(time.time() * 1000)
    
    async def _simulate_order(self, signal: TradingSignal, side: str, quantity: float) -> OrderResult:
        """Simulate order execution for paper trading"""
        try:
            # Simulate small slippage
            slippage = 0.001  # 0.1% slippage
            if side == "BUY":
                filled_price = signal.entry_price * (1 + slippage)
            else:
                filled_price = signal.entry_price * (1 - slippage)
            
            order_id = f"PAPER_{signal.symbol}_{int(time.time())}"
            
            self.logger.info(f" Paper trade executed: {side} {quantity:.4f} {signal.symbol} @ ${filled_price:.4f}")
            
            return OrderResult(
                success=True,
                order_id=order_id,
                filled_price=filled_price,
                filled_quantity=quantity,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return OrderResult(False, error_message=str(e))
    
    async def _simulate_close(self, position: Position, quantity: float, reason: str) -> OrderResult:
        """Simulate position close for paper trading"""
        try:
            # Use current price with small slippage
            slippage = 0.001
            if position.side == "LONG":
                filled_price = position.current_price * (1 - slippage)
            else:
                filled_price = position.current_price * (1 + slippage)
            
            order_id = f"PAPER_CLOSE_{position.symbol}_{int(time.time())}"
            
            self.logger.info(f" Paper close executed: {quantity:.4f} {position.symbol} @ ${filled_price:.4f} ({reason})")
            
            return OrderResult(
                success=True,
                order_id=order_id,
                filled_price=filled_price,
                filled_quantity=quantity,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return OrderResult(False, error_message=str(e))
    
    async def close_session(self):
        """Close the aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def get_current_price(self, symbol: str) -> float:
        """Get current market price for a symbol"""
        try:
            if self.paper_trading:
                # For paper trading, get price from market data
                # This is a simplified approach - in reality you'd get live price
                import requests
                import asyncio
                
                # Use asyncio.to_thread for the synchronous request
                response = await asyncio.to_thread(
                    requests.get,
                    f"https://fapi.binance.com/fapi/v1/ticker/price",
                    params={"symbol": symbol},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return float(data['price'])
                else:
                    self.logger.error(f"Failed to get price for {symbol}")
                    return 0.0
            else:
                # For live trading, use the actual Binance API
                url = f"{self.base_url}/fapi/v1/ticker/price"
                params = {"symbol": symbol}
                
                async with self.session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data['price'])
                    else:
                        self.logger.error(f"Failed to get price for {symbol}: {response.status}")
                        return 0.0
                        
        except Exception as e:
            self.logger.error(f"Error getting current price for {symbol}: {e}")
            return 0.0

# Example usage
async def main():
    """Test order executor"""
    executor = OrderExecutor()
    
    try:
        # Start executor
        success = await executor.start_executor()
        
        if success:
            # Test account info
            account = await executor.get_account_info()
            if account:
                print(f"PROFIT: Account Balance: ${account.get('totalWalletBalance', 'N/A')}")
            
            # Test signal execution (paper trading)
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
            
            result = await executor.execute_signal(test_signal)
            print(f"Order result: {result}")
        
    except Exception as e:
        print(f"ERROR: Error: {e}")
    finally:
        await executor.close_session()

if __name__ == "__main__":
    asyncio.run(main())
