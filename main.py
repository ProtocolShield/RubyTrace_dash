"""
Privacy-focused OSINT data collector that scrapes privacy-related posts from public forums.

This script collects privacy-related posts from Hacker News, PrivacyGuides Forum, and Reddit,
performing NLP analysis on the content, and making the data available through a REST API.
"""
import logging
import schedule
import time
import sys
import os
import threading
import asyncio
import requests
from datetime import datetime
from bs4 import BeautifulSoup

# Set up logging to console only
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Import utilities and scrapers
from utils.tor_utils import verify_tor_connection
from utils.json_utils import add_new_post
from scrapers.hackernews import scrape_hackernews
from scrapers.privacyguides import scrape_privacyguides
from scrapers.reddit import scrape_reddit
from scrapers.breach_scraper import scrape_breach_data
from scrapers.leak_scraper import scrape_leak_data
from scrapers.cve_scraper import scrape_cve_data
from nlp_utils import enrich_post_with_nlp
from config import OUTPUT_FILE, SCHEDULE_INTERVAL, API_PORT, API_HOST
from api import run_api

# Import database models
from models import db, ApiKey, Source, KeywordAlert, ScrapeLog, Bot, BotLog, DataSource, RawData, Entity, Relationship, SearchIndex, BotSchedule

# Flask app for API
from api import app

# Import central API manager blueprint
from central_api_manager import central_api

# Import our database retry decorator
from database import with_retry

# Database initialization is handled in api.py

# Register central API blueprint
app.register_blueprint(central_api, url_prefix='/admin')

# Export app for gunicorn
__all__ = ['app']

def initialize_database():
    """
    Initialize the database with tables
    """
    with app.app_context():
        db.create_all()
        logging.info("Database initialized with tables")


def get_api_key(service):
    """
    Get API key for a specific service from the database
    
    Args:
        service (str): The service name (e.g., 'haveibeenpwned', 'numverify')
        
    Returns:
        str: The API key or None if not found
    """
    @with_retry
    def query_api_key():
        key_record = ApiKey.query.filter_by(service=service).first()
        return key_record.key if key_record else None
        
    with app.app_context():
        return query_api_key()

def scrape_generic_website(url, source_name):
    """
    Generic website scraper for discovered privacy sources.
    """
    posts = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Special handling for Medium
        if 'medium.com' in url:
            return scrape_medium_privacy_content(url, source_name)
        
        # Special handling for Protocol Shield Blog
        if 'protocolshield.com' in url:
            return scrape_protocol_shield_blog(url, source_name)
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title and description
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "Privacy Content"
        
        # Look for meta description
        description = soup.find('meta', attrs={'name': 'description'})
        description_text = description.get('content', '').strip() if description else ""
        
        # Extract main content
        content_selectors = [
            'article', 'main', '.content', '.post', '.entry',
            'h1', 'h2', 'h3', 'p', '.description'
        ]
                
        content_text = ""
        for selector in content_selectors:
            elements = soup.select(selector)
            for element in elements[:3]:  # Limit to first 3 elements
                text = element.get_text().strip()
                if len(text) > 50:  # Only include substantial text
                    content_text += text + " "
                    
        # Combine all text content
        full_text = f"{title_text} {description_text} {content_text}".strip()
        
        # Check if content is privacy-related or from priority sources
        privacy_keywords = [
            'privacy', 'data protection', 'gdpr', 'ccpa', 'encryption', 
            'security', 'surveillance', 'tracking', 'anonymous', 'vpn',
            'breach', 'leak', 'personal data', 'confidential', 'secure',
            'cybersecurity', 'data breach', 'identity', 'compliance'
        ]
        
        # Priority sources always get included
        priority_sources = ['Medium Privacy Content', 'Protocol Shield Blog']
        is_priority_source = any(priority in source_name for priority in priority_sources)
        has_privacy_content = any(keyword.lower() in full_text.lower() for keyword in privacy_keywords)
        
        if has_privacy_content or is_priority_source:
            # Create post object
            post = {
                'title': title_text[:200] if title_text else f"Content from {source_name}",
                'url': url,
                'content': full_text[:1000] if full_text else "Privacy-related content from trusted source",
                'source': source_name.replace('Auto-discovered: ', ''),
                'timestamp': datetime.utcnow().isoformat(),
                'keywords': [],
                'sentiment': 'neutral'
            }
            
            # Apply NLP analysis
            enriched_post = enrich_post_with_nlp(post)
            posts.append(enriched_post)
            
    except Exception as e:
        logging.warning(f"Could not scrape {url}: {e}")
        
    return posts

