"""
Utilities for working with JSON data.
"""
import json
import os
import logging
from datetime import datetime

def load_existing_data(filename):
    """
    Load existing data from the JSON file.
    
    Args:
        filename (str): The JSON file to load
    
    Returns:
        list: The loaded data as a list of dictionaries, or an empty list if no file exists
    """
    if not os.path.exists(filename):
        return []
    
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing JSON in {filename}: {e}")
        return []
    except Exception as e:
        logging.error(f"Error loading data from {filename}: {e}")
        return []

def save_data(data, filename):
    """
    Save data to a JSON file.
    
    Args:
        data (list): The data to save
        filename (str): The JSON file to save to
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logging.error(f"Error saving data to {filename}: {e}")
        return False

def is_duplicate_post(post, existing_data):
    """
    Check if a post already exists in the data.
    
    Args:
        post (dict): The post to check
        existing_data (list): List of existing posts
    
    Returns:
        bool: True if the post is a duplicate, False otherwise
    """
    for existing_post in existing_data:
        # Consider posts as duplicates if they have the same URL or the same title from the same source
        if (post['url'] == existing_post.get('url') or 
            (post['title'] == existing_post.get('title') and 
             post['source'] == existing_post.get('source'))):
            return True
    return False

def add_new_post(post, data_file):
    """
    Add a new post to the data file if it doesn't already exist.
    
    Args:
        post (dict): The post to add
        data_file (str): Path to the data file
    
    Returns:
        bool: True if the post was added, False if it was a duplicate
    """
    existing_data = load_existing_data(data_file)
    
    if is_duplicate_post(post, existing_data):
        return False
    
    # Add the new post
    existing_data.append(post)
    save_data(existing_data, data_file)
    return True
