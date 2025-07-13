"""
Test the fixed initialization process
"""
import asyncio
import sys

async def test_initialization():
    """Test that initialization completes without hanging"""
    try:
        print("Testing component initialization...")
        
        # Test market scanner
        from market_scanner import MarketScanner
        scanner = MarketScanner()
        await scanner.start_scanner()
        print("✓ Market scanner initialized")
        
        # Test signal generator  
        from signal_generator import SignalGenerator
        generator = SignalGenerator()
        result = await generator.start_generator()
        print(f"✓ Signal generator initialized: {result}")
        
        # Test order executor
        from order_executor import OrderExecutor
        executor = OrderExecutor()
        await executor.start_executor()
        print("✓ Order executor initialized")
        
        print("\n🎉 All components initialized successfully!")
        print("The main engine should now continue to monitoring phase")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Testing TCAP v3 initialization fixes...")
    asyncio.run(test_initialization())
