"""
OSINT Feed Bot for consuming APIs and RSS feeds
Integrates with HN, Reddit, PrivacyGuides, and CVE (if available)
"""

import asyncio
import logging
import json
import time
import random
from datetime import datetime
from typing import Dict, List, Optional, Any

from .base_bot import BaseBot
from models import DataSource
from scrapers.hackernews import scrape_hackernews
from scrapers.reddit import scrape_reddit
from scrapers.privacyguides import scrape_privacyguides


class OSINTFeedBot(BaseBot):
    """
    Bot for collecting data from OSINT feeds (APIs, RSS, public data services)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        default_config = {
            'rate_limit_per_service': {
                'hackernews': (1, 3),
                'reddit': (2, 5),
                'privacyguides': (2, 5),
            },
            'keyword_filtering': True,
            'risk_keywords': [
                'exploit', 'vulnerability', 'cve', 'zero-day', 'ransomware',
                'malware', 'breach', 'leak', 'hacker', 'security', 'privacy'
            ]
        }
        if config:
            default_config.update(config)
        super().__init__("OSINTFeedBot", "osint", default_config)
    
    async def collect_data(self, source: DataSource) -> List[Dict[str, Any]]:
        try:
            self.logger.info(f"Collecting OSINT feed from {source.name}")
            name = source.name.lower()
            if 'hacker' in name:
                items = await fetch_hackernews_items_async(self)
                return [self._map_hn_item(i, source) for i in items if self._passes_filter_dict(i)]
            if 'reddit' in name:
                items = await fetch_reddit_items_async(self)
                return [self._map_reddit_item(i, source) for i in items if self._passes_filter_dict(i)]
            if 'privacyguides' in name or 'privacy guides' in name:
                items = await fetch_privacy_guides_async(self)
                return [self._map_pg_item(i, source) for i in items if self._passes_filter_dict(i)]
            return []
        except Exception as e:
            self.logger.error(f"OSINT feed collection error for {source.name}: {e}")
            return []
    
    def _passes_filter_dict(self, item: Dict[str, Any]) -> bool:
        text = json.dumps(item).lower()
        return any(kw in text for kw in self.config['risk_keywords'])
    
    def _map_hn_item(self, item: Dict[str, Any], source: DataSource) -> Dict[str, Any]:
        title = item.get('title', '')
        url = item.get('url')
        text = item.get('summary', '')
        return {
            'url': url,
            'title': title,
            'content': text,
            'raw_html': None,
            'content_type': 'text/plain',
            'metadata': {'source': item.get('source')},
            'risk_score': 0.4 if 'cve' in (title or '').lower() else 0.2,
            'keywords': ','.join(self.config['risk_keywords']),
            'tags': f"source:{source.category},feed:hackernews",
            'risk_keywords': ','.join([kw for kw in self.config['risk_keywords'] if kw in (title or '').lower() or kw in (text or '').lower()]),
            'search_text': f"{title} {text}",
            'file_path': None,
            'file_hash': None
        }
    
    def _map_reddit_item(self, item: Dict[str, Any], source: DataSource) -> Dict[str, Any]:
        title = item.get('title', '')
        text = item.get('summary', '')
        url = item.get('url')
        return {
            'url': url,
            'title': title,
            'content': text,
            'raw_html': None,
            'content_type': 'text/plain',
            'metadata': {'source': item.get('source')},
            'risk_score': 0.3,
            'keywords': ','.join(self.config['risk_keywords']),
            'tags': f"source:{source.category},feed:reddit",
            'risk_keywords': ','.join([kw for kw in self.config['risk_keywords'] if kw in (title or '').lower() or kw in (text or '').lower()]),
            'search_text': f"{title} {text}",
            'file_path': None,
            'file_hash': None
        }
    
    def _map_pg_item(self, item: Dict[str, Any], source: DataSource) -> Dict[str, Any]:
        title = item.get('title', '')
        text = item.get('summary', '')
        url = item.get('url')
        return {
            'url': url,
            'title': title,
            'content': text,
            'raw_html': None,
            'content_type': 'text/plain',
            'metadata': {'source': item.get('source')},
            'risk_score': 0.3,
            'keywords': ','.join(self.config['risk_keywords']),
            'tags': f"source:{source.category},feed:privacyguides",
            'risk_keywords': ','.join([kw for kw in self.config['risk_keywords'] if kw in (title or '').lower() or kw in (text or '').lower()]),
            'search_text': f"{title} {text}",
            'file_path': None,
            'file_hash': None
        }


# Async wrappers around existing scrapers (which return lists of dicts)
async def fetch_hackernews_items_async(bot: BaseBot) -> List[Dict[str, Any]]:
    try:
        items = await asyncio.to_thread(scrape_hackernews)
        await asyncio.sleep(random.uniform(*bot.config['rate_limit_per_service']['hackernews']))
        return items or []
    except Exception:
        return []

async def fetch_reddit_items_async(bot: BaseBot) -> List[Dict[str, Any]]:
    try:
        items = await asyncio.to_thread(scrape_reddit)
        await asyncio.sleep(random.uniform(*bot.config['rate_limit_per_service']['reddit']))
        return items or []
    except Exception:
        return []

async def fetch_privacy_guides_async(bot: BaseBot) -> List[Dict[str, Any]]:
    try:
        items = await asyncio.to_thread(scrape_privacyguides)
        await asyncio.sleep(random.uniform(*bot.config['rate_limit_per_service']['privacyguides']))
        return items or []
    except Exception:
        return []
