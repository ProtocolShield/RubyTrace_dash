"""
Integration layer for radar.protocolshield.com WordPress frontend
"""
from flask import Flask, jsonify, request, Blueprint
from flask_cors import cross_origin
from datetime import datetime
from auth_utils import require_rate_limit
from utils.json_utils import load_existing_data
from config import OUTPUT_FILE
from auth_models import MapData

# WordPress integration blueprint
radar_api = Blueprint('radar_api', __name__, url_prefix='/radar')

@radar_api.route('/health', methods=['GET'])
@cross_origin(origins=['https://radar.protocolshield.com'])
def radar_health():
    """Health check for WordPress integration"""
    return jsonify({
        'status': 'operational',
        'services': {
            'osint_collector': 'active',
            'data_api': 'available',
            'map_services': 'ready',
            'authentication': 'enabled'
        },
        'timestamp': datetime.utcnow().isoformat()
    })

@radar_api.route('/public/posts', methods=['GET'])
@cross_origin(origins=['https://radar.protocolshield.com'])
@require_rate_limit(limit_per_hour=200)
def public_posts():
    """Public posts endpoint for WordPress frontend"""
    # Get filtering parameters
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))
    source_filter = request.args.get('source')
    keyword = request.args.get('keyword')
    
    # Load and filter posts
    all_posts = load_existing_data(OUTPUT_FILE)
    filtered_posts = []
    
    for post in all_posts:
        # Remove sensitive fields for public API
        public_post = {
            'id': post.get('url', '')[-10:],  # Use URL suffix as ID
            'title': post.get('title', ''),
            'summary': post.get('summary', ''),
            'source': post.get('source', ''),
            'timestamp': post.get('timestamp', ''),
            'risk_level': calculate_public_risk_level(post)
        }
        
        # Apply filters
        if source_filter and post.get('source') != source_filter:
            continue
        if keyword and keyword.lower() not in post.get('title', '').lower():
            continue
            
        filtered_posts.append(public_post)
    
    # Sort by timestamp (newest first)
    filtered_posts.sort(
        key=lambda x: x.get('timestamp', ''), 
        reverse=True
    )
    
    # Pagination
    total = len(filtered_posts)
    paginated_posts = filtered_posts[offset:offset + limit]
    
    return jsonify({
        'posts': paginated_posts,
        'pagination': {
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_more': offset + limit < total
        },
        'filters_applied': {
            'source': source_filter,
            'keyword': keyword
        }
    })

@radar_api.route('/public/sources', methods=['GET'])
@cross_origin(origins=['https://radar.protocolshield.com'])
def public_sources():
    """Available data sources for filtering"""
    posts = load_existing_data(OUTPUT_FILE)
    sources = list(set(post.get('source', 'Unknown') for post in posts))
    
    source_stats = {}
    for source in sources:
        count = len([p for p in posts if p.get('source') == source])
        source_stats[source] = count
    
    return jsonify({
        'sources': sources,
        'statistics': source_stats,
        'total_sources': len(sources)
    })

@radar_api.route('/public/map/incidents', methods=['GET'])
@cross_origin(origins=['https://radar.protocolshield.com'])
@require_rate_limit(limit_per_hour=100)
def public_map_incidents():
    """Public map data for WordPress visualization"""
    # Get map data with limited detail for public consumption
    map_points = MapData.query.all()
    
    public_map_data = []
    for point in map_points:
        public_point = {
            'latitude': round(point.latitude, 2),  # Reduced precision
            'longitude': round(point.longitude, 2),
            'country': point.country,
            'city': point.city,
            'incident_count': min(point.breach_count, 50),  # Cap for public view
            'risk_level': point.risk_level,
            'last_updated': point.created_at.strftime('%Y-%m')  # Month precision
        }
        public_map_data.append(public_point)
    
    return jsonify({
        'incidents': public_map_data,
        'total_locations': len(public_map_data),
        'risk_summary': {
            'high_risk': len([p for p in map_points if p.risk_level == 'high']),
            'medium_risk': len([p for p in map_points if p.risk_level == 'medium']),
            'low_risk': len([p for p in map_points if p.risk_level == 'low'])
        },
        'data_classification': 'public_summary'
    })

