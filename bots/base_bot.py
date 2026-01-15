"""
Base Bot Class for OSINT Data Collection
Provides common functionality for all specialized bots
"""

import asyncio
import aiohttp
import logging
import json
import hashlib
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from urllib.parse import urljoin, urlparse
from fake_useragent import UserAgent
import tldextract
from models import db, Bot, BotLog, DataSource, RawData, Entity, Relationship, SearchIndex
from database import with_retry


class BaseBot:
    """
    Base class for all OSINT collection bots
    Implements common functionality and anti-detection measures
    """
    
    def __init__(self, bot_name: str, bot_type: str, config: Dict[str, Any] = None):
        self.bot_name = bot_name
        self.bot_type = bot_type
        self.config = config or {}
        self.logger = logging.getLogger(f"bot.{bot_name}")
        
        # Anti-detection measures
        self.user_agents = UserAgent()
        self.session = None
        self.proxy_pool = []
        self.rate_limit_delays = {}
        self.fingerprint_rotation = True
        
        # Data collection state
        self.collected_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.session_start_time = None
        
        # Bot status tracking (in-memory)
        self._status = 'stopped'
        self._last_run = None
        
        # Bot database record
        self.bot_record = None
        self._init_bot_record()
    
    def _init_bot_record(self):
        """Initialize or get bot database record"""
        try:
            self.bot_record = Bot.query.filter_by(name=self.bot_name).first()
            if not self.bot_record:
                self.bot_record = Bot(
                    name=self.bot_name,
                    bot_type=self.bot_type,
                    config_json=json.dumps(self.config),
                    status='stopped'
                )
                db.session.add(self.bot_record)
                db.session.commit()
            else:
                # Update config if changed
                if self.bot_record.config_json != json.dumps(self.config):
                    self.bot_record.config_json = json.dumps(self.config)
                    self.bot_record.updated_at = datetime.utcnow()
                    db.session.commit()
        except Exception as e:
            self.logger.error(f"Failed to initialize bot record: {e}")
            # Create a minimal bot record without database
            self.bot_record = type('MockBot', (), {
                'name': self.bot_name,
                'bot_type': self.bot_type,
                'status': 'stopped',
                'config_json': json.dumps(self.config)
            })()
    
    async def start(self):
        """Start the bot"""
        try:
            self.logger.info(f"Starting {self.bot_name} bot")
            
            # Set in-memory status first
            self._status = 'running'
            self._last_run = datetime.utcnow()
            
            # Try to update database if possible
            try:
                if hasattr(self.bot_record, 'status'):
                    self.bot_record.status = 'running'
                    self.bot_record.last_run = datetime.utcnow()
                    db.session.commit()
            except Exception as db_error:
                self.logger.warning(f"Database update failed: {db_error}")
            
            await self._setup_session()
            self.session_start_time = datetime.utcnow()
            
            await self._log_bot_status('success', f"Bot {self.bot_name} started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start bot {self.bot_name}: {e}")
            self._status = 'stopped'  # Reset status on failure
            await self._log_bot_status('error', f"Failed to start: {str(e)}")
            return False
    
    async def stop(self):
        """Stop the bot"""
        try:
            self.logger.info(f"Stopping {self.bot_name} bot")

            # Set in-memory status first
            self._status = 'stopped'

            # Try to update database if possible
            try:
                if hasattr(self.bot_record, 'status'):
                    self.bot_record.status = 'stopped'
                    db.session.commit()
            except Exception as db_error:
                self.logger.warning(f"Database update failed: {db_error}")

            # Close HTTP session properly
            if self.session and not self.session.closed:
                try:
                    await self.session.close()
                    self.session = None
                except Exception as session_error:
                    self.logger.warning(f"Failed to close session: {session_error}")

            await self._log_bot_status('success', f"Bot {self.bot_name} stopped")
            return True

        except Exception as e:
            self.logger.error(f"Failed to stop bot {self.bot_name}: {e}")
            return False
    
    async def pause(self):
        """Pause the bot"""
        try:
            self.logger.info(f"Pausing {self.bot_name} bot")
            
            # Try to update database if possible
            try:
                if hasattr(self.bot_record, 'status'):
                    self.bot_record.status = 'paused'
                    db.session.commit()
            except Exception as db_error:
                self.logger.warning(f"Database update failed: {db_error}")
            
            await self._log_bot_status('success', f"Bot {self.bot_name} paused")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to pause bot {self.bot_name}: {e}")
            return False
    
    async def _setup_session(self):
        """Setup HTTP session with anti-detection measures"""
        try:
            # Close existing session if any
            if self.session and not self.session.closed:
                try:
                    await self.session.close()
                except Exception as e:
                    self.logger.warning(f"Failed to close existing session: {e}")
            
            # Create new session with proper event loop handling
            connector = aiohttp.TCPConnector(
                limit=50,
                ttl_dns_cache=300,
                use_dns_cache=True,
                ssl=False  # Allow self-signed certificates
            )
            
            timeout = aiohttp.ClientTimeout(total=60, connect=20)
            headers = self._get_rotated_headers()
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers=headers
            )
            
            self.logger.debug(f"Session created successfully for {self.bot_name}")
            
        except Exception as e:
            self.logger.error(f"Failed to create session for {self.bot_name}: {e}")
            self.session = None
    
    def _get_rotated_headers(self) -> Dict[str, str]:
        """Get rotated headers to avoid fingerprinting"""
        if not self.fingerprint_rotation:
            return {'User-Agent': self.user_agents.random}
        
        # Rotate multiple headers to appear more human-like
        headers = {
            'User-Agent': self.user_agents.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': random.choice([
                'en-US,en;q=0.5',
                'en-GB,en;q=0.5',
                'en-CA,en;q=0.5',
                'en-AU,en;q=0.5'
            ]),
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Randomly add some headers
        if random.random() > 0.5:
            headers['Cache-Control'] = 'max-age=0'
        
        if random.random() > 0.7:
            headers['Sec-Fetch-Dest'] = 'document'
            headers['Sec-Fetch-Mode'] = 'navigate'
            headers['Sec-Fetch-Site'] = 'none'
        
        return headers
    
    async def _make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[aiohttp.ClientResponse]:
        """Make HTTP request with anti-detection measures"""
        try:
            # Ensure we have a valid session
            if not self.session or self.session.closed:
                await self._setup_session()
                if not self.session:
                    self.logger.error(f"Cannot make request - no valid session for {url}")
                    return None
            
            # Rate limiting
            domain = tldextract.extract(url).domain
            await self._respect_rate_limit(domain)
            
            # Random delay
            await self._random_delay()
            
            try:
                # Rotate headers for each request
                if self.fingerprint_rotation:
                    kwargs['headers'] = self._get_rotated_headers()
                
                response = await self.session.request(method, url, **kwargs)
                
                # Update rate limit tracking
                self._update_rate_limit(domain)
                
                return response
                
            except Exception as e:
                self.logger.error(f"Request failed for {url}: {e}")
                self.failed_urls.add(url)
                
                # If it's a session error, try to recreate the session
                if "Event loop is closed" in str(e) or "session is closed" in str(e):
                    self.logger.info("Attempting to recreate session due to session error")
                    try:
                        await self._setup_session()
                    except Exception as session_error:
                        self.logger.error(f"Failed to recreate session: {session_error}")
                
                return None
                
        except Exception as e:
            self.logger.error(f"Session setup failed for {url}: {e}")
            self.failed_urls.add(url)
            return None
    
    async def _respect_rate_limit(self, domain: str):
        """Respect rate limits for domains"""
        if domain in self.rate_limit_delays:
            last_request = self.rate_limit_delays[domain]
            time_since = time.time() - last_request
            
            # Random delay between 1-5 seconds
            min_delay = 1
            max_delay = 5
            
            if time_since < min_delay:
                await asyncio.sleep(min_delay - time_since)
            elif time_since < max_delay:
                # Random additional delay
                await asyncio.sleep(random.uniform(0, 2))
    
    def _update_rate_limit(self, domain: str):
        """Update rate limit tracking"""
        self.rate_limit_delays[domain] = time.time()
    
    async def _random_delay(self):
        """Add random delay to appear more human-like"""
        # Random delay between 0.5-3 seconds
        delay = random.uniform(0.5, 3.0)
        await asyncio.sleep(delay)
    
    async def collect_data(self, source: DataSource) -> List[Dict[str, Any]]:
        """
        Collect data from a source - to be implemented by subclasses
        """
        raise NotImplementedError("Subclasses must implement collect_data")
    
    async def process_raw_data(self, raw_data: Dict[str, Any], source: DataSource) -> RawData:
        """Process and store raw data"""
        try:
            # Get bot_id safely
            bot_id = None
            if hasattr(self.bot_record, 'id') and self.bot_record.id:
                bot_id = self.bot_record.id
            else:
                # Try to get bot record from database
                try:
                    bot_record = Bot.query.filter_by(name=self.bot_name).first()
                    if bot_record:
                        bot_id = bot_record.id
                except Exception as e:
                    self.logger.warning(f"Could not get bot_id: {e}")
            
            # Create raw data record
            raw_data_record = RawData(
                source_id=source.id,
                bot_id=bot_id,
                url=raw_data.get('url'),
                title=raw_data.get('title'),
                content=raw_data.get('content'),
                raw_html=raw_data.get('raw_html'),
                file_path=raw_data.get('file_path'),
                file_hash=raw_data.get('file_hash'),
                content_type=raw_data.get('content_type'),
                metadata_json=json.dumps(raw_data.get('metadata', {})),
                risk_score=raw_data.get('risk_score', 0.0)
            )
            
            db.session.add(raw_data_record)
            db.session.commit()
            
            # Create search index
            search_index = SearchIndex(
                raw_data_id=raw_data_record.id,
                search_text=raw_data.get('search_text', ''),
                keywords=raw_data.get('keywords', ''),
                tags=raw_data.get('tags', ''),
                risk_keywords=raw_data.get('risk_keywords', '')
            )
            
            db.session.add(search_index)
            db.session.commit()
            
            self.logger.info(f"Successfully stored raw data: {raw_data_record.title}")
            return raw_data_record
            
        except Exception as e:
            self.logger.error(f"Failed to process raw data: {e}")
            db.session.rollback()
            return None
    
    async def extract_entities(self, raw_data: RawData) -> List[Entity]:
        """Extract entities from raw data"""
        # Basic entity extraction - can be enhanced with NLP
        entities = []
        
        if raw_data.content:
            # Extract potential entities (basic implementation)
            content = raw_data.content.lower()
            
            # Extract emails
            import re
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', raw_data.content)
            for email in emails:
                entities.append(Entity(
                    raw_data_id=raw_data.id,
                    entity_type='email',
                    entity_value=email,
                    confidence=0.8
                ))
            
            # Extract URLs
            urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', raw_data.content)
            for url in urls:
                entities.append(Entity(
                    raw_data_id=raw_data.id,
                    entity_type='url',
                    entity_value=url,
                    confidence=0.9
                ))
        
        if entities:
            db.session.add_all(entities)
            db.session.commit()
        
        return entities
    
    async def _log_bot_status(self, status: str, message: str, data_collected: int = 0, execution_time: float = None):
        """Log bot status to database"""
        try:
            # Only try to log if we have a valid bot record with an ID
            if hasattr(self.bot_record, 'id') and self.bot_record.id:
                bot_log = BotLog(
                    bot_id=self.bot_record.id,
                    status=status,
                    message=message,
                    data_collected=data_collected,
                    execution_time=execution_time
                )
                
                db.session.add(bot_log)
                db.session.commit()
            else:
                # Log to console if database logging fails
                self.logger.info(f"Bot Status: {status} - {message}")
                
        except Exception as e:
            self.logger.error(f"Failed to log bot status: {e}")
            # Fallback to console logging
            self.logger.info(f"Bot Status: {status} - {message}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bot status"""
        try:
            return {
                'name': self.bot_name,
                'type': self.bot_type,
                'status': self._status,  # Use in-memory status
                'last_run': self._last_run,
                'next_run': getattr(self.bot_record, 'next_run', None) if self.bot_record else None,
                'collected_urls': len(self.collected_urls),
                'failed_urls': len(self.failed_urls)
            }
        except Exception as e:
            self.logger.error(f"Error getting bot status: {e}")
            return {
                'name': self.bot_name,
                'type': self.bot_type,
                'status': self._status,  # Fallback to in-memory status
                'last_run': self._last_run,
                'next_run': None,
                'collected_urls': len(self.collected_urls),
                'failed_urls': len(self.failed_urls)
            }
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update bot configuration"""
        self.config.update(new_config)
        try:
            if self.bot_record and hasattr(self.bot_record, 'config_json'):
                self.bot_record.config_json = json.dumps(self.config)
                self.bot_record.updated_at = datetime.utcnow()
                db.session.commit()
        except Exception as e:
            self.logger.warning(f"Failed to update bot config in database: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session and not self.session.closed:
            try:
                await self.session.close()
                self.session = None
            except Exception as e:
                self.logger.warning(f"Failed to close session: {e}")
        
        try:
            if self.bot_record and hasattr(self.bot_record, 'status'):
                self.bot_record.status = 'stopped'
                db.session.commit()
        except Exception as e:
            self.logger.warning(f"Failed to update bot status in database: {e}")
    
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
                print(f"Warning: Failed to cleanup bot session: {e}")
