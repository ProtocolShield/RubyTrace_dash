#!/bin/bash

echo "🚀 OSINT Platform Manual Deployment Script"
echo "=========================================="
echo ""
echo "This script will install all required packages and configure the system."
echo "Please run this script with sudo privileges."
echo ""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "✅ Running as root - proceeding with installation..."
else
   echo "❌ This script must be run as root (use: sudo bash manual_deployment.sh)"
   exit 1
fi

echo ""
echo "📦 Step 1: Updating system packages..."
apt update && apt upgrade -y

echo ""
echo "🔧 Step 2: Installing required packages..."
apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib git curl wget tor ufw fail2ban

echo ""
echo "🔥 Step 3: Configuring firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo ""
echo "🧅 Step 4: Setting up Tor service..."
systemctl start tor
systemctl enable tor

echo ""
echo "⏳ Step 5: Waiting for Tor to be ready..."
sleep 10

echo ""
echo "🔍 Step 6: Verifying Tor connection..."
netstat -tlnp | grep :9050 || echo "Warning: Tor SOCKS port not accessible"

echo ""
echo "🐘 Step 7: Setting up PostgreSQL database..."
systemctl start postgresql
systemctl enable postgresql

# Create database and user
echo ""
echo "Creating database and user..."
sudo -u postgres psql -c "CREATE USER osint_user WITH PASSWORD 'secure_password_2024';"
sudo -u postgres psql -c "CREATE DATABASE osint_db OWNER osint_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE osint_db TO osint_user;"

echo ""
echo "📁 Step 8: Setting up project directory..."
cd /opt
mkdir -p osint-bots
cd osint-bots

echo ""
echo "🐍 Step 9: Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo ""
echo "📚 Step 10: Installing Python dependencies..."
pip install --upgrade pip
pip install -r /home/jux/deploy_requirements.txt

echo ""
echo "📖 Step 11: Downloading NLTK data..."
python3 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('averaged_perceptron_tagger')"

echo ""
echo "⚙️ Step 12: Creating environment configuration..."
cat > .env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://osint_user:secure_password_2024@localhost:5432/osint_db

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
EOF

echo ""
echo "⚙️ Step 13: Creating systemd service..."
tee /etc/systemd/system/osint-bots.service > /dev/null << 'EOF'
[Unit]
Description=OSINT Bot System with Tor
After=network.target postgresql.service tor.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/osint-bots
Environment=PATH=/opt/osint-bots/venv/bin
EnvironmentFile=/opt/osint-bots/.env
ExecStart=/opt/osint-bots/venv/bin/python /opt/osint-bots/main.py
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
ProtectHome=true
ProtectSystem=strict
ReadWritePaths=/opt/osint-bots /var/log

[Install]
WantedBy=multi-user.target
EOF

echo ""
echo "🚀 Step 14: Enabling and starting service..."
systemctl daemon-reload
systemctl enable osint-bots
systemctl start osint-bots

echo ""
echo "📊 Step 15: Checking service status..."
systemctl status osint-bots --no-pager

echo ""
echo "🌐 Step 16: Setting up nginx with security headers..."
tee /etc/nginx/sites-available/osint-bots > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Logging
    access_log /var/log/nginx/osint_access.log;
    error_log /var/log/nginx/osint_error.log;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Additional security headers
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files caching
    location /static/ {
        proxy_pass http://127.0.0.1:5000;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

echo ""
echo "🔗 Step 17: Enabling nginx site..."
ln -sf /etc/nginx/sites-available/osint-bots /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
systemctl restart nginx

echo ""
echo "📋 Step 18: Setting up log rotation..."
tee /etc/logrotate.d/osint-bots > /dev/null << 'EOF'
/var/log/nginx/osint_*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF

echo ""
echo "💾 Step 19: Creating backup script..."
cat > /opt/osint-bots/backup_db.sh << 'EOF'
#!/bin/bash
# Database backup script
DATE=$(date +%Y%m%d_%H%M%S)
sudo -u postgres pg_dump osint_db > /opt/osint-bots/backup_osint_db_$DATE.sql
find /opt/osint-bots/backup_*.sql -mtime +7 -delete
EOF

chmod +x /opt/osint-bots/backup_db.sh

# Add backup to cron
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/osint-bots/backup_db.sh") | crontab -

echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "🌐 Access your OSINT Bot System at: http://$(curl -s ifconfig.me)"
echo ""
echo "🔧 Service management commands:"
echo "  - Check status: sudo systemctl status osint-bots"
echo "  - View logs: sudo journalctl -u osint-bots -f"
echo "  - Restart: sudo systemctl restart osint-bots"
echo "  - Tor status: sudo systemctl status tor"
echo "  - Database: postgresql://osint_user:secure_password_2024@localhost:5432/osint_db"
echo ""
echo "⚠️  IMPORTANT SECURITY NOTES:"
echo "  - Change the database password in .env file and PostgreSQL!"
echo "  - Set up SSL certificates for HTTPS access"
echo "  - Configure your domain name in nginx configuration"
echo "  - Update SECRET_KEY in environment variables"
echo ""
echo "🎉 Deployment completed! Your OSINT platform is now running with Tor and PostgreSQL."
