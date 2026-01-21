# Data Quality Validator - Cyberpunk Edition 🔥⚡

**Comprehensive data integrity monitoring for Whale Tracker database**

## Overview

The Data Quality Validator is a critical component that ensures the integrity of whale tracking data by detecting and reporting anomalies across five key dimensions:

1. **Density Check** - Validates snapshot coverage completeness
2. **Precision Check** - Detects zero-balance corruption from RPC failures
3. **Time Drift** - Identifies stale data from archive node issues
4. **Statistical Outliers** - Flags impossible balance changes
5. **LST Consistency** - Validates stETH/ETH rate sanity

## Why This Matters

From **WHALES_ANALYSIS.docx**:
> "Масштабные перемещения активов, такие как переводы холодного хранения или подготовка к Proof-of-Reserves, часто ошибочно интерпретируются рынком как начало крупных продаж."

**Translation:** Large asset movements like cold storage transfers are often misinterpreted as major sell-offs.

The validator prevents these false positives by identifying technical noise BEFORE it triggers production alerts.

## Installation

No additional dependencies required - uses existing Whale Tracker infrastructure:

```bash
# Already installed via requirements.txt
sqlalchemy
asyncpg
```

## Usage

### Command Line

```bash
# Run validation and get JSON report
python data_quality_validator.py

# Exit codes:
# 0 = HEALTHY (all systems nominal)
# 1 = DEGRADED (minor issues detected)
# 2 = CRITICAL (manual intervention required)
```

### Programmatic Usage

```python
from data_quality_validator import DataQualityValidator, HealthStatus
from models.db_connection import get_session

async def check_data_health():
    async with get_session() as session:
        validator = DataQualityValidator(session)
        report = await validator.run_all_checks()
        
        if report["overall_status"] == HealthStatus.CRITICAL.value:
            # Trigger alert to ops team
            await send_pager_duty_alert(report)
        
        return report
```

### Integration with Main Loop

Add to `main.py` for periodic validation:

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from data_quality_validator import DataQualityValidator

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', hours=6)  # Every 6 hours
async def validate_data_quality():
    async with get_session() as session:
        validator = DataQualityValidator(session)
        report = await validator.run_all_checks()
        
        # Log to monitoring dashboard
        logger.info(f"Data Quality: {report['overall_status']} ({report['overall_score']:.1f}/100)")
        
        # Send Telegram alert if critical
        if report["overall_status"] == "critical":
            await telegram_notifier.send_critical_alert(
                f"🚨 DATA QUALITY CRITICAL\n"
                f"Score: {report['overall_score']:.1f}/100\n"
                f"Issues: {report['summary']['critical_issues']}"
            )

scheduler.start()
```

## Validation Checks Explained

### 1. Density Check

**Problem:** Missing hourly snapshots create "holes" in time-series data.

**Algorithm:**
```
Expected snapshots = unique_whales × 24 hours
Actual snapshots = COUNT(*) WHERE timestamp >= now - 24h
Density = (actual / expected) × 100
```

**Thresholds:**
- ✅ **HEALTHY**: Density ≥ 85%
- ⚠️ **DEGRADED**: Density 70-85%
- 🚨 **CRITICAL**: Density < 70%

**Example Output:**
```
🔬 CHECK 1/5: Snapshot Density Analysis...
  ├─ Unique Whales: 987
  ├─ Expected Snapshots: 23,688
  ├─ Actual Snapshots: 20,134
  └─ Density: 85.01% [HEALTHY]
```

### 2. Precision Check

**Problem:** Multicall RPC failures return `0x0` instead of real balance, creating false "whale exits".

**Detection:** Known whales should NEVER have `balance_eth = 0`

**Thresholds:**
- ✅ **HEALTHY**: 0 zero-balance whales
- ⚠️ **DEGRADED**: 1-5 zero balances (recent RPC hiccups)
- 🚨 **CRITICAL**: >5 zero balances (systemic RPC failure)

**Example Output:**
```
🔬 CHECK 2/5: Precision Integrity Validation...
  ├─ Zero-Balance Whales: 2
  └─ Status: [DEGRADED]

