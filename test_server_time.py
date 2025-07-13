#!/usr/bin/env python3
"""
Test server startup time feature
"""

import requests
import json
from datetime import datetime

def test_server_startup_time():
    print("🧪 Testing Server Startup Time Feature...")
    
    try:
        # Test health endpoint
        response = requests.get('http://localhost:5000/api/health')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health endpoint accessible")
            print(f"   Status: {data.get('status')}")
            print(f"   Current time: {data.get('timestamp')}")
            print(f"   Server startup: {data.get('server_startup_time')}")
            print(f"   Session start: {data.get('session_start_time')}")
            
            # Parse and format times
            if data.get('server_startup_time'):
                startup_time = datetime.fromisoformat(data['server_startup_time'].replace('Z', '+00:00'))
                now = datetime.now()
                diff = now - startup_time.replace(tzinfo=None)
                print(f"   Server uptime: {diff}")
                
        else:
            print(f"❌ Health endpoint returned {response.status_code}")
            
    except requests.ConnectionError:
        print("❌ Could not connect to server - make sure backend is running on localhost:5000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_server_startup_time()
