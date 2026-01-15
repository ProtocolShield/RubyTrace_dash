"""
Scraper for Hacker News.
"""
import logging
from bs4 import BeautifulSoup
from datetime import datetime
import re
from utils.tor_utils import fetch_with_tor
from config import SOURCES, PRIVACY_KEYWORDS

def extract_hn_timestamp(item_id):
    """
    Fetch the timestamp for a Hacker News post by its item ID.
    
    Args:
        item_id (str): The Hacker News item ID
    
    Returns:
        str: ISO-formatted timestamp or None if unable to determine
    """
    item_url = f"https://news.ycombinator.com/item?id={item_id}"
    html = fetch_with_tor(item_url)
    
    if not html:
        return None
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Try to find the timestamp from the page
    timestamp_elem = soup.select_one('.age')
    if timestamp_elem and 'title' in timestamp_elem.attrs:
        # The title attribute contains the ISO timestamp
        return timestamp_elem['title']
    
    # Fallback to current time if we couldn't find it
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

def extract_hn_summary(item_id):
    """
    Extract a summary from the Hacker News post.
    
    Args:
        item_id (str): The Hacker News item ID
    
    Returns:
        str: Summary text or None if unable to determine
    """
    item_url = f"https://news.ycombinator.com/item?id={item_id}"
    html = fetch_with_tor(item_url)
    
    if not html:
        return None
    
    soup = BeautifulSoup(html, 'html.parser')
    
    # Check if it's a text post
    text_elem = soup.select_one('.toptext')
    if text_elem:
        text = text_elem.get_text(strip=True)
        # Return the first 200 characters as a summary
        return text[:200] + ('...' if len(text) > 200 else '')
    
    # Check if it's a link to an article
    link = soup.select_one('.titleline a')
    if link and 'href' in link.attrs:
        article_url = link['href']
        # Only proceed if it's a full URL
        if article_url.startswith('http'):
            article_html = fetch_with_tor(article_url)
            if article_html:
                article_soup = BeautifulSoup(article_html, 'html.parser')
                # Try to find the description from meta tags
                description = None
                meta_desc = article_soup.select_one('meta[name="description"]')
                if meta_desc and 'content' in meta_desc.attrs:
                    description = meta_desc['content']
                
                # If no meta description, try to get the first paragraph
                if not description:
                    first_p = article_soup.select_one('p')
                    if first_p:
                        description = first_p.get_text(strip=True)
                
                if description:
                    return description[:200] + ('...' if len(description) > 200 else '')
    
    # If we couldn't get a summary, return the first comments as a fallback
    comments = soup.select('.commtext')
    if comments:
        return comments[0].get_text(strip=True)[:200] + '...'
    
    return "No summary available"

def scrape_hackernews():
    """
    Scrape privacy-related posts from Hacker News.
    
    Returns:
        list: List of posts matching the privacy keywords
    """
    posts = []
    
    # Get the source configuration
    source_config = SOURCES['hackernews']
    
    # Scrape both the front page and newest page for more coverage
    urls = [source_config['url'], source_config['newest_url']]
    
    for url in urls:
        html = fetch_with_tor(url)
        if not html:
            logging.error(f"Failed to fetch {url}")
            continue
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all story rows (each post has 3 rows: title, spacer, info)
        stories = soup.select('tr.athing')
        
        for story in stories:
            story_id = story.get('id')
            if not story_id:
                continue
                
            # Extract the title and link
            title_elem = story.select_one('.titleline a')
            if not title_elem:
                continue
                
            title = title_elem.get_text(strip=True)
            
            # Check if the title contains any privacy keywords
            if not any(keyword.lower() in title.lower() for keyword in PRIVACY_KEYWORDS):
                # If title doesn't match, skip this post
                continue
            
            # Get the URL
            url = title_elem.get('href', '')
            if url.startswith('item?id='):
                # It's a self post
                url = f"https://news.ycombinator.com/{url}"
            elif not url.startswith('http'):
                # It's a relative URL
                url = f"https://news.ycombinator.com/{url}"
                
            # Ensure we have the HN item URL for the API
            if 'item?id=' not in url:
                url = f"https://news.ycombinator.com/item?id={story_id}"
                
            # Extract timestamp
            timestamp = extract_hn_timestamp(story_id)
            
            # Extract summary
            summary = extract_hn_summary(story_id)
            
            # Add to our posts list
            post = {
                "source": source_config['name'],
                "timestamp": timestamp,
                "url": url,
                "title": title,
                "summary": summary
            }
            
            posts.append(post)
            logging.info(f"Found privacy-related post on Hacker News: {title}")
            
    return posts
