import requests
import json

print("🔍 Testing Autonomous API (Fixed)...")
print("="*60)

# Test Overview
print("\n📊 OVERVIEW ENDPOINT:")
try:
    response = requests.get("http://localhost:8000/api/v1/autonomous/overview?user_id=demo_user")
    data = response.json()
    
    if data.get("status") == "success":
        overview = data["data"]
        print(f"✅ Success!")
        print(f"Visual count: {len(overview['visual_primitives'])}")
        print(f"Behavior scores:")
        print(f"  - Density: {overview['behavior_scores']['density']:.3f}")
        print(f"  - Complexity: {overview['behavior_scores']['complexity']:.3f}")
        print(f"  - Temporal: {overview['behavior_scores']['temporal']:.3f}")
        print(f"\nPrimitives:")
        for i, prim in enumerate(overview['visual_primitives']):
            print(f"  {i+1}. [{prim['primitive']}] {prim['title']}")
    else:
        print(f"❌ Error: {data}")
except Exception as e:
    print(f"❌ ERROR: {e}")

# Test Dashboard
print("\n" + "="*60)
print("\n📊 DASHBOARD ENDPOINT:")
try:
    response = requests.get("http://localhost:8000/api/v1/autonomous/dashboard?user_id=demo_user")
    data = response.json()
    
    if data.get("status") == "success":
        dashboard = data["data"]
        print(f"✅ Success!")
        print(f"Visual count: {len(dashboard['visual_primitives'])}")
        print(f"Behavior scores:")
        print(f"  - Density: {dashboard['behavior_scores']['density']:.3f}")
        print(f"  - Complexity: {dashboard['behavior_scores']['complexity']:.3f}")
        print(f"  - Temporal: {dashboard['behavior_scores']['temporal']:.3f}")
        print(f"\nPrimitives:")
        for i, prim in enumerate(dashboard['visual_primitives']):
            print(f"  {i+1}. [{prim['primitive']}] {prim['title']}")
    else:
        print(f"❌ Error: {data}")
except Exception as e:
    print(f"❌ ERROR: {e}")

print("\n" + "="*60)
