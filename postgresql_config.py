"""
PostgreSQL configuration for OSINT platform using Neon database.
"""
import os

# Neon PostgreSQL Database Configuration
NEON_DATABASE_URL = "postgresql://neondb_owner:npg_2uJ7LoQrHpSe@ep-square-haze-a815v283-pooler.eastus2.azure.neon.tech/Radar-db?sslmode=require&channel_binding=require"
NEON_REST_API_URL = "https://ep-square-haze-a815v283.apirest.eastus2.azure.neon.tech/Radar-db/rest/v1"

# Set the database URL for the application
os.environ['DATABASE_URL'] = NEON_DATABASE_URL

# Database connection settings
DATABASE_CONFIG = {
    'url': NEON_DATABASE_URL,
    'rest_api': NEON_REST_API_URL,
    'pool_size': 5,
    'max_overflow': 10,
    'pool_timeout': 30,
    'pool_recycle': 1800,  # 30 minutes
    'ssl_mode': 'require',
    'channel_binding': 'require'
}

def get_database_config():
    """Get the database configuration."""
    return DATABASE_CONFIG

def test_neon_connection():
    """Test connection to Neon PostgreSQL database."""
    try:
        import psycopg2
        from urllib.parse import urlparse

        # Parse the connection string
        result = urlparse(NEON_DATABASE_URL)
        dbname = result.path[1:]  # Remove leading slash
        user = result.username
        password = result.password
        host = result.hostname
        port = result.port or 5432

        # Connect to the database
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port,
            sslmode='require'
        )

        # Test the connection
        cur = conn.cursor()
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]

        cur.close()
        conn.close()

        return True, f"Neon PostgreSQL connection successful: {version}"

    except Exception as e:
        return False, f"Neon PostgreSQL connection failed: {str(e)}"

if __name__ == "__main__":
    print("🧪 Testing Neon PostgreSQL Connection")
    print("=" * 50)
    print(f"📡 Database URL: {NEON_DATABASE_URL}")
    print(f"🌐 REST API: {NEON_REST_API_URL}")
    print()

    success, message = test_neon_connection()
    if success:
        print("✅ Connection successful!")
        print(f"📊 {message}")
    else:
        print("❌ Connection failed!")
        print(f"📊 {message}")
