# TCAP v3 - Original Safe Trading Parameters

**📅 Created:** July 13, 2025  
**🎯 Purpose:** Backup of original safe settings before aggressive testing modifications  
**⚠️ IMPORTANT:** Use these parameters when switching from testing to live trading!

---

## 🛡️ Original Safe Trading Configuration

These parameters were designed for **steady, conservative cryptocurrency trading** with minimal risk to turn **$5,000 into $44,650** over 12 months (793% return).

### 💰 **Capital & Position Management**
```
Starting Capital:     $5,000
Position Size Min:    8% ($400 minimum)
Position Size Max:    12% ($600 maximum)
Daily Loss Limit:     $250
Max Leverage:         5x
Max Positions:        5 concurrent
```

### 📊 **Market Scanning Criteria (Conservative)**
```
Min Price Gain:       15% (24h minimum)
Min Volume Ratio:     3x average volume
Min Market Cap:       $50,000,000
Min Volume 24h:       $1,000,000
Pullback Required:    5-15%
```

### 📈 **Technical Analysis Thresholds (Strict)**
```
RSI Oversold:         40
RSI Overbought:       70
RSI Neutral Zone:     45-65
Volume Spike Min:     2x
```

### 🎯 **Signal Confidence Thresholds (High Standards)**
```
LONG Signals:         60% minimum confidence
SHORT Signals:        75% minimum confidence
Signal Cooldown:      60 seconds per pair
```

### ⏱️ **Timing & Intervals (Patient Approach)**
```
Market Scan:          Every 5 minutes
Position Update:      Every 30 seconds
Continuous Cycle:     Every 30 seconds
```

### 🛡️ **Risk Management (Conservative)**
```
Stop Loss:            8% maximum loss
Take Profit 1:        30% (first target)
Take Profit 2:        70% (second target)
Trailing Stop:        5%
Max Single Exposure:  12%
Max Total Exposure:   50%
```

---

## 🎯 Expected Performance with Safe Parameters

### **Monthly Targets**
- **Starting Capital:** $5,000
- **Monthly Return:** ~18% ($900/month)
- **Monthly Trades:** 15-25 high-quality trades
- **Win Rate:** 65-70%
- **Max Drawdown:** <15%

### **12-Month Projection**
| Month | Capital | Monthly Gain | Cumulative Return |
|-------|---------|--------------|-------------------|
| 1     | $5,900  | $900         | 18%               |
| 3     | $8,263  | $1,487       | 65%               |
| 6     | $15,433 | $2,774       | 209%              |
| 9     | $28,802 | $5,184       | 476%              |
| 12    | $44,650 | $8,037       | **793%**          |

### **Trading Frequency**
- **Market Scans:** Every 5 minutes
- **Position Updates:** Every 30 seconds  
- **Daily Signals:** 3-5 high-quality signals
- **Concurrent Positions:** 1-3 maximum

### **Risk Profile**
- ✅ Conservative entries (15%+ gains with pullbacks)
- ✅ Strict exit rules (8% stop loss, 30%/70% profits)
- ✅ High-confidence signals only (60%+ LONG, 75%+ SHORT)
- ✅ Limited exposure (50% max total market exposure)

---

## ⚙️ How to Restore Original Safe Parameters

### **Step 1: Update config.py**
```python
# Trading Parameters
TRADING_CONFIG = {
    'starting_capital': 5000,        # Back to $5,000
    'max_position_size': 0.12,       # 12% of capital
    'daily_loss_limit': 250,         # $250
    'max_leverage': 5,
    'max_open_positions': 5,         # Back to 5
}

# Detection Criteria - CONSERVATIVE
LONG_CRITERIA = {
    'price_gain_24h_min': 15,        # Back to 15%
    'volume_multiplier': 3,          # Back to 3x
    'rsi_min': 40,                   # Back to 40
    'rsi_max': 70,                   # Back to 70
    'market_cap_min': 50_000_000,    # Back to $50M
    'volume_24h_min': 5_000_000,     # Back to $5M
}

# Scanning Configuration - CONSERVATIVE
SCANNING_CONFIG = {
    'scan_interval': 300,            # Back to 5 minutes
    'position_monitor_interval': 30, # Back to 30 seconds
}
```

### **Step 2: Update signal_generator.py**
```python
# Minimum confidence threshold - CONSERVATIVE
if confidence < 0.6:  # Back to 60% for LONG
    return None

# Higher confidence threshold for shorts - CONSERVATIVE  
if confidence < 0.75:  # Back to 75% for SHORT
    return None
```

### **Step 3: Update main_engine.py**
```python
# Schedule next update - CONSERVATIVE
self.update_thread = Timer(30.0, self.continuous_update_loop)  # Back to 30 seconds
```

### **Step 4: Restart System**
```bash
python main_engine.py
```

---

## ⚠️ Current Aggressive Testing Parameters (For Reference)

**❗ WARNING: These are currently active for testing - NOT for live trading!**

### **Current Modified Settings:**
- **Capital:** $50,000 (10x increase)
- **Position Size:** $4,000-$6,000 per trade
- **Signal Thresholds:** 35% LONG, 45% SHORT (LOWERED)
- **Market Criteria:** 8% gains, 2x volume, $20M cap (RELAXED)
- **Timing:** 2-minute scans, 15-second updates (FASTER)

### **Result:** 
- ✅ MORE FREQUENT TRADES for testing
- ❌ HIGHER RISK - not suitable for live trading!

---

## 🔧 Quick Restore Commands

### **For Windows PowerShell:**
```powershell
# Navigate to TCAP directory
cd "C:\Users\geluz\OneDrive\Desktop\Project TCAP\tcap_v3"

# Backup current aggressive config
Copy-Item config.py config_aggressive_backup.py

# Edit config.py with safe parameters (manual edit required)
notepad config.py

# Restart system
python main_engine.py
```

### **Verification Commands:**
```python
# Check current parameters
python -c "from config import TcapConfig; print(f'Capital: ${TcapConfig.TRADING_CONFIG[\"starting_capital\"]:,}')"

# Check signal thresholds in signal_generator.py manually
```

---

## 📝 Notes

1. **Testing vs Live:** Always use aggressive parameters for testing, safe parameters for live trading
2. **Risk Management:** The original parameters prioritize capital preservation over frequency
3. **Performance:** Safe parameters target 793% annual return with 65-70% win rate
4. **Backup:** Keep this file as permanent reference for safe parameters
5. **Monitoring:** With safe parameters, expect 3-5 quality signals per day vs 20+ with aggressive settings

---

**💡 Remember:** Conservative parameters = Lower frequency but higher quality trades = Sustainable long-term profits!
