🚀 Project TCAP: Overview

| Phase | Purpose | Tools/Logic Needed |
|-------|---------|-------------------|
| **T — Track** | Continuously monitor price & volume across Binance | Binance API, 24h price snapshots, volume rolling averages |
| **C — Check** | Identify when a coin has reset, then spiked again | Reset logic (track 24h windows), conditions like ≥15% gain + volume surge |
| **A — Alert** | Notify you instantly when a coin matches all criteria | Telegram bot, Discord webhook, or app push notifications |
| **P — Place** | Manually or automatically enter trade (optional auto-trading later) | TradingView integration, Binance Spot/Perp trading API |

## Implementation Status

### ✅ Completed Features (v2.0)
- **Track**: Continuous monitoring of 75+ USDT futures pairs
- **Check**: Real-time analysis with customizable gain/volume filters
- **Alert**: Browser notifications for price movements
- **Dashboard**: Modern web interface with live updates

### 🔄 Enhanced Features
- **Real-time Data**: Auto-refresh every 15 seconds
- **Background Monitoring**: Continuous data collection every 30 seconds
- **Smart Filtering**: 1%+ gain and $1M+ volume thresholds (adjustable)
- **Professional UI**: Glassmorphism design with live indicators
- **Data Export**: CSV export functionality
- **Organized Structure**: Clean folder organization for maintainability

### 🎯 Future Enhancements
- **Advanced Alerts**: Telegram/Discord integration
- **Auto-trading**: Optional trade execution
- **Reset Detection**: Enhanced logic for coin reset identification
- **Portfolio Integration**: Position tracking
- **Mobile App**: Native applications

## Technical Architecture

```
Frontend (Browser) ← HTTP API → Backend (Flask) ← REST API → Binance Futures
     ↓                              ↓
Live Dashboard              Continuous Monitoring
Auto-refresh 15s            Background updates 30s
```

## Current Capabilities

### Data Sources
- **Primary**: Binance Futures API (fapi.binance.com)
- **Coverage**: All USDT perpetual futures pairs
- **Update Frequency**: Real-time with smart caching

### Analysis Features
- 1-hour price change calculation
- 24-hour volume analysis
- Percentage gain tracking
- Volume threshold filtering
- Real-time sorting and filtering

### User Interface
- Live status indicators
- Customizable filters
- Export functionality
- Alert system
- Mobile-responsive design
