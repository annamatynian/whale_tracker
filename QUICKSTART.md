# 🚀 EC2 QUICK START

## 1. CREATE EC2 (AWS Console)
```
Instance: t3.micro
AMI: Ubuntu 22.04 LTS
Storage: 15 GB
Security Group: Allow SSH (22), HTTPS (443)
```

## 2. CONNECT & DEPLOY
```bash
# SSH или Session Manager
git clone YOUR_REPO whale-tracker
cd whale-tracker
chmod +x deploy.sh
./deploy.sh

# Edit credentials
nano .env

# Start
pm2 restart whale-tracker-scheduler
```

## 3. VERIFY
```bash
pm2 logs whale-tracker-scheduler
```

**Получишь push в Telegram!** 📱

---

## 📋 .ENV TEMPLATE
```bash
DB_HOST=your-rds.amazonaws.com
DB_PASSWORD=your_pass
ETH_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/KEY
TELEGRAM_BOT_TOKEN=8450952201:AAGbnQ6lhcI-fBSO-Vwmxyi-BjPx7nHwKsE
TELEGRAM_CHAT_ID=764547167
ENABLE_TELEGRAM=True
```

---

## 💰 COST
**FREE** (t3.micro 750h/month)

## 📊 RESOURCES  
RAM: ~200MB + 2GB swap ✅
