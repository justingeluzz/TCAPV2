#!/usr/bin/env python3
"""
Debug first hits leaderboard
"""

import requests
import json

def debug_first_hits():
    print("🔍 Debugging First Hits Leaderboard...")
    
    try:
        # Test first hits endpoint
        response = requests.get('http://localhost:5000/api/first-hits')
        if response.status_code == 200:
            data = response.json()
            print(f"✅ First hits endpoint accessible")
            print(f"   Success: {data.get('success')}")
            print(f"   Data keys: {list(data.get('data', {}).keys())}")
            
            if 'data' in data and 'leaderboard' in data['data']:
                leaderboard = data['data']['leaderboard']
                print(f"   Leaderboard entries: {len(leaderboard)}")
                print(f"   Current threshold: {data['data'].get('current_threshold')}%")
                print(f"   Total first hits: {data['data'].get('total_first_hits')}")
                
                for i, hit in enumerate(leaderboard[:3]):  # Show first 3
                    print(f"   #{i+1}: {hit.get('symbol')} - {hit.get('first_hit_gain', 'N/A')}% gain")
                    print(f"        Threshold used: {hit.get('threshold_used', 'N/A')}%")
                    print(f"        Time: {hit.get('first_hit_time', 'N/A')}")
            else:
                print(f"   ❌ Unexpected data structure: {json.dumps(data, indent=2)}")
                
        else:
            print(f"❌ First hits endpoint returned {response.status_code}")
            print(f"   Response: {response.text}")
            
        # Also test live data to see what's being tracked
        print("\n🔍 Checking live data...")
        response = requests.get('http://localhost:5000/api/live-data?min_gain=3&min_volume=1')
        if response.status_code == 200:
            data = response.json()
            live_data = data.get('data', [])
            print(f"   Live data entries: {len(live_data)}")
            for i, item in enumerate(live_data[:3]):  # Show first 3
                print(f"   #{i+1}: {item.get('symbol')} - {item.get('gain_pct', 'N/A')}% gain")
        
    except requests.ConnectionError:
        print("❌ Could not connect to server - make sure backend is running on localhost:5000")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_first_hits()
