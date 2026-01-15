#!/usr/bin/env python3
"""
Test script to verify data collection and show results
"""

import requests
import json
import time

def test_data_collection():
    """Test the data collection system"""
    base_url = "http://127.0.0.1:5000/api"
    
    print("🔍 Testing OSINT Bot Data Collection System")
    print("=" * 50)
    
    # 1. Check bot status
    print("\n1. Checking bot status...")
    try:
        response = requests.get(f"{base_url}/bots")
        if response.status_code == 200:
            bots = response.json()
            print("✅ Bots status retrieved successfully")
            for bot_type, status in bots['bots'].items():
                print(f"   {bot_type}: {status.get('status', 'unknown')}")
        else:
            print(f"❌ Failed to get bot status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting bot status: {e}")
    
    # 2. Check data sources
    print("\n2. Checking data sources...")
    try:
        response = requests.get(f"{base_url}/datasources")
        if response.status_code == 200:
            sources = response.json()
            print(f"✅ Found {len(sources['sources'])} data sources")
            for source in sources['sources'][:5]:  # Show first 5
                print(f"   - {source['name']} ({source['source_type']}) - {source['risk_level']}")
        else:
            print(f"❌ Failed to get data sources: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting data sources: {e}")
    
    # 3. Start surface bot
    print("\n3. Starting surface web bot...")
    try:
        response = requests.post(f"{base_url}/bots/surface/start")
        if response.status_code == 200:
            print("✅ Surface bot started")
        else:
            print(f"❌ Failed to start surface bot: {response.status_code}")
    except Exception as e:
        print(f"❌ Error starting surface bot: {e}")
    
    # 4. Run collection cycle
    print("\n4. Running data collection cycle...")
    try:
        response = requests.post(
            f"{base_url}/bots/run-cycle",
            headers={"Content-Type": "application/json"},
            json={"bot_type": "surface", "source_type": "surface_web"}
        )
        if response.status_code == 200:
            print("✅ Collection cycle started")
        else:
            print(f"❌ Failed to start collection cycle: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error starting collection cycle: {e}")
    
    # 5. Wait and check results
    print("\n5. Waiting for data collection...")
    time.sleep(15)  # Wait 15 seconds
    
    # 6. Check collected data
    print("\n6. Checking collected data...")
    try:
        response = requests.get(f"{base_url}/data/stats")
        if response.status_code == 200:
            stats = response.json()
            print("✅ Data statistics retrieved")
            print(f"   Raw data entries: {stats['stats']['total_raw_data']}")
            print(f"   Entities: {stats['stats']['total_entities']}")
            print(f"   Relationships: {stats['stats']['total_relationships']}")
            print(f"   Last 24h: {stats['stats']['last_24h']}")
        else:
            print(f"❌ Failed to get data stats: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting data stats: {e}")
    
    # 7. Check bot logs
    print("\n7. Checking bot logs...")
    try:
        response = requests.get(f"{base_url}/bot-logs")
        if response.status_code == 200:
            logs = response.json()
            print(f"✅ Found {len(logs['logs'])} bot log entries")
            for log in logs['logs'][-3:]:  # Show last 3 logs
                print(f"   [{log['timestamp']}] {log['bot_name']}: {log['message']}")
        else:
            print(f"❌ Failed to get bot logs: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting bot logs: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test completed!")
    print("\nNext steps:")
    print("1. Open http://127.0.0.1:5000/admin/bots to see the full interface")
    print("2. Check the 'Collected Data' tab for detailed results")
    print("3. View bot logs for detailed activity")

if __name__ == "__main__":
    test_data_collection()
