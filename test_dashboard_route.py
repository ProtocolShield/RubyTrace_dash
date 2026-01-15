import sys
sys.path.append('.')
from api import app
import json
import jwt
from datetime import datetime, timedelta

# JWT secret key (same as in api.py)
JWT_SECRET_KEY = 'privacy-osint-jwt-secret-key'

print('Testing /user/dashboard route...')

# Create a valid JWT token for testing
token_payload = {
    'user_id': 1,
    'username': 'testuser',
    'risk_level': 'low',
    'exp': datetime.utcnow() + timedelta(hours=24)
}
token = jwt.encode(token_payload, JWT_SECRET_KEY, algorithm='HS256')

with app.test_client() as client:
    response = client.get('/user/dashboard', headers={'Authorization': f'Bearer {token}'})
    print('Dashboard route status:', response.status_code)
    if response.status_code == 200:
        print('Response is HTML template (length:', len(response.data), 'bytes)')
        # Check if it contains expected elements
        response_text = response.data.decode('utf-8')
        if 'user_dashboard.html' in response_text or 'Activity Timeline' in response_text:
            print('✓ Template appears to be rendered correctly')
        else:
            print('✗ Template may not be rendering correctly')
    else:
        print('Error response:', response.data.decode('utf-8')[:500])
