# 🔧 Troubleshooting Guide - LP Health Tracker

This guide helps you diagnose and fix common issues with LP Health Tracker.

## 🚨 Quick Diagnostics

### First Steps
```bash
# 1. Test your configuration
python run.py --test-config

# 2. Check recent logs
tail -f logs/lp_tracker.log

# 3. Verify Python environment
python --version  # Should be 3.9+
pip list | grep -E "(web3|requests|asyncio)"

# 4. Test network connectivity
ping 8.8.8.8
curl -I https://api.coingecko.com/
```

---

## 🔍 Common Issues & Solutions

### ❌ Configuration Errors

#### Issue: "TELEGRAM_BOT_TOKEN is required"
**Symptoms:**
```
❌ Configuration Errors Found:
   • TELEGRAM_BOT_TOKEN is required
   • TELEGRAM_CHAT_ID is required
```

**Solutions:**
1. **Check .env file exists:**
   ```bash
   ls -la .env
   # If missing: cp .env.example .env
   ```

2. **Verify .env format:**
   ```env
   # Correct format
   TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklmnop"
   TELEGRAM_CHAT_ID="987654321"
   
   # Wrong format (no quotes needed, but quotes are OK)
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklmnop
   ```

3. **Get Telegram credentials:**
   ```bash
   # Create bot: message @BotFather on Telegram
   # Send: /newbot
   # Follow instructions to get token
   
   # Get Chat ID: message @userinfobot
   # Send: /start
   # Copy the ID number
   ```

