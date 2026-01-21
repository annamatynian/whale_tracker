# 📂 PROJECT FILE MAP - Quick Navigation

Visual guide to all important files for Phase 2 LST Correction.

---

## 🎯 START HERE

```
📄 NEXT_SESSION_START.md          ← Read this first next time
📄 FINAL_REPORT.md                 ← Complete project summary
📄 COMMANDS_CHEAT_SHEET.md         ← All commands in one place
```

---

## 📚 DOCUMENTATION

```
whale_tracker/
│
├── 📁 Documentation (Phase 2)
│   ├── 📄 FINAL_REPORT.md                    ★ Complete overview
│   ├── 📄 PHASE_2_LST_COMPLETE.md            ★ Technical deep-dive
│   ├── 📄 IMPLEMENTATION_SUMMARY.md          ★ High-level summary
│   ├── 📄 IMPLEMENTATION_STATUS.md           Progress checklist
│   ├── 📄 TESTING_GUIDE.md                   Testing instructions
│   ├── 📄 PRE_TESTING_CHECKLIST.md           Pre-test verification
│   ├── 📄 COMMANDS_CHEAT_SHEET.md            Command reference
│   ├── 📄 NEXT_SESSION_START.md              Quick start guide
│   └── 📄 PROJECT_FILE_MAP.md                ← This file
│
├── 📁 Documentation (Previous Phases)
│   ├── 📄 STEP5_COMPLETE.md                  Phase 1: Basic calculator
│   ├── 📄 PHASE_2_1_COMPLETE.md              Earlier work
│   ├── 📄 QUICK_START.md                     Original quick start
│   └── 📄 BUSINESS_ALIGNMENT_ANALYSIS.md     Strategy docs
```

---

## 💻 SOURCE CODE

```
whale_tracker/
│
├── 📁 Core Implementation
│   ├── src/analyzers/
│   │   └── 📄 accumulation_score_calculator.py   ★ Main calculator (MODIFIED)
│   │       ├── _assign_tags()                   NEW: 76 lines
│   │       ├── _detect_lst_migration()          NEW: 69 lines
│   │       ├── calculate_accumulation_score()   UPDATED
│   │       └── _calculate_metrics()             UPDATED
│   │
│   ├── src/providers/
│   │   └── 📄 coingecko_provider.py              ★ Price provider (MODIFIED)
│   │       ├── get_current_price()              NEW: 50 lines
│   │       ├── get_historical_price()           NEW: 73 lines
│   │       └── get_steth_eth_rate()             EXISTING
│   │
│   ├── src/schemas/
│   │   └── 📄 accumulation_schemas.py            Schema (Phase 1 - complete)
│   │
│   ├── src/repositories/
│   │   ├── 📄 accumulation_repository.py         Database access
│   │   └── 📄 snapshot_repository.py             Historical snapshots
│   │
│   └── 📄 run_collective_analysis.py             ★ Main entry point (MODIFIED)
│       ├── Added: price_provider init
│       ├── Added: snapshot_repo init
│       └── Enhanced: results display
```

---

## 🧪 TESTS

```
whale_tracker/
│
├── 📁 Tests
│   ├── tests/unit/
│   │   ├── 📄 test_accumulation_calculator_lst.py   ★ NEW: 6 tests
│   │   │   ├── TestSmartTags (4 tests)
│   │   │   └── TestLSTMigrationDetection (2 tests)
│   │   │
│   │   └── 📄 test_accumulation_calculator.py       Old tests (still valid)
│   │
│   └── 📄 pytest.ini                                 Pytest config
```

---

## 🗃️ DATABASE

```
whale_tracker/
│
├── 📁 Database
│   ├── alembic/
│   │   ├── versions/
│   │   │   └── 📄 xxx_add_lst_fields.py         Phase 1 migration (applied)
│   │   └── 📄 env.py
│   │
│   ├── 📄 alembic.ini                            Alembic config
│   ├── 📄 init_postgres.py                       DB initialization
│   └── 📄 check_database_status.py               Health check
```

