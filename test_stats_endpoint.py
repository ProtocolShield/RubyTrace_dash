import sys
sys.path.append('.')
from api import app
import json
import jwt
from datetime import datetime, timedelta

# JWT secret key (same as in api.py)
JWT_SECRET_KEY = 'privacy-osint-jwt-secret-key'

print('Testing /api/user/stats endpoint...')

# Create a valid JWT token for testing
token_payload = {
    'user_id': 1,
    'username': 'testuser',
    'risk_level': 'low',
    'exp': datetime.utcnow() + timedelta(hours=24)
}
token = jwt.encode(token_payload, JWT_SECRET_KEY, algorithm='HS256')

with app.test_client() as client:
    response = client.get('/api/user/stats', headers={'Authorization': f'Bearer {token}'})
    print('Status:', response.status_code)
    if response.status_code == 200:
        data = json.loads(response.data)
        print('Response keys:', list(data.keys()))
        if 'charts' in data:
            print('Charts keys:', list(data['charts'].keys()))
            if 'timeline' in data['charts']:
                print('Timeline data length:', len(data['charts']['timeline']))
            if 'top_domains' in data['charts']:
                print('Top domains length:', len(data['charts']['top_domains']))
            if 'top_keywords' in data['charts']:
                print('Top keywords length:', len(data['charts']['top_keywords']))
        else:
            print('No charts data found')
    else:
        print('Error response:', response.data.decode('utf-8'))
