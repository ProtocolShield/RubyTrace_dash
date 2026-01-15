"""
Whois API Integration
Provides domain registration and ownership information
"""

import requests
import json
from datetime import datetime
from typing import Dict, Any, List
from . import APIIntegration

class WhoisIntegration(APIIntegration):
    """Whois API integration for domain information"""

    def __init__(self, api_key: str, config: Dict[str, Any] = None):
        super().__init__(api_key, config)
        self.name = "whois"
        self.base_url = "https://api.whois.com"
        self.rate_limits = {
            'requests_per_minute': 60,
            'requests_per_hour': 1000,
            'burst_limit': 10
        }

    def test_connection(self) -> bool:
        """Test Whois API connection"""
        try:
            # Test with a known domain
            test_domain = "example.com"
            response = requests.get(f"{self.base_url}/whois/{test_domain}", timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Whois connection test failed: {e}")
            return False

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities"""
        return [
            "domain_lookup",
            "domain_availability",
            "registrar_info",
            "expiration_check",
            "domain_history"
        ]

    def execute_query(self, query_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a query against Whois API"""
        if query_type == "domain_lookup":
            return self.lookup_domain(params.get('domain', ''))
        elif query_type == "domain_availability":
            return self.check_availability(params.get('domain', ''))
        elif query_type == "registrar_info":
            return self.get_registrar_info(params.get('domain', ''))
        elif query_type == "expiration_check":
            return self.check_expiration(params.get('domain', ''))
        elif query_type == "domain_history":
            return self.get_domain_history(params.get('domain', ''))
        else:
            return {'error': f'Unknown query type: {query_type}'}

    def lookup_domain(self, domain: str) -> Dict[str, Any]:
        """Get comprehensive whois information for a domain"""
        try:
            response = requests.get(
                f"{self.base_url}/whois/{domain}",
                headers={'Authorization': f'Bearer {self.api_key}'} if self.api_key else {},
                timeout=30
            )

            if response.status_code != 200:
                return {'error': f'Whois API returned {response.status_code}'}

            data = response.json()

            # Parse and structure the whois data
            whois_info = {
                'domain': domain,
                'available': data.get('available', False),
                'registered': data.get('registered', False)
            }

            if whois_info['registered']:
                whois_info.update({
                    'registrar': data.get('registrar', {}).get('name'),
                    'creation_date': data.get('creation_date'),
                    'expiration_date': data.get('expiration_date'),
                    'updated_date': data.get('updated_date'),
                    'name_servers': data.get('name_servers', []),
                    'status': data.get('status', []),
                    'registrant': {
                        'name': data.get('registrant', {}).get('name'),
                        'organization': data.get('registrant', {}).get('organization'),
                        'email': data.get('registrant', {}).get('email'),
                        'phone': data.get('registrant', {}).get('phone'),
                        'address': data.get('registrant', {}).get('address')
                    } if data.get('registrant') else None,
                    'admin_contact': data.get('admin_contact'),
                    'tech_contact': data.get('tech_contact')
                })

            return whois_info

        except Exception as e:
            return {'error': f'Failed to lookup domain: {str(e)}'}

    def check_availability(self, domain: str) -> Dict[str, Any]:
        """Check if a domain is available for registration"""
        try:
            response = requests.get(
                f"{self.base_url}/availability/{domain}",
                headers={'Authorization': f'Bearer {self.api_key}'} if self.api_key else {},
                timeout=15
            )

            if response.status_code != 200:
                return {'error': f'Whois API returned {response.status_code}'}

            data = response.json()

            return {
                'domain': domain,
                'available': data.get('available', False),
                'premium': data.get('premium', False),
                'price': data.get('price'),
                'currency': data.get('currency')
            }

        except Exception as e:
            return {'error': f'Failed to check availability: {str(e)}'}

    def get_registrar_info(self, domain: str) -> Dict[str, Any]:
        """Get information about the domain registrar"""
        try:
            # First get basic whois info
            whois_data = self.lookup_domain(domain)

            if 'error' in whois_data:
                return whois_data

            if not whois_data.get('registered'):
                return {'domain': domain, 'registered': False}

            registrar_name = whois_data.get('registrar')
            if not registrar_name:
                return {'error': 'Registrar information not available'}

            # Try to get additional registrar details
            response = requests.get(
                f"{self.base_url}/registrar/{registrar_name.replace(' ', '%20')}",
                headers={'Authorization': f'Bearer {self.api_key}'} if self.api_key else {},
                timeout=15
            )

            registrar_info = {
                'domain': domain,
                'registrar_name': registrar_name,
                'abuse_contact': None,
                'website': None,
                'trust_score': None
            }

            if response.status_code == 200:
                data = response.json()
                registrar_info.update({
                    'abuse_contact': data.get('abuse_contact'),
                    'website': data.get('website'),
                    'trust_score': data.get('trust_score'),
                    'registration_count': data.get('registration_count')
                })

            return registrar_info

        except Exception as e:
            return {'error': f'Failed to get registrar info: {str(e)}'}

    def check_expiration(self, domain: str) -> Dict[str, Any]:
        """Check domain expiration date and status"""
        try:
            whois_data = self.lookup_domain(domain)

            if 'error' in whois_data:
                return whois_data

            if not whois_data.get('registered'):
                return {'domain': domain, 'registered': False}

            expiration_date = whois_data.get('expiration_date')
            if not expiration_date:
                return {'domain': domain, 'expiration_date': None, 'status': 'unknown'}

            # Parse expiration date
            try:
                exp_date = datetime.fromisoformat(expiration_date.replace('Z', '+00:00'))
                now = datetime.utcnow()
                days_until_expiry = (exp_date - now).days

                status = 'active'
                if days_until_expiry < 0:
                    status = 'expired'
                elif days_until_expiry < 30:
                    status = 'expiring_soon'
                elif days_until_expiry < 90:
                    status = 'expires_soon'

                return {
                    'domain': domain,
                    'expiration_date': expiration_date,
                    'days_until_expiry': max(0, days_until_expiry),
                    'status': status,
                    'can_renew': days_until_expiry > 0
                }

            except Exception as parse_error:
                return {
                    'domain': domain,
                    'expiration_date': expiration_date,
                    'status': 'unknown',
                    'parse_error': str(parse_error)
                }

        except Exception as e:
            return {'error': f'Failed to check expiration: {str(e)}'}

    def get_domain_history(self, domain: str) -> Dict[str, Any]:
        """Get historical whois data for a domain"""
        try:
            response = requests.get(
                f"{self.base_url}/history/{domain}",
                headers={'Authorization': f'Bearer {self.api_key}'} if self.api_key else {},
                timeout=30
            )

            if response.status_code != 200:
                return {'error': f'Whois API returned {response.status_code}'}

            data = response.json()

            history = []
            if 'history' in data:
                for entry in data['history']:
                    history.append({
                        'date': entry.get('date'),
                        'registrar': entry.get('registrar'),
                        'name_servers': entry.get('name_servers', []),
                        'status': entry.get('status', [])
                    })

            return {
                'domain': domain,
                'history': history,
                'total_changes': len(history),
                'first_seen': history[0]['date'] if history else None,
                'last_updated': history[-1]['date'] if history else None
            }

        except Exception as e:
            return {'error': f'Failed to get domain history: {str(e)}'}
