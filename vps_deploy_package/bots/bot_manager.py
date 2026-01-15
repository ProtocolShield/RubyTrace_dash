"""
Bot Manager for registering, configuring, and controlling bots
Provides CRUD for bots and data sources, and run orchestration
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from models import db, Bot, DataSource, BotSchedule
from .surface_web_bot import SurfaceWebBot
from .deep_web_bot import DeepWebBot
from .dark_web_bot import DarkWebBot
from .osint_feed_bot import OSINTFeedBot


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
                q = q.filter_by(source_type=source_type)
            return q.order_by(DataSource.created_at.desc()).all()
        except Exception as e:
            # Return empty list if database access fails
            return []
    
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
