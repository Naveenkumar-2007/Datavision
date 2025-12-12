"""
Quick API test to verify settings persistence
"""
import requests
import json

# Test user ID (replace with real one from Supabase auth)
user_id = "test-user-123"
workspace_id = user_id  # We're using user_id as workspace_id

print("=" * 60)
print("Testing Notification Settings API")
print("=" * 60)

# Test 1: Get settings (should return defaults first time)
print("\n[Test 1] GET settings...")
response = requests.get(
    f"http://localhost:8000/api/settings/{workspace_id}/{user_id}",
    headers={"Authorization": "Bearer fake-token-for-testing"}
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("Current settings:")
    print(json.dumps(response.json(), indent=2))
else:
    print(f"Error: {response.text}")

# Test 2: Update settings (turn everything OFF)
print("\n[Test 2] PATCH settings (turn all OFF)...")
update_data = {
    "email_notifications": False,
    "push_notifications": False,
    "weekly_reports": False,
    "ai_insights": False
}

response = requests.patch(
    f"http://localhost:8000/api/settings/{workspace_id}/{user_id}",
    headers={"Authorization": "Bearer fake-token-for-testing"},
    json=update_data
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    print("Updated settings:")
    print(json.dumps(response.json(), indent=2))
else:
    print(f"Error: {response.text}")

# Test 3: Get settings again (should be all OFF now)
print("\n[Test 3] GET settings again (verify they saved)...")
response = requests.get(
    f"http://localhost:8000/api/settings/{workspace_id}/{user_id}",
    headers={"Authorization": "Bearer fake-token-for-testing"}
)
print(f"Status: {response.status_code}")
if response.status_code == 200:
    settings = response.json()
    print("Saved settings:")
    print(json.dumps(settings, indent=2))
    
    # Verify
    if (settings.get('email_notifications') == False and
        settings.get('push_notifications') == False and
        settings.get('weekly_reports') == False and
        settings.get('ai_insights') == False):
        print("\n✅ SUCCESS! Settings persisted correctly!")
    else:
        print("\n❌ FAILED! Settings did not persist!")
else:
    print(f"Error: {response.text}")

print("\n" + "=" * 60)
