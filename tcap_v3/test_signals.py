#!/usr/bin/env python3
"""Quick test for LONG signal generation"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from signal_generator import SignalGenerator
from config import TcapConfig

async def test_long_signals():
    """Test if LONG signals can be generated with current settings"""
    try:
        print("🔍 Testing LONG signal generation...")
        
        config = TcapConfig()
        generator = SignalGenerator()
        
        print(f"📊 Current LONG criteria:")
        print(f"   - Min 24h gain: {config.LONG_CRITERIA['price_gain_24h_min']}%")
        print(f"   - Min confidence: 15%")
        print(f"   - Min volume: ${config.LONG_CRITERIA['volume_24h_min']:,}")
        
        # First, let's see what the market scanner finds
        print(f"\n🔍 Testing market scanner...")
        market_data = await generator.market_scanner.scan_all_markets()
        print(f"📊 Market scanner found {len(market_data)} total pairs")
        
        if market_data:
            # Show top gainers
            gainers = [m for m in market_data if m.price_change_percent_24h > 0]
            gainers.sort(key=lambda x: x.price_change_percent_24h, reverse=True)
            
            print(f"📈 Top 5 gainers today:")
            for data in gainers[:5]:
                print(f"   {data.symbol}: +{data.price_change_percent_24h:.1f}% (Vol: ${data.volume_24h:,.0f})")
        
        signals = await generator.generate_signals()
        
        print(f"\n🎯 Results: {len(signals)} total signals")
        
        long_signals = [s for s in signals if s.side == "LONG"]
        short_signals = [s for s in signals if s.side == "SHORT"]
        
        print(f"   📈 LONG signals: {len(long_signals)}")
        print(f"   📉 SHORT signals: {len(short_signals)}")
        
        if long_signals:
            print(f"\n🚀 Top LONG signals:")
            for signal in long_signals[:5]:
                print(f"   {signal.symbol}: {signal.confidence:.1%} confidence")
                print(f"      Entry: ${signal.entry_price:.4f}")
                print(f"      TP1: ${signal.take_profit_1:.4f} (+1%)")
                print(f"      TP2: ${signal.take_profit_2:.4f} (+2%)")
        else:
            print("❌ No LONG signals found - will lower criteria even more")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_long_signals())
