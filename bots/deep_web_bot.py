"""
Deep Web Bot for collecting data from deep web sources
Collects from pastebin sites, forums, and semi-public platforms
"""

import asyncio
import aiohttp
import logging
import json
import re
import hashlib
import os
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin, urlparse, parse_qs
from bs4 import BeautifulSoup
import tldextract
from .base_bot import BaseBot
from models import DataSource, RawData, Entity


class DeepWebBot(BaseBot):
    """
    Bot for collecting data from deep web sources
    Includes pastebin sites, forums, and other semi-public platforms
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        default_config = {
            'max_pages_per_site': 100,
            'content_extraction': True,
            'keyword_filtering': True,
            'risk_keywords': [
                'hack', 'exploit', 'vulnerability', 'breach', 'leak',
                'malware', 'ransomware', 'phishing', 'cyber', 'security',
                'privacy', 'surveillance', 'encryption', 'backdoor',
                'dump', 'paste', 'leak', 'credential', 'password'
            ],
            'pastebin_patterns': [
                r'pastebin\.com/[a-zA-Z0-9]+',
                r'ghostbin\.co/[a-zA-Z0-9]+',
                r'rentry\.co/[a-zA-Z0-9]+',
                r'paste\.ee/[a-zA-Z0-9]+',
                r'paste\.gg/[a-zA-Z0-9]+'
            ],
            'forum_patterns': [
                r'forum\.[a-zA-Z0-9.-]+',
                r'board\.[a-zA-Z0-9.-]+',
                r'community\.[a-zA-Z0-9.-]+'
            ],
            'file_extensions': ['.txt', '.csv', '.json', '.xml', '.sql', '.log'],
            'max_file_size': 100 * 1024 * 1024,  # 100MB
            'respect_robots_txt': True,
            'delay_between_requests': (2, 5)  # Random delay range in seconds
        }
        
        if config:
            default_config.update(config)
        
        super().__init__("DeepWebBot", "deep", default_config)
        
        # Deep web specific settings
        self.visited_urls = set()
        self.site_page_counts = {}
        self.robots_cache = {}
        
    async def collect_data(self, source: DataSource) -> List[Dict[str, Any]]:
        """Collect data from a deep web source"""
        try:
            self.logger.info(f"Starting deep web data collection from {source.name}")
            
            collected_data = []
            start_url = source.url
            
            # Parse source configuration
            source_config = json.loads(source.config_json) if source.config_json else {}
            max_pages = source_config.get('max_pages_per_site', self.config['max_pages_per_site'])
            
            # Check robots.txt if enabled
            if self.config['respect_robots_txt']:
                await self._check_robots_txt(start_url)
            
            # Determine source type and collect accordingly
            if self._is_pastebin_site(start_url):
                collected_data = await self._collect_from_pastebin(start_url, max_pages, source)
            elif self._is_forum_site(start_url):
                collected_data = await self._collect_from_forum(start_url, max_pages, source)
            else:
                collected_data = await self._collect_generic(start_url, max_pages, source)
            
            self.logger.info(f"Collected {len(collected_data)} items from {source.name}")
            return collected_data
            
        except Exception as e:
            self.logger.error(f"Error collecting data from {source.name}: {e}")
            await self._log_bot_status('error', f"Collection failed: {str(e)}")
            return []
    
    def _is_pastebin_site(self, url: str) -> bool:
        """Check if URL is a pastebin-like site"""
        url_lower = url.lower()
        for pattern in self.config['pastebin_patterns']:
            if re.search(pattern, url_lower):
                return True
        return False
    
    def _is_forum_site(self, url: str) -> bool:
        """Check if URL is a forum-like site"""
        url_lower = url.lower()
        for pattern in self.config['forum_patterns']:
            if re.search(pattern, url_lower):
                return True
        return False
    
    async def _check_robots_txt(self, base_url: str):
        """Check robots.txt for crawling restrictions"""
        try:
            robots_url = urljoin(base_url, '/robots.txt')
            response = await self._make_request(robots_url)
            
            if response and response.status == 200:
                robots_content = await response.text()
                self.robots_cache[base_url] = robots_content
                
                # Parse robots.txt for disallowed paths
                disallowed = []
                for line in robots_content.split('\n'):
                    if line.startswith('Disallow:'):
                        path = line.split(':', 1)[1].strip()
                        disallowed.append(path)
                
                self.logger.info(f"Robots.txt found for {base_url}, disallowed paths: {disallowed}")
                
        except Exception as e:
            self.logger.debug(f"Could not fetch robots.txt for {base_url}: {e}")
    
    async def _collect_from_pastebin(self, start_url: str, max_pages: int, source: DataSource) -> List[Dict[str, Any]]:
        """Collect data from pastebin-like sites"""
        collected_data = []
        
        try:
            # Get the main page
            response = await self._make_request(start_url)
            if not response or response.status != 200:
                return collected_data
            
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract paste links
            paste_links = self._extract_paste_links(soup, start_url)
            
            # Collect from each paste
            for paste_url in paste_links[:max_pages]:
                try:
                    paste_data = await self._collect_paste_content(paste_url, source)
                    if paste_data:
                        collected_data.append(paste_data)
                    
                    # Rate limiting
                    delay = random.uniform(*self.config['delay_between_requests'])
                    await asyncio.sleep(delay)
                    
                except Exception as e:
                    self.logger.error(f"Error collecting from paste {paste_url}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error collecting from pastebin site {start_url}: {e}")
        
        return collected_data
    
    def _extract_paste_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract links to individual pastes"""
        links = []
        
        # Common selectors for paste links
        selectors = [
            'a[href*="/"]',  # Links with path
            '.paste-link',    # Common class names
            '.entry a',
            'a[href*="paste"]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href:
                    absolute_url = urljoin(base_url, href)
                    if self._is_valid_paste_url(absolute_url):
                        links.append(absolute_url)
        
        return list(set(links))  # Remove duplicates
    
    def _is_valid_paste_url(self, url: str) -> bool:
        """Check if URL is a valid paste URL"""
        # Check if URL matches pastebin patterns
        for pattern in self.config['pastebin_patterns']:
            if re.search(pattern, url):
                return True
        
        # Check if URL has a reasonable length (paste IDs are usually short)
        path = urlparse(url).path
        if len(path.strip('/')) <= 20:  # Most paste IDs are short
            return True
        
        return False
    
    async def _collect_paste_content(self, paste_url: str, source: DataSource) -> Optional[Dict[str, Any]]:
        """Collect content from a single paste"""
        try:
            response = await self._make_request(paste_url)
            if not response or response.status != 200:
                return None
            
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract paste content
            paste_content = self._extract_paste_text(soup)
            if not paste_content:
                return None
            
            # Check if content is relevant
            if not self._is_content_relevant(paste_content):
                return None
            
            # Extract title (if available)
            title = self._extract_paste_title(soup, paste_url)
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(paste_content, title)
            
            # Extract metadata
            metadata = self._extract_paste_metadata(soup, response.headers)
            
            paste_data = {
                'url': paste_url,
                'title': title,
                'content': paste_content,
                'raw_html': content,
                'content_type': 'text/plain',
                'metadata': metadata,
                'risk_score': risk_score,
                'keywords': self._extract_keywords(paste_content),
                'tags': f"type:paste,source:{source.category}",
                'risk_keywords': self._extract_risk_keywords(paste_content),
                'search_text': f"{title} {paste_content}",
                'file_path': None,
                'file_hash': self._calculate_content_hash(content)
            }
            
            return paste_data
            
        except Exception as e:
            self.logger.error(f"Error collecting paste content from {paste_url}: {e}")
            return None
    
    def _extract_paste_text(self, soup: BeautifulSoup) -> str:
        """Extract text content from paste"""
        # Common selectors for paste content
        selectors = [
            '#paste',           # Pastebin
            '.paste',           # Generic
            '.content',         # Common
            'pre',              # Preformatted text
            '.text',            # Text content
            '#content'          # Content area
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        # Fallback: try to find any large text block
        text_elements = soup.find_all(['pre', 'div', 'p'])
        for element in text_elements:
            text = element.get_text(strip=True)
            if len(text) > 100:  # Assume large text blocks are content
                return text
        
        return ""
    
    def _extract_paste_title(self, soup: BeautifulSoup, url: str) -> str:
        """Extract title from paste"""
        # Try to find title in various places
        title = soup.find('title')
        if title:
            title_text = title.get_text(strip=True)
            if title_text and title_text.lower() != 'untitled':
                return title_text
        
        # Try to find heading
        heading = soup.find(['h1', 'h2', 'h3'])
        if heading:
            return heading.get_text(strip=True)
        
        # Use URL as fallback
        path = urlparse(url).path
        if path and path != '/':
            return path.strip('/').replace('-', ' ').replace('_', ' ')
        
        return "Untitled Paste"
    
    def _extract_paste_metadata(self, soup: BeautifulSoup, headers: Dict[str, str]) -> Dict[str, Any]:
        """Extract metadata from paste"""
        metadata = {
            'headers': dict(headers),
            'meta_tags': {},
            'paste_info': {}
        }
        
        # Extract meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata['meta_tags'][name] = content
        
        # Try to extract paste-specific information
        info_selectors = [
            '.paste-info',
            '.metadata',
            '.info',
            '.details'
        ]
        
        for selector in info_selectors:
            element = soup.select_one(selector)
            if element:
                metadata['paste_info'][selector] = element.get_text(strip=True)
        
        return metadata
    
    async def _collect_from_forum(self, start_url: str, max_pages: int, source: DataSource) -> List[Dict[str, Any]]:
        """Collect data from forum-like sites"""
        collected_data = []
        
        try:
            # Get the main forum page
            response = await self._make_request(start_url)
            if not response or response.status != 200:
                return collected_data
            
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract forum thread links
            thread_links = self._extract_forum_threads(soup, start_url)
            
            # Collect from each thread
            for thread_url in thread_links[:max_pages]:
                try:
                    thread_data = await self._collect_forum_thread(thread_url, source)
                    if thread_data:
                        collected_data.append(thread_data)
                    
                    # Rate limiting
                    delay = random.uniform(*self.config['delay_between_requests'])
                    await asyncio.sleep(delay)
                    
                except Exception as e:
                    self.logger.error(f"Error collecting from thread {thread_url}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error collecting from forum site {start_url}: {e}")
        
        return collected_data
    
    def _extract_forum_threads(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract links to forum threads"""
        links = []
        
        # Common selectors for forum threads
        selectors = [
            'a[href*="thread"]',
            'a[href*="topic"]',
            'a[href*="post"]',
            '.thread-title a',
            '.topic-title a',
            '.forum-thread a'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                href = element.get('href')
                if href:
                    absolute_url = urljoin(base_url, href)
                    if self._is_valid_forum_url(absolute_url):
                        links.append(absolute_url)
        
        return list(set(links))
    
    def _is_valid_forum_url(self, url: str) -> bool:
        """Check if URL is a valid forum thread URL"""
        path = urlparse(url).path
        
        # Check for common forum patterns
        forum_patterns = [
            r'/thread/',
            r'/topic/',
            r'/post/',
            r'/forum/',
            r'/board/'
        ]
        
        for pattern in forum_patterns:
            if re.search(pattern, path):
                return True
        
        return False
    
    async def _collect_forum_thread(self, thread_url: str, source: DataSource) -> Optional[Dict[str, Any]]:
        """Collect content from a forum thread"""
        try:
            response = await self._make_request(thread_url)
            if not response or response.status != 200:
                return None
            
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract thread content
            thread_content = self._extract_thread_content(soup)
            if not thread_content:
                return None
            
            # Check if content is relevant
            if not self._is_content_relevant(thread_content):
                return None
            
            # Extract title
            title = self._extract_thread_title(soup, thread_url)
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(thread_content, title)
            
            # Extract metadata
            metadata = self._extract_thread_metadata(soup, response.headers)
            
            thread_data = {
                'url': thread_url,
                'title': title,
                'content': thread_content,
                'raw_html': content,
                'content_type': 'text/html',
                'metadata': metadata,
                'risk_score': risk_score,
                'keywords': self._extract_keywords(thread_content),
                'tags': f"type:forum,source:{source.category}",
                'risk_keywords': self._extract_risk_keywords(thread_content),
                'search_text': f"{title} {thread_content}",
                'file_path': None,
                'file_hash': self._calculate_content_hash(content)
            }
            
            return thread_data
            
        except Exception as e:
            self.logger.error(f"Error collecting thread content from {thread_url}: {e}")
            return None
    
    def _extract_thread_content(self, soup: BeautifulSoup) -> str:
        """Extract content from forum thread"""
        # Common selectors for forum content
        selectors = [
            '.post-content',
            '.message-content',
            '.thread-content',
            '.forum-post',
            '.post-body',
            '.message-body'
        ]
        
        content_parts = []
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and len(text) > 50:  # Only include substantial content
                    content_parts.append(text)
        
        if content_parts:
            return ' '.join(content_parts)
        
        # Fallback: try to find any text content
        text_elements = soup.find_all(['p', 'div'])
        for element in text_elements:
            text = element.get_text(strip=True)
            if text and len(text) > 100:
                content_parts.append(text)
        
        return ' '.join(content_parts)
    
    def _extract_thread_title(self, soup: BeautifulSoup, url: str) -> str:
        """Extract title from forum thread"""
        # Try to find title in various places
        title = soup.find('title')
        if title:
            title_text = title.get_text(strip=True)
            if title_text:
                return title_text
        
        # Try to find heading
        heading = soup.find(['h1', 'h2', 'h3'])
        if heading:
            return heading.get_text(strip=True)
        
        # Use URL as fallback
        path = urlparse(url).path
        if path and path != '/':
            return path.strip('/').replace('-', ' ').replace('_', ' ')
        
        return "Untitled Thread"
    
    def _extract_thread_metadata(self, soup: BeautifulSoup, headers: Dict[str, str]) -> Dict[str, Any]:
        """Extract metadata from forum thread"""
        metadata = {
            'headers': dict(headers),
            'meta_tags': {},
            'thread_info': {}
        }
        
        # Extract meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata['meta_tags'][name] = content
        
        # Try to extract thread-specific information
        info_selectors = [
            '.thread-info',
            '.post-info',
            '.message-info',
            '.forum-info'
        ]
        
        for selector in info_selectors:
            element = soup.select_one(selector)
            if element:
                metadata['thread_info'][selector] = element.get_text(strip=True)
        
        return metadata
    
    async def _collect_generic(self, start_url: str, max_pages: int, source: DataSource) -> List[Dict[str, Any]]:
        """Generic collection method for unknown site types"""
        collected_data = []
        
        try:
            # Get the main page
            response = await self._make_request(start_url)
            if not response or response.status != 200:
                return collected_data
            
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract all links
            links = self._extract_generic_links(soup, start_url)
            
            # Collect from each link
            for link_url in links[:max_pages]:
                try:
                    page_data = await self._collect_generic_page(link_url, source)
                    if page_data:
                        collected_data.append(page_data)
                    
                    # Rate limiting
                    delay = random.uniform(*self.config['delay_between_requests'])
                    await asyncio.sleep(delay)
                    
                except Exception as e:
                    self.logger.error(f"Error collecting from page {link_url}: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error collecting from generic site {start_url}: {e}")
        
        return collected_data
    
    def _extract_generic_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract links from generic site"""
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href and not href.startswith(('#', 'javascript:', 'mailto:')):
                absolute_url = urljoin(base_url, href)
                if self._is_valid_generic_url(absolute_url, base_url):
                    links.append(absolute_url)
        
        return list(set(links))
    
    def _is_valid_generic_url(self, url: str, base_url: str) -> bool:
        """Check if URL is valid for generic collection"""
        # Only include URLs from the same domain
        base_domain = tldextract.extract(base_url).domain
        url_domain = tldextract.extract(url).domain
        
        if base_domain != url_domain:
            return False
        
        # Exclude common non-content paths
        exclude_patterns = [
            r'/admin/',
            r'/login',
            r'/logout',
            r'/register',
            r'/search',
            r'/api/',
            r'/static/',
            r'/assets/',
            r'/css/',
            r'/js/',
            r'/images/'
        ]
        
        path = urlparse(url).path
        for pattern in exclude_patterns:
            if re.search(pattern, path):
                return False
        
        return True
    
    async def _collect_generic_page(self, page_url: str, source: DataSource) -> Optional[Dict[str, Any]]:
        """Collect content from a generic page"""
        try:
            response = await self._make_request(page_url)
            if not response or response.status != 200:
                return None
            
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract page content
            page_content = self._extract_generic_content(soup)
            if not page_content:
                return None
            
            # Check if content is relevant
            if not self._is_content_relevant(page_content):
                return None
            
            # Extract title
            title = self._extract_generic_title(soup, page_url)
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(page_content, title)
            
            # Extract metadata
            metadata = self._extract_generic_metadata(soup, response.headers)
            
            page_data = {
                'url': page_url,
                'title': title,
                'content': page_content,
                'raw_html': content,
                'content_type': 'text/html',
                'metadata': metadata,
                'risk_score': risk_score,
                'keywords': self._extract_keywords(page_content),
                'tags': f"type:generic,source:{source.category}",
                'risk_keywords': self._extract_risk_keywords(page_content),
                'search_text': f"{title} {page_content}",
                'file_path': None,
                'file_hash': self._calculate_content_hash(content)
            }
            
            return page_data
            
        except Exception as e:
            self.logger.error(f"Error collecting page content from {page_url}: {e}")
            return None
    
    def _extract_generic_content(self, soup: BeautifulSoup) -> str:
        """Extract content from generic page"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # Try to find main content areas
        main_selectors = [
            'main', 'article', '.content', '.main-content', '.post-content',
            '.entry-content', '.article-content', '#content', '#main'
        ]
        
        for selector in main_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(separator=' ', strip=True)
        
        # Fallback to body text
        return soup.get_text(separator=' ', strip=True)
    
    def _extract_generic_title(self, soup: BeautifulSoup, url: str) -> str:
        """Extract title from generic page"""
        # Try to find title in various places
        title = soup.find('title')
        if title:
            title_text = title.get_text(strip=True)
            if title_text:
                return title_text
        
        # Try to find heading
        heading = soup.find(['h1', 'h2', 'h3'])
        if heading:
            return heading.get_text(strip=True)
        
        # Use URL as fallback
        path = urlparse(url).path
        if path and path != '/':
            return path.strip('/').replace('-', ' ').replace('_', ' ')
        
        return "Untitled Page"
    
    def _extract_generic_metadata(self, soup: BeautifulSoup, headers: Dict[str, str]) -> Dict[str, Any]:
        """Extract metadata from generic page"""
        metadata = {
            'headers': dict(headers),
            'meta_tags': {},
            'page_info': {}
        }
        
        # Extract meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata['meta_tags'][name] = content
        
        return metadata
    
    def _is_content_relevant(self, content: str) -> bool:
        """Check if content is relevant based on keywords"""
        if not self.config['keyword_filtering']:
            return True
        
        text = content.lower()
        
        # Check for risk keywords
        for keyword in self.config['risk_keywords']:
            if keyword.lower() in text:
                return True
        
        # Check for cybersecurity terms
        cyber_terms = ['security', 'cyber', 'hack', 'vulnerability', 'breach']
        if any(term in text for term in cyber_terms):
            return True
        
        return False
    
    def _calculate_risk_score(self, content: str, title: str) -> float:
        """Calculate risk score based on content analysis"""
        score = 0.0
        text = f"{title} {content}".lower()
        
        # High risk keywords
        high_risk = ['exploit', 'malware', 'ransomware', 'breach', 'leak', 'dump']
        for keyword in high_risk:
            if keyword in text:
                score += 0.3
        
        # Medium risk keywords
        medium_risk = ['hack', 'vulnerability', 'attack', 'threat', 'paste']
        for keyword in medium_risk:
            if keyword in text:
                score += 0.2
        
        # Low risk keywords
        low_risk = ['security', 'cyber', 'privacy', 'encryption']
        for keyword in low_risk:
            if keyword in text:
                score += 0.1
        
        return min(score, 1.0)
    
    def _extract_risk_keywords(self, content: str) -> str:
        """Extract risk-related keywords from content"""
        if not content:
            return ""
        
        text = content.lower()
        found_keywords = []
        
        for keyword in self.config['risk_keywords']:
            if keyword.lower() in text:
                found_keywords.append(keyword)
        
        return ','.join(found_keywords)
    
    def _extract_keywords(self, content: str) -> str:
        """Extract keywords from content"""
        if not content:
            return ""
        
        # Simple keyword extraction (can be enhanced with NLP)
        words = re.findall(r'\b\w+\b', content.lower())
        word_freq = {}
        
        for word in words:
            if len(word) > 3:  # Only words longer than 3 characters
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Get top 10 most frequent words
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
        return ','.join([word for word, freq in top_words])
    
    def _calculate_content_hash(self, content: str) -> str:
        """Calculate hash of content for deduplication"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def run_collection_cycle(self, sources: List[DataSource]):
        """Run a complete collection cycle for multiple sources"""
        try:
            self.logger.info("Starting deep web collection cycle")
            
            total_collected = 0
            start_time = time.time()
            
            for source in sources:
                if source.source_type in ['deep', 'deep_web'] and source.enabled:
                    try:
                        collected = await self.collect_data(source)
                        total_collected += len(collected)
                        
                        # Process collected data
                        for data in collected:
                            raw_data_record = await self.process_raw_data(data, source)
                            if raw_data_record:
                                await self.extract_entities(raw_data_record)
                        
                        # Update source last scraped time
                        source.last_scraped = datetime.utcnow()
                        db.session.commit()
                        
                    except Exception as e:
                        self.logger.error(f"Error processing source {source.name}: {e}")
                        continue
            
            execution_time = time.time() - start_time
            await self._log_bot_status(
                'success', 
                f"Collection cycle completed. Collected {total_collected} items.",
                total_collected,
                execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Error in collection cycle: {e}")
            await self._log_bot_status('error', f"Collection cycle failed: {str(e)}")