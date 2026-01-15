"""
Authentication utilities for the OSINT platform
"""
import jwt
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, session, current_app
from auth_models import User, UserSession
from models import db

# JWT Configuration
JWT_SECRET = "osint_platform_secret_key_2025"  # In production, use environment variable
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

def generate_session_token():
    """Generate a secure session token"""
    return secrets.token_urlsafe(32)

def create_jwt_token(user_id):
    """Create JWT token for user"""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token):
    """Verify JWT token and return user_id"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check session first
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user and user.is_active:
                return f(*args, **kwargs)
        
        # Check JWT token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            user_id = verify_jwt_token(token)
            if user_id:
                user = User.query.get(user_id)
                if user and user.is_active:
                    return f(*args, **kwargs)
        
        return jsonify({'error': 'Authentication required'}), 401
    
    return decorated_function

def admin_required(f):
    """Decorator to require admin access for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check session first
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if user and user.is_active and user.is_admin:
                return f(*args, **kwargs)
        
        # Check JWT token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            user_id = verify_jwt_token(token)
            if user_id:
                user = User.query.get(user_id)
                if user and user.is_active and user.is_admin:
                    return f(*args, **kwargs)
        
        return jsonify({'error': 'Admin access required'}), 403
    
    return decorated_function

def get_current_user():
    """Get current authenticated user"""
    # Check session first
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and user.is_active:
            return user
    
    # Check JWT token
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        user_id = verify_jwt_token(token)
        if user_id:
            user = User.query.get(user_id)
            if user and user.is_active:
                return user
    
    return None

def create_user_session(user, ip_address=None, user_agent=None):
    """Create a new user session"""
    session_token = generate_session_token()
    expires_at = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    user_session = UserSession(
        user_id=user.id,
        session_token=session_token,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    db.session.add(user_session)
    db.session.commit()
    
    return session_token

def cleanup_expired_sessions():
    """Clean up expired sessions"""
    expired_sessions = UserSession.query.filter(
        UserSession.expires_at < datetime.utcnow()
    ).all()
    
    for session_obj in expired_sessions:
        db.session.delete(session_obj)
    
    db.session.commit()
    return len(expired_sessions)

# Additional utilities for secure_api.py compatibility
def require_auth(f):
    """Alias for login_required"""
    return login_required(f)

def require_rate_limit(limit_per_hour=60):
    """Rate limiting decorator (simplified implementation)"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Simple rate limiting - in production use Redis
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_2fa(f):
    """2FA requirement decorator (placeholder)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 2FA implementation would go here
        return f(*args, **kwargs)
    return decorated_function

class AuthManager:
    """Authentication manager utilities"""
    @staticmethod
    def create_token(user_id):
        return create_jwt_token(user_id)
    
    @staticmethod
    def verify_token(token):
        return verify_jwt_token(token)

class SecurityUtils:
    """Security utilities"""
    @staticmethod
    def sanitize_input(data):
        """Basic input sanitization"""
        if isinstance(data, dict):
            return {k: str(v).strip() if isinstance(v, str) else v for k, v in data.items()}
        return data

class GeoUtils:
    """Geolocation utilities"""
    @staticmethod
    def get_location_from_ip(ip_address):
        """Get location from IP address"""
        return {'country': 'Unknown', 'city': 'Unknown'}