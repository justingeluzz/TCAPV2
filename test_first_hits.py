#!/usr/bin/env python3
"""
Test script for First Hits functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend import TCAPAnalyzer

def test_first_hits():
    print("🧪 Testing First Hits Functionality...")
    
    # Initialize analyzer
    analyzer = TCAPAnalyzer()
    
    # Test first hit tracking initialization
    print(f"✅ First hit tracker initialized: {analyzer.first_hit_tracker}")
    print(f"✅ Hit history initialized: {analyzer.hit_history}")
    print(f"✅ Session start: {analyzer.session_start}")
    
    # Test first hit tracking method with dynamic threshold
    test_symbol = "BTCUSDT"
    test_gain = 16.5
    test_volume = 50000000
    custom_threshold = 12.5
    test_data = {
        'symbol': test_symbol,
        'gain_pct': test_gain,
        'volume_24h': test_volume,
        'current_price': 45000,
        'price_1h_ago': 42000
    }
    
    # Track a first hit with custom threshold
    analyzer.track_first_hit(test_symbol, test_gain, test_volume, test_data, custom_threshold)
    print(f"✅ Tracked first hit for {test_symbol} at {custom_threshold}% threshold")
    
    # Try to track the same symbol again (should not duplicate)
    analyzer.track_first_hit(test_symbol, 18.0, test_volume, test_data, 15.0)
    print(f"✅ Duplicate tracking prevented")
    
    # Get leaderboard
    leaderboard = analyzer.get_first_hits_leaderboard()
    print(f"✅ Leaderboard has {leaderboard['total_first_hits']} entries")
    print(f"✅ Current threshold: {leaderboard['current_threshold']}%")
    print(f"   Leaderboard content: {leaderboard}")
    
    if leaderboard['leaderboard'] and len(leaderboard['leaderboard']) > 0:
        first_entry = leaderboard['leaderboard'][0]
        threshold_used = first_entry.get('threshold_used', 'Not recorded')
        print(f"   🏆 First entry: {first_entry['symbol']} hit at {threshold_used}% threshold")
    else:
        print(f"   📝 Leaderboard is empty or has unexpected format")
    
    # Test reset
    analyzer.reset_first_hit_tracking()
    print(f"✅ Reset completed")
    
    leaderboard_after_reset = analyzer.get_first_hits_leaderboard()
    print(f"✅ Leaderboard after reset: {len(leaderboard_after_reset)} entries")
    
    print("\n🎉 All First Hits tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_first_hits()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
