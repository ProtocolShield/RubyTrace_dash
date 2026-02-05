"""
API for accessing the privacy OSINT data.
"""
from flask import Flask, jsonify, request, send_from_directory, session, redirect, send_file
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import json
import logging
import os
import threading
from config import (
    OUTPUT_FILE, API_PORT, API_HOST, PRIVACY_KEYWORDS,
    SOURCES, REDDIT_SUBREDDITS, SOURCES_CONFIG_FILE
)
from utils.json_utils import load_existing_data, save_data
from nlp_utils import enrich_post_with_nlp
from searchers.email_search import search_email, clear_email_cache
from searchers.phone_search import search_phone, clear_phone_cache
from crawlers.crawler_scheduler import start_crawler_scheduler, stop_crawler_scheduler, crawler_scheduler
from datetime import datetime
from models import db, ApiKey, Source, KeywordAlert, ScrapeLog, Bot, BotLog, DataSource, RawData, Entity, Relationship, SearchIndex, BotSchedule, GlobalConfig
from api_integrations import api_manager
from api_integrations.wayback_integration import WaybackIntegration
from api_integrations.openai_integration import OpenAIIntegration
from file_upload_system import upload_manager

# Import secure API components
from secure_api import secure_api
from onion_admin import onion_admin
from radar_integration import radar_api
from auth_models import User, AccessLog, APIRateLimit, MapData
from auth_utils import require_auth, require_rate_limit, SecurityUtils
from user_routes import user_routes

# Set up logger
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, static_folder='static')
CORS(app)

# Register secure API blueprints
app.register_blueprint(secure_api)
app.register_blueprint(onion_admin)
app.register_blueprint(radar_api)
app.register_blueprint(user_routes)

# Configure sessions
app.secret_key = os.environ.get('SECRET_KEY', 'privacy-osint-secret-key')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours in seconds

# Configure the database
db.configured = True
# Prefer DATABASE_URL from environment; fall back to local SQLite for development
_env_db_url = os.environ.get('DATABASE_URL', '').strip()
if _env_db_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = _env_db_url
else:
    # Local SQLite file in project root
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.getcwd(), 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 5,
    'max_overflow': 10,
    'pool_timeout': 30,
    'pool_recycle': 1800,  # Recycle connections after 30 minutes
    'pool_pre_ping': True  # Check connection before using
}

# Ensure SQLAlchemy is initialized with Flask app
with app.app_context():
    db.init_app(app)
    db.create_all()

# Admin user credentials - in a production environment, these should be stored in a database
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD_HASH = generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'privacy123'))

# Import the retry decorator
from database import with_retry

# Initialize API integrations from stored API keys
def initialize_api_integrations():
    """Initialize API integrations from stored API keys"""
    try:
        api_keys = ApiKey.query.all()
        for key in api_keys:
            service = key.service.lower()
            if service == 'wayback':
                api_manager.register_integration(WaybackIntegration, key.key)
            elif service == 'openai':
                api_manager.register_integration(OpenAIIntegration, key.key)
            # Add other services here as needed
        logging.info("API integrations initialized successfully")
    except Exception as e:
        logging.error(f"Error initializing API integrations: {e}")

# Initialize integrations when app starts
with app.app_context():
    initialize_api_integrations()

@app.route('/')
def landing():
    """Serve the new homepage with integrated OSINT dashboard."""
    return send_from_directory('static', 'homepage.html')

@app.route('/eng/login')
def admin_login():
    """Serve the admin login page."""
    return send_from_directory('static', 'admin_login.html')

@app.route('/admin')
def admin_route():
    """Serve the admin dashboard."""
    # Check if the user is logged in
    if not session.get('admin_logged_in'):
        return redirect('/eng/login')
    return send_from_directory('static', 'index.html')

@app.route('/admin/configure-apis')
def admin_configure_apis():
    """Serve the API configuration panel."""
    # Check if the user is logged in
    if not session.get('admin_logged_in'):
        return redirect('/eng/login')
    return send_from_directory('templates', 'admin_api_panel.html')
    
@app.route('/dashboard')
def admin_dashboard():
    """Serve the admin dashboard after successful login."""
    # Check if the user is logged in
    if not session.get('admin_logged_in'):
        return redirect('/eng/login')
    return send_from_directory('static', 'index.html')
     
@app.route('/<path:path>')
def static_files(path):
    """Serve static files."""
    return send_from_directory('static', path)
    
@app.route('/api/admin-login', methods=['POST'])
def handle_admin_login():
    """Handle admin login authentication."""
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Invalid request, no data provided"}), 400
        
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
        
    # Check if the credentials match
    if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
        # Set the session variable to indicate the user is logged in
        session['admin_logged_in'] = True
        session['admin_username'] = username
        
        return jsonify({"success": True, "message": "Login successful"})
    else:
        return jsonify({"error": "Invalid username or password"}), 401

@app.route('/api/admin-logout', methods=['POST'])
def handle_admin_logout():
    """Handle admin logout."""
    # Clear the session
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    
    return jsonify({"success": True, "message": "Logout successful"})

