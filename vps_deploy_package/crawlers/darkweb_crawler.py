"""
Dark web crawler for .onion sites with comprehensive privacy monitoring.
"""

import asyncio
import aiohttp
import logging
import re
import json
import hashlib
from datetime import datetime
from urllib.parse import urljoin, urlparse
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
from utils.tor_manager import tor_manager
from models import db, Source, ScrapeLog
from database import with_retry

class DarkWebCrawler:
    def __init__(self):
        self.session = None
        self.discovered_onions = set()
        self.visited_sites = set()
        self.ua = UserAgent()
        
        # Known .onion directories and starting points
        self.onion_directories = [
            'http://3g2upl4pq6kufc4m.onion',  # DuckDuckGo
            'http://facebookcorewwwi.onion',  # Facebook
            'http://thehiddenwiki.onion',     # Hidden Wiki (example)
        ]
        
        # Privacy-related onion keywords
        self.privacy_keywords = [
            'privacy', 'surveillance', 'leak', 'breach', 'whistleblower',
            'anonymous', 'secure', 'encrypted', 'vpn', 'tor', 'darknet',
            'government', 'nsa', 'cia', 'fbi', 'intelligence', 'classified',
            'documents', 'files', 'database', 'records', 'evidence'
        ]

    async def init_session(self):
        """Initialize HTTP session with Tor proxy"""
        try:
            # Check Tor status
            if not tor_manager.is_running:
                raise Exception("Tor service not running")

            # Close any existing session
            if self.session and not self.session.closed:
                try:
                    await self.session.close()
                except Exception as e:
                    logging.warning(f"Error closing existing session: {e}")

            proxy_config = tor_manager.get_proxy_config()
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=2,
                use_dns_cache=False
            )

            timeout = aiohttp.ClientTimeout(total=60, connect=30)
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
            }

            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=headers
            )

            logging.info("Dark web crawler session initialized successfully")

        except Exception as e:
            logging.error(f"Failed to initialize dark web crawler session: {e}")
            self.session = None
            raise

    async def close_session(self):
        """Close HTTP session"""
        if self.session and not self.session.closed:
            try:
                await self.session.close()
                self.session = None
                logging.info("Dark web crawler session closed successfully")
            except Exception as e:
                logging.warning(f"Error closing dark web crawler session: {e}")
                self.session = None

    async def discover_onion_sites(self, keywords, max_depth=3):
        """Discover .onion sites based on keywords"""
        discovered_sites = []
        
        for start_url in self.onion_directories:
            try:
                await self._crawl_onion_site(start_url, keywords, discovered_sites, 0, max_depth)
            except Exception as e:
                logging.error(f"Error crawling {start_url}: {e}")
                continue
        
        return discovered_sites

    async def _crawl_onion_site(self, url, keywords, discovered_sites, depth, max_depth):
        """Recursively crawl .onion site for relevant content"""
        if depth >= max_depth or url in self.visited_sites:
            return
        
        self.visited_sites.add(url)
        
        try:
            proxy_url = f"socks5://127.0.0.1:{tor_manager.tor_port}"
            
            async with self.session.get(
                url,
                proxy=proxy_url,
                ssl=False,
                allow_redirects=True
            ) as response:
                
                if response.status != 200:
                    return
                
                content = await response.text()
                
                # Check if content contains privacy keywords
                if self._contains_keywords(content, keywords):
                    site_info = await self._extract_site_info(url, content)
                    discovered_sites.append(site_info)
                    await self._save_discovered_onion(url, keywords, site_info)
                
                # Extract .onion links for further crawling
                onion_links = self._extract_onion_links(content, url)
                
                for link in onion_links[:5]:  # Limit to avoid infinite crawling
                    await self._crawl_onion_site(link, keywords, discovered_sites, depth + 1, max_depth)
                    
                    # Rate limiting for dark web
                    await asyncio.sleep(3)
        
        except Exception as e:
            logging.error(f"Error crawling {url}: {e}")

    def _extract_onion_links(self, content, base_url):
        """Extract .onion links from content"""
        soup = BeautifulSoup(content, 'html.parser')
        onion_links = set()
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Check if it's an .onion link
            if '.onion' in href:
                if href.startswith('http'):
                    onion_links.add(href)
                elif href.startswith('/'):
                    parsed_base = urlparse(base_url)
                    onion_links.add(f"{parsed_base.scheme}://{parsed_base.netloc}{href}")
        
        return list(onion_links)

    def _contains_keywords(self, content, keywords):
        """Check if content contains privacy keywords"""
        content_lower = content.lower()
        
        # Check for provided keywords
        for keyword in keywords:
            if keyword.lower() in content_lower:
                return True
        
        # Check for privacy-specific keywords
        for keyword in self.privacy_keywords:
            if keyword in content_lower:
                return True
        
        return False

    async def _extract_site_info(self, url, content):
        """Extract site information"""
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract title
        title_tag = soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else 'Unknown'
        
        # Extract description
        description = ''
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            description = meta_desc.get('content', '')
        
        # Extract text content sample
        text_content = soup.get_text()
        content_sample = ' '.join(text_content.split()[:100])  # First 100 words
        
        return {
            'url': url,
            'title': title,
            'description': description,
            'content_sample': content_sample,
            'discovered_at': datetime.utcnow().isoformat(),
            'type': 'darkweb'
        }

    async def _save_discovered_onion(self, url, keywords, site_info):
        """Save discovered .onion site to database"""
        @with_retry
        def save_to_db():
            try:
                # Check if source already exists
                existing = Source.query.filter_by(url=url).first()
                if existing:
                    return
                
                # Create new source
                source = Source(
                    name=site_info['title'][:100],
                    url=url,
                    source_type='darkweb',
                    risk_level='high',
                    enabled=True,
                    scrape_interval=120  # 2 hours for dark web
                )
                
                db.session.add(source)
                db.session.commit()
                
                logging.info(f"Discovered new .onion site: {site_info['title']}")
                
            except Exception as e:
                logging.error(f"Error saving .onion site: {e}")
                db.session.rollback()
        
        save_to_db()

    async def monitor_known_onions(self, onion_sites, keywords):
        """Monitor known .onion sites for new content"""
        results = []
        
        for site in onion_sites:
            try:
                proxy_url = f"socks5://127.0.0.1:{tor_manager.tor_port}"
                
                async with self.session.get(
                    site['url'],
                    proxy=proxy_url,
                    ssl=False
                ) as response:
                    
                    if response.status == 200:
                        content = await response.text()
                        
                        if self._contains_keywords(content, keywords):
                            site_info = await self._extract_site_info(site['url'], content)
                            results.append(site_info)
                
                # Rate limiting
                await asyncio.sleep(5)
                
            except Exception as e:
                logging.error(f"Error monitoring {site['url']}: {e}")
        
        return results

    async def search_dark_web_markets(self, keywords):
        """Search dark web markets for privacy-related content"""
        # This would require specific market URLs and authentication
        # For security and legal reasons, this is a placeholder
        logging.info("Dark web market search requested - requires specific configuration")
        return []

    def __del__(self):
        """Destructor to ensure cleanup"""
        if hasattr(self, 'session') and self.session:
            try:
                # Create a new event loop if none exists
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                if loop.is_running():
                    # Schedule cleanup for later
                    loop.create_task(self.session.close())
                else:
                    # Run cleanup immediately
                    loop.run_until_complete(self.session.close())
            except Exception as e:
                # Log to stderr since logger might not be available
                print(f"Warning: Failed to cleanup dark web crawler session: {e}")

