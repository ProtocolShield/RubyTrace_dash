# 🚀 Manual VPS Deployment Instructions

## **Step 1: SSH into your VPS**
```bash
ssh jux@193.203.162.30
# Password: Jux@Test123
```

## **Step 2: Create Project Directory**
```bash
sudo mkdir -p /opt/osint-bots
sudo chown jux:jux /opt/osint-bots
cd /opt/osint-bots
```

## **Step 3: Update System & Install Dependencies**
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nginx sqlite3 git curl wget
```

## **Step 4: Create Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

## **Step 5: Install Python Dependencies**
```bash
pip install flask==2.3.3 flask-sqlalchemy==3.0.5 flask-cors==4.0.0 aiohttp==3.8.6 beautifulsoup4==4.12.2 praw==7.7.1 fake-useragent==1.4.0 textblob==0.17.1 nltk==3.8.1 schedule==1.2.0 langdetect==1.0.9 tldextract==5.1.1 PyPDF2==3.0.1 python-docx==1.1.0 PyJWT==2.8.0 requests==2.31.0 lxml==4.9.3 html5lib==1.1 urllib3==2.0.7
```

## **Step 6: Download NLTK Data**
```bash
python3 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('averaged_perceptron_tagger')"
```

## **Step 7: Upload Files**
You need to upload the project files to `/opt/osint-bots/`. You can do this by:

### **Option A: Using SCP from your local machine**
```bash
# From your local machine, run:
scp -r vps_deploy_package/* jux@193.203.162.30:/opt/osint-bots/
```

### **Option B: Using Git (if you have a repository)**
```bash
git clone <your-repo-url> /opt/osint-bots/
```

### **Option C: Manual file creation**
Create the files manually on the VPS using nano/vim.

## **Step 8: Set File Permissions**
```bash
chmod +x deploy_vps.sh
```

## **Step 9: Run Deployment Script**
```bash
./deploy_vps.sh
```

## **Step 10: Test the System**
```bash
# Check if service is running
sudo systemctl status osint-bots

# Test the API
curl http://193.203.162.30/api/bots

# Access the web interface
# Open browser: http://193.203.162.30
```

## **Step 11: Start Data Collection**
```bash
# Start Surface Web Bot
curl -X POST http://193.203.162.30/api/bots/surface/start

# Run a collection cycle
curl -X POST http://193.203.162.30/api/bots/run-cycle \
  -H "Content-Type: application/json" \
  -d '{"bot_type": "surface", "source_type": "surface"}'
```

## **Step 12: Monitor Data Collection**
```bash
# View collected data stats
curl http://193.203.162.30/api/data/stats

# Check bot logs
curl http://193.203.162.30/api/bot-logs

# View service logs
sudo journalctl -u osint-bots -f
```

## **🔧 Management Commands**

```bash
# Restart service
sudo systemctl restart osint-bots

# Stop service
sudo systemctl stop osint-bots

# View logs
sudo journalctl -u osint-bots -f

# Check nginx status
sudo systemctl status nginx
```

## **📊 Expected Results**

### **Immediate (First 24 hours):**
- 100-500 articles collected from surface web
- 50-200 OSINT feed records
- Basic entity extraction working
- Database growing with raw data

### **After 1 week:**
- 1000+ articles and posts
- Entity relationships forming
- Search functionality working
- Performance metrics available

## **🌐 Access URLs**

- **Main Interface**: http://193.203.162.30
- **Admin Panel**: http://193.203.162.30/admin
- **Bot Management**: http://193.203.162.30/admin/bots

## **⚠️ Important Notes**

- **Legal Compliance**: Only collect from public sources
- **Rate Limiting**: Respect robots.txt and site policies
- **Storage**: Monitor disk space (data grows quickly)
- **Security**: Change default passwords and secure access
- **Backups**: Set up regular database backups

## **🆘 Troubleshooting**

### **Service Won't Start:**
```bash
sudo journalctl -u osint-bots -n 50
```

### **Port Already in Use:**
```bash
sudo netstat -tlnp | grep :5000
sudo kill -9 <PID>
```

### **Database Issues:**
```bash
cd /opt/osint-bots
source venv/bin/activate
python3 -c "from models import db; db.create_all()"
```

## **📞 Support**

If you encounter issues:
1. Check service logs: `sudo journalctl -u osint-bots -f`
2. Verify file permissions
3. Check nginx configuration
4. Ensure all dependencies are installed

Your OSINT Bot System will be accessible at: **http://193.203.162.30**


