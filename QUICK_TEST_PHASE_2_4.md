# QUICK TEST CHECKLIST - PHASE 2.4

## Before Running
```bash
# 1. Ensure database is up to date
alembic upgrade head

# 2. Check PostgreSQL is running
psql -U postgres -d whale_tracker -c "SELECT 1"
```

## Test 1: --once Mode (5 min test)
```bash
python main.py --once
```

### Expected Output:
```
✅ "Initializing snapshot system (Phase 2)..."
✅ "✅ Snapshot database manager initialized"
✅ "Running initial snapshot..."
✅ "🕐 Starting hourly snapshot job..."
✅ "✅ Hourly snapshot complete: X snapshots saved"
```

### Verify Database:
```bash
psql -U postgres -d whale_tracker -c "SELECT COUNT(*), MAX(snapshot_timestamp) FROM whale_balance_snapshots;"
```
**Should see:** At least 1 snapshot timestamp

## Test 2: Normal Mode (check scheduler setup)
```bash
python main.py
# Wait ~30 seconds, then Ctrl+C
```

### Expected Logs:
```
✅ "Running initial snapshot..."
✅ "Adding hourly snapshot job to scheduler..."
✅ "✅ Hourly snapshot job scheduled (every 1 hour)"
✅ "Scheduler started successfully!"
```

### Verify Shutdown:
```
✅ "Stopping scheduler..."
✅ "Closing snapshot database connections..."
✅ "Snapshot database closed"
```

## Test 3: Check Logs
```bash
tail -20 logs/whale_tracker.log
```

### Should contain:
- [x] Snapshot system initialization
- [x] Initial snapshot completion
- [x] Scheduler setup
- [x] No error tracebacks

## Test 4: Long Run (optional - 1+ hour)
```bash
python main.py
# Let it run for 1+ hour
```

### After 1 hour, check:
```bash
psql -U postgres -d whale_tracker -c "
SELECT DATE_TRUNC('hour', snapshot_timestamp) as hour,
       COUNT(DISTINCT whale_address) as whales
FROM whale_balance_snapshots
GROUP BY hour
ORDER BY hour DESC;
"
```

**Should see:** Multiple hourly timestamps

## Success Criteria
- [x] Test 1 passes (--once mode works)
- [x] Test 2 passes (scheduler configured)
- [x] Test 3 passes (logs clean)
- [x] Database contains snapshots
- [x] No Python errors
- [x] Clean shutdown

## If Something Fails

### Error: "Web3Manager must be initialized"
**Fix:** Already handled - setup() called before snapshot

### Error: "Table doesn't exist"
**Fix:** Run `alembic upgrade head`

### Error: "Can't connect to database"
**Fix:** Check PostgreSQL is running, check .env credentials

### Error: RPC rate limits
**Expected:** Multicall should handle this with retry logic
**If persistent:** Reduce whale_limit in run_hourly_snapshot (1000 → 500)

## Next Steps After Success

1. ✅ Commit changes
2. ✅ Test `run_collective_analysis.py`
3. ✅ Monitor hourly snapshots over 24h
4. ✅ Verify accumulation score calculation

---

**PHASE 2 COMPLETE!** 🎉
