#!/usr/bin/env python3
"""
Script to add comprehensive test data sources for OSINT bot testing
"""

import requests
import json
import time

# Test data sources
test_sources = [
    # Surface Web Sources
    {
        "name": "Hacker News",
        "url": "https://news.ycombinator.com",
        "source_type": "surface_web",
        "category": "news",
        "keywords": "cybersecurity, hacking, data breach, vulnerability, exploit",
        "risk_level": "medium",
        "enabled": True
    },
    {
        "name": "The Hacker News",
        "url": "https://thehackernews.com",
        "source_type": "surface_web",
        "category": "news",
        "keywords": "cyber attack, malware, vulnerability, exploit, breach",
        "risk_level": "high",
        "enabled": True
    },
    {
        "name": "Bleeping Computer",
        "url": "https://www.bleepingcomputer.com",
        "source_type": "surface_web",
        "category": "news",
        "keywords": "malware, ransomware, cyber attack, security, breach",
        "risk_level": "high",
        "enabled": True
    },
    {
        "name": "TechCrunch Security",
        "url": "https://techcrunch.com/tag/security/",
        "source_type": "surface_web",
        "category": "news",
        "keywords": "security, breach, cyber attack, malware, ransomware",
        "risk_level": "medium",
        "enabled": True
    },
    
    # Deep Web Sources
    {
        "name": "Reddit r/netsec",
        "url": "https://www.reddit.com/r/netsec",
        "source_type": "deep_web",
        "category": "forum",
        "keywords": "security, vulnerability, exploit, malware, breach",
        "risk_level": "medium",
        "enabled": True
    },
    {
        "name": "Reddit r/hacking",
        "url": "https://www.reddit.com/r/hacking",
        "source_type": "deep_web",
        "category": "forum",
        "keywords": "hacking, exploit, vulnerability, malware, security",
        "risk_level": "high",
        "enabled": True
    },
    {
        "name": "GitHub Security",
        "url": "https://github.com/topics/security",
        "source_type": "deep_web",
        "category": "repository",
        "keywords": "security, vulnerability, exploit, malware, hacking",
        "risk_level": "medium",
        "enabled": True
    },
    {
        "name": "Pastebin Recent",
        "url": "https://pastebin.com/archive",
        "source_type": "deep_web",
        "category": "paste",
        "keywords": "leak, dump, password, credential, database",
        "risk_level": "high",
        "enabled": True
    },
    
    # OSINT Feed Sources
    {
        "name": "CVE Database",
        "url": "https://cve.mitre.org",
        "source_type": "osint_feed",
        "category": "vulnerability",
        "keywords": "CVE, vulnerability, exploit, security",
        "risk_level": "medium",
        "enabled": True
    },
    {
        "name": "NIST NVD",
        "url": "https://nvd.nist.gov/vuln",
        "source_type": "osint_feed",
        "category": "vulnerability",
        "keywords": "CVE, vulnerability, NVD, security",
        "risk_level": "medium",
        "enabled": True
    },
    {
        "name": "MITRE ATT&CK",
        "url": "https://attack.mitre.org",
        "source_type": "osint_feed",
        "category": "threat_intel",
        "keywords": "ATT&CK, technique, tactic, malware, threat",
        "risk_level": "medium",
        "enabled": True
    }
]

def add_test_sources():
    """Add all test sources to the system"""
    base_url = "http://127.0.0.1:5000/api"
    
    print("Adding test data sources...")
    
    for i, source in enumerate(test_sources, 1):
        try:
            response = requests.post(
                f"{base_url}/datasources",
                headers={"Content-Type": "application/json"},
                json=source
            )
            
            if response.status_code == 200:
                print(f"✅ {i}. Added: {source['name']} ({source['source_type']})")
            else:
                print(f"❌ {i}. Failed to add {source['name']}: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ {i}. Error adding {source['name']}: {str(e)}")
        
        time.sleep(0.5)  # Small delay between requests
    
    print("\n" + "="*50)
    print("Test sources added! Now you can:")
    print("1. Go to http://127.0.0.1:5000/admin/bots")
    print("2. Start the Surface Web bot")
    print("3. Click 'Run Cycle' to test data collection")
    print("4. Check the 'Collected Data' tab for results")

if __name__ == "__main__":
    add_test_sources()
