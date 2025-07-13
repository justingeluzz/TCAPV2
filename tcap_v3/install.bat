@echo off
REM TCAP v3 Installation Script for Windows
REM Run this script to install TCAP v3 dependencies

echo  Installing TCAP v3 - Automated Trading System
echo ================================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Please install Python 3.8+ first.
    pause
    exit /b 1
)

REM Check if pip is installed
pip --version >nul 2>&1
if errorlevel 1 (
    echo pip not found. Please install pip first.
    pause
    exit /b 1
)

echo 📦 Installing Python dependencies...

REM Install required packages
pip install aiohttp>=3.8.0
pip install pandas>=1.3.0
pip install numpy>=1.21.0
pip install ta>=0.7.0
pip install python-dotenv>=0.19.0
pip install cryptography>=3.4.8

echo Dependencies installed successfully!

echo Setting up environment...

REM Create logs directory
if not exist "logs" mkdir logs

REM Create .env file template if it doesn't exist
if not exist ".env" (
    echo # TCAP v3 Configuration > .env
    echo BINANCE_API_KEY=your_binance_api_key_here >> .env
    echo BINANCE_SECRET_KEY=your_binance_secret_key_here >> .env
    echo. >> .env
    echo # Trading Configuration >> .env
    echo PAPER_TRADING=true >> .env
    echo STARTING_CAPITAL=5000 >> .env
    echo MAX_POSITION_SIZE=0.12 >> .env
    echo DAILY_LOSS_LIMIT=250 >> .env
    
    echo Created .env configuration file
    echo Please edit .env and add your Binance API keys
)

echo TCAP v3 installation complete!
echo.
echo  Next steps:
echo 1. Edit .env file with your Binance API keys
echo 2. Set PAPER_TRADING=false when ready for live trading
echo 3. Run: python main_engine.py
echo.
echo  Happy trading!
pause
