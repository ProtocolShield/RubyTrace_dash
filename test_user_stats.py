import requests
import json

# Login as test user to get JWT token
login_data = {
    "username": "testuser",
    "password": "testpass"
}

session = requests.Session()
response = session.post('http://127.0.0.1:5000/api/user/login', json=login_data)

if response.status_code == 200:
    token = response.json()['token']
    print("✅ User login successful, token obtained")
    
    # Set Authorization header for subsequent requests
    session.headers.update({'Authorization': f'Bearer {token}'})
    
    # Test /api/user/stats endpoint
    stats_response = session.get('http://127.0.0.1:5000/api/user/stats')
    if stats_response.status_code == 200:
        stats = stats_response.json()
        print("✅ /api/user/stats successful")
        print(f"Stats: {json.dumps(stats, indent=2)}")
        
        # Verify structure for overview
        if 'stats' in stats:
            s = stats['stats']
            print(f"Total items: {s.get('total_items', 'N/A')}")
            print(f"New 24h: {s.get('new_items_24h', 'N/A')}")
            print(f"High risk: {s.get('high_risk_items', 'N/A')}")
            print(f"New CVEs: {s.get('new_cves', 'N/A')}")
        
        if 'charts' in stats:
            c = stats['charts']
            print(f"Timeline data points: {len(c.get('timeline', []))}")
            print(f"Top domains: {len(c.get('top_domains', []))}")
            print(f"Top keywords: {len(c.get('top_keywords', []))}")
    else:
        print(f"❌ /api/user/stats failed: {stats_response.status_code} - {stats_response.text}")
else:
    print(f"❌ User login failed: {response.status_code} - {response.text}")

# Test quick actions indirectly via other endpoints if needed
# Test search endpoint
search_response = session.get('http://127.0.0.1:5000/api/user/search?q=test&limit=5')
if search_response.status_code == 200:
    print("✅ User search endpoint works")
else:
    print(f"❌ User search failed: {search_response.status_code}")

# Test alerts endpoint
alerts_response = session.get('http://127.0.0.1:5000/api/user/alerts?limit=5')
if alerts_response.status_code == 200:
    print("✅ User alerts endpoint works")
else:
    print(f"❌ User alerts failed: {alerts_response.status_code}")
