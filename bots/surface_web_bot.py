"""
Surface Web Bot for collecting data from public websites
Collects from news sites, forums, social media, and public repositories
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


class SurfaceWebBot(BaseBot):
    """
    Bot for collecting data from surface web sources
    Includes news sites, forums, social media, and public repositories
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        default_config = {
            'max_depth': 4,  # Increased from 3 to 4
            'max_pages_per_site': 100,  # Increased from 50 to 100
            'file_download': True,
            'content_extraction': True,
            'keyword_filtering': False,  # Changed to False to collect ALL content
            'risk_keywords': [
                'hack', 'exploit', 'vulnerability', 'breach', 'leak',
                'malware', 'ransomware', 'phishing', 'cyber', 'security',
                'privacy', 'surveillance', 'encryption', 'backdoor'
            ],
            'allowed_domains': [],
            'blocked_domains': [],
            'file_extensions': ['.pdf', '.txt', '.csv', '.json', '.xml', '.sql'],
            'max_file_size': 50 * 1024 * 1024  # 50MB
        }
        
        if config:
            default_config.update(config)
        
        super().__init__("SurfaceWebBot", "surface", default_config)
        
        # Surface web specific settings
        self.visited_urls = set()
        self.site_page_counts = {}
        self.content_cache = {}
        
    async def collect_data(self, source: DataSource) -> List[Dict[str, Any]]:
        """Collect data from a surface web source"""
        try:
            self.logger.info(f"Starting data collection from {source.name}")
            
            collected_data = []
            start_url = source.url
            
            # Parse source configuration
            source_config = json.loads(source.config_json) if source.config_json else {}
            max_depth = source_config.get('max_depth', self.config['max_depth'])
            max_pages = source_config.get('max_pages_per_site', self.config['max_pages_per_site'])
            
            # Start crawling from the source URL
            await self._crawl_site(start_url, max_depth, max_pages, collected_data, source)
            
            self.logger.info(f"Collected {len(collected_data)} items from {source.name}")
            return collected_data
            
        except Exception as e:
            self.logger.error(f"Error collecting data from {source.name}: {e}")
            await self._log_bot_status('error', f"Collection failed: {str(e)}")
            return []
    
    async def _crawl_site(self, start_url: str, max_depth: int, max_pages: int, 
                          collected_data: List[Dict[str, Any]], source: DataSource):
        """Crawl a website recursively"""
        queue = [(start_url, 0)]  # (url, depth)
        visited = set()
        
        while queue and len(visited) < max_pages:
            current_url, depth = queue.pop(0)
            
            if current_url in visited or depth > max_depth:
                continue
            
            visited.add(current_url)
            
            try:
                # Collect data from current page
                page_data = await self._collect_page_data(current_url, source)
                if page_data:
                    collected_data.append(page_data)
                
                # Extract links for next level if not at max depth
                if depth < max_depth:
                    links = await self._extract_links(current_url)
                    for link in links:
                        if link not in visited and len(visited) < max_pages:
                            queue.append((link, depth + 1))
                
                # Rate limiting
                await asyncio.sleep(random.uniform(1, 3))
                
            except Exception as e:
                self.logger.error(f"Error processing {current_url}: {e}")
                continue
    
    async def _collect_page_data(self, url: str, source: DataSource) -> Optional[Dict[str, Any]]:
        """Collect data from a single page"""
        try:
            response = await self._make_request(url)
            if not response or response.status != 200:
                return None
            
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract page information
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ''
            
            # Extract main content
            main_content = self._extract_main_content(soup)
            
            # Check if content is relevant
            if not self._is_content_relevant(main_content, title_text):
                return None
            
            # Extract metadata
            metadata = self._extract_metadata(soup, response.headers)
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(main_content, title_text)
            
            # Extract keywords and tags
            keywords = get_keywords(main_content) if main_content else []
            sentiment = analyze_sentiment(main_content) if main_content else 'neutral'
            
            # Check for downloadable files
            files = await self._extract_downloadable_files(soup, url)
            
            page_data = {
                'url': url,
                'title': title_text,
                'content': main_content,
                'raw_html': content,
                'content_type': 'text/html',
                'metadata': metadata,
                'risk_score': risk_score,
                'keywords': ','.join(keywords),
                'tags': f"sentiment:{sentiment},source:{source.category}",
                'risk_keywords': self._extract_risk_keywords(main_content),
                'search_text': f"{title_text} {main_content}",
                'file_path': files[0] if files else None,
                'file_hash': self._calculate_content_hash(content)
            }
            
            return page_data
            
        except Exception as e:
            self.logger.error(f"Error collecting page data from {url}: {e}")
            return None
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from HTML, excluding navigation and ads"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside", "form"]):
            script.decompose()
        
        # Try to find main content areas with more comprehensive selectors
        main_selectors = [
            'main', 'article', '.content', '.main-content', '.post-content',
            '.entry-content', '.article-content', '#content', '#main', '.post',
            '.story', '.news-content', '.article-body', '.post-body',
            '.content-area', '.main', '.primary', '.entry'
        ]
        
        for selector in main_selectors:
            element = soup.select_one(selector)
            if element:
                # Get text with better formatting
                text = element.get_text(separator='\n', strip=True)
                if len(text) > 100:  # Ensure we have substantial content
                    return text
        
        # Try to find paragraphs and text blocks
        paragraphs = soup.find_all(['p', 'div', 'section'])
        if paragraphs:
            content_parts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 20:  # Only include substantial paragraphs
                    content_parts.append(text)
            
            if content_parts:
                return '\n\n'.join(content_parts)
        
        # Fallback to body text but clean it up
        body_text = soup.get_text(separator='\n', strip=True)
        # Remove excessive whitespace and empty lines
        lines = [line.strip() for line in body_text.split('\n') if line.strip()]
        return '\n'.join(lines)
    
    def _extract_metadata(self, soup: BeautifulSoup, headers: Dict[str, str]) -> Dict[str, Any]:
        """Extract metadata from HTML and headers"""
        metadata = {
            'headers': dict(headers),
            'meta_tags': {},
            'links': []
        }
        
        # Extract meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata['meta_tags'][name] = content
        
        # Extract links
        for link in soup.find_all('a', href=True):
            metadata['links'].append({
                'text': link.get_text(strip=True),
                'href': link['href'],
                'title': link.get('title', '')
            })
        
        return metadata
    
    def _is_content_relevant(self, content: str, title: str) -> bool:
        """Check if content is relevant based on keywords"""
        if not self.config['keyword_filtering']:
            return True
        
        # If keyword filtering is disabled, accept all substantial content
        if len(content) < 50:  # Reject very short content
            return False
        
        text = f"{title} {content}".lower()
        
        # Check for risk keywords
        for keyword in self.config['risk_keywords']:
            if keyword.lower() in text:
                return True
        
        # Check for cybersecurity terms
        cyber_terms = ['security', 'cyber', 'hack', 'vulnerability', 'breach', 
                      'technology', 'software', 'internet', 'data', 'privacy']
        if any(term in text for term in cyber_terms):
            return True
        
        # Accept content with substantial length even without specific keywords
        if len(content) > 200:
            return True
        
        return False
    
    def _calculate_risk_score(self, content: str, title: str) -> float:
        """Calculate risk score based on content analysis"""
        score = 0.0
        text = f"{title} {content}".lower()
        
        # High risk keywords
        high_risk = ['exploit', 'malware', 'ransomware', 'breach', 'leak']
        for keyword in high_risk:
            if keyword in text:
                score += 0.3
        
        # Medium risk keywords
        medium_risk = ['hack', 'vulnerability', 'attack', 'threat']
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
    
    async def _extract_downloadable_files(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract downloadable file links"""
        if not self.config['file_download']:
            return []
        
        files = []
        file_extensions = self.config['file_extensions']
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(href.lower().endswith(ext) for ext in file_extensions):
                file_url = urljoin(base_url, href)
                
                # Check file size before downloading
                try:
                    file_info = await self._get_file_info(file_url)
                    if file_info and file_info['size'] <= self.config['max_file_size']:
                        downloaded_path = await self._download_file(file_url)
                        if downloaded_path:
                            files.append(downloaded_path)
                except Exception as e:
                    self.logger.warning(f"Failed to process file {file_url}: {e}")
        
        return files
    
    async def _get_file_info(self, file_url: str) -> Optional[Dict[str, Any]]:
        """Get file information without downloading"""
        try:
            async with self.session.head(file_url) as response:
                if response.status == 200:
                    size = int(response.headers.get('content-length', 0))
                    content_type = response.headers.get('content-type', '')
                    return {
                        'size': size,
                        'content_type': content_type
                    }
        except Exception as e:
            self.logger.debug(f"Failed to get file info for {file_url}: {e}")
        
        return None
    
    async def _download_file(self, file_url: str) -> Optional[str]:
        """Download a file to local storage"""
        try:
            async with self.session.get(file_url) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    # Create downloads directory if it doesn't exist
                    os.makedirs('downloads', exist_ok=True)
                    
                    # Generate filename
                    filename = os.path.basename(urlparse(file_url).path)
                    if not filename:
                        filename = hashlib.md5(file_url.encode()).hexdigest()[:10]
                    
                    file_path = os.path.join('downloads', filename)
                    
                    # Write file
                    with open(file_path, 'wb') as f:
                        f.write(content)
                    
                    return file_path
                    
        except Exception as e:
            self.logger.error(f"Failed to download file {file_url}: {e}")
        
        return None
    
    async def _extract_links(self, url: str) -> List[str]:
        """Extract links from a page for crawling"""
        try:
            response = await self._make_request(url)
            if not response or response.status != 200:
                return []
            
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            
            links = []
            base_domain = tldextract.extract(url).domain
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                absolute_url = urljoin(url, href)
                
                # Only include links to the same domain
                link_domain = tldextract.extract(absolute_url).domain
                if link_domain == base_domain:
                    # Filter out common non-content links
                    if not any(skip in absolute_url.lower() for skip in [
                        '/tag/', '/category/', '/author/', '/page/', '/comment',
                        '/login', '/register', '/admin', '/wp-admin', '/feed'
                    ]):
                        links.append(absolute_url)
            
            # Return more links for better coverage
            return links[:50]  # Increased from 20 to 50
            
        except Exception as e:
            self.logger.error(f"Error extracting links from {url}: {e}")
            return []
    
    def _calculate_content_hash(self, content: str) -> str:
        """Calculate hash of content for deduplication"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    async def run_collection_cycle(self, sources: List[DataSource]):
        """Run a complete collection cycle for multiple sources"""
        try:
            self.logger.info("Starting surface web collection cycle")
            
            # Ensure we have a valid session
            if not self.session or self.session.closed:
                await self._setup_session()
            
            total_collected = 0
            start_time = time.time()
            
            for source in sources:
                if source.source_type in ['surface', 'surface_web'] and source.enabled:
                    try:
                        self.logger.info(f"Processing source: {source.name} ({source.url})")
                        
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
                        await asyncio.sleep(1)
                        
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
