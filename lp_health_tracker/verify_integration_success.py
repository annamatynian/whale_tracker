#!/usr/bin/env python3
"""
Verification Script - Core Functionality Integration
===================================================

Проверяет успешность интеграции HIGH PRIORITY тестов:
- test_bug_fix.py → tests/test_data_analyzer.py 
- test_net_pnl.py → tests/test_data_analyzer.py
- test_master_plan_stage1.py → tests/test_integration_stage1.py
"""

import subprocess
import sys
from pathlib import Path

def run_pytest_command(command, description):
    """Run a pytest command and return the result."""
    print(f"\n🧪 {description}")
    print("-" * 60)
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=Path(__file__).parent
        )
        
        # Extract summary information
        lines = result.stdout.split('\n')
        summary_line = ""
        for line in lines:
            if ('passed' in line or 'failed' in line or 'skipped' in line) and '=' in line:
                summary_line = line.strip()
                break
        
        if result.returncode == 0:
            print(f"✅ PASSED: {summary_line}")
            return True
        else:
            print(f"❌ FAILED: {summary_line}")
            # Show stderr if there's an error
            if result.stderr:
                print(f"Error: {result.stderr[:300]}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Run verification tests for integrated functionality."""
    print("🎯 VERIFYING HIGH PRIORITY INTEGRATION SUCCESS")
    print("=" * 60)
    
    # Test categories to verify
    tests = [
        # 1. Regression tests for bug fixes
        (
            "python -m pytest tests/test_data_analyzer.py::TestAlertThresholdRegressionBugFix -v",
            "Regression Tests - Alert Threshold Bug Fix"
        ),
        
        # 2. Net P&L calculation tests  
        (
            "python -m pytest tests/test_data_analyzer.py::TestNetPnLCalculatorIntegration -v",
            "Net P&L Calculator Integration Tests"
        ),
        
        # 3. Core IL calculation tests (original + new)
        (
            "python -m pytest tests/test_data_analyzer.py::TestImpermanentLossCalculator -v",
            "Core IL Calculation Tests (Enhanced)"
        ),
        
        # 4. Stage 1 integration tests
        (
            "python -m pytest tests/test_integration_stage1.py -m stage1 -v",
            "Stage 1 Integration Tests"
        ),
        
        # 5. All unit tests in data_analyzer
        (
            "python -m pytest tests/test_data_analyzer.py -m unit -v",
            "All Unit Tests - Core Functionality"
        ),
        
        # 6. All regression tests
        (
            "python -m pytest tests/test_data_analyzer.py -m regression -v", 
            "All Regression Tests - Bug Prevention"
        )
    ]
    
    # Run tests and collect results
    results = []
    for command, description in tests:
        success = run_pytest_command(command, description)
        results.append((description, success))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 INTEGRATION VERIFICATION SUMMARY")
    print("-" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    
    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {description}")
    
    print(f"\n🎯 OVERALL RESULT: {passed_tests}/{total_tests} TEST CATEGORIES PASSED")
    
    if passed_tests == total_tests:
        print("\n🎉 INTEGRATION VERIFICATION SUCCESSFUL!")
        print("✅ All core functionality tests working")
        print("✅ Regression tests protecting against bugs")  
        print("✅ Stage 1 integration tests operational")
        print("✅ Professional pytest framework established")
        
        print("\n🚀 READY FOR:")
        print("• Stage 2 integration (test_stage2_final.py)")
        print("• Stage 3 blockchain integration")
        print("• Production deployment")
        
    elif passed_tests >= total_tests * 0.8:  # 80% success rate
        print("\n✅ INTEGRATION MOSTLY SUCCESSFUL!")
        print(f"⚠️  {total_tests - passed_tests} test categories need attention")
        print("💡 This is normal during development - some methods may not be fully implemented yet")
        
        print("\n📋 NEXT STEPS:")
        print("1. Check skipped tests for missing implementations")
        print("2. Implement missing methods in data_analyzer.py")
        print("3. Continue with Stage 2 integration")
        
    else:
        print("\n⚠️  INTEGRATION NEEDS ATTENTION")
        print("💡 Several test categories failed - check implementation status")
        print("🔧 Review error messages above for specific issues")
    
    print("\n📚 REFERENCE COMMANDS:")
    print("# Run specific test categories:")
    print("pytest tests/test_data_analyzer.py -m 'unit' -v")
    print("pytest tests/test_data_analyzer.py -m 'regression' -v") 
    print("pytest tests/test_integration_stage1.py -m 'stage1' -v")
    print("\n# Run all integrated tests:")
    print("pytest tests/test_data_analyzer.py tests/test_integration_stage1.py -v")

if __name__ == "__main__":
    main()
