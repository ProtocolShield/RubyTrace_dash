#!/usr/bin/env python3
"""
Add Telegram group data sources for bot collection
"""

import requests
import json
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Telegram groups data sources
TELEGRAM_SOURCES = [
    {
        "name": "Hacker News Telegram",
        "url": "https://t.me/hackernews",
        "source_type": "social_media",
        "category": "news",
        "risk_level": "medium",
        "scrape_interval": 30,
        "description": "Official Hacker News Telegram channel"
    },
    {
        "name": "Cyber Security News",
        "url": "https://t.me/cybersecuritynews",
        "source_type": "social_media", 
        "category": "news",
        "risk_level": "high",
        "scrape_interval": 30,
        "description": "Latest cybersecurity news and updates"
    },
    {
        "name": "Hackers News",
        "url": "https://t.me/hackersnews",
        "source_type": "social_media",
        "category": "news", 
        "risk_level": "high",
        "scrape_interval": 30,
        "description": "Hacking and cybersecurity news"
    },
    {
        "name": "Security Affairs",
        "url": "https://t.me/securityaffairs",
        "source_type": "social_media",
        "category": "threat_intel",
        "risk_level": "high", 
        "scrape_interval": 30,
        "description": "Security affairs and threat intelligence"
    },
    {
        "name": "Malware News",
        "url": "https://t.me/malwarenews",
        "source_type": "social_media",
        "category": "threat_intel",
        "risk_level": "critical",
        "scrape_interval": 30,
        "description": "Latest malware and threat news"
    },
    {
        "name": "Vulnerability Database",
        "url": "https://t.me/vulndb",
        "source_type": "social_media",
        "category": "vulnerability",
        "risk_level": "high",
        "scrape_interval": 30,
        "description": "Vulnerability database and CVE updates"
    },
    {
        "name": "Hacking Tools",
        "url": "https://t.me/hackingtools",
        "source_type": "social_media",
        "category": "tools",
        "risk_level": "critical",
        "scrape_interval": 30,
        "description": "Hacking tools and techniques"
    },
    {
        "name": "Penetration Testing",
        "url": "https://t.me/pentesting",
        "source_type": "social_media",
        "category": "tools",
        "risk_level": "high",
        "scrape_interval": 30,
        "description": "Penetration testing techniques and tools"
    },
    {
        "name": "Bug Bounty",
        "url": "https://t.me/bugbounty",
        "source_type": "social_media",
        "category": "vulnerability",
        "risk_level": "medium",
        "scrape_interval": 30,
        "description": "Bug bounty programs and vulnerabilities"
    },
    {
        "name": "OSINT Tools",
        "url": "https://t.me/osinttools",
        "source_type": "social_media",
        "category": "osint",
        "risk_level": "medium",
        "scrape_interval": 30,
        "description": "OSINT tools and techniques"
    },
    {
        "name": "Dark Web Monitor",
        "url": "https://t.me/darkwebmonitor",
        "source_type": "social_media",
        "category": "threat_intel",
        "risk_level": "critical",
        "scrape_interval": 30,
        "description": "Dark web monitoring and intelligence"
    },
    {
        "name": "Data Breach Alert",
        "url": "https://t.me/databreachalert",
        "source_type": "social_media",
        "category": "threat_intel",
        "risk_level": "high",
        "scrape_interval": 30,
        "description": "Data breach alerts and notifications"
    },
    {
        "name": "Ransomware Tracker",
        "url": "https://t.me/ransomwaretracker",
        "source_type": "social_media",
        "category": "threat_intel",
        "risk_level": "critical",
        "scrape_interval": 30,
        "description": "Ransomware tracking and alerts"
    },
    {
        "name": "Cryptocurrency Security",
        "url": "https://t.me/cryptosecurity",
        "source_type": "social_media",
        "category": "crypto",
        "risk_level": "high",
        "scrape_interval": 30,
        "description": "Cryptocurrency security and threats"
    },
    {
        "name": "IoT Security",
        "url": "https://t.me/iotsecurity",
        "source_type": "social_media",
        "category": "iot",
        "risk_level": "high",
        "scrape_interval": 30,
        "description": "IoT security and vulnerabilities"
    }
]

def add_telegram_sources():
    """Add Telegram group data sources to the system"""
    
    base_url = "http://127.0.0.1:5000"
    
    print("🔗 Adding Telegram Group Data Sources")
    print("=" * 50)
    
    added_count = 0
    failed_count = 0
    
    for source in TELEGRAM_SOURCES:
        try:
            print(f"Adding: {source['name']} - {source['url']}")
            
            # Prepare the data
            data = {
                "name": source["name"],
                "url": source["url"],
                "source_type": source["source_type"],
                "category": source["category"],
                "risk_level": source["risk_level"],
                "scrape_interval": source["scrape_interval"],
                "enabled": True,
                "config": {
                    "description": source["description"],
                    "platform": "telegram",
                    "requires_auth": False,
                    "public_channel": True
                }
            }
            
            # Make API request
            response = requests.post(
                f"{base_url}/api/datasources",
                json=data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print(f"✅ Successfully added: {source['name']}")
                    added_count += 1
                else:
                    print(f"❌ Failed to add {source['name']}: {result.get('error', 'Unknown error')}")
                    failed_count += 1
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                failed_count += 1
                
        except Exception as e:
            print(f"❌ Error adding {source['name']}: {e}")
            failed_count += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Summary:")
    print(f"   ✅ Successfully added: {added_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📈 Total Telegram sources: {added_count + failed_count}")
    
    if added_count > 0:
        print(f"\n🎉 Successfully added {added_count} Telegram group data sources!")
        print("The bots will now be able to collect data from these Telegram channels.")
    else:
        print("\n⚠️ No Telegram sources were added successfully.")

if __name__ == "__main__":
    add_telegram_sources()
