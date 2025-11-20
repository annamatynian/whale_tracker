# 🧪 Market Conditions Agent - Testing Guide

This guide walks you through comprehensive testing of the Market Conditions Agent according to our architectural principles.

## 📋 Testing Checklist

### 1. Modular Testing (Unit Testing)

Test the agent logic in isolation using mocked API responses:

```bash
# Run all unit tests
python -m pytest tests/unit/test_market_agent.py -v

# Run specific test categories
python -m pytest tests/unit/test_market_agent.py::TestMarketConditionsLogic -v
python -m pytest tests/unit/test_market_agent.py::TestErrorHandling -v
```

**Covered scenarios:**
- ✅ **Aggressive mode:** USDT dominance < 4.5% → `market_regime="AGGRESSIVE"`
- ✅ **Conservative mode:** USDT dominance > 4.5% → `market_regime="CONSERVATIVE"`  
- ✅ **Boundary value:** USDT dominance exactly 4.5% → `market_regime="CONSERVATIVE"`
- ✅ **API errors:** Missing fields → `market_regime="UNKNOWN"` with proper logging
- ✅ **Performance metrics:** Timing data captured correctly
- ✅ **Git hash tracking:** Reproducibility information included
- ✅ **Pydantic validation:** Invalid data rejected properly

### 2. Integration Testing

Test real-world interactions with external APIs:

```bash
# Run integration tests (requires internet)
python -m pytest tests/integration/test_market_agent_integration.py -v -m integration

# Quick smoke test
python tests/run_market_tests.py
```

**Covered scenarios:**
- ✅ **Real API calls:** Successful connection to CoinGecko
- ✅ **JSON validation:** Output conforms to `MarketConditionsReport` schema
- ✅ **Network errors:** Graceful handling of connectivity issues
- ✅ **Retry mechanism:** Automatic recovery from temporary failures
- ✅ **Performance benchmarks:** Response times within acceptable limits

### 3. Architectural Principles Compliance

#### Principle #4: Fault Tolerance ✅
```bash
# Test with broken network
python -c "
import sys, os
sys.path.insert(0, 'agents')
from market_conditions.market_agent import analyze_market_conditions
from unittest.mock import patch

with patch('market_conditions.market_agent.fetch_coingecko_global_data', side_effect=Exception('Network down')):
    result = analyze_market_conditions()
    print(f'Result: {result.market_regime}')  # Should be UNKNOWN, not crash
"
```

#### Principle #6: Observability ✅
```bash
# Check logging output
python agents/market_conditions/market_agent.py
```
**Expected logs:**
- 🚀 Starting market conditions analysis...
- ✅ Analysis complete. USDT Dominance: X.X%, Market Regime: XXX (API: XXXms, Total: XXXms)

#### Principle #7: Reproducibility ✅
```bash
# Verify git hash in output
python -c "
import sys
sys.path.insert(0, 'agents')
from market_conditions.market_agent import analyze_market_conditions
result = analyze_market_conditions()
print(f'Git hash: {result.git_commit_hash}')
print(result.model_dump_json(indent=2))
"
```

## 🚀 Quick Start Testing

Run the comprehensive test suite:

```bash
# Full test suite
python tests/run_market_tests.py

# Or step by step:
python -m pytest tests/unit/ -v                    # Unit tests
python -m pytest tests/integration/ -v -m integration  # Integration tests
python agents/market_conditions/market_agent.py        # Manual smoke test
```

## 📊 Expected Test Results

### Unit Tests (Mock Data)
```
TestMarketConditionsLogic::test_aggressive_regime_below_threshold PASSED
TestMarketConditionsLogic::test_conservative_regime_above_threshold PASSED  
TestMarketConditionsLogic::test_boundary_value_exactly_threshold PASSED
TestErrorHandling::test_api_failure_returns_unknown PASSED
TestPerformanceMetrics::test_performance_metrics_captured PASSED
TestGitHashTracking::test_git_hash_captured_when_available PASSED
TestPydanticValidation::test_valid_model_creation PASSED
```

### Integration Tests (Real API)
```
TestRealAPIIntegration::test_real_api_call_success PASSED
TestRealAPIIntegration::test_full_agent_execution PASSED
TestNetworkErrorHandling::test_timeout_handling PASSED
TestRetryMechanism::test_retry_on_temporary_failure PASSED
TestArchitecturalPrinciples::test_principle_4_fault_tolerance PASSED
```

### Example Output (Real API)
```json
{
  "market_regime": "CONSERVATIVE",
  "usdt_dominance_percentage": 5.2,
  "data_source": "CoinGecko",
  "analysis_timestamp": "2025-01-17T15:30:45.123456",
  "git_commit_hash": "a1b2c3d",
  "api_response_time_ms": 156.7,
  "processing_time_ms": 168.2
}
```

## 🐛 Troubleshooting

### Common Issues

**Import errors:**
```bash
# Ensure you're in project root
cd crypto-multi-agent-system
python -m pytest tests/unit/test_market_agent.py -v
```

**Network timeouts:**
```bash
# Run only unit tests if network is unstable
python -m pytest tests/unit/ -v
```

**Missing dependencies:**
```bash
pip install -r requirements.txt
```

### Test Environment Setup

```bash
# Install test dependencies
pip install pytest pytest-mock

# Verify agent works manually
cd agents/market_conditions
python market_agent.py
```

## ✅ Success Criteria

All tests should pass before proceeding to next development phase:

- 🧪 **Unit tests:** 15/15 passing (100% coverage of logic)
- 🌐 **Integration tests:** 8/8 passing (real API interaction)
- 📊 **Manual verification:** Agent runs without errors
- 📝 **Output validation:** JSON conforms to Pydantic schema
- 🔧 **Git tracking:** Commit hash present in output
- ⚡ **Performance:** API response < 10s, processing < 1s

## 🎯 Next Steps After All Tests Pass

1. **Commit stable version:**
   ```bash
   git add .
   git commit -m "Market Conditions Agent - All tests passing"
   ```

2. **Tag stable release:**
   ```bash
   git tag v0.1-market-agent-stable
   ```

3. **Document performance baseline:**
   - Record typical API response times
   - Note any environmental dependencies
   - Update architecture documentation

The Market Conditions Agent is now ready for integration into the larger multi-agent system! 🎉
