#!/usr/bin/env python3
"""
Run the specific failing integration tests to check if they're fixed
"""

import subprocess
import sys
import os

def run_failing_tests():
    """Run the 4 tests that were failing."""
    
    failing_tests = [
        'tests/integration/test_integration_stage1.py::TestStage1MultiPoolManagerIntegration::test_load_positions_from_json',
        'tests/integration/test_integration_stage1.py::TestStage1CompleteWorkflow::test_complete_stage1_workflow', 
        'tests/integration/test_integration_stage2.py::TestStage2MultiPoolManagerLiveData::test_analyze_all_pools_with_live_data',
        'tests/integration/test_integration_stage2.py::TestStage2CompleteWorkflow::test_complete_stage2_workflow'
    ]
    
    print("🧪 Running previously failing integration tests...")
    print("=" * 60)
    
    results = {}
    
    for test in failing_tests:
        print(f"\n🔍 Running: {test}")
        print("-" * 40)
        
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pytest', test, '-v', '--tb=short', '--no-header'
            ], capture_output=True, text=True, timeout=60, cwd=os.getcwd())
            
            if result.returncode == 0:
                print("✅ PASSED")
                results[test] = "PASSED"
            else:
                print("❌ FAILED")
                print("Output:", result.stdout[-500:])  # Last 500 chars
                if result.stderr:
                    print("Error:", result.stderr[-200:])  # Last 200 chars of error
                results[test] = "FAILED"
                
        except subprocess.TimeoutExpired:
            print("⏱️ TIMEOUT")
            results[test] = "TIMEOUT"
        except Exception as e:
            print(f"❌ ERROR: {e}")
            results[test] = "ERROR"
    
    # Summary
    print("\n📊 SUMMARY")
    print("=" * 60)
    
    passed_count = sum(1 for status in results.values() if status == "PASSED")
    total_count = len(results)
    
    for test, status in results.items():
        short_name = test.split("::")[-1]
        status_icon = {"PASSED": "✅", "FAILED": "❌", "TIMEOUT": "⏱️", "ERROR": "🔥"}[status]
        print(f"{status_icon} {short_name}: {status}")
    
    print(f"\nResult: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("🎉 All tests now PASSING! JSON loading issue is FIXED!")
        return True
    else:
        print("⚠️ Some tests still failing. Need more investigation.")
        return False

if __name__ == "__main__":
    success = run_failing_tests()
    sys.exit(0 if success else 1)
