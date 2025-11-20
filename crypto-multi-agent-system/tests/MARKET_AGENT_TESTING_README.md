# Market Conditions Agent - Testing Guide

This directory contains comprehensive tests for the Market Conditions Agent following the testing checklist.

## 🧪 Test Structure

```
tests/
├── unit/
│   └── test_market_agent.py          # Unit tests with mocks
├── integration/
│   └── test_market_agent_integration.py  # Real API tests
├── test_checklist_market_agent.py    # Complete testing checklist
└── run_market_tests.py               # Convenient test runner
```

## 🚀 Quick Start

### Option 1: Run Complete Checklist (Recommended)
```bash
python tests/test_checklist_market_agent.py
```
This executes the full testing plan exactly as specified and provides a comprehensive report.

### Option 2: Run Convenient Test Runner
```bash
python tests/run_market_tests.py
```

### Option 3: Run Individual Test Suites
```bash
# Unit tests only (no internet required)
pytest tests/unit/test_market_agent.py -v

# Integration tests only (requires internet)
pytest tests/integration/test_market_agent_integration.py -v -m integration

# All tests
pytest tests/ -v
```

## 📋 Testing Checklist Coverage

### ✅ 1. Modular Testing (Unit Testing)
- **Aggressive market test**: USDT dominance < 4.5% → `AGGRESSIVE`
- **Conservative market test**: USDT dominance > 4.5% → `CONSERVATIVE` 
- **Boundary value test**: USDT dominance = 4.5% → `CONSERVATIVE`
- **API error test**: Missing fields → `UNKNOWN` state without crashing

### ✅ 2. Integration Testing  
- **Real API call**: Successfully connects to CoinGecko
- **Pydantic validation**: Output validates against `MarketConditionsReport` schema
- **JSON serialization**: Output is valid JSON

### ✅ 3. Architectural Principles Verification
- **Principle #4 (Fault Tolerance)**: Graceful handling of API failures
- **Principle #6 (Observability)**: Clear logging messages
- **Principle #7 (Reproducibility)**: Git commit hash in output

## 🔧 Test Requirements

### Dependencies
```bash
pip install pytest pytest-mock tenacity
```

### Internet Connection
Integration tests require internet access to test real CoinGecko API calls.

### Git Repository
Reproducibility tests require the code to be in a git repository for hash generation.

## 📊 Expected Test Results

### Successful Unit Test Output
```
✅ test_aggressive_market_regime PASSED
✅ test_conservative_market_regime PASSED  
✅ test_boundary_value_exactly_threshold PASSED
✅ test_api_failure_returns_unknown PASSED
✅ test_malformed_api_response_missing_field PASSED
```

### Successful Integration Test Output
```
✅ test_real_api_call_success PASSED
✅ test_full_analysis_with_real_api PASSED
✅ test_pydantic_validation_with_real_data PASSED
```

### Performance Baseline Example
```
📊 Performance Baseline:
   Average API Response: 156.7ms
   Average Total Time: 168.2ms
```

## 🐛 Troubleshooting

### Common Issues

**Import Error: `No module named 'market_agent'`**
- Solution: Run tests from the project root directory

**API Tests Failing**
- Check internet connection
- Verify CoinGecko API is accessible: `curl https://api.coingecko.com/api/v3/global`

**Git Hash Tests Failing**  
- Ensure code is in a git repository: `git init` if needed
- Ensure git is installed and accessible

**Performance Tests Failing**
- Check network stability
- Adjust performance thresholds in integration tests if needed

### Debug Individual Components
```bash
# Test just the API call
python -c "from agents.market_conditions.market_agent import fetch_coingecko_global_data; print(fetch_coingecko_global_data())"

# Test full analysis
python -c "from agents.market_conditions.market_agent import analyze_market_conditions; print(analyze_market_conditions().model_dump_json(indent=2))"
```

## 📈 Performance Benchmarks

### Expected Performance Ranges
- **API Response Time**: 50-2000ms (depending on network)
- **Total Processing Time**: 60-2500ms  
- **Success Rate**: >99% under normal network conditions
- **Retry Recovery**: Should recover from 1-2 transient failures

### Performance Degradation Indicators
- API response time > 3000ms consistently
- Total processing time > 5000ms
- Multiple retry failures in sequence

## 🎯 Success Criteria

All tests must pass before proceeding to the next agent:

1. ✅ All unit tests pass (logic correctness)
2. ✅ All integration tests pass (real-world functionality)  
3. ✅ All architectural principles verified
4. ✅ Performance within acceptable ranges
5. ✅ No hardcoded secrets detected
6. ✅ Proper error handling and logging

## 📝 Adding New Tests

When adding functionality to the Market Conditions Agent:

1. **Add unit tests** in `tests/unit/test_market_agent.py`
2. **Add integration tests** if external services are involved
3. **Update the checklist** in `test_checklist_market_agent.py`
4. **Update performance baselines** if significant changes are made

## 🔄 Continuous Integration

For CI/CD pipelines:
```bash
# Quick tests (no network required)
pytest tests/unit/ -v

# Full test suite (requires network)
python tests/test_checklist_market_agent.py
```

Test exit codes:
- `0`: All tests passed
- `1`: Some tests failed
