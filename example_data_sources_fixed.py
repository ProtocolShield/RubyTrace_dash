#!/usr/bin/env python3
"""
Example data sources for each bot type
Demonstrates how to add data sources programmatically
"""

import sys
import os
import json

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, DataSource
from api import app

def add_example_sources():
    """Add example data sources for each bot type"""

    example_sources = [
        # Surface Web Sources
        {
            'name': 'Hacker News',
            'url': 'https://news.ycombinator.com/',
            'source_type': 'surface',
            'category': 'news',
            'risk_level': 'low',
            'scrape_interval': 30,
            'config': {
                'max_depth': 2,
                'max_pages_per_site': 20,
                'content_extraction': True
            }
        },
        {
            'name': 'Reddit Cybersecurity',
            'url': 'https://www.reddit.com/r/cybersecurity/',
            'source_type': 'surface',
            'category': 'forum',
            'risk_level': 'medium',
            'scrape_interval': 60,
            'config': {
                'max_depth': 3,
                'max_pages_per_site': 50,
                'keyword_filtering': True
            }
        },
        {
            'name': 'Krebs on Security',
            'url': 'https://krebsonsecurity.com/',
            'source_type': 'surface',
            'category': 'blog',
            'risk_level': 'medium',
            'scrape_interval': 120,
            'config': {
                'max_depth': 1,
                'max_pages_per_site': 10
            }
        },

        # Deep Web Sources (examples - would need actual access)
        {
            'name': 'Academic Database',
            'url': '    ,
            'source_type': 'deep',
            'category': 'academic',
            'risk_level': 'low',
            'scrape_interval': 240,
            'config': {
                'requires_auth': True,
                'auth_type': 'oauth',
                'max_pages_per_site': 100
            }
        },

        # Dark Web Sources (examples - would need Tor)
        {
            'name': 'Dark Web Market Monitor',
            'url': 'http://example.onion/market',
            'source_type': 'dark',
            'category': 'market',
            'risk_level': 'high',
            'scrape_interval': 480,
            'config': {
                'use_tor': True,
                'max_depth': 2,
                'rate_limit': 10
            }
        },
        {
            'name': 'Dark Web Forum',
            'url': 'http://example.onion/forum',
            'source_type': 'dark',
            'category': 'forum',
            'risk_level': 'high',
            'scrape_interval': 360,
            'config': {
                'use_tor': True,
                'keyword_filtering': True,
                'content_analysis': True
            }
        },

        # OSINT Feed Sources
        {
            'name': 'NIST Vulnerability Feed',
            'url': 'https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json',
            'source_type': 'osint',
            'category': 'vulnerability',
            'risk_level': 'medium',
            'scrape_interval': 60,
            'config': {
                'feed_type': 'json',
                'data_format': 'cve',
                'auto_process': True
            }
        },
        {
            'name': 'HaveIBeenPwned API',
            'url': 'https://haveibeenpwned.com/api/v3/breaches',
            'source_type': 'osint',
            'category': 'breach',
            'risk_level': 'medium',
            'scrape_interval': 1440,  # Daily
            'config': {
                'feed_type': 'api',
                'requires_api_key': True,
                'data_format': 'breach'
            }
        },
        {
            'name': 'AlienVault OTX',
            'url': 'https://otx.alienvault.com/api/v1/pulses/subscribed',
            'source_type': 'osint',
            'category': 'threat_intel',
            'risk_level': 'high',
            'scrape_interval': 180,
            'config': {
                'feed_type': 'api',
                'requires_api_key': True,
                'data_format': 'pulse'
            }
        }
    ]

    with app.app_context():
        # Initialize database
        db.create_all()
        
        added_count = 0

        for source_data in example_sources:
            try:
                # Check if source already exists
                existing = DataSource.query.filter_by(name=source_data['name']).first()
                if existing:
                    print(f"⚠️  Source '{source_data['name']}' already exists, skipping...")
                    continue

                # Create new data source
                data_source = DataSource(
                    name=source_data['name'],
                    url=source_data['url'],
                    source_type=source_data['source_type'],
                    category=source_data['category'],
                    risk_level=source_data['risk_level'],
                    enabled=True,
                    scrape_interval=source_data['scrape_interval'],
                    config_json=json.dumps(source_data['config'])
                )

                db.session.add(data_source)
                added_count += 1

                print(f"✅ Added {source_data['source_type']} source: {source_data['name']}")

            except Exception as e:
                print(f"❌ Error adding {source_data['name']}: {e}")
                continue

        try:
            db.session.commit()
            print(f"\n🎉 Successfully added {added_count} data sources!")
        except Exception as e:
            print(f"❌ Error committing changes: {e}")
            db.session.rollback()

def show_current_sources():
    """Display current data sources by type"""
    print("\n📊 Current Data Sources by Type")
    print("=" * 50)

    with app.app_context():
        # Initialize database
        db.create_all()
        
        sources = DataSource.query.all()

        if not sources:
            print("No data sources found.")
            return

        # Group by type
        by_type = {}
        for source in sources:
            if source.source_type not in by_type:
                by_type[source.source_type] = []
            by_type[source.source_type].append(source)

        for source_type, type_sources in by_type.items():
            print(f"\n🔹 {source_type.upper()} ({len(type_sources)} sources):")
            for source in type_sources:
                status = "✅" if source.enabled else "❌"
                print(f"   {status} {source.name} ({source.category}, {source.risk_level} risk)")

if __name__ == "__main__":
    print("Example Data Sources Setup")
    print("=" * 30)

    # Show current sources
    show_current_sources()

    # Ask user if they want to add examples
    response = input("\nAdd example data sources? (y/n): ").strip().lower()
    if response in ['y', 'yes']:
        add_example_sources()
        show_current_sources()
    else:
        print("Operation cancelled.")
