"""
User authentication routes for the OSINT platform
"""
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from werkzeug.security import check_password_hash
from datetime import datetime
import re
import logging

from auth_models import User, UserSession, Alert, Watchlist, Case, GraphNode, GraphEdge
from auth_utils import (
    login_required, admin_required, get_current_user,
    create_jwt_token, create_user_session
)
from models import db, CVEItem as CVE
from bots.bot_manager import BotManager
from cve_manager import CVEManager

logger = logging.getLogger(__name__)

# Create user routes blueprint
user_routes = Blueprint('user_routes', __name__)

# Initialize BotManager instance
bot_manager = BotManager()

@user_routes.route('/')
def homepage():
    """Serve the new homepage"""
    return render_template('new_homepage.html')

@user_routes.route('/login')
def login_page():
    """Serve the login page"""
    return render_template('login.html')

@user_routes.route('/register')
def register_page():
    """Serve the registration page"""
    return render_template('register.html')

@user_routes.route('/dashboard')
@login_required
def dashboard():
    """User dashboard - requires authentication"""
    user = get_current_user()
    return render_template('user_dashboard.html', user=user)

# API Routes
@user_routes.route('/api/auth/register', methods=['POST'])
def api_register():
    """Handle user registration"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['full_name', 'username', 'email', 'password', 'confirm_password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate data
        full_name = data['full_name'].strip()
        username = data['username'].strip().lower()
        email = data['email'].strip().lower()
        password = data['password']
        confirm_password = data['confirm_password']
        terms = data.get('terms', False)
        
        # Basic validation
        if len(full_name) < 2:
            return jsonify({'error': 'Full name must be at least 2 characters'}), 400
        
        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters'}), 400
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return jsonify({'error': 'Username can only contain letters, numbers, and underscores'}), 400
        
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            return jsonify({'error': 'Please enter a valid email address'}), 400
        
        if len(password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        
        if password != confirm_password:
            return jsonify({'error': 'Passwords do not match'}), 400
        
        if not terms:
            return jsonify({'error': 'You must agree to the terms of service'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing_user:
            if existing_user.username == username:
                return jsonify({'error': 'Username is already taken'}), 400
            else:
                return jsonify({'error': 'Email is already registered'}), 400
        
        # Create new user
        user = User(
            username=username,
            email=email,
            full_name=full_name,
            is_active=False  # Requires admin approval
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'Registration successful! Please wait for admin approval.',
            'user_id': user.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed. Please try again.'}), 500

@user_routes.route('/api/auth/login', methods=['POST'])
def api_login():
    """Handle user login"""
    try:
        data = request.get_json()
        
        username_or_email = data.get('username', '').strip().lower()
        password = data.get('password', '')
        remember = data.get('remember', False)
        
        if not username_or_email or not password:
            return jsonify({'error': 'Username/email and password are required'}), 400
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account pending admin approval'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Create session
        session['user_id'] = user.id
        session['username'] = user.username
        
        # Create JWT token
        token = create_jwt_token(user.id)
        
        # Create user session record
        session_token = create_user_session(
            user, 
            request.remote_addr, 
            request.headers.get('User-Agent')
        )
        
        return jsonify({
            'message': 'Login successful',
            'token': token,
            'user': user.to_dict(),
            'redirect_url': '/dashboard'
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Login failed. Please try again.'}), 500

@user_routes.route('/api/auth/logout', methods=['POST'])
@login_required
def api_logout():
    """Handle user logout"""
    try:
        # Clear session
        session.clear()
        
        return jsonify({'message': 'Logout successful'}), 200
        
    except Exception as e:
        return jsonify({'error': 'Logout failed'}), 500

@user_routes.route('/api/auth/check-username', methods=['POST'])
def check_username():
    """Check if username is available"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip().lower()
        
        if len(username) < 3:
            return jsonify({'available': False, 'error': 'Username too short'}), 400
        
        existing_user = User.query.filter_by(username=username).first()
        
        return jsonify({'available': existing_user is None}), 200
        
    except Exception as e:
        return jsonify({'available': False, 'error': 'Check failed'}), 500

@user_routes.route('/api/auth/user')
@login_required
def get_user_info():
    """Get current user information"""
    try:
        user = get_current_user()
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get user info'}), 500

@user_routes.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'OSINT Platform API'
    }), 200

@user_routes.route('/stats/simple', methods=['GET'])
@login_required
def get_simple_stats():
    """Get simple dashboard statistics"""
    try:
        return jsonify(bot_manager.get_simple_stats()), 200
    except Exception as e:
        return jsonify({'error': 'Failed to load simple stats'}), 500

