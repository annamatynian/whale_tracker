#!/usr/bin/env python3
"""
Stage 1 Fixes Validation Script
==============================

Проверяет исправления ошибок в Stage 1 и общий статус системы.

Usage:
    python test_stage1_fixes.py
"""

import subprocess
import sys
import time
from datetime import datetime

def print_header(title):
    """Print formatted header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def print_section(title):
    """Print formatted section."""
    print(f"\n🔍 {title}")
    print("-" * 40)

def run_pytest(test_pattern, description):
    """Run pytest with specific pattern and return results."""
    print(f"\n▶️ {description}")
    print(f"   Command: pytest {test_pattern}")
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_pattern, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        print(f"   Exit code: {result.returncode}")
        
        if result.returncode == 0:
            print("   ✅ PASSED")
            return True
        else:
            print("   ❌ FAILED")
            if result.stdout:
                print("   STDOUT:", result.stdout[-500:])  # Last 500 chars
            if result.stderr:
                print("   STDERR:", result.stderr[-500:])
            return False
            
    except subprocess.TimeoutExpired:
        print("   ⏰ TIMEOUT")
        return False
    except Exception as e:
        print(f"   💥 ERROR: {e}")
        return False

def main():
    """Main test execution."""
    print_header("LP HEALTH TRACKER - STAGE 1 FIXES VALIDATION")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    # 1. Test Stage 1 specifically
    print_section("STAGE 1 INTEGRATION TESTS")
    results['stage1'] = run_pytest(
        "tests/test_integration_stage1.py",
        "Stage 1 Integration Tests (Datetime Fix)"
    )
    
    # 2. Test specific data analyzer functionality
    print_section("DATA ANALYZER UNIT TESTS")
    results['data_analyzer'] = run_pytest(
        "tests/test_data_analyzer.py",
        "Data Analyzer Unit Tests"
    )
    
    # 3. Test core IL calculations
    print_section("CORE FUNCTIONALITY")
    results['il_calculations'] = run_pytest(
        "tests/test_integration_stage1.py::test_il_calculation_accuracy",
        "IL Calculation Accuracy Test"
    )
    
    # 4. Test the specific fixed function
    print_section("DATETIME FIX VERIFICATION")
    results['datetime_fix'] = run_pytest(
        "tests/test_integration_stage1.py::test_analyze_position_with_fees",
        "Analyze Position With Fees Test (Datetime Fix)"
    )
    
    # 5. Quick overall system check
    print_section("QUICK SYSTEM CHECK")
    results['system_check'] = run_pytest(
        "tests/test_integration_stage1.py::test_complete_stage1_workflow",
        "Complete Stage 1 Workflow Test"
    )
    
    # 6. Optional: Run Stage 2 if available
    print_section("STAGE 2 STATUS CHECK")
    results['stage2'] = run_pytest(
        "tests/test_integration_stage2.py",
        "Stage 2 Integration Tests (Status Check)"
    )
    
    # Summary
    print_header("TEST RESULTS SUMMARY")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    print(f"📊 Overall Results: {passed}/{total} test suites passed")
    print()
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name:20} {status}")
    
    # Critical assessment
    print(f"\n🎯 CRITICAL ASSESSMENT:")
    
    if results.get('stage1', False) and results.get('datetime_fix', False):
        print("   ✅ Stage 1 datetime fixes are working correctly!")
        print("   ✅ Core IL calculations are functional")
        
        if results.get('stage2', False):
            print("   ✅ Stage 2 is also working - system is in great shape!")
            overall_status = "EXCELLENT"
        else:
            print