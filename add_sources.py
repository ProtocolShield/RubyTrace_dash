import requests
import json

# Add example data sources
sources = [
    {
        "name": "Hacker News",
        "url": "https://news.ycombinator.com",
        "source_type": "surface",
        "category": "news",
        "risk_level": "low",
        "enabled": True,
        "scrape_interval": 30
    },
    {
        "name": "Reddit Cybersecurity",
        "url": "https://www.reddit.com/r/cybersecurity/",
        "source_type": "deep",
        "category": "forum",
        "risk_level": "medium",
        "enabled": True,
        "scrape_interval": 60
    },
    {
        "name": "NIST Vulnerability Feed",
        "url": "https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json",
        "source_type": "osint",
        "category": "vulnerability",
        "risk_level": "medium",
        "enabled": True,
        "scrape_interval": 60
    }
]

base_url = "http://127.0.0.1:5000/api/datasources"

for source in sources:
    try:
        response = requests.post(base_url, json=source)
        if response.status_code == 200:
            print(f"✅ Added: {source['name']}")
        else:
            print(f"❌ Failed to add {source['name']}: {response.status_code}")
    except Exception as e:
        print(f"❌ Error adding {source['name']}: {e}")
