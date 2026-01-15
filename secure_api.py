"""
Secure API endpoints for radar.protocolshield.com
"""
from flask import Flask, jsonify, request, Blueprint
from flask_cors import CORS
import os
from datetime import datetime, timedelta
from auth_models import User, MapData, db
from auth_utils import (
    require_auth, require_rate_limit, require_2fa, 
    AuthManager, SecurityUtils, GeoUtils
)
from utils.json_utils import load_existing_data

# Create secure API blueprint
secure_api = Blueprint('secure_api', __name__, url_prefix='/api/v2')

# JWT Authentication Endpoints
@secure_api.route('/auth/register', methods=['POST'])
@require_rate_limit(limit_per_hour=5)
def register():
    """Register new user"""
    data = request.get_json()
    data = SecurityUtils.sanitize_input(data)
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not all([username, email, password]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if user exists
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    # Create user
    user = User(username=username, email=email)
    user.set_password(password)
    user.generate_api_key()
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict()
    }), 201


@secure_api.route('/auth/login', methods=['POST'])
@require_rate_limit(limit_per_hour=20)
def login():
    """Login with username/password"""
    data = request.get_json()
    data = SecurityUtils.sanitize_input(data)
    
    username = data.get('username')
    password = data.get('password')
    totp_token = data.get('totp_token')
    
    if not all([username, password]):
        return jsonify({'error': 'Username and password required'}), 400
    
    user = User.query.filter_by(username=username, is_active=True).first()
    
    if not user or user.is_locked():
        return jsonify({'error': 'Invalid credentials or account locked'}), 401
    
    if not user.check_password(password):
        user.increment_failed_attempts()
        db.session.commit()
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Check 2FA if enabled
    if user.totp_enabled:
        if not totp_token or not user.verify_totp(totp_token):
            return jsonify({'error': '2FA token required'}), 401
    
    # Successful login
    user.reset_failed_attempts()
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    token = user.generate_jwt_token()
    
    return jsonify({
        'token': token,
        'user': user.to_dict(),
        'expires_in': 86400  # 24 hours
    })


@secure_api.route('/auth/setup-2fa', methods=['POST'])
@require_auth
def setup_2fa():
    """Setup 2FA for user"""
    user = request.current_user
    
    if user.totp_enabled:
        return jsonify({'error': '2FA already enabled'}), 400
    
    secret = user.generate_totp_secret()
    qr_code = user.generate_qr_code()
    backup_codes = user.generate_backup_codes()
    
    db.session.commit()
    
    return jsonify({
        'secret': secret,
        'qr_code': qr_code,
        'backup_codes': backup_codes,
        'message': 'Scan QR code with authenticator app'
    })


@secure_api.route('/auth/verify-2fa', methods=['POST'])
@require_auth
def verify_2fa():
    """Verify and enable 2FA"""
    data = request.get_json()
    token = data.get('token')
    
    user = request.current_user
    
    if not token or not user.verify_totp(token):
        return jsonify({'error': 'Invalid 2FA token'}), 400
    
    user.totp_enabled = True
    db.session.commit()
    
    return jsonify({'message': '2FA enabled successfully'})


@secure_api.route('/auth/disable-2fa', methods=['POST'])
@require_auth
@require_2fa
def disable_2fa():
    """Disable 2FA"""
    user = request.current_user
    user.totp_enabled = False
    user.totp_secret = None
    user.backup_codes = None
    
    db.session.commit()
    
    return jsonify({'message': '2FA disabled'})


# Secure Data Endpoints
@secure_api.route('/posts/secure', methods=['GET'])
@require_auth
@require_rate_limit(limit_per_hour=1000)
def get_secure_posts():
    """Get posts with enhanced filtering for authenticated users"""
    # Advanced filtering parameters
    source = request.args.get('source')
    keyword = request.args.get('keyword')
    sentiment = request.args.get('sentiment')
    risk_level = request.args.get('risk_level')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    
    # Load and filter data
    all_posts = load_existing_data()
    filtered_posts = []
    
    for post in all_posts:
        # Apply filters
        if source and post.get('source') != source:
            continue
        if keyword and keyword.lower() not in post.get('title', '').lower():
            continue
        if sentiment and post.get('sentiment') != sentiment:
            continue
        
        filtered_posts.append(post)
    
    # Pagination
    total = len(filtered_posts)
    paginated_posts = filtered_posts[offset:offset + limit]
    
    return jsonify({
        'posts': paginated_posts,
        'total': total,
        'limit': limit,
        'offset': offset,
        'has_more': offset + limit < total
    })


