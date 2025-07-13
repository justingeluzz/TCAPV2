# TCAP v2 Startup Script
Write-Host "🚀 Starting TCAP v2 - Crypto Trading Analysis Platform" -ForegroundColor Green
Write-Host ""

# Change to project root directory
Set-Location (Split-Path -Parent $PSScriptRoot)

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python from https://python.org" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Change to backend directory and install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
Set-Location "backend"
try {
    pip install -r requirements.txt
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Start the backend server
Write-Host "🌐 Starting backend server on http://localhost:5000" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 After the server starts:" -ForegroundColor Yellow
Write-Host "   1. Open frontend/index.html in your browser" -ForegroundColor White
Write-Host "   2. The frontend will automatically connect to the backend" -ForegroundColor White
Write-Host ""
Write-Host "🔄 Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start the Python backend
python backend.py
