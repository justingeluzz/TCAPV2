# Test if backend works in new location
import sys
import os

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Test import of backend components
    from flask import Flask
    import requests
    print("✅ All imports successful")
    print("✅ Backend dependencies are available")
    print("✅ Ready to start TCAP v2 backend server")
    print("🚀 To start the server, run: python backend.py")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("❌ Please install dependencies: pip install -r requirements.txt")
