#!/usr/bin/env python3
"""
Quick Test Runner for Gas Calculator Dependency Injection
=========================================================

Fast validation of critical changes after dependency injection refactoring.

Usage: python quick_test_gas_refactor_fixed.py

Author: Generated for DeFi-RAG Project
"""

import subprocess
import sys
import os
from pathlib import Path


def run_test(command, description):
    """Run a single test command."""
    print(f"\nTesting: {description}")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60,
            shell=True
        )
        
        if result.returncode == 0:
            print(f"[PASS] {description}")
            if result.stdout:
                # Show only key lines
                lines = result.stdout.split('\n')
                for line in lines:
                    if '[PASS]' in line or 'PASSED' in line or 'SUCCESS' in line:
                        print(f"   {line}")
            return True
        else:
            print(f"[FAIL] {description}")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] {description}")
        return False
    except Exception as e:
        print(f"[ERROR] {description}: {e}")
        return False


def main():
    """Run critical tests quickly."""
    print("QUICK GAS CALCULATOR DEPENDENCY INJECTION TEST")
    print("=" * 60)
    print("Testing critical functionality after refactoring...\n")
    
    # Check if we're in the right directory
    if not os.path.exists("src/gas_cost_calculator.py"):
        print("[ERROR] Please run this from the lp_health_tracker root directory")
        return False
    
    tests = [
        ("python test_dependency_injection_fixed.py", "Dependency Injection Validation"),
        ("python test_gas_integration_fixed.py", "Integration with main.py"),
        ("python regression_test_fixed.py", "Regression Testing")
    ]
    
    results = []
    
    for command, description in tests:
        success = run_test(command, description)
        results.append((description, success))
    
    # Summary
    print("\n" + "=" * 60)
    print("QUICK TEST RESULTS")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for description, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"   {status} - {description}")
    
    print(f"\nSummary: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\nALL CRITICAL TESTS PASSED!")
        print("   Dependency injection refactoring is successful!")
        print("   [PASS] GasCostCalculator is properly decoupled")
        print("   [PASS] Integration with main.py works")
        print("   [PASS] No regressions detected")
        print("\nReady for production use!")
        return True
    else:
        print(f"\n{total - passed} TEST(S) FAILED!")
        print("   Review the failing tests before proceeding.")
        print("\nNext steps:")
        print("   1. Fix the failing tests")
        print("   2. Check detailed logs")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
