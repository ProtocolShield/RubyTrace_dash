#!/bin/bash

echo "🚀 OSINT Bot System Deployment Script with Tor & PostgreSQL"
echo "=========================================================="

# Update system
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install required packages including Tor and PostgreSQL
echo "🔧 Installing required packages..."
sudo apt install -y python3 python3-pip python3-venv nginx postgresql postgresql-contrib git curl wget tor ufw fail2ban

# Configure firewall
echo "🔥 Configuring firewall..."
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Start and enable Tor service
echo "🧅 Setting up Tor service..."
sudo systemctl start tor
sudo systemctl enable tor

# Wait for Tor to be ready
echo "⏳ Waiting for Tor service to be ready..."
sleep 10

# Verify Tor is working
echo "🔍 Verifying Tor connection..."
sudo netstat -tlnp | grep :9050 || echo "Warning: Tor SOCKS port not accessible"

# Configure PostgreSQL
echo "🐘 Setting up PostgreSQL database..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql -c "CREATE USER osint_user WITH PASSWORD 'secure_password_2024';"
sudo -u postgres psql -c "CREATE DATABASE osint_db OWNER osint_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE osint_db TO osint_user;"

# Create project directory
echo "📁 Creating project directory..."
sudo mkdir -p /opt/osint-bots
sudo chown $USER:$USER /opt/osint-bots
cd /opt/osint-bots

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r deploy_requirements.txt

# Download NLTK data
echo "📖 Downloading NLTK data..."
python3 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('averaged_perceptron_tagger')"

# Create environment file for database configuration
echo "⚙️ Creating environment configuration..."
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

# Create systemd service
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/osint-bots.service > /dev/null << 'EOF'
[Unit]
Description=OSINT Bot System with Tor
After=network.target postgresql.service tor.service

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/osint-bots
Environment=PATH=/opt/osint-bots/venv/bin
EnvironmentFile=/opt/osint-bots/.env
ExecStart=/opt/osint-bots/venv/bin/python main.py
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

# Enable and start service
echo "🚀 Enabling and starting service..."
sudo systemctl daemon-reload
sudo systemctl enable osint-bots
sudo systemctl start osint-bots

# Check service status
echo "📊 Checking service status..."
sudo systemctl status osint-bots --no-pager

# Create nginx configuration with security headers
echo "🌐 Setting up nginx with security headers..."
sudo tee /etc/nginx/sites-available/osint-bots > /dev/null << 'EOF'
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

# Enable nginx site
sudo ln -sf /etc/nginx/sites-available/osint-bots /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

# Set up log rotation
echo "📋 Setting up log rotation..."
sudo tee /etc/logrotate.d/osint-bots > /dev/null << 'EOF'
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

# Create backup script
echo "💾 Creating backup script..."
cat > backup_db.sh << 'EOF'
#!/bin/bash
# Database backup script
DATE=$(date +%Y%m%d_%H%M%S)
sudo -u postgres pg_dump osint_db > /opt/osint-bots/backup_osint_db_$DATE.sql
find /opt/osint-bots/backup_*.sql -mtime +7 -delete
EOF

chmod +x backup_db.sh

# Make backup script executable and add to cron
sudo cp backup_db.sh /opt/osint-bots/
sudo chown $USER:$USER /opt/osint-bots/backup_db.sh
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/osint-bots/backup_db.sh") | crontab -

echo "✅ Deployment completed!"
echo "🌐 Access your OSINT Bot System at: http://$(curl -s ifconfig.me)"
echo "🔧 Service status: sudo systemctl status osint-bots"
echo "📋 Logs: sudo journalctl -u osint-bots -f"
echo "🔄 Restart: sudo systemctl restart osint-bots"
echo "🧅 Tor status: sudo systemctl status tor"
echo "🐘 Database: postgresql://osint_user:secure_password_2024@localhost:5432/osint_db"
echo ""
echo "⚠️  IMPORTANT: Change the database password in .env file and PostgreSQL!"
echo "⚠️  Set up SSL certificates for HTTPS access"
echo "⚠️  Configure your domain name in nginx configuration"
