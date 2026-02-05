"""
Telegram Bot for collecting data from Telegram channels and groups
Collects messages, media, and metadata from public Telegram channels
"""

import asyncio
import aiohttp
import logging
import json
import re
import hashlib
import os
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
import tldextract
from .base_bot import BaseBot
from models import db, DataSource, RawData, Entity
from nlp_utils import get_keywords, analyze_sentiment


class TelegramBot(BaseBot):
    """
    Bot for collecting data from Telegram channels and groups
    Includes message content, media, and metadata collection
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        default_config = {
            'max_messages': 100,  # Maximum messages to collect per channel
            'include_media': True,
            'include_metadata': True,
            'keyword_filtering': False,  # Collect all messages
            'risk_keywords': [
                'hack', 'exploit', 'vulnerability', 'breach', 'leak',
                'malware', 'ransomware', 'phishing', 'cyber', 'security',
                'privacy', 'surveillance', 'encryption', 'backdoor',
                'cve', 'zero-day', 'attack', 'threat', 'intrusion'
            ],
            'allowed_channels': [],
            'blocked_channels': [],
            'media_types': ['image', 'video', 'document', 'audio'],
            'max_media_size': 10 * 1024 * 1024  # 10MB
        }
        
        if config:
            default_config.update(config)
        
        super().__init__("TelegramBot", "telegram", default_config)
        
        # Telegram specific settings
        self.visited_channels = set()
        self.message_cache = {}
        self.media_cache = {}
        
    async def collect_data(self, source: DataSource) -> List[Dict[str, Any]]:
        """Collect data from a Telegram channel"""
        try:
            self.logger.info(f"Starting Telegram data collection from {source.name}")
            
            collected_data = []
            channel_url = source.url
            
            # Parse source configuration
            source_config = json.loads(source.config_json) if source.config_json else {}
            max_messages = source_config.get('max_messages', self.config['max_messages'])
            
            # Extract channel username from URL
            channel_username = self._extract_channel_username(channel_url)
            if not channel_username:
                self.logger.error(f"Could not extract channel username from {channel_url}")
                return []
            
            # Collect messages from the channel
            await self._collect_channel_messages(channel_username, max_messages, collected_data, source)
            
            self.logger.info(f"Collected {len(collected_data)} items from {source.name}")
            return collected_data
            
        except Exception as e:
            self.logger.error(f"Error collecting data from {source.name}: {e}")
            await self._log_bot_status('error', f"Collection failed: {str(e)}")
            return []
    
    def _extract_channel_username(self, url: str) -> Optional[str]:
        """Extract channel username from Telegram URL"""
        try:
            # Handle different Telegram URL formats
            if 't.me/' in url:
                username = url.split('t.me/')[-1].split('/')[0]
                return username
            elif 'telegram.me/' in url:
                username = url.split('telegram.me/')[-1].split('/')[0]
                return username
            else:
                # Try to extract from any URL format
                parsed = urlparse(url)
                path_parts = parsed.path.strip('/').split('/')
                if path_parts:
                    return path_parts[0]
        except Exception as e:
            self.logger.error(f"Error extracting channel username from {url}: {e}")
        
        return None
    
    async def _collect_channel_messages(self, channel_username: str, max_messages: int, 
                                       collected_data: List[Dict[str, Any]], source: DataSource):
        """Collect messages from a Telegram channel"""
        try:
            # Use Telegram web interface to collect data
            web_url = f"https://t.me/s/{channel_username}"
            
            response = await self._make_request(web_url)
            if not response or response.status != 200:
                self.logger.warning(f"Could not access {web_url}")
                return
            
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract channel information
            channel_info = self._extract_channel_info(soup, channel_username)
            
            # Extract messages
            messages = self._extract_messages(soup, max_messages)
            
            for message in messages:
                # Check if message is relevant
                if not self._is_message_relevant(message['text'], message.get('title', '')):
                    continue
                
                # Create message data
                message_data = {
                    'url': f"https://t.me/{channel_username}/{message.get('id', '')}",
                    'title': message.get('title', f"Message from {channel_username}"),
                    'content': message['text'],
                    'raw_html': message.get('html', ''),
                    'content_type': 'text/telegram',
                    'metadata': {
                        'channel': channel_username,
                        'channel_info': channel_info,
                        'message_id': message.get('id'),
                        'timestamp': message.get('timestamp'),
                        'author': message.get('author'),
                        'media': message.get('media', []),
                        'views': message.get('views'),
                        'forwards': message.get('forwards')
                    },
                    'risk_score': self._calculate_risk_score(message['text'], message.get('title', '')),
                    'keywords': ','.join(get_keywords(message['text']) if message['text'] else []),
                    'tags': f"telegram,channel:{channel_username},category:{source.category}",
                    'risk_keywords': self._extract_risk_keywords(message['text']),
                    'search_text': f"{message.get('title', '')} {message['text']}",
                    'file_path': None,
                    'file_hash': self._calculate_content_hash(message['text'])
                }
                
                collected_data.append(message_data)
                
        except Exception as e:
            self.logger.error(f"Error collecting channel messages from {channel_username}: {e}")
    
    def _extract_channel_info(self, soup: BeautifulSoup, channel_username: str) -> Dict[str, Any]:
        """Extract channel information from Telegram web page"""
        info = {
            'username': channel_username,
            'title': '',
            'description': '',
            'subscribers': 0,
            'verified': False
        }
        
        try:
            # Extract channel title
            title_elem = soup.find('div', class_='tgme_page_title')
            if title_elem:
                info['title'] = title_elem.get_text(strip=True)
            
            # Extract channel description
            desc_elem = soup.find('div', class_='tgme_page_description')
            if desc_elem:
                info['description'] = desc_elem.get_text(strip=True)
            
            # Extract subscriber count
            subscribers_elem = soup.find('div', class_='tgme_page_extra')
            if subscribers_elem:
                text = subscribers_elem.get_text()
                # Look for subscriber count pattern
                match = re.search(r'(\d+(?:,\d+)*)\s*(?:subscribers?|members?)', text, re.IGNORECASE)
                if match:
                    info['subscribers'] = int(match.group(1).replace(',', ''))
            
            # Check if verified
            verified_elem = soup.find('i', class_='verified-icon')
            if verified_elem:
                info['verified'] = True
                
        except Exception as e:
            self.logger.warning(f"Error extracting channel info: {e}")
        
        return info
    
    def _extract_messages(self, soup: BeautifulSoup, max_messages: int) -> List[Dict[str, Any]]:
        """Extract messages from Telegram web page"""
        messages = []
        
        try:
            # Find message containers
            message_elems = soup.find_all('div', class_='tgme_widget_message')
            
            for i, msg_elem in enumerate(message_elems[:max_messages]):
                try:
                    message = self._extract_single_message(msg_elem)
                    if message:
                        messages.append(message)
                except Exception as e:
                    self.logger.warning(f"Error extracting message {i}: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error extracting messages: {e}")
        
        return messages
    
    def _extract_single_message(self, msg_elem) -> Optional[Dict[str, Any]]:
        """Extract a single message from message element"""
        try:
            message = {
                'id': '',
                'text': '',
                'title': '',
                'author': '',
                'timestamp': '',
                'views': 0,
                'forwards': 0,
                'media': [],
                'html': str(msg_elem)
            }
            
            # Extract message ID
            id_elem = msg_elem.find('a', class_='tgme_widget_message_date')
            if id_elem and id_elem.get('href'):
                href = id_elem['href']
                match = re.search(r'/(\d+)$', href)
                if match:
                    message['id'] = match.group(1)
            
            # Extract message text
            text_elem = msg_elem.find('div', class_='tgme_widget_message_text')
            if text_elem:
                message['text'] = text_elem.get_text(strip=True)
            
            # Extract message title (if it's a forwarded message)
            title_elem = msg_elem.find('div', class_='tgme_widget_message_author')
            if title_elem:
                message['title'] = title_elem.get_text(strip=True)
            
            # Extract timestamp
            date_elem = msg_elem.find('a', class_='tgme_widget_message_date')
            if date_elem:
                message['timestamp'] = date_elem.get_text(strip=True)
            
            # Extract media
            media_elems = msg_elem.find_all(['img', 'video', 'audio'])
            for media_elem in media_elems:
                media_info = {
                    'type': media_elem.name,
                    'src': media_elem.get('src', ''),
                    'alt': media_elem.get('alt', '')
                }
                message['media'].append(media_info)
            
            # Extract views and forwards
            views_elem = msg_elem.find('span', class_='tgme_widget_message_views')
            if views_elem:
                views_text = views_elem.get_text()
                match = re.search(r'(\d+)', views_text)
                if match:
                    message['views'] = int(match.group(1))
            
            return message
            
        except Exception as e:
            self.logger.warning(f"Error extracting single message: {e}")
            return None
    
    def _is_message_relevant(self, text: str, title: str) -> bool:
        """Check if message is relevant based on content"""
        if not self.config['keyword_filtering']:
            return len(text) > 10  # Accept messages with substantial content
        
        # If keyword filtering is disabled, accept all substantial content
        if len(text) < 20:  # Reject very short messages
            return False
        
        text_combined = f"{title} {text}".lower()
        
        # Check for risk keywords
        for keyword in self.config['risk_keywords']:
            if keyword.lower() in text_combined:
                return True
        
        # Check for cybersecurity terms
        cyber_terms = ['security', 'cyber', 'hack', 'vulnerability', 'breach', 
                      'technology', 'software', 'internet', 'data', 'privacy',
                      'cve', 'exploit', 'malware', 'threat', 'attack']
        if any(term in text_combined for term in cyber_terms):
            return True
        
        # Accept messages with substantial length even without specific keywords
        if len(text) > 100:
            return True
        
        return False
    
    def _calculate_risk_score(self, text: str, title: str) -> float:
        """Calculate risk score based on message content"""
        score = 0.0
        text_combined = f"{title} {text}".lower()
        
        # High risk keywords
        high_risk = ['exploit', 'malware', 'ransomware', 'breach', 'leak', 'zero-day']
        for keyword in high_risk:
            if keyword in text_combined:
                score += 0.3
        
        # Medium risk keywords
        medium_risk = ['hack', 'vulnerability', 'attack', 'threat', 'cve']
        for keyword in medium_risk:
            if keyword in text_combined:
                score += 0.2
        
        # Low risk keywords
        low_risk = ['security', 'cyber', 'privacy', 'encryption']
        for keyword in low_risk:
            if keyword in text_combined:
                score += 0.1
        
        return min(score, 1.0)
    
    def _extract_risk_keywords(self, text: str) -> str:
        """Extract risk-related keywords from message text"""
        if not text:
            return ""
        
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in self.config['risk_keywords']:
            if keyword.lower() in text_lower:
                found_keywords.append(keyword)
        
        return ','.join(found_keywords)
    
    def _calculate_content_hash(self, content: str) -> str:
        """Calculate hash of message content for deduplication"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def run_collection_cycle(self, sources: List[DataSource]):
        """Run a complete collection cycle for Telegram sources"""
        try:
            self.logger.info("Starting Telegram collection cycle")
            
            # Ensure we have a valid session
            if not self.session or self.session.closed:
                await self._setup_session()
            
            total_collected = 0
            start_time = time.time()
            
            for source in sources:
                if source.source_type in ['social_media', 'telegram'] and source.enabled:
                    try:
                        self.logger.info(f"Processing Telegram source: {source.name} ({source.url})")
                        
                        # Check session before each source
                        if self.session.closed:
                            await self._setup_session()
                        
                        collected = await self.collect_data(source)
                        total_collected += len(collected)
                        
                        # Process collected data
                        for data in collected:
                            raw_data_record = await self.process_raw_data(data, source)
                            if raw_data_record:
                                await self.extract_entities(raw_data_record)
                        
                        # Update source last scraped time
                        try:
                            source.last_scraped = datetime.utcnow()
                            db.session.commit()
                        except Exception as db_error:
                            self.logger.warning(f"Failed to update source timestamp: {db_error}")
                        
                        # Small delay between sources
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        self.logger.error(f"Error processing Telegram source {source.name}: {e}")
                        continue
            
            execution_time = time.time() - start_time
            await self._log_bot_status(
                'success', 
                f"Telegram collection cycle completed. Collected {total_collected} items.",
                total_collected,
                execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Error in Telegram collection cycle: {e}")
            await self._log_bot_status('error', f"Telegram collection cycle failed: {str(e)}")