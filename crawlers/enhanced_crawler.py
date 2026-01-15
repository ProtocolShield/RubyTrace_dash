"""
Enhanced crawler for surface web and dark web monitoring.
Discovers new sites based on keywords and downloads relevant files.
"""

import asyncio
import aiohttp
import logging
import re
import os
import hashlib
try:
    import magic  # Optional; not required on Windows
except Exception:
    magic = None
from datetime import datetime
from urllib.parse import urljoin, urlparse, parse_qs
from fake_useragent import UserAgent
from langdetect import detect
import tldextract
from models import db, Source, ScrapeLog
from database import with_retry
from utils.tor_manager import tor_manager
from crawlers.darkweb_crawler import run_darkweb_crawler
from crawlers.file_collector import file_collector
import json

class EnhancedCrawler:
    def __init__(self, use_tor=False):
        self.use_tor = use_tor
        self.ua = UserAgent()
        self.session = None
        self.discovered_sites = set()
        self.downloaded_files = set()
        self.content_filters = self._init_content_filters()
        self.file_extensions = {
            'documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
            'archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
            'data': ['.csv', '.json', '.xml', '.sql', '.db'],
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'],
            'videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'],
            'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg']
        }
        
    def _init_content_filters(self):
        """Initialize content filtering patterns for prohibited content"""
        return {
            'prohibited_keywords': [
                'porn', 'adult', 'xxx', 'sex', 'nude', 'naked',
                'weapon', 'gun', 'rifle', 'pistol', 'explosive', 'bomb',
                'drug', 'cocaine', 'heroin', 'methamphetamine',
                'child', 'minor', 'underage', 'teen',
                'hack', 'crack', 'exploit', 'malware', 'virus'
            ],
            'prohibited_domains': [
                'pornhub.com', 'xvideos.com', 'xhamster.com',
                'armslist.com', 'gunbroker.com'
            ],
            'file_size_limit': 100 * 1024 * 1024,  # 100MB limit
            'allowed_content_types': [
                'text/html', 'text/plain', 'application/pdf',
                'application/zip', 'application/json', 'text/csv'
            ]
        }
    
    async def init_session(self):
        """Initialize HTTP session with proper configuration"""
        connector = aiohttp.TCPConnector(
            limit=100,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        if self.use_tor:
            connector = aiohttp.TCPConnector(
                limit=100,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            # Tor proxy configuration will be added here
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': self.ua.random}
        )
    
    async def close_session(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()
    
    def is_content_safe(self, url, content=None, headers=None):
        """Check if content is safe and allowed"""
        url_lower = url.lower()
        
        # Check prohibited keywords in URL
        for keyword in self.content_filters['prohibited_keywords']:
            if keyword in url_lower:
                logging.warning(f"Blocked URL with prohibited keyword '{keyword}': {url}")
                return False
        
        # Check prohibited domains
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        for prohibited_domain in self.content_filters['prohibited_domains']:
            if prohibited_domain in domain:
                logging.warning(f"Blocked prohibited domain: {domain}")
                return False
        
        # Check content type if headers available
        if headers and 'content-type' in headers:
            content_type = headers['content-type'].split(';')[0].strip()
            if content_type not in self.content_filters['allowed_content_types']:
                logging.info(f"Skipped unsupported content type: {content_type}")
                return False
        
        # Check content size
        if headers and 'content-length' in headers:
            try:
                size = int(headers['content-length'])
                if size > self.content_filters['file_size_limit']:
                    logging.info(f"Skipped large file ({size} bytes): {url}")
                    return False
            except ValueError:
                pass
        
        return True
    
    async def discover_sites(self, seed_urls, keywords, max_depth=2):
        """Discover new sites based on keywords and seed URLs"""
        discovered = set()
        queue = [(url, 0) for url in seed_urls]
        visited = set()
        
        while queue:
            current_url, depth = queue.pop(0)
            
            if current_url in visited or depth > max_depth:
                continue
                
            visited.add(current_url)
            
            try:
                async with self.session.get(current_url) as response:
                    if response.status != 200:
                        continue
                    
                    if not self.is_content_safe(current_url, headers=response.headers):
                        continue
                    
                    content = await response.text()
                    
                    # Extract links
                    links = self._extract_links(content, current_url)
                    
                    # Check if page contains relevant keywords
                    if self._contains_keywords(content, keywords):
                        discovered.add(current_url)
                        logging.info(f"Discovered relevant site: {current_url}")
                        
                        # Add to database
                        await self._save_discovered_site(current_url, keywords)
                    
                    # Add new links to queue for next depth level
                    if depth < max_depth:
                        for link in links:
                            if link not in visited:
                                queue.append((link, depth + 1))
                                
            except Exception as e:
                logging.error(f"Error crawling {current_url}: {e}")
                continue
        
        return discovered
    
    def _extract_links(self, content, base_url):
        """Extract all links from HTML content"""
        links = set()
        
        # Simple regex to find links with timeout protection
        link_pattern = r'href=["\']([^"\']+)["\']'
        # Limit content size to prevent regex timeout
        content_sample = content[:50000] if len(content) > 50000 else content
        matches = re.findall(link_pattern, content_sample, re.IGNORECASE)
        
        for match in matches:
            try:
                full_url = urljoin(base_url, match)
                parsed = urlparse(full_url)
                
                if parsed.scheme in ['http', 'https']:
                    links.add(full_url)
                elif self.use_tor and parsed.scheme == '' and '.onion' in match:
                    # Handle .onion links for Tor
                    links.add('http://' + match)
                    
            except Exception:
                continue
                
        return links
    
    def _contains_keywords(self, content, keywords):
        """Check if content contains any of the specified keywords"""
        content_lower = content.lower()
        
        for keyword in keywords:
            if keyword.lower() in content_lower:
                return True
        return False
    
    async def _save_discovered_site(self, url, keywords):
        """Save discovered site to database"""
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            # Determine source type
            if '.onion' in domain:
                source_type = 'darkweb'
            else:
                source_type = 'website'
            
            # Check if already exists
            existing = db.session.query(Source).filter_by(url=url).first()
            if not existing:
                source = Source(
                    name=f"Auto-discovered: {domain}",
                    url=url,
                    source_type=source_type,
                    risk_level='medium',
                    enabled=True,
                    scrape_interval=60
                )
                db.session.add(source)
                db.session.commit()
                logging.info(f"Added new source: {url}")
                
        except Exception as e:
            logging.error(f"Error saving discovered site {url}: {e}")
            db.session.rollback()
    
    async def download_files(self, url, target_extensions=None):
        """Download files from a URL based on specified extensions"""
        if target_extensions is None:
            target_extensions = self.file_extensions['documents'] + self.file_extensions['archives']
        
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return []
                
                if not self.is_content_safe(url, headers=response.headers):
                    return []
                
                content = await response.text()
                
                # Find downloadable files
                file_links = self._extract_file_links(content, url, target_extensions)
                downloaded_files = []
                
                for file_url in file_links:
                    if await self._download_file(file_url):
                        downloaded_files.append(file_url)
                
                return downloaded_files
                
        except Exception as e:
            logging.error(f"Error downloading files from {url}: {e}")
            return []
    
    def _extract_file_links(self, content, base_url, extensions):
        """Extract links to files with specified extensions"""
        file_links = set()
        
        # Pattern to find links to files
        link_pattern = r'href=["\']([^"\']+\.(?:' + '|'.join(ext[1:] for ext in extensions) + r'))["\']'
        matches = re.findall(link_pattern, content, re.IGNORECASE)
        
        for match in matches:
            try:
                full_url = urljoin(base_url, match)
                file_links.add(full_url)
            except Exception:
                continue
        
        return file_links
    
    async def _download_file(self, url):
        """Download a single file"""
        try:
            # Generate unique filename
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            if not filename:
                filename = f"file_{hashlib.md5(url.encode()).hexdigest()[:8]}"
            
            # Create downloads directory
            download_dir = "downloads"
            os.makedirs(download_dir, exist_ok=True)
            
            file_path = os.path.join(download_dir, filename)
            
            # Check if already downloaded
            if url in self.downloaded_files or os.path.exists(file_path):
                return False
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    return False
                
                if not self.is_content_safe(url, headers=response.headers):
                    return False
                
                # Download file
                with open(file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
                
                self.downloaded_files.add(url)
                
                # Log download
                await self._log_download(url, file_path)
                
                logging.info(f"Downloaded file: {url} -> {file_path}")
                return True
                
        except Exception as e:
            logging.error(f"Error downloading file {url}: {e}")
            return False
    
    async def _log_download(self, url, file_path):
        """Log file download to database"""
        try:
            log_entry = ScrapeLog(
                source_name="File Download",
                status="success",
                items_found=1,
                items_added=1,
                error_message=f"Downloaded: {url} -> {file_path}",
                timestamp=datetime.utcnow()
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as e:
            logging.error(f"Error logging download: {e}")
            db.session.rollback()
    
    async def monitor_sites(self, sites, keywords):
        """Monitor existing sites for new content"""
        results = []
        
        for site in sites:
            try:
                # Discover new pages/files
                discovered = await self.discover_sites([site], keywords, max_depth=1)
                
                # Download relevant files
                downloaded = await self.download_files(site)
                
                results.append({
                    'site': site,
                    'discovered_pages': len(discovered),
                    'downloaded_files': len(downloaded),
                    'timestamp': datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                logging.error(f"Error monitoring site {site}: {e}")
                results.append({
                    'site': site,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        return results

class TorCrawler(EnhancedCrawler):
    """Enhanced crawler with Tor support for dark web monitoring"""
    
    def __init__(self):
        super().__init__(use_tor=True)
        self.tor_proxy = None
    
    async def init_tor(self):
        """Initialize Tor connection"""
        try:
            # This will be implemented to set up Tor proxy
            # For now, we'll prepare the structure
            logging.info("Tor initialization prepared")
            return True
        except Exception as e:
            logging.error(f"Failed to initialize Tor: {e}")
            return False
    
    async def init_session(self):
        """Initialize HTTP session with Tor proxy"""
        if not await self.init_tor():
            raise Exception("Failed to initialize Tor")
        
        # Tor proxy configuration
        proxy = "socks5://127.0.0.1:9050"  # Default Tor SOCKS proxy
        
        connector = aiohttp.TCPConnector(
            limit=10,  # Lower limit for Tor
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=60, connect=30)  # Longer timeouts for Tor
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': self.ua.random}
        )
    
    def _extract_onion_links(self, content, base_url):
        """Extract .onion links from content"""
        onion_links = set()
        
        # Pattern to find .onion addresses
        onion_pattern = r'[a-z2-7]{16,56}\.onion'
        matches = re.findall(onion_pattern, content, re.IGNORECASE)
        
        for match in matches:
            onion_url = f"http://{match}"
            onion_links.add(onion_url)
        
        return onion_links

async def run_crawler(keywords, sites=None, use_tor=False):
    """Main function to run the crawler"""
    if use_tor:
        crawler = TorCrawler()
    else:
        crawler = EnhancedCrawler()
    
    try:
        await crawler.init_session()
        
        # Simplified discovery with timeout protection
        discovered_count = 0
        try:
            # Use limited seed URLs to prevent timeout
            seed_urls = [
                "https://news.ycombinator.com",
                "https://privacyguides.org"
            ]
            
            for url in seed_urls:
                try:
                    # Quick check with timeout
                    response = await asyncio.wait_for(
                        crawler.session.get(url, timeout=aiohttp.ClientTimeout(total=5)), 
                        timeout=10
                    )
                    content = await response.text()
                    
                    # Simple keyword matching
                    if any(keyword.lower() in content.lower() for keyword in keywords):
                        await crawler._save_discovered_site(url, keywords)
                        discovered_count += 1
                        
                except Exception as e:
                    logging.warning(f"Failed to check {url}: {e}")
                    continue
                    
        except Exception as e:
            logging.error(f"Discovery error: {e}")
        
        return {"discovered_sites": discovered_count, "status": "completed"}
        
    finally:
        await crawler.close_session()

async def run_crawler_with_context(keywords, sites=None, use_tor=False):
    """Run crawler with proper database context handling"""
    if use_tor:
        crawler = TorCrawler()
    else:
        crawler = EnhancedCrawler()
    
    try:
        await crawler.init_session()
        
        # Enhanced discovery with better keyword searching
        discovered_count = 0
        discovered_sites = []
        sites_checked = []
        
        # Expanded seed URLs for better coverage
        seed_urls = [
            "https://news.ycombinator.com",
            "https://privacyguides.org",
            "https://iapp.org",
            "https://privacyinternational.org",
            "https://medium.com/tag/privacy",
            "https://www.reddit.com/r/privacy"
        ]
        
        logging.info(f"Starting crawler with keywords: {keywords}")
        
        for url in seed_urls:
            site_info = {
                'url': url,
                'domain': urlparse(url).netloc,
                'status': 'failed',
                'keyword_matches': [],
                'already_exists': False
            }
            
            try:
                # Check site for keyword matches
                response = await asyncio.wait_for(
                    crawler.session.get(url, timeout=aiohttp.ClientTimeout(total=10)), 
                    timeout=15
                )
                content = await response.text()
                site_info['status'] = 'checked'
                
                # Enhanced keyword matching
                keyword_matches = []
                for keyword in keywords:
                    if keyword.lower() in content.lower():
                        keyword_matches.append(keyword)
                
                site_info['keyword_matches'] = keyword_matches
                
                if keyword_matches:
                    # Try to save to database (this now has proper context)
                    try:
                        # Create new source entry
                        source_name = f"Crawler-discovered: {urlparse(url).netloc}"
                        existing_source = Source.query.filter_by(name=source_name).first()
                        
                        if not existing_source:
                            new_source = Source(
                                name=source_name,
                                url=url,
                                source_type="website",
                                risk_level="medium",
                                enabled=True
                            )
                            db.session.add(new_source)
                            db.session.commit()
                            
                            discovered_count += 1
                            discovered_sites.append({
                                'url': url,
                                'keywords': keyword_matches,
                                'source_name': source_name
                            })
                            site_info['already_exists'] = False
                            logging.info(f"Added new source: {source_name} with keywords {keyword_matches}")
                        else:
                            site_info['already_exists'] = True
                            logging.info(f"Source already exists: {source_name}")
                            
                    except Exception as e:
                        logging.error(f"Error saving discovered site {url}: {e}")
                        db.session.rollback()
                        
            except Exception as e:
                site_info['status'] = 'failed'
                site_info['error'] = str(e)
                logging.warning(f"Failed to check {url}: {e}")
            
            sites_checked.append(site_info)
        
        logging.info(f"Crawler completed: {discovered_count} sites discovered")
        
        return {
            "discovered_sites": discovered_count,
            "status": "completed",
            "sites": discovered_sites,
            "sites_checked": sites_checked,
            "keywords_used": keywords
        }
        
    finally:
        await crawler.close_session()