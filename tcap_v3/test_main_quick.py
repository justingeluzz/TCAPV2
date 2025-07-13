"""
Quick main engine test to verify balance fix
"""
import asyncio
import sys

async def test_main_engine():
    """Test main engine initialization"""
    try:
        # Import and create engine
        from main_engine import TcapEngine
        
        engine = TcapEngine()
        print("✓ Main engine created successfully")
        
        # Test component initialization (partial)
        print("Testing component initialization...")
        
        # Initialize order executor and test balance
        await engine.order_executor.start_executor()
        balance = await engine.order_executor.get_account_balance()
        print(f"✓ Account balance: ${balance:.2f}")
        
        # Initialize other components
        await engine.market_scanner.start_scanner()
        print("✓ Market scanner started")
        
        # Stop components cleanly
        await engine.market_scanner.stop_scanner()
        print("✓ Components stopped cleanly")
        
        print("\n🎉 MAIN ENGINE TEST PASSED!")
        print("The balance error has been fixed!")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_main_engine())
