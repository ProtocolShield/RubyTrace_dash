#!/bin/bash

echo "🚀 OSINT Bot System Deployment Script"
echo "====================================="

# Update system
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install required packages
echo "🔧 Installing required packages..."
sudo apt install -y python3 python3-pip python3-venv nginx sqlite3 git curl wget

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
pip install flask flask-sqlalchemy flask-cors aiohttp asyncio beautifulsoup4 praw fake-useragent textblob nltk schedule langdetect tldextract PyPDF2 python-docx PyJWT

# Download NLTK data
echo "📖 Downloading NLTK data..."
python3 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('averaged_perceptron_tagger')"

# Create requirements.txt
echo "📝 Creating requirements.txt..."
cat > requirements.txt << 'EOF'
flask==2.3.3
flask-sqlalchemy==3.0.5
flask-cors==4.0.0
aiohttp==3.8.6
beautifulsoup4==4.12.2
praw==7.7.1
fake-useragent==1.4.0
textblob==0.17.1
nltk==3.8.1
schedule==1.2.0
langdetect==1.0.9
tldextract==5.1.1
PyPDF2==3.0.1
python-docx==1.1.0
PyJWT==2.8.0
EOF

# Create systemd service
echo "⚙️ Creating systemd service..."
sudo tee /etc/systemd/system/osint-bots.service > /dev/null << 'EOF'
[Unit]
Description=OSINT Bot System
After=network.target

[Service]
Type=simple
User=jux
WorkingDirectory=/opt/osint-bots
Environment=PATH=/opt/osint-bots/venv/bin
ExecStart=/opt/osint-bots/venv/bin/python api.py
Restart=always
RestartSec=10

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

# Create nginx configuration
echo "🌐 Setting up nginx..."
sudo tee /etc/nginx/sites-available/osint-bots > /dev/null << 'EOF'
server {
    listen 80;
    server_name 193.203.162.30;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Enable nginx site
sudo ln -sf /etc/nginx/sites-available/osint-bots /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo systemctl restart nginx

echo "✅ Deployment completed!"
echo "🌐 Access your OSINT Bot System at: http://193.203.162.30"
echo "🔧 Service status: sudo systemctl status osint-bots"
echo "📋 Logs: sudo journalctl -u osint-bots -f"
echo "🔄 Restart: sudo systemctl restart osint-bots"
