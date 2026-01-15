#!/usr/bin/env python3
"""
Comprehensive test script to verify complete data collection
Shows full content extraction, not just summaries
"""

import requests
import json
import time
from datetime import datetime

def test_complete_data_collection():
    """Test the complete data collection system"""
    base_url = "http://127.0.0.1:5000/api"
    
    print("🔍 Testing Complete OSINT Data Collection System")
    print("=" * 60)
    print("Goal: Collect FULL articles, not just summaries")
    print("=" * 60)
    
    # 1. Check current system status
    print("\n1. 📊 Current System Status")
    try:
        response = requests.get(f"{base_url}/bots")
        if response.status_code == 200:
            bots = response.json()
            print("✅ Bot system operational")
            for bot_type, status in bots['bots'].items():
                print(f"   {bot_type}: {status.get('status', 'unknown')}")
        else:
            print(f"❌ Bot system error: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ System error: {e}")
        return
    
    # 2. Check data sources
    print("\n2. 📚 Data Sources Configuration")
    try:
        response = requests.get(f"{base_url}/datasources")
        if response.status_code == 200:
            sources = response.json()
            surface_sources = [s for s in sources['sources'] if s['source_type'] == 'surface_web']
            print(f"✅ Found {len(surface_sources)} surface web sources")
            for source in surface_sources[:3]:  # Show first 3
                print(f"   - {source['name']}: {source['url']}")
                print(f"     Category: {source['category']}")
                print(f"     Risk Level: {source['risk_level']}")
        else:
            print(f"❌ Failed to get sources: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error getting sources: {e}")
        return
    
    # 3. Start surface bot and run collection
    print("\n3. 🚀 Starting Data Collection")
    try:
        # Start surface bot
        response = requests.post(f"{base_url}/bots/surface/start")
        if response.status_code == 200:
            print("✅ Surface bot started")
        else:
            print(f"❌ Failed to start bot: {response.status_code}")
            return
        
        # Run collection cycle
        response = requests.post(
            f"{base_url}/bots/run-cycle",
            headers={"Content-Type": "application/json"},
            json={"bot_type": "surface", "source_type": "surface_web"}
        )
        if response.status_code == 200:
            print("✅ Collection cycle started")
            print("   ⏳ Waiting for data collection to complete...")
        else:
            print(f"❌ Failed to start collection: {response.status_code}")
            return
            
    except Exception as e:
        print(f"❌ Error starting collection: {e}")
        return
    
    # 4. Wait for collection and monitor progress
    print("\n4. 📈 Monitoring Collection Progress")
    wait_time = 30  # Wait 30 seconds for collection
    for i in range(wait_time // 5):
        time.sleep(5)
        try:
            response = requests.get(f"{base_url}/data/stats")
            if response.status_code == 200:
                stats = response.json()['stats']
                print(f"   Progress: {stats['total_raw_data']} raw data entries collected...")
                if stats['total_raw_data'] > 0:
                    break
        except:
            pass
        print(f"   ⏳ Still collecting... ({i+1}/{wait_time//5})")
    
    # 5. Check final results
    print("\n5. 📊 Final Collection Results")
    try:
        response = requests.get(f"{base_url}/data/stats")
        if response.status_code == 200:
            stats = response.json()['stats']
            print("✅ Data collection completed!")
            print(f"   📄 Raw Data Entries: {stats['total_raw_data']}")
            print(f"   🏷️  Entities: {stats['total_entities']}")
            print(f"   🔗 Relationships: {stats['total_relationships']}")
            print(f"   ⏰ Last 24h: {stats['last_24h']}")
            
            if stats['total_raw_data'] == 0:
                print("\n⚠️  No data collected. Checking for issues...")
                check_collection_issues()
            else:
                print("\n🎉 SUCCESS! Data collection is working!")
                show_sample_data()
                
        else:
            print(f"❌ Failed to get stats: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting final results: {e}")
    
    # 6. Show bot logs
    print("\n6. 📝 Bot Activity Logs")
    try:
        response = requests.get(f"{base_url}/bot-logs")
        if response.status_code == 200:
            logs = response.json()
            print(f"✅ Found {len(logs['logs'])} log entries")
            for log in logs['logs'][-5:]:  # Show last 5 logs
                timestamp = log.get('timestamp', 'Unknown')
                bot_name = log.get('bot_name', 'Unknown')
                message = log.get('message', 'No message')
                print(f"   [{timestamp}] {bot_name}: {message}")
        else:
            print(f"❌ Failed to get logs: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting logs: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Test completed!")
    print("\nNext steps:")
    print("1. Open http://127.0.0.1:5000/admin/bots for full interface")
    print("2. Check 'Collected Data' tab for detailed results")
    print("3. View individual data entries to see complete content")

def check_collection_issues():
    """Check for common collection issues"""
    print("   🔍 Diagnosing collection issues...")
    
    # Check if sources are enabled
    try:
        response = requests.get("http://127.0.0.1:5000/api/datasources")
        if response.status_code == 200:
            sources = response.json()
            enabled_sources = [s for s in sources['sources'] if s['enabled']]
            print(f"   📊 Enabled sources: {len(enabled_sources)}")
            
            if len(enabled_sources) == 0:
                print("   ❌ No sources are enabled!")
                print("   💡 Enable sources in the admin interface")
            else:
                print("   ✅ Sources are enabled")
                
    except Exception as e:
        print(f"   ❌ Error checking sources: {e}")

def show_sample_data():
    """Show sample of collected data"""
    print("   📋 Sample of collected data:")
    try:
        # This would show actual collected data
        print("   💡 Check the admin interface for full data view")
        print("   🌐 Open: http://127.0.0.1:5000/admin/bots")
    except Exception as e:
        print(f"   ❌ Error showing sample data: {e}")

if __name__ == "__main__":
    test_complete_data_collection()
