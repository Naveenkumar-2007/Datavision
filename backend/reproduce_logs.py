import requests
import time
import sys

BASE_URL = "http://localhost:8000"

def test_logs():
    print(f"🚀 Sending requests to {BASE_URL} to trigger logs...")
    
    endpoints = [
        "/api",
        "/api/v2",
        "/docs",
        "/openapi.json"
    ]
    
    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        try:
            print(f"👉 Requesting: {url}")
            response = requests.get(url)
            print(f"   ✅ Status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            
    print("\n✅ traffic generation complete. check your server terminal for access logs!")

if __name__ == "__main__":
    test_logs()