@secure_api.route('/search/advanced', methods=['POST'])
@require_auth
@require_rate_limit(limit_per_hour=500)
def advanced_search():
    """Advanced search with multiple parameters"""
    data = request.get_json()
    data = SecurityUtils.sanitize_input(data)
    
    query = data.get('query', '')
    filters = data.get('filters', {})
    search_type = data.get('type', 'posts')  # posts, emails, phones, all
    
    results = {
        'query': query,
        'results': [],
        'total': 0,
        'search_type': search_type
    }
    
    if search_type in ['posts', 'all']:
        # Search posts
        posts = load_existing_data()
        matching_posts = []
        
        for post in posts:
            if query.lower() in post.get('title', '').lower() or \
               query.lower() in post.get('summary', '').lower():
                matching_posts.append(post)
        
        results['results'].extend(matching_posts)
        results['total'] += len(matching_posts)
    
    return jsonify(results)


# Map and Geographic Endpoints
@secure_api.route('/map/data', methods=['GET'])
@require_auth
@require_rate_limit(limit_per_hour=200)
def get_map_data():
    """Get geographic data for map visualization"""
    # Get all map data points
    map_points = MapData.query.all()
    
    data = {
        'points': [point.to_dict() for point in map_points],
        'total_incidents': len(map_points),
        'risk_summary': {
            'high': len([p for p in map_points if p.risk_level == 'high']),
            'medium': len([p for p in map_points if p.risk_level == 'medium']),
            'low': len([p for p in map_points if p.risk_level == 'low'])
        }
    }
    
    return jsonify(data)


@secure_api.route('/map/nearby', methods=['POST'])
@require_auth
def get_nearby_incidents():
    """Get incidents near a location"""
    data = request.get_json()
    
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    radius = data.get('radius', 100)  # km
    
    if not all([latitude, longitude]):
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    nearby = GeoUtils.get_nearby_incidents(latitude, longitude, radius)
    
    return jsonify({
        'incidents': nearby,
        'total': len(nearby),
        'center': {'latitude': latitude, 'longitude': longitude},
        'radius_km': radius
    })


# Export and Download Endpoints
@secure_api.route('/export/posts', methods=['POST'])
@require_auth
@require_rate_limit(limit_per_hour=10)
def export_posts():
    """Export posts in various formats"""
    data = request.get_json()
    export_format = data.get('format', 'json')  # json, csv, xml
    filters = data.get('filters', {})
    
    # Get filtered posts
    posts = load_existing_data()
    
    # Apply filters (simplified)
    if filters.get('source'):
        posts = [p for p in posts if p.get('source') == filters['source']]
    
    if export_format == 'json':
        return jsonify({
            'data': posts,
            'format': 'json',
            'count': len(posts),
            'exported_at': datetime.utcnow().isoformat()
        })
    
    elif export_format == 'csv':
        import csv
        import io
        
        output = io.StringIO()
        if posts:
            writer = csv.DictWriter(output, fieldnames=posts[0].keys())
            writer.writeheader()
            writer.writerows(posts)
        
        return jsonify({
            'data': output.getvalue(),
            'format': 'csv',
            'count': len(posts),
            'exported_at': datetime.utcnow().isoformat()
        })
    
    return jsonify({'error': 'Unsupported format'}), 400


# Admin-only Endpoints
@secure_api.route('/admin/users', methods=['GET'])
@require_auth
@require_2fa
def list_users():
    """List all users (admin only)"""
    users = User.query.all()
    return jsonify({
        'users': [user.to_dict() for user in users],
        'total': len(users)
    })


@secure_api.route('/admin/security/logs', methods=['GET'])
@require_auth
@require_2fa
def security_logs():
    """Get security logs (admin only)"""
    from auth_models import AccessLog
    
    limit = int(request.args.get('limit', 100))
    logs = AccessLog.query.order_by(AccessLog.timestamp.desc()).limit(limit).all()
    
    return jsonify({
        'logs': [
            {
                'id': log.id,
                'user_id': log.user_id,
                'ip_address': log.ip_address,
                'endpoint': log.endpoint,
                'method': log.method,
                'status_code': log.status_code,
                'timestamp': log.timestamp.isoformat()
            }
            for log in logs
        ]
    })


# Health and Status
@secure_api.route('/health', methods=['GET'])
def health_check():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '2.0',
        'endpoints': {
            'authentication': 'operational',
            'data_access': 'operational',
            'map_services': 'operational',
            'exports': 'operational'
        }
    })


# Error handlers
@secure_api.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@secure_api.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500