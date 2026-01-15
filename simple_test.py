#!/usr/bin/env python3
"""
Simple PostgreSQL connection test for Neon database.
"""
import os

def test_neon_connection():
    """Test connection to Neon PostgreSQL database."""
    try:
        # Set the database URL
        db_url = "postgresql://neondb_owner:npg_2uJ7LoQrHpSe@ep-square-haze-a815v283-pooler.eastus2.azure.neon.tech/Radar-db?sslmode=require&channel_binding=require"

        # Try to import psycopg2
        try:
            import psycopg2
        except ImportError:
            return False, "psycopg2 not installed. Run: pip install psycopg2-binary"

        # Parse the connection string
        from urllib.parse import urlparse
        result = urlparse(db_url)
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

def main():
    """Test the Neon PostgreSQL connection."""
    print("🧪 Testing Neon PostgreSQL Connection")
    print("=" * 40)
    print("📡 Database URL: postgresql://neondb_owner:***@ep-square-haze-a815v283-pooler.eastus2.azure.neon.tech/Radar-db?sslmode=require&channel_binding=require")
    print()

    success, message = test_neon_connection()

    if success:
        print("✅ Connection successful!")
        print(f"📊 {message}")
        print()
        print("🎉 Your Neon PostgreSQL database is working correctly!")
        return True
    else:
        print("❌ Connection failed!")
        print(f"📊 {message}")
        print()
        print("🔧 Troubleshooting steps:")
        print("1. Check your internet connection")
        print("2. Verify your Neon database credentials")
        print("3. Ensure the database is active in Neon dashboard")
        print("4. Install psycopg2: pip install psycopg2-binary")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
