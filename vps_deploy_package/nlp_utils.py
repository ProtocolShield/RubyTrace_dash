"""
NLP utilities for text analysis of privacy-related content.
"""
import os
import logging
import nltk
from textblob import TextBlob
from config import NLTK_DATA_PATH, ENABLE_SENTIMENT_ANALYSIS

# Create NLTK data directory if it doesn't exist
os.makedirs(NLTK_DATA_PATH, exist_ok=True)
nltk.data.path.append(NLTK_DATA_PATH)
nltk.data.path.append('/home/runner/nltk_data')  # Add the default NLTK data path

# Add privacy-specific keywords that should be prioritized
PRIVACY_KEYWORDS = {
    'privacy', 'security', 'encryption', 'surveillance', 'anonymity', 'vpn', 
    'tracker', 'gdpr', 'ccpa', 'breach', 'data', 'protection', 'personal', 
    'identity', 'biometric', 'facial', 'recognition', 'cookies', 'leak', 
    'vulnerability', 'backdoor', 'malware', 'spyware', 'hacker', 'cyberattack',
    'cybersecurity', 'firewall', 'proxy', 'tor', 'fingerprinting', 'anonymous'
}

# Download necessary NLTK and TextBlob data
try:
    # Use predownloaded data from our earlier bash commands
    stopwords = set(nltk.corpus.stopwords.words('english'))
    
    # Initialize TextBlob with basic keyword extraction capability
    text = "This is a test message for privacy and security."
    test_blob = TextBlob(text)
    logging.info("NLP processing successfully initialized")
except Exception as e:
    logging.warning(f"Failed to initialize language processing: {e}")
    
# Fall back to basic word tokenization if TextBlob noun phrase extraction fails
def extract_phrases(text):
    """Extract important phrases using simple rules if TextBlob fails"""
    words = []
    try:
        words = text.lower().split()
        # Filter out very short words and common stopwords
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'by', 'about', 'like'}
        words = [w for w in words if len(w) > 3 and w not in common_words]
        
        # Prioritize privacy-related keywords
        for word in list(words):
            if word in PRIVACY_KEYWORDS:
                # Move privacy-related words to the front
                words.remove(word)
                words.insert(0, word)
    except Exception as e:
        logging.warning(f"Error in extract_phrases: {e}")
    return words


def get_keywords(text, top_n=5):
    """
    Extract the most important keywords from a text.
    
    Args:
        text (str): The text to analyze
        top_n (int): Number of top keywords to return
        
    Returns:
        list: List of top keywords
    """
    if not text:
        return []
        
    try:
        # First check for exact matches with our privacy keywords
        words = text.lower().split()
        privacy_matches = [word for word in words if word in PRIVACY_KEYWORDS]
        
        # Tokenize the text
        blob = TextBlob(text.lower())
        
        # Extract noun phrases as keywords
        noun_phrases = list(blob.noun_phrases)
        
        # Combine privacy matches and noun phrases, prioritizing privacy matches
        combined_keywords = privacy_matches + [np for np in noun_phrases if np not in privacy_matches]
        
        # If we have keywords from the above methods, return them
        if combined_keywords:
            return combined_keywords[:top_n]
            
        # Otherwise, use word frequencies
        try:
            stopwords = set(nltk.corpus.stopwords.words('english'))
            filtered_words = [word for word in blob.words if len(word) > 3 and word not in stopwords]
        except:
            filtered_words = [word for word in blob.words if len(word) > 3]
            
        # Count word frequencies
        word_counts = {}
        for word in filtered_words:
            # Prioritize privacy keywords
            if word in PRIVACY_KEYWORDS:
                word_counts[word] = 1000  # Give high priority
            elif word in word_counts:
                word_counts[word] += 1
            else:
                word_counts[word] = 1
                
        # Sort by frequency and get top N
        keywords = sorted(word_counts.keys(), key=lambda x: word_counts[x], reverse=True)
        
        # Return top N keywords
        return keywords[:top_n]
        
    except Exception as e:
        logging.warning(f"Error extracting keywords: {e}")
        # Use our fallback method
        simple_keywords = extract_phrases(text)
        return simple_keywords[:top_n]


def analyze_sentiment(text):
    """
    Analyze the sentiment of a text.
    
    Args:
        text (str): The text to analyze
        
    Returns:
        dict: Sentiment analysis results including:
            - polarity: float from -1 (negative) to 1 (positive)
            - subjectivity: float from 0 (objective) to 1 (subjective)
            - assessment: str, one of 'positive', 'negative', 'neutral'
    """
    if not ENABLE_SENTIMENT_ANALYSIS or not text:
        return {
            "polarity": 0.0,
            "subjectivity": 0.0,
            "assessment": "neutral"
        }
        
    try:
        # Use TextBlob for sentiment analysis
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        # Classify the sentiment
        if polarity > 0.1:
            assessment = "positive"
        elif polarity < -0.1:
            assessment = "negative"
        else:
            assessment = "neutral"
            
        return {
            "polarity": polarity,
            "subjectivity": subjectivity,
            "assessment": assessment
        }
        
    except Exception as e:
        logging.warning(f"Error analyzing sentiment: {e}")
        return {
            "polarity": 0.0,
            "subjectivity": 0.0,
            "assessment": "neutral"
        }


def enrich_post_with_nlp(post):
    """
    Enrich a post with NLP analysis.
    
    Args:
        post (dict): The post to enrich
        
    Returns:
        dict: The enriched post with NLP data
    """
    # Create a copy of the post to avoid modifying the original
    enriched = post.copy()
    
    # Extract text for analysis (combine title and summary)
    text = f"{post.get('title', '')} {post.get('summary', '')}"
    
    # Extract keywords
    enriched["keywords"] = get_keywords(text)
    
    # Analyze sentiment
    enriched["sentiment"] = analyze_sentiment(text)
    
    return enriched