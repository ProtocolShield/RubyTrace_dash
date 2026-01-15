#!/bin/bash

echo "🚀 OSINT Platform PostgreSQL/Neon Deployment Script"
echo "=================================================="
echo ""
echo "This script will configure your OSINT platform to use Neon PostgreSQL database."
echo "Please run this script with sudo privileges."
echo ""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "✅ Running as root - proceeding with configuration..."
else
   echo "❌ This script must be run as root (use: sudo bash postgresql_deployment.sh)"
   exit 1
fi

echo ""
echo "📦 Step 1: Installing PostgreSQL client tools..."
apt update
apt install -y postgresql-client postgresql-contrib

echo ""
echo "🔧 Step 2: Installing Python PostgreSQL adapter..."
pip3 install psycopg2-binary

echo ""
echo "📁 Step 3: Setting up project directory..."
cd /opt/osint-bots

echo ""
echo "⚙️ Step 4: Creating Neon PostgreSQL environment configuration..."
cat > .env << 'EOF'
# Neon PostgreSQL Database Configuration
DATABASE_URL=postgresql://neondb_owner:npg_2uJ7LoQrHpSe@ep-square-haze-a815v283-pooler.eastus2.azure.neon.tech/Radar-db?sslmode=require&channel_binding=require

# Tor Configuration
TOR_ENABLED=true
TOR_SOCKS_PORT=9050
TOR_CONTROL_PORT=9051

# Security Settings
SECRET_KEY=your-secret-key-here-change-in-production
FLASK_ENV=production

# API Configuration
API_HOST=127.0.0.1
API_PORT=5000

# Logging
LOG_LEVEL=INFO

# SSL Settings for PostgreSQL
PGSSLMODE=require
PGCHANNELBINDING=require
EOF

echo ""
echo "🧪 Step 5: Testing PostgreSQL connection..."
python3 -c "
import os
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_2uJ7LoQrHpSe@ep-square-haze-a815v283-pooler.eastus2.azure.neon.tech/Radar-db?sslmode=require&channel_binding=require'
from database import test_postgresql_connection
success, message = test_postgresql_connection()
print(f'Connection test: {message}')
"

if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL connection test passed!"
else
    echo "❌ PostgreSQL connection test failed!"
    echo "Please check your Neon database credentials and network connectivity."
    exit 1
fi

echo ""
echo "🏗️ Step 6: Initializing database tables..."
python3 -c "
import os
os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_2uJ7LoQrHpSe@ep-square-haze-a815v283-pooler.eastus2.azure.neon.tech/Radar-db?sslmode=require&channel_binding=require'
from database import init_postgresql_tables
success, message = init_postgresql_tables()
print(f'Table initialization: {message}')
"

echo ""
echo "🔄 Step 7: Restarting OSINT service with new database configuration..."
systemctl restart osint-bots

echo ""
echo "📊 Step 8: Checking service status..."
systemctl status osint-bots --no-pager

echo ""
echo "✅ PostgreSQL/Neon configuration completed successfully!"
echo ""
echo "🌐 Your OSINT platform is now using Neon PostgreSQL database!"
echo ""
echo "🔧 Database connection details:"
echo "  - Host: ep-square-haze-a815v283-pooler.eastus2.azure.neon.tech"
echo "  - Database: Radar-db"
echo "  - User: neondb_owner"
echo "  - SSL Mode: require"
echo "  - Channel Binding: require"
echo ""
echo "📋 Service management commands:"
echo "  - Check status: sudo systemctl status osint-bots"
echo "  - View logs: sudo journalctl -u osint-bots -f"
echo "  - Restart: sudo systemctl restart osint-bots"
echo "  - Test DB: python3 -c 'from database import test_postgresql_connection; print(test_postgresql_connection())'"
echo ""
echo "⚠️  IMPORTANT NOTES:"
echo "  - Your application is now using the Neon PostgreSQL database"
echo "  - All data will be stored in the cloud database"
echo "  - Make sure your Neon database remains active"
echo "  - Consider setting up automated backups in Neon dashboard"
echo ""
echo "🎉 Configuration completed! Your OSINT platform is now using PostgreSQL!"
