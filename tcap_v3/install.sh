#!/bin/bash

# TCAP v3 Installation Script for Windows (PowerShell)
# Run this script to install TCAP v3 dependencies

echo "Installing TCAP v3 - Automated Trading System"
echo "================================================"

# Check if Python is installed
python --version
if [ $? -ne 0 ]; then
    echo " Python not found. Please install Python 3.8+ first."
    exit 1
fi

# Check if pip is installed
pip --version
if [ $? -ne 0 ]; then
    echo "pip not found. Please install pip first."
    exit 1
fi

echo "Installing Python dependencies..."

# Install required packages
pip install aiohttp>=3.8.0
pip install pandas>=1.3.0
pip install numpy>=1.21.0
pip install ta>=0.7.0
pip install python-dotenv>=0.19.0
pip install cryptography>=3.4.8

echo "Dependencies installed successfully!"

echo "Setting up environment..."

# Create logs directory
mkdir -p logs

# Create .env file template if it doesn't exist
if [ ! -f .env ]; then
    cat > .env << EOF
# TCAP v3 Configuration
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here

# Trading Configuration
PAPER_TRADING=true
STARTING_CAPITAL=5000
MAX_POSITION_SIZE=0.12
DAILY_LOSS_LIMIT=250
EOF
    echo " Created .env configuration file"
    echo " Please edit .env and add your Binance API keys"
fi

echo " TCAP v3 installation complete!"
echo ""
echo " Next steps:"
echo "1. Edit .env file with your Binance API keys"
echo "2. Set PAPER_TRADING=false when ready for live trading"
echo "3. Run: python main_engine.py"
echo ""
echo " Happy trading!"
