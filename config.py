"""
Configuration settings for the OSINT data collector.
"""
import os

# Tor SOCKS5 proxy settings
TOR_PROXY_HOST = "127.0.0.1"
TOR_PROXY_PORT = 9050

# Sources to scrape
SOURCES = {
    "hackernews": {
        "name": "Hacker News",
        "url": "https://news.ycombinator.com/",
        "newest_url": "https://news.ycombinator.com/newest",
        "type": "hackernews"
    },
    "privacyguides": {
        "name": "PrivacyGuides Forum",
        "url": "https://discuss.privacyguides.org/c/privacy-news/11",
        "type": "privacyguides"
    }
}

# Reddit subreddits - can be modified through API
REDDIT_SUBREDDITS = [
    "privacy", 
    "privacytoolsIO", 
    "cybersecurity", 
    "netsec",
    "opsec", 
    "encryption"
]

# File to store source configuration
SOURCES_CONFIG_FILE = "sources_config.json"

# Privacy-related keywords for filtering
PRIVACY_KEYWORDS = [
    "privacy", "security", "leak", "breach", "surveillance", 
    "tracking", "tor", "vpn", "encryption", "crypto", 
    "anonymity", "metadata", "data collection", "gdpr", 
    "ccpa", "duckduckgo", "firefox", "brave", "signal",
    "protonmail", "tutanota", "e2e", "end-to-end", "backdoor",
    "zero-knowledge", "zero-trust", "fingerprinting", "telemetry"
]

# Output JSON file
OUTPUT_FILE = "data.json"

# Schedule settings (in minutes)
SCHEDULE_INTERVAL = 30

# Reddit API settings
REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.environ.get("REDDIT_USER_AGENT", "OSINT Privacy Collector (by /u/privacy_researcher)")

# API settings
API_PORT = 5000
API_HOST = "127.0.0.1"

# NLP settings
NLTK_DATA_PATH = "nltk_data"
ENABLE_SENTIMENT_ANALYSIS = True

# Production settings
PRODUCTION = os.environ.get('FLASK_ENV') == 'production'

# Tor settings
TOR_ENABLED = os.environ.get('TOR_ENABLED', 'false').lower() == 'true'
TOR_SOCKS_PORT = int(os.environ.get('TOR_SOCKS_PORT', 9050))
TOR_CONTROL_PORT = int(os.environ.get('TOR_CONTROL_PORT', 9051))

# Security settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# Database settings
DATABASE_URL = os.environ.get('DATABASE_URL')

# API settings
API_HOST = os.environ.get('API_HOST', '127.0.0.1')
API_PORT = int(os.environ.get('API_PORT', 5000))

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
UPLOADS_DIR = os.path.join(BASE_DIR, 'uploads')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Create directories if they don't exist
for directory in [STATIC_DIR, TEMPLATES_DIR, UPLOADS_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)
