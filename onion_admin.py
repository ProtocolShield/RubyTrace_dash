"""
.onion backend access for admin users
"""
from flask import Flask, jsonify, request, Blueprint
import os
from datetime import datetime
from auth_models import User, MapData, db
from auth_utils import require_auth, require_2fa, SecurityUtils
from utils.json_utils import load_existing_data

# Create .onion admin blueprint
onion_admin = Blueprint('onion_admin', __name__, url_prefix='/admin/.onion')

@onion_admin.before_request
def verify_onion_access():
    """Verify this is accessed via .onion"""
    if not SecurityUtils.validate_onion_access():
        # In development, we'll allow regular access
        # In production, this should reject non-.onion requests
        pass

@onion_admin.route('/dashboard', methods=['GET'])
@require_auth
@require_2fa
def admin_dashboard():
    """Secure admin dashboard"""
    user = request.current_user
    
    # Get system statistics
    total_posts = len(load_existing_data())
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    map_incidents = MapData.query.count()
    
    return jsonify({
        'admin_user': user.to_dict(),
        'system_stats': {
            'total_posts': total_posts,
            'total_users': total_users,
            'active_users': active_users,
            'map_incidents': map_incidents,
            'server_time': datetime.utcnow().isoformat()
        },
        'access_type': 'onion' if SecurityUtils.validate_onion_access() else 'clearnet'
    })

@onion_admin.route('/core-data', methods=['GET'])
@require_auth
@require_2fa
def get_core_data():
    """Access core OSINT data (admin only)"""
    # Enhanced data access for admin users
    all_posts = load_existing_data()
    
    # Add metadata and risk analysis
    enhanced_posts = []
    for post in all_posts:
        enhanced_post = post.copy()
        enhanced_post['admin_metadata'] = {
            'risk_score': calculate_risk_score(post),
            'data_sources': identify_data_sources(post),
            'geographic_indicators': extract_geo_indicators(post),
            'timestamp_analysis': analyze_timestamps(post)
        }
        enhanced_posts.append(enhanced_post)
    
    return jsonify({
        'posts': enhanced_posts,
        'total': len(enhanced_posts),
        'admin_access': True,
        'classification': 'restricted'
    })

@onion_admin.route('/system/security', methods=['GET'])
@require_auth
@require_2fa
def security_overview():
    """System security overview"""
    from auth_models import AccessLog, APIRateLimit
    
    # Recent access logs
    recent_logs = AccessLog.query.order_by(
        AccessLog.timestamp.desc()
    ).limit(50).all()
    
    # Failed login attempts
    failed_attempts = AccessLog.query.filter_by(
        status_code=401
    ).order_by(AccessLog.timestamp.desc()).limit(20).all()
    
    # Rate limit violations
    rate_violations = APIRateLimit.query.filter(
        APIRateLimit.requests_count > 80
    ).all()
    
    return jsonify({
        'security_overview': {
            'recent_access': [
                {
                    'user_id': log.user_id,
                    'ip': log.ip_address,
                    'endpoint': log.endpoint,
                    'status': log.status_code,
                    'timestamp': log.timestamp.isoformat()
                }
                for log in recent_logs
            ],
            'failed_attempts': [
                {
                    'ip': log.ip_address,
                    'endpoint': log.endpoint,
                    'timestamp': log.timestamp.isoformat()
                }
                for log in failed_attempts
            ],
            'rate_violations': [
                {
                    'ip': rv.ip_address,
                    'endpoint': rv.endpoint,
                    'requests': rv.requests_count,
                    'window_start': rv.window_start.isoformat()
                }
                for rv in rate_violations
            ]
        }
    })

@onion_admin.route('/system/users/manage', methods=['POST'])
@require_auth
@require_2fa
def manage_users():
    """Manage user accounts"""
    data = request.get_json()
    action = data.get('action')  # create, deactivate, reset_api, grant_admin
    target_user_id = data.get('user_id')
    
    if action == 'create':
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')
        
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        user.generate_api_key()
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict()
        })
    
    elif action == 'deactivate':
        user = User.query.get(target_user_id)
        if user:
            user.is_active = False
            db.session.commit()
            return jsonify({'message': 'User deactivated'})
    
    elif action == 'reset_api':
        user = User.query.get(target_user_id)
        if user:
            user.generate_api_key()
            db.session.commit()
            return jsonify({
                'message': 'API key reset',
                'new_api_key': user.api_key
            })
    
    return jsonify({'error': 'Invalid action or user not found'}), 400

def calculate_risk_score(post):
    """Calculate risk score for a post"""
    score = 0
    
    # Check for high-risk keywords
    high_risk_keywords = [
        'breach', 'leak', 'vulnerability', 'exploit', 
        'password', 'credential', 'database', 'hack'
    ]
    
    title = post.get('title', '').lower()
    summary = post.get('summary', '').lower()
    
    for keyword in high_risk_keywords:
        if keyword in title or keyword in summary:
            score += 10
    
    # Check source reliability
    source = post.get('source', '')
    if source in ['Hacker News', 'PrivacyGuides']:
        score += 5  # More reliable sources
    
    return min(score, 100)  # Cap at 100

def identify_data_sources(post):
    """Identify data sources mentioned in post"""
    text = f"{post.get('title', '')} {post.get('summary', '')}".lower()
    
    data_sources = []
    source_keywords = {
        'social_media': ['facebook', 'twitter', 'instagram', 'linkedin'],
        'databases': ['mysql', 'mongodb', 'postgresql', 'redis'],
        'cloud': ['aws', 'azure', 'gcp', 'cloud'],
        'websites': ['website', 'web', 'site', 'domain']
    }
    
    for category, keywords in source_keywords.items():
        for keyword in keywords:
            if keyword in text:
                data_sources.append(category)
                break
    
    return list(set(data_sources))

def extract_geo_indicators(post):
    """Extract geographic indicators from post"""
    text = f"{post.get('title', '')} {post.get('summary', '')}".lower()
    
    # Simple country/region detection
    geo_keywords = {
        'us': ['united states', 'usa', 'america'],
        'eu': ['europe', 'european', 'eu'],
        'asia': ['china', 'japan', 'india', 'asia'],
        'global': ['global', 'worldwide', 'international']
    }
    
    regions = []
    for region, keywords in geo_keywords.items():
        for keyword in keywords:
            if keyword in text:
                regions.append(region)
                break
    
    return regions

def analyze_timestamps(post):
    """Analyze timestamp patterns"""
    timestamp = post.get('timestamp', '')
    
    try:
        # Parse timestamp if possible
        from datetime import datetime
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        return {
            'hour': dt.hour,
            'day_of_week': dt.weekday(),
            'is_weekend': dt.weekday() >= 5,
            'time_zone_offset': 'UTC'  # Simplified
        }
    except:
        return {'analysis': 'timestamp_parse_failed'}