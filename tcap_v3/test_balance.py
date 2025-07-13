"""
Test script to verify get_account_balance method works
"""
import asyncio
from order_executor import OrderExecutor

async def test_balance():
    executor = OrderExecutor()
    await executor.start_executor()
    balance = await executor.get_account_balance()
    print(f"Account balance: ${balance:.2f}")

if __name__ == "__main__":
    asyncio.run(test_balance())
