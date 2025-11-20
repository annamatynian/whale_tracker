@echo off
REM GAS REFACTOR TESTING COMMANDS - WINDOWS
REM =======================================

echo 🚀 TESTING GAS CALCULATOR DEPENDENCY INJECTION REFACTOR
echo ========================================================

echo.
echo 📍 OPTION 1: QUICK VALIDATION (5 minutes)
echo python quick_test_gas_refactor.py

echo.
echo 📍 OPTION 2: COMPREHENSIVE TESTING (15-20 minutes)
echo python test_comprehensive_gas_refactor.py

echo.
echo 📍 OPTION 3: MANUAL STEP-BY-STEP
echo # 1. Dependency injection validation
echo python test_dependency_injection.py
echo.
echo # 2. Integration validation  
echo python test_gas_integration.py
echo.
echo # 3. Unit tests
echo pytest tests/unit/test_gas_cost_calculator.py -v
echo pytest tests/unit/test_gas_quick.py -v
echo.
echo # 4. Integration tests
echo pytest tests/integration/test_integration_stage1.py -v
echo pytest tests/integration/test_integration_stage2.py -v
echo.
echo # 5. Regression testing
echo python regression_test.py
echo.
echo # 6. E2E testing
echo pytest tests/e2e/test_core_functionality.py -v

echo.
echo 🎯 CRITICAL SUCCESS CRITERIA:
echo ✅ test_dependency_injection.py PASSES
echo ✅ test_gas_integration.py PASSES
echo ✅ regression_test.py PASSES
echo ✅ No unit test failures due to API changes

echo.
echo 🚀 RECOMMENDED: Start with OPTION 1 for quick validation

pause
