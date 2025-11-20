# Windows Testing Guide

## Fixed Issues

### Problem 1: Unicode/Emoji Errors Fixed
- Windows console (CP1251) cannot display Unicode emojis
- **Solution**: Created Windows-compatible test files with ASCII-only output

### Problem 2: Missing TokenCandidate Class Fixed  
- Tests expected `TokenCandidate` class but it was missing
- **Solution**: Added `TokenCandidate` class to `pump_models.py`

## Quick Start (5 minutes)

```cmd
# Navigate to project
cd C:\Users\annam\Documents\DeFi-RAG-Project\crypto-multi-agent-system

# Run Windows-compatible test suite
python test_master_windows.py
```

## Individual Tests (if master test fails)

```cmd
# Test 1: Check imports and basic functionality
python test_imports_windows.py

# Test 2: Quick component test  
python test_quick_windows.py

# Test 3: Mock data without API keys
python test_mock_data_windows.py
```

## Expected Results

### Success Output
```
WINDOWS-COMPATIBLE CRYPTO MULTI-AGENT TEST
================================================================================ 
TEST 1/3: Import Check
Script: test_imports_windows.py (CRITICAL)
================================================================================
OK SimpleOrchestrator imported
OK All dependencies imported
Result test_imports_windows.py: PASS

... (more tests)

SUCCESS: ALL CRITICAL TESTS PASSED!
System ready for next stage
```

### What Each Test Does

1. **test_imports_windows.py**
   - Checks all imports work correctly
   - Validates system configuration  
   - Tests backwards compatibility
   - **Should always pass** if system is set up correctly

2. **test_quick_windows.py**
   - Tests orchestrator initialization
   - Tests discovery agent creation
   - Tests scoring system basic functionality
   - **Quick 30-second health check**

3. **test_mock_data_windows.py**
   - Creates fake token candidates
   - Tests scoring algorithms
   - Tests ranking and filtering  
   - **Works without API keys**

## If Tests Fail

### Common Issues:

1. **Import Errors**:
   ```cmd
   pip install -r requirements.txt
   ```

2. **Wrong Directory**:
   ```cmd
   # Make sure you see these folders:
   dir agents
   dir tools
   dir config
   ```

3. **Python Version**:
   ```cmd
   python --version
   # Should be 3.8 or higher
   ```

## After Successful Testing

1. **Add API Keys** (create `.env` file):
   ```env
   DEXSCREENER_API_KEY=your_key
   COINGECKO_API_KEY=your_key  
   GOPLUS_API_KEY=your_key
   TELEGRAM_BOT_TOKEN=your_token
   ```

2. **Test with real APIs**:
   ```cmd
   python main.py --config-check
   python main.py --dry-run
   ```

3. **Run full system**:
   ```cmd
   python main.py
   ```

## Understanding Test Results

- **100% Success**: System ready for production
- **80-99% Success**: Minor issues, mostly ready  
- **50-79% Success**: Serious problems need fixing
- **<50% Success**: Major issues, system not ready

## Files Created for Windows Compatibility

| File | Purpose |
|------|---------|
| `test_master_windows.py` | Main test runner (Windows safe) |
| `test_imports_windows.py` | Import and config tests |
| `test_quick_windows.py` | Quick health check |  
| `test_mock_data_windows.py` | Mock data testing |

---

**Start with**: `python test_master_windows.py` - this will run everything automatically and give you a clear report on system status.