#### Issue: "At least one RPC provider API key is required"
**Solutions:**
1. **Get free Infura API key:**
   - Visit [infura.io](https://app.infura.io/)
   - Create account and project
   - Copy Project ID to INFURA_API_KEY

2. **Alternative - Get Alchemy API key:**
   - Visit [alchemy.com](https://dashboard.alchemy.com/)
   - Create account and app
   - Copy API Key to ALCHEMY_API_KEY

3. **Use public endpoints (not recommended for production):**
   ```env
   # Remove or comment out API keys to use public endpoints
   # INFURA_API_KEY=""
   # ALCHEMY_API_KEY=""
   ```

### ❌ Connection Issues

#### Issue: "Web3 connection failed"
**Symptoms:**
```
❌ Failed to initialize Web3 connection
Error: HTTPSConnectionPool(...): Max retries exceeded
```

**Solutions:**
1. **Check API key validity:**
   ```bash
   # Test Infura connection
   curl "https://mainnet.infura.io/v3/YOUR_API_KEY" \
     -X POST \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
   ```

2. **Verify network setting:**
   ```env
   # Make sure network matches your API key
   DEFAULT_NETWORK="ethereum_mainnet"  # or ethereum_sepolia for testnet
   ```

3. **Check firewall/proxy:**
   ```bash
   # Test HTTPS connectivity
   curl -I https://mainnet.infura.io
   curl -I https://eth-mainnet.alchemyapi.io
   ```

4. **Try alternative provider:**
   ```env
   # Switch from Infura to Alchemy or vice versa
   ALCHEMY_API_KEY="your_alchemy_key"
   # INFURA_API_KEY=""  # Comment out
   ```

#### Issue: "Telegram bot not responding"
**Symptoms:**
- No startup message received
- Alerts not being sent
- Test configuration passes but no messages

**Solutions:**
1. **Verify bot token:**
   ```bash
   # Test bot API
   curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe"
   # Should return bot information
   ```

2. **Check Chat ID:**
   ```bash
   # Send test message
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage" \
     -d "chat_id=<YOUR_CHAT_ID>&text=Test message"
   ```

3. **Start conversation with bot:**
   - Find your bot in Telegram
   - Send `/start` message
   - Bot must receive at least one message to send responses

4. **Check bot permissions:**
   - Bot must be able to send messages
   - If using group chat, add bot as admin

### ❌ Position Management Issues

#### Issue: "No positions found"
**Symptoms:**
```
❌ No positions found.
💡 Use 'python run.py --add-position' to add your first position.
```

**Solutions:**
1. **Add position interactively:**
   ```bash
   python run.py --add-position
   # Follow prompts to add position
   ```

2. **Create from example:**
   ```bash
   cp data/positions.json.example data/positions.json
   nano data/positions.json  # Edit with your data
   ```

3. **Verify file exists and is valid:**
   ```bash
   ls -la data/positions.json
   python -m json.tool data/positions.json  # Validate JSON
   ```

#### Issue: "Position not found" or "Invalid position data"
**Solutions:**
1. **Check position format:**
   ```json
   {
     "name": "WETH-USDC Uniswap V2",
     "pair_address": "0xB4e16d0168e52d35CaCD2b6464f00d6eB9002C6D",
     "token_a_symbol": "WETH",
     "token_b_symbol": "USDC",
     "initial_liquidity_a": 1.0,
     "initial_liquidity_b": 2000.0,
     "initial_price_a_usd": 2000.0,
     "initial_price_b_usd": 1.0,
     "wallet_address": "0xYourWalletAddress",
     "network": "ethereum_mainnet",
     "il_alert_threshold": 0.05,
     "protocol": "uniswap_v2",
     "active": true
   }
   ```

2. **Validate wallet address:**
   ```bash
   # Check address format (should start with 0x and be 42 characters)
   echo "0xYourWalletAddress" | grep -E "^0x[a-fA-F0-9]{40}$"
   ```

3. **Verify pair address:**
   - Use Etherscan to verify LP pair contract address
   - Make sure it's the correct protocol (V2, not V3)

### ❌ Import and Module Issues

#### Issue: "ModuleNotFoundError: No module named 'src'"
**Symptoms:**
```python
ModuleNotFoundError: No module named 'src.data_analyzer'
```

**Solutions:**
1. **Run from correct directory:**
   ```bash
   cd lp_health_tracker  # Make sure you're in project root
   python run.py
   ```

2. **Check Python path:**
   ```bash
   # Add to environment
   export PYTHONPATH="$(pwd):$PYTHONPATH"
   python run.py
   ```

3. **Use relative imports in tests:**
   ```bash
   # Run tests from project root
   pytest tests/
   ```

#### Issue: "ImportError: cannot import name 'X' from 'Y'"
**Solutions:**
1. **Update dependencies:**
   ```bash
   pip install -r requirements.txt --upgrade
   ```

2. **Check Python version:**
   ```bash
   python --version  # Must be 3.9+
   ```

3. **Reinstall in virtual environment:**
   ```bash
   deactivate
   rm -rf venv
   python -m venv venv
   source venv/bin/activate  # or venv\\Scripts\\activate on Windows
   pip install -r requirements.txt
   ```

### ❌ Data and API Issues

#### Issue: "Failed to get token price" or "API rate limit exceeded"
**Solutions:**
1. **Check API limits:**
   ```bash
   # CoinGecko free tier: 50 requests/minute
   # Consider getting API key for higher limits
   ```

2. **Reduce check frequency:**
   ```env
   CHECK_INTERVAL_MINUTES=30  # Instead of 15 or 5
   ```

3. **Add API key for CoinGecko:**
   ```env
   COINGECKO_API_KEY="your_api_key"  # Pro plan
   ```

4. **Use mock data for testing:**
   ```python
   # In your test setup
   from src.data_providers import MockDataProvider
   provider = MockDataProvider({'WETH': 2000.0, 'USDC': 1.0})
   ```

#### Issue: "IL calculation returns unexpected values"
**Solutions:**
1. **Check price inputs:**
   ```python
   # Debug IL calculation
   print(f"Initial ratio: {initial_price_a / initial_price_b}")
   print(f"Current ratio: {current_price_a / current_price_b}")
   ```

2. **Verify calculation:**
   ```python
   # Manual IL calculation
   price_ratio = (current_price_a / current_price_b) / (initial_price_a / initial_price_b)
   il = 2 * (math.sqrt(price_ratio) / (1 + price_ratio)) - 1
   il_loss = abs(il) if il < 0 else 0.0
   ```

3. **Check for edge cases:**
   - Zero prices
   - Negative ratios
   - Very large price changes

---

## 🧪 Testing and Debugging

### Debug Mode
```bash
# Enable debug logging
LOG_LEVEL=DEBUG python run.py

# Run specific test
pytest tests/test_data_analyzer.py -v -s

# Debug with breakpoints
pytest tests/test_specific.py -v -s --pdb
```

### Manual Testing
```python
# Test IL calculation manually
from src.data_analyzer import ImpermanentLossCalculator

calc = ImpermanentLossCalculator()
il = calc.calculate_impermanent_loss(2000.0, 2500.0)  # ETH price +25%
print(f"IL: {il:.4f} ({il:.2%})")  # Should be ~0.0125 (1.25%)
```

### Check Dependencies
```bash
# Verify all required packages
pip check

# List installed packages
pip list

# Compare with requirements
pip install -r requirements.txt --dry-run
```

---

## 🔧 Performance Issues

### High Memory Usage
**Solutions:**
1. **Reduce check frequency:**
   ```env
   CHECK_INTERVAL_MINUTES=30
   ```

2. **Limit concurrent requests:**
   ```env
   MAX_CONCURRENT_REQUESTS=5
   ```

3. **Clear logs periodically:**
   ```bash
   # Rotate logs
   truncate -s 0 logs/lp_tracker.log
   ```

### Slow Response Times
**Solutions:**
1. **Use faster RPC provider:**
   ```env
   # Alchemy is often faster than Infura
   ALCHEMY_API_KEY="your_key"
   ```

2. **Optimize timeout settings:**
   ```env
   API_TIMEOUT_SECONDS=15  # Reduce from 30
   ```

3. **Enable caching:**
   ```env
   CACHE_TTL_SECONDS=300  # 5 minutes
   ```

---

## 🛠️ System-Level Issues

### Permission Errors (Linux/macOS)
```bash
# Fix file permissions
chmod +x run.py
chown -R $USER:$USER .

# Fix Python executable permissions
chmod +x venv/bin/python
```

### Port Already in Use
```bash
# Find process using port
lsof -i :8000
# Kill process if needed
kill -9 <PID>
```

### Disk Space Issues
```bash
# Check disk usage
df -h

# Clean logs
find logs/ -name "*.log" -mtime +7 -delete

# Clean Python cache
find . -name "__pycache__" -type d -exec rm -rf {} +
```

---

## 📊 Monitoring and Health Checks

### System Health
```bash
# Check system resources
top
htop
free -h
df -h

# Check network
netstat -an | grep :8000
ss -tulpn | grep :8000
```

### Application Health
```bash
# Check service status (if using systemd)
sudo systemctl status lptracker

# Check process
ps aux | grep "python.*run.py"

# Test configuration
python run.py --test-config
```

### Log Analysis
```bash
# View recent errors
grep -i error logs/lp_tracker.log | tail -20

# Watch logs in real-time
tail -f logs/lp_tracker.log

# Count error types
grep -i error logs/lp_tracker.log | cut -d' ' -f4- | sort | uniq -c
```

---

## 🚨 Emergency Procedures

### Service Won't Start
1. **Check configuration:**
   ```bash
   python run.py --test-config
   ```

2. **Check logs:**
   ```bash
   tail -50 logs/lp_tracker.log
   ```

3. **Restart from clean state:**
   ```bash
   # Stop service
   sudo systemctl stop lptracker
   
   # Clear logs
   truncate -s 0 logs/lp_tracker.log
   
   # Test manually
   python run.py --test-config
   
   # Start service
   sudo systemctl start lptracker
   ```

### Data Corruption
1. **Backup current state:**
   ```bash
   cp data/positions.json data/positions.json.backup
   ```

2. **Restore from example:**
   ```bash
   cp data/positions.json.example data/positions.json
   # Edit with your positions
   ```

3. **Validate JSON:**
   ```bash
   python -m json.tool data/positions.json
   ```

### Network Issues
1. **Test connectivity:**
   ```bash
   curl -I https://api.coingecko.com/
   curl -I https://mainnet.infura.io/
   ```

2. **Use alternative providers:**
   ```env
   # Switch to backup provider
   ALCHEMY_API_KEY="backup_key"
   ```

3. **Use offline mode (if implemented):**
   ```env
   OFFLINE_MODE=true
   ```

---

## 📞 Getting Help

### Self-Diagnosis Checklist
- [ ] Configuration file exists and is valid
- [ ] API keys are correct and active
- [ ] Network connectivity is working
- [ ] Python environment is correct (3.9+)
- [ ] All dependencies are installed
- [ ] Telegram bot is properly configured
- [ ] Log files show specific error messages

### Reporting Issues
When creating a GitHub issue, include:

1. **Environment information:**
   ```bash
   python --version
   pip list | grep -E "(web3|requests|aiohttp)"
   uname -a  # Linux/macOS
   ```

2. **Configuration (anonymized):**
   ```env
   DEFAULT_NETWORK=ethereum_mainnet
   CHECK_INTERVAL_MINUTES=15
   # Don't include actual API keys!
   ```

3. **Error logs:**
   ```bash
   # Last 50 lines of logs
   tail -50 logs/lp_tracker.log
   ```

4. **Steps to reproduce:**
   - What you were trying to do
   - What command you ran
   - What you expected to happen
   - What actually happened

### Contact Channels
- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and help
- **Documentation**: Check all files in `/docs` folder

---

## 🎯 Prevention Tips

### Best Practices
1. **Always test configuration** before deployment
2. **Monitor logs regularly** for early warning signs
3. **Keep backups** of working configurations
4. **Update gradually** - test in development first
5. **Monitor resource usage** to prevent system overload

### Regular Maintenance
```bash
# Weekly maintenance script
#!/bin/bash

# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python packages
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Clean old logs
find logs/ -name "*.log.*" -mtime +30 -delete

# Test configuration
python run.py --test-config

# Restart service
sudo systemctl restart lptracker
```

---

**🚀 Still having issues? Create a detailed GitHub issue with the information above!**