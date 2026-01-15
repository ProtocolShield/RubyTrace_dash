import requests
import json

# Register a test user
register_data = {
    "username": "testuser",
    "password": "testpass",
    "email": "test@example.com"
}

try:
    response = requests.post('http://127.0.0.1:5000/api/user/register', json=register_data)
    if response.status_code == 201:
        print("✅ Test user registered successfully")
    else:
        print(f"❌ Failed to register user: {response.status_code} - {response.text}")
except Exception as e:
    print(f"❌ Error registering user: {e}")

# Login as admin to approve the user
admin_login_data = {
    "username": "admin",
    "password": "privacy123"
}

try:
    response = requests.post('http://127.0.0.1:5000/api/admin-login', json=admin_login_data)
    if response.status_code == 200:
        print("✅ Admin login successful")
        # Now approve the user
        # First get all users to find the test user ID
        users_response = requests.get('http://127.0.0.1:5000/api/user-management/users')
        if users_response.status_code == 200:
            users = users_response.json()
            test_user = next((u for u in users if u['username'] == 'testuser'), None)
            if test_user:
                approve_response = requests.post(f'http://127.0.0.1:5000/api/user-management/users/{test_user["id"]}/approve')
                if approve_response.status_code == 200:
                    print("✅ Test user approved successfully")
                else:
                    print(f"❌ Failed to approve user: {approve_response.status_code}")
            else:
                print("❌ Test user not found in user list")
        else:
            print(f"❌ Failed to get users: {users_response.status_code}")
    else:
        print(f"❌ Admin login failed: {response.status_code} - {response.text}")
except Exception as e:
    print(f"❌ Error in admin operations: {e}")
