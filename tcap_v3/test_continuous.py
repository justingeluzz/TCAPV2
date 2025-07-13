#!/usr/bin/env python3
"""
Test script to demonstrate TCAP v3 continuous monitoring
"""

import asyncio
import sys
import os

# Add the tcap_v3 directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main_engine import TcapEngine

async def test_continuous_monitoring():
    """Test the continuous monitoring for a short period"""
    print("START: Testing TCAP v3 Continuous Monitoring")
    print("=" * 50)
    
    engine = TcapEngine()
    
    try:
        # Start the trading system
        await engine.start_trading()
        
    except KeyboardInterrupt:
        print("\n[STOP] Test stopped by user")
    except Exception as e:
        print(f"ERROR: Error during test: {e}")
    finally:
        await engine.stop_trading()
        print("SUCCESS: Test completed")

if __name__ == "__main__":
    print("Starting TCAP v3 continuous monitoring test...")
    print("This will run continuously. Press Ctrl+C to stop.")
    asyncio.run(test_continuous_monitoring())
