#!/usr/bin/env python3
"""
Stage 1 Integration Test Verification
====================================

Quick verification that our new pytest integration is working correctly.
"""

import subprocess
import sys
from pathlib import Path

def run_pytest_command(command, description):
    """Run a pytest command and return the result."""
    print(f"\n🧪 {description}")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print("✅ PASSED")
            if result.stdout:
                # Show only the summary line
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'passed' in line and 'failed' in line:
                        print(f"   {line.strip()}")
                        break
        else:
            print("❌ FAILED")
            print("STDOUT:", result.stdout[-200:])  # Last 200 chars
            print("STDERR:", result.stderr[-200:])  # Last 200 chars
            
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Run verification tests."""
    print("🎯 STAGE 1 PYTEST INTEGRATION VERIFICATION")
    print("=" * 55)
    
    # Change to project directory
    project_dir = Path(__file__).parent
    print(f"Project directory: {project_dir}")
    
    tests = [
        # Test 1: Check if pytest can discover our new test
        (
            "python -m pytest tests/test_integration_stage1.py --collect-only",
            "Test Discovery - Can pytest find our new tests?"
        ),
        
        # Test 2: Run only unit tests from Stage 1
        (
            "python -m pytest tests/test_integration_stage1.py -m 'stage1 and unit' -v",
            "Unit Tests - Fast isolated tests"
        ),
        
        # Test 3: Test our new fixtures work
        (
            "python -m pytest tests/test_integration_stage1.py::TestStage1PositionConfiguration::test_position_has_required_fields -v",
            "Fixtures Test - Do our new fixtures work?"
        ),
        
        # Test 4: Check markers are recognized
        (
            "python -m pytest --markers | grep stage1",
            "Markers Check - Are stage1 markers recognized?"
        )
    ]
    
    success_count = 0
    total_tests = len(tests)
    
    for command, description in tests:
        if run_pytest_command(command, description):
            success_count += 1
    
    print("\n" + "=" * 55)
    print(f"📊 VERIFICATION RESULTS: {success_count}/{total_tests} PASSED")
    
    if success_count == total_tests:
        print("🎉 STAGE 1 PYTEST INTEGRATION SUCCESSFUL!")
        print("✅ All tests discoverable")
        print("✅ Fixtures working")
        print("✅ Markers configured")
        print("✅ Ready for Stage 2 integration")
    else:
        print("⚠️  Some issues detected. Check output above.")
        print("💡 This is normal in development - some dependencies may be missing")
    
    print("\n🚀 NEXT STEPS:")
    print("1. Run: pytest tests/test_integration_stage1.py -m stage1 -v")
    print("2. Integrate test_stage2_final.py next")
    print("3. Continue with remaining HIGH PRIORITY files")

if __name__ == "__main__":
    main()
