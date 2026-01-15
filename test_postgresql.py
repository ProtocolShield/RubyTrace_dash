#!/usr/bin/env python3
"""
Test PostgreSQL connection and setup for OSINT platform.
"""
import os
import sys
import logging
from database import test_postgresql_connection, init_postgresql_tables, create_db_engine

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """Test PostgreSQL connection and setup."""
    print("🧪 Testing PostgreSQL Connection")
    print("=" * 40)

    # Set the PostgreSQL connection string
    postgres_url = "postgresql://neondb_owner:npg_2uJ7LoQrHpSe@ep-square-haze-a815v283-pooler.eastus2.azure.neon.tech/Radar-db?sslmode=require&channel_binding=require"

    # Set environment variable
    os.environ['DATABASE_URL'] = postgres_url

    print(f"📡 Connection String: {postgres_url}")
    print()

    # Test connection
    print("🔍 Testing database connection...")
    success, message = test_postgresql_connection()

    if success:
        print("✅ Connection successful!")
        print(f"📊 {message}")
        print()

        # Test table initialization
        print("🏗️  Testing table initialization...")
        success, message = init_postgresql_tables()

        if success:
            print("✅ Tables initialized successfully!")
            print(f"📊 {message}")
        else:
            print("❌ Table initialization failed!")
            print(f"📊 {message}")

    else:
        print("❌ Connection failed!")
        print(f"📊 {message}")
        return False

    print()
    print("🎉 PostgreSQL setup completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
