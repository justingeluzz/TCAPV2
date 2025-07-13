# 🚀 TCAP v3 - Automated Cryptocurrency Trading System

## 📋 Overview

TCAP v3 is a fully automated cryptocurrency trading system that implements the complete **Track, Check, Alert, Place** workflow for Binance Futures trading.

### 🎯 Key Features

- **Fully Automated Trading**: Complete hands-off operation
- **Smart Risk Management**: Position sizing, stop losses, daily limits
- **Technical Analysis**: RSI, MACD, volume analysis, support/resistance
- **200+ Pair Monitoring**: All Binance USDT futures pairs
- **Paper Trading Mode**: Test strategies without real money
- **Professional Logging**: Comprehensive activity tracking

## 💰 Trading Strategy

- **Primary**: 80% Long trades (trend following)
- **Secondary**: 20% Short trades (mean reversion)
- **Target**: ₱5,000 → ₱44,660 over 12 months
- **Win Rate**: 55-65% target
- **Risk Management**: Max 12% position size, 5x leverage

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Windows 10/11
- Binance account with API access

### Quick Install
```bash
# Clone or download TCAP v3 files
cd tcap_v3

# Run installation script
install.bat

# Edit configuration
notepad .env
```

### Manual Install
```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

Edit `.env` file:
```env
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here
PAPER_TRADING=true
STARTING_CAPITAL=5000
```

## 🚀 Usage

### Start Trading System
```bash
python main_engine.py
```

### Paper Trading (Recommended First)
Keep `PAPER_TRADING=true` in `.env` to test without real money.

### Live Trading
Set `PAPER_TRADING=false` when ready for real trading.

## 📊 System Components

### Core Modules
- **market_scanner.py**: Monitors 200+ crypto pairs
- **technical_analyzer.py**: RSI, MACD, volume analysis
- **signal_generator.py**: Combines analysis for trade signals
- **risk_manager.py**: Position sizing and safety systems
- **order_executor.py**: Binance API integration
- **main_engine.py**: Orchestrates everything

### Detection Process
1. **TRACK**: Scan all USDT pairs every 5 minutes
2. **CHECK**: Apply technical filters (RSI 40-70, MACD bullish, 3x+ volume)
3. **ALERT**: Generate signals for 15-40% gainers with pullbacks
4. **PLACE**: Execute trades automatically with stop losses

## 🛡️ Safety Features

### Automated Protection
- Daily loss limit (₱250 default)
- Position size limits (max 12% capital)
- Maximum 4 open positions
- Emergency stop functionality
- Market crash detection

### Risk Management
- Intelligent position sizing
- Automatic stop losses (-6% to -8%)
- Take profit automation (+30%, +70%)
- Correlation limits

## 📈 Performance Tracking

### Real-time Monitoring
- Portfolio value updates
- Open position tracking
- Daily/weekly P&L
- Win rate statistics
- Risk exposure metrics

### Logging
All activity logged to `logs/` directory:
- Trade executions
- Risk management actions
- System status updates
- Error handling

## 🔧 Configuration Options

### Trading Parameters
```python
TRADING_CONFIG = {
    'starting_capital': 5000,
    'max_position_size': 0.12,  # 12%
    'max_leverage': 5,
    'daily_loss_limit': 250,
    'max_open_positions': 4
}
```

### Detection Criteria
```python
LONG_CRITERIA = {
    'price_gain_24h_min': 15,  # 15% minimum
    'price_gain_24h_max': 40,  # 40% maximum
    'rsi_min': 40,
    'rsi_max': 70,
    'volume_multiplier': 3,    # 3x average
    'pullback_min': 5,         # 5% pullback
    'pullback_max': 15         # 15% pullback
}
```

## 🚨 Important Disclaimers

### Risk Warnings
- ⚠️ Cryptocurrency trading involves significant risk
- ⚠️ Only trade with money you can afford to lose
- ⚠️ Past performance doesn't guarantee future results
- ⚠️ Start with paper trading mode

### Recommended Approach
1. **Test extensively** in paper trading mode
2. **Start small** with minimum capital
3. **Monitor regularly** especially first few days
4. **Adjust parameters** based on performance

## 📞 Support

### Common Issues
- **API Connection**: Verify API keys and permissions
- **Dependencies**: Run `pip install -r requirements.txt`
- **Permissions**: Ensure Binance futures trading enabled

### Log Files
Check `logs/` directory for detailed error information.

## 📋 System Requirements

### Minimum
- Windows 10/11
- Python 3.8+
- 4GB RAM
- Stable internet connection

### Recommended
- 8GB+ RAM for better performance
- SSD storage for faster logging
- Dedicated internet connection

## 🎯 Expected Performance

### Target Metrics
- **Monthly Return**: 15-25%
- **Win Rate**: 55-65%
- **Max Drawdown**: <20%
- **Trades per Month**: 30-60
- **Operation**: 24/7 automated

### Growth Projection
```
Month 1: ₱5,000 → ₱6,000 (+20%)
Month 3: ₱5,000 → ₱8,640 (+73%)
Month 6: ₱5,000 → ₱14,930 (+199%)
Month 12: ₱5,000 → ₱44,660 (+793%)
```

## 🏆 Advantages

### vs Manual Trading
- ✅ No emotional decisions
- ✅ 24/7 market monitoring
- ✅ Instant signal execution
- ✅ Consistent risk management

### vs Commercial Bots
- ✅ Zero monthly fees
- ✅ Full control and customization
- ✅ Transparent logic
- ✅ Small account optimized

---

**TCAP v3 - Professional automated trading for sustainable cryptocurrency wealth building** 🚀
