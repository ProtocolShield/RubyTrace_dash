"""
Scraper for Reddit privacy-related subreddits.
"""
import logging
import praw
import time
import json
import os
from datetime import datetime
from api import app
from models import ApiKey
from database import with_retry
from config import (
    PRIVACY_KEYWORDS, REDDIT_SUBREDDITS, SOURCES_CONFIG_FILE
)

def get_subreddits():
    """
    Get the list of subreddits to scrape, with customization support.
    
    Returns:
        list: List of subreddit names to scrape
    """
    # Use the default list from config
    subreddits = REDDIT_SUBREDDITS.copy()
    
    # Check if we have a custom configuration file
    if os.path.exists(SOURCES_CONFIG_FILE):
        try:
            with open(SOURCES_CONFIG_FILE, 'r') as f:
                config = json.load(f)
                if 'reddit_subreddits' in config and isinstance(config['reddit_subreddits'], list):
                    # Override with custom list
                    return config['reddit_subreddits']
        except Exception as e:
            logging.warning(f"Error loading custom sources config: {e}")
    
    return subreddits

def scrape_reddit():
    """
    Scrape privacy-related posts from Reddit privacy subreddits.
    
    Returns:
        list: List of posts matching the privacy keywords
    """
    posts = []
    
    try:
        with app.app_context():
            @with_retry
            def get_reddit_keys():
                client_id_record = ApiKey.query.filter_by(service='reddit_client_id').first()
                client_secret_record = ApiKey.query.filter_by(service='reddit_client_secret').first()
                
                if not client_id_record or not client_secret_record:
                    return None, None
                
                return client_id_record.key, client_secret_record.key
            
            client_id, client_secret = get_reddit_keys()
            
            if not client_id or not client_secret:
                logging.error("Reddit API credentials not configured in database (services: 'reddit_client_id', 'reddit_client_secret'). Skipping Reddit scraping.")
                return posts
        
        # Initialize Reddit API client
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent='PrivacyOSINT/1.0 by /u/privacy_osint_bot'
        )
        
        # Get the list of subreddits to scrape (with customization support)
        subreddits = get_subreddits()
        
        for subreddit_name in subreddits:
            logging.info(f"Scraping r/{subreddit_name}...")
            
            try:
                subreddit = reddit.subreddit(subreddit_name)
                
                # Get hot posts from the subreddit
                for submission in subreddit.hot(limit=25):
                    # Skip stickied posts
                    if submission.stickied:
                        continue
                        
                    title = submission.title
                    
                    # Check if the post contains any of our privacy keywords
                    # Note: For privacy-specific subreddits, we might want to include all posts
                    # But we'll still filter by keywords for consistency
                    if not any(keyword.lower() in title.lower() for keyword in PRIVACY_KEYWORDS):
                        continue
                    
                    # Convert the creation timestamp to ISO format
                    timestamp = datetime.utcfromtimestamp(submission.created_utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                    
                    # Get the post URL
                    url = f"https://www.reddit.com{submission.permalink}"
                    
                    # Extract summary (selftext or first comment)
                    summary = "No summary available"
                    if submission.selftext:
                        # Use the post's own text if available
                        summary = submission.selftext[:200] + ('...' if len(submission.selftext) > 200 else '')
                    else:
                        # Try to get the first comment
                        submission.comments.replace_more(limit=0)
                        if submission.comments.list():
                            first_comment = submission.comments.list()[0].body
                            summary = first_comment[:200] + ('...' if len(first_comment) > 200 else '')
                    
                    post = {
                        "source": f"Reddit - r/{subreddit_name}",
                        "timestamp": timestamp,
                        "url": url,
                        "title": title,
                        "summary": summary
                    }
                    
                    posts.append(post)
                    logging.info(f"Found privacy-related post on r/{subreddit_name}: {title}")
                    
                # Be nice to Reddit API - pause between subreddits
                time.sleep(2)
                
            except Exception as e:
                logging.error(f"Error scraping r/{subreddit_name}: {e}")
                continue
        
    except Exception as e:
        logging.error(f"Error initializing Reddit API: {e}")
        
    return posts