import requests
import json

# Check if test user exists and is approved
try:
    # Login as admin first
    admin_login_data = {
        "username": "admin",
        "password": "privacy123"
    }

    response = requests.post('http://127.0.0.1:5000/api/admin-login', json=admin_login_data)
    if response.status_code == 200:
        print("✅ Admin login successful")

        # Try to get users with session cookie
        session = requests.Session()
        session.post('http://127.0.0.1:5000/api/admin-login', json=admin_login_data)

        users_response = session.get('http://127.0.0.1:5000/api/user-management/users')
        if users_response.status_code == 200:
            users = users_response.json()
            test_user = next((u for u in users if u['username'] == 'testuser'), None)
            if test_user:
                print(f"Test user found: ID={test_user['id']}, Active={test_user['is_active']}")
                if not test_user['is_active']:
                    # Approve the user
                    approve_response = session.post(f'http://127.0.0.1:5000/api/user-management/users/{test_user["id"]}/approve')
                    if approve_response.status_code == 200:
                        print("✅ Test user approved successfully")
                    else:
                        print(f"❌ Failed to approve user: {approve_response.status_code}")
                else:
                    print("✅ Test user is already approved")
            else:
                print("❌ Test user not found")
        else:
            print(f"❌ Failed to get users: {users_response.status_code} - {users_response.text}")
    else:
        print(f"❌ Admin login failed: {response.status_code} - {response.text}")

except Exception as e:
    print(f"❌ Error: {e}")

# Try to login as test user to check if approved
try:
    test_login_data = {
        "username": "testuser",
        "password": "testpass"
    }

    response = requests.post('http://127.0.0.1:5000/api/user/login', json=test_login_data)
    if response.status_code == 200:
        print("✅ Test user login successful - user is approved")
    else:
        print(f"❌ Test user login failed: {response.status_code} - {response.text}")
except Exception as e:
    print(f"❌ Error testing user login: {e}")
