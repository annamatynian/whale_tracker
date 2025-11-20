"""
Test Runner for Market Conditions Agent

This script provides an easy way to run all tests with proper reporting.
"""

import subprocess
import sys
import os

def run_unit_tests():
    """Run unit tests with detailed output."""
    print("🧪 Running Unit Tests...")
    print("=" * 50)
    
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/unit/test_market_agent.py",
        "-v", "--tb=short", "--color=yes"
    ]
    
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.dirname(__file__)))
    return result.returncode == 0

def run_integration_tests():
    """Run integration tests (requires internet connection)."""
    print("\n🌐 Running Integration Tests...")
    print("=" * 50)
    print("⚠️  Note: These tests require internet connection to CoinGecko API")
    
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/integration/test_market_agent_integration.py",
        "-v", "--tb=short", "--color=yes", "-m", "integration"
    ]
    
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.dirname(__file__)))
    return result.returncode == 0

def run_quick_smoke_test():
    """Run a quick smoke test of the agent."""
    print("\n🚀 Running Quick Smoke Test...")
    print("=" * 50)
    
    try:
        # Add agents to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents'))
        
        from market_conditions.market_agent import analyze_market_conditions
        
        print("   Executing analyze_market_conditions()...")
        result = analyze_market_conditions()
        
        print(f"   ✅ Success!")
        print(f"   Market Regime: {result.market_regime}")
        print(f"   USDT Dominance: {result.usdt_dominance_percentage:.2f}%")
        print(f"   Processing Time: {result.processing_time_ms:.1f}ms")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

def main():
    """Main test runner."""
    print("🔍 Market Conditions Agent - Test Suite")
    print("=" * 60)
    
    all_passed = True
    
    # Run unit tests
    if not run_unit_tests():
        all_passed = False
        print("❌ Unit tests failed!")
    else:
        print("✅ Unit tests passed!")
    
    # Run integration tests
    if not run_integration_tests():
        all_passed = False
        print("❌ Integration tests failed!")
    else:
        print("✅ Integration tests passed!")
    
    # Run smoke test
    if not run_quick_smoke_test():
        all_passed = False
        print("❌ Smoke test failed!")
    else:
        print("✅ Smoke test passed!")
    
    # Final report
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! Market Conditions Agent is ready!")
        print("\n📋 Next Steps:")
        print("   1. git add .")
        print("   2. git commit -m 'Market Conditions Agent - All tests passing'")
        print("   3. git tag v0.1-market-agent-stable")
    else:
        print("💥 SOME TESTS FAILED! Please fix issues before proceeding.")
        sys.exit(1)

if __name__ == "__main__":
    main()
