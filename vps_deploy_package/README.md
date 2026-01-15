# OSINT Bot System - VPS Deployment Package

## 🚀 Quick Deployment

1. **Upload files to your VPS:**
   ```bash
   scp -r vps_deploy_package/* jux@193.203.162.30:/opt/osint-bots/
   ```

2. **SSH into your VPS:**
   ```bash
   ssh jux@193.203.162.30
   ```

3. **Run the deployment script:**
   ```bash
   cd /opt/osint-bots
   chmod +x deploy_vps.sh
   ./deploy_vps.sh
   ```

4. **Access your system:**
   - Main Interface: http://193.203.162.30
   - Admin Panel: http://193.203.162.30/admin
   - Bot Management: http://193.203.162.30/admin/bots

## 📊 What Data Will Be Collected

### **Data Types:**
- **Raw Content**: HTML, text, JSON from websites
- **Structured Data**: Entities (people, organizations, tools, vulnerabilities)
- **Metadata**: URLs, timestamps, source information
- **Relationships**: Connections between entities

### **Expected Volume (Daily):**
- **Surface Web**: 100-1000+ articles/posts
- **Deep Web**: 50-500 paste entries
- **Dark Web**: 10-100 forum posts
- **OSINT Feeds**: 200-2000 structured records

### **Pre-configured Sources:**
- Hacker News
- Reddit cybersecurity communities
- NIST CVE database
- Tech blogs and forums
- Pastebin and clone sites

## 🔐 Adding Your Credentials

### **For Invite-Only Forums:**
```json
{
    "name": "Private Forum",
    "url": "https://private-forum.com",
    "auth_type": "login",
    "username": "your_username",
    "password": "your_password"
}
```

### **For Telegram/Discord:**
- **Telegram**: Add bot tokens for private groups
- **Discord**: Public servers only (ToS compliance)

## 🧪 Testing the System

### **1. Check Service Status:**
```bash
sudo systemctl status osint-bots
```

### **2. Start Data Collection:**
```bash
# Start Surface Web Bot
curl -X POST http://193.203.162.30/api/bots/surface/start

# Run collection cycle
curl -X POST http://193.203.162.30/api/bots/run-cycle \
  -H "Content-Type: application/json" \
  -d '{"bot_type": "surface", "source_type": "surface"}'
```

### **3. Monitor Data Collection:**
```bash
# View stats
curl http://193.203.162.30/api/data/stats

# Check logs
curl http://193.203.162.30/api/bot-logs
```

## 🔧 Management Commands

```bash
# View logs
sudo journalctl -u osint-bots -f

# Restart service
sudo systemctl restart osint-bots

# Stop service
sudo systemctl stop osint-bots

# Check nginx status
sudo systemctl status nginx
```

## 📁 File Structure

```
/opt/osint-bots/
├── api.py                 # Main Flask API
├── models.py              # Database models
├── bots/                  # Bot implementations
├── templates/             # HTML templates
├── static/                # CSS/JS files
├── deploy_vps.sh          # Deployment script
├── requirements.txt       # Python dependencies
└── venv/                  # Python virtual environment
```

## ⚠️ Important Notes

- **Legal Compliance**: Only collect from public sources
- **Rate Limiting**: Respect robots.txt and site policies
- **Storage**: Monitor disk space (data grows quickly)
- **Security**: Change default passwords and secure access
- **Backups**: Set up regular database backups

## 🆘 Troubleshooting

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

## 📞 Support

If you encounter issues:
1. Check service logs: `sudo journalctl -u osint-bots -f`
2. Verify file permissions
3. Check nginx configuration
4. Ensure all dependencies are installed

Your OSINT Bot System will be accessible at: **http://193.203.162.30**
