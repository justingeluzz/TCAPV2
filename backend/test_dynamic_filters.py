# Test Dynamic Filters for TCAP v2
import requests
import json
import time

BASE_URL = "http://localhost:5000"

def test_dynamic_filters():
    print("🧪 Testing TCAP v2 Dynamic Filter System")
    print("=" * 50)
    
    try:
        # Test 1: Get current filters
        print("\n1. Getting current filter parameters...")
        response = requests.get(f"{BASE_URL}/api/monitoring/filters")
        if response.status_code == 200:
            filters = response.json()
            print(f"✅ Current filters: {filters['current_filters']}")
        else:
            print(f"❌ Failed to get filters: {response.status_code}")
            return
        
        # Test 2: Update filters
        print("\n2. Updating filter parameters...")
        new_filters = {
            "min_gain": 0.5,
            "min_volume": 2.0
        }
        
        response = requests.post(
            f"{BASE_URL}/api/monitoring/filters", 
            json=new_filters,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Filters updated: {result['current_filters']}")
        else:
            print(f"❌ Failed to update filters: {response.status_code}")
            return
        
        # Test 3: Verify filters were applied
        print("\n3. Verifying filter update...")
        time.sleep(2)  # Wait a moment
        
        response = requests.get(f"{BASE_URL}/api/monitoring/filters")
        if response.status_code == 200:
            filters = response.json()
            current = filters['current_filters']
            if current['min_gain'] == 0.5 and current['min_volume'] == 2.0:
                print("✅ Filter update verified successfully!")
            else:
                print(f"❌ Filter mismatch: expected 0.5/2.0, got {current['min_gain']}/{current['min_volume']}")
        
        # Test 4: Test live data with new filters
        print("\n4. Testing live data with updated filters...")
        response = requests.get(f"{BASE_URL}/api/live-data?min_gain=0.5&min_volume=2")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Live data response: {data['count']} pairs found")
            print(f"📊 Total monitored: {data.get('total_monitored', 'unknown')}")
        else:
            print(f"❌ Failed to get live data: {response.status_code}")
        
        print("\n🎉 Dynamic filter testing completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend server")
        print("💡 Make sure the backend is running on localhost:5000")
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    test_dynamic_filters()
