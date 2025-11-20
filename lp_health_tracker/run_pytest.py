#!/usr/bin/env python3
"""
Run pytest tests for LP Health Tracker
=====================================

This script runs the pytest test suite and shows results.

Author: Generated for DeFi-RAG Project
"""

import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run pytest with different test categories."""
    
    # Change to project directory
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    print("🧪 Running pytest Test Suite for LP Health Tracker")
    print("=" * 60)
    
    # Test categories to run
    test_categories = [
        ("unit", "Unit Tests (fast, isolated)"),
        ("integration", "Integration Tests"),
        ("regression", "Regression Tests")
    ]
    
    overall_success = True
    
    for category, description in test_categories:
        print(f"\n📋 Running {description}...")
        print("-" * 40)
        
        try:
            # Run pytest for this category
            result = subprocess.run([
                sys.executable, "-m", "pytest",
                "-v",
                "-m", category,
                "--tb=short",
                "--disable-warnings"
            ], 
            capture_output=True, 
            text=True,
            timeout=60  # 1 minute timeout per category
            )
            
            if result.returncode == 0:
                print(f"✅ {description} PASSED")
                if result.stdout:
                    # Show summary line only
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'passed' in line and ('warning' in line or 'error' in line or 'failed' in line):
                            print(f"   📊 {line.strip()}")
                            break
            else:
                print(f"❌ {description} FAILED")
                overall_success = False
                
                # Show errors
                if result.stdout:
                    print("STDOUT:")
                    print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
                if result.stderr:
                    print("STDERR:")  
                    print(result.stderr[:500] + "..." if len(result.stderr) > 500 else result.stderr)
        
        except subprocess.TimeoutExpired:
            print(f"⏰ {description} TIMED OUT (>60s)")
            overall_success = False
        except Exception as e:
            print(f"💥 {description} ERROR: {e}")
            overall_success = False
    
    # Also run tests without markers (catch all)
    print(f"\n📋 Running All Available Tests...")
    print("-" * 40)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/",
            "-v", 
            "--tb=line",
            "--disable-warnings",
            "-x"  # Stop on first failure
        ], 
        capture_output=True, 
        text=True,
        timeout=120  # 2 minute timeout
        )
        
        if result.returncode == 0:
            print("✅ All Tests PASSED")
        else:
            print("❌ Some Tests FAILED")
            overall_success = False
            
        # Show summary
        if result.stdout:
            lines = result.stdout.split('\n')
            for line in lines[-10:]:  # Last 10 lines usually have summary
                if line.strip() and ('passed' in line or 'failed' in line or 'error' in line):
                    print(f"   📊 {line.strip()}")
    
    except subprocess.TimeoutExpired:
        print("⏰ All Tests TIMED OUT")
        overall_success = False
    except Exception as e:
        print(f"💥 Test Execution ERROR: {e}")
        overall_success = False
    
    print("\n" + "=" * 60)
    if overall_success:
        print("🎉 ALL PYTEST TESTS COMPLETED SUCCESSFULLY!")
        print("✅ Pydantic integration has not broken existing functionality.")
    else:
        print("⚠️  SOME TESTS FAILED - REVIEW NEEDED")
        print("❌ There may be regressions from Pydantic integration.")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    exit(main())
