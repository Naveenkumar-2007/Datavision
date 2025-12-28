"""
Test Advanced Engine via API
=============================
Tests the new V2 engines through the API endpoints.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_advanced_api():
    """Test Overview and Dashboard with Advanced Pattern Detection."""
    
    print("="*70)
    print("🚀 TESTING ADVANCED ENGINE VIA API")
    print("="*70)
    
    # Test Overview
    print("\n📊 Testing Overview Endpoint...")
    response = requests.get(f"{BASE_URL}/api/v1/autonomous/overview?user_id=demo_user")
    
    if response.status_code == 200:
        data = response.json()
        visuals = data['data']['visual_primitives']
        print(f"   ✅ Overview SUCCESS!")
        print(f"   📈 Visual count: {len(visuals)}")
        print(f"   🎨 Chart types:")
        for i, v in enumerate(visuals[:5], 1):
            print(f"      {i}. {v['primitive']}: {v['title']}")
    else:
        print(f"   ❌ FAILED: {response.status_code}")
        print(f"   Error: {response.text}")
    
    # Test Dashboard
    print("\n📊 Testing Dashboard Endpoint...")
    response = requests.get(f"{BASE_URL}/api/v1/autonomous/dashboard?user_id=demo_user")
    
    if response.status_code == 200:
        data = response.json()
        visuals = data['data']['visual_primitives']
        print(f"   ✅ Dashboard SUCCESS!")
        print(f"   📈 Visual count: {len(visuals)}")
        print(f"   🎨 Chart types:")
        for i, v in enumerate(visuals[:5], 1):
            print(f"      {i}. {v['primitive']}: {v['title']}")
    else:
        print(f"   ❌ FAILED: {response.status_code}")
        print(f"   Error: {response.text}")
    
    print("\n" + "="*70)
    print("✅ API TESTS COMPLETE")
    print("="*70)

if __name__ == "__main__":
    test_advanced_api()
