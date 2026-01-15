"""
Phone number search module for privacy OSINT data collector.

This module contains functions to search for phone numbers in various public sources:
- Spam report databases
- Public classifieds sites
- Basic information lookup (country, carrier)
"""
import requests
import logging
import re
import os
import json
from urllib.parse import quote_plus
from utils.tor_utils import setup_session

# API keys will be fetched from database when needed
NUMVERIFY_API_KEY = None

# Cache for search results
phone_search_cache = {}

def validate_phone(phone_number):
    """
    Validate if a string is a proper phone number.
    Accepts formats: +1234567890, 1234567890, 123-456-7890
    
    Args:
        phone_number (str): Phone number to validate
        
    Returns:
        bool: True if valid phone number, False otherwise
    """
    # Strip all non-numeric characters except leading +
    if phone_number.startswith('+'):
        stripped = '+' + ''.join(filter(str.isdigit, phone_number[1:]))
    else:
        stripped = ''.join(filter(str.isdigit, phone_number))
    
    # Check basic length requirements (most countries between 8-15 digits)
    if stripped.startswith('+'):
        return 8 <= len(stripped) <= 16
    else:
        return 7 <= len(stripped) <= 15

def normalize_phone(phone_number):
    """
    Normalize a phone number to E.164 format.
    
    Args:
        phone_number (str): Phone number to normalize
        
    Returns:
        str: Normalized phone number
    """
    # Strip all non-numeric characters
    digits_only = ''.join(filter(str.isdigit, phone_number))
    
    # Check if there's a country code
    if phone_number.startswith('+'):
        return f"+{digits_only}"
    elif len(digits_only) == 10 and digits_only.startswith(('5', '6', '7', '8', '9')):
        # Assuming US/Canada number without country code (simple heuristic)
        return f"+1{digits_only}"
    else:
        # Return as-is with + prefix
        return f"+{digits_only}"

def lookup_basic_info(phone_number):
    """
    Look up basic information about a phone number.
    This function uses the NumVerify API if an API key is available,
    or a basic regex-based approach otherwise.
    
    Args:
        phone_number (str): Phone number to look up
        
    Returns:
        dict: Basic information about the phone number
    """
    if not validate_phone(phone_number):
        return {"error": "Invalid phone number format", "valid": False}
        
    # Check cache first
    normalized = normalize_phone(phone_number)
    cache_key = f"basic_{normalized}"
    if cache_key in phone_search_cache:
        return phone_search_cache[cache_key]
        
    # Try to get API key from database
    try:
        from main import get_api_key
        api_key = get_api_key('numverify')
    except Exception as e:
        logging.warning(f"Error getting API key from database: {e}")
        api_key = None
    
    # If API key is available, use NumVerify
    if api_key:
        try:
            # Extract the numbers only (no + sign)
            number_only = normalized.lstrip('+')
            
            # NumVerify API endpoint
            api_url = f"http://apilayer.net/api/validate?access_key={api_key}&number={number_only}"
            
            response = requests.get(api_url)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("valid"):
                    result = {
                        "valid": True,
                        "number": data.get("international_format"),
                        "country": data.get("country_name"),
                        "country_code": data.get("country_code"),
                        "carrier": data.get("carrier"),
                        "line_type": data.get("line_type")
                    }
                else:
                    result = {"valid": False, "message": "Number not valid"}
                    
                # Cache result
                phone_search_cache[cache_key] = result
                return result
            else:
                return {"error": f"API error: {response.status_code}", "valid": False}
                
        except Exception as e:
            logging.error(f"Error using NumVerify API: {e}")
            # Fall back to basic approach
            pass
    
    # Basic approach if no API or API failed
    # This is very simplified and not accurate for most cases
    if normalized.startswith('+1') and len(normalized) == 12:
        return {
            "valid": True,
            "number": normalized,
            "country": "United States or Canada",
            "country_code": "1",
            "note": "Basic information only. For more accurate data, provide a NumVerify API key."
        }
    elif normalized.startswith('+44') and len(normalized) >= 12:
        return {
            "valid": True,
            "number": normalized,
            "country": "United Kingdom",
            "country_code": "44",
            "note": "Basic information only. For more accurate data, provide a NumVerify API key."
        }
    elif normalized.startswith('+'):
        return {
            "valid": True,
            "number": normalized,
            "note": "Limited information available. For more accurate data, provide a NumVerify API key."
        }
    else:
        return {"valid": False, "message": "Unable to determine number information"}