[WARNING] Whale 0x1234abcd... has 3 zero-balance snapshots (likely RPC cache miss)
```

### 3. Time Drift

**Problem:** Stale data from archive node cache or block reorgs.

**Algorithm:**
```
Expected block time = 12 seconds (Ethereum post-merge)
For each snapshot:
  expected_block_time = ref_time - (ref_block - current_block) × 12s
  drift = |snapshot_time - expected_block_time|
  drift_pct = (drift / 720s) × 100  # 720s = 60 blocks
```

**Thresholds:**
- ✅ **HEALTHY**: Avg drift < 5%
- ⚠️ **DEGRADED**: Avg drift 5-10%
- 🚨 **CRITICAL**: Avg drift > 10%

**Example Output:**
```
🔬 CHECK 3/5: Time Drift Analysis...
  ├─ Sample Size: 100
  ├─ Average Drift: 3.42%
  ├─ Max Drift: 8.91%
  └─ Status: [HEALTHY]
```

### 4. Statistical Outliers

**Problem:** Parser bugs or RPC corruption create phantom "dumps" without on-chain proof.

**Detection:** Balance changes >50% per hour are physiologically impossible without visible transactions.

**Thresholds:**
- ✅ **HEALTHY**: 0 outliers
- ⚠️ **DEGRADED**: 1-3 outliers (isolated glitch)
- 🚨 **CRITICAL**: >3 outliers (systemic corruption)

**Example Output:**
```
🔬 CHECK 4/5: Statistical Outlier Detection...
  ├─ Whales Checked: 156
  ├─ Outliers Found: 1
  └─ Status: [DEGRADED]

[WARNING] Suspicious 67.3% balance change for 0x9876fedc...
  (1250.45 → 409.12 ETH)
```

### 5. LST Consistency

**Problem:** Corrupted stETH/ETH rates block `[Depeg Risk]` tag calculation.

**Historical Bounds (2022-2025):**
- Lowest: 0.9329 (Terra/Luna crisis)
- Highest: 1.0012 (normal operations)
- Safety range: 0.90 ≤ rate ≤ 1.10

**Thresholds:**
- ✅ **HEALTHY**: All rates in bounds
- ⚠️ **DEGRADED**: 1-2 violations
- 🚨 **CRITICAL**: >2 violations

**Example Output:**
```
🔬 CHECK 5/5: LST Consistency Validation...
  ├─ Metrics Checked: 24
  ├─ Avg Rate: 0.9987
  ├─ Rate Range: 0.9956 - 1.0023
  ├─ Violations: 0
  └─ Status: [HEALTHY]
```

## JSON Report Format

```json
{
  "overall_status": "healthy",
  "overall_score": 92.5,
  "checks": [
    {
      "check_name": "snapshot_density",
      "status": "healthy",
      "score": 100.0,
      "issues": [],
      "metrics": {
        "density_pct": 87.3,
        "unique_whales": 987,
        "expected_snapshots": 23688,
        "actual_snapshots": 20674,
        "missing_snapshots": 3014
      },
      "timestamp": "2026-01-20T16:30:00Z"
    }
    // ... 4 more checks
  ],
  "summary": {
    "total_issues": 2,
    "critical_issues": 0,
    "warnings": 2,
    "checks_passed": 4,
    "checks_failed": 0
  },
  "timestamp": "2026-01-20T16:30:15Z"
}
```

## Dashboard Integration

The validator outputs cyberpunk-styled logs perfect for terminal dashboards:

```
╔═══════════════════════════════════════════════════════════╗
║   WHALE TRACKER - DATA QUALITY VALIDATION SYSTEM          ║
║   Cyberpunk Edition 🔥⚡                                  ║
╚═══════════════════════════════════════════════════════════╝

🔍 INITIATING DATA QUALITY SCAN...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔬 CHECK 1/5: Snapshot Density Analysis...
  ├─ Unique Whales: 987
  ├─ Expected Snapshots: 23,688
  ├─ Actual Snapshots: 20,134
  └─ Density: 85.01% [HEALTHY]

