"""
Quick test runner for Volume Ratio Health Check
Runs all related tests in sequence
"""

import subprocess
import sys

def run_test(test_name, command):
    """Run a test and report results."""
    print("\n" + "=" * 80)
    print(f"Running: {test_name}")
    print("=" * 80)
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=r'C:\Users\annam\Documents\DeFi-RAG-Project\crypto-multi-agent-system'
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print(f"\n✅ {test_name}: PASSED")
            return True
        else:
            print(f"\n❌ {test_name}: FAILED (exit code {result.returncode})")
            return False
            
    except Exception as e:
        print(f"\n❌ {test_name}: ERROR - {e}")
        return False


def main():
    """Run all Volume Ratio Health Check tests."""
    print("=" * 80)
    print("VOLUME RATIO HEALTH CHECK - TEST SUITE")
    print("=" * 80)
    
    results = []
    
    # Test 1: Built-in unit tests
    results.append(run_test(
        "Built-in Unit Tests (volume_metrics_extension.py)",
        "python agents/discovery/volume_metrics_extension.py"
    ))
    
    # Test 2: Comprehensive test
    results.append(run_test(
        "Comprehensive Health Check Test",
        "python test_volume_ratio_health_check.py"
    ))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("\n✅ Volume Ratio Health Check implementation is COMPLETE")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    print("=" * 80)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
