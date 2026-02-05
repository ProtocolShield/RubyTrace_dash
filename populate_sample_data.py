#!/usr/bin/env python3
"""
Populate sample data for testing the user dashboard overview section
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import db, RawData, CVEItem, DataSource, Bot
from config import DATABASE_URL

def create_sample_data():
    """Create sample data for dashboard testing"""

    # Create sample data sources if they don't exist
    sources = [
        {'name': 'HackerNews', 'url': 'https://news.ycombinator.com/', 'source_type': 'surface', 'category': 'news', 'risk_level': 'low'},
        {'name': 'Reddit Privacy', 'url': 'https://reddit.com/r/privacy', 'source_type': 'surface', 'category': 'forum', 'risk_level': 'medium'},
        {'name': 'Surface News Feed', 'url': 'https://news.example.com/', 'source_type': 'surface', 'category': 'news', 'risk_level': 'low'},
        {'name': 'Deep Web Forum', 'url': 'http://deepforum.example.onion', 'source_type': 'deep', 'category': 'forum', 'risk_level': 'high'},
        {'name': 'Dark Web Marketplace', 'url': 'http://darkmarket.example.onion', 'source_type': 'dark', 'category': 'market', 'risk_level': 'critical'},
        {'name': 'NIST NVD', 'url': 'https://nvd.nist.gov/vuln/full-listing', 'source_type': 'osint', 'category': 'cve', 'risk_level': 'medium'},
        {'name': 'CVE Database', 'url': 'https://cve.mitre.org/', 'source_type': 'osint', 'category': 'cve', 'risk_level': 'medium'},
    ]

    for source_data in sources:
        source = DataSource.query.filter_by(name=source_data['name']).first()
        if not source:
            source = DataSource(**source_data)
            db.session.add(source)
            print(f"Created source: {source.name}")

    # Create sample bot if it doesn't exist
    bot = Bot.query.filter_by(name='Test Bot').first()
    if not bot:
        bot = Bot(name='Test Bot', bot_type='surface', status='running')
        db.session.add(bot)
        print("Created test bot")

    db.session.commit()

    # Get sources and bot
    sources = DataSource.query.all()
    bot = Bot.query.first()

    # Create sample RawData entries
    sample_titles = [
        "New Privacy Breach at Major Tech Company",
        "Critical Security Vulnerability in Popular Software",
        "Data Leak Exposes Millions of User Records",
        "Hacking Tools Found on Dark Web Marketplace",
        "Government Surveillance Program Revealed",
        "Zero-Day Exploit Discovered in Web Browser",
        "Cryptocurrency Exchange Hacked",
        "Malware Campaign Targets Financial Institutions",
        "Social Engineering Attack Bypasses Security",
        "Insider Threat Leads to Data Compromise",
        "Ransomware Attack Encrypts Corporate Network",
        "Supply Chain Attack Compromises Software Updates",
        "Phishing Campaign Steals Credentials",
        "IoT Device Vulnerability Exploited",
        "Cloud Storage Misconfiguration Exposed Data",
        "API Key Leak in Public Repository",
        "SQL Injection Vulnerability Found",
        "Cross-Site Scripting in Web Application",
        "Buffer Overflow in Legacy Software",
        "Man-in-the-Middle Attack Intercepts Traffic"
    ]

    sample_urls = [
        "https://news.example.com/privacy-breach",
        "https://security.example.com/vulnerability",
        "https://leak.example.com/data-exposure",
        "https://darkweb.example.com/tools",
        "https://surveillance.example.com/government",
        "https://exploit.example.com/browser-zero-day",
        "https://crypto.example.com/exchange-hack",
        "https://malware.example.com/financial-targets",
        "https://social.example.com/engineering-attack",
        "https://insider.example.com/threat-compromise",
        "https://ransomware.example.com/network-encryption",
        "https://supply.example.com/chain-attack",
        "https://phishing.example.com/credential-theft",
        "https://iot.example.com/device-vulnerability",
        "https://cloud.example.com/storage-misconfig",
        "https://api.example.com/key-leak",
        "https://sql.example.com/injection-vuln",
        "https://xss.example.com/web-app-vuln",
        "https://buffer.example.com/overflow-legacy",
        "https://mitm.example.com/traffic-intercept"
    ]

    # Create 100 sample RawData entries over the last 30 days
    for i in range(100):
        days_ago = random.randint(0, 30)
        created_at = datetime.utcnow() - timedelta(days=days_ago, hours=random.randint(0, 23))

        source = random.choice(sources)
        title = random.choice(sample_titles)
        url = random.choice(sample_urls)
        risk_score = random.uniform(1.0, 10.0)

        content = f"This is sample content for {title}. Risk score: {risk_score:.1f}. Created {days_ago} days ago."

        raw_data = RawData(
            source_id=source.id,
            bot_id=bot.id if bot else None,
            url=url,
            title=title,
            content=content,
            risk_score=risk_score,
            created_at=created_at
        )

        db.session.add(raw_data)

    print("Created 100 sample RawData entries")

    # Create sample CVE entries
    cve_titles = [
        "Remote Code Execution in Web Framework",
        "SQL Injection in Database Driver",
        "Buffer Overflow in Network Library",
        "Cross-Site Scripting in CMS",
        "Privilege Escalation in OS Kernel",
        "Denial of Service in HTTP Server",
        "Information Disclosure in API",
        "Authentication Bypass in Login System",
        "Directory Traversal in File Upload",
        "Command Injection in Shell Interface"
    ]

    severities = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

    for i in range(20):
        days_ago = random.randint(0, 30)
        published_at = datetime.utcnow() - timedelta(days=days_ago)

        cve_id = f"CVE-2024-{1000 + i:04d}"
        title = random.choice(cve_titles)
        severity = random.choice(severities)
        cvss = random.uniform(1.0, 10.0) if severity != 'LOW' else random.uniform(1.0, 4.0)

        description = f"{title} - CVSS Score: {cvss:.1f}, Severity: {severity}"

        cve = CVEItem(
            cve_id=cve_id,
            title=title,
            description=description,
            severity=severity,
            cvss=cvss,
            published_at=published_at
        )

        db.session.add(cve)

    print("Created 20 sample CVE entries")

    db.session.commit()
    print("Sample data populated successfully!")

if __name__ == "__main__":
    # Set up Flask app context for database operations
    from api import app

    with app.app_context():
        try:
            create_sample_data()
        except Exception as e:
            print(f"Error populating sample data: {e}")
            db.session.rollback()
            sys.exit(1)
