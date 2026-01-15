"""
User authentication models for the OSINT platform
"""
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import db

class User(db.Model):
    """User model for authentication and user management"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=False)  # Admin approval required
    is_admin = db.Column(db.Boolean, default=False)
    api_key = db.Column(db.String(255), unique=True, nullable=True)
    twofa_enabled = db.Column(db.Boolean, default=False)
    twofa_secret = db.Column(db.String(32), nullable=True)
    risk_level = db.Column(db.String(20), default='low')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
    
    def generate_api_key(self):
        """Generate API key for user"""
        import secrets
        self.api_key = secrets.token_urlsafe(32)

class UserSession(db.Model):
    """User session tracking"""
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    
    user = db.relationship('User', backref='sessions')

class MapData(db.Model):
    """Map data for threat visualization"""
    __tablename__ = 'map_data'
    
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    threat_level = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'threat_level': self.threat_level,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AccessLog(db.Model):
    """Access log for tracking user activity"""
    __tablename__ = 'access_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(100), nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=False)
    endpoint = db.Column(db.String(255), nullable=True)
    method = db.Column(db.String(10), nullable=True)
    status_code = db.Column(db.Integer, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_agent = db.Column(db.Text, nullable=True)

    user = db.relationship('User', backref='access_logs')

class APIRateLimit(db.Model):
    """API rate limiting tracking"""
    __tablename__ = 'api_rate_limits'

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    endpoint = db.Column(db.String(255), nullable=False)
    requests_count = db.Column(db.Integer, default=1)
    window_start = db.Column(db.DateTime, default=datetime.utcnow)
    is_blocked = db.Column(db.Boolean, default=False)
    source = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Convert map data to dictionary"""
        return {
            'id': self.id,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'threat_level': self.threat_level,
            'description': self.description,
            'source': self.source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Alert(db.Model):
    """User alerts for monitoring threats"""
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # keyword, threat, anomaly
    risk_score = db.Column(db.Float, default=0.0)
    source_type = db.Column(db.String(50), nullable=True)
    query = db.Column(db.String(500), nullable=True)
    threshold = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_triggered = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref='alerts')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'alert_type': self.alert_type,
            'risk_score': self.risk_score,
            'source_type': self.source_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Watchlist(db.Model):
    """User watchlists for monitoring specific queries"""
    __tablename__ = 'watchlists'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    query = db.Column(db.String(500), nullable=False)
    search_type = db.Column(db.String(50), nullable=False)  # email, phone, domain, etc.
    frequency = db.Column(db.String(20), default='daily')  # hourly, daily, weekly
    is_active = db.Column(db.Boolean, default=True)
    last_searched = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='watchlists')

    def to_dict(self):
        return {
            'id': self.id,
            'query': self.query,
            'search_type': self.search_type,
            'last_searched': self.last_searched.isoformat() if self.last_searched else None
        }


class Case(db.Model):
    """Investigation cases for users"""
    __tablename__ = 'cases'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='open')  # open, closed, pending
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='cases')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class GraphNode(db.Model):
    """Nodes for user graph visualization"""
    __tablename__ = 'graph_nodes'

    id = db.Column(db.String(100), primary_key=True)  # Use string ID for flexibility
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    label = db.Column(db.String(200), nullable=False)
    node_type = db.Column(db.String(50), nullable=False)  # raw_data, cve, breach
    metadata_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='graph_nodes')

    def to_dict(self):
        return {
            'id': self.id,
            'label': self.label,
            'type': self.node_type
        }


class GraphEdge(db.Model):
    """Edges for user graph visualization"""
    __tablename__ = 'graph_edges'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    source_id = db.Column(db.String(100), db.ForeignKey('graph_nodes.id'), nullable=False)
    target_id = db.Column(db.String(100), db.ForeignKey('graph_nodes.id'), nullable=False)
    relationship_type = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='graph_edges')
    source = db.relationship('GraphNode', foreign_keys=[source_id], backref='outgoing_edges')
    target = db.relationship('GraphNode', foreign_keys=[target_id], backref='incoming_edges')

    def to_dict(self):
        return {
            'source': self.source_id,
            'target': self.target_id
        }
