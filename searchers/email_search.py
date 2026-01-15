"""
Email search module for privacy OSINT data collector.

This module contains functions to search for email addresses in various public sources:
- Have I Been Pwned API integration
- Public pastebin sites via Google dorking
- Forum scraping for exposed emails
"""
import requests
import logging
import re
import os
import json
from urllib.parse import quote_plus
from utils.tor_utils import setup_session

# API key will be fetched from the database when needed
HIBP_API_KEY = None

# Cache for search results to minimize API calls
email_search_cache = {}

def validate_email(email):
    """
    Validate if a string is a proper email address.
    
    Args:
        email (str): Email address to validate
        
    Returns:
        bool: True if valid email, False otherwise
    """
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))

def search_haveibeenpwned(email):
    """
    Search the Have I Been Pwned API for breaches containing the email.
    
    Args:
        email (str): Email address to search
        
    Returns:
        dict: Results from HIBP including breaches or error message
    """
    if not validate_email(email):
        return {"error": "Invalid email format", "found": False}
    
    # Check cache first
    cache_key = f"hibp_{email}"
    if cache_key in email_search_cache:
        return email_search_cache[cache_key]
        
    # HIBP API endpoint
    api_url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
    
    # Try to get API key from database
    try:
        from main import get_api_key
        api_key = get_api_key('haveibeenpwned')
    except Exception as e:
        logging.warning(f"Error getting API key from database: {e}")
        api_key = None
    
    # Set up headers - API key is required for the v3 API
    headers = {
        "User-Agent": "Privacy OSINT Collector",
        "hibp-api-key": api_key,
    }
    
    try:
        # If no API key, provide informative error
        if not api_key:
            return {
                "error": "HIBP API key is required. Configure it in the Settings page.",
                "found": False
            }
            
        # Make the request
        response = requests.get(api_url, headers=headers)
        
        # Handle responses
        if response.status_code == 200:
            # Email found in breaches
            breaches = response.json()
            result = {
                "found": True,
                "breach_count": len(breaches),
                "breaches": [
                    {
                        "name": breach.get("Name"),
                        "domain": breach.get("Domain"),
                        "breach_date": breach.get("BreachDate"),
                        "data_classes": breach.get("DataClasses")
                    }
                    for breach in breaches
                ]
            }
            email_search_cache[cache_key] = result
            return result
        elif response.status_code == 404:
            # Email not found in any breaches
            result = {"found": False, "message": "Email not found in any known data breaches"}
            email_search_cache[cache_key] = result
            return result
        elif response.status_code == 401:
            # Unauthorized - API key issue
            return {"error": "Invalid or missing API key for Have I Been Pwned", "found": False}
        elif response.status_code == 429:
            # Rate limit exceeded
            return {"error": "Rate limit exceeded. Try again later.", "found": False}
        else:
            # Other errors
            return {"error": f"API error: {response.status_code}", "found": False}
    
    except Exception as e:
        logging.error(f"Error searching HIBP: {e}")
        return {"error": f"Search failed: {str(e)}", "found": False}

def search_pastebin_sites(email):
    """
    Search public pastebin sites for the email address using a search engine.
    This uses a simplified approach with direct HTTP requests.
    
    Args:
        email (str): Email address to search
        
    Returns:
        dict: Results of the search
    """
    if not validate_email(email):
        return {"error": "Invalid email format", "found": False}
    
    # Check cache first
    cache_key = f"pastebin_{email}"
    if cache_key in email_search_cache:
        return email_search_cache[cache_key]
    
    # List of sites to check (can be expanded)
    paste_sites = [
        {"name": "Pastebin", "domain": "pastebin.com"},
        {"name": "GitHub Gists", "domain": "gist.github.com"}
    ]
    
    results = {"found": False, "sites": []}
    session = setup_session()
    
    for site in paste_sites:
        try:
            # Using a dorking-like approach with a regular search
            # This is a simplified method; real dorking would use special search engine operators
            encoded_email = quote_plus(email)
            search_url = f"https://{site['domain']}/?q={encoded_email}"
            
            response = session.get(search_url, timeout=10)
            
            if response.status_code == 200:
                # Very basic check - if email is in the response content, considered "found"
                if email in response.text:
                    site_result = {
                        "site": site["name"],
                        "found": True,
                        "url": search_url
                    }
                    results["found"] = True
                    results["sites"].append(site_result)
                else:
                    site_result = {
                        "site": site["name"],
                        "found": False
                    }
                    results["sites"].append(site_result)
            else:
                site_result = {
                    "site": site["name"],
                    "error": f"Search failed with status code: {response.status_code}"
                }
                results["sites"].append(site_result)
                
        except Exception as e:
            logging.error(f"Error searching {site['name']}: {e}")
            site_result = {
                "site": site["name"],
                "error": str(e)
            }
            results["sites"].append(site_result)
    
    # Cache results
    email_search_cache[cache_key] = results
    return results

def search_email(email):
    """
    Main function to search for an email across multiple sources.
    
    Args:
        email (str): Email address to search
        
    Returns:
        dict: Comprehensive search results from all sources
    """
    if not validate_email(email):
        return {"error": "Invalid email format", "found": False}
    
    # Consolidate results from multiple sources
    results = {
        "email": email,
        "timestamp": "",  # Will be set by the API
        "sources": {}
    }
    
    # Check Have I Been Pwned
    hibp_results = search_haveibeenpwned(email)
    results["sources"]["haveibeenpwned"] = hibp_results
    
    # Check pastebin sites
    pastebin_results = search_pastebin_sites(email)
    results["sources"]["pastebin_sites"] = pastebin_results
    
    # Determine overall status
    results["found"] = any([
        source.get("found", False) 
        for source in results["sources"].values()
    ])
    
    return results

def clear_email_cache():
    """Clear the email search cache."""
    email_search_cache.clear()
    return {"success": True, "message": "Email search cache cleared"}