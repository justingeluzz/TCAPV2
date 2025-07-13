# TCAP v2 - Python Backend for Binance API Integration
# Run this server to provide API endpoints for the frontend

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import time
import logging
from datetime import datetime
import json
import threading
from threading import Timer

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BinanceAPI:
    def __init__(self):
        self.base_url = "https://fapi.binance.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TCAP-v2/1.0',
            'Content-Type': 'application/json'
        })
    
    def get_exchange_info(self):
        """Get all futures trading pairs"""
        try:
            response = self.session.get(f"{self.base_url}/fapi/v1/exchangeInfo")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching exchange info: {e}")
            raise
    
    def get_klines(self, symbol, interval="1h", limit=2):
        """Get kline/candlestick data for a symbol"""
        try:
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            response = self.session.get(f"{self.base_url}/fapi/v1/klines", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching klines for {symbol}: {e}")
            return None
    
    def get_24hr_ticker(self, symbol):
        """Get 24hr ticker statistics for a symbol"""
        try:
            params = {'symbol': symbol}
            response = self.session.get(f"{self.base_url}/fapi/v1/ticker/24hr", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Error fetching 24hr ticker for {symbol}: {e}")
            return None

class TCAPAnalyzer:
    def __init__(self):
        self.binance = BinanceAPI()
        self.cache = {}
        self.cache_timeout = 30  # Cache for 30 seconds for faster updates
        self.continuous_update = True
        self.update_thread = None
        self.latest_data = []
        # Dynamic filter parameters (can be updated by frontend)
        self.current_min_gain = 3.0  # Default 3% (matches typical frontend default)
        self.current_min_volume = 1  # Default $1M
        # First hit tracking
        self.first_hit_tracker = {}  # Track first hits
        self.hit_history = []        # Store chronological hits
        self.session_start = datetime.now()
        self.server_startup_time = datetime.now()  # Track when server was started
        logger.info(f"🎯 TCAPAnalyzer initialized with default filters: min_gain={self.current_min_gain}%, min_volume=${self.current_min_volume}M")
        self.start_continuous_monitoring()
    
    def start_continuous_monitoring(self):
        """Start continuous background monitoring"""
        logger.info("🔄 Starting continuous monitoring...")
        # Delay initial start by 5 seconds to allow frontend to sync filters
        self.update_thread = Timer(5.0, self.continuous_update_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
    
    def continuous_update_loop(self):
        """Continuously update data in background"""
        if self.continuous_update:
            try:
                logger.info("🔄 Auto-updating crypto data...")
                # Use current dynamic parameters for continuous monitoring
                self.latest_data = self.get_top_movers(
                    min_gain=self.current_min_gain, 
                    min_volume_millions=self.current_min_volume, 
                    max_symbols=100
                )
                logger.info(f"✅ Updated: {len(self.latest_data)} pairs analyzed (min_gain: {self.current_min_gain}%, min_volume: ${self.current_min_volume}M)")
            except Exception as e:
                logger.error(f"❌ Error in continuous update: {e}")
            
            # Schedule next update in 30 seconds
            if self.continuous_update:
                self.update_thread = Timer(30.0, self.continuous_update_loop)
                self.update_thread.daemon = True
                self.update_thread.start()
    
    def update_filter_parameters(self, min_gain=None, min_volume=None):
        """Update the dynamic filter parameters used for continuous monitoring"""
        old_min_gain = self.current_min_gain
        old_min_volume = self.current_min_volume
        
        if min_gain is not None:
            self.current_min_gain = float(min_gain)
        if min_volume is not None:
            self.current_min_volume = float(min_volume)
        
        logger.info(f"� Frontend sync: min_gain={old_min_gain}% → {self.current_min_gain}%, min_volume=${old_min_volume}M → ${self.current_min_volume}M")
        
        # Auto-reset first hits if threshold changed significantly (more than 0.5%)
        if min_gain is not None and abs(old_min_gain - self.current_min_gain) > 0.5:
            logger.info(f"🔄 Threshold changed significantly ({old_min_gain}% → {self.current_min_gain}%), resetting first hits tracking")
            self.reset_first_hit_tracking()
        
        # Clear cache to force refresh with new parameters
        cache_keys_to_clear = [key for key in self.cache.keys() if key.startswith('top_movers_')]
        for key in cache_keys_to_clear:
            del self.cache[key]
    
    def track_first_hit(self, symbol, gain_percent, volume, price_data, threshold_used=None):
        """Track when a coin first hits the current filter criteria"""
        hit_time = datetime.now()
        threshold = threshold_used or self.current_min_gain
        
        # Only track if this symbol hasn't been recorded yet in this session
        # AND the gain meets the specified threshold
        if (symbol not in self.first_hit_tracker and 
            gain_percent >= threshold):
            
            hit_data = {
                'symbol': symbol,
                'first_hit_time': hit_time,
                'first_hit_gain': gain_percent,
                'volume': volume,
                'current_price': price_data['current_price'],
                'price_1h_ago': price_data['price_1h_ago'],
                'threshold_used': threshold,  # Record the exact threshold used
                'minutes_since_session_start': (hit_time - self.session_start).total_seconds() / 60,
                'is_new_hit': True
            }
            
            self.first_hit_tracker[symbol] = hit_data
            self.hit_history.append(hit_data)
            
            # Sort hit history by time (chronological order, oldest first for true "first to hit")
            self.hit_history.sort(key=lambda x: x['first_hit_time'])
            
            logger.info(f"🎯 NEW FIRST HIT #{len(self.hit_history)}: {symbol} reached {gain_percent:.2f}% (threshold: {threshold}%) at {hit_time.strftime('%H:%M:%S')}")
            
            return True  # New first hit
        else:
            # Update existing data but don't mark as new
            self.first_hit_tracker[symbol].update({
                'current_gain': gain_percent,
                'current_price': price_data['current_price'],
                'is_new_hit': False
            })
            return False  # Already tracked
    
    def get_first_hits_leaderboard(self, limit=20):
        """Get the first hits leaderboard"""
        return {
            'session_start': self.session_start.isoformat(),
            'total_first_hits': len(self.first_hit_tracker),
            'current_threshold': self.current_min_gain,  # Include current threshold
            'current_volume_threshold': self.current_min_volume,  # Include volume threshold
            'leaderboard': self.hit_history[:limit],
            'currently_active': [
                hit for hit in self.hit_history[:limit] 
                if hit['symbol'] in [item['symbol'] for item in self.latest_data]
            ]
        }
    
    def reset_first_hit_tracking(self):
        """Reset first hit tracking (new session)"""
        self.first_hit_tracker.clear()
        self.hit_history.clear()
        self.session_start = datetime.now()
        logger.info("🔄 First hit tracking reset - new session started")

    def stop_continuous_monitoring(self):
        """Stop continuous monitoring"""
        self.continuous_update = False
        if self.update_thread:
            self.update_thread.cancel()
    
    def get_usdt_futures_pairs(self):
        """Step 1: Get all USDT futures pairs"""
        cache_key = "usdt_pairs"
        now = time.time()
        
        if cache_key in self.cache and (now - self.cache[cache_key]['timestamp']) < 3600:  # Cache for 1 hour
            return self.cache[cache_key]['data']
        
        try:
            exchange_info = self.binance.get_exchange_info()
            usdt_pairs = [
                symbol['symbol'] for symbol in exchange_info['symbols']
                if (symbol['symbol'].endswith('USDT') and 
                    symbol['contractType'] == 'PERPETUAL' and
                    symbol['status'] == 'TRADING')
            ]
            
            self.cache[cache_key] = {
                'data': usdt_pairs,
                'timestamp': now
            }
            
            logger.info(f"Found {len(usdt_pairs)} USDT perpetual pairs")
            return usdt_pairs
            
        except Exception as e:
            logger.error(f"Error getting USDT pairs: {e}")
            return []
    
    def analyze_symbol(self, symbol):
        """Analyze a single symbol for price movement and volume"""
        try:
            # Step 2: Get price data (1 hour ago vs current)
            klines = self.binance.get_klines(symbol, "1h", 2)
            if not klines or len(klines) < 2:
                return None
            
            # Step 3: Get 24h volume data
            ticker_24hr = self.binance.get_24hr_ticker(symbol)
            if not ticker_24hr:
                return None
            
            # Calculate 1-hour gain
            previous_candle = klines[0]  # 1 hour ago
            current_candle = klines[1]   # Current/latest
            
            price_1h_ago = float(previous_candle[1])  # Open price of previous candle
            current_price = float(current_candle[4])  # Close price of current candle
            volume_24h = float(ticker_24hr['quoteVolume'])
            
            # Calculate percentage gain
            if price_1h_ago > 0:
                gain_pct = ((current_price - price_1h_ago) / price_1h_ago) * 100
            else:
                gain_pct = 0
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'price_1h_ago': price_1h_ago,
                'gain_pct': round(gain_pct, 2),
                'volume_24h': volume_24h,
                'timestamp': int(time.time() * 1000)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            return None
    
    def get_top_movers(self, min_gain=1, min_volume_millions=1, max_symbols=50):
        """Get top moving cryptocurrencies based on criteria"""
        cache_key = f"top_movers_{min_gain}_{min_volume_millions}"
        now = time.time()
        
        # For continuous monitoring, use shorter cache timeout
        cache_timeout = 15 if self.continuous_update else self.cache_timeout
        
        # Check cache
        if cache_key in self.cache and (now - self.cache[cache_key]['timestamp']) < cache_timeout:
            logger.info(f"📋 Returning cached data ({len(self.cache[cache_key]['data'])} pairs)")
            return self.cache[cache_key]['data']
        
        # Get all USDT pairs
        usdt_pairs = self.get_usdt_futures_pairs()
        if not usdt_pairs:
            return []
        
        # For continuous monitoring, process more pairs but with intelligent batching
        if self.continuous_update:
            max_symbols = min(max_symbols, 75)  # Process more pairs for better coverage
        else:
            max_symbols = min(max_symbols, 50)
        
        # Limit to prevent API rate limiting
        usdt_pairs = usdt_pairs[:max_symbols]
        
        results = []
        min_volume = min_volume_millions * 1_000_000  # Convert to actual volume
        
        logger.info(f"🔍 Analyzing {len(usdt_pairs)} symbols (continuous: {self.continuous_update})...")
        
        for i, symbol in enumerate(usdt_pairs):
            try:
                analysis = self.analyze_symbol(symbol)
                if analysis:
                    # Step 4: Filter based on conditions
                    if (analysis['gain_pct'] >= min_gain and 
                        analysis['volume_24h'] >= min_volume):
                        results.append(analysis)
                        
                        # Track first hits for new potential coins
                        if self.continuous_update:
                            self.track_first_hit(analysis['symbol'], analysis['gain_pct'], analysis['volume_24h'], analysis, min_gain)
                
                # Adaptive delay based on monitoring mode
                if i % 15 == 0:  # Reduced batch size for more frequent updates
                    delay = 0.05 if self.continuous_update else 0.1
                    time.sleep(delay)
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue
        
        # Step 5: Sort by gain percentage (descending)
        results.sort(key=lambda x: x['gain_pct'], reverse=True)
        
        # Cache results
        self.cache[cache_key] = {
            'data': results,
            'timestamp': now
        }
        
        logger.info(f"Found {len(results)} coins meeting criteria")
        return results

# Initialize analyzer
analyzer = TCAPAnalyzer()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'server_startup_time': analyzer.server_startup_time.isoformat(),
        'session_start_time': analyzer.session_start.isoformat(),
        'service': 'TCAP v2 API'
    })

@app.route('/api/pairs', methods=['GET'])
def get_pairs():
    """Get all USDT futures pairs"""
    try:
        pairs = analyzer.get_usdt_futures_pairs()
        return jsonify({
            'pairs': pairs,
            'count': len(pairs),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze/<symbol>', methods=['GET'])
def analyze_symbol(symbol):
    """Analyze a specific symbol"""
    try:
        result = analyzer.analyze_symbol(symbol.upper())
        if result:
            return jsonify(result)
        else:
            return jsonify({'error': 'Symbol not found or analysis failed'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/status', methods=['GET'])
def get_monitoring_status():
    """Get continuous monitoring status"""
    return jsonify({
        'continuous_monitoring': analyzer.continuous_update,
        'cache_timeout': analyzer.cache_timeout,
        'latest_data_count': len(analyzer.latest_data),
        'last_update': datetime.now().isoformat()
    })

@app.route('/api/monitoring/start', methods=['POST'])
def start_monitoring():
    """Start continuous monitoring"""
    if not analyzer.continuous_update:
        analyzer.continuous_update = True
        analyzer.start_continuous_monitoring()
        return jsonify({'status': 'started', 'message': 'Continuous monitoring started'})
    return jsonify({'status': 'already_running', 'message': 'Monitoring already active'})

@app.route('/api/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """Stop continuous monitoring"""
    analyzer.stop_continuous_monitoring()
    return jsonify({'status': 'stopped', 'message': 'Continuous monitoring stopped'})

@app.route('/api/monitoring/filters', methods=['POST'])
def update_monitoring_filters():
    """Update the filter parameters for continuous monitoring"""
    try:
        data = request.get_json() or {}
        min_gain = data.get('min_gain')
        min_volume = data.get('min_volume')
        
        # Update the analyzer's filter parameters
        analyzer.update_filter_parameters(min_gain=min_gain, min_volume=min_volume)
        
        return jsonify({
            'status': 'updated',
            'message': 'Filter parameters updated successfully',
            'current_filters': {
                'min_gain': analyzer.current_min_gain,
                'min_volume': analyzer.current_min_volume
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitoring/filters', methods=['GET'])
def get_monitoring_filters():
    """Get current filter parameters"""
    return jsonify({
        'current_filters': {
            'min_gain': analyzer.current_min_gain,
            'min_volume': analyzer.current_min_volume
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/live-data', methods=['GET'])
def get_live_data():
    """Get the latest continuously monitored data"""
    min_gain = float(request.args.get('min_gain', analyzer.current_min_gain))
    min_volume = float(request.args.get('min_volume', analyzer.current_min_volume))
    
    # Update analyzer's filter parameters if they changed
    if min_gain != analyzer.current_min_gain or min_volume != analyzer.current_min_volume:
        analyzer.update_filter_parameters(min_gain=min_gain, min_volume=min_volume)
    
    # Filter the latest data based on current criteria
    filtered_data = [
        item for item in analyzer.latest_data
        if (item['gain_pct'] >= min_gain and 
            (item['volume_24h'] / 1_000_000) >= min_volume)
    ]
    
    # Sort by gain percentage
    filtered_data.sort(key=lambda x: x['gain_pct'], reverse=True)
    
    return jsonify({
        'data': filtered_data,
        'count': len(filtered_data),
        'total_monitored': len(analyzer.latest_data),
        'continuous_monitoring': analyzer.continuous_update,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/top-movers', methods=['GET'])
def get_top_movers():
    """Get top moving cryptocurrencies"""
    try:
        # Get query parameters
        min_gain = float(request.args.get('min_gain', 10))
        min_volume = float(request.args.get('min_volume', 10))
        max_results = int(request.args.get('max_results', 50))
        
        results = analyzer.get_top_movers(
            min_gain=min_gain,
            min_volume_millions=min_volume,
            max_symbols=max_results
        )
        
        return jsonify({
            'data': results,
            'count': len(results),
            'filters': {
                'min_gain_pct': min_gain,
                'min_volume_millions': min_volume,
                'max_results': max_results
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in top-movers endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/<format>', methods=['GET'])
def export_data(format):
    """Export data in CSV or JSON format"""
    try:
        min_gain = float(request.args.get('min_gain', 10))
        min_volume = float(request.args.get('min_volume', 10))
        
        results = analyzer.get_top_movers(
            min_gain=min_gain,
            min_volume_millions=min_volume
        )
        
        if format.lower() == 'csv':
            # Return CSV format instructions
            return jsonify({
                'format': 'csv',
                'headers': ['Symbol', '1h Ago Price', 'Current Price', '% Gain', '24h Volume'],
                'data': results,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({
                'format': 'json',
                'data': results,
                'timestamp': datetime.now().isoformat()
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/first-hits', methods=['GET'])
def get_first_hits():
    """Get the first hits leaderboard"""
    try:
        leaderboard = analyzer.get_first_hits_leaderboard()
        return jsonify({
            'success': True,
            'data': leaderboard,
            'timestamp': datetime.now().isoformat(),
            'session_start': analyzer.session_start.isoformat() if analyzer.session_start else None
        })
    except Exception as e:
        logger.error(f"Error in first-hits endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/first-hits/reset', methods=['POST'])
def reset_first_hits():
    """Reset the first hits tracking"""
    try:
        analyzer.reset_first_hit_tracking()
        return jsonify({
            'success': True,
            'message': 'First hits tracking has been reset',
            'timestamp': datetime.now().isoformat(),
            'session_start': analyzer.session_start.isoformat()
        })
    except Exception as e:
        logger.error(f"Error resetting first-hits: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting TCAP v2 Backend Server...")
    print("🔄 CONTINUOUS MONITORING MODE ENABLED")
    print("🎯 DYNAMIC FILTER SUPPORT ENABLED")
    print("📊 Endpoints available:")
    print("   - GET /api/health - Health check")
    print("   - GET /api/pairs - Get all USDT futures pairs")
    print("   - GET /api/analyze/<symbol> - Analyze specific symbol")
    print("   - GET /api/top-movers - Get top moving cryptocurrencies")
    print("   - GET /api/live-data - Get continuously monitored live data")
    print("   - GET /api/monitoring/status - Get monitoring status")
    print("   - POST /api/monitoring/start - Start continuous monitoring")
    print("   - POST /api/monitoring/stop - Stop continuous monitoring")
    print("   - GET /api/monitoring/filters - Get current filter parameters")
    print("   - POST /api/monitoring/filters - Update filter parameters")
    print("   - GET /api/export/<format> - Export data")
    print("   - GET /api/first-hits - Get first hits leaderboard")
    print("   - POST /api/first-hits/reset - Reset first hits tracking")
    print("   - GET /api/first-hits - Get first hits leaderboard")
    print("   - POST /api/first-hits/reset - Reset first hits tracking")
    print("\n💡 Continuous Features:")
    print("   ✅ Auto-updates every 30 seconds")
    print("   ✅ Real-time data caching")
    print("   ✅ Background monitoring")
    print("   ✅ Live API endpoints")
    print("   ✅ Dynamic filter parameters")
    print("   ✅ Frontend-backend filter synchronization")
    print("   🎯 First Hit Tracking - 'First to Hit 15%' feature")
    print(f"\n🎯 Current Filter Defaults:")
    print(f"   📈 Min Gain: {analyzer.current_min_gain}%")
    print(f"   💰 Min Volume: ${analyzer.current_min_volume}M")
    print("\n🌐 Frontend should connect to: http://localhost:5000")
    print("📈 Live monitoring starts automatically!")
    print("🔄 Filters will update dynamically from frontend!")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