@app.route('/api/crawler/start', methods=['POST'])
def start_crawler():
    """Start the enhanced crawler system."""
    try:
        start_crawler_scheduler()
        return jsonify({"success": True, "message": "Enhanced crawler started"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/crawler/stop', methods=['POST'])
def stop_crawler():
    """Stop the enhanced crawler system."""
    try:
        stop_crawler_scheduler()
        return jsonify({"success": True, "message": "Enhanced crawler stopped"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/crawler/status', methods=['GET'])
def crawler_status():
    """Get the status of the enhanced crawler."""
    try:
        status = {
            "running": crawler_scheduler.running,
            "discovered_sites": len(crawler_scheduler._get_active_sources()) if hasattr(crawler_scheduler, '_get_active_sources') else 0,
            "active_keywords": len(crawler_scheduler._get_active_keywords()) if hasattr(crawler_scheduler, '_get_active_keywords') else 0
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/crawler/run-manual', methods=['POST'])
def run_manual_crawl():
    """Run a manual crawl with specified parameters."""
    try:
        data = request.get_json()
        keywords = data.get('keywords', [])
        use_tor = data.get('use_tor', False)
        
        if not keywords:
            return jsonify({"error": "Keywords are required"}), 400
        
        # Run crawler with Flask application context
        import asyncio
        from crawlers.enhanced_crawler import run_crawler_with_context
        
        def run_crawl():
            with app.app_context():  # Ensure Flask application context
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    # Add timeout to prevent worker timeout
                    results = asyncio.wait_for(
                        run_crawler_with_context(keywords, use_tor=use_tor),
                        timeout=45  # 45 second timeout to prevent worker timeout
                    )
                    results = loop.run_until_complete(results)
                    return results
                except asyncio.TimeoutError:
                    return {"error": "Crawl timed out", "discovered_sites": 0}
                except Exception as e:
                    logging.error(f"Manual crawl error: {e}")
                    return {"error": str(e), "discovered_sites": 0}
                finally:
                    loop.close()
        
        results = run_crawl()
        
        # Return more detailed results
        if isinstance(results, dict):
            discovered_count = results.get('discovered_sites', 0)
            return jsonify({
                "success": True, 
                "message": f"Manual crawl completed - found {discovered_count} sites",
                "results_count": discovered_count,
                "details": results
            })
        else:
            return jsonify({
                "success": True, 
                "message": f"Manual crawl completed",
                "results_count": len(results) if isinstance(results, list) else 0
            })
        
    except Exception as e:
        logging.error(f"Manual crawl endpoint error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/scraper/run', methods=['POST'])
def run_manual_scrape():
    """Run manual scraping of all configured sources."""
    try:
        def run_scrape():
            try:
                from main import run_scraper
                run_scraper()
            except Exception as e:
                logging.error(f"Manual scrape error: {e}")
        
        # Run in background thread
        thread = threading.Thread(target=run_scrape)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "status": "started",
            "message": "Manual scraping started for all configured sources"
        })
        
    except Exception as e:
        logging.error(f"Error starting manual scrape: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/downloads', methods=['GET'])
def get_downloads():
    """Get list of downloaded files."""
    try:
        from crawlers.file_collector import file_collector
        
        files = file_collector.get_downloaded_files()
        total_size = sum(f['size'] for f in files)
        
        return jsonify({
            'downloads': files,
            'total_size': total_size,
            'total_files': len(files)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/downloads/start', methods=['POST'])
def start_file_collection():
    """Start file collection from specified URLs."""
    try:
        data = request.get_json()
        urls = data.get('urls', [])
        keywords = data.get('keywords', [])
        
        if not urls:
            return jsonify({'error': 'No URLs provided'}), 400
        
        # Start file collection in background
        def run_collection():
            import asyncio
            from crawlers.file_collector import file_collector
            
            async def collect_files():
                results = []
                for url in urls:
                    try:
                        downloaded = await file_collector.scan_and_download(url, keywords)
                        results.extend(downloaded)
                    except Exception as e:
                        logging.error(f"Error collecting from {url}: {e}")
                return results
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(collect_files())
        
        import threading
        thread = threading.Thread(target=run_collection)
        thread.start()
        
        return jsonify({'message': 'File collection started', 'urls': len(urls)})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tor/start', methods=['POST'])
def start_tor():
    """Start Tor service for dark web crawling."""
    try:
        from utils.tor_manager import tor_manager
        
        if tor_manager.start_tor_service():
            return jsonify({'message': 'Tor service started successfully', 'status': 'running'})
        else:
            return jsonify({'error': 'Tor service not available in this environment'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tor/stop', methods=['POST'])
def stop_tor():
    """Stop Tor service."""
    try:
        from utils.tor_manager import tor_manager
        
        tor_manager.stop_tor_service()
        return jsonify({'message': 'Tor service stopped', 'status': 'stopped'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tor/status')
def tor_status():
    """Get Tor service status."""
    try:
        from utils.tor_manager import tor_manager
        
        return jsonify({
            'running': tor_manager.is_running,
            'port': tor_manager.tor_port,
            'control_port': tor_manager.control_port,
            'available': tor_manager.is_running
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/darkweb/crawl', methods=['POST'])
def start_darkweb_crawl():
    """Start dark web crawling."""
    try:
        from utils.tor_manager import tor_manager
        
        if not tor_manager.is_running:
            return jsonify({'error': 'Tor service not running. Start Tor first.'}), 400
        
        data = request.get_json()
        keywords = data.get('keywords', [])
        
        if not keywords:
            return jsonify({'error': 'No keywords provided'}), 400
        
        # Start dark web crawling in background
        def run_darkweb_crawl():
            import asyncio
            from crawlers.darkweb_crawler import run_darkweb_crawler
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(run_darkweb_crawler(keywords))
        
        import threading
        thread = threading.Thread(target=run_darkweb_crawl)
        thread.start()
        
        return jsonify({'message': 'Dark web crawl started', 'keywords': keywords})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api')
def api_index():
    """API root endpoint with documentation."""
    return jsonify({
        "name": "Privacy OSINT Data API",
        "description": "API for accessing privacy-related posts collected from public forums",
        "endpoints": {
            "/api/posts": "Get all collected posts (with optional filtering)",
            "/api/posts/sources": "Get list of available sources",
            "/api/posts/search": "Search posts by keyword",
            "/api/posts/sentiment": "Get posts filtered by sentiment (positive, negative, neutral)",
            "/api/config/keywords": "Get or update privacy keywords for filtering (GET/POST)",
            "/api/config/sources": "Get all configured sources (GET)",
            
            # New endpoints for source management
            "/api/sources": "Get, add, update, or delete data sources with type and risk level (GET/POST/PUT/DELETE)",
            "/api/sources/types": "Get list of source types (forum, news, pastebin, darkweb)",
            "/api/sources/risk-levels": "Get list of risk levels (low, medium, high)",
            
            # New alerts endpoints
            "/api/alerts": "Get or manage keyword-based alerts (GET/POST/PUT/DELETE)",
            "/api/alerts/check": "Manually check for alerts based on current data",
            
            # New logs endpoints
            "/api/logs": "Get scraping logs with optional filtering",
            "/api/logs/errors": "Get only error logs from scraping operations",
            
            # New scheduling endpoints
            "/api/schedule": "Get or update the scraping schedule (GET/POST)",
            "/api/config/sources/reddit": "Get or manage Reddit subreddits (GET/POST)",
            "/api/config/sources/add": "Add a new source (POST)"
        },
        "usage": {
            "filtering": "Use query parameters to filter results, e.g. ?source=Hacker+News&limit=5",
            "search": "Use /api/posts/search?q=YOUR_QUERY to search posts",
            "sentiment": "Use /api/posts/sentiment?sentiment=positive|negative|neutral"
        },
        "search_tools": {
            "/api/search/email": "Search for an email address in public data breaches and forums",
            "/api/search/phone": "Search for a phone number in public databases and listings"
        },
        "homepage_endpoints": {
            "/api/stats": "Get system statistics for the homepage",
            "/api/search": "Search API endpoint for the homepage"
        }
    })

@app.route('/api/search/email', methods=['GET', 'POST'])
def search_email_api():
    """
    Search for an email address in public data breaches and forums.
    
    GET: Use query parameter ?email=user@example.com
    POST: Send JSON with {"email": "user@example.com"}
    """
    # Get email from query params or JSON body
    if request.method == 'GET':
        email = request.args.get('email')
    else:  # POST
        if not request.is_json:
            return jsonify({"error": "Request must be JSON for POST method"}), 400
        email = request.get_json().get('email')
    
    # Validate email parameter
    if not email:
        return jsonify({
            "error": "Missing email parameter", 
            "usage": {
                "GET": "/api/search/email?email=user@example.com",
                "POST": "Send JSON with {'email': 'user@example.com'}"
            }
        }), 400
    
    # Perform the search
    results = search_email(email)
    
    # Add timestamp to results
    results["timestamp"] = datetime.now().isoformat()
    
    return jsonify(results)

@app.route('/api/stats')
def get_stats():
    """Get system statistics for the homepage."""
    try:
        # Load existing data
        existing_data = load_existing_data(OUTPUT_FILE)
        
        # Calculate statistics
        total_posts = len(existing_data)
        
        # Count by source
        sources = {}
        high_risk_count = 0
        recent_incidents = 0
        
        for post in existing_data:
            source = post.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
            
            # Count high risk posts
            if post.get('risk_level', '').lower() == 'high':
                high_risk_count += 1
            
            # Count recent incidents (last 24 hours)
            if post.get('timestamp'):
                try:
                    post_time = datetime.fromisoformat(post['timestamp'].replace('Z', '+00:00'))
                    if (datetime.now() - post_time.replace(tzinfo=None)).days == 0:
                        recent_incidents += 1
                except:
                    pass
        
        return jsonify({
            "total_posts": total_posts,
            "active_sources": len(sources),
            "high_risk": high_risk_count,
            "recent_incidents": recent_incidents,
            "posts_change": 0,  # This would be calculated from previous data
            "sources_change": 0,
            "risk_change": 0,
            "incidents_change": 0,
            "last_updated": datetime.now().isoformat()
        })
    except Exception as e:
        logging.error(f"Error getting stats: {str(e)}")
        return jsonify({
            "total_posts": 0,
            "active_sources": 0,
            "high_risk": 0,
            "recent_incidents": 0,
            "posts_change": 0,
            "sources_change": 0,
            "risk_change": 0,
            "incidents_change": 0,
            "last_updated": datetime.now().isoformat()
        })

@app.route('/api/search')
def search_api():
    """Search API endpoint for the homepage."""
    try:
        query = request.args.get('q', '').strip()
        source_filter = request.args.get('source', '').strip()
        risk_filter = request.args.get('risk_level', '').strip()
        time_filter = request.args.get('time_range', '').strip()
        limit = min(int(request.args.get('limit', 20)), 100)
        
        if not query:
            return jsonify({"error": "Query parameter 'q' is required"}), 400
        
        # Load existing data
        existing_data = load_existing_data(OUTPUT_FILE)
        
        # Filter results
        results = []
        for post in existing_data:
            # Text search
            if query.lower() not in post.get('content', '').lower() and \
               query.lower() not in post.get('title', '').lower():
                continue
            
            # Source filter
            if source_filter and post.get('source', '') != source_filter:
                continue
            
            # Risk filter
            if risk_filter and post.get('risk_level', '').lower() != risk_filter.lower():
                continue
            
            # Time filter
            if time_filter and post.get('timestamp'):
                try:
                    post_time = datetime.fromisoformat(post['timestamp'].replace('Z', '+00:00'))
                    now = datetime.now()
                    
                    if time_filter == '1h' and (now - post_time.replace(tzinfo=None)).total_seconds() > 3600:
                        continue
                    elif time_filter == '24h' and (now - post_time.replace(tzinfo=None)).days > 0:
                        continue
                    elif time_filter == '7d' and (now - post_time.replace(tzinfo=None)).days > 7:
                        continue
                    elif time_filter == '30d' and (now - post_time.replace(tzinfo=None)).days > 30:
                        continue
                except:
                    pass
            
            results.append(post)
        
        # Sort by relevance (timestamp for now)
        results.sort(key=lambda x: (x.get('timestamp') or ''), reverse=True)
        
        # Limit results
        results = results[:limit]
        
        return jsonify({
            "results": results,
            "total": len(results),
            "query": query,
            "filters": {
                "source": source_filter,
                "risk_level": risk_filter,
                "time_range": time_filter
            }
        })
    except Exception as e:
        logging.error(f"Error in search API: {str(e)}")
        return jsonify({"error": "Search failed"}), 500

@app.route('/api/search/phone', methods=['GET', 'POST'])
def search_phone_api():
    """
    Search for a phone number in public databases and listings.
    
    GET: Use query parameter ?phone=+12125551234
    POST: Send JSON with {"phone": "+12125551234"}
    """
    # Get phone from query params or JSON body
    if request.method == 'GET':
        phone = request.args.get('phone')
    else:  # POST
        if not request.is_json:
            return jsonify({"error": "Request must be JSON for POST method"}), 400
        phone = request.get_json().get('phone')
    
    # Validate phone parameter
    if not phone:
        return jsonify({
            "error": "Missing phone parameter", 
            "usage": {
                "GET": "/api/search/phone?phone=+12125551234",
                "POST": "Send JSON with {'phone': '+12125551234'}"
            }
        }), 400
    
    # Perform the search
    results = search_phone(phone)
    
    # Add timestamp to results
    results["timestamp"] = datetime.now().isoformat()
    
    return jsonify(results)

@app.route('/api/search/clear_cache', methods=['POST'])
def clear_search_cache():
    """Clear the search cache for both email and phone searches."""
    email_result = clear_email_cache()
    phone_result = clear_phone_cache()
    
    return jsonify({
        "success": True,
        "email_cache": email_result,
        "phone_cache": phone_result
    })

@app.route('/api/posts')
def get_posts():
    """Get all posts with optional filtering."""
    # Load the data
    posts = load_existing_data(OUTPUT_FILE)
    
    # Apply filtering based on query parameters
    source = request.args.get('source')
    limit = request.args.get('limit')
    
    if source:
        posts = [p for p in posts if p.get('source') == source]
    
    # Sort by timestamp (newest first)
    posts.sort(key=lambda x: (x.get('timestamp') or ''), reverse=True)
    
    # Apply limit if specified
    if limit and limit.isdigit():
        posts = posts[:int(limit)]
    
    # Hide sensitive source internals
    for p in posts:
        p.pop('internal_source', None)
        p.pop('credentials_used', None)
    
    # Enrich posts with NLP analysis
    enriched_posts = [enrich_post_with_nlp(post) for post in posts]
    
    return jsonify(enriched_posts)

@app.route('/api/cve', methods=['GET'])
def get_cve_feed():
    from models import CVEItem
    try:
        limit = min(int(request.args.get('limit', 50)), 200)
        q = CVEItem.query.order_by(CVEItem.published_at.desc().nullslast(), CVEItem.created_at.desc())
        items = q.limit(limit).all()
        return jsonify([
            {
                'id': i.id,
                'cve_id': i.cve_id,
                'title': i.title,
                'description': i.description,
                'severity': i.severity,
                'cvss': i.cvss,
                'affected_products': i.affected_products,
                'tags': i.tags,
                'published_at': i.published_at.isoformat() if i.published_at else None,
                'created_at': i.created_at.isoformat(),
                'link': i.source_url,
            } for i in items
        ])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cve', methods=['POST'])
def add_cve():
    from models import CVEItem
    try:
        data = request.get_json() or {}
        
        # Validate required fields
        if not data.get('cve_id'):
            return jsonify({'error': 'CVE ID is required'}), 400
        
        # Check if CVE already exists
        existing = CVEItem.query.filter_by(cve_id=data['cve_id']).first()
        if existing:
            return jsonify({'error': f'CVE {data["cve_id"]} already exists'}), 400
        
        # Create new CVE
        cve = CVEItem(
            cve_id=data['cve_id'],
            title=data.get('title'),
            description=data.get('description'),
            severity=data.get('severity'),
            cvss=float(data['cvss']) if data.get('cvss') else None,
            affected_products=data.get('affected_products'),
            tags=data.get('tags'),
            source_url=data.get('source_url'),
            published_at=datetime.fromisoformat(data['published_at']) if data.get('published_at') else None
        )
        
        db.session.add(cve)
        db.session.commit()
        
        return jsonify({'success': True, 'id': cve.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/news', methods=['GET'])
def get_news_feed():
    from models import NewsItem
    try:
        limit = min(int(request.args.get('limit', 50)), 200)
        risk = request.args.get('risk')
        q = NewsItem.query
        if risk:
            q = q.filter_by(risk_level=risk)
        q = q.order_by(NewsItem.published_at.desc().nullslast(), NewsItem.created_at.desc())
        items = q.limit(limit).all()
        return jsonify([
            {
                'id': i.id,
                'title': i.title,
                'summary': i.summary,
                'risk_level': i.risk_level,
                'tags': i.tags,
                'url': i.url,
                'source_name': i.source_name,
                'published_at': i.published_at.isoformat() if i.published_at else None,
                'created_at': i.created_at.isoformat(),
            } for i in items
        ])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/news', methods=['POST'])
def add_news():
    from models import NewsItem
    try:
        data = request.get_json() or {}
        
        # Validate required fields
        if not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400
        
        # Create new news item
        news = NewsItem(
            title=data['title'],
            url=data.get('url'),
            source_name=data.get('source_name'),
            summary=data.get('summary'),
            tags=data.get('tags'),
            risk_level=data.get('risk_level'),
            published_at=datetime.fromisoformat(data['published_at']) if data.get('published_at') else None
        )
        
        db.session.add(news)
        db.session.commit()
        
        return jsonify({'success': True, 'id': news.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/tools', methods=['GET'])
def get_tools_feed():
    from models import ToolItem
    try:
        limit = min(int(request.args.get('limit', 50)), 200)
        q = ToolItem.query.order_by(ToolItem.created_at.desc())
        items = q.limit(limit).all()
        return jsonify([
            {
                'id': i.id,
                'name': i.name,
                'description': i.description,
                'risk_level': i.risk_level,
                'url': i.url,
                'source_name': i.source_name,
                'file_path': i.file_path,
                'is_private': i.is_private,
                'created_at': i.created_at.isoformat(),
            } for i in items
        ])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tools', methods=['POST'])
def add_tool():
    from models import ToolItem
    try:
        data = request.get_json() or {}
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Tool name is required'}), 400
        
        # Create new tool
        tool = ToolItem(
            name=data['name'],
            url=data.get('url'),
            source_name=data.get('source_name'),
            description=data.get('description'),
            risk_level=data.get('risk_level'),
            file_path=data.get('file_path'),
            is_private=data.get('is_private', True)
        )
        
        db.session.add(tool)
        db.session.commit()
        
        return jsonify({'success': True, 'id': tool.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/tools/<int:tool_id>/download')
def download_tool(tool_id):
    from models import ToolItem
    try:
        tool = ToolItem.query.get(tool_id)
        if not tool:
            return jsonify({'error': 'Tool not found'}), 404
        
        if not tool.file_path or not os.path.exists(tool.file_path):
            return jsonify({'error': 'Tool file not found'}), 404
        
        return send_file(tool.file_path, as_attachment=True, download_name=f"{tool.name}.zip")
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/config', methods=['GET', 'POST'])
def global_config():
    try:
        if request.method == 'GET':
            cfg = GlobalConfig.query.get(1)
            if not cfg:
                cfg = GlobalConfig(id=1, keywords='', settings_json='{}')
                db.session.add(cfg)
                db.session.commit()
            return jsonify({
                'keywords': cfg.keywords or '',
                'settings': cfg.settings_json or '{}',
                'updated_at': cfg.updated_at.isoformat() if cfg.updated_at else None
            })
        else:
            data = request.get_json() or {}
            cfg = GlobalConfig.query.get(1)
            if not cfg:
                cfg = GlobalConfig(id=1)
                db.session.add(cfg)
            cfg.keywords = data.get('keywords', cfg.keywords)
            cfg.settings_json = data.get('settings', cfg.settings_json)
            db.session.commit()
            return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/breaches', methods=['GET'])
def get_breaches():
    """Get all breaches with optional filtering."""
    from models import BreachItem
    try:
        limit = min(int(request.args.get('limit', 50)), 200)
        q = BreachItem.query.order_by(BreachItem.created_at.desc())
        items = q.limit(limit).all()
        return jsonify([
            {
                'id': i.id,
                'name': i.name,
                'description': i.description,
                'affected_organizations': i.affected_organizations,
                'data_types_exposed': i.data_types_exposed,
                'records_affected': i.records_affected,
                'discovery_date': i.discovery_date.isoformat() if i.discovery_date else None,
                'disclosure_date': i.disclosure_date.isoformat() if i.disclosure_date else None,
                'source_url': i.source_url,
                'created_at': i.created_at.isoformat(),
            } for i in items
        ])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/breaches', methods=['POST'])
def add_breach():
    """Add a new breach entry."""
    from models import BreachItem
    try:
        data = request.get_json() or {}
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Breach name is required'}), 400
        
        # Create new breach
        breach = BreachItem(
            name=data['name'],
            description=data.get('description'),
            affected_organizations=data.get('affected_organizations'),
            data_types_exposed=data.get('data_types_exposed'),
            records_affected=data.get('records_affected'),
            discovery_date=datetime.fromisoformat(data['discovery_date']) if data.get('discovery_date') else None,
            disclosure_date=datetime.fromisoformat(data['disclosure_date']) if data.get('disclosure_date') else None,
            source_url=data.get('source_url')
        )
        
        db.session.add(breach)
        db.session.commit()
        
        return jsonify({'success': True, 'id': breach.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/leaks', methods=['GET'])
def get_leaks():
    """Get all leaks with optional filtering."""
    from models import LeakItem
    try:
        limit = min(int(request.args.get('limit', 50)), 200)
        q = LeakItem.query.order_by(LeakItem.created_at.desc())
        items = q.limit(limit).all()
        return jsonify([
            {
                'id': i.id,
                'source': i.source,
                'data_content': i.data_content,
                'verification_status': i.verification_status,
                'associated_breach_id': i.associated_breach_id,
                'created_at': i.created_at.isoformat(),
            } for i in items
        ])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leaks', methods=['POST'])
def add_leak():
    """Add a new leak entry."""
    from models import LeakItem
    try:
        data = request.get_json() or {}
        
        # Validate required fields
        if not data.get('source'):
            return jsonify({'error': 'Leak source is required'}), 400
        
        # Create new leak
        leak = LeakItem(
            source=data['source'],
            data_content=data.get('data_content'),
            verification_status=data.get('verification_status', 'unverified'),
            associated_breach_id=data.get('associated_breach_id')
        )
        
        db.session.add(leak)
        db.session.commit()
        
        return jsonify({'success': True, 'id': leak.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/uploads', methods=['POST'])
def admin_upload():
    from models import UploadItem
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        f = request.files['file']
        os.makedirs('uploads', exist_ok=True)
        safe_name = f.filename
        storage_path = os.path.join('uploads', safe_name)
        f.save(storage_path)
        size_bytes = os.path.getsize(storage_path)
        content_type = f.mimetype
        risk = request.form.get('risk_level', 'low')
        is_public = request.form.get('is_public', 'false').lower() == 'true'
        item = UploadItem(
            filename=safe_name,
            content_type=content_type,
            size_bytes=size_bytes,
            risk_level=risk,
            is_public=is_public,
            uploader_id=None,
            storage_path=storage_path,
            upload_metadata=None,
        )
        db.session.add(item)
        db.session.commit()
        return jsonify({'success': True, 'id': item.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/posts/sources')
def get_sources():
    """Get list of available sources."""
    posts = load_existing_data(OUTPUT_FILE)
    sources = sorted(list(set(post.get('source') for post in posts)))
    return jsonify(sources)

@app.route('/api/posts/search')
def search_posts():
    """Search posts by keyword."""
    query = request.args.get('q', '').lower()
    
    if not query:
        return jsonify({"error": "No search query provided. Use ?q=QUERY"}), 400
    
    posts = load_existing_data(OUTPUT_FILE)
    
    # Search in title and summary
    results = []
    for post in posts:
        title = post.get('title', '').lower()
        summary = post.get('summary', '').lower()
        
        if query in title or query in summary:
            results.append(enrich_post_with_nlp(post))
    
    # Sort by timestamp (newest first)
    results.sort(key=lambda x: (x.get('timestamp') or ''), reverse=True)
    
    return jsonify(results)

@app.route('/api/posts/sentiment')
def get_posts_by_sentiment():
    """Get posts filtered by sentiment."""
    sentiment = request.args.get('sentiment', '').lower()
    
    if sentiment not in ['positive', 'negative', 'neutral']:
        return jsonify({
            "error": "Invalid sentiment. Use 'positive', 'negative', or 'neutral'."
        }), 400
    
    posts = load_existing_data(OUTPUT_FILE)
    
    # Enrich all posts with NLP data
    enriched_posts = [enrich_post_with_nlp(post) for post in posts]
    
    # Filter by sentiment
    filtered = [
        post for post in enriched_posts 
        if post.get('sentiment', {}).get('assessment') == sentiment
    ]
    
    # Sort by sentiment strength (polarity absolute value)
    if sentiment in ['positive', 'negative']:
        filtered.sort(
            key=lambda x: abs(x.get('sentiment', {}).get('polarity', 0)), 
            reverse=True
        )
    
    return jsonify(filtered)
    
@app.route('/api/config/keywords', methods=['GET'])
def get_keywords():
    """Get the list of privacy keywords used for filtering."""
    return jsonify(PRIVACY_KEYWORDS)
    
@app.route('/api/config/keywords', methods=['POST'])
def update_keywords():
    """Update the list of privacy keywords used for filtering."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
        
    data = request.get_json()
    keywords = data.get('keywords')
    
    if not keywords or not isinstance(keywords, list):
        return jsonify({"error": "Invalid keywords format. Must be a non-empty list."}), 400
        
    # Update the keywords in the global config
    global PRIVACY_KEYWORDS
    PRIVACY_KEYWORDS.clear()
    PRIVACY_KEYWORDS.extend(keywords)
    
    # Save the updated keywords to a file to persist across restarts
    try:
        config_file = "keywords_config.json"
        with open(config_file, 'w') as f:
            json.dump({"keywords": PRIVACY_KEYWORDS}, f, indent=2)
        return jsonify({"success": True, "keywords": PRIVACY_KEYWORDS})
    except Exception as e:
        logging.error(f"Error saving keywords: {e}")
        return jsonify({"error": f"Failed to save keywords: {str(e)}"}), 500
        
@app.route('/api/config/sources', methods=['GET'])
def get_legacy_configured_sources():
    """Get all configured sources for scraping."""
    # Load built-in sources
    configured_sources = {
        "default_sources": {
            k: v for k, v in SOURCES.items()
        }
    }
    
    # Load Reddit subreddits
    configured_sources["reddit_subreddits"] = get_reddit_subreddits()
    
    # Load any custom sources
    if os.path.exists(SOURCES_CONFIG_FILE):
        try:
            with open(SOURCES_CONFIG_FILE, 'r') as f:
                sources_config = json.load(f)
                if "custom_sources" in sources_config:
                    configured_sources["custom_sources"] = sources_config["custom_sources"]
        except Exception as e:
            logging.error(f"Error loading sources config: {e}")
    
    return jsonify(configured_sources)

def get_reddit_subreddits():
    """Get the current list of Reddit subreddits being scraped."""
    # Load from config file if it exists
    if os.path.exists(SOURCES_CONFIG_FILE):
        try:
            with open(SOURCES_CONFIG_FILE, 'r') as f:
                sources_config = json.load(f)
                if "reddit_subreddits" in sources_config:
                    return sources_config["reddit_subreddits"]
        except Exception as e:
            logging.error(f"Error loading Reddit subreddits: {e}")
    
    # Return default subreddits if no custom config
    return REDDIT_SUBREDDITS

@app.route('/api/config/sources/reddit', methods=['GET'])
def get_reddit_sources():
    """Get the current list of Reddit subreddits being scraped."""
    return jsonify(get_reddit_subreddits())

@app.route('/api/config/sources/reddit', methods=['POST'])
def update_reddit_sources():
    """Update the list of Reddit subreddits to scrape."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
        
    data = request.get_json()
    subreddits = data.get('subreddits')
    
    if not subreddits or not isinstance(subreddits, list):
        return jsonify({"error": "Invalid subreddits format. Must be a non-empty list."}), 400
    
    # Validate subreddit names
    for subreddit in subreddits:
        if not isinstance(subreddit, str) or not subreddit.strip():
            return jsonify({"error": f"Invalid subreddit name: {subreddit}"}), 400
    
    # Clean subreddit names
    cleaned_subreddits = [s.strip() for s in subreddits if s.strip()]
    
    # Save to config file
    try:
        # Load existing config or create new one
        sources_config = {}
        if os.path.exists(SOURCES_CONFIG_FILE):
            try:
                with open(SOURCES_CONFIG_FILE, 'r') as f:
                    sources_config = json.load(f)
            except:
                pass
        
        # Update subreddits
        sources_config["reddit_subreddits"] = cleaned_subreddits
        
        # Save back to file
        with open(SOURCES_CONFIG_FILE, 'w') as f:
            json.dump(sources_config, f, indent=2)
            
        return jsonify({
            "success": True, 
            "reddit_subreddits": cleaned_subreddits
        })
    except Exception as e:
        logging.error(f"Error saving Reddit subreddits: {e}")
        return jsonify({"error": f"Failed to save Reddit subreddits: {str(e)}"}), 500

@app.route('/api/config/sources/add', methods=['POST'])
def add_custom_source():
    """Add a new custom source for scraping."""
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
        
    data = request.get_json()
    source_id = data.get('id')
    source_name = data.get('name')
    source_url = data.get('url')
    source_type = data.get('type')
    
    # Validate required fields
    if not all([source_id, source_name, source_url, source_type]):
        return jsonify({
            "error": "Missing required fields. Please provide id, name, url, and type."
        }), 400
    
    # Validate source type
    allowed_types = ['reddit', 'custom']
    if source_type not in allowed_types:
        return jsonify({
            "error": f"Invalid source type. Must be one of: {', '.join(allowed_types)}"
        }), 400
    
    # Handle Reddit type separately
    if source_type == 'reddit':
        # Extract subreddit name from source_id
        subreddit = source_id.strip()
        if not subreddit:
            return jsonify({"error": "Invalid subreddit name"}), 400
            
        # Add to Reddit subreddits
        subreddits = get_reddit_subreddits()
        if subreddit not in subreddits:
            subreddits.append(subreddit)
            
            # Save to config file
            try:
                # Load existing config or create new one
                sources_config = {}
                if os.path.exists(SOURCES_CONFIG_FILE):
                    try:
                        with open(SOURCES_CONFIG_FILE, 'r') as f:
                            sources_config = json.load(f)
                    except:
                        pass
                
                # Update subreddits
                sources_config["reddit_subreddits"] = subreddits
                
                # Save back to file
                with open(SOURCES_CONFIG_FILE, 'w') as f:
                    json.dump(sources_config, f, indent=2)
                    
                return jsonify({
                    "success": True, 
                    "message": f"Added subreddit: r/{subreddit}",
                    "reddit_subreddits": subreddits
                })
            except Exception as e:
                logging.error(f"Error adding Reddit subreddit: {e}")
                return jsonify({"error": f"Failed to add Reddit subreddit: {str(e)}"}), 500
        else:
            return jsonify({
                "message": f"Subreddit r/{subreddit} is already in the list",
                "reddit_subreddits": subreddits
            })
    
    # For custom sources
    elif source_type == 'custom':
        try:
            # Load existing config or create new one
            sources_config = {}
            if os.path.exists(SOURCES_CONFIG_FILE):
                try:
                    with open(SOURCES_CONFIG_FILE, 'r') as f:
                        sources_config = json.load(f)
                except:
                    pass
            
            # Initialize custom_sources if not present
            if "custom_sources" not in sources_config:
                sources_config["custom_sources"] = {}
            
            # Add the new source
            sources_config["custom_sources"][source_id] = {
                "name": source_name,
                "url": source_url,
                "type": source_type
            }
            
            # Save back to file
            with open(SOURCES_CONFIG_FILE, 'w') as f:
                json.dump(sources_config, f, indent=2)
                
            return jsonify({
                "success": True, 
                "message": f"Added custom source: {source_name}",
                "custom_sources": sources_config["custom_sources"]
            })
        except Exception as e:
            logging.error(f"Error adding custom source: {e}")
            return jsonify({"error": f"Failed to add custom source: {str(e)}"}), 500

@app.route('/api/config/api_keys', methods=['GET', 'POST', 'PUT'])
def manage_api_keys():
    """Get or add API keys."""
    if request.method == 'GET':
        @with_retry
        def get_api_keys():
            keys = ApiKey.query.all()
            services = [
                {
                    "service": k.service,
                    "key_preview": f"{k.key[:4]}...{k.key[-4:]}" if len(k.key) > 8 else "***",
                    "updated_at": k.updated_at.isoformat() if k.updated_at else None,
                    "created_at": k.created_at.isoformat() if k.created_at else None
                }
                for k in keys
            ]
            return jsonify({
                "success": True,
                "services": services
            })
            
        try:
            return get_api_keys()
        except Exception as e:
            logging.error(f"Error fetching API keys: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500
    
    elif request.method == 'POST':
        @with_retry
        def save_api_key():
            data = request.get_json()
            
            if not data or 'service' not in data or 'key' not in data:
                return jsonify({
                    "success": False,
                    "error": "Missing required fields: service and key"
                }), 400
            
            service = data['service'].strip().lower()
            key = data['key'].strip()
            
            if not service or not key:
                return jsonify({
                    "success": False,
                    "error": "Service name and key cannot be empty"
                }), 400
            
            # Check if service already exists
            existing_key = ApiKey.query.filter_by(service=service).first()
            
            if existing_key:
                # Update existing key
                existing_key.key = key
                existing_key.updated_at = datetime.utcnow()
                db.session.commit()
                return jsonify({
                    "success": True,
                    "message": f"API key for {service} updated successfully"
                })
            else:
                # Create new key
                new_key = ApiKey(service=service, key=key)
                db.session.add(new_key)
                db.session.commit()
                return jsonify({
                    "success": True,
                    "message": f"API key for {service} added successfully"
                })
        
        try:
            return save_api_key()
        except Exception as e:
            logging.error(f"Error saving API key: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

    elif request.method == 'PUT':
        @with_retry
        def update_api_key():
            data = request.get_json()
            
            if not data or 'service' not in data or 'key' not in data:
                return jsonify({
                    "success": False,
                    "error": "Missing required fields: service and key"
                }), 400
            
            service = data['service'].strip().lower()
            key = data['key'].strip()
            
            if not service or not key:
                return jsonify({
                    "success": False,
                    "error": "Service name and key cannot be empty"
                }), 400
            
            # Check if service exists
            existing_key = ApiKey.query.filter_by(service=service).first()
            
            if not existing_key:
                return jsonify({
                    "success": False,
                    "error": f"API key for {service} not found"
                }), 404
            
            # Update the key
            existing_key.key = key
            existing_key.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                "success": True,
                "message": f"API key for {service} updated successfully"
            })
        
        try:
            return update_api_key()
        except Exception as e:
            logging.error(f"Error updating API key: {e}")
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500

@app.route('/api/config/integrated_apis', methods=['GET'])
def get_integrated_apis():
    """Get the list of all integrated APIs."""
    from models import GlobalConfig
    try:
        global_config = GlobalConfig.query.get(1)
        if not global_config:
            return jsonify({"integrated_apis": {}})
        
        settings = json.loads(global_config.settings_json or '{}')
        integrated_apis = settings.get('integrated_apis', {})
        
        return jsonify({
            "success": True,
            "integrated_apis": integrated_apis,
            "total": len(integrated_apis)
        })
        
    except Exception as e:
        logging.error(f"Error fetching integrated APIs: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "integrated_apis": {}
        }), 500

@app.route('/api/config/integrate_api', methods=['POST'])
def integrate_api():
    """Integrate a new API dynamically into the backend pipelines."""
    from models import GlobalConfig
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['service', 'key', 'api_type', 'endpoint_url']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        service = data['service'].strip().lower()
        key = data['key'].strip()
        api_type = data['api_type'].strip().lower()
        endpoint_url = data['endpoint_url'].strip()
        
        # Validate API type
        valid_api_types = ['breach', 'leak', 'cve', 'news', 'tool', 'custom']
        if api_type not in valid_api_types:
            return jsonify({
                "error": f"Invalid API type. Must be one of: {', '.join(valid_api_types)}"
            }), 400
        
        # Save the API key
        existing_key = ApiKey.query.filter_by(service=service).first()
        if existing_key:
            existing_key.key = key
            existing_key.updated_at = datetime.utcnow()
        else:
            new_key = ApiKey(service=service, key=key)
            db.session.add(new_key)
        
        db.session.commit()
        
        # Create API configuration for dynamic integration
        api_config = {
            'service': service,
            'api_type': api_type,
            'endpoint_url': endpoint_url,
            'enabled': data.get('enabled', True),
            'refresh_interval': data.get('refresh_interval', 60),  # minutes
            'priority': data.get('priority', 'medium'),
            'metadata': data.get('metadata', {})
        }
        
        # Save API configuration to global config
        global_config = GlobalConfig.query.get(1)
        if not global_config:
            global_config = GlobalConfig(id=1, keywords='', settings_json='{}')
            db.session.add(global_config)
        
        # Parse existing settings
        settings = json.loads(global_config.settings_json or '{}')
        if 'integrated_apis' not in settings:
            settings['integrated_apis'] = {}
        
        # Add or update the API configuration
        settings['integrated_apis'][service] = api_config
        global_config.settings_json = json.dumps(settings)
        global_config.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        # Log the integration
        logging.info(f"API integration successful: {service} ({api_type})")
        
        return jsonify({
            "success": True,
            "message": f"API {service} integrated successfully",
            "config": api_config
        })
        
    except Exception as e:
        logging.error(f"Error integrating API: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/config/integrate_api/<service>', methods=['DELETE'])
def remove_integrated_api(service):
    """Remove an integrated API from the system."""
    from models import GlobalConfig
    try:
        global_config = GlobalConfig.query.get(1)
        if not global_config:
            return jsonify({"error": "Global configuration not found"}), 404
        
        settings = json.loads(global_config.settings_json or '{}')
        integrated_apis = settings.get('integrated_apis', {})
        
        if service not in integrated_apis:
            return jsonify({"error": f"API {service} not found in integrated APIs"}), 404
        
        # Remove the API from integrated list
        del integrated_apis[service]
        settings['integrated_apis'] = integrated_apis
        global_config.settings_json = json.dumps(settings)
        global_config.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        logging.info(f"API removed from integration: {service}")
        
        return jsonify({
            "success": True,
            "message": f"API {service} removed from integration successfully"
        })
        
    except Exception as e:
        logging.error(f"Error removing integrated API: {e}")
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/config/api_keys/<service>', methods=['DELETE'])
def delete_api_key(service):
    """Delete an API key by service name."""
    @with_retry
    def delete_key():
        key = ApiKey.query.filter_by(service=service).first()
        
        if not key:
            return jsonify({
                "success": False,
                "error": f"API key for {service} not found"
            }), 404
        
        db.session.delete(key)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"API key for {service} deleted successfully"
        })
    
    try:
        return delete_key()
    except Exception as e:
        logging.error(f"Error deleting API key: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/tools/clear_cache', methods=['POST'])
def clear_all_search_cache():
    """Clear the search cache for both email and phone searches."""
    try:
        email_result = clear_email_cache()
        phone_result = clear_phone_cache()
        
        return jsonify({
            "success": True,
            "email_cache": email_result["message"],
            "phone_cache": phone_result["message"]
        })
    except Exception as e:
        logging.error(f"Error clearing search cache: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# New endpoints for source management with type and risk level

SOURCE_TYPES = ["forum", "news", "pastebin", "darkweb"]
RISK_LEVELS = ["low", "medium", "high"]

@app.route('/api/sources/types', methods=['GET'])
def get_source_types():
    """Get list of source types."""
    return jsonify(SOURCE_TYPES)

@app.route('/api/sources/risk-levels', methods=['GET'])
def get_risk_levels():
    """Get list of risk levels."""
    return jsonify(RISK_LEVELS)

@app.route('/api/sources', methods=['GET'])
def get_db_sources():
    """Get all sources from database with type and risk level information."""
    try:
        sources = Source.query.all()
        return jsonify([{
            "id": source.id,
            "name": source.name,
            "url": source.url,
            "source_type": source.source_type,
            "risk_level": source.risk_level,
            "enabled": source.enabled,
            "scrape_interval": source.scrape_interval,
            "created_at": source.created_at.isoformat() if source.created_at else None,
            "updated_at": source.updated_at.isoformat() if source.updated_at else None
        } for source in sources])
    except Exception as e:
        logging.error(f"Error fetching sources: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/config/sources/db', methods=['GET'])
def get_sources_for_dashboard():
    """Get all configured sources for the sources management interface."""
    try:
        # Use a more efficient query with direct column selection
        sources = db.session.query(Source).options(
            db.defer(Source.created_at),
            db.defer(Source.updated_at)
        ).all()
        
        sources_data = [{
            "id": source.id,
            "name": source.name,
            "url": source.url,
            "source_type": source.source_type,
            "risk_level": source.risk_level,
            "enabled": source.enabled,
            "scrape_interval": source.scrape_interval,
            "created_at": None,
            "updated_at": None
        } for source in sources]
        
        response = jsonify({
            "sources": sources_data,
            "total": len(sources_data)
        })
        response.headers['Content-Type'] = 'application/json'
        return response
    except Exception as e:
        logging.error(f"Error fetching configured sources: {e}")
        error_response = jsonify({"error": str(e), "sources": [], "total": 0})
        error_response.headers['Content-Type'] = 'application/json'
        return error_response, 500

@app.route('/api/sources', methods=['POST'])
def add_db_source():
    """Add a new source with type and risk level."""
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'url', 'source_type', 'risk_level']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Validate source type and risk level
        if data['source_type'] not in SOURCE_TYPES:
            return jsonify({"error": f"Invalid source type. Must be one of: {', '.join(SOURCE_TYPES)}"}), 400
        
        if data['risk_level'] not in RISK_LEVELS:
            return jsonify({"error": f"Invalid risk level. Must be one of: {', '.join(RISK_LEVELS)}"}), 400
        
        # Check if source with the same name already exists
        existing_source = Source.query.filter_by(name=data['name']).first()
        if existing_source:
            return jsonify({"error": f"Source with name '{data['name']}' already exists"}), 400
        
        # Create new source
        new_source = Source(
            name=data['name'],
            url=data['url'],
            source_type=data['source_type'],
            risk_level=data['risk_level'],
            enabled=data.get('enabled', True),
            scrape_interval=data.get('scrape_interval', 60)
        )
        
        db.session.add(new_source)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Source '{data['name']}' added successfully",
            "source": {
                "id": new_source.id,
                "name": new_source.name,
                "url": new_source.url,
                "source_type": new_source.source_type,
                "risk_level": new_source.risk_level,
                "enabled": new_source.enabled,
                "scrape_interval": new_source.scrape_interval,
                "created_at": new_source.created_at.isoformat() if new_source.created_at else None
            }
        })
    except Exception as e:
        logging.error(f"Error adding source: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/sources/<int:source_id>', methods=['PUT'])
def update_source(source_id):
    """Update an existing source."""
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json()
        source = Source.query.get(source_id)
        
        if not source:
            return jsonify({"error": f"Source with ID {source_id} not found"}), 404
        
        # Update fields if provided
        if 'name' in data and data['name']:
            # Check if another source with this name already exists
            existing = Source.query.filter_by(name=data['name']).first()
            if existing and existing.id != source_id:
                return jsonify({"error": f"Another source with name '{data['name']}' already exists"}), 400
            source.name = data['name']
            
        if 'url' in data and data['url']:
            source.url = data['url']
            
        if 'source_type' in data and data['source_type']:
            if data['source_type'] not in SOURCE_TYPES:
                return jsonify({"error": f"Invalid source type. Must be one of: {', '.join(SOURCE_TYPES)}"}), 400
            source.source_type = data['source_type']
            
        if 'risk_level' in data and data['risk_level']:
            if data['risk_level'] not in RISK_LEVELS:
                return jsonify({"error": f"Invalid risk level. Must be one of: {', '.join(RISK_LEVELS)}"}), 400
            source.risk_level = data['risk_level']
            
        if 'enabled' in data:
            source.enabled = bool(data['enabled'])
            
        if 'scrape_interval' in data and isinstance(data['scrape_interval'], (int, float)):
            source.scrape_interval = int(data['scrape_interval'])
        
        source.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Source '{source.name}' updated successfully",
            "source": {
                "id": source.id,
                "name": source.name,
                "url": source.url,
                "source_type": source.source_type,
                "risk_level": source.risk_level,
                "enabled": source.enabled,
                "scrape_interval": source.scrape_interval,
                "updated_at": source.updated_at.isoformat() if source.updated_at else None
            }
        })
    except Exception as e:
        logging.error(f"Error updating source: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/sources/<int:source_id>', methods=['DELETE'])
def delete_source(source_id):
    """Delete a source."""
    try:
        source = Source.query.get(source_id)
        
        if not source:
            return jsonify({"error": f"Source with ID {source_id} not found"}), 404
        
        source_name = source.name
        db.session.delete(source)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Source '{source_name}' deleted successfully"
        })
    except Exception as e:
        logging.error(f"Error deleting source: {e}")
        return jsonify({"error": str(e)}), 500

# New endpoints for keyword alerts

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get all keyword alerts."""
    @with_retry
    def fetch_alerts():
        alerts = KeywordAlert.query.all()
        return jsonify([{
            "id": alert.id,
            "keyword": alert.keyword,
            "priority": alert.priority,
            "enabled": alert.enabled,
            "created_at": alert.created_at.isoformat() if alert.created_at else None,
            "last_triggered": alert.last_triggered.isoformat() if alert.last_triggered else None
        } for alert in alerts])
    
    try:
        return fetch_alerts()
    except Exception as e:
        logging.error(f"Error fetching alerts: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/alerts', methods=['POST'])
def add_alert():
    """Add a new keyword alert."""
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json() or {}
        
        # Validate required fields
        if 'keyword' not in data or not data['keyword']:
            return jsonify({"error": "Missing required field: keyword"}), 400
            
        # Validate priority
        priority = data.get('priority', 'medium')
        if priority not in ['low', 'medium', 'high']:
            return jsonify({"error": "Invalid priority. Must be one of: low, medium, high"}), 400
        
        # Check if alert for this keyword already exists
        existing_alert = KeywordAlert.query.filter_by(keyword=data['keyword']).first()
        if existing_alert:
            return jsonify({"error": f"Alert for keyword '{data['keyword']}' already exists"}), 400
        
        # Create new alert
        new_alert = KeywordAlert(
            keyword=data['keyword'],
            priority=priority,
            enabled=data.get('enabled', True)
        )
        
        db.session.add(new_alert)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Alert for keyword '{data['keyword']}' added successfully",
            "alert": {
                "id": new_alert.id,
                "keyword": new_alert.keyword,
                "priority": new_alert.priority,
                "enabled": new_alert.enabled,
                "created_at": new_alert.created_at.isoformat() if new_alert.created_at else None
            }
        })
    except Exception as e:
        logging.error(f"Error adding alert: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/alerts/<int:alert_id>', methods=['PUT'])
def update_alert(alert_id):
    """Update an existing alert."""
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.get_json() or {}
        alert = KeywordAlert.query.get(alert_id)
        
        if not alert:
            return jsonify({"error": f"Alert with ID {alert_id} not found"}), 404
        
        # Update fields if provided
        if 'keyword' in data and data['keyword']:
            # Check if another alert with this keyword already exists
            existing = KeywordAlert.query.filter_by(keyword=data['keyword']).first()
            if existing and existing.id != alert_id:
                return jsonify({"error": f"Another alert for keyword '{data['keyword']}' already exists"}), 400
            alert.keyword = data['keyword']
            
        if 'priority' in data and data['priority']:
            if data['priority'] not in ['low', 'medium', 'high']:
                return jsonify({"error": "Invalid priority. Must be one of: low, medium, high"}), 400
            alert.priority = data['priority']
            
        if 'enabled' in data:
            alert.enabled = bool(data['enabled'])
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Alert for keyword '{alert.keyword}' updated successfully",
            "alert": {
                "id": alert.id,
                "keyword": alert.keyword,
                "priority": alert.priority,
                "enabled": alert.enabled,
                "updated_at": datetime.utcnow().isoformat()
            }
        })
    except Exception as e:
        logging.error(f"Error updating alert: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    """Delete a keyword alert."""
    try:
        alert = KeywordAlert.query.get(alert_id)
        
        if not alert:
            return jsonify({"error": f"Alert with ID {alert_id} not found"}), 404
        
        keyword = alert.keyword
        db.session.delete(alert)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Alert for keyword '{keyword}' deleted successfully"
        })
    except Exception as e:
        logging.error(f"Error deleting alert: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/alerts/check', methods=['POST'])
def check_alerts():
    """Check for alerts based on current data."""
    try:
        posts = load_existing_data(OUTPUT_FILE)
        alerts = KeywordAlert.query.filter_by(enabled=True).all()
        
        if not alerts:
            return jsonify({
                "success": True,
                "message": "No active alerts configured",
                "triggered": []
            })
            
        
        # Dictionary to hold triggered alerts
        triggered = {}
        
        # Check each post against each alert
        for post in posts:
            post_text = (post.get('title', '') + ' ' + post.get('summary', '')).lower()
            post_url = post.get('url', '')
            
            for alert in alerts:
                if alert.keyword.lower() in post_text:
                    # If this alert hasn't been triggered yet, initialize it
                    if alert.id not in triggered:
                        triggered[alert.id] = {
                            "alert": {
                                "id": alert.id,
                                "keyword": alert.keyword,
                                "priority": alert.priority
                            },
                            "matching_posts": []
                        }
                    
                    # Add this post to the triggered alert
                    triggered[alert.id]["matching_posts"].append({
                        "title": post.get('title', ''),
                        "source": post.get('source', ''),
                        "url": post_url,
                        "timestamp": post.get('timestamp', '')
                    })
                    
                    # Update the alert's last_triggered timestamp in the database
                    alert.last_triggered = datetime.utcnow()
        
        # Commit the database updates for last_triggered timestamps
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Found {len(triggered)} triggered alerts",
            "triggered": list(triggered.values())
        })
    except Exception as e:
        logging.error(f"Error checking alerts: {e}")
        return jsonify({"error": str(e)}), 500

# New endpoints for scraping logs

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get scraping logs with optional filtering."""
    try:
        # Get query parameters
        source = request.args.get('source')
        status = request.args.get('status')
        limit_str = request.args.get('limit')
        
        # Build the query
        query = ScrapeLog.query
        
        if source:
            query = query.filter_by(source_name=source)
            
        if status and status in ['success', 'error']:
            query = query.filter_by(status=status)
        
        # Order by timestamp descending (newest first)
        query = query.order_by(ScrapeLog.timestamp.desc())
        
        # Apply limit if specified
        if limit_str and limit_str.isdigit():
            query = query.limit(int(limit_str))
        else:
            # Default limit
            query = query.limit(50)
        
        logs = query.all()
        
        return jsonify([{
            "id": log.id,
            "source_name": log.source_name,
            "status": log.status,
            "items_found": log.items_found,
            "items_added": log.items_added,
            "error_message": log.error_message,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None
        } for log in logs])
    except Exception as e:
        logging.error(f"Error fetching logs: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs/errors', methods=['GET'])
def get_error_logs():
    """Get only error logs from scraping operations."""
    try:
        # Reuse the get_logs function with status=error
        request.args = request.args.copy()
        request.args['status'] = 'error'
        return get_logs()
    except Exception as e:
        logging.error(f"Error fetching error logs: {e}")
        return jsonify({"error": str(e)}), 500
        
@app.route('/api/logs/sources', methods=['GET'])
def get_log_sources(): 
    """Get unique source names from scraping logs."""
    try:
        # Query all unique source names from logs
        sources = db.session.query(ScrapeLog.source_name).distinct().all()
        # Extract source names from tuples

        source_names = [source[0] for source in sources]
        return jsonify(source_names)
    except Exception as e:
        logging.error(f"Error fetching log sources: {e}")
        return jsonify({"error": str(e)}), 500

# Schedule management endpoints
@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    """Get the current scraping schedule."""
    from config import SCHEDULE_INTERVAL
    import schedule
    
    # Get next run time (if available)
    next_run = None
    for job in schedule.jobs:
        if job.job_func.__name__ == 'run_scraper':
            next_run = job.next_run.isoformat() if job.next_run else None
            break
            
    return jsonify({
        "interval_minutes": SCHEDULE_INTERVAL,
        "next_run": next_run,
        "active": True
    })

@app.route('/api/schedule', methods=['POST'])
@with_retry
def update_schedule():
    """Update the scraping schedule."""
    import schedule
    from main import run_scraper
    
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
        
    data = request.get_json()
    
    # Validate interval parameter
    if 'interval_minutes' not in data:
        return jsonify({"error": "Missing required parameter: interval_minutes"}), 400
        
    try:
        interval = int(data['interval_minutes'])
        
        if interval < 15:
            return jsonify({"error": "Interval must be at least 15 minutes"}), 400
            
        # Update the SCHEDULE_INTERVAL in config file
        try:
            # Read the current config file
            with open('config.py', 'r') as f:
                config_content = f.read()
                
            # Update the SCHEDULE_INTERVAL value
            import re
            new_config = re.sub(
                r'SCHEDULE_INTERVAL\s*=\s*\d+', 
                f'SCHEDULE_INTERVAL = {interval}', 
                config_content
            )
            
            # Write the updated config back to file
            with open('config.py', 'w') as f:
                f.write(new_config)
                
            # Update the global variable
            import config
            config.SCHEDULE_INTERVAL = interval
            
            # Clear existing schedule
            schedule.clear()
            
            # Create a new schedule with the updated interval
            schedule.every(interval).minutes.do(run_scraper)
            
            return jsonify({
                "success": True,
                "message": f"Schedule updated to run every {interval} minutes",
                "interval_minutes": interval
            })
        except Exception as e:
            logging.error(f"Error updating schedule configuration: {e}")
            return jsonify({"error": f"Failed to update schedule: {str(e)}"}), 500
    except ValueError:
        return jsonify({"error": "Invalid interval: must be a number"}), 400

# User Management API Endpoints
def check_admin_session():
    """Check if admin is logged in via session"""
    admin_logged_in = session.get('admin_logged_in', False)
    logging.debug(f"Admin session check: {admin_logged_in}, session keys: {list(session.keys())}")
    return admin_logged_in

@app.route('/api/user-management/users', methods=['GET'])
def get_all_users():
    """Get all users for admin management."""
    # Check if admin is logged in via session
    if not check_admin_session():
        return jsonify({"error": "Admin access required"}), 403
    
    try:
        users = User.query.all()
        users_data = [user.to_dict() for user in users]
        return jsonify(users_data)
    except Exception as e:
        logging.error(f"Error fetching users: {e}")
        return jsonify({"error": "Failed to fetch users"}), 500

@app.route('/api/user-management/users/<int:user_id>/approve', methods=['POST'])
def approve_user(user_id):
    """Approve a pending user."""
    # Check if admin is logged in via session
    if not check_admin_session():
        return jsonify({"error": "Admin access required"}), 403
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        if user.is_active:
            return jsonify({"error": "User is already active"}), 400
        
        # Activate the user
        user.is_active = True
        user.approved_at = datetime.utcnow()
        # Note: We don't have approved_by field relationship, so we skip it for now
        
        db.session.commit()
        
        logging.info(f"User {user.username} approved by admin")
        return jsonify({"success": True, "message": "User approved successfully"})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error approving user {user_id}: {e}")
        return jsonify({"error": "Failed to approve user"}), 500

@app.route('/api/user-management/users/<int:user_id>/decline', methods=['DELETE'])
def decline_user(user_id):
    """Decline and delete a pending user."""
    # Check if admin is logged in via session
    if not check_admin_session():
        return jsonify({"error": "Admin access required"}), 403
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        if user.is_active:
            return jsonify({"error": "Cannot decline an active user"}), 400
        
        # Delete the user
        username = user.username
        db.session.delete(user)
        db.session.commit()
        
        logging.info(f"User {username} declined and deleted by admin")
        return jsonify({"success": True, "message": "User declined and removed successfully"})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error declining user {user_id}: {e}")
        return jsonify({"error": "Failed to decline user"}), 500

@app.route('/api/user-management/users/<int:user_id>/deactivate', methods=['POST'])
def deactivate_user(user_id):
    """Deactivate an active user."""
    # Check if admin is logged in via session
    if not check_admin_session():
        return jsonify({"error": "Admin access required"}), 403
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        if not user.is_active:
            return jsonify({"error": "User is already inactive"}), 400
        
        if user.is_admin:
            return jsonify({"error": "Cannot deactivate admin users"}), 400
        
        # Deactivate the user
        user.is_active = False
        db.session.commit()
        
        logging.info(f"User {user.username} deactivated by admin")
        return jsonify({"success": True, "message": "User deactivated successfully"})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deactivating user {user_id}: {e}")
        return jsonify({"error": "Failed to deactivate user"}), 500

@app.route('/api/user-management/users/<int:user_id>/make-admin', methods=['POST'])
def make_user_admin(user_id):
    """Make a user an admin."""
    # Check if admin is logged in via session
    if not check_admin_session():
        return jsonify({"error": "Admin access required"}), 403
    
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        if user.is_admin:
            return jsonify({"error": "User is already an admin"}), 400
        
        # Make user admin and ensure they're active
        user.is_admin = True
        user.is_active = True
        if not user.approved_at:
            user.approved_at = datetime.utcnow()
        
        db.session.commit()
        
        logging.info(f"User {user.username} promoted to admin")
        return jsonify({"success": True, "message": "User promoted to admin successfully"})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error making user {user_id} admin: {e}")
        return jsonify({"error": "Failed to make user admin"}), 500

def run_api():
    """Run the API server."""
    # Initialize the database with the Flask app
    db.init_app(app)
    
    # Create all tables
    with app.app_context():
        db.create_all()
        # Initialize test sources
        try:
            init_test_sources()
        except Exception as e:
            logging.warning(f"Could not initialize test sources: {e}")
    
    logging.info(f"Starting API server on http://{API_HOST}:{API_PORT}")
    app.run(host=API_HOST, port=API_PORT, debug=False)

@app.route('/api/bots', methods=['GET'])
def list_bots():
    """List statuses of all bots."""
    try:
        from bots.bot_manager import BotManager
        manager = BotManager()
        statuses = {
            'surface': manager.get_bot_status('surface'),
            'deep': manager.get_bot_status('deep'),
            'dark': manager.get_bot_status('dark'),
            'osint': manager.get_bot_status('osint')
        }
        return jsonify({'success': True, 'bots': statuses})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def _run_async(coro):
    """Run an async coroutine in a background thread and return immediately."""
    import threading
    def _runner():
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Ensure Flask app context is available in the thread
            with app.app_context():
                loop.run_until_complete(coro)
        except Exception as e:
            logging.error(f"Error in async runner: {e}")
        finally:
            # Clean up any pending tasks
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            # Close the loop
            loop.close()
    t = threading.Thread(target=_runner, daemon=True)
    t.start()


@app.route('/api/bots/<bot_type>/start', methods=['POST'])
def start_bot(bot_type):
    """Start a bot asynchronously."""
    try:
        from bots.bot_manager import BotManager
        manager = BotManager()
        _run_async(manager.start_bot(bot_type))
        return jsonify({'success': True, 'message': f'{bot_type} bot starting'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/bots/<bot_type>/stop', methods=['POST'])
def stop_bot(bot_type):
    """Stop a bot asynchronously."""
    try:
        from bots.bot_manager import BotManager
        manager = BotManager()
        _run_async(manager.stop_bot(bot_type))
        return jsonify({'success': True, 'message': f'{bot_type} bot stopping'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/bots/<bot_type>/status', methods=['GET'])
def bot_status(bot_type):
    """Get status of a specific bot."""
    try:
        # Ensure database is initialized
        with app.app_context():
            db.create_all()
        
        from bots.bot_manager import BotManager
        manager = BotManager()
        return jsonify({'success': True, 'status': manager.get_bot_status(bot_type)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/bots/run-cycle', methods=['POST'])
def run_bot_cycle():
    """Run a bot collection cycle for a given bot_type and source_type and return immediately."""
    try:
        # Ensure database is initialized
        with app.app_context():
            db.create_all()
        
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        data = request.get_json() or {}
        bot_type = data.get('bot_type')
        source_type = data.get('source_type')
        if bot_type not in ['surface', 'deep', 'dark', 'osint']:
            return jsonify({'error': 'Invalid bot_type'}), 400
        if source_type not in ['surface', 'deep', 'dark', 'osint', 'surface_web', 'deep_web', 'dark_web', 'osint_feed']:
            return jsonify({'error': 'Invalid source_type'}), 400
        from bots.bot_manager import BotManager
        manager = BotManager()
        _run_async(manager.run_cycle(bot_type, source_type))
        return jsonify({'success': True, 'message': f'Run cycle started for {bot_type} on {source_type} sources'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# DataSource CRUD (separate from legacy Source)
@app.route('/api/datasources', methods=['GET'])
def list_data_sources():
    """List DataSource entries used by bots."""
    try:
        from models import DataSource
        items = DataSource.query.order_by(DataSource.created_at.desc()).all()
        sources_data = [
            {
                'id': s.id,
                'name': s.name,
                'url': s.url,
                'source_type': s.source_type,
                'category': s.category,
                'risk_level': s.risk_level,
                'enabled': s.enabled,
                'scrape_interval': s.scrape_interval,
                'last_scraped': s.last_scraped.isoformat() if s.last_scraped else None,
                'next_scrape': s.next_scrape.isoformat() if s.next_scrape else None,
                'config': json.loads(s.config_json or '{}')
            } for s in items
        ]
        return jsonify({
            'success': True,
            'sources': sources_data,
            'total': len(sources_data)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'sources': [],
            'total': 0
        }), 500

# New endpoint to sync Source to DataSource
@app.route('/api/sync-sources', methods=['POST'])
def sync_sources_to_datasources():
    """Sync all entries from Source table to DataSource table."""
    try:
        from models import Source, DataSource
        sources = Source.query.all()
        synced_count = 0
        
        for src in sources:
            # Check if DataSource with same name exists
            existing = DataSource.query.filter_by(name=src.name).first()
            if not existing:
                ds = DataSource(
                    name=src.name,
                    url=src.url,
                    source_type=src.source_type,
                    category='default',
                    risk_level=src.risk_level,
                    enabled=src.enabled,
                    scrape_interval=src.scrape_interval,
                    config_json='{}'
                )
                db.session.add(ds)
                synced_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Synced {synced_count} sources to DataSource table'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/datasources', methods=['POST'])
def create_data_source():
    """Create a new DataSource entry."""
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        data = request.get_json() or {}
        required = ['name', 'url', 'source_type', 'category', 'risk_level']
        for f in required:
            if not data.get(f):
                return jsonify({'error': f'Missing required field: {f}'}), 400
        from models import DataSource
        ds = DataSource(
            name=data['name'],
            url=data['url'],
            source_type=data['source_type'],
            category=data['category'],
            risk_level=data['risk_level'],
            enabled=bool(data.get('enabled', True)),
            scrape_interval=int(data.get('scrape_interval', 60)),
            config_json=json.dumps(data.get('config', {}))
        )
        db.session.add(ds)
        db.session.commit()
        return jsonify({'success': True, 'id': ds.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/datasources/<int:ds_id>', methods=['PUT'])
def update_data_source(ds_id):
    """Update a DataSource entry."""
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        data = request.get_json() or {}
        from models import DataSource
        ds = DataSource.query.get(ds_id)
        if not ds:
            return jsonify({'error': 'DataSource not found'}), 404
        for attr in ['name', 'url', 'source_type', 'category', 'risk_level', 'enabled', 'scrape_interval']:
            if attr in data and data[attr] is not None:
                setattr(ds, attr, data[attr] if attr != 'scrape_interval' else int(data[attr]))
        if 'config' in data:
            ds.config_json = json.dumps(data['config'] or {})
        ds.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/datasources/<int:ds_id>', methods=['DELETE'])
def delete_data_source(ds_id):
    """Delete a DataSource entry."""
    try:
        from models import DataSource
        ds = DataSource.query.get(ds_id)
        if not ds:
            return jsonify({'error': 'DataSource not found'}), 404
        db.session.delete(ds)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/admin/bots')
def admin_bots():
    """Serve admin panel with bots control."""
    if not session.get('admin_logged_in'):
        return redirect('/eng/login')
    try:
        from flask import render_template
        return render_template('admin_bots.html')
    except Exception:
        # Fallback: return the raw file if rendering fails for some reason
        return send_from_directory('templates', 'admin_bots.html')


@app.route('/api/admin/init-db', methods=['POST'])
def init_db_tables():
    """Initialize database tables for new models."""
    try:
        db.create_all()
        return jsonify({'success': True, 'message': 'Database tables initialized'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/bot-logs', methods=['GET'])
def get_bot_logs():
    """Get bot activity logs."""
    try:
        # Ensure database is initialized
        with app.app_context():
            db.create_all()
        
        from models import BotLog, Bot
        logs = BotLog.query.join(Bot).order_by(BotLog.timestamp.desc()).limit(100).all()
        return jsonify({
            'success': True,
            'logs': [{
                'id': log.id,
                'bot_name': log.bot.name if log.bot else 'Unknown',
                'bot_type': log.bot.bot_type if log.bot else 'Unknown',
                'message': log.message,
                'status': log.status,
                'data_collected': log.data_collected,
                'execution_time': log.execution_time,
                'timestamp': log.timestamp.isoformat() if log.timestamp else None
            } for log in logs]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/data/stats', methods=['GET'])
def get_data_stats():
    """Get data collection statistics."""
    try:
        from models import Entity, Relationship, RawData
        from datetime import datetime, timedelta
        
        # Get counts
        try:
            total_entities = Entity.query.count()
            total_relationships = Relationship.query.count()
        except Exception as e:
            logger.warning(f"Could not fetch Entity/Relationship counts: {e}")
            total_entities = 0
            total_relationships = 0
        
        total_raw_data = RawData.query.count()
        
        # Get last 24 hours data
        yesterday = datetime.utcnow() - timedelta(days=1)
        last_24h = RawData.query.filter(RawData.created_at >= yesterday).count()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_entities': total_entities,
                'total_relationships': total_relationships,
                'total_raw_data': total_raw_data,
                'last_24h': last_24h
            }
        })
    except Exception as e:
        logger.error(f"Error getting data stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/data/raw', methods=['GET'])
def get_raw_data():
    """Get all raw data collected by bots with full content"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        source_type = request.args.get('source_type', '')
        bot_type = request.args.get('bot_type', '')
        
        query = RawData.query
        
        # Filter by source type if specified
        if source_type:
            query = query.join(DataSource).filter(DataSource.source_type == source_type)
        
        # Filter by bot type if specified
        if bot_type:
            query = query.filter(RawData.bot_type == bot_type)
        
        # Order by collection date (newest first)
        query = query.order_by(RawData.created_at.desc())
        
        # Paginate results
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        raw_data_list = []
        for raw_data in pagination.items:
            try:
                # Get related source info
                source = DataSource.query.get(raw_data.source_id) if raw_data.source_id else None

                # Get search index info
                search_index = SearchIndex.query.filter_by(raw_data_id=raw_data.id).first()

                # Handle null content safely
                content = raw_data.content or ''
                raw_html = raw_data.raw_html or ''

                # Safely parse metadata
                try:
                    metadata = json.loads(raw_data.metadata_json) if raw_data.metadata_json else {}
                except json.JSONDecodeError as json_error:
                    logger.warning(f"Invalid JSON in metadata for raw_data {raw_data.id}: {json_error}")
                    metadata = {}

                data_item = {
                    'id': raw_data.id,
                    'url': raw_data.url,
                    'title': raw_data.title,
                    'content': content,  # Full content
                    'content_preview': content[:500] + '...' if content and len(content) > 500 else content,
                    'content_length': len(content) if content else 0,
                    'raw_html': raw_data.raw_html[:1000] + '...' if raw_data.raw_html and len(raw_data.raw_html) > 1000 else raw_data.raw_html,
                    'content_type': raw_data.content_type,
                    'risk_score': raw_data.risk_score,
                    'keywords': search_index.keywords if search_index else '',
                    'tags': search_index.tags if search_index else '',
                    'risk_keywords': search_index.risk_keywords if search_index else '',
                    'created_at': raw_data.created_at.isoformat() if raw_data.created_at else None,
                    'source_name': source.name if source else 'Unknown',
                    'source_type': source.source_type if source else 'Unknown',
                    'source_category': source.category if source else 'Unknown',
                    'bot_type': raw_data.bot.bot_type if raw_data.bot else 'Unknown',
                    'metadata': metadata
                }
                raw_data_list.append(data_item)
            except Exception as item_error:
                logger.error(f"Error processing raw_data item {raw_data.id}: {item_error}")
                # Skip this item and continue with others
                continue
        
        return jsonify({
            'success': True,
            'data': raw_data_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/data/raw/<int:data_id>', methods=['GET'])
def get_raw_data_detail(data_id):
    """Get detailed view of a specific raw data entry with full content"""
    try:
        raw_data = RawData.query.get_or_404(data_id)
        source = DataSource.query.get(raw_data.source_id) if raw_data.source_id else None
        
        # Get search index info
        search_index = SearchIndex.query.filter_by(raw_data_id=raw_data.id).first()
        
        # Handle null content safely
        content = raw_data.content or ''
        raw_html = raw_data.raw_html or ''

        data_detail = {
            'id': raw_data.id,
            'url': raw_data.url,
            'title': raw_data.title,
            'content': content,  # Full content
            'content_type': raw_data.content_type,
            'risk_score': raw_data.risk_score,
            'keywords': search_index.keywords if search_index else '',
            'tags': search_index.tags if search_index else '',
            'risk_keywords': search_index.risk_keywords if search_index else '',
            'created_at': raw_data.created_at.isoformat() if raw_data.created_at else None,
            'source_name': source.name if source else 'Unknown',
            'source_type': source.source_type if source else 'Unknown',
            'source_category': source.category if source else 'Unknown',
            'bot_type': raw_data.bot.bot_type if raw_data.bot else 'Unknown',
            'metadata': json.loads(raw_data.metadata_json) if raw_data.metadata_json else {},
            'raw_html': raw_html  # Full HTML
        }
        
        return jsonify({'success': True, 'data': data_detail})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/data/search', methods=['GET'])
def search_raw_data():
    """Search raw data by keywords, title, or content"""
    try:
        query = request.args.get('q', '')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        if not query:
            return jsonify({'success': False, 'error': 'Search query is required'}), 400
        
        # Search in title, content, and keywords
        search_filter = RawData.query.join(SearchIndex).filter(
            RawData.title.contains(query) |
            RawData.content.contains(query) |
            SearchIndex.keywords.contains(query) |
            SearchIndex.tags.contains(query)
        )
        
        # Order by relevance (title matches first, then content)
        search_results = search_filter.order_by(
            RawData.title.contains(query).desc(),
            RawData.content.contains(query).desc(),
            RawData.created_at.desc()
        )
        
        # Paginate results
        pagination = search_results.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        results_list = []
        for raw_data in pagination.items:
            source = DataSource.query.get(raw_data.source_id) if raw_data.source_id else None
            
            # Get search index info
            search_index = SearchIndex.query.filter_by(raw_data_id=raw_data.id).first()
            
            # Handle null content safely
            content = raw_data.content or ''
            data_item = {
                'id': raw_data.id,
                'url': raw_data.url,
                'title': raw_data.title,
                'content_preview': content[:300] + '...' if content and len(content) > 300 else content,
                'content_length': len(content) if content else 0,
                'keywords': search_index.keywords if search_index else '',
                'tags': search_index.tags if search_index else '',
                'risk_keywords': search_index.risk_keywords if search_index else '',
                'risk_score': raw_data.risk_score,
                'created_at': raw_data.created_at.isoformat() if raw_data.created_at else None,
                'source_name': source.name if source else 'Unknown',
                'source_type': source.source_type if source else 'Unknown',
                'bot_type': raw_data.bot.bot_type if raw_data.bot else 'Unknown'
            }
            results_list.append(data_item)
        
        return jsonify({
            'success': True,
            'data': results_list,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def init_test_sources():
    """Initialize test data sources for comprehensive testing"""
    with app.app_context():
        db.create_all()
        
        # Clear existing sources
        DataSource.query.delete()
        
        # Surface Web Sources
        surface_sources = [
            {
                'name': 'Hacker News',
                'url': 'https://news.ycombinator.com',
                'source_type': 'surface_web',
                'keywords': 'cybersecurity, hacking, data breach, vulnerability, exploit',
                'risk_level': 'medium',
                'enabled': True
            },
            {
                'name': 'TechCrunch Security',
                'url': 'https://techcrunch.com/tag/security/',
                'source_type': 'surface_web',
                'keywords': 'security, breach, cyber attack, malware, ransomware',
                'risk_level': 'medium',
                'enabled': True
            },
            {
                'name': 'The Hacker News',
                'url': 'https://thehackernews.com',
                'source_type': 'surface_web',
                'keywords': 'cyber attack, malware, vulnerability, exploit, breach',
                'risk_level': 'high',
                'enabled': True
            },
            {
                'name': 'Bleeping Computer',
                'url': 'https://www.bleepingcomputer.com',
                'source_type': 'surface_web',
                'keywords': 'malware, ransomware, cyber attack, security, breach',
                'risk_level': 'high',
                'enabled': True
            }
        ]
        
        # Deep Web Sources
        deep_sources = [
            {
                'name': 'Pastebin Recent',
                'url': 'https://pastebin.com/archive',
                'source_type': 'deep_web',
                'keywords': 'leak, dump, password, credential, database',
                'risk_level': 'high',
                'enabled': True
            },
            {
                'name': 'GitHub Security',
                'url': 'https://github.com/topics/security',
                'source_type': 'deep_web',
                'keywords': 'security, vulnerability, exploit, malware, hacking',
                'risk_level': 'medium',
                'enabled': True
            },
            {
                'name': 'Reddit r/netsec',
                'url': 'https://www.reddit.com/r/netsec',
                'source_type': 'deep_web',
                'keywords': 'security, vulnerability, exploit, malware, breach',
                'risk_level': 'medium',
                'enabled': True
            },
            {
                'name': 'Reddit r/hacking',
                'url': 'https://www.reddit.com/r/hacking',
                'source_type': 'deep_web',
                'keywords': 'hacking, exploit, vulnerability, malware, security',
                'risk_level': 'high',
                'enabled': True
            }
        ]
        
        # Dark Web Sources (Tor required)
        dark_sources = [
            {
                'name': 'Darknet Live',
                'url': 'http://darknetlive.com',
                'source_type': 'dark_web',
                'keywords': 'darknet, market, forum, onion, tor',
                'risk_level': 'high',
                'enabled': False  # Disabled until Tor is configured
            }
        ]
        
        # OSINT Feed Sources
        osint_sources = [
            {
                'name': 'CVE Database',
                'url': 'https://cve.mitre.org',
                'source_type': 'osint_feed',
                'keywords': 'CVE, vulnerability, exploit, security',
                'risk_level': 'medium',
                'enabled': True
            },
            {
                'name': 'NIST NVD',
                'url': 'https://nvd.nist.gov/vuln',
                'source_type': 'osint_feed',
                'keywords': 'CVE, vulnerability, NVD, security',
                'risk_level': 'medium',
                'enabled': True
            },
            {
                'name': 'MITRE ATT&CK',
                'url': 'https://attack.mitre.org',
                'source_type': 'osint_feed',
                'keywords': 'ATT&CK, technique, tactic, malware, threat',
                'risk_level': 'medium',
                'enabled': True
            }
        ]
        
        # Add all sources
        all_sources = surface_sources + deep_sources + dark_sources + osint_sources
        
        for source_data in all_sources:
            source = DataSource(
                name=source_data['name'],
                url=source_data['url'],
                source_type=source_data['source_type'],
                keywords=source_data['keywords'],
                risk_level=source_data['risk_level'],
                enabled=source_data['enabled'],
                last_scraped=None
            )
            db.session.add(source)
        
        db.session.commit()
        return len(all_sources)

@app.route('/api/admin/init-test-sources', methods=['POST'])
def init_test_sources_endpoint():
    """Initialize test data sources"""
    try:
        count = init_test_sources()
        return jsonify({
            'success': True,
            'message': f'Initialized {count} test data sources',
            'sources_added': count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# API Integration Management Endpoints

@app.route('/api/integrations', methods=['GET'])
def list_integrations():
    """List all registered API integrations"""
    try:
        integrations = api_manager.list_integrations()
        return jsonify({'success': True, 'integrations': integrations})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/integrations/<integration_name>/query', methods=['POST'])
def execute_integration_query(integration_name):
    """Execute a query on a specific integration"""
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        data = request.get_json()
        query_type = data.get('query_type')
        params = data.get('params', {})

        if not query_type:
            return jsonify({'error': 'query_type is required'}), 400

        result = api_manager.execute_query(integration_name, query_type, params)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/integrations/test/<integration_name>', methods=['POST'])
def test_integration(integration_name):
    """Test a specific integration"""
    try:
        integration = api_manager.get_integration(integration_name)
        if not integration:
            return jsonify({'error': f'Integration {integration_name} not found'}), 404

        test_result = integration.test_connection()
        return jsonify({
            'integration': integration_name,
            'test_result': test_result,
            'status': 'success' if test_result else 'failed'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/integrations/reload', methods=['POST'])
def reload_integrations():
    """Reload all API integrations from database"""
    try:
        initialize_api_integrations()
        integrations = api_manager.list_integrations()
        return jsonify({
            'success': True,
            'message': 'Integrations reloaded successfully',
            'integrations': integrations
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# File Upload System Endpoints

@app.route('/api/uploads', methods=['POST'])
def upload_file():
    """Upload file with malware scanning and risk assessment"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        # Get upload parameters
        uploader_id = request.form.get('uploader_id', type=int)
        is_public = request.form.get('is_public', 'false').lower() == 'true'
        risk_level_override = request.form.get('risk_level_override')

        # Process upload
        result = upload_manager.process_upload(file, uploader_id, is_public)

        if 'error' in result:
            return jsonify({'error': result['error']}), 400

        # Store in database if successful
        if result['storage_status'] != 'quarantined':
            try:
                from models import UploadItem
                upload_item = UploadItem(
                    filename=result['filename'],
                    content_type=result['scan_result']['mime_type'],
                    size_bytes=result['scan_result']['file_size'],
                    risk_level=result['scan_result']['risk_assessment']['level'],
                    is_public=is_public,
                    uploader_id=uploader_id,
                    storage_path=result['storage_path'],
                    upload_metadata=json.dumps({
                        'scan_result': result['scan_result'],
                        'uploaded_at': result['uploaded_at'],
                        'partial_content': result.get('partial_content')
                    })
                )
                db.session.add(upload_item)
                db.session.commit()
                result['upload_id'] = upload_item.id
            except Exception as db_error:
                logger.error(f"Database error storing upload: {db_error}")
                # File is already saved, so we can still return success

        return jsonify({
            'success': True,
            'upload_result': result
        })

    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/uploads', methods=['GET'])
def list_uploads():
    """List uploaded files with filtering"""
    try:
        from models import UploadItem

        # Get query parameters
        risk_level = request.args.get('risk_level')
        uploader_id = request.args.get('uploader_id', type=int)
        is_public = request.args.get('is_public')
        limit = min(int(request.args.get('limit', 50)), 200)

        query = UploadItem.query

        if risk_level:
            query = query.filter_by(risk_level=risk_level)
        if uploader_id:
            query = query.filter_by(uploader_id=uploader_id)
        if is_public is not None:
            query = query.filter_by(is_public=is_public.lower() == 'true')

        query = query.order_by(UploadItem.uploaded_at.desc()).limit(limit)
        uploads = query.all()

        result = []
        for upload in uploads:
            metadata = json.loads(upload.upload_metadata or '{}')
            result.append({
                'id': upload.id,
                'filename': upload.filename,
                'content_type': upload.content_type,
                'size_bytes': upload.size_bytes,
                'risk_level': upload.risk_level,
                'is_public': upload.is_public,
                'uploader_id': upload.uploader_id,
                'uploaded_at': upload.uploaded_at.isoformat() if upload.uploaded_at else None,
                'scan_result': metadata.get('scan_result'),
                'storage_status': 'quarantined' if upload.storage_path and 'quarantine' in upload.storage_path else 'stored'
            })

        return jsonify({
            'success': True,
            'uploads': result,
            'total': len(result)
        })

    except Exception as e:
        logging.error(f"Error listing uploads: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/uploads/<int:upload_id>', methods=['GET'])
def get_upload_details(upload_id):
    """Get detailed information about a specific upload"""
    try:
        from models import UploadItem

        upload = UploadItem.query.filter(UploadItem.id == upload_id).first()
        if not upload:
            return jsonify({'error': 'Upload not found'}), 404

        metadata = json.loads(upload.upload_metadata or '{}')

        # Use upload.uploaded_at instead of upload.created_at if created_at is missing
        try:
            created_at = upload.created_at
        except AttributeError:
            created_at = upload.uploaded_at

        try:
            updated_at = upload.updated_at
        except AttributeError:
            updated_at = None

        return jsonify({
            'success': True,
            'upload': {
                'id': upload.id,
                'filename': upload.filename,
                'content_type': upload.content_type,
                'size_bytes': upload.size_bytes,
                'risk_level': upload.risk_level,
                'is_public': upload.is_public,
                'uploader_id': upload.uploader_id,
                'storage_path': upload.storage_path,
                'created_at': created_at.isoformat() if created_at else None,
                'updated_at': updated_at.isoformat() if updated_at else None,
                'scan_result': metadata.get('scan_result'),
                'partial_content': metadata.get('partial_content'),
                'uploaded_at': metadata.get('uploaded_at')
            }
        })

    except Exception as e:
        logger.error(f"Error getting upload details: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/uploads/<int:upload_id>/download', methods=['GET'])
def download_upload(upload_id):
    """Download an uploaded file"""
    try:
        from models import UploadItem

        upload = UploadItem.query.get(upload_id)
        if not upload:
            return jsonify({'error': 'Upload not found'}), 404

        if not upload.storage_path or not os.path.exists(upload.storage_path):
            return jsonify({'error': 'File not found on disk'}), 404

        # Check if file is quarantined
        if 'quarantine' in upload.storage_path:
            return jsonify({'error': 'File is quarantined and cannot be downloaded'}), 403

        return send_file(
            upload.storage_path,
            as_attachment=True,
            download_name=upload.filename
        )

    except Exception as e:
        logger.error(f"Error downloading upload: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/uploads/<int:upload_id>/scan', methods=['POST'])
def rescan_upload(upload_id):
    """Rescan an uploaded file"""
    try:
        from models import UploadItem

        upload = UploadItem.query.get(upload_id)
        if not upload:
            return jsonify({'error': 'Upload not found'}), 404

        if not upload.storage_path or not os.path.exists(upload.storage_path):
            return jsonify({'error': 'File not found on disk'}), 404

        # Rescan the file
        scan_result = upload_manager.scan_file(upload.storage_path)

        # Update metadata
        metadata = json.loads(upload.upload_metadata or '{}')
        metadata['scan_result'] = scan_result
        metadata['last_scan'] = datetime.utcnow().isoformat()

        upload.upload_metadata = json.dumps(metadata)
        upload.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'File rescanned successfully',
            'scan_result': scan_result
        })

    except Exception as e:
        logger.error(f"Error rescanning upload: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/uploads/quarantine', methods=['GET'])
def list_quarantined():
    """List quarantined files"""
    try:
        from models import UploadItem

        quarantined = UploadItem.query.filter(
            UploadItem.storage_path.contains('quarantine')
        ).order_by(UploadItem.created_at.desc()).all()

        result = []
        for upload in quarantined:
            metadata = json.loads(upload.upload_metadata or '{}')
            result.append({
                'id': upload.id,
                'filename': upload.filename,
                'risk_level': upload.risk_level,
                'created_at': upload.created_at.isoformat() if upload.created_at else None,
                'scan_result': metadata.get('scan_result')
            })

        return jsonify({
            'success': True,
            'quarantined': result,
            'total': len(result)
        })

    except Exception as e:
        logger.error(f"Error listing quarantined files: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500