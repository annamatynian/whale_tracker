#!/usr/bin/env python3
"""
Complete Regression Testing Suite - Windows Compatible
=====================================================

Runs both custom regression tests and pytest suite to verify
that Pydantic integration hasn't broken existing functionality.
Windows console compatible version.

Usage: python full_regression_test_windows.py

Author: Generated for DeFi-RAG Project
"""

import subprocess
import sys
import os
from pathlib import Path

def run_custom_regression():
    """Run our custom regression test."""
    print("RUNNING Custom Regression Tests...")
    print("=" * 50)
    
    try:
        result = subprocess.run([
            sys.executable, "regression_test_windows.py"
        ], capture_output=True, text=True, timeout=60)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("[TIMEOUT] Custom regression test timed out")
        return False
    except Exception as e:
        print(f"[ERROR] Error running custom regression test: {e}")
        return False

def run_pytest_suite():
    """Run pytest test suite."""
    print("\nRUNNING pytest Test Suite...")
    print("=" * 50)
    
    try:
        result = subprocess.run([
            sys.executable, "run_pytest_windows.py"
        ], capture_output=True, text=True, timeout=180)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("[TIMEOUT] pytest suite timed out")
        return False
    except Exception as e:
        print(f"[ERROR] Error running pytest suite: {e}")
        return False

def check_dependencies():
    """Check if required testing dependencies are available."""
    print("CHECKING Testing Dependencies...")
    print("-" * 30)
    
    dependencies = [
        ("pytest", "pytest"),
        ("pytest_asyncio", "pytest-asyncio"),
        ("pydantic", "pydantic"),
    ]
    
    missing = []
    
    for module, name in dependencies:
        try:
            __import__(module)
            print(f"   [OK] {name} available")
        except ImportError:
            print(f"   [ERROR] {name} missing")
            missing.append(name)
    
    if missing:
        print(f"\nMissing dependencies: {', '.join(missing)}")
        print("Install with: pip install -r requirements_testing.txt")
        return False
    
    print("   [OK] All testing dependencies available")
    return True

def main():
    """Run complete regression test suite."""
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    print("LP Health Tracker - Complete Regression Testing")
    print("=" * 60)
    print("Purpose: Verify that Pydantic integration hasn't broken anything")
    print("=" * 60)
    
    # Check dependencies first
    if not check_dependencies():
        print("\n[ERROR] Cannot run tests - missing dependencies")
        return 1
    
    success_count = 0
    total_tests = 2
    
    # Run custom regression tests
    if run_custom_regression():
        success_count += 1
        print("[OK] Custom regression tests PASSED")
    else:
        print("[ERROR] Custom regression tests FAILED")
    
    # Run pytest suite  
    if run_pytest_suite():
        success_count += 1
        print("[OK] pytest test suite PASSED")
    else:
        print("[ERROR] pytest test suite FAILED")
    
    # Final summary
    print("\n" + "=" * 60)
    print("REGRESSION TESTING RESULTS:")
    print(f"   [OK] Passed: {success_count}/{total_tests}")
    print(f"   Success Rate: {success_count/total_tests*100:.1f}%")
    
    if success_count == total_tests:
        print("\nALL REGRESSION TESTS PASSED!")
        print("Pydantic integration is stable and hasn't broken existing functionality.")
        print("System is ready for next development phase.")
    else:
        print(f"\n{total_tests - success_count} TEST SUITE(S) FAILED!")
        print("There are regressions that need to be fixed before proceeding.")
        print("Please review failed tests and fix issues.")
    
    return 0 if success_count == total_tests else 1

if __name__ == "__main__":
    print("Starting regression testing...")
    exit(main())
