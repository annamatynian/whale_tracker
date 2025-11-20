#!/usr/bin/env python3
"""
Test all 4 previously failing tests
"""

import subprocess
import sys
import os

def run_all_fixed_tests():
    """Run all 4 tests that were previously failing."""
    
    tests = [
        "tests/integration/test_integration_stage1.py::TestStage1MultiPoolManagerIntegration::test_load_positions_from_json",
        "tests/integration/test_integration_stage1.py::TestStage1CompleteWorkflow::test_complete_stage1_workflow", 
        "tests/integration/test_integration_stage2.py::TestStage2MultiPoolManagerLiveData::test_analyze_all_pools_with_live_data",
        "tests/integration/test_integration_stage2.py::TestStage2CompleteWorkflow::test_complete_stage2_workflow"
    ]
    
    print("🧪 Running all 4 previously failing tests...")
    print("=" * 60)
    
    cmd = [sys.executable, "-m", "pytest"] + tests + ["-v"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
        
        print(f"\nReturn code: {result.returncode}")
        
        if result.returncode == 0:
            print("\n🎉 SUCCESS! All 4 tests are now PASSING!")
        else:
            print("\n⚠️  Some tests still failing. Check output above.")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("❌ Tests timed out after 120 seconds")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = run_all_fixed_tests()
    sys.exit(0 if success else 1)
