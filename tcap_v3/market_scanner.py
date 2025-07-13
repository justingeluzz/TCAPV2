"""
TCAP v3 Market Scanner
Monitors 200+ Binance USDT futures pairs for trading opportunities
"""

import asyncio
import requests
import time
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

from config import TcapConfig

@dataclass
class MarketData:
    """Market data structure for each trading pair"""
    symbol: str
    price: float
    price_change_24h: float
    price_change_percent_24h: float
    price_change_1h: float
    price_change_percent_1h: float
    volume_24h: float
    volume_usdt_24h: float
    high_24h: float
    low_24h: float
    open_24h: float
    market_cap: Optional[float] = None
    avg_volume_20d: Optional[float] = None
    volume_ratio: float = 1.0  # Added: volume ratio vs average
    current_price: float = 0.0  # Added: current price alias
    pullback_from_high: float = 0.0  # Added: pullback percentage
    last_updated: datetime = None

class MarketScanner:
    """
    TCAP v3 Market Scanner
    Continuously monitors Binance futures markets for trading opportunities
    """
    
    def __init__(self):
        self.config = TcapConfig()
        self.session: Optional[requests.Session] = None
        self.is_running = False
        self.scan_count = 0
        self.last_scan_time = None
        self.market_data: Dict[str, MarketData] = {}
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    async def start_scanner(self):
        """Initialize the market scanner"""
        self.logger.info("Starting TCAP v3 Market Scanner...")
        self.is_running = True
        
        # Create requests session (thread-safe)
        self.session = requests.Session()
        
        try:
            # Run one initial scan
            await self.scan_all_markets()
            self.logger.info("Market scanner initialized successfully")
            
        except Exception as e:
            self.logger.error(f"ERROR: Scanner initialization error: {e}")
            if self.session:
                self.session.close()
                
    async def run_scanning_loop(self):
        """Run the continuous market scanning loop"""
        try:
            while self.is_running:
                await self.scan_all_markets()
                try:
                    await asyncio.sleep(self.config.SCANNING_CONFIG['scan_interval'])
                except asyncio.CancelledError:
                    self.logger.info("Market scanner sleep cancelled - shutting down")
                    break
        except asyncio.CancelledError:
            self.logger.info("Market scanner cancelled - shutting down gracefully")
        except Exception as e:
            self.logger.error(f"ERROR: Scanner error: {e}")
        finally:
            if self.session:
                await self.session.close()
    
    async def stop_scanner(self):
        """Stop the market scanner"""
        self.logger.info("STOP: Stopping market scanner...")
        self.is_running = False
        await self._reset_session()
    
    async def scan_all_markets(self):
        """Scan all USDT futures pairs for opportunities"""
        try:
            start_time = time.time()
            self.logger.info(f"Starting market scan #{self.scan_count + 1}")
            
            # Get all USDT futures pairs
            pairs = await self.get_futures_pairs()
            if not pairs:
                self.logger.warning("WARNING: No pairs retrieved")
                return
            
            # Get 24hr ticker data for all pairs
            ticker_data = await self.get_24hr_ticker_data()
            if not ticker_data:
                self.logger.warning("WARNING: No ticker data retrieved")
                return
            
            # Process market data
            candidates = []
            for ticker in ticker_data:
                if ticker['symbol'].endswith('USDT'):
                    market_data = self.process_ticker_data(ticker)
                    if market_data:
                        self.market_data[market_data.symbol] = market_data
                        
                        # Apply basic filters
                        if self.passes_basic_filters(market_data):
                            candidates.append(market_data)
            
            # Log scan results
            scan_time = time.time() - start_time
            self.scan_count += 1
            self.last_scan_time = datetime.now()
            
            self.logger.info(f"Scan #{self.scan_count} completed in {scan_time:.2f}s")
            self.logger.info(f"Scanned {len(self.market_data)} pairs, {len(candidates)} candidates found")
            
            # Log top candidates
            if candidates:
                top_candidates = sorted(candidates, key=lambda x: x.price_change_percent_24h, reverse=True)[:5]
                self.logger.info("Top candidates:")
                for i, candidate in enumerate(top_candidates, 1):
                    self.logger.info(f"   {i}. {candidate.symbol}: +{candidate.price_change_percent_24h:.1f}% "
                                   f"(Vol: ${candidate.volume_usdt_24h/1_000_000:.1f}M)")
            
            return candidates
            
        except Exception as e:
            self.logger.error(f"ERROR: Error in scan_all_markets: {e}")
            return []
    
    async def get_futures_pairs(self) -> List[str]:
        """Get all active USDT futures trading pairs"""
        try:
            # Ensure we have a valid session for the current event loop
            await self._ensure_session()
            
            url = f"{self.config.BINANCE_BASE_URL}/fapi/v1/exchangeInfo"
            
            # Use asyncio.to_thread to run sync request in thread pool
            response = await asyncio.to_thread(self.session.get, url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                pairs = []
                
                for symbol_info in data['symbols']:
                    if (symbol_info['status'] == 'TRADING' and 
                        symbol_info['symbol'].endswith('USDT') and
                        symbol_info['contractType'] == 'PERPETUAL'):
                        pairs.append(symbol_info['symbol'])
                
                self.logger.info(f"Found {len(pairs)} active USDT futures pairs")
                return pairs
            else:
                self.logger.error(f"ERROR: Failed to get exchange info: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"ERROR: Error getting futures pairs: {e}")
            # Reset session on error
            await self._reset_session()
            return []
    
    async def get_24hr_ticker_data(self) -> List[Dict]:
        """Get 24hr ticker statistics for all symbols"""
        try:
            # Ensure we have a valid session for the current event loop
            await self._ensure_session()
            
            url = f"{self.config.BINANCE_BASE_URL}/fapi/v1/ticker/24hr"
            
            # Use asyncio.to_thread to run sync request in thread pool
            response = await asyncio.to_thread(self.session.get, url, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"Retrieved ticker data for {len(data)} symbols")
                return data
            else:
                self.logger.error(f"ERROR: Failed to get ticker data: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"ERROR: Error getting ticker data: {e}")
            # Reset session on error
            await self._reset_session()
            return []
    
    def process_ticker_data(self, ticker: Dict) -> Optional[MarketData]:
        """Process raw ticker data into MarketData object"""
        try:
            symbol = ticker['symbol']
            
            # Skip if not USDT pair
            if not symbol.endswith('USDT'):
                return None
            
            return MarketData(
                symbol=symbol,
                price=float(ticker['lastPrice']),
                price_change_24h=float(ticker['priceChange']),
                price_change_percent_24h=float(ticker['priceChangePercent']),
                price_change_1h=0.0,  # Will be calculated separately
                price_change_percent_1h=0.0,  # Will be calculated separately
                volume_24h=float(ticker['volume']),
                volume_usdt_24h=float(ticker['quoteVolume']),
                high_24h=float(ticker['highPrice']),
                low_24h=float(ticker['lowPrice']),
                open_24h=float(ticker['openPrice']),
                last_updated=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"ERROR: Error processing ticker for {ticker.get('symbol', 'unknown')}: {e}")
            return None
    
    def passes_basic_filters(self, market_data: MarketData) -> bool:
        """Apply basic filters to identify potential candidates"""
        try:
            criteria = self.config.LONG_CRITERIA
            
            # Price gain filter (15-40% for long trades)
            if not (criteria['price_gain_24h_min'] <= market_data.price_change_percent_24h <= criteria['price_gain_24h_max']):
                return False
            
            # Volume filter (minimum $5M 24hr volume)
            if market_data.volume_usdt_24h < criteria['volume_24h_min']:
                return False
            
            # Exclude stablecoins and weird pairs
            excluded_tokens = ['USDC', 'BUSD', 'TUSD', 'USDP', 'FDUSD', 'UP', 'DOWN', 'BEAR', 'BULL']
            for excluded in excluded_tokens:
                if excluded in market_data.symbol:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"ERROR: Error in basic filters for {market_data.symbol}: {e}")
            return False
    
    def get_top_gainers(self, limit: int = 20) -> List[MarketData]:
        """Get top gaining pairs from latest scan"""
        try:
            filtered_data = [data for data in self.market_data.values() 
                           if self.passes_basic_filters(data)]
            
            return sorted(filtered_data, 
                         key=lambda x: x.price_change_percent_24h, 
                         reverse=True)[:limit]
        except Exception as e:
            self.logger.error(f"ERROR: Error getting top gainers: {e}")
            return []
    
    def get_scanner_stats(self) -> Dict:
        """Get scanner statistics"""
        return {
            'is_running': self.is_running,
            'scan_count': self.scan_count,
            'last_scan_time': self.last_scan_time,
            'total_pairs': len(self.market_data),
            'candidates_count': len([data for data in self.market_data.values() 
                                   if self.passes_basic_filters(data)])
        }
    
    def get_latest_candidates(self) -> List[MarketData]:
        """Get latest candidates from the most recent scan (non-async version)"""
        try:
            candidates = []
            for market_data in self.market_data.values():
                if self.passes_basic_filters(market_data):
                    candidates.append(market_data)
            
            # Sort by 24h price change percentage (descending)
            candidates.sort(key=lambda x: x.price_change_percent_24h, reverse=True)
            
            if candidates:
                self.logger.info(f"Retrieved {len(candidates)} latest candidates")
            else:
                self.logger.warning("No candidates found - market data may be empty")
            return candidates
            
        except Exception as e:
            self.logger.error(f"ERROR: Error getting latest candidates: {e}")
            return []
    
    async def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get current prices for specified symbols"""
        try:
            if not symbols:
                return {}
            
            # Use ticker/price endpoint for current prices
            url = f"{self.config.BINANCE_BASE_URL}/fapi/v1/ticker/price"
            
            if not self.session:
                self.session = requests.Session()
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                all_prices = response.json()
                
                # Create a dictionary for quick lookup
                price_dict = {}
                for item in all_prices:
                    if item['symbol'] in symbols:
                        price_dict[item['symbol']] = float(item['price'])
                
                self.logger.debug(f"Retrieved prices for {len(price_dict)} symbols")
                return price_dict
            else:
                self.logger.error(f"Failed to get current prices: {response.status_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error getting current prices: {e}")
            return {}

    def get_current_price(self, symbol: str) -> float:
        """Get current price for a single symbol"""
        try:
            if symbol in self.market_data:
                return self.market_data[symbol].price
            
            # Fallback to API call
            url = f"{self.config.BINANCE_BASE_URL}/fapi/v1/ticker/price"
            params = {'symbol': symbol}
            
            if not self.session:
                self.session = requests.Session()
            
            response = self.session.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return float(data['price'])
            else:
                self.logger.error(f"Failed to get price for {symbol}: {response.status_code}")
                return 0.0
                
        except Exception as e:
            self.logger.error(f"Error getting price for {symbol}: {e}")
            return 0.0
    
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

    async def get_current_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Get current prices for symbols"""
        price_dict = {}
        for symbol in symbols:
            if symbol in self.market_data:
                price_dict[symbol] = self.market_data[symbol].price
            else:
                price_dict[symbol] = 50000.0  # Default price
        return price_dict

# Example usage for testing
async def main():
    """Test the market scanner"""
    scanner = MarketScanner()
    
    try:
        # Run a single scan
        candidates = await scanner.scan_all_markets()
        
        if candidates:
            print(f"\nTARGET: Found {len(candidates)} candidates:")
            for candidate in candidates[:10]:  # Show top 10
                print(f"   {candidate.symbol}: +{candidate.price_change_percent_24h:.1f}% "
                      f"(${candidate.volume_usdt_24h/1_000_000:.1f}M volume)")
        
        # Get scanner stats
        stats = scanner.get_scanner_stats()
        print(f"\nSTATS: Scanner Stats: {stats}")
        
    except Exception as e:
        print(f"ERROR: Error: {e}")
    finally:
        await scanner.stop_scanner()

if __name__ == "__main__":
    asyncio.run(main())
