"""
Wayback Machine API Integration
Provides historical web data and URL analysis
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from . import APIIntegration

class WaybackIntegration(APIIntegration):
    """Wayback Machine API integration for historical web data"""

    def __init__(self, api_key: str = "", config: Dict[str, Any] = None):
        super().__init__(api_key, config)
        self.base_url = "https://archive.org/wayback/available"
        self.name = "wayback"
        self.rate_limits = {
            'requests_per_minute': 10,
            'requests_per_hour': 500,
            'burst_limit': 5
        }

    def test_connection(self) -> bool:
        """Test Wayback Machine API connection"""
        try:
            # Test with a known URL
            test_url = "https://example.com"
            response = requests.get(f"{self.base_url}?url={test_url}", timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Wayback connection test failed: {e}")
            return False

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities"""
        return [
            "url_history",
            "snapshot_retrieval",
            "domain_analysis",
            "historical_data"
        ]

    def execute_query(self, query_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a query against Wayback Machine API"""
        if query_type == "url_history":
            return self.get_url_history(params.get('url', ''))
        elif query_type == "snapshot":
            return self.get_snapshot(params.get('url', ''), params.get('timestamp', ''))
        elif query_type == "domain_analysis":
            return self.analyze_domain(params.get('domain', ''))
        else:
            return {'error': f'Unknown query type: {query_type}'}

    def get_url_history(self, url: str) -> Dict[str, Any]:
        """Get historical snapshots for a URL"""
        try:
            # Wayback CDX API for getting all snapshots
            cdx_url = f"https://web.archive.org/cdx/search/cdx?url={url}&output=json&limit=100"

            response = requests.get(cdx_url, timeout=30)
            if response.status_code != 200:
                return {'error': f'Wayback API returned {response.status_code}'}

            data = response.json()

            if not data or len(data) <= 1:
                return {'snapshots': [], 'total': 0}

            # Parse CDX format
            snapshots = []
            for row in data[1:]:  # Skip header row
                if len(row) >= 9:
                    snapshot = {
                        'timestamp': row[1],
                        'original_url': row[2],
                        'status_code': row[4],
                        'content_type': row[3],
                        'archive_url': f"https://web.archive.org/web/{row[1]}/{row[2]}",
                        'digest': row[5]
                    }
                    snapshots.append(snapshot)

            return {
                'url': url,
                'snapshots': snapshots,
                'total': len(snapshots),
                'first_snapshot': snapshots[0]['timestamp'] if snapshots else None,
                'last_snapshot': snapshots[-1]['timestamp'] if snapshots else None
            }

        except Exception as e:
            return {'error': f'Failed to get URL history: {str(e)}'}

    def get_snapshot(self, url: str, timestamp: str = "") -> Dict[str, Any]:
        """Get a specific snapshot or the closest available"""
        try:
            params = {'url': url}
            if timestamp:
                params['timestamp'] = timestamp

            response = requests.get(self.base_url, params=params, timeout=30)

            if response.status_code != 200:
                return {'error': f'Wayback API returned {response.status_code}'}

            data = response.json()

            if 'archived_snapshots' in data and data['archived_snapshots']:
                snapshot = data['archived_snapshots']['closest']
                return {
                    'url': url,
                    'requested_timestamp': timestamp,
                    'available_timestamp': snapshot.get('timestamp'),
                    'archive_url': snapshot.get('url'),
                    'status': snapshot.get('status')
                }
            else:
                return {'url': url, 'available': False, 'message': 'No snapshot available'}

        except Exception as e:
            return {'error': f'Failed to get snapshot: {str(e)}'}

    def analyze_domain(self, domain: str) -> Dict[str, Any]:
        """Analyze domain history and patterns"""
        try:
            # Get recent snapshots for the domain
            cdx_url = f"https://web.archive.org/cdx/search/cdx?url={domain}/*&output=json&limit=500&from=20200101"

            response = requests.get(cdx_url, timeout=60)
            if response.status_code != 200:
                return {'error': f'Wayback API returned {response.status_code}'}

            data = response.json()

            if not data or len(data) <= 1:
                return {'domain': domain, 'snapshots': [], 'analysis': 'No historical data found'}

            # Analyze patterns
            snapshots = []
            status_codes = {}
            content_types = {}
            monthly_activity = {}

            for row in data[1:]:
                if len(row) >= 9:
                    timestamp = row[1]
                    status_code = row[4]
                    content_type = row[3]

                    snapshots.append({
                        'timestamp': timestamp,
                        'url': row[2],
                        'status_code': status_code,
                        'content_type': content_type
                    })

                    # Count status codes
                    status_codes[status_code] = status_codes.get(status_code, 0) + 1

                    # Count content types
                    content_types[content_type] = content_types.get(content_type, 0) + 1

                    # Monthly activity
                    month_key = timestamp[:6]  # YYYYMM
                    monthly_activity[month_key] = monthly_activity.get(month_key, 0) + 1

            analysis = {
                'total_snapshots': len(snapshots),
                'date_range': {
                    'first': snapshots[0]['timestamp'] if snapshots else None,
                    'last': snapshots[-1]['timestamp'] if snapshots else None
                },
                'status_codes': status_codes,
                'content_types': content_types,
                'monthly_activity': dict(sorted(monthly_activity.items())),
                'most_common_status': max(status_codes, key=status_codes.get) if status_codes else None
            }

            return {
                'domain': domain,
                'snapshots': snapshots[:100],  # Limit for response size
                'analysis': analysis
            }

        except Exception as e:
            return {'error': f'Failed to analyze domain: {str(e)}'}

class Connector:
    def __init__(self, config):
        self.config = config

    def fetch(self, query):
        # Example: Call Wayback API (pseudo)
        return {'snapshot': f'Wayback result for {query}'}
