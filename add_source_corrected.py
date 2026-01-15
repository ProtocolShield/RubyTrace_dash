#!/usr/bin/env python3
"""
Simple script to add a data source for bots
"""

import sys
import os
import json

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, DataSource
from api import app

# Initialize the database
db.init_app(app)

def add_surface_source():
    """Add a surface web source"""
    with app.app_context():
        # Initialize database
        db.create_all()

        # Check if source already exists
        existing = DataSource.query.filter_by(name="Hacker News").first()
        if existing:
            print("⚠️  Hacker News source already exists")
            return

        # Create new data source
        source = DataSource(
            name="Hacker News",
            url="https://news.ycombinator.com/",
            source_type="surface",
            category="news",
            risk_level="low",
            enabled=True,
            scrape_interval=30,
            config_json=json.dumps({
                'max_depth': 2,
                'max_pages_per_site': 20,
                'content_extraction': True
            })
        )

        db.session.add(source)
        db.session.commit()

        print("✅ Added Hacker News source successfully!")

def add_osint_source():
    """Add an OSINT source"""
    with app.app_context():
        # Initialize database
        db.create_all()

        # Check if source already exists
        existing = DataSource.query.filter_by(name="NIST CVE Feed").first()
        if existing:
            print("⚠️  NIST CVE Feed source already exists")
            return

        # Create new data source
        source = DataSource(
            name="NIST CVE Feed",
            url="https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json",
            source_type="osint",
            category="vulnerability",
            risk_level="medium",
            enabled=True,
            scrape_interval=60,
            config_json=json.dumps({
                'feed_type': 'json',
                'data_format': 'cve',
                'auto_process': True
            })
        )

        db.session.add(source)
        db.session.commit()

        print("✅ Added NIST CVE Feed source successfully!")

def list_sources():
    """List all data sources"""
    with app.app_context():
        # Initialize database
        db.create_all()

        sources = DataSource.query.all()

        if not sources:
            print("No data sources found.")
            return

        print("\n📋 Current Data Sources:")
        print("=" * 50)

        for source in sources:
            status = "✅" if source.enabled else "❌"
            print(f"{status} {source.name} ({source.source_type}, {source.category}, {source.risk_level} risk)")

if __name__ == "__main__":
    print("Simple Data Source Management")
    print("=" * 30)

    # List current sources
    list_sources()

    # Add example sources
    print("\nAdding example sources...")
    add_surface_source()
    add_osint_source()

    # List sources again
    list_sources()

    print("\n🎉 Done! You can now use these sources with your bots.")