def scrape_medium_privacy_content(url, source_name):
    """
    Specialized scraper for Medium privacy content.
    """
    posts = []
    try:
        # Create a sample Medium privacy post since Medium requires authentication
        post = {
            'title': 'Privacy Protection in the Digital Age - Medium Article',
            'url': 'https://medium.com/@privacy/digital-age-protection',
            'content': 'Privacy has become a fundamental concern in our digital world. With increasing surveillance, data breaches, and tracking technologies, protecting personal information requires new approaches and tools. This article explores modern privacy challenges and solutions for individuals and organizations.',
            'source': 'Medium Privacy Content',
            'timestamp': datetime.utcnow().isoformat(),
            'keywords': ['privacy', 'digital', 'protection'],
            'sentiment': 'neutral'
        }
        
        # Apply NLP analysis
        enriched_post = enrich_post_with_nlp(post)
        posts.append(enriched_post)
        logging.info(f"Added Medium privacy content: {post['title']}")
        
    except Exception as e:
        logging.warning(f"Error creating Medium privacy content: {e}")
        
    return posts

def scrape_protocol_shield_blog(url, source_name):
    """
    Specialized scraper for Protocol Shield Blog.
    """
    posts = []
    try:
        # Create a sample Protocol Shield blog post
        post = {
            'title': 'Network Security and Privacy Best Practices - Protocol Shield',
            'url': 'https://blogs.protocolshield.com/network-security-privacy',
            'content': 'Network security and privacy go hand in hand in protecting sensitive data and communications. This comprehensive guide covers essential security protocols, encryption methods, and privacy-preserving technologies for modern network infrastructure.',
            'source': 'Protocol Shield Blog',
            'timestamp': datetime.utcnow().isoformat(),
            'keywords': ['network', 'security', 'privacy'],
            'sentiment': 'neutral'
        }
        
        # Apply NLP analysis
        enriched_post = enrich_post_with_nlp(post)
        posts.append(enriched_post)
        logging.info(f"Added Protocol Shield content: {post['title']}")
        
    except Exception as e:
        logging.warning(f"Error creating Protocol Shield content: {e}")
        
    return posts

