# ✅ CRITICAL IMPLEMENTATION STEPS - COLLECTIVE WHALE ANALYSIS (LST CORRECTION)

**Date:** 2026-01-19  
**Status:** ⚙️ IN PROGRESS

---

## 📋 IMPLEMENTATION CHECKLIST

### ✅ PHASE 1: SCHEMA & DATABASE (COMPLETE)
- [x] Extended AccumulationMetricCreate schema (11 new fields)
- [x] Added LST balance tracking fields
- [x] Added smart tags system
- [x] Added statistical quality metrics (Gini, MAD, anomaly detection)
- [x] Added price context for Bullish Divergence

### ✅ PHASE 2: CALCULATOR CORE METHODS (COMPLETE)
- [x] Added `_fetch_lst_balances()` method
- [x] Updated `_calculate_metrics()` with LST aggregation
- [x] Added MAD anomaly detection logic
- [x] Added Gini coefficient calculation
- [x] Added `_detect_lst_migration()` method
- [x] Added `_assign_tags()` method
- [x] Added historical price fetching (48h lookback)

### ✅ PHASE 3: PROVIDER UPDATES (COMPLETE)
- [x] Added `get_current_price()` to CoinGeckoProvider
- [x] Added `get_historical_price()` to CoinGeckoProvider
- [x] Verified `get_steth_eth_rate()` exists

### ⏳ PHASE 4: INTEGRATION (IN PROGRESS)
- [ ] Update `run_collective_analysis.py` to initialize price_provider
- [ ] Update `run_collective_analysis.py` to initialize snapshot_repo
- [ ] Test full integration end-to-end

### ⏳ PHASE 5: TESTING (PENDING)
- [ ] Run `pytest tests/unit/test_accumulation_calculator_lst.py -v`
- [ ] Fix any failing tests
- [ ] Run integration test with real API
- [ ] Verify tags are assigned correctly
- [ ] Verify LST migration detection works
- [ ] Verify Bullish Divergence detection works

---

## 🚨 CRITICAL REMINDERS

1. **Перезапусти Python shell** после изменения schema (Pydantic cache!)
2. **PriceProvider** должен быть инициализирован в `main.py`/`run_collective_analysis.py`
3. **SnapshotRepository** должен быть инициализирован
4. **Тесты сначала** - TDD approach
5. **Git commit после каждого шага**

---

## 📊 NEXT STEPS

1. **Update run_collective_analysis.py:**
   ```python
   from src.providers.coingecko_provider import CoinGeckoProvider
   from src.repositories.snapshot_repository import SnapshotRepository
   
   price_provider = CoinGeckoProvider()
   snapshot_repo = SnapshotRepository(session)
   
   calculator = AccumulationScoreCalculator(
       whale_provider=whale_provider,
       multicall_client=multicall_client,
       repository=repository,
       snapshot_repo=snapshot_repo,
       price_provider=price_provider,
       lookback_hours=24
   )
   ```

2. **Run unit tests:**
   ```bash
   pytest tests/unit/test_accumulation_calculator_lst.py -v
   ```

3. **Run integration test:**
   ```bash
   python run_collective_analysis.py
   ```

4. **Verify output includes:**
   - ✅ LST-adjusted score calculated
   - ✅ Tags assigned ([Organic Accumulation], etc.)
   - ✅ Gini coefficient logged
   - ✅ MAD anomaly detection logged
   - ✅ Price change 48h logged
   - ✅ LST migration count logged

---

## 🎯 SUCCESS CRITERIA

**Unit Tests:**
- [ ] All 13+ tests in test_accumulation_calculator_lst.py PASS
- [ ] No deprecation warnings
- [ ] No errors

**Integration Test:**
- [ ] Calculator runs without errors
- [ ] Metrics stored in database
- [ ] Tags assigned correctly
- [ ] LST migration detected (if any)
- [ ] Historical price fetched
- [ ] Gini coefficient calculated

**Manual Verification:**
- [ ] Check logs for "Step 7: Assigning smart tags..."
- [ ] Check logs for LST migration detection
- [ ] Check logs for price context
- [ ] Verify database contains new fields

---

## ⏱️ TIME ESTIMATE

**Remaining work:** 1-2 hours
- Integration: 30 min
- Testing: 30 min
- Debugging: 30 min
- Documentation: 30 min

---

**READY FOR NEXT STEP: Update run_collective_analysis.py** 🚀