async def run_darkweb_crawler(options: dict):
    """Main function to run dark web crawler with options"""
    try:
        # Check if Tor is available
        if options.get('use_tor', True):
            if not tor_manager.is_running:
                logging.error("Tor service not running - cannot access dark web")
                return []

        crawler = DarkWebCrawler()

        try:
            await crawler.init_session()

            # Get keywords from options
            keywords = options.get('risk_keywords', [])
            max_pages = options.get('max_pages', 50)
            start_url = options.get('start_url')

            if start_url:
                # Crawl specific site
                discovered_sites = []
                await crawler._crawl_onion_site(start_url, keywords, discovered_sites, 0, 2)
                logging.info(f"Dark web crawl completed. Processed {len(discovered_sites)} pages from {start_url}")
                return discovered_sites
            else:
                # Discover new sites
                discovered_sites = await crawler.discover_onion_sites(keywords, max_depth=2)
                logging.info(f"Dark web crawl completed. Discovered {len(discovered_sites)} relevant sites")
                return discovered_sites

        except Exception as e:
            logging.error(f"Dark web crawler error: {e}")
            return []

        finally:
            # Ensure session is always closed
            try:
                await crawler.close_session()
            except Exception as close_error:
                logging.warning(f"Error closing crawler session: {close_error}")

    except Exception as e:
        logging.error(f"Failed to initialize dark web crawler: {e}")
        return []
