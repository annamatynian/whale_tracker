# 🚀 COMMANDS CHEAT SHEET

Quick reference for all testing and verification commands.

---

## 📍 SETUP

```bash
# Navigate to project
cd C:\Users\annam\Documents\DeFi-RAG-Project\whale_tracker

# Restart Python shell (clear Pydantic cache)
# Close any open Python shells/terminals and open fresh one
```

---

## 🧪 TESTING

### Unit Tests (Fast - No DB needed)
```bash
# All LST tests
pytest tests/unit/test_accumulation_calculator_lst.py -v

# Specific test class
pytest tests/unit/test_accumulation_calculator_lst.py::TestSmartTags -v

# Single test
pytest tests/unit/test_accumulation_calculator_lst.py::TestSmartTags::test_tag_organic_accumulation -v

# With coverage
pytest tests/unit/test_accumulation_calculator_lst.py --cov=src.analyzers.accumulation_score_calculator -v
```

### Integration Test (Requires DB)
```bash
# Full pipeline
python run_collective_analysis.py

# With logging
python run_collective_analysis.py 2>&1 | tee integration_test.log
```

---

## 🔍 VERIFICATION

### Database Status
```bash
# Check PostgreSQL running
python check_database_status.py

# Start PostgreSQL (if needed)
net start postgresql-x64-18

# Stop PostgreSQL
net stop postgresql-x64-18
```

### Import Check
```bash
# Check CoinGeckoProvider
python -c "from src.providers.coingecko_provider import CoinGeckoProvider; print('✅ CoinGeckoProvider OK')"

# Check Calculator
python -c "from src.analyzers.accumulation_score_calculator import AccumulationScoreCalculator; print('✅ Calculator OK')"

# Check all imports
python -c "
from src.providers.coingecko_provider import CoinGeckoProvider
from src.repositories.snapshot_repository import SnapshotRepository
from src.analyzers.accumulation_score_calculator import AccumulationScoreCalculator
print('✅ All imports OK')
"
```

### Code Verification
```bash
# Check method exists in calculator
python -c "
from src.analyzers.accumulation_score_calculator import AccumulationScoreCalculator
assert hasattr(AccumulationScoreCalculator, '_assign_tags')
assert hasattr(AccumulationScoreCalculator, '_detect_lst_migration')
print('✅ Methods exist')
"

# Check method exists in provider
python -c "
from src.providers.coingecko_provider import CoinGeckoProvider
p = CoinGeckoProvider()
assert hasattr(p, 'get_current_price')
assert hasattr(p, 'get_historical_price')
assert hasattr(p, 'get_steth_eth_rate')
print('✅ Provider methods exist')
"
```

---

## 📊 DATABASE

### Check Tables
```bash
# Check accumulation_metrics table has new columns
python -c "
from src.core.database_manager import DatabaseManager
import asyncio

async def check():
    db = DatabaseManager()
    await db.initialize()
    session = db.get_session()
    
    from sqlalchemy import inspect
    inspector = inspect(session.bind)
    columns = [c['name'] for c in inspector.get_columns('accumulation_metrics')]
    
    required = ['lst_adjusted_score', 'concentration_gini', 'is_anomaly', 'tags']
    missing = [col for col in required if col not in columns]
    
    if missing:
        print(f'❌ Missing columns: {missing}')
        print('Run: alembic upgrade head')
    else:
        print('✅ All columns present')
    
    await db.close()

asyncio.run(check())
"
```

### Apply Migrations (if needed)
```bash
# Check migration status
alembic current

# Apply pending migrations
alembic upgrade head

# Create new migration (if schema changed)
alembic revision --autogenerate -m "Add LST correction fields"
```

---

## 🐛 DEBUGGING

### View Recent Logs
```bash
# Tail latest log
ls logs/*.log | sort | tail -1 | xargs tail -100

# Search for errors
ls logs/*.log | xargs grep "ERROR"

# Search for specific step
ls logs/*.log | xargs grep "Step 7: Assigning smart tags"
```

### Interactive Testing
```bash
# Start Python REPL
python

# In REPL:
from src.providers.coingecko_provider import CoinGeckoProvider
import asyncio

p = CoinGeckoProvider()

# Test current price
asyncio.run(p.get_current_price('ETH'))

# Test historical price
from datetime import datetime, timedelta, UTC
timestamp = datetime.now(UTC) - timedelta(hours=48)
asyncio.run(p.get_historical_price('ETH', timestamp))

# Test stETH rate
asyncio.run(p.get_steth_eth_rate())
```

---

## 📦 GIT

### Status Check
```bash
# See what changed
git status

# See diff
git diff src/analyzers/accumulation_score_calculator.py
```

### Commit
```bash
# Add all files
git add .

# Commit with message
git commit -m "feat(collective): Add LST correction, smart tags, MAD detection, Gini index

- LST aggregation (ETH + WETH + stETH)
- MAD anomaly detection (3×MAD threshold)
- Gini coefficient for concentration
- 6 smart tags system
- LST migration detection
- Bullish divergence (48h price context)
- Historical price integration (CoinGecko)

Tests: 6 unit tests added
Files: calculator, provider, integration updated"

# Push (if ready)
git push origin main
```

---

## 🎯 QUICK WORKFLOW

### First Time Today
```bash
cd C:\Users\annam\Documents\DeFi-RAG-Project\whale_tracker
# Restart Python shell
pytest tests/unit/test_accumulation_calculator_lst.py -v
```

### If Tests Fail
```bash
# Read error
# Fix code
# Restart Python shell
pytest tests/unit/test_accumulation_calculator_lst.py -v
```

### After Tests Pass
```bash
python run_collective_analysis.py
# Check output
git add .
git commit -m "feat: LST correction complete"
```

---

## 📚 DOCUMENTATION NAVIGATION

```bash
# Start here
cat NEXT_SESSION_START.md

# Before testing
cat PRE_TESTING_CHECKLIST.md

# Full details
cat PHASE_2_LST_COMPLETE.md

# If stuck
cat TESTING_GUIDE.md

# Overview
cat IMPLEMENTATION_SUMMARY.md
```

---

## 🚨 EMERGENCY FIXES

### "Tests won't run"
```bash
cd C:\Users\annam\Documents\DeFi-RAG-Project\whale_tracker
python -m pytest tests/unit/test_accumulation_calculator_lst.py -v
```

### "Imports failing"
```bash
# Check PYTHONPATH
echo %PYTHONPATH%

# Set if needed (from project root)
set PYTHONPATH=%CD%
```

### "Database issues"
```bash
# Restart PostgreSQL
net stop postgresql-x64-18
net start postgresql-x64-18

# Reinitialize
python init_postgres.py
```

### "Pydantic errors"
```bash
# Kill all Python processes
taskkill /F /IM python.exe

# Restart fresh shell
# Try again
```

---

**MOST COMMON COMMAND:**
```bash
pytest tests/unit/test_accumulation_calculator_lst.py -v
```

**SECOND MOST COMMON:**
```bash
python run_collective_analysis.py
```

**USE THESE FIRST** ⬆️
