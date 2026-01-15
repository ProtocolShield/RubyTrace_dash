"""
Utilities for working with HTTP requests.
Originally designed to work with Tor, now supports direct connections as fallback.
"""
import logging
import requests
import time
from requests.exceptions import RequestException
from config import TOR_PROXY_HOST, TOR_PROXY_PORT

import platform
import socket

# Global flag to track Tor availability - default to False
TOR_AVAILABLE = False

def setup_session():
    """
    Create a requests session.
    
    Returns:
        requests.Session: A session configured with appropriate headers
    """
    session = requests.Session()
    
    # Set User-Agent to not disclose too much information
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0'
    })
    
    return session

def fetch_with_tor(url, max_retries=3, backoff_factor=2):
    """
    Fetch a URL with retry logic.
    Originally designed to use Tor, now uses direct connections.
    
    Args:
        url (str): The URL to fetch
        max_retries (int): Maximum number of retry attempts
        backoff_factor (int): Backoff factor for retries
    
    Returns:
        str: The response content if successful, None otherwise
    """
    session = setup_session()
    
    for attempt in range(max_retries):
        try:
            response = session.get(url, timeout=30)
            
            # Check if we got a successful response
            if response.status_code == 200:
                return response.text
            
            logging.warning(f"HTTP error {response.status_code} for {url}")
            
        except RequestException as e:
            logging.warning(f"Request failed (attempt {attempt+1}/{max_retries}): {e}")
        
        # Calculate backoff time: backoff_factor * (2 ^ (attempt))
        if attempt < max_retries - 1:
            backoff_time = backoff_factor * (2 ** attempt)
            logging.info(f"Retrying in {backoff_time} seconds...")
            time.sleep(backoff_time)
    
    logging.error(f"Failed to fetch {url} after {max_retries} attempts")
    return None

def verify_tor_connection():
    """
    Verify that the Tor connection is working.
    
    Returns:
        bool: True if Tor is available, False otherwise
    """
    global TOR_AVAILABLE
    if TOR_AVAILABLE:
        return True
    
    # Check if Tor SOCKS5 proxy is open on localhost:9050
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect(("127.0.0.1", 9050))
        sock.close()
        TOR_AVAILABLE = True
        logging.info("Tor SOCKS5 proxy detected on 127.0.0.1:9050")
        return True
    except Exception:
        logging.warning("Tor SOCKS5 proxy not detected on 127.0.0.1:9050")
    
    # Additional platform-specific checks can be added here
    if platform.system() == "Windows":
        logging.warning("Tor is not detected on Windows system. Please ensure Tor is running.")
    else:
        logging.warning("Tor is not detected. Please ensure Tor is running.")
    
    TOR_AVAILABLE = False
    return False
