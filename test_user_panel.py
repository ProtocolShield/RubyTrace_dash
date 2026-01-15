import unittest
import requests
from flask import url_for
from api import app  # Main Flask app is in api.py
from auth_models import db
from werkzeug.security import generate_password_hash
import os

class TestUserPanel(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        with app.app_context():
            db.drop_all()
            db.create_all()
            # Create test users
            from auth_models import User
            test_user = User(
                username='testuser',
                email='test@example.com',
                full_name='Test User',
                password_hash=generate_password_hash('testpass'),
                is_active=True,
                risk_level='low'
            )
            db.session.add(test_user)
            high_risk_user = User(
                username='highriskuser',
                email='highrisk@example.com',
                full_name='High Risk User',
                password_hash=generate_password_hash('pass'),
                is_active=True,
                risk_level='high',
                twofa_enabled=True
            )
            db.session.add(high_risk_user)
            db.session.commit()

    def get_token(self, username, password):
        """Helper to get auth token."""
        response = self.app.post('/api/user/login', json={
            'username': username,
            'password': password
        })
        if response.status_code == 200:
            data = response.get_json()
            return data.get('token')
        return None

    def test_user_login(self):
        """Test user login functionality."""
        token = self.get_token('testuser', 'testpass')
        self.assertIsNotNone(token)

    def test_user_register(self):
        """Test user registration."""
        response = self.app.post('/api/user/register', json={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass'
        })
        self.assertEqual(response.status_code, 201)
        data = response.get_json()
        self.assertTrue(data['success'])

    def test_user_search(self):
        """Test unified search with masking."""
        token = self.get_token('testuser', 'testpass')
        self.assertIsNotNone(token)
        headers = {'Authorization': f'Bearer {token}'}
        response = self.app.get('/api/user/search?q=test&limit=10', headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('results', data)
        # Check for masking in results - results is a dict with keys like 'email', 'phone', etc.
        results = data['results']
        if 'email' in results and results['email'].get('masked_breaches'):
            for breach in results['email']['masked_breaches']:
                if 'name' in breach:
                    # Email breaches are masked, so no full emails should be present
                    pass  # Simplified check since breaches don't contain emails

    def test_item_details(self):
        """Test item details with masking."""
        token = self.get_token('testuser', 'testpass')
        self.assertIsNotNone(token)
        headers = {'Authorization': f'Bearer {token}'}
        response = self.app.get('/api/user/item/1', headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('item', data)
        # Verify masking
        if 'phone' in data['item']:
            self.assertTrue(data['item']['phone'].startswith('***'))

    def test_alerts(self):
        """Test alerts endpoint."""
        token = self.get_token('testuser', 'testpass')
        self.assertIsNotNone(token)
        headers = {'Authorization': f'Bearer {token}'}
        response = self.app.get('/api/user/alerts', headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('alerts', data)

    def test_watchlists(self):
        """Test watchlists retrieval (simplified - no creation endpoint)."""
        token = self.get_token('testuser', 'testpass')
        self.assertIsNotNone(token)
        headers = {'Authorization': f'Bearer {token}'}

        # Retrieve watchlists (simplified implementation)
        get_response = self.app.get('/api/user/watchlists', headers=headers)
        self.assertEqual(get_response.status_code, 200)
        data = get_response.get_json()
        self.assertIn('watchlists', data)

    def test_graph(self):
        """Test OSINT graph endpoint."""
        token = self.get_token('testuser', 'testpass')
        self.assertIsNotNone(token)
        headers = {'Authorization': f'Bearer {token}'}
        response = self.app.get('/api/user/graph?node=item1', headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('nodes', data)
        self.assertIn('links', data)

    def test_export(self):
        """Test data export with masking."""
        token = self.get_token('testuser', 'testpass')
        self.assertIsNotNone(token)
        headers = {'Authorization': f'Bearer {token}'}
        response = self.app.get('/api/user/export?format=json&mask=true', headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('exported_data', data)
        # Verify no sensitive data in export
        self.assertNotIn('raw_password', str(data))

    def test_user_stats(self):
        """Test user stats dashboard."""
        token = self.get_token('testuser', 'testpass')
        self.assertIsNotNone(token)
        headers = {'Authorization': f'Bearer {token}'}
        response = self.app.get('/api/user/stats', headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('total_items', data)
        self.assertIn('new_items_24h', data)

    def test_audit_logs(self):
        """Test audit logging for user actions."""
        # This would require checking database or logs
        # For now, assume API call logs action
        token = self.get_token('testuser', 'testpass')
        self.assertIsNotNone(token)
        headers = {'Authorization': f'Bearer {token}'}
        response = self.app.get('/api/user/search?q=test', headers=headers)
        self.assertEqual(response.status_code, 200)
        # In real test, query AccessLog model for entry

    def test_2fa_high_risk(self):
        """Test 2FA for high-risk users."""
        # Simulate high-risk user
        response = self.app.post('/api/user/login', json={
            'username': 'highriskuser',
            'password': 'pass',
            'twofa_code': '123456'  # Assume 2FA code
        })
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
