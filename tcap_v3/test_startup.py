"""
Quick test of main engine startup
"""
import asyncio
from main_engine import TcapEngine

async def test_startup():
    engine = TcapEngine()
    print("Testing main engine startup...")
    
    try:
        # Test initialization only
        result = await engine._initialize_components()
        print(f"Initialization result: {result}")
        
        if result:
            print("✅ SUCCESS: Initialization completed without hanging!")
            print("Main engine should now continue to monitoring phase")
        else:
            print("❌ FAILED: Initialization failed")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_startup())
