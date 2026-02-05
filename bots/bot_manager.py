"""
Bot Manager for registering, configuring, and controlling bots
Provides CRUD for bots and data sources, and run orchestration
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from models import db, Bot, DataSource, BotSchedule, RawData, CVEItem
from .surface_web_bot import SurfaceWebBot
from .deep_web_bot import DeepWebBot
from .dark_web_bot import DarkWebBot
from .osint_feed_bot import OSINTFeedBot
from datetime import datetime, timedelta


class BotManager:
    _instance = None
    _bots = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BotManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.bots = {
                'surface': SurfaceWebBot(),
                'deep': DeepWebBot(),
                'dark': DarkWebBot(),
                'osint': OSINTFeedBot()
            }
            self.logger = logging.getLogger('bot.BotManager')
            self._initialized = True
    
    # Bot control
    async def start_bot(self, bot_type: str) -> bool:
        bot = self.bots.get(bot_type)
        if not bot:
            return False
        return await bot.start()
    
    async def stop_bot(self, bot_type: str) -> bool:
        bot = self.bots.get(bot_type)
        if not bot:
            return False
        return await bot.stop()
    
    def get_bot_status(self, bot_type: str) -> Dict[str, Any]:
        bot = self.bots.get(bot_type)
        if not bot:
            return {'status': 'unknown'}
        
        # Get status from bot instance (which may have in-memory state)
        status = bot.get_status()
        
        # If bot shows as running but database shows stopped, trust the bot
        if status.get('status') == 'running':
            return status
        
        # Try to get status from database as fallback
        try:
            from models import Bot
            bot_record = Bot.query.filter_by(name=bot.bot_name).first()
            if bot_record:
                status['status'] = bot_record.status
                status['last_run'] = bot_record.last_run
                status['next_run'] = bot_record.next_run
        except Exception as e:
            # If database access fails, return bot's in-memory status
            pass
        
        return status
    
    def update_bot_config(self, bot_type: str, new_config: Dict[str, Any]):
        bot = self.bots.get(bot_type)
        if bot:
            bot.update_config(new_config)
    
    # Data source CRUD
    def add_source(self, name: str, url: str, source_type: str, category: str, risk_level: str, config: Dict[str, Any] = None) -> DataSource:
        source = DataSource(
            name=name,
            url=url,
            source_type=source_type,
            category=category,
            risk_level=risk_level,
            enabled=True,
            config_json=json.dumps(config or {})
        )
        db.session.add(source)
        db.session.commit()
        return source
    
    def update_source(self, source_id: int, updates: Dict[str, Any]) -> Optional[DataSource]:
        source = DataSource.query.get(source_id)
        if not source:
            return None
        
        for key, value in updates.items():
            if hasattr(source, key):
                setattr(source, key, value)
        
        if 'config' in updates:
            source.config_json = json.dumps(updates['config'])
        
        source.updated_at = datetime.utcnow()
        db.session.commit()
        return source
    
    def delete_source(self, source_id: int) -> bool:
        source = DataSource.query.get(source_id)
        if not source:
            return False
        db.session.delete(source)
        db.session.commit()
        return True
    
    def list_sources(self, source_type: Optional[str] = None) -> List[DataSource]:
        try:
            q = DataSource.query
            if source_type:
                # Allow passing a list/tuple of types or legacy names like 'osint_feed'
                if isinstance(source_type, (list, tuple, set)):
                    q = q.filter(DataSource.source_type.in_(list(source_type)))
                else:
                    st = source_type
                    # Map legacy/alternate names to actual values stored in DB
                    if st in ('osint_feed', 'osint'):
                        # accept either 'osint' or 'osint_feed' values in the DB
                        q = q.filter(DataSource.source_type.in_(['osint', 'osint_feed']))
                    elif st == 'all':
                        # no filter
                        pass
                    else:
                        q = q.filter_by(source_type=st)
            return q.order_by(DataSource.created_at.desc()).all()
        except Exception as e:
            # Log error and return empty list if database access fails
            try:
                self.logger.error(f"Error listing sources ({source_type}): {e}")
            except Exception:
                pass
            return []

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get core dashboard statistics: total items, new items last 24h, high-risk items"""
        try:
            from datetime import datetime, timedelta
            from models import RawData

            now = datetime.utcnow()
            yesterday = now - timedelta(hours=24)

            # Total items collected
            total_items_collected = RawData.query.count()

            # New items in last 24h
            new_items_from_last_24_hours = RawData.query.filter(RawData.created_at > yesterday).count()

            # High-risk items (risk_score > 7)
            high_risk_items = RawData.query.filter(RawData.risk_score > 7).count()

            return {
                'totalItemsCollected': total_items_collected,
                'newItemsFromLast24Hours': new_items_from_last_24_hours,
                'highRiskItems': high_risk_items
            }
        except Exception as e:
            self.logger.error(f"Failed to get dashboard stats: {e}")
            return {
                'totalItemsCollected': 0,
                'newItemsFromLast24Hours': 0,
                'highRiskItems': 0
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get platform-wide statistics for dashboard overview"""
        try:
            now = datetime.utcnow()
            yesterday = now - timedelta(hours=24)
            two_days_ago = now - timedelta(hours=48)
            thirty_days_ago = now - timedelta(days=30)

            # Total items collected
            total_items = RawData.query.count()

            # New items in last 24h
            new_items_24h = RawData.query.filter(RawData.created_at > yesterday).count()

            # High-risk items (assuming risk_score > 7 is high-risk)
            high_risk_items = RawData.query.filter(RawData.risk_score > 7).count()

            # New CVEs in last 24h
            new_cves = CVEItem.query.filter(CVEItem.created_at > yesterday).count()

            # Calculate changes (vs previous 24h period)
            prev_new_items = RawData.query.filter(
                RawData.created_at.between(two_days_ago, yesterday)
            ).count()
            new_items_24h_change = self._calculate_change(new_items_24h, prev_new_items)

            prev_high_risk = RawData.query.filter(
                RawData.risk_score > 7,
                RawData.created_at.between(two_days_ago, yesterday)
            ).count()
            high_risk_change = self._calculate_change(high_risk_items, prev_high_risk)

            prev_new_cves = CVEItem.query.filter(
                CVEItem.created_at.between(two_days_ago, yesterday)
            ).count()
            new_cves_change = self._calculate_change(new_cves, prev_new_cves)

            # For total_items, compare to total from 24h ago (approximate)
            prev_total = total_items - new_items_24h  # Rough estimate
            total_change = self._calculate_change(total_items, prev_total)

            # Activity Timeline (last 30 days, daily counts)
            timeline_data = []
            for i in range(30):
                day_start = thirty_days_ago + timedelta(days=i)
                day_end = day_start + timedelta(days=1)
                count = RawData.query.filter(
                    RawData.created_at.between(day_start, day_end)
                ).count()
                timeline_data.append({
                    'date': day_start.date().isoformat(),
                    'count': count
                })

            # Top Affected Domains (from raw data URLs)
            from sqlalchemy import func, text
            try:
                # Try a SQL-based approach (may work on MySQL/Postgres with appropriate functions)
                domain_query = db.session.query(
                    func.substring_index(func.substring_index(RawData.url, '://', -1), '/', 1).label('domain'),
                    func.count(RawData.id).label('count')
                ).filter(
                    RawData.url.isnot(None),
                    RawData.created_at > thirty_days_ago
                ).group_by(text('domain')).order_by(func.count(RawData.id).desc()).limit(10).all()

                top_domains = [{'name': row.domain, 'count': row.count} for row in domain_query]
            except Exception:
                # Fallback for SQLite or DBs without substring_index: compute in Python
                from urllib.parse import urlparse
                urls = db.session.query(RawData.url).filter(RawData.url.isnot(None), RawData.created_at > thirty_days_ago).all()
                counts = {}
                for (u,) in urls:
                    try:
                        parsed = urlparse(u)
                        domain = parsed.netloc or parsed.path.split('/')[0]
                        if domain.startswith('www.'):
                            domain = domain[4:]
                        if domain:
                            counts[domain] = counts.get(domain, 0) + 1
                    except Exception:
                        continue
                top_domains = [{'name': k, 'count': v} for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]]

            # Top Keywords (from content analysis - simplified version)
            # For now, use most common words from titles/descriptions
            # Use title and content (description field doesn't exist on RawData)
            keyword_query = db.session.query(
                RawData.title,
                RawData.content
            ).filter(
                RawData.created_at > thirty_days_ago,
                (RawData.title.isnot(None)) | (RawData.content.isnot(None))
            ).limit(100).all()

            keyword_counts = {}
            for row in keyword_query:
                # Row is a tuple (title, content)
                title_text = row[0] or ''
                content_text = row[1] or ''
                text = f"{title_text} {content_text}".lower()
                words = [w.strip('.,!?()[]{}') for w in text.split() if len(w) > 3]
                for word in words:
                    if word in ['that', 'with', 'from', 'this', 'have', 'been', 'were', 'they', 'their', 'what', 'when', 'where', 'which', 'will', 'would', 'could', 'should', 'there', 'here', 'some', 'many', 'most', 'much', 'such', 'than', 'then', 'them', 'these', 'those', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'among']:
                        continue  # Skip common stop words
                    keyword_counts[word] = keyword_counts.get(word, 0) + 1

            top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            top_keywords = [{'keyword': k, 'count': v} for k, v in top_keywords]

            return {
                'stats': {
                    'total_items': total_items,
                    'new_items_24h': new_items_24h,
                    'high_risk_items': high_risk_items,
                    'new_cves': new_cves,
                    'total_change': total_change,
                    'new_items_24h_change': new_items_24h_change,
                    'high_risk_change': high_risk_change,
                    'new_cves_change': new_cves_change
                },
                'charts': {
                    'timeline': timeline_data,
                    'top_domains': top_domains,
                    'top_keywords': top_keywords
                }
            }
        except Exception as e:
            self.logger.error(f"Failed to get stats: {e}")
            return {
                'stats': {
                    'total_items': 0,
                    'new_items_24h': 0,
                    'high_risk_items': 0,
                    'new_cves': 0,
                    'total_change': 'N/A',
                    'new_items_24h_change': 'N/A',
                    'high_risk_change': 'N/A',
                    'new_cves_change': 'N/A'
                },
                'charts': {
                    'timeline': [],
                    'top_domains': [],
                    'top_keywords': []
                }
            }
            
    def get_simple_stats(self) -> Dict[str, Any]:
        """
        Returns the core stats required by the user dashboard:
        - totalItemsCollected
        - newItemsFromLast24Hours
        - highRiskItems
        """
        try:
            now = datetime.utcnow()
            yesterday = now - timedelta(hours=24)

            total_items = RawData.query.count()
            new_items_24h = RawData.query.filter(RawData.created_at > yesterday).count()
            high_risk_items = RawData.query.filter(RawData.risk_score > 7).count()

            return {
                "success": True,
                "stats": {
                    "totalItemsCollected": total_items,
                    "newItemsFromLast24Hours": new_items_24h,
                    "highRiskItems": high_risk_items
                }
            }
        except Exception as e:
            self.logger.error(f"Failed to load simple stats: {e}")
            return {
                "success": False,
                "stats": {
                    "totalItemsCollected": 0,
                    "newItemsFromLast24Hours": 0,
                    "highRiskItems": 0
                }
            }

    def _calculate_change(self, current: int, previous: int) -> str:
        """Calculate percentage change as string"""
        if previous == 0:
            return 'N/A' if current == 0 else '+100%'
        change = ((current - previous) / previous) * 100
        sign = '+' if change >= 0 else ''
        return f"{sign}{change:.1f}%"
    
    # Orchestration
    async def run_cycle(self, bot_type: str, source_type: str):
        """Run a collection cycle for a specific bot type and source type"""
        try:
            bot = self.bots.get(bot_type)
            if not bot:
                self.logger.error(f"Bot type {bot_type} not found")
                return

            sources = self.list_sources(source_type)
            if not sources:
                self.logger.warning(f"No sources found for type {source_type}")
                return

            self.logger.info(f"Starting collection cycle for {bot_type} bot on {len(sources)} {source_type} sources")

            # Ensure bot has a valid session
            if not bot.session or bot.session.closed:
                await bot._setup_session()

            await bot.run_collection_cycle(sources)

        except Exception as e:
            self.logger.error(f"Error in collection cycle for {bot_type}: {e}")
            # Try to log the error to bot status
            try:
                await bot._log_bot_status('error', f"Collection cycle failed: {str(e)}")
            except:
                pass

    async def refresh_osint_feed(self, feed_type: str):
        """Refresh a specific OSINT feed type (cve, news, tools)"""
        try:
            bot = self.bots.get('osint')
            if not bot:
                self.logger.error("OSINT bot not found")
                return False

            # Filter sources by feed type
            # support both 'osint' and legacy 'osint_feed' source_type values
            sources = self.list_sources(['osint', 'osint_feed'])
            if not sources:
                self.logger.warning("No OSINT feed sources found")
                return False

            # Filter sources based on feed_type if specified
            if feed_type and feed_type != 'all':
                # Map feed_type to source names or categories
                feed_filters = {
                    'cve': ['CVE Database', 'NIST NVD'],
                    'news': ['TechCrunch Security', 'The Hacker News'],
                    'tools': ['MITRE ATT&CK']
                }
                filtered_names = feed_filters.get(feed_type, [])
                sources = [s for s in sources if s.name in filtered_names]

            if not sources:
                self.logger.warning(f"No sources found for feed type: {feed_type}")
                return False

            self.logger.info(f"Refreshing {feed_type} feeds with {len(sources)} sources")

            # Ensure bot has a valid session
            if not bot.session or bot.session.closed:
                await bot._setup_session()

            await bot.run_collection_cycle(sources)
            return True

        except Exception as e:
            self.logger.error(f"Error refreshing OSINT feed {feed_type}: {e}")
            return False