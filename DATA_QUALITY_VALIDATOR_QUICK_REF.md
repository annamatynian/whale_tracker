# Data Quality Validator - Quick Reference Card 📋

**Emergency Operator Guide - Keep This Handy!**

---

## Quick Health Check

```bash
# Run validator NOW
python data_quality_validator.py

# Check exit code
echo $?  # Linux/Mac
echo %errorlevel%  # Windows

# 0 = ✅ HEALTHY
# 1 = ⚠️  DEGRADED
# 2 = 🚨 CRITICAL
```

---

## Status Indicators

### ✅ HEALTHY (Score: 85-100)
**Action:** None required  
**Meaning:** All systems nominal, data quality excellent

### ⚠️ DEGRADED (Score: 60-84)
**Action:** Monitor closely, investigate warnings  
**Meaning:** Minor issues detected, may self-resolve

### 🚨 CRITICAL (Score: 0-59)
**Action:** IMMEDIATE INTERVENTION REQUIRED  
**Meaning:** Major corruption, accumulation analysis SUSPENDED

---

## Common Issues & Fixes

### Problem: "Incomplete Data - Only 72% coverage"

**Cause:** Missing hourly snapshots  

**Fix:**
```bash
# Check if SnapshotJob is running
python -c "from src.jobs.snapshot_job import SnapshotJob; print('OK')"

# Manual snapshot NOW
python run_manual_snapshot.py

# Check database
SELECT COUNT(*) FROM whale_balance_snapshots 
WHERE snapshot_timestamp >= NOW() - INTERVAL '24 hours';
```

---

### Problem: "Zero-balance whales detected"

**Cause:** RPC provider failures (Multicall returning 0x0)  

**Fix:**
```bash
# 1. Check RPC provider health
curl -X POST https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# 2. Switch to backup RPC (in .env)
ALCHEMY_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/BACKUP_KEY

# 3. Re-run snapshots
python run_manual_snapshot.py

# 4. Delete corrupted snapshots
DELETE FROM whale_balance_snapshots 
WHERE balance_eth = 0 
AND snapshot_timestamp >= NOW() - INTERVAL '1 hour';
```

---

### Problem: "High time drift - 15% average deviation"

**Cause:** Stale archive node cache or system clock issues  

**Fix:**
```bash
# 1. Check system clock
date  # Should match UTC time

# 2. Sync NTP (if off)
sudo ntpdate -s time.nist.gov  # Linux/Mac
w32tm /resync  # Windows

# 3. Check database time
SELECT NOW() AS db_time, 
       pg_postmaster_start_time() AS db_start;

# 4. Verify latest snapshot
SELECT MAX(snapshot_timestamp) FROM whale_balance_snapshots;
```

---

### Problem: "Suspicious 67% balance change"

**Cause:** Parser bug or RPC response corruption  

**Fix:**
```bash
# 1. Check on-chain (Etherscan)
# Look up whale address, verify actual balance

# 2. If legitimate (whale really dumped):
# → No action needed, signal is correct

# 3. If corrupted data:
# → Delete bad snapshots
DELETE FROM whale_balance_snapshots 
WHERE address = '0xSUSPICIOUS_WHALE' 
AND snapshot_timestamp BETWEEN 'START' AND 'END';

# → Re-snapshot
python -c "
from src.data.whale_list_provider import WhaleListProvider
from src.data.multicall_client import MulticallClient
# ... re-fetch balance for this whale
"
```

---

### Problem: "LST rate 0.85 outside bounds (0.90-1.10)"

**Cause:** CoinGecko API failure or actual depeg event  

