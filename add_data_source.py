#!/usr/bin/env python3
"""
Script to add data sources for bots
Allows adding data sources for surface, deep, dark, and OSINT bots
"""

import sys
import os
import json
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, DataSource
from api import app

def add_data_source():
    """Interactive script to add a data source"""
    print("🔧 Add Data Source for Bot")
    print("=" * 40)

    # Get user input
    print("\nAvailable bot types:")
    print("1. surface - Surface web sources (news, forums, public sites)")
    print("2. deep - Deep web sources (requires special access)")
    print("3. dark - Dark web sources (.onion sites)")
    print("4. osint - OSINT feed sources (RSS, APIs)")

    while True:
        try:
            choice = input("\nSelect bot type (1-4): ").strip()
            if choice == '1':
                source_type = 'surface'
                break
            elif choice == '2':
                source_type = 'deep'
                break
            elif choice == '3':
                source_type = 'dark'
                break
            elif choice == '4':
                source_type = 'osint'
                break
            else:
                print("Invalid choice. Please select 1-4.")
        except KeyboardInterrupt:
            print("\nOperation cancelled.")
            return

    # Get source details
    name = input("Source name: ").strip()
    if not name:
        print("Name is required.")
        return

    url = input("Source URL: ").strip()
    if not url:
        print("URL is required.")
        return

    # Category suggestions based on type
    categories = {
        'surface': ['news', 'forum', 'blog', 'social', 'academic', 'government'],
        'deep': ['database', 'archive', 'repository', 'internal'],
        'dark': ['market', 'forum', 'leak', 'whistleblower'],
        'osint': ['rss', 'api', 'feed', 'intelligence']
    }

    print(f"\nSuggested categories for {source_type}: {', '.join(categories[source_type])}")
    category = input("Category: ").strip()
    if not category:
        category = categories[source_type][0]  # Use first suggestion as default

    # Risk level
    print("\nRisk levels:")
    print("1. low - Public information, no sensitive data")
    print("2. medium - Some sensitive information, moderate risk")
    print("3. high - Highly sensitive data, high security risk")

    while True:
        risk_choice = input("Risk level (1-3): ").strip()
        if risk_choice == '1':
            risk_level = 'low'
            break
        elif risk_choice == '2':
            risk_level = 'medium'
            break
        elif risk_choice == '3':
            risk_level = 'high'
            break
        else:
            print("Invalid choice. Please select 1-3.")

    # Scrape interval
    while True:
        try:
            interval = input("Scrape interval (minutes, default 60): ").strip()
            if not interval:
                scrape_interval = 60
            else:
                scrape_interval = int(interval)
                if scrape_interval < 15:
                    print("Interval must be at least 15 minutes.")
                    continue
            break
        except ValueError:
            print("Please enter a valid number.")

    # Additional configuration
    config = {}

    if source_type == 'surface':
        max_depth = input("Max crawl depth (default 3): ").strip()
        if max_depth:
            config['max_depth'] = int(max_depth)

        max_pages = input("Max pages per site (default 50): ").strip()
        if max_pages:
            config['max_pages_per_site'] = int(max_pages)

    elif source_type == 'dark':
        use_tor = input("Use Tor for access? (y/n, default y): ").strip().lower()
        if use_tor in ['n', 'no']:
            config['use_tor'] = False
        else:
            config['use_tor'] = True

    elif source_type == 'osint':
        feed_type = input("Feed type (rss/api/json, default rss): ").strip()
        if feed_type:
            config['feed_type'] = feed_type
        else:
            config['feed_type'] = 'rss'

    # Create data source
    with app.app_context():
        try:
            # Check if source with same name exists
            existing = DataSource.query.filter_by(name=name).first()
            if existing:
                print(f"❌ Source with name '{name}' already exists.")
                return

            # Create new data source
            data_source = DataSource(
                name=name,
                url=url,
                source_type=source_type,
                category=category,
                risk_level=risk_level,
                enabled=True,
                scrape_interval=scrape_interval,
                config_json=json.dumps(config) if config else '{}'
            )

            db.session.add(data_source)
            db.session.commit()

            print("
✅ Data source added successfully!"            print(f"   Name: {name}")
            print(f"   URL: {url}")
            print(f"   Type: {source_type}")
            print(f"   Category: {category}")
            print(f"   Risk Level: {risk_level}")
            print(f"   Scrape Interval: {scrape_interval} minutes")
            if config:
                print(f"   Configuration: {json.dumps(config, indent=2)}")

        except Exception as e:
            print(f"❌ Error adding data source: {e}")
            db.session.rollback()

def list_data_sources():
    """List all data sources"""
    print("\n📋 Current Data Sources")
    print("=" * 50)

    with app.app_context():
        sources = DataSource.query.order_by(DataSource.created_at.desc()).all()

        if not sources:
            print("No data sources found.")
            return

        for source in sources:
            print(f"\n🔹 {source.name}")
            print(f"   URL: {source.url}")
            print(f"   Type: {source.source_type}")
            print(f"   Category: {source.category}")
            print(f"   Risk: {source.risk_level}")
            print(f"   Enabled: {source.enabled}")
            print(f"   Interval: {source.scrape_interval} min")
            if source.config_json and source.config_json != '{}':
                config = json.loads(source.config_json)
                print(f"   Config: {config}")

def main():
    """Main function"""
    print(f"Data Source Management Tool - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    while True:
        print("\nOptions:")
        print("1. Add new data source")
        print("2. List all data sources")
        print("3. Exit")

        choice = input("\nSelect option (1-3): ").strip()

        if choice == '1':
            add_data_source()
        elif choice == '2':
            list_data_sources()
        elif choice == '3':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please select 1-3.")

if __name__ == "__main__":
    main()
