"""
Scraper for PrivacyGuides Forum.
"""
import logging
from bs4 import BeautifulSoup
from datetime import datetime
import re
from utils.tor_utils import fetch_with_tor
from config import SOURCES, PRIVACY_KEYWORDS

def scrape_privacyguides():
    """
    Scrape privacy-related posts from PrivacyGuides Forum.
    
    Returns:
        list: List of posts matching the privacy keywords
    """
    posts = []
    
    # Get the source configuration
    source_config = SOURCES['privacyguides']
    url = source_config['url']
    
    html = fetch_with_tor(url)
    if not html:
        logging.error(f"Failed to fetch {url}")
        return posts
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Find all topic rows
    topics = soup.select('.topic-list-item')
    
    for topic in topics:
        # Extract title and link
        title_elem = topic.select_one('.title a')
        if not title_elem:
            continue
        
        title = title_elem.get_text(strip=True)
        
        # All posts on PrivacyGuides Forum are privacy-related, but
        # we'll still apply the keyword filtering for consistency
        if not any(keyword.lower() in title.lower() for keyword in PRIVACY_KEYWORDS):
            # Check the category to see if it's definitely privacy-related
            category = topic.select_one('.category-name')
            if category and any(keyword.lower() in category.get_text(strip=True).lower() 
                              for keyword in ["privacy", "security"]):
                # It's in a privacy category, so include it
                pass
            else:
                # If title and category don't match keywords, skip this post
                continue
        
        # Get the relative URL
        relative_url = title_elem.get('href', '')
        if not relative_url:
            continue
            
        # Make it an absolute URL
        if relative_url.startswith('/'):
            post_url = f"https://discuss.privacyguides.org{relative_url}"
        else:
            post_url = f"https://discuss.privacyguides.org/{relative_url}"
        
        # Extract timestamp
        timestamp_elem = topic.select_one('.relative-date')
        timestamp = None
        if timestamp_elem and 'data-time' in timestamp_elem.attrs:
            try:
                timestamp_seconds = int(timestamp_elem['data-time']) / 1000
                timestamp = datetime.utcfromtimestamp(timestamp_seconds).strftime('%Y-%m-%dT%H:%M:%SZ')
            except (ValueError, TypeError):
                pass
        
        if not timestamp:
            timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        # Fetch the post page to get a summary
        post_html = fetch_with_tor(post_url)
        summary = "No summary available"
        
        if post_html:
            post_soup = BeautifulSoup(post_html, 'html.parser')
            content_elem = post_soup.select_one('.topic-body .cooked')
            if content_elem:
                content = content_elem.get_text(strip=True)
                # Get the first 200 characters as a summary
                summary = content[:200] + ('...' if len(content) > 200 else '')
        
        # Add to our posts list
        post = {
            "source": source_config['name'],
            "timestamp": timestamp,
            "url": post_url,
            "title": title,
            "summary": summary
        }
        
        posts.append(post)
        logging.info(f"Found privacy-related post on PrivacyGuides Forum: {title}")
    
    return posts
