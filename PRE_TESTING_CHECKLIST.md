# ✅ PRE-TESTING CHECKLIST

Run through this before testing to ensure everything is ready.

---

## 🔍 VERIFICATION STEPS

### 1. File Existence Check
```bash
# Check all files exist
ls src/analyzers/accumulation_score_calculator.py
ls src/providers/coingecko_provider.py
ls tests/unit/test_accumulation_calculator_lst.py
ls run_collective_analysis.py
```

### 2. Python Environment
```bash
# Verify you're in project root
pwd
# Should show: C:\Users\annam\Documents\DeFi-RAG-Project\whale_tracker

# Restart Python (clear Pydantic cache)
# Close any open Python shells and restart
```

### 3. Database Status
```bash
# Check PostgreSQL is running
python check_database_status.py

# Expected: "✅ Database healthy"
```

### 4. Dependencies Check
```bash
# Check key imports work
python -c "from src.providers.coingecko_provider import CoinGeckoProvider; print('✅ OK')"
python -c "from src.analyzers.accumulation_score_calculator import AccumulationScoreCalculator; print('✅ OK')"
```

---

## 📋 QUICK CODE REVIEW

### In accumulation_score_calculator.py - Check Methods Exist:
- [ ] `_assign_tags(self, metric, whale_count)` - around line 560
- [ ] `_detect_lst_migration(self, addresses, eth_current, ...)` - around line 490
- [ ] Updated `calculate_accumulation_score()` - calls both methods
- [ ] Updated `_calculate_metrics()` - accepts lst_migration_count and price_change_48h_pct

### In coingecko_provider.py - Check Methods Exist:
- [ ] `get_current_price(self, token_symbol, vs_currency='usd')` - around line 270
- [ ] `get_historical_price(self, token_symbol, timestamp, vs_currency='usd')` - around line 320
- [ ] `get_steth_eth_rate(self)` - should already exist

### In run_collective_analysis.py - Check Updates:
- [ ] Imports: CoinGeckoProvider, SnapshotRepository
- [ ] price_provider = CoinGeckoProvider(network="ethereum")
- [ ] snapshot_repo = SnapshotRepository(session)
- [ ] Calculator initialized with both

---

## 🎯 READY TO TEST?

If all checks above ✅:
```bash
# RUN TESTS
pytest tests/unit/test_accumulation_calculator_lst.py -v
```

If ANY checks ❌:
- Fix the issue first
- Re-run this checklist
- Then test

---

## 🚨 COMMON FIXES

### "Method not found" error
→ Check you saved the file after editing
→ Restart Python shell

### "Import error"
→ Check you're in project root
→ Check file exists at expected path

### "Database error"
→ Start PostgreSQL
→ Run `python init_postgres.py`

---

**After all checks pass → Run tests** ⬆️
