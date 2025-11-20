# Research & Exploration Tests

This directory contains historical research and exploration tests that were used during development but are not part of the active testing suite.

## 📚 Research Files

### APR vs APY Analysis
- `test_apr_vs_apy.py` - Initial APR vs APY comparison research
- `test_apr_vs_apy_final.py` - Final APR vs APY analysis
- `test_apr_vs_apy_real_data.py` - Real data validation for APR calculations

**Purpose:** Understanding the difference between simple interest (APR) and compound interest (APY) for LP fee calculations. Research concluded that for daily calculations over typical LP periods, the difference is negligible (<0.1%).

### DeFi Llama API Exploration
- `test_defi_llama_scout.py` - Initial DeFi Llama API exploration
- `test_defi_llama_scout_v2_only.py` - Focused DeFi Llama testing

**Purpose:** Exploring DeFi Llama API structure to understand how to fetch real APR data for different protocols. Led to successful integration in Stage 2.

## 🎯 Historical Context

These files represent important R&D phases:

1. **Mathematical Validation Phase** - Ensuring our IL and fee calculations were mathematically correct
2. **API Research Phase** - Understanding external data sources before integration
3. **Performance Analysis** - Comparing different calculation approaches

## 📋 Status

- ✅ Research completed successfully
- ✅ Findings integrated into main codebase
- ✅ Files archived for historical reference
- ❌ Not part of active test suite

## 🔗 Related Production Code

Research findings were implemented in:
- `src/data_analyzer.py` - IL and fee calculations
- `src/data_providers.py` - DeFi Llama integration
- `tests/test_data_analyzer.py` - Unit tests for mathematical functions

---

*These files are kept for documentation and historical reference. Do not modify or include in pytest runs.*