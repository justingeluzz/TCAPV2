@echo off
echo 🚀 Starting TCAP v2 - Crypto Trading Analysis Platform
echo.

REM Change to project root directory
cd /d "%~dp0.."

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Install dependencies if needed
echo 📦 Installing dependencies...
cd backend
pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed
echo.

REM Start the backend server
echo 🌐 Starting backend server on http://localhost:5000
echo.
echo 💡 After the server starts:
echo    1. Open frontend/index.html in your browser
echo    2. The frontend will automatically connect to the backend
echo.
echo 🔄 Press Ctrl+C to stop the server
echo.

python backend.py
