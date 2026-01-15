"""
Database models for the application
"""
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import QueuePool


class Base(DeclarativeBase):
    pass


# Configure SQLAlchemy with more robust connection pooling
engine_options = {
    'pool_size': 5,
    'max_overflow': 10,
    'pool_timeout': 30,
    'pool_recycle': 1800,  # Recycle connections after 30 minutes
    'pool_pre_ping': True,  # Check connection before using
    'poolclass': QueuePool
}

db = SQLAlchemy(model_class=Base, engine_options=engine_options)


class ApiKey(db.Model):
    """
    Model for storing API keys securely
    """
    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(100), unique=True, nullable=False)
    key = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ApiKey {self.service}>"


class Source(db.Model):
    """
    Model for storing data sources with type and risk level
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    url = db.Column(db.String(500), nullable=False)
    source_type = db.Column(db.String(50), nullable=False)  # forum, news, pastebin, darkweb
    risk_level = db.Column(db.String(20), nullable=False)   # low, medium, high
    enabled = db.Column(db.Boolean, default=True)
    scrape_interval = db.Column(db.Integer, default=60)     # minutes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Source {self.name} ({self.source_type}/{self.risk_level})>"
    
    
class KeywordAlert(db.Model):
    """
    Model for keyword-based alerts
    """
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(100), nullable=False)
    priority = db.Column(db.String(20), nullable=False)  # low, medium, high
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_triggered = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f"<KeywordAlert {self.keyword} ({self.priority})>"
        
        
class ScrapeLog(db.Model):
    """
    Model for tracking scrape operations and errors
    """
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('source.id'), nullable=True)
    source_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # success, error
    items_found = db.Column(db.Integer, default=0)
    items_added = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    source = db.relationship('Source', backref='logs')
    
    def __repr__(self):
        return f"<ScrapeLog {self.source_name} {self.status} at {self.timestamp}>"
 

class CVEItem(db.Model):
    """
    CVE entries collected from multiple sources with detailed information
    """
    id = db.Column(db.Integer, primary_key=True)
    cve_id = db.Column(db.String(50), unique=True, nullable=False)
    title = db.Column(db.String(500), nullable=True)
    description = db.Column(db.Text, nullable=True)
    severity = db.Column(db.String(20), nullable=True)
    cvss = db.Column(db.Float, nullable=True)
    cvss_vector = db.Column(db.String(200), nullable=True)
    affected_products = db.Column(db.Text, nullable=True)  # JSON string
    affected_vendors = db.Column(db.Text, nullable=True)  # JSON string
    tags = db.Column(db.Text, nullable=True)  # comma-separated
    source_url = db.Column(db.String(1000), nullable=True)
    references = db.Column(db.Text, nullable=True)  # JSON string
    exploit_available = db.Column(db.Boolean, default=False)
    patch_available = db.Column(db.Boolean, default=False)
    published_at = db.Column(db.DateTime, nullable=True)
    last_modified_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<CVE {self.cve_id} {self.severity}>"


class NewsItem(db.Model):
    """
    Threat news feed items
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    url = db.Column(db.String(1000), nullable=False)
    source_name = db.Column(db.String(200), nullable=True)
    summary = db.Column(db.Text, nullable=True)
    tags = db.Column(db.Text, nullable=True)  # comma-separated
    risk_level = db.Column(db.String(20), nullable=True)
    published_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<News {self.title[:30]}>"


