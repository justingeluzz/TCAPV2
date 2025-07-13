"""
Quick test to verify shutdown handling fixes
"""
import asyncio
import signal
import sys

async def test_shutdown():
    print("Testing shutdown handling...")
    
    try:
        # Simulate the main loop
        counter = 0
        while True:
            print(f"Running... {counter}")
            counter += 1
            
            try:
                await asyncio.sleep(2)
            except asyncio.CancelledError:
                print("Sleep cancelled - shutting down gracefully")
                break
                
    except asyncio.CancelledError:
        print("Main task cancelled - shutting down gracefully")
    except KeyboardInterrupt:
        print("KeyboardInterrupt - shutting down gracefully")
    finally:
        print("Cleanup complete")

async def main():
    try:
        await test_shutdown()
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("Shutdown requested")
    finally:
        print("Main cleanup complete")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("System interrupted by user")
    finally:
        print("Test shutdown complete")
