# 🗄️ PostgreSQL/Neon Database Configuration

This guide explains how to configure your OSINT platform to use PostgreSQL with Neon database.

## 📋 Prerequisites

- ✅ OSINT platform already deployed on VPS
- ✅ Neon PostgreSQL database account
- ✅ Database credentials (connection string)

## 🚀 Quick Setup

### Option 1: Using the Automated Script

1. **Upload the PostgreSQL deployment script to your VPS:**
   ```bash
   scp postgresql_deployment.sh jux@193.203.162.30:/home/jux/
   ```

2. **Run the PostgreSQL configuration script:**
   ```bash
   ssh jux@193.203.162.30
   chmod +x postgresql_deployment.sh
   sudo bash postgresql_deployment.sh
   ```

### Option 2: Manual Configuration

1. **Install PostgreSQL client:**
   ```bash
   sudo apt update
   sudo apt install postgresql-client postgresql-contrib
   ```

2. **Install Python PostgreSQL adapter:**
   ```bash
   pip3 install psycopg2-binary
   ```

3. **Configure environment variables:**
   ```bash
   cd /opt/osint-bots
   cat > .env << 'EOF'
   DATABASE_URL=postgresql://neondb_owner:npg_2uJ7LoQrHpSe@ep-square-haze-a815v283-pooler.eastus2.azure.neon.tech/Radar-db?sslmode=require&channel_binding=require
   FLASK_ENV=production
   SECRET_KEY=your-secret-key-change-in-production
   EOF
   ```

4. **Test the connection:**
   ```bash
   python3 -c "
   import os
   os.environ['DATABASE_URL'] = 'postgresql://neondb_owner:npg_2uJ7LoQrHpSe@ep-square-haze-a815v283-pooler.eastus2.azure.neon.tech/Radar-db?sslmode=require&channel_binding=require'
   from database import test_postgresql_connection
   success, message = test_postgresql_connection()
   print(f'Connection test: {message}')
   "
   ```

5. **Restart the service:**
   ```bash
   sudo systemctl restart osint-bots
   ```

## 🧪 Testing the Configuration

### Test Database Connection

```bash
# Test from local machine
python3 test_postgresql.py

# Test from VPS
python3 -c "from postgresql_config import test_neon_connection; print(test_neon_connection())"
```

### Check Service Status

```bash
sudo systemctl status osint-bots
sudo journalctl -u osint-bots -f
```

### Verify Database Usage

```bash
# Check if the application is using PostgreSQL
python3 -c "
from database import get_db_url
print('Database URL:', get_db_url())
"
```

## 📊 Database Information

### Connection Details
- **Host:** ep-square-haze-a815v283-pooler.eastus2.azure.neon.tech
- **Database:** Radar-db
- **User:** neondb_owner
- **SSL Mode:** require
- **Channel Binding:** require

### REST API Endpoint
- **URL:** https://ep-square-haze-a815v283.apirest.eastus2.azure.neon.tech/Radar-db/rest/v1

## 🔧 Configuration Files

### Environment Configuration (`.env.postgresql`)
```bash
# PostgreSQL Configuration for OSINT Platform
DATABASE_URL=postgresql://neondb_owner:npg_2uJ7LoQrHpSe@ep-square-haze-a815v283-pooler.eastus2.azure.neon.tech/Radar-db?sslmode=require&channel_binding=require
FLASK_ENV=production
SECRET_KEY=your-secret-key-change-this-in-production
LOG_LEVEL=INFO
TOR_ENABLED=true
TOR_SOCKS_PORT=9050
TOR_CONTROL_PORT=9051
```

### Python Configuration (`postgresql_config.py`)
```python
# Neon PostgreSQL Database Configuration
NEON_DATABASE_URL = "postgresql://neondb_owner:npg_2uJ7LoQrHpSe@ep-square-haze-a815v283-pooler.eastus2.azure.neon.tech/Radar-db?sslmode=require&channel_binding=require"
NEON_REST_API_URL = "https://ep-square-haze-a815v283.apirest.eastus2.azure.neon.tech/Radar-db/rest/v1"
```

## 🛠️ Troubleshooting

### Common Issues

1. **Connection Timeout**
   - Check your internet connection
   - Verify Neon database is active
   - Check firewall settings

2. **SSL Connection Error**
   - Ensure SSL mode is set to 'require'
   - Check channel binding configuration
   - Verify certificate validity

3. **Authentication Error**
   - Verify username and password
   - Check database user permissions
   - Ensure database exists

### Debug Commands

```bash
# Test direct PostgreSQL connection
psql "postgresql://neondb_owner:npg_2uJ7LoQrHpSe@ep-square-haze-a815v283-pooler.eastus2.azure.neon.tech/Radar-db?sslmode=require&channel_binding=require"

# Check application logs
sudo journalctl -u osint-bots -n 50

# Test database engine creation
python3 -c "from database import create_db_engine; engine = create_db_engine(); print('Engine created successfully')"
```

## 📈 Monitoring

### Database Performance
- Monitor connection pool usage
- Check query performance in Neon dashboard
- Set up alerts for connection issues

### Application Logs
```bash
# View recent logs
sudo journalctl -u osint-bots -n 100

# Follow logs in real-time
sudo journalctl -u osint-bots -f

# Filter database-related logs
sudo journalctl -u osint-bots | grep -i database
```

## 🔒 Security Considerations

1. **Connection Security**
   - Always use SSL encryption
   - Enable channel binding
   - Use strong passwords

2. **Access Control**
   - Limit database user permissions
   - Use firewall rules
   - Monitor access logs

3. **Data Protection**
   - Regular backups
   - Encryption at rest
   - Access logging

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify your Neon database credentials
3. Test the connection using the test scripts
4. Check application and system logs
5. Ensure all prerequisites are met

## 🎉 Success Indicators

Your PostgreSQL configuration is successful when:

- ✅ Database connection test passes
- ✅ Application starts without database errors
- ✅ Data is being stored in PostgreSQL
- ✅ Service status shows no database-related errors
- ✅ Logs show successful database operations

---

**🎊 Congratulations! Your OSINT platform is now configured to use PostgreSQL with Neon database!**
