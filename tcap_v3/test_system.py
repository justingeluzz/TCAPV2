"""
TCAP v3 Comprehensive Error Check
Tests all major components for errors and functionality
"""
import asyncio
import sys
import traceback
from datetime import datetime

async def test_imports():
    """Test all module imports"""
    print("Testing imports...")
    try:
        from config import TcapConfig
        from market_scanner import MarketScanner
        from technical_analyzer import TechnicalAnalyzer
        from signal_generator import SignalGenerator
        from order_executor import OrderExecutor
        from risk_manager import RiskManager
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

async def test_config():
    """Test configuration loading"""
    print("Testing configuration...")
    try:
        from config import TcapConfig
        config = TcapConfig()
        starting_capital = config.TRADING_CONFIG['starting_capital']
        print(f"✓ Config loaded successfully - Starting capital: ${starting_capital}")
        return True
    except Exception as e:
        print(f"✗ Config error: {e}")
        return False

async def test_order_executor():
    """Test OrderExecutor balance method"""
    print("Testing OrderExecutor balance...")
    try:
        from order_executor import OrderExecutor
        executor = OrderExecutor()
        await executor.start_executor()
        balance = await executor.get_account_balance()
        print(f"✓ OrderExecutor balance: ${balance:.2f}")
        return True
    except Exception as e:
        print(f"✗ OrderExecutor error: {e}")
        return False

async def test_market_scanner():
    """Test MarketScanner initialization"""
    print("Testing MarketScanner...")
    try:
        from market_scanner import MarketScanner
        scanner = MarketScanner()
        print("✓ MarketScanner initialized successfully")
        return True
    except Exception as e:
        print(f"✗ MarketScanner error: {e}")
        return False

async def test_signal_generator():
    """Test SignalGenerator initialization"""
    print("Testing SignalGenerator...")
    try:
        from signal_generator import SignalGenerator
        generator = SignalGenerator()
        print("✓ SignalGenerator initialized successfully")
        return True
    except Exception as e:
        print(f"✗ SignalGenerator error: {e}")
        return False

async def test_risk_manager():
    """Test RiskManager initialization"""
    print("Testing RiskManager...")
    try:
        from risk_manager import RiskManager
        risk_mgr = RiskManager()
        print("✓ RiskManager initialized successfully")
        return True
    except Exception as e:
        print(f"✗ RiskManager error: {e}")
        return False

async def main():
    """Run all tests"""
    print("=" * 60)
    print("TCAP v3 Comprehensive Error Check")
    print("=" * 60)
    print(f"Test started at: {datetime.now()}")
    print()
    
    tests = [
        test_imports,
        test_config,
        test_order_executor,
        test_market_scanner,
        test_signal_generator,
        test_risk_manager
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("ALL TESTS PASSED - TCAP v3 is ready to run!")
    else:
        print(f"⚠️ {failed} tests failed - Please fix errors before running")
    
    print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Test runner error: {e}")
        traceback.print_exc()
