# TCAP v2 - Crypto Trading Analysis Platform

🚀 **Advanced cryptocurrency trading analysis platform that tracks top movers in real-time**

## Features

### ✅ Step-by-Step Implementation (As Requested)

1. **Get All USDT Futures Pairs** - Fetches all USDT-margined perpetual futures from Binance
2. **Get Price 1 Hour Ago** - Calculates 1-hour price movements using candlestick data
3. **Get 24h Volume** - Filters coins with volume ≥ $1M to ensure liquidity (adjustable)
4. **Filter Top Movers** - Identifies coins with ≥1% gains and high volume (adjustable)
5. **Real-time Monitoring** - Live dashboard with auto-refresh every 15 seconds
6. **Data Export** - Export results to CSV format
7. **Alert System** - Browser notifications when criteria are met

### 🎯 Key Capabilities

- **Real-time Data**: Live cryptocurrency market analysis with continuous monitoring
- **Smart Filtering**: Customizable gain % and volume thresholds  
- **Modern UI**: Beautiful, responsive dashboard with glassmorphism design
- **Export Options**: CSV export for further analysis
- **Alert System**: Browser notifications for significant movements
- **Mobile Friendly**: Responsive design works on all devices
- **Continuous Monitoring**: Background updates every 30 seconds

## Project Structure

```
Project TCAP/
├── frontend/
│   ├── index.html          # Main dashboard interface
│   ├── styles.css          # Modern CSS styling with glassmorphism
│   └── script.js           # Frontend JavaScript logic
├── backend/
│   ├── backend.py          # Python Flask API server
│   └── requirements.txt    # Python dependencies
├── scripts/
│   ├── start.bat          # Windows startup script
│   └── start.ps1          # PowerShell startup script
├── docs/
│   ├── README.md          # This documentation file
│   └── Project TCAP Overview.md  # Project overview
└── exports/               # Exported CSV files will be saved here
```

## Quick Start

### Option 1: Use Startup Scripts (Recommended)

**Windows Batch:**
```batch
# Run the startup script
scripts\start.bat
```

**PowerShell:**
```powershell
# Run the PowerShell script
scripts\start.ps1
```

### Option 2: Manual Setup

**1. Install Dependencies**
```powershell
cd backend
pip install -r requirements.txt
```

**2. Start the Backend Server**
```powershell
cd backend
python backend.py
```

The backend will start on `http://localhost:5000`

**3. Open the Frontend**
Open `frontend/index.html` in your web browser, or use a local server:

```powershell
cd frontend
python -m http.server 8080
# Then visit http://localhost:8080
```

## API Endpoints

The backend provides these REST endpoints:

- `GET /api/health` - Health check
- `GET /api/pairs` - Get all USDT futures pairs
- `GET /api/top-movers?min_gain=1&min_volume=1` - Get filtered results
- `GET /api/live-data` - Get continuously monitored live data
- `GET /api/analyze/<symbol>` - Analyze specific cryptocurrency
- `GET /api/monitoring/status` - Get monitoring status
- `POST /api/monitoring/start` - Start continuous monitoring
- `POST /api/monitoring/stop` - Stop continuous monitoring
- `GET /api/export/csv` - Export data in CSV format

## Configuration

### Default Settings
- **Minimum Gain**: 1% (adjustable in UI)
- **Minimum Volume**: $1M (adjustable in UI)
- **Auto-Refresh**: Every 15 seconds (frontend)
- **Background Updates**: Every 30 seconds (backend)
- **Data Source**: Binance Futures API

### Customization
You can modify filters in the web interface:
- Adjust minimum gain percentage (0-100%)
- Change volume requirements ($1M to any amount)
- Sort by gain, volume, or symbol
- Set custom alert thresholds

## Example API Usage

```bash
# Get top movers with 5% gain and $2M volume
curl "http://localhost:5000/api/top-movers?min_gain=5&min_volume=2"

# Get live continuously monitored data
curl "http://localhost:5000/api/live-data?min_gain=1&min_volume=1"

# Analyze specific coin
curl "http://localhost:5000/api/analyze/BTCUSDT"

# Check monitoring status
curl "http://localhost:5000/api/monitoring/status"
```

## Data Format