@user_routes.route('/api/user/alerts', methods=['GET'])
@login_required
def get_user_alerts():
    """Get user alerts"""
    try:
        user = get_current_user()
        alerts = Alert.query.filter_by(user_id=user.id).all()
        return jsonify({
            'success': True,
            'alerts': [alert.to_dict() for alert in alerts]
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to load alerts'}), 500


@user_routes.route('/api/user/watchlists', methods=['GET'])
@login_required
def get_user_watchlists():
    """Get user watchlists"""
    try:
        user = get_current_user()
        watchlists = Watchlist.query.filter_by(user_id=user.id).all()
        return jsonify({
            'success': True,
            'watchlists': [watchlist.to_dict() for watchlist in watchlists]
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to load watchlists'}), 500


@user_routes.route('/api/user/watchlists', methods=['POST'])
@login_required
def create_watchlist():
    """Create a new watchlist"""
    try:
        data = request.get_json()
        user = get_current_user()
        
        if not data.get('query') or not data.get('search_type'):
            return jsonify({'error': 'Query and search type are required'}), 400
        
        watchlist = Watchlist(
            user_id=user.id,
            query=data['query'],
            search_type=data['search_type'],
            frequency=data.get('frequency', 'daily')
        )
        
        db.session.add(watchlist)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Watchlist created successfully',
            'watchlist': watchlist.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create watchlist'}), 500


@user_routes.route('/api/user/graph', methods=['GET'])
@login_required
def get_user_graph():
    """Get user graph data"""
    try:
        user = get_current_user()
        nodes = GraphNode.query.filter_by(user_id=user.id).all()
        edges = GraphEdge.query.filter_by(user_id=user.id).all()
        return jsonify({
            'success': True,
            'graph': {
                'nodes': [node.to_dict() for node in nodes],
                'edges': [edge.to_dict() for edge in edges]
            }
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to load graph data'}), 500


@user_routes.route('/api/user/cases', methods=['GET'])
@login_required
def get_user_cases():
    """Get user cases"""
    try:
        user = get_current_user()
        cases = Case.query.filter_by(user_id=user.id).all()
        return jsonify({
            'success': True,
            'cases': [case.to_dict() for case in cases]
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to load cases'}), 500


@user_routes.route('/api/user/cves', methods=['GET'])
@login_required
def get_user_cves():
    """Get CVEs for user dashboard"""
    try:
        # Get query parameters for filtering
        limit = request.args.get('limit', type=int)
        severity = request.args.get('severity')
        search = request.args.get('search')

        # Use CVEManager to get CVEs
        if search:
            cves = CVEManager.search_cves(search, limit=limit)
        elif severity:
            cves = CVEManager.get_cves_by_severity(severity, limit=limit)
        else:
            cves = CVEManager.get_all_cves(limit=limit)

        return jsonify({
            'success': True,
            'cves': cves
        }), 200
    except Exception as e:
        logger.error(f"Error loading CVEs: {e}")
        return jsonify({'error': 'Failed to load CVEs'}), 500




@user_routes.route('/api/user/stats', methods=['GET'])
@login_required
def get_user_stats():
    """Get comprehensive platform statistics for dashboard overview"""
    try:
        stats_data = bot_manager.get_stats()
        return jsonify({
            'success': True,
            'stats': stats_data.get('stats', {}),
            'charts': stats_data.get('charts', {})
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to load stats'
        }), 500

@user_routes.route('/api/user/breach-leak-data', methods=['GET'])
@login_required
def get_user_breach_leak_data():
    """Return combined breach and leak items for the user dashboard (requires auth)."""
    try:
        limit = min(int(request.args.get('limit', 50)), 500)
        from models import BreachItem, LeakItem

        # Query admin-side breaches and leaks
        breaches = BreachItem.query.order_by(BreachItem.created_at.desc()).limit(limit).all()
        leaks = LeakItem.query.order_by(LeakItem.created_at.desc()).limit(limit).all()

        # Normalize records
        breaches_data = [{
            'id': b.id,
            'type': 'breach',
            'title': b.name,
            'description': b.description,
            'records_affected': b.records_affected,
            'source_url': b.source_url,
            'created_at': b.created_at.isoformat() if b.created_at else None
        } for b in breaches]

        leaks_data = [{
            'id': l.id,
            'type': 'leak',
            'title': l.source,
            'description': l.data_content,
            'verification_status': l.verification_status,
            'associated_breach_id': l.associated_breach_id,
            'created_at': l.created_at.isoformat() if l.created_at else None
        } for l in leaks]

        combined = breaches_data + leaks_data
        combined.sort(key=lambda x: x.get('created_at') or '', reverse=True)

        return jsonify({'success': True, 'data': combined}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to load breach/leak data', 'details': str(e)}), 500

# Admin routes for user management
@user_routes.route('/api/admin/users')
@admin_required
def get_all_users():
    """Get all users (admin only)"""
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users]), 200
        
    except Exception as e:
        return jsonify({'error': 'Failed to get users'}), 500

@user_routes.route('/api/admin/users/<int:user_id>/approve', methods=['POST'])
@admin_required
def approve_user(user_id):
    """Approve a user (admin only)"""
    try:
        user = User.query.get_or_404(user_id)
        admin = get_current_user()
        
        user.is_active = True
        user.approved_at = datetime.utcnow()
        user.approved_by = admin.id
        
        db.session.commit()
        
        return jsonify({
            'message': f'User {user.username} approved successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to approve user'}), 500

@user_routes.route('/api/admin/users/<int:user_id>/reject', methods=['POST'])
@admin_required
def reject_user(user_id):
    """Reject/deactivate a user (admin only)"""
    try:
        user = User.query.get_or_404(user_id)
        
        user.is_active = False
        user.approved_at = None
        user.approved_by = None
        
        db.session.commit()
        
        return jsonify({
            'message': f'User {user.username} rejected successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to reject user'}), 500

@user_routes.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """Delete a user (admin only)"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Don't allow deleting admin users
        if user.is_admin:
            return jsonify({'error': 'Cannot delete admin users'}), 403
        
        # Delete user sessions first
        UserSession.query.filter_by(user_id=user_id).delete()
        
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'message': f'User {username} deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete user'}), 500

# Error handlers
@user_routes.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@user_routes.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500