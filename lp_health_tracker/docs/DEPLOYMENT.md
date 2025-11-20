# 🚀 Deployment Guide - LP Health Tracker

This guide covers deployment scenarios for different environments and use cases.

## 📋 Deployment Options

### 🏠 **Local Development**
Perfect for testing and development.

### ☁️ **Cloud VPS**
Recommended for production use with 24/7 monitoring.

### 🐳 **Docker Container**
Containerized deployment for easy scaling.

### 🏢 **Enterprise On-Premise**
Self-hosted solution for institutional compliance.

---

## 🏠 Local Development Deployment

### Prerequisites
```bash
# System requirements
Python 3.9+
Git 2.20+
4GB RAM (minimum)
1GB free disk space

# Check versions
python --version
git --version
```

### Setup Steps
```bash
# 1. Clone repository
git clone <repository-url>
cd lp_health_tracker

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\\Scripts\\activate
# Linux/macOS:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Setup environment
cp .env.example .env
nano .env  # Edit with your settings

# 6. Verify installation
python run.py --test-config
```

### Running Locally
```bash
# Start monitoring (foreground)
python run.py

# Run with debug logging
LOG_LEVEL=DEBUG python run.py

# Test without starting agent
python run.py --test-config
```

---

## ☁️ Cloud VPS Deployment

### Recommended Providers
- **DigitalOcean**: $5-10/month droplet
- **Vultr**: $2.50-6/month VPS
- **Linode**: $5-10/month instance
- **AWS EC2**: t3.micro (free tier eligible)

### Server Specifications

**Minimum Requirements:**
- **CPU**: 1 vCore
- **RAM**: 1GB
- **Storage**: 10GB SSD
- **Network**: 1TB transfer/month

**Recommended:**
- **CPU**: 2 vCores  
- **RAM**: 2GB
- **Storage**: 20GB SSD
- **Network**: Unlimited transfer

### VPS Setup

```bash
# 1. Connect to server
ssh root@your-server-ip

# 2. Update system
apt update && apt upgrade -y

# 3. Install Python and Git
apt install python3 python3-pip python3-venv git -y

# 4. Create user for app
useradd -m -s /bin/bash lptracker
usermod -aG sudo lptracker

# 5. Switch to app user
su - lptracker

# 6. Clone and setup application
git clone <repository-url>
cd lp_health_tracker
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 7. Configure environment
cp .env.example .env
nano .env  # Add your API keys

# 8. Test configuration
python run.py --test-config
```

### Production Service Setup

Create systemd service for automatic startup and management:

```bash
# Create service file
sudo nano /etc/systemd/system/lptracker.service
```

Service configuration:
```ini
[Unit]
Description=LP Health Tracker
After=network.target

[Service]
Type=simple
User=lptracker
WorkingDirectory=/home/lptracker/lp_health_tracker
Environment=PATH=/home/lptracker/lp_health_tracker/venv/bin
ExecStart=/home/lptracker/lp_health_tracker/venv/bin/python run.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable lptracker

# Start service
sudo systemctl start lptracker

# Check status
sudo systemctl status lptracker

# View logs
sudo journalctl -u lptracker -f
```

### Nginx Reverse Proxy (Optional)

If you plan to add a web interface later:

```bash
# Install Nginx
sudo apt install nginx -y

# Create configuration
sudo nano /etc/nginx/sites-available/lptracker
```

Nginx config:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/lptracker /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🐳 Docker Deployment

### Dockerfile
```dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements first (for layer caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Set environment variables
ENV PYTHONPATH=/app
ENV LOG_TO_FILE=true

# Run application
CMD ["python", "run.py"]
```

### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  lptracker:
    build: .
    container_name: lp_health_tracker
    restart: unless-stopped
    environment:
      - LOG_LEVEL=INFO
      - LOG_TO_FILE=true
    env_file:
      - .env
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - redis  # Optional: for caching

  redis:  # Optional: for advanced caching
    image: redis:7-alpine
    container_name: lptracker_redis
    restart: unless-stopped
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### Docker Commands
```bash
# Build and run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f lptracker

# Stop services
docker-compose down

# Update and restart
git pull
docker-compose build
docker-compose up -d
```

---

## 🏢 Enterprise On-Premise Deployment

### Architecture Components

```
Enterprise LP Health Tracker
├── Load Balancer (HAProxy/Nginx)
├── Application Servers (Multiple instances)
├── Database Cluster (PostgreSQL/MongoDB)
├── Cache Layer (Redis Cluster)
├── Monitoring (Prometheus/Grafana)
└── Backup System (Automated backups)
```

### High Availability Setup

**Application Servers:**
```bash
# Server 1
git clone <repository-url> /opt/lptracker-1
cd /opt/lptracker-1
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Server 2
git clone <repository-url> /opt/lptracker-2
cd /opt/lptracker-2
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Database Migration:**
```python
# config/enterprise_settings.py
DATABASE_URL = "postgresql://user:pass@db-cluster:5432/lptracker"
REDIS_URL = "redis://redis-cluster:6379/0"
```

**Load Balancer Configuration (HAProxy):**
```
backend lptracker_backend
    balance roundrobin
    server app1 10.0.1.10:8000 check
    server app2 10.0.1.11:8000 check
    server app3 10.0.1.12:8000 check
```

### Monitoring Setup

**Prometheus Configuration:**
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'lptracker'
    static_configs:
      - targets: ['app1:8000', 'app2:8000', 'app3:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

**Grafana Dashboard:**
- System metrics (CPU, memory, disk)
- Application metrics (positions monitored, alerts sent)
- Business metrics (IL detected, P&L tracked)

---

## 🔧 Configuration Management

### Environment Variables

**Production Environment:**
```env
# .env.production
DEFAULT_NETWORK=ethereum_mainnet
CHECK_INTERVAL_MINUTES=15
LOG_LEVEL=INFO
LOG_TO_FILE=true

