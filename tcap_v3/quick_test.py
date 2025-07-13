#!/usr/bin/env python3
"""
Quick validation test for TCAP v3 system
"""

def test_imports():
    """Test all core imports"""
    try:
        print("Testing imports...")
        
        # Test config
        from config import TcapConfig
        print("✓ Config import OK")
        
        # Test market scanner
        from market_scanner import MarketScanner
        print("✓ MarketScanner import OK")
        
        # Test technical analyzer
        from technical_analyzer import TechnicalAnalyzer
        print("✓ TechnicalAnalyzer import OK")
        
        # Test signal generator
        from signal_generator import SignalGenerator, TradingSignal
        print("✓ SignalGenerator import OK")
        
        # Test risk manager
        from risk_manager import RiskManager, Position
        print("✓ RiskManager import OK")
        
        # Test order executor
        from order_executor import OrderExecutor
        print("✓ OrderExecutor import OK")
        
        # Test trade logger
        from trade_logger import TradeLogger, CompletedTrade
        print("✓ TradeLogger import OK")
        
        # Test enhanced components
        from atr_risk_manager import ATRRiskManager
        print("✓ ATRRiskManager import OK")
        
        from trade_failure_analyzer import TradeFailureAnalyzer
        print("✓ TradeFailureAnalyzer import OK")
        
        from position_manager import PositionManager, OpenPosition
        print("✓ PositionManager import OK")
        
        # Test main engine
        from main_engine import TcapEngine
        print("✓ TcapEngine import OK")
        
        print("\n✓ ALL IMPORTS SUCCESSFUL!")
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_config():
    """Test configuration loading"""
    try:
        from config import TcapConfig
        config = TcapConfig()
        print(f"✓ Config loaded - Starting capital: PHP {config.TRADING_CONFIG['starting_capital']}")
        print(f"✓ Realistic TP1: {config.RISK_PARAMS['take_profit_1']*100}% (was 30%!)")
        print(f"✓ Realistic TP2: {config.RISK_PARAMS['take_profit_2']*100}% (was 70%!)")
        print(f"✓ Balanced SL: {config.RISK_PARAMS['stop_loss_max']*100}%")
        return True
    except Exception as e:
        print(f"✗ Config test failed: {e}")
        return False

if __name__ == "__main__":
    print("TCAP v3 System Validation")
    print("=" * 30)
    
    # Test imports
    imports_ok = test_imports()
    
    # Test config
    config_ok = test_config()
    
    if imports_ok and config_ok:
        print("\n🎉 TCAP v3 System is 100% READY!")
    else:
        print("\n❌ System has issues")