@radar_api.route('/public/stats', methods=['GET'])
@cross_origin(origins=['https://radar.protocolshield.com'])
def public_statistics():
    """Public statistics for WordPress dashboard widgets"""
    posts = load_existing_data(OUTPUT_FILE)
    map_points = MapData.query.all()
    
    # Calculate basic statistics
    total_posts = len(posts)
    total_incidents = len(map_points)
    
    # Recent activity (last 7 days)
    from datetime import timedelta
    recent_cutoff = (datetime.utcnow() - timedelta(days=7)).isoformat()
    recent_posts = [
        p for p in posts 
        if p.get('timestamp', '') > recent_cutoff
    ]
    
    # Source breakdown
    source_breakdown = {}
    for post in posts:
        source = post.get('source', 'Unknown')
        source_breakdown[source] = source_breakdown.get(source, 0) + 1
    
    return jsonify({
        'overview': {
            'total_posts': total_posts,
            'total_incidents': total_incidents,
            'recent_posts_7d': len(recent_posts),
            'active_sources': len(source_breakdown)
        },
        'source_breakdown': source_breakdown,
        'risk_distribution': {
            'high': len([p for p in map_points if p.risk_level == 'high']),
            'medium': len([p for p in map_points if p.risk_level == 'medium']),
            'low': len([p for p in map_points if p.risk_level == 'low'])
        },
        'last_updated': datetime.utcnow().isoformat()
    })

@radar_api.route('/public/search', methods=['POST'])
@cross_origin(origins=['https://radar.protocolshield.com'])
@require_rate_limit(limit_per_hour=50)
def public_search():
    """Public search endpoint for WordPress"""
    data = request.get_json()
    query = data.get('query', '').strip().lower()
    
    if not query or len(query) < 3:
        return jsonify({'error': 'Query must be at least 3 characters'}), 400
    
    posts = load_existing_data(OUTPUT_FILE)
    results = []
    
    for post in posts:
        title = post.get('title', '').lower()
        summary = post.get('summary', '').lower()
        
        if query in title or query in summary:
            result = {
                'title': post.get('title', ''),
                'summary': post.get('summary', '')[:200] + '...',  # Truncate
                'source': post.get('source', ''),
                'timestamp': post.get('timestamp', ''),
                'relevance': calculate_relevance(query, post)
            }
            results.append(result)
    
    # Sort by relevance
    results.sort(key=lambda x: x['relevance'], reverse=True)
    
    return jsonify({
        'query': query,
        'results': results[:20],  # Limit to 20 results
        'total_matches': len(results)
    })

@radar_api.route('/wordpress/config', methods=['GET'])
@cross_origin(origins=['https://radar.protocolshield.com'])
def wordpress_config():
    """Configuration data for WordPress integration"""
    return jsonify({
        'api_version': '2.0',
        'endpoints': {
            'posts': '/radar/public/posts',
            'map': '/radar/public/map/incidents',
            'stats': '/radar/public/stats',
            'search': '/radar/public/search',
            'sources': '/radar/public/sources'
        },
        'rate_limits': {
            'posts': '200 requests/hour',
            'map': '100 requests/hour',
            'search': '50 requests/hour',
            'general': '1000 requests/hour'
        },
        'data_update_frequency': '30 minutes',
        'supported_filters': ['source', 'keyword', 'risk_level'],
        'cors_enabled': True
    })

def calculate_public_risk_level(post):
    """Calculate simplified risk level for public display"""
    title = post.get('title', '').lower()
    summary = post.get('summary', '').lower()
    
    high_risk_keywords = ['breach', 'leak', 'hack', 'vulnerability', 'exploit']
    medium_risk_keywords = ['security', 'privacy', 'data', 'credential']
    
    for keyword in high_risk_keywords:
        if keyword in title or keyword in summary:
            return 'high'
    
    for keyword in medium_risk_keywords:
        if keyword in title or keyword in summary:
            return 'medium'
    
    return 'low'

def calculate_relevance(query, post):
    """Calculate search relevance score"""
    title = post.get('title', '').lower()
    summary = post.get('summary', '').lower()
    
    score = 0
    
    # Title matches are more important
    if query in title:
        score += 10
    
    # Summary matches
    if query in summary:
        score += 5
    
    # Exact word matches
    title_words = title.split()
    summary_words = summary.split()
    
    if query in title_words:
        score += 15
    
    if query in summary_words:
        score += 8
    
    return score