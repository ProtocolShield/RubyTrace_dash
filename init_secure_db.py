"""
Initialize database with new security models
"""
import os
from flask import Flask
from models import db
from auth_models import User, AccessLog, APIRateLimit, MapData

def initialize_secure_database():
    """Initialize database with security models"""
    # Create a standalone Flask app for database initialization
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # Use SQLite for local development
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database with app
    db.init_app(app)
    
    with app.app_context():
        try:
            # Create all tables including new security models
            db.create_all()
            
            # Create default admin user if it doesn't exist
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    email='admin@protocolshield.com',
                    full_name='System Administrator',
                    is_admin=True,
                    is_active=True
                )
                admin_user.set_password('SecureAdmin2024!')
                admin_user.generate_api_key()
                
                db.session.add(admin_user)
                print("Created default admin user")
            
            # Create sample map data points
            if MapData.query.count() == 0:
                sample_locations = [
                    {
                        'latitude': 40.7128,
                        'longitude': -74.0060,
                        'threat_level': 'high',
                        'description': 'High threat level area'
                    },
                    {
                        'latitude': 51.5074,
                        'longitude': -0.1278,
                        'threat_level': 'medium',
                        'description': 'Medium threat level area'
                    },
                    {
                        'latitude': 35.6762,
                        'longitude': 139.6503,
                        'threat_level': 'low',
                        'description': 'Low threat level area'
                    },
                    {
                        'latitude': 52.5200,
                        'longitude': 13.4050,
                        'threat_level': 'high',
                        'description': 'High threat level area'
                    },
                    {
                        'latitude': -33.8688,
                        'longitude': 151.2093,
                        'threat_level': 'low',
                        'description': 'Low threat level area'
                    }
                ]
                
                for location in sample_locations:
                    map_point = MapData(**location)
                    db.session.add(map_point)
                
                print("Created sample map data points")
            
            db.session.commit()
            print("Database initialization completed successfully")
            
            return True
            
        except Exception as e:
            print(f"Database initialization failed: {str(e)}")
            db.session.rollback()
            return False

if __name__ == '__main__':
    success = initialize_secure_database()
    if success:
        print("\n✅ Secure database initialized successfully")
        print("📍 Default admin credentials:")
        print("   Username: admin")
        print("   Password: SecureAdmin2024!")
        print("🔐 Security features enabled:")
        print("   - JWT authentication")
        print("   - 2FA support")
        print("   - Rate limiting")
        print("   - .onion admin access")
        print("   - Map visualization data")
    else:
        print("\n❌ Database initialization failed")
