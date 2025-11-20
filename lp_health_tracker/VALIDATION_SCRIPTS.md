# 🧪 Validation Scripts

This directory contains **validation scripts** for manual testing and demonstration purposes. These are **NOT automated tests** and should not be run in CI/CD.

## 📋 Purpose

- **Manual validation** of system functionality
- **Demo scripts** for showcasing features
- **Quick checks** during development
- **Visual verification** of outputs

## 🔧 Scripts

### **validate_stage2_demo.py**
- **Purpose:** Manual validation of Stage 2 live data integration
- **Usage:** `python validate_stage2_demo.py`
- **Output:** Human-readable demonstration of API integration

### **quick_test.py** 
- **Purpose:** Quick manual test of bug fixes
- **Usage:** `python quick_test.py`
- **Output:** Visual confirmation of alert logic

## ⚠️ Important Notes

### **These are NOT pytest tests:**
- ❌ No isolation (depend on external files)
- ❌ Print-based validation (not assert-based)
- ❌ Monolithic scripts (not independent tests)
- ❌ Wide exception handling (may mask issues)

### **For automated testing, use:**
```bash
# Run unit tests
pytest tests/ -m "not slow and not integration"

# Run integration tests  
pytest tests/ -m integration

# Run all tests
pytest tests/
```

## 🎯 When to Use

### **Use validation scripts for:**
- ✅ Manual verification during development
- ✅ Demonstrating features to stakeholders
- ✅ Quick visual checks of output
- ✅ One-off testing scenarios

### **Use pytest tests for:**
- ✅ Automated CI/CD testing
- ✅ Regression testing
- ✅ Test-driven development
- ✅ Code coverage analysis
- ✅ Integration with IDEs

## 🚀 Migration Path

If you want to convert a validation script to proper tests:

1. **Move logic** to `tests/test_integration_end_to_end.py`
2. **Add pytest fixtures** for data isolation
3. **Replace print()** with assert statements
4. **Add proper markers** (@pytest.mark.integration, @pytest.mark.slow)
5. **Remove file dependencies** (use fixtures instead)

## 📚 Best Practices

### **For validation scripts:**
- Keep them simple and focused
- Use descriptive names (validate_*, demo_*, manual_*)
- Document their purpose clearly
- Don't rely on them for quality assurance

### **For automated tests:**
- Use pytest framework
- Ensure isolation and independence
- Use proper assertions
- Maintain in tests/ directory
