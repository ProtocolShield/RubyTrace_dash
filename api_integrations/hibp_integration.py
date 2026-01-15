"""
Have I Been Pwned (HIBP) API Integration
Checks for compromised email addresses and passwords in data breaches
"""

import requests
import hashlib
import json
from typing import Dict, Any, List
from . import APIIntegration

class HIBPIntegration(APIIntegration):
    """Have I Been Pwned API integration for breach checking"""

    def __init__(self, api_key: str, config: Dict[str, Any] = None):
        super().__init__(api_key, config)
        self.name = "hibp"
        self.base_url = "https://haveibeenpwned.com/api/v3"
        self.rate_limits = {
            'requests_per_minute': 10,  # HIBP has strict rate limits
            'requests_per_hour': 100,
            'burst_limit': 5
        }

    def test_connection(self) -> bool:
        """Test HIBP API connection"""
        try:
            # Test with a known breached account (use a test email)
            headers = {'hibp-api-key': self.api_key} if self.api_key else {}
            response = requests.get(
                f"{self.base_url}/breachedaccount/test@example.com",
                headers=headers,
                timeout=10
            )
            # 404 is expected for non-breached accounts, which is a successful response
            return response.status_code in [200, 404, 429]
        except Exception as e:
            print(f"HIBP connection test failed: {e}")
            return False

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities"""
        return [
            "check_email_breaches",
            "check_password_breaches",
            "get_breach_details",
            "get_paste_details",
            "check_domain_breaches"
        ]

    def execute_query(self, query_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a query against HIBP API"""
        if query_type == "check_email_breaches":
            return self.check_email_breaches(params.get('email', ''))
        elif query_type == "check_password_breaches":
            return self.check_password_breaches(params.get('password', ''))
        elif query_type == "get_breach_details":
            return self.get_breach_details(params.get('breach_name', ''))
        elif query_type == "get_paste_details":
            return self.get_paste_details(params.get('email', ''))
        elif query_type == "check_domain_breaches":
            return self.check_domain_breaches(params.get('domain', ''))
        else:
            return {'error': f'Unknown query type: {query_type}'}

    def check_email_breaches(self, email: str) -> Dict[str, Any]:
        """Check if an email address has been involved in data breaches"""
        try:
            headers = {'hibp-api-key': self.api_key} if self.api_key else {}
            response = requests.get(
                f"{self.base_url}/breachedaccount/{email}",
                headers=headers,
                timeout=30
            )

            if response.status_code == 404:
                return {
                    'email': email,
                    'breached': False,
                    'breaches': [],
                    'total_breaches': 0
                }
            elif response.status_code == 429:
                return {'error': 'Rate limit exceeded. Please try again later.'}
            elif response.status_code != 200:
                return {'error': f'HIBP API returned {response.status_code}'}

            breaches = response.json()

            # Format breach data
            formatted_breaches = []
            for breach in breaches:
                formatted_breaches.append({
                    'name': breach.get('Name'),
                    'title': breach.get('Title'),
                    'domain': breach.get('Domain'),
                    'breach_date': breach.get('BreachDate'),
                    'added_date': breach.get('AddedDate'),
                    'modified_date': breach.get('ModifiedDate'),
                    'pwn_count': breach.get('PwnCount'),
                    'description': breach.get('Description'),
                    'data_classes': breach.get('DataClasses', []),
                    'is_verified': breach.get('IsVerified', False),
                    'is_fabricated': breach.get('IsFabricated', False),
                    'is_sensitive': breach.get('IsSensitive', False),
                    'is_retired': breach.get('IsRetired', False),
                    'is_spam_list': breach.get('IsSpamList', False),
                    'logo_path': breach.get('LogoPath')
                })

            return {
                'email': email,
                'breached': True,
                'breaches': formatted_breaches,
                'total_breaches': len(formatted_breaches)
            }

        except Exception as e:
            return {'error': f'Failed to check email breaches: {str(e)}'}

    def check_password_breaches(self, password: str) -> Dict[str, Any]:
        """Check if a password has been compromised using k-anonymity"""
        try:
            # Create SHA-1 hash of the password
            sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()

            # Use k-anonymity: send first 5 characters of hash
            prefix = sha1_hash[:5]
            suffix = sha1_hash[5:]

            headers = {'hibp-api-key': self.api_key} if self.api_key else {}
            response = requests.get(
                f"{self.base_url}/range/{prefix}",
                headers=headers,
                timeout=30
            )

            if response.status_code == 429:
                return {'error': 'Rate limit exceeded. Please try again later.'}
            elif response.status_code != 200:
                return {'error': f'HIBP API returned {response.status_code}'}

            # Parse the response to find matching suffix
            lines = response.text.strip().split('\n')
            compromised_count = 0

            for line in lines:
                if ':' in line:
                    hash_suffix, count = line.split(':')
                    if hash_suffix == suffix:
                        compromised_count = int(count)
                        break

            return {
                'password_hash': sha1_hash,
                'compromised': compromised_count > 0,
                'compromise_count': compromised_count,
                'checked_prefix': prefix
            }

        except Exception as e:
            return {'error': f'Failed to check password breaches: {str(e)}'}

    def get_breach_details(self, breach_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific breach"""
        try:
            headers = {'hibp-api-key': self.api_key} if self.api_key else {}
            response = requests.get(
                f"{self.base_url}/breach/{breach_name}",
                headers=headers,
                timeout=30
            )

            if response.status_code == 404:
                return {'error': f'Breach {breach_name} not found'}
            elif response.status_code == 429:
                return {'error': 'Rate limit exceeded. Please try again later.'}
            elif response.status_code != 200:
                return {'error': f'HIBP API returned {response.status_code}'}

            breach = response.json()

            return {
                'name': breach.get('Name'),
                'title': breach.get('Title'),
                'domain': breach.get('Domain'),
                'breach_date': breach.get('BreachDate'),
                'added_date': breach.get('AddedDate'),
                'modified_date': breach.get('ModifiedDate'),
                'pwn_count': breach.get('PwnCount'),
                'description': breach.get('Description'),
                'data_classes': breach.get('DataClasses', []),
                'is_verified': breach.get('IsVerified', False),
                'is_fabricated': breach.get('IsFabricated', False),
                'is_sensitive': breach.get('IsSensitive', False),
                'is_retired': breach.get('IsRetired', False),
                'is_spam_list': breach.get('IsSpamList', False),
                'logo_path': breach.get('LogoPath')
            }

        except Exception as e:
            return {'error': f'Failed to get breach details: {str(e)}'}

    def get_paste_details(self, email: str) -> Dict[str, Any]:
        """Get pastebin and other paste site details for an email"""
        try:
            headers = {'hibp-api-key': self.api_key} if self.api_key else {}
            response = requests.get(
                f"{self.base_url}/pasteaccount/{email}",
                headers=headers,
                timeout=30
            )

            if response.status_code == 404:
                return {
                    'email': email,
                    'pastes': [],
                    'total_pastes': 0
                }
            elif response.status_code == 429:
                return {'error': 'Rate limit exceeded. Please try again later.'}
            elif response.status_code != 200:
                return {'error': f'HIBP API returned {response.status_code}'}

            pastes = response.json()

            # Format paste data
            formatted_pastes = []
            for paste in pastes:
                formatted_pastes.append({
                    'source': paste.get('Source'),
                    'id': paste.get('Id'),
                    'title': paste.get('Title'),
                    'date': paste.get('Date'),
                    'email_count': paste.get('EmailCount')
                })

            return {
                'email': email,
                'pastes': formatted_pastes,
                'total_pastes': len(formatted_pastes)
            }

        except Exception as e:
            return {'error': f'Failed to get paste details: {str(e)}'}

    def check_domain_breaches(self, domain: str) -> Dict[str, Any]:
        """Get all breaches for a specific domain"""
        try:
            headers = {'hibp-api-key': self.api_key} if self.api_key else {}
            response = requests.get(
                f"{self.base_url}/breaches?domain={domain}",
                headers=headers,
                timeout=30
            )

            if response.status_code == 429:
                return {'error': 'Rate limit exceeded. Please try again later.'}
            elif response.status_code != 200:
                return {'error': f'HIBP API returned {response.status_code}'}

            breaches = response.json()

            # Format breach data
            formatted_breaches = []
            for breach in breaches:
                formatted_breaches.append({
                    'name': breach.get('Name'),
                    'title': breach.get('Title'),
                    'domain': breach.get('Domain'),
                    'breach_date': breach.get('BreachDate'),
                    'added_date': breach.get('AddedDate'),
                    'pwn_count': breach.get('PwnCount'),
                    'description': breach.get('Description'),
                    'data_classes': breach.get('DataClasses', []),
                    'is_verified': breach.get('IsVerified', False),
                    'is_sensitive': breach.get('IsSensitive', False)
                })

            return {
                'domain': domain,
                'breaches': formatted_breaches,
                'total_breaches': len(formatted_breaches)
            }

        except Exception as e:
            return {'error': f'Failed to check domain breaches: {str(e)}'}

    def get_data_classes(self) -> Dict[str, Any]:
        """Get all available data classes that can be breached"""
        try:
            headers = {'hibp-api-key': self.api_key} if self.api_key else {}
            response = requests.get(
                f"{self.base_url}/dataclasses",
                headers=headers,
                timeout=30
            )

            if response.status_code != 200:
                return {'error': f'HIBP API returned {response.status_code}'}

            data_classes = response.json()

            return {
                'data_classes': data_classes,
                'total_classes': len(data_classes)
            }

        except Exception as e:
            return {'error': f'Failed to get data classes: {str(e)}'}
