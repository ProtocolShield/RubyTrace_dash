#!/usr/bin/env python3
"""
Debug script to test data collection pipeline step by step
"""

import requests
import json
import time

def debug_data_collection():
    """Debug the data collection pipeline"""
    base_url = "http://127.0.0.1:5000/api"
    
    print("🔍 Debugging OSINT Data Collection Pipeline")
    print("=" * 50)
    
    # 1. Test a simple data collection from Hacker News
    print("\n1. 🧪 Testing Simple Data Collection")
    
    try:
        # Start surface bot
        response = requests.post(f"{base_url}/bots/surface/start")
        if response.status_code == 200:
            print("✅ Surface bot started")
        else:
            print(f"❌ Failed to start bot: {response.status_code}")
            return
        
        # Run a quick collection cycle
        response = requests.post(
            f"{base_url}/bots/run-cycle",
            headers={"Content-Type": "application/json"},
            json={"bot_type": "surface", "source_type": "surface_web"}
        )
        if response.status_code == 200:
            print("✅ Collection cycle started")
        else:
            print(f"❌ Failed to start collection: {response.status_code}")
            return
        
        # Wait for collection
        print("   ⏳ Waiting 10 seconds for collection...")
        time.sleep(10)
        
        # Check results
        response = requests.get(f"{base_url}/data/stats")
        if response.status_code == 200:
            stats = response.json()['stats']
            print(f"   📊 Results: {stats['total_raw_data']} raw data entries")
            
            if stats['total_raw_data'] > 0:
                print("   🎉 SUCCESS! Data is being collected and stored!")
            else:
                print("   ⚠️  Still 0 entries. Checking for processing issues...")
                check_processing_issues()
        else:
            print(f"   ❌ Failed to get stats: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")
    
    # 2. Check bot logs for detailed information
    print("\n2. 📝 Checking Bot Logs")
    try:
        response = requests.get(f"{base_url}/bot-logs")
        if response.status_code == 200:
            logs = response.json()
            recent_logs = logs['logs'][-3:]  # Last 3 logs
            print(f"   Found {len(logs['logs'])} total log entries")
            
            for log in recent_logs:
                timestamp = log.get('timestamp', 'Unknown')
                bot_name = log.get('bot_name', 'Unknown')
                message = log.get('message', 'No message')
                data_collected = log.get('data_collected', 0)
                print(f"   [{timestamp}] {bot_name}: {message} (Data: {data_collected})")
        else:
            print(f"   ❌ Failed to get logs: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error getting logs: {e}")
    
    # 3. Check data sources status
    print("\n3. 📚 Checking Data Sources")
    try:
        response = requests.get(f"{base_url}/datasources")
        if response.status_code == 200:
            sources = response.json()
            surface_sources = [s for s in sources['sources'] if s['source_type'] == 'surface_web']
            print(f"   Found {len(surface_sources)} surface web sources")
            
            for source in surface_sources:
                last_scraped = source.get('last_scraped', 'Never')
                print(f"   - {source['name']}: Last scraped: {last_scraped}")
        else:
            print(f"   ❌ Failed to get sources: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error getting sources: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Debug completed!")
    print("\nIf data collection is still 0, the issue might be:")
    print("1. Content filtering too strict")
    print("2. Data processing pipeline broken")
    print("3. Database storage issues")
    print("4. Network/accessibility issues")

def check_processing_issues():
    """Check for data processing issues"""
    print("   🔍 Checking processing pipeline...")
    
    # Check if RawData table has any entries
    try:
        # This would check the database directly
        print("   💡 Check the admin interface for detailed debugging")
        print("   🌐 Open: http://127.0.0.1:5000/admin/bots")
    except Exception as e:
        print(f"   ❌ Error checking processing: {e}")

if __name__ == "__main__":
    debug_data_collection()