def search_spam_databases(phone_number):
    """
    Search public spam report databases for the phone number.
    
    Args:
        phone_number (str): Phone number to search
        
    Returns:
        dict: Results of the search
    """
    if not validate_phone(phone_number):
        return {"error": "Invalid phone number format", "found": False}
        
    # Check cache first
    normalized = normalize_phone(phone_number)
    cache_key = f"spam_{normalized}"
    if cache_key in phone_search_cache:
        return phone_search_cache[cache_key]
    
    # List of spam report sites to check
    spam_sites = [
        {"name": "Who Calls Me", "domain": "whocallsme.com"},
        {"name": "800notes", "domain": "800notes.com"}
    ]
    
    results = {"found": False, "sites": []}
    session = setup_session()
    
    for site in spam_sites:
        try:
            # Strip all non-numeric characters for the search
            digits_only = ''.join(filter(str.isdigit, phone_number))
            
            # Construct search URL
            search_url = f"https://{site['domain']}/search/{digits_only}"
            
            response = session.get(search_url, timeout=10)
            
            if response.status_code == 200:
                # Simple check if the number appears in the response
                if digits_only in response.text:
                    site_result = {
                        "site": site["name"],
                        "found": True,
                        "url": search_url,
                        "note": "Number found in database, may have spam reports"
                    }
                    results["found"] = True
                    results["sites"].append(site_result)
                else:
                    site_result = {
                        "site": site["name"],
                        "found": False,
                        "note": "Number not found in database"
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
    phone_search_cache[cache_key] = results
    return results

def search_classifieds(phone_number):
    """
    Search public classified sites for the phone number.
    
    Args:
        phone_number (str): Phone number to search
        
    Returns:
        dict: Results of the search
    """
    if not validate_phone(phone_number):
        return {"error": "Invalid phone number format", "found": False}
        
    # Check cache first
    normalized = normalize_phone(phone_number)
    cache_key = f"classified_{normalized}"
    if cache_key in phone_search_cache:
        return phone_search_cache[cache_key]
    
    # Strip all non-numeric characters for the search
    digits_only = ''.join(filter(str.isdigit, phone_number))
    
    # Create a search-friendly version with formatting (e.g., 123-456-7890)
    if len(digits_only) == 10:  # US format
        formatted = f"{digits_only[:3]}-{digits_only[3:6]}-{digits_only[6:]}"
    else:
        formatted = digits_only
    
    # List of classified sites to check
    classified_sites = [
        {"name": "Craigslist", "domain": "craigslist.org"}
    ]
    
    results = {"found": False, "sites": []}
    session = setup_session()
    
    for site in classified_sites:
        try:
            # For Craigslist, use Google search as direct API is not available
            search_url = f"https://www.google.com/search?q=site:{site['domain']}+{quote_plus(formatted)}"
            
            response = session.get(search_url, timeout=10)
            
            if response.status_code == 200:
                # Check if there are results (simplified)
                if digits_only in response.text or formatted in response.text:
                    site_result = {
                        "site": site["name"],
                        "found": True,
                        "url": search_url,
                        "note": "Phone number may appear in listings"
                    }
                    results["found"] = True
                    results["sites"].append(site_result)
                else:
                    site_result = {
                        "site": site["name"],
                        "found": False,
                        "note": "Phone number not found in public listings"
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
    phone_search_cache[cache_key] = results
    return results

def search_phone(phone_number):
    """
    Main function to search for a phone number across multiple sources.
    
    Args:
        phone_number (str): Phone number to search
        
    Returns:
        dict: Comprehensive search results from all sources
    """
    if not validate_phone(phone_number):
        return {"error": "Invalid phone number format", "valid": False}
    
    normalized = normalize_phone(phone_number)
    
    # Consolidate results from multiple sources
    results = {
        "phone_number": normalized,
        "original_input": phone_number,
        "timestamp": "",  # Will be set by the API
        "sources": {}
    }
    
    # Get basic information
    basic_info = lookup_basic_info(normalized)
    results["sources"]["basic_info"] = basic_info
    
    # Check spam databases
    spam_results = search_spam_databases(normalized)
    results["sources"]["spam_databases"] = spam_results
    
    # Check classified sites
    classified_results = search_classifieds(normalized)
    results["sources"]["classified_sites"] = classified_results
    
    # Determine overall status
    results["found"] = any([
        source.get("found", False) 
        for source in results["sources"].values()
        if isinstance(source, dict) and "found" in source
    ])
    
    return results

def clear_phone_cache():
    """Clear the phone search cache."""
    phone_search_cache.clear()
    return {"success": True, "message": "Phone search cache cleared"}