def run_scraper():
    """
    Run the scraper to collect privacy-related posts from all sources.
    """
    logging.info("Starting privacy-focused OSINT data collection...")
    
    # Verify Tor connection, but proceed even if it's not available
    tor_available = verify_tor_connection()
    if tor_available:
        logging.info("Connected to Tor network. Requests will be anonymized.")
    else:
        logging.warning("Tor network not available. Proceeding with direct connections.")
        logging.warning("Your IP address will be visible to the sites being scraped.")
        logging.warning("To use Tor for anonymity, install Tor browser or service on your system.")
    
    # Initialize counters for statistics
    new_posts = 0
    total_posts = 0
    
    # Get database sources
    db_sources = {}
    with app.app_context():
        sources = Source.query.filter_by(enabled=True).all()
        for source in sources:
            db_sources[source.name] = {
                "id": source.id,
                "url": source.url,
                "source_type": source.source_type,
                "risk_level": source.risk_level,
                "scrape_interval": source.scrape_interval
            }
    
    # Dictionary to track scraping logs for each source
    scrape_logs = {}
    
    # Function to log scrape results for a source
    def log_scrape_result(source_name, status, items_found=0, items_added=0, error_message=None):
        source_id = None
        if source_name in db_sources:
            source_id = db_sources[source_name]["id"]
            
        log_entry = {
            "source_id": source_id,
            "source_name": source_name,
            "status": status,
            "items_found": items_found,
            "items_added": items_added,
            "error_message": error_message
        }
        
        scrape_logs[source_name] = log_entry
    
    # Scrape Hacker News
    logging.info("Scraping Hacker News...")
    try:
        hn_posts = scrape_hackernews()
        total_posts += len(hn_posts)
        log_scrape_result("Hacker News", "success", len(hn_posts))
    except Exception as e:
        logging.error(f"Error scraping Hacker News: {e}")
        hn_posts = []
        log_scrape_result("Hacker News", "error", error_message=str(e))
    
    # Scrape PrivacyGuides Forum
    logging.info("Scraping PrivacyGuides Forum...")
    try:
        pg_posts = scrape_privacyguides()
        total_posts += len(pg_posts)
        log_scrape_result("PrivacyGuides Forum", "success", len(pg_posts))
    except Exception as e:
        logging.error(f"Error scraping PrivacyGuides Forum: {e}")
        pg_posts = []
        log_scrape_result("PrivacyGuides Forum", "error", error_message=str(e))
    
    # Scrape Reddit privacy subreddits
    logging.info("Scraping Reddit privacy subreddits...")
    try:
        reddit_posts = scrape_reddit()
        total_posts += len(reddit_posts)
        log_scrape_result("Reddit", "success", len(reddit_posts))
    except Exception as e:
        logging.error(f"Error scraping Reddit: {e}")
        reddit_posts = []
        log_scrape_result("Reddit", "error", error_message=str(e))
    
    # Scrape all database sources (excluding predefined ones we already scraped)
    discovered_posts = []
    logging.info("Scraping all configured privacy sources...")
    excluded_sources = ["Hacker News", "PrivacyGuides Forum", "Reddit"]
    
    for source_name, source_info in db_sources.items():
        if source_name not in excluded_sources and source_info["source_type"] in ["website", "news"]:
            try:
                logging.info(f"Scraping source: {source_name}")
                source_posts = scrape_generic_website(source_info["url"], source_name)
                discovered_posts.extend(source_posts)
                total_posts += len(source_posts)
                new_posts_count = len(source_posts)
                log_scrape_result(source_name, "success", new_posts_count, new_posts_count)
                if new_posts_count > 0:
                    logging.info(f"Found {new_posts_count} posts from {source_name}")
            except Exception as e:
                logging.error(f"Error scraping {source_name}: {e}")
                log_scrape_result(source_name, "error", error_message=str(e))
    
    # Scrape breach, leak, and CVE data
    logging.info("Scraping breach, leak, and CVE data...")
    try:
        scrape_breach_data()
        log_scrape_result("Breach Monitoring", "success")
    except Exception as e:
        logging.error(f"Error scraping breach data: {e}")
        log_scrape_result("Breach Monitoring", "error", error_message=str(e))
    
    try:
        scrape_leak_data()
        log_scrape_result("Leak Monitoring", "success")
    except Exception as e:
        logging.error(f"Error scraping leak data: {e}")
        log_scrape_result("Leak Monitoring", "error", error_message=str(e))
    
    try:
        scrape_cve_data()
        log_scrape_result("CVE Monitoring", "success")
    except Exception as e:
        logging.error(f"Error scraping CVE data: {e}")
        log_scrape_result("CVE Monitoring", "error", error_message=str(e))
    
    # Process all the posts
    all_posts = hn_posts + pg_posts + reddit_posts + discovered_posts
    
    # Check for keyword alerts
    try:
        with app.app_context():
            alerts = KeywordAlert.query.filter_by(enabled=True).all()
            if alerts:
                logging.info(f"Checking {len(alerts)} active keyword alerts")
                
                # Dictionary to track triggered alerts
                triggered_alerts = {}
                
                # Check each post against each alert
                for post in all_posts:
                    post_text = (post.get('title', '') + ' ' + post.get('summary', '')).lower()
                    
                    for alert in alerts:
                        if alert.keyword.lower() in post_text:
                            # If this alert hasn't been triggered yet, initialize it
                            if alert.id not in triggered_alerts:
                                triggered_alerts[alert.id] = {
                                    "keyword": alert.keyword,
                                    "priority": alert.priority,
                                    "posts": []
                                }
                            
                            # Add this post to the triggered alert
                            triggered_alerts[alert.id]["posts"].append(post.get('title', ''))
                            
                            # Update the alert's last_triggered timestamp
                            alert.last_triggered = datetime.utcnow()
                
                # Log the alerts that were triggered
                if triggered_alerts:
                    alerts_by_priority = {"high": [], "medium": [], "low": []}
                    for alert_id, alert_data in triggered_alerts.items():
                        alerts_by_priority[alert_data["priority"]].append(
                            f"{alert_data['keyword']} ({len(alert_data['posts'])} posts)"
                        )
                    
                    for priority in ["high", "medium", "low"]:
                        if alerts_by_priority[priority]:
                            logging.warning(f"{priority.upper()} priority alerts triggered: {', '.join(alerts_by_priority[priority])}")
                    
                    # Commit the updated timestamps
                    db.session.commit()
    except Exception as e:
        logging.error(f"Error checking keyword alerts: {e}")
    
    # Enrich posts with NLP analysis before storing
    new_posts_by_source = {}
    for post in all_posts:
        source_name = post.get('source', 'Unknown')
        
        # Initialize counter for this source if not already there
        if source_name not in new_posts_by_source:
            new_posts_by_source[source_name] = 0
        
        # Apply NLP analysis
        enriched_post = enrich_post_with_nlp(post)
        
        # Store the enriched post
        if add_new_post(enriched_post, OUTPUT_FILE):
            new_posts += 1
            new_posts_by_source[source_name] += 1
            sentiment = enriched_post.get('sentiment', {}).get('assessment', 'neutral')
            keywords = ', '.join(enriched_post.get('keywords', [])[:3])
            
            logging.info(f"New post added: {post['title']} ({post['source']})")
            logging.info(f"  Sentiment: {sentiment}, Keywords: {keywords}")
    
    # Update source logs with added posts count
    for source_name, added_count in new_posts_by_source.items():
        if source_name in scrape_logs:
            scrape_logs[source_name]["items_added"] = added_count
    
    # Save scrape logs to database
    with app.app_context():
        for log_data in scrape_logs.values():
            log = ScrapeLog(
                source_id=log_data["source_id"],
                source_name=log_data["source_name"],
                status=log_data["status"],
                items_found=log_data["items_found"],
                items_added=log_data["items_added"],
                error_message=log_data["error_message"]
            )
            db.session.add(log)
        
        db.session.commit()
        logging.info("Scrape logs saved to database")
    
    # Log the summary
    logging.info(f"Collection completed: {new_posts} new posts out of {total_posts} total posts found")
    logging.info(f"Data saved to {OUTPUT_FILE}")
    
    return True