---

## 📦 CONFIGURATION

```
whale_tracker/
│
├── 📁 Configuration
│   ├── 📄 .env                                   Secrets (not in git)
│   ├── 📄 .env.postgres                          DB config
│   ├── 📄 requirements.txt                       Python dependencies
│   └── config/
│       └── 📄 database.yml                       DB settings
```

---

## 🎯 QUICK NAVIGATION

### "I want to understand the implementation"
→ Read: `PHASE_2_LST_COMPLETE.md` (450 lines, comprehensive)

### "I want to run tests"
→ Read: `COMMANDS_CHEAT_SHEET.md`
→ Run: `pytest tests/unit/test_accumulation_calculator_lst.py -v`

### "I want high-level overview"
→ Read: `IMPLEMENTATION_SUMMARY.md` (280 lines, executive level)

### "I want to start fresh next session"
→ Read: `NEXT_SESSION_START.md` (80 lines, action-focused)

### "I need to verify setup"
→ Read: `PRE_TESTING_CHECKLIST.md` (120 lines, step-by-step)

### "I'm stuck/debugging"
→ Read: `TESTING_GUIDE.md` (180 lines, troubleshooting)

### "What's been done so far?"
→ Read: `FINAL_REPORT.md` (450 lines, complete report)

---

## 📊 FILE STATISTICS

### Documentation
```
Total files: 8
Total lines: ~1,800
Average: 225 lines per file

Largest: PHASE_2_LST_COMPLETE.md (450 lines)
Most useful: COMMANDS_CHEAT_SHEET.md (quick reference)
Start here: NEXT_SESSION_START.md (quick start)
```

### Source Code
```
Modified files: 3
New methods: 4
Lines added: ~400
Tests created: 6
```

---

## 🚀 WORKFLOW

```
Start
  ↓
Read NEXT_SESSION_START.md
  ↓
Follow PRE_TESTING_CHECKLIST.md
  ↓
Use COMMANDS_CHEAT_SHEET.md
  ↓
If stuck → TESTING_GUIDE.md
  ↓
After success → Git commit
  ↓
Done!
```

---

## 💡 COLOR CODING

```
★ = Modified/Most Important
📄 = Regular file
📁 = Directory
NEW = Created in Phase 2
MODIFIED = Updated in Phase 2
EXISTING = Already existed
```

---

## 🔍 SEARCH INDEX

**Find by topic:**

- **Testing:** `TESTING_GUIDE.md`, `COMMANDS_CHEAT_SHEET.md`
- **Implementation:** `PHASE_2_LST_COMPLETE.md`, `accumulation_score_calculator.py`
- **Overview:** `IMPLEMENTATION_SUMMARY.md`, `FINAL_REPORT.md`
- **Quick Start:** `NEXT_SESSION_START.md`, `COMMANDS_CHEAT_SHEET.md`
- **Technical Details:** `PHASE_2_LST_COMPLETE.md`
- **Business Value:** `FINAL_REPORT.md`, `IMPLEMENTATION_SUMMARY.md`

**Find by activity:**

- **Running tests:** `COMMANDS_CHEAT_SHEET.md` → Testing section
- **Debugging:** `TESTING_GUIDE.md` → Common Issues section
- **Understanding code:** `PHASE_2_LST_COMPLETE.md` → Technical Details
- **Getting started:** `NEXT_SESSION_START.md`
- **Verification:** `PRE_TESTING_CHECKLIST.md`

---

**MOST IMPORTANT FILES:**

1. `NEXT_SESSION_START.md` - Start here next time
2. `COMMANDS_CHEAT_SHEET.md` - Most used commands
3. `PHASE_2_LST_COMPLETE.md` - Technical reference
4. `accumulation_score_calculator.py` - Core implementation
5. `test_accumulation_calculator_lst.py` - Tests

**USE THESE FIRST** ⬆️