🔬 CHECK 2/5: Precision Integrity Validation...
  ├─ Zero-Balance Whales: 0
  └─ Status: [HEALTHY]

🔬 CHECK 3/5: Time Drift Analysis...
  ├─ Sample Size: 100
  ├─ Average Drift: 3.42%
  ├─ Max Drift: 8.91%
  └─ Status: [HEALTHY]

🔬 CHECK 4/5: Statistical Outlier Detection...
  ├─ Whales Checked: 156
  ├─ Outliers Found: 0
  └─ Status: [HEALTHY]

🔬 CHECK 5/5: LST Consistency Validation...
  ├─ Metrics Checked: 24
  ├─ Avg Rate: 0.9987
  ├─ Rate Range: 0.9956 - 1.0023
  ├─ Violations: 0
  └─ Status: [HEALTHY]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 SCAN COMPLETE - STATUS: HEALTHY
📊 OVERALL SCORE: 100.0/100
⚠️  TOTAL ISSUES: 0
```

## Automation Examples

### 1. Cron Job (Linux/Mac)

```bash
# Add to crontab (runs every 6 hours)
0 */6 * * * cd /path/to/whale_tracker && python data_quality_validator.py | tee -a logs/data_quality.log
```

### 2. Windows Task Scheduler

```powershell
# Create scheduled task (PowerShell)
$action = New-ScheduledTaskAction -Execute "python" -Argument "data_quality_validator.py" -WorkingDirectory "C:\whale_tracker"
$trigger = New-ScheduledTaskTrigger -Once -At 00:00 -RepetitionInterval (New-TimeSpan -Hours 6)
Register-ScheduledTask -Action $action -Trigger $trigger -TaskName "WhaleTrackerDataQuality"
```

### 3. Docker Health Check

```dockerfile
# Add to Dockerfile
HEALTHCHECK --interval=6h --timeout=30s --retries=3 \
  CMD python data_quality_validator.py || exit 1
```

## Performance Considerations

- **Execution Time:** ~5-15 seconds (depends on database size)
- **Memory Usage:** <50 MB (uses async streaming queries)
- **Database Impact:** Read-only queries with proper indexes
- **Recommended Frequency:** Every 6 hours (or after major market events)

## Troubleshooting

### Common Issues

**Problem:** "No snapshots found in last 24h"
```
Solution: Verify SnapshotJob is running hourly
Check: SELECT COUNT(*) FROM whale_balance_snapshots 
       WHERE snapshot_timestamp >= NOW() - INTERVAL '24 hours';
```

**Problem:** High density of zero-balance whales
```
Solution: Check RPC provider health (Alchemy/Infura)
Check MulticallClient logs for error rate
Consider switching to backup RPC endpoint
```

**Problem:** Extreme time drift (>20%)
```
Solution: Verify system clock synchronization (NTP)
Check if using archive node with stale cache
Restart blockchain data sync if necessary
```

**Problem:** LST rate violations
```
Solution: Verify CoinGecko API connectivity
Check steth_eth_rate in accumulation_metrics table
Consider manual rate override if API down
```

## Related Documentation

- `WHALES_ANALYSIS.docx` - Statistical validation methodology
- `AAVE_COMPOUND.docx` - LST correction and precision handling
- `FLOATING_POINT_FIX.md` - Decimal precision requirements
- `PHASE_2_LST_COMPLETE.md` - LST integration details

## Future Enhancements

Planned improvements (not yet implemented):

1. **Transaction Correlation Check**
   - Cross-reference extreme balance changes with on-chain transactions
   - Uses Etherscan API to validate outlier legitimacy

2. **Depeg Prediction Model**
   - Machine learning model to predict stETH de-pegs 24h in advance
   - Uses Curve pool depth + validator exit queue

3. **Automated Remediation**
   - Auto-trigger re-snapshot for missing data
   - Auto-flag corrupted records for manual review

4. **Grafana Dashboard**
   - Real-time visualization of data quality metrics
   - Historical trending of validation scores

## Contact

For issues or improvements, contact the Whale Tracker development team.

**Built with 🔥 by the Whale Tracker Team - January 2026**
