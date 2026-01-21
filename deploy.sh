#!/bin/bash
# Whale Tracker - Fresh EC2 Setup + Swap for t3.micro (1GB RAM)

set -e
echo "🐋 WHALE TRACKER - EC2 SETUP"

# 1. Create swap (для стабильности на 1GB RAM)
if [ ! -f /swapfile ]; then
    echo "💾 Creating 2GB swap..."
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

# 2. System update
sudo apt update && sudo apt upgrade -y

# 3. Install dependencies
sudo apt install -y python3 python3-pip python3-venv git nodejs npm postgresql-client
sudo npm install -g pm2

# 4. Clone project
cd ~
if [ ! -d "whale-tracker" ]; then
    git clone YOUR_GITHUB_URL whale-tracker
fi
cd whale-tracker

# 5. Python setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 6. Create .env
cp .env.example .env
echo "⚠️  Edit .env: nano .env"

# 7. PM2 setup
pm2 start ecosystem.config.js
pm2 save
pm2 startup