The API returns data in this format:

```json
{
  "data": [
    {
      "symbol": "ADAUSDT",
      "current_price": 0.8945,
      "price_1h_ago": 0.7650,
      "gain_pct": 16.93,
      "volume_24h": 125000000,
      "timestamp": 1704710400000
    }
  ],
  "count": 1,
  "total_monitored": 75,
  "continuous_monitoring": true,
  "filters": {
    "min_gain_pct": 1,
    "min_volume_millions": 1
  }
}
```

## Continuous Monitoring Features

### Backend Monitoring
- ✅ **Auto-updates every 30 seconds** - Background data collection
- ✅ **Smart caching** - Reduces API calls with 15-second cache
- ✅ **75+ pairs monitored** - Comprehensive market coverage
- ✅ **Intelligent batching** - Optimized API rate limit usage

### Frontend Updates
- ✅ **Auto-refresh every 15 seconds** - Real-time data display
- ✅ **Live status indicators** - Shows connection and update status
- ✅ **Background updates** - No loading overlay for auto-refresh
- ✅ **Manual refresh option** - Force immediate update with loading indicator

## Technical Implementation

### Backend (Python Flask)
- **Binance API Integration**: Direct connection to Binance Futures API
- **Continuous Monitoring**: Background threads for data updates
- **Smart Caching**: Reduces API calls with intelligent caching
- **Error Handling**: Robust error handling and fallbacks
- **Rate Limiting**: Respects Binance API rate limits
- **CORS Enabled**: Allows frontend communication

### Frontend (Modern JavaScript)
- **Real-time Updates**: Auto-refresh with loading states
- **Continuous Monitoring**: TCAPApp class with auto-refresh
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Progressive Enhancement**: Falls back to demo data if backend unavailable
- **Modern UI**: Clean, professional interface with glassmorphism and animations
- **Live Indicators**: Real-time status dots and pulse animations

### File Organization
- **Separation of Concerns**: Frontend, backend, scripts, and docs are organized
- **Easy Maintenance**: Clear folder structure for better project management
- **Scalability**: Organized structure supports future enhancements

## Troubleshooting

### Common Issues

**Backend won't start:**
```powershell
# Make sure Python is installed
python --version

# Install dependencies in backend folder
cd backend
pip install -r requirements.txt

# Check if port 5000 is available
netstat -an | findstr :5000
```

**Frontend shows demo data:**
- Ensure backend is running on `http://localhost:5000`
- Check browser console for error messages
- Verify CORS is enabled (included in backend)
- Make sure to open `frontend/index.html`

**API rate limiting:**
- The backend implements smart caching to reduce API calls
- Binance allows 1200 requests per minute
- Backend processes max 75 symbols per continuous update

**Continuous monitoring not working:**
- Check `/api/monitoring/status` endpoint
- Restart backend server if needed
- Browser console should show "Auto-refresh started" message

## Development

### Architecture
```
Frontend (Browser) ↔ Backend (Flask) ↔ Binance API
      ↓                    ↓
 Auto-refresh         Continuous
 every 15s           monitoring
                     every 30s
```

### Key Files
- `backend/backend.py`: Main Flask application with API endpoints
- `frontend/script.js`: Frontend logic and API communication  
- `frontend/styles.css`: Modern CSS with glassmorphism design
- `frontend/index.html`: Dashboard structure and layout
- `scripts/start.*`: Automated startup scripts

## Future Enhancements

### Planned Features
- **Telegram Alerts**: Send notifications to Telegram
- **Discord Integration**: Post alerts to Discord channels
- **Advanced Charting**: Price charts and technical indicators
- **Portfolio Tracking**: Track your trading positions
- **Auto-trading**: Automated trade execution (optional)
- **Historical Data**: Analyze past performance
- **Mobile App**: Native iOS/Android applications
- **WebSocket Integration**: Even faster real-time updates

## License

This project is for educational and personal use. Please comply with Binance API terms of service.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review browser console for errors
3. Ensure all dependencies are installed
4. Verify Binance API is accessible
5. Check that both frontend and backend are in correct folders

---

**Built with ❤️ for crypto traders and developers**

**Version 2.0 - Enhanced with continuous monitoring and organized folder structure**
