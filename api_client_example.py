#!/usr/bin/env python3
"""
API Client Example for Data Source Management
Demonstrates how to use the REST API to manage data sources
"""

import requests
import json
import sys

# API base URL (adjust if running on different port/host)
API_BASE = "http://localhost:5000"

def add_data_source_api(name, url, source_type, category, risk_level, config=None):
    """Add a data source using the API"""
    endpoint = f"{API_BASE}/api/datasources"

    data = {
        "name": name,
        "url": url,
        "source_type": source_type,
        "category": category,
        "risk_level": risk_level,
        "enabled": True,
        "scrape_interval": 60,
        "config": config or {}
    }

    try:
        response = requests.post(endpoint, json=data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Added data source: {name}")
            return result
        else:
            print(f"❌ Failed to add {name}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error adding {name}: {e}")
        return None

def list_data_sources_api():
    """List all data sources using the API"""
    endpoint = f"{API_BASE}/api/datasources"

    try:
        response = requests.get(endpoint)
        if response.status_code == 200:
            sources = response.json()
            print(f"\n📋 Data Sources ({len(sources)} total):")
            for source in sources:
                status = "✅" if source['enabled'] else "❌"
                print(f"  {status} {source['name']} ({source['source_type']}, {source['category']}, {source['risk_level']} risk)")
            return sources
        else:
            print(f"❌ Failed to list sources: {response.text}")
            return []
    except Exception as e:
        print(f"❌ Error listing sources: {e}")
        return []

def update_data_source_api(source_id, updates):
    """Update a data source using the API"""
    endpoint = f"{API_BASE}/api/datasources/{source_id}"

    try:
        response = requests.put(endpoint, json=updates)
        if response.status_code == 200:
            print(f"✅ Updated data source ID {source_id}")
            return response.json()
        else:
            print(f"❌ Failed to update source {source_id}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error updating source {source_id}: {e}")
        return None

def delete_data_source_api(source_id):
    """Delete a data source using the API"""
    endpoint = f"{API_BASE}/api/datasources/{source_id}"

    try:
        response = requests.delete(endpoint)
        if response.status_code == 200:
            print(f"✅ Deleted data source ID {source_id}")
            return True
        else:
            print(f"❌ Failed to delete source {source_id}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error deleting source {source_id}: {e}")
        return False

def add_example_sources_via_api():
    """Add example data sources using the API"""
    print("Adding example data sources via API...")

    examples = [
        {
            "name": "TechCrunch Cybersecurity",
            "url": "https://techcrunch.com/tag/cybersecurity/",
            "source_type": "surface",
            "category": "news",
            "risk_level": "low",
            "config": {"max_depth": 2, "max_pages_per_site": 20}
        },
        {
            "name": "OWASP RSS Feed",
            "url": "https://owasp.org/rss.xml",
            "source_type": "osint",
            "category": "security",
            "risk_level": "low",
            "config": {"feed_type": "rss"}
        },
        {
            "name": "Exploit Database",
            "url": "https://www.exploit-db.com/",
            "source_type": "surface",
            "category": "vulnerability",
            "risk_level": "high",
            "config": {"max_depth": 3, "keyword_filtering": True}
        }
    ]

    added_sources = []
    for example in examples:
        result = add_data_source_api(**example)
        if result:
            added_sources.append(result)

    return added_sources

def demonstrate_bot_operations():
    """Demonstrate bot operations via API"""
    print("\n🤖 Bot Operations Demo")
    print("=" * 30)

    # List bots
    try:
        response = requests.get(f"{API_BASE}/api/bots")
        if response.status_code == 200:
            bots_data = response.json()
            print("Current bot statuses:")
            for bot_type, status in bots_data['bots'].items():
                print(f"  {bot_type}: {status.get('status', 'unknown')}")
        else:
            print(f"❌ Failed to get bot statuses: {response.text}")
    except Exception as e:
        print(f"❌ Error getting bot statuses: {e}")

    # Example: Start surface bot
    print("\nStarting surface web bot...")
    try:
        response = requests.post(f"{API_BASE}/api/bots/surface/start")
        if response.status_code == 200:
            print("✅ Surface bot started successfully")
        else:
            print(f"❌ Failed to start surface bot: {response.text}")
    except Exception as e:
        print(f"❌ Error starting surface bot: {e}")

def main():
    """Main demonstration function"""
    print("🔧 Data Source Management via API")
    print("=" * 40)
    print(f"API Base URL: {API_BASE}")
    print("Make sure the API server is running!")

    # Check if API is running
    try:
        response = requests.get(f"{API_BASE}/api")
        if response.status_code != 200:
            print("❌ API server is not running or not accessible")
            print("Please start the API server first with: python api.py")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API server: {e}")
        print("Please start the API server first with: python api.py")
        return

    # List current sources
    current_sources = list_data_sources_api()

    # Add example sources
    response = input("\nAdd example data sources? (y/n): ").strip().lower()
    if response in ['y', 'yes']:
        added_sources = add_example_sources_via_api()

        # Demonstrate update
        if added_sources:
            first_source = added_sources[0]
            source_id = first_source.get('id')
            if source_id:
                print(f"\nUpdating source ID {source_id}...")
                update_data_source_api(source_id, {"scrape_interval": 120})

    # Demonstrate bot operations
    response = input("\nDemonstrate bot operations? (y/n): ").strip().lower()
    if response in ['y', 'yes']:
        demonstrate_bot_operations()

    print("\n🎉 API demonstration complete!")

if __name__ == "__main__":
    main()
