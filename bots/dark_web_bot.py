"""
Dark Web Bot for collecting data from Tor hidden services and darknet sources
Uses Tor for anonymization and existing dark web crawler utilities
"""

import asyncio
import logging
import json
import time
import random
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

from .base_bot import BaseBot
from models import DataSource, RawData
from utils.tor_manager import start_tor, stop_tor, get_tor_proxy, verify_tor, new_tor_identity
from crawlers.darkweb_crawler import run_darkweb_crawler


class DarkWebBot(BaseBot):
    """
    Bot for collecting data from dark web sources (.onion and related)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        default_config = {
            'use_tor': True,
            'rotate_identity_every': 50,  # Rotate Tor identity every N requests
            'max_pages_per_site': 60,
            'keyword_filtering': True,
            'risk_keywords': [
                'exploit', 'zero-day', 'ransomware', 'malware', 'ddos',
                'breach', 'database', 'dump', 'credentials', 'logs',
                'keylogger', 'stealer', 'botnet', 'cpanel', 'whmcs', 'vpn',
                'rdp', 'fullz', 'skimmer', 'stripe', 'paypal'
            ],
            'delay_between_requests': (3, 7)
        }
        if config:
            default_config.update(config)
        super().__init__("DarkWebBot", "dark", default_config)
        self.request_counter = 0
    
    async def start(self):
        # Start Tor if enabled
        if self.config.get('use_tor', True):
            start_tor()
            verify_tor()
        return await super().start()
    
    async def stop(self):
        # Stop Tor if we started it
        if self.config.get('use_tor', True):
            stop_tor()
        return await super().stop()
    
    async def collect_data(self, source: DataSource) -> List[Dict[str, Any]]:
        """Collect data from a dark web source using the existing crawler"""
        try:
            self.logger.info(f"Starting dark web data collection from {source.name}")
            
            source_config = json.loads(source.config_json) if source.config_json else {}
            max_pages = source_config.get('max_pages_per_site', self.config['max_pages_per_site'])
            
            crawler_options = {
                'start_url': source.url,
                'max_pages': max_pages,
                'keyword_filtering': self.config['keyword_filtering'],
                'risk_keywords': self.config['risk_keywords'],
                'use_tor': self.config.get('use_tor', True),
                'tor_proxy': get_tor_proxy() if self.config.get('use_tor', True) else None,
            }
            
            # Run the dark web crawler (expected to be async-compatible)
            results = await run_darkweb_crawler(crawler_options)
            
            collected = []
            for item in results:
                # Basic mapping from crawler item to raw data schema
                content = item.get('content') or item.get('text') or ''
                title = item.get('title') or ''
                url = item.get('url') or source.url
                raw_html = item.get('raw_html')
                
                if self.config['keyword_filtering'] and not self._content_contains_keywords(f"{title} {content}"):
                    continue
                
                risk_keywords = self._extract_risk_keywords(content or '')
                
                collected.append({
                    'url': url,
                    'title': title,
                    'content': content,
                    'raw_html': raw_html,
                    'content_type': item.get('content_type', 'text/html' if raw_html else 'text/plain'),
                    'metadata': item.get('metadata', {}),
                    'risk_score': self._calculate_risk_score(content or '', title),
                    'keywords': ','.join(item.get('keywords', [])),
                    'tags': f"source:{source.category},network:tor",
                    'risk_keywords': risk_keywords,
                    'search_text': f"{title} {content}",
                    'file_path': item.get('file_path'),
                    'file_hash': item.get('file_hash')
                })
            
            # Identity rotation
            self.request_counter += len(collected)
            if self.config.get('use_tor', True) and self.request_counter >= self.config['rotate_identity_every']:
                new_tor_identity()
                self.request_counter = 0
            
            return collected
            
        except Exception as e:
            self.logger.error(f"Error collecting data from {source.name}: {e}")
            await self._log_bot_status('error', f"Collection failed: {str(e)}")
            return []
    
    def _content_contains_keywords(self, text: str) -> bool:
        text_l = text.lower()
        return any(k.lower() in text_l for k in self.config['risk_keywords'])
    
    def _calculate_risk_score(self, content: str, title: str) -> float:
        score = 0.0
        text = f"{title} {content}".lower()
        for kw in ['exploit', 'ransomware', 'credentials', 'database', 'fullz', 'botnet']:
            if kw in text:
                score += 0.25
        for kw in ['hack', 'leak', 'breach', 'dump', 'rdp']:
            if kw in text:
                score += 0.15
        return min(score, 1.0)