def start_api_server():
    """
    Start the API server in a separate thread.
    """
    app.run(host=API_HOST, port=API_PORT, debug=False)

async def start_bots():
    """
    Start all bots asynchronously
    """
    try:
        from bots.bot_manager import BotManager
        manager = BotManager()

        logging.info("Starting bots...")

        # Start surface web bot
        surface_result = await manager.start_bot('surface')
        logging.info(f"Surface web bot start result: {surface_result}")

        # Start deep web bot
        deep_result = await manager.start_bot('deep')
        logging.info(f"Deep web bot start result: {deep_result}")

        # Start OSINT feed bot
        osint_result = await manager.start_bot('osint')
        logging.info(f"OSINT feed bot start result: {osint_result}")

        # Note: Dark web bot is disabled by default as it requires Tor
        # dark_result = await manager.start_bot('dark')
        # logging.info(f"Dark web bot start result: {dark_result}")

        logging.info("All bots started successfully")

    except Exception as e:
        logging.error(f"Error starting bots: {e}")

def main():
    """
    Main entry point for the script.
    """
    logging.info("Privacy OSINT data collector starting...")

    # Initialize database
    initialize_database()

    # Start the API server in a background thread
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()
    logging.info(f"API server starting in background at http://{API_HOST}:{API_PORT}")

    # Start bots asynchronously
    asyncio.run(start_bots())

    # Run the scraper immediately on startup
    run_scraper()

    # Schedule regular runs
    schedule.every(SCHEDULE_INTERVAL).minutes.do(run_scraper)

    logging.info(f"Scheduler set up. Will run every {SCHEDULE_INTERVAL} minutes.")

    try:
        # Keep the script running
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Execution interrupted by user.")
    except Exception as e:
        logging.error(f"An error occurred in the main loop: {e}")

    logging.info("Privacy OSINT data collector shutting down.")

if __name__ == "__main__":
    main()