class ToolItem(db.Model):
    """
    Hacking tools and scripts (private storage)
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), nullable=False)
    url = db.Column(db.String(1000), nullable=True)
    source_name = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    risk_level = db.Column(db.String(20), nullable=True)
    file_path = db.Column(db.String(1000), nullable=True)
    is_private = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Tool {self.name}>"


class UploadItem(db.Model):
    """
    Admin uploads with metadata (partial info only)
    """
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(500), nullable=False)
    content_type = db.Column(db.String(200), nullable=True)
    size_bytes = db.Column(db.Integer, nullable=True)
    risk_level = db.Column(db.String(20), default='low')
    is_public = db.Column(db.Boolean, default=False)
    uploader_id = db.Column(db.Integer, nullable=True)
    storage_path = db.Column(db.String(1000), nullable=True)
    upload_metadata = db.Column(db.Text, nullable=True)  # JSON string
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Upload {self.filename} {self.risk_level}>"


class BreachItem(db.Model):
    """
    Breach entries collected from various sources
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    affected_organizations = db.Column(db.Text, nullable=True)  # JSON string
    data_types_exposed = db.Column(db.Text, nullable=True)  # JSON string
    records_affected = db.Column(db.Integer, nullable=True)
    discovery_date = db.Column(db.DateTime, nullable=True)
    disclosure_date = db.Column(db.DateTime, nullable=True)
    source_url = db.Column(db.String(1000), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Breach {self.name}>"

class LeakItem(db.Model):
    """
    Leak entries collected from various sources
    """
    id = db.Column(db.Integer, primary_key=True)
    source = db.Column(db.String(500), nullable=False)
    data_content = db.Column(db.Text, nullable=True)
    verification_status = db.Column(db.String(50), nullable=True)  # e.g., verified, unverified
    associated_breach_id = db.Column(db.Integer, db.ForeignKey('breach_item.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Leak from {self.source}>"

class GlobalConfig(db.Model):
    """
    Global configuration for scrapers and bots
    """
    id = db.Column(db.Integer, primary_key=True, default=1)
    keywords = db.Column(db.Text, nullable=True)  # comma-separated
    settings_json = db.Column(db.Text, nullable=True)  # JSON blob for dynamic settings
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<GlobalConfig {self.id}>"


# New models for the enhanced bot system

class Bot(db.Model):
    """
    Bot configuration and management
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    bot_type = db.Column(db.String(50), nullable=False)  # surface, deep, dark, osint
    status = db.Column(db.String(20), default='stopped')  # running, stopped, paused, error
    config_json = db.Column(db.Text, nullable=True)  # JSON configuration
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_run = db.Column(db.DateTime, nullable=True)
    next_run = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Bot {self.name} ({self.bot_type})>"


class BotLog(db.Model):
    """
    Bot execution logs
    """
    id = db.Column(db.Integer, primary_key=True)
    bot_id = db.Column(db.Integer, db.ForeignKey('bot.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # success, error, warning
    message = db.Column(db.Text, nullable=True)
    data_collected = db.Column(db.Integer, default=0)
    execution_time = db.Column(db.Float, nullable=True)  # seconds
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    bot = db.relationship('Bot', backref='logs')
    
    def __repr__(self):
        return f"<BotLog {self.bot_id} {self.status} at {self.timestamp}>"


class DataSource(db.Model):
    """
    Enhanced data source configuration
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(1000), nullable=False)
    source_type = db.Column(db.String(50), nullable=False)  # surface, deep, dark, osint
    category = db.Column(db.String(100), nullable=False)  # forum, news, pastebin, social, etc.
    risk_level = db.Column(db.String(20), nullable=False)  # low, medium, high, extreme
    enabled = db.Column(db.Boolean, default=True)
    scrape_interval = db.Column(db.Integer, default=60)  # minutes
    last_scraped = db.Column(db.DateTime, nullable=True)
    next_scrape = db.Column(db.DateTime, nullable=True)
    config_json = db.Column(db.Text, nullable=True)  # Source-specific configuration
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<DataSource {self.name} ({self.source_type}/{self.category})>"


class RawData(db.Model):
    """
    Raw data storage for all collected information
    """
    id = db.Column(db.Integer, primary_key=True)
    source_id = db.Column(db.Integer, db.ForeignKey('data_source.id'), nullable=False)
    bot_id = db.Column(db.Integer, db.ForeignKey('bot.id'), nullable=True)
    url = db.Column(db.String(1000), nullable=True)
    title = db.Column(db.String(500), nullable=True)
    content = db.Column(db.Text, nullable=True)
    raw_html = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(1000), nullable=True)
    file_hash = db.Column(db.String(64), nullable=True)
    content_type = db.Column(db.String(100), nullable=True)
    metadata_json = db.Column(db.Text, nullable=True)  # Headers, timestamps, etc.
    risk_score = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    source = db.relationship('DataSource', backref='raw_data')
    bot = db.relationship('Bot', backref='raw_data')
    
    def __repr__(self):
        return f"<RawData {self.id} from {self.source_id}>"


class Entity(db.Model):
    """
    Extracted entities from raw data
    """
    id = db.Column(db.Integer, primary_key=True)
    raw_data_id = db.Column(db.Integer, db.ForeignKey('raw_data.id'), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)  # person, organization, location, tool, etc.
    entity_value = db.Column(db.String(500), nullable=False)
    confidence = db.Column(db.Float, default=0.0)
    metadata_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    raw_data = db.relationship('RawData', backref='entities')
    
    def __repr__(self):
        return f"<Entity {self.entity_type}: {self.entity_value}>"


class Relationship(db.Model):
    """
    Relationships between entities
    """
    id = db.Column(db.Integer, primary_key=True)
    source_entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=False)
    target_entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=False)
    relationship_type = db.Column(db.String(100), nullable=False)  # works_for, located_in, uses, etc.
    confidence = db.Column(db.Float, default=0.0)
    metadata_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    source_entity = db.relationship('Entity', foreign_keys=[source_entity_id], backref='outgoing_relationships')
    target_entity = db.relationship('Entity', foreign_keys=[target_entity_id], backref='incoming_relationships')
    
    def __repr__(self):
        return f"<Relationship {self.source_entity_id} {self.relationship_type} {self.target_entity_id}>"


class SearchIndex(db.Model):
    """
    Searchable index for quick data retrieval
    """
    id = db.Column(db.Integer, primary_key=True)
    raw_data_id = db.Column(db.Integer, db.ForeignKey('raw_data.id'), nullable=False)
    search_text = db.Column(db.Text, nullable=False)  # Processed text for search
    keywords = db.Column(db.Text, nullable=True)  # comma-separated keywords
    tags = db.Column(db.Text, nullable=True)  # comma-separated tags
    risk_keywords = db.Column(db.Text, nullable=True)  # comma-separated risk indicators
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    raw_data = db.relationship('RawData', backref='search_indices')
    
    def __repr__(self):
        return f"<SearchIndex {self.id} for {self.raw_data_id}>"


class BotSchedule(db.Model):
    """
    Bot scheduling configuration
    """
    id = db.Column(db.Integer, primary_key=True)
    bot_id = db.Column(db.Integer, db.ForeignKey('bot.id'), nullable=False)
    schedule_type = db.Column(db.String(20), nullable=False)  # interval, cron, manual
    schedule_config = db.Column(db.Text, nullable=True)  # JSON configuration
    enabled = db.Column(db.Boolean, default=True)
    last_run = db.Column(db.DateTime, nullable=True)
    next_run = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    bot = db.relationship('Bot', backref='schedules')
    
    def __repr__(self):
        return f"<BotSchedule {self.bot_id} {self.schedule_type}>"