# API Keys (secure storage)
INFURA_API_KEY=your_secure_infura_key
TELEGRAM_BOT_TOKEN=your_secure_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Performance settings
MAX_CONCURRENT_REQUESTS=10
API_TIMEOUT_SECONDS=30
CACHE_TTL_SECONDS=300
```

**Development Environment:**
```env
# .env.development
DEFAULT_NETWORK=ethereum_sepolia
CHECK_INTERVAL_MINUTES=5
LOG_LEVEL=DEBUG
LOG_TO_FILE=false

# Test API keys
INFURA_API_KEY=test_key
TELEGRAM_BOT_TOKEN=test_bot
```

### Security Considerations

**API Key Management:**
```bash
# Use environment-specific key files
cp .env.production.example .env.production
chmod 600 .env.production  # Secure permissions

# Or use secret management
export INFURA_API_KEY=$(vault kv get -field=api_key secret/lptracker)
```

**Network Security:**
```bash
# Firewall configuration
ufw allow 22    # SSH
ufw allow 80    # HTTP (if web interface)
ufw allow 443   # HTTPS
ufw deny incoming
ufw enable
```

---

## 📊 Monitoring & Maintenance

### Health Checks

**Application Health:**
```bash
# Check service status
sudo systemctl status lptracker

# Test configuration
python run.py --test-config

# Check recent logs
tail -f logs/lp_tracker.log
```

**System Health:**
```bash
# Monitor resources
htop
df -h
free -h

# Check network connectivity
ping 8.8.8.8
curl -I https://api.coingecko.com/
```

### Backup Strategy

**Configuration Backup:**
```bash
# Backup script (backup.sh)
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/lptracker_$DATE"

mkdir -p $BACKUP_DIR
cp -r data/ $BACKUP_DIR/
cp .env $BACKUP_DIR/
cp logs/*.log $BACKUP_DIR/

tar -czf "/backups/lptracker_backup_$DATE.tar.gz" $BACKUP_DIR
rm -rf $BACKUP_DIR

# Keep only last 30 backups
find /backups -name "lptracker_backup_*.tar.gz" -mtime +30 -delete
```

**Automated Backups:**
```bash
# Add to crontab
crontab -e

# Backup daily at 2 AM
0 2 * * * /home/lptracker/backup.sh
```

### Updates and Maintenance

**Update Process:**
```bash
# 1. Backup current version
./backup.sh

# 2. Pull latest changes
git pull origin main

# 3. Update dependencies
source venv/bin/activate
pip install -r requirements.txt

# 4. Test configuration
python run.py --test-config

# 5. Restart service
sudo systemctl restart lptracker

# 6. Verify operation
sudo systemctl status lptracker
tail -f logs/lp_tracker.log
```

**Rollback Plan:**
```bash
# If update fails, rollback
git reset --hard HEAD~1
sudo systemctl restart lptracker
```

---

## 🔍 Troubleshooting Deployment

### Common Issues

**Permission Errors:**
```bash
# Fix file permissions
chown -R lptracker:lptracker /home/lptracker/lp_health_tracker
chmod +x run.py
```

**Python Path Issues:**
```bash
# Add to .bashrc
export PYTHONPATH="/home/lptracker/lp_health_tracker:$PYTHONPATH"
```

**Service Won't Start:**
```bash
# Check service logs
sudo journalctl -u lptracker -n 50

# Check application logs
tail -f logs/lp_tracker.log

# Test manually
cd /home/lptracker/lp_health_tracker
source venv/bin/activate
python run.py --test-config
```

### Performance Optimization

**System Tuning:**
```bash
# Increase file descriptor limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Optimize network settings
echo "net.core.somaxconn = 65536" >> /etc/sysctl.conf
sysctl -p
```

**Application Tuning:**
```env
# .env optimizations
MAX_CONCURRENT_REQUESTS=20
API_TIMEOUT_SECONDS=15
CACHE_TTL_SECONDS=180
CHECK_INTERVAL_MINUTES=10
```

---

## 📈 Scaling Considerations

### Horizontal Scaling

**Multi-Instance Setup:**
- Deploy multiple instances with different wallet sets
- Use load balancer for web interface
- Shared database for historical data
- Centralized logging and monitoring

**Auto-Scaling (Kubernetes):**
```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lptracker
spec:
  replicas: 3
  selector:
    matchLabels:
      app: lptracker
  template:
    metadata:
      labels:
        app: lptracker
    spec:
      containers:
      - name: lptracker
        image: lptracker:latest
        env:
        - name: CHECK_INTERVAL_MINUTES
          value: "15"
```

### Vertical Scaling

**Resource Limits:**
```yaml
# docker-compose.yml
services:
  lptracker:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

---

## 🎯 Success Metrics

### Deployment KPIs

**Technical Metrics:**
- Uptime: >99.5%
- Response time: <30 seconds for alerts
- Error rate: <1% of monitoring cycles
- Resource usage: <80% CPU/memory

**Business Metrics:**
- Positions monitored: Track growth
- Alerts sent: Accuracy and timeliness
- User satisfaction: Response time to issues
- Cost efficiency: Infrastructure costs vs. value

---

**🚀 Ready to deploy? Choose your deployment method and follow the guides above!**

**Need help?** → See [Troubleshooting Guide](docs/TROUBLESHOOTING.md) or create an issue.