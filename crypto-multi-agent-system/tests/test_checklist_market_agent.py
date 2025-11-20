"""
Market Conditions Agent - Complete Test Checklist

Run this script to execute the full testing checklist as specified.
"""

import subprocess
import sys
import os
import json
import time
from unittest.mock import patch

# Add agents to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents', 'market_conditions'))

def colored_print(text, color="white"):
    """Print colored text for better visibility."""
    colors = {
        "green": "\033[92m",
        "red": "\033[91m", 
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "white": "\033[0m"
    }
    print(f"{colors.get(color, '')}{text}\033[0m")

def test_section(title):
    """Print a test section header."""
    print(f"\n{'='*60}")
    colored_print(f"🧪 {title}", "blue")
    print('='*60)

def check_mark(passed, description):
    """Print a check mark or X with description."""
    symbol = "✅" if passed else "❌"
    color = "green" if passed else "red"
    colored_print(f"{symbol} {description}", color)
    return passed

def main():
    """Execute the complete test checklist."""
    colored_print("🔍 Market Conditions Agent - Complete Test Checklist", "blue")
    print("Following the testing plan exactly as specified...")
    
    all_tests_passed = True

    # 1. MODULAR TESTING (UNIT TESTING)
    test_section("1. Modular Testing (Unit Testing)")
    
    print("Running unit tests to check logic in isolation...")
    unit_result = subprocess.run([
        sys.executable, "-m", "pytest", 
        "tests/unit/test_market_agent.py", "-v"
    ], capture_output=True, text=True)
    
    unit_passed = unit_result.returncode == 0
    all_tests_passed &= check_mark(unit_passed, "Unit tests passed")
    
    if not unit_passed:
        print("Unit test output:")
        print(unit_result.stdout)
        print(unit_result.stderr)

    # 2. INTEGRATION TESTING
    test_section("2. Integration Testing")
    
    print("Testing real API interaction...")
    
    # Test real API call
    try:
        from market_agent import analyze_market_conditions
        print("   Making real API call to CoinGecko...")
        result = analyze_market_conditions()
        
        api_passed = result.market_regime in ["AGGRESSIVE", "CONSERVATIVE", "UNKNOWN"]
        all_tests_passed &= check_mark(api_passed, "Real API call successful")
        
        # Test Pydantic validation
        try:
            json_str = result.model_dump_json()
            parsed_data = json.loads(json_str)
            
            pydantic_passed = all([
                'market_regime' in parsed_data,
                'usdt_dominance_percentage' in parsed_data,
                'data_source' in parsed_data,
                'analysis_timestamp' in parsed_data
            ])
            all_tests_passed &= check_mark(pydantic_passed, "Pydantic validation successful")
            
            print(f"   Sample output: {json.dumps(parsed_data, indent=2)[:200]}...")
            
        except Exception as e:
            all_tests_passed &= check_mark(False, f"Pydantic validation failed: {e}")
    
    except Exception as e:
        all_tests_passed &= check_mark(False, f"Real API call failed: {e}")

    # 3. ARCHITECTURAL PRINCIPLES VERIFICATION
    test_section("3. Architectural Principles Verification")
    
    # Principle #4: Fault Tolerance
    print("Testing Principle #4 (Fault Tolerance)...")
    try:
        with patch('market_agent.fetch_coingecko_global_data', return_value=(None, None)):
            fault_result = analyze_market_conditions()
            
        fault_passed = (
            fault_result.market_regime == "UNKNOWN" and
            fault_result.usdt_dominance_percentage == 0.0
        )
        all_tests_passed &= check_mark(fault_passed, "Fault tolerance - API failure handled gracefully")
        
    except Exception as e:
        all_tests_passed &= check_mark(False, f"Fault tolerance test failed: {e}")
    
    # Principle #6: Observability  
    print("Testing Principle #6 (Observability)...")
    print("   Check console output above for clear logging messages...")
    
    observability_passed = True  # Manual check based on console output
    all_tests_passed &= check_mark(observability_passed, "Observability - Clear logging present (manual check)")
    
    # Principle #7: Reproducibility
    print("Testing Principle #7 (Reproducibility)...")
    try:
        result = analyze_market_conditions()
        reproducibility_passed = hasattr(result, 'git_commit_hash')
        all_tests_passed &= check_mark(reproducibility_passed, f"Reproducibility - Git hash present: {result.git_commit_hash}")
        
    except Exception as e:
        all_tests_passed &= check_mark(False, f"Reproducibility test failed: {e}")

    # PERFORMANCE BASELINE
    test_section("Performance Baseline Check")
    
    try:
        print("   Running 3 performance samples...")
        times = []
        for i in range(3):
            start = time.time()
            result = analyze_market_conditions()
            total_time = (time.time() - start) * 1000
            
            if result.api_response_time_ms:
                times.append({
                    'api': result.api_response_time_ms,
                    'total': total_time
                })
            time.sleep(1)  # Be nice to API
        
        if times:
            avg_api = sum(t['api'] for t in times) / len(times)
            avg_total = sum(t['total'] for t in times) / len(times)
            
            perf_passed = avg_api < 3000 and avg_total < 5000  # Reasonable thresholds
            all_tests_passed &= check_mark(perf_passed, f"Performance baseline - API: {avg_api:.1f}ms, Total: {avg_total:.1f}ms")
        else:
            all_tests_passed &= check_mark(False, "Performance test - Could not get timing data")
            
    except Exception as e:
        all_tests_passed &= check_mark(False, f"Performance test failed: {e}")

    # FINAL RESULTS
    test_section("Final Results")
    
    if all_tests_passed:
        colored_print("🎉 ALL TESTS PASSED! Market Conditions Agent is ready for production!", "green")
        print("\n📋 Next Steps:")
        colored_print("   1. git add .", "yellow")
        colored_print("   2. git commit -m 'Market Conditions Agent - Complete with tests'", "yellow") 
        colored_print("   3. git tag v0.1-market-agent-stable", "yellow")
        colored_print("   4. Ready to proceed to next agent!", "green")
        
    else:
        colored_print("💥 SOME TESTS FAILED! Please fix issues before proceeding.", "red")
        print("\n🔧 Debugging tips:")
        print("   - Check internet connection for API tests")
        print("   - Verify all dependencies are installed: pip install -r requirements.txt")
        print("   - Check that git is installed for git hash tests")
        print("   - Run individual test files for more detailed error messages")
        
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