**Fix:**
```bash
# 1. Verify CoinGecko API
curl "https://api.coingecko.com/api/v3/simple/price?ids=staked-ether&vs_currencies=eth"

# 2. Check Curve stETH/ETH pool
# Visit: https://curve.fi/#/ethereum/pools/steth/

# 3. If API down, manual override:
UPDATE accumulation_metrics 
SET steth_eth_rate = 0.9987 
WHERE steth_eth_rate IS NULL 
OR steth_eth_rate NOT BETWEEN 0.90 AND 1.10;

# 4. If REAL depeg:
# → This is a legit market event
# → Validator should flag it but not block analysis
# → Review [Depeg Risk] tag logic
```

---

## Alert Response Workflow

### When You Receive: "🚨 DATA QUALITY CRITICAL"

**Step 1:** Check validator output
```bash
python data_quality_validator.py | tee critical_report.txt
```

**Step 2:** Identify root cause
- Density < 70%? → Missing snapshots
- Zero balances? → RPC failure
- Time drift > 10%? → Clock/cache issue
- Outliers > 3? → Parser corruption
- LST violations? → API/depeg event

**Step 3:** Apply fix (see above)

**Step 4:** Re-run validator
```bash
python data_quality_validator.py
# Should return exit code 0 (HEALTHY)
```

**Step 5:** Resume accumulation analysis
```bash
# Analysis will auto-resume once validator returns HEALTHY
# Or manually trigger:
python run_collective_analysis.py
```

---

## Automation Examples

### Cron (Linux/Mac)
```bash
# Every 6 hours
0 */6 * * * cd /whale_tracker && python data_quality_validator.py >> logs/validator.log 2>&1
```

### Systemd Timer (Linux)
```ini
# /etc/systemd/system/whale-validator.timer
[Unit]
Description=Whale Tracker Data Quality Check

[Timer]
OnBootSec=5min
OnUnitActiveSec=6h

[Install]
WantedBy=timers.target
```

### Windows Task Scheduler
```powershell
$action = New-ScheduledTaskAction `
  -Execute "python" `
  -Argument "data_quality_validator.py" `
  -WorkingDirectory "C:\whale_tracker"

$trigger = New-ScheduledTaskTrigger `
  -Once -At 00:00 `
  -RepetitionInterval (New-TimeSpan -Hours 6)

Register-ScheduledTask `
  -Action $action `
  -Trigger $trigger `
  -TaskName "WhaleDataQuality"
```

---

## Logs & Reports

### View Recent Reports
```bash
# Last 5 validation reports
ls -lt logs/data_quality_reports/ | head -6

# View specific report
cat logs/data_quality_reports/report_20260120_163000.json | jq .
```

### Search Logs
```bash
# Find all CRITICAL events
grep "CRITICAL" logs/whale_tracker.log

# Find density issues
grep "Incomplete Data" logs/whale_tracker.log

# Find LST violations
grep "LST rate" logs/whale_tracker.log
```

---

## Emergency Contacts

**For Production Issues:**
- Telegram: @whale_tracker_ops_bot
- Email: ops@whale-tracker.io
- PagerDuty: Escalate to on-call engineer

**For Questions:**
- Documentation: `DATA_QUALITY_VALIDATOR_README.md`
- Source Code: `data_quality_validator.py`
- Integration Guide: `integration_example.py`

---

## Testing Your Fix

```bash
# After fixing an issue, verify:

# 1. Validator passes
python data_quality_validator.py
# Exit code: 0

# 2. Recent snapshots present
python -c "
from sqlalchemy import select, func
from models.database import WhaleBalanceSnapshot
from datetime import datetime, timedelta, timezone

# Check last hour
count = session.execute(
    select(func.count(WhaleBalanceSnapshot.id))
    .where(WhaleBalanceSnapshot.snapshot_timestamp >= 
           datetime.now(timezone.utc) - timedelta(hours=1))
).scalar()

print(f'Snapshots in last hour: {count}')
# Should be ~1000 (one per whale)
"

# 3. Accumulation score calculation works
python run_collective_analysis.py
# Should complete without errors
```

---

**Print This Card and Keep Near Monitoring Station! 🖨️**
