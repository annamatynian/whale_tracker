"""
Architectural Principles Checker for Market Conditions Agent

This script verifies compliance with our architectural principles.
Run this before committing to ensure quality standards.
"""

import sys
import os
import subprocess
import time
from unittest.mock import patch

# Add agents to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'agents'))

def check_principle_1_simplicity():
    """Principle #1: Maximum simplicity - verify code structure."""
    print("🔍 Checking Principle #1: Maximum Simplicity...")
    
    # Check that market_agent.py is not overly complex
    agent_file = os.path.join(os.path.dirname(__file__), '..', 'agents', 'market_conditions', 'market_agent.py')
    
    with open(agent_file, 'r') as f:
        lines = f.readlines()
    
    # Simple metrics
    total_lines = len(lines)
    code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
    
    print(f"   📄 Total lines: {total_lines}")
    print(f"   💻 Code lines: {code_lines}")
    
    # Simplicity checks
    if code_lines < 300:
        print("   ✅ Code is concise and readable")
        return True
    else:
        print("   ⚠️  Code might be getting complex")
        return False

def check_principle_2_data_contracts():
    """Principle #2: Strict data contracts - verify Pydantic usage."""
    print("\n🔍 Checking Principle #2: Strict Data Contracts...")
    
    try:
        from market_conditions.market_agent import MarketConditionsReport
        
        # Test invalid data is rejected
        try:
            MarketConditionsReport(
                market_regime="INVALID",
                usdt_dominance_percentage=150.0,
                data_source="Test"
            )
            print("   ❌ Pydantic validation not working!")
            return False
        except ValueError:
            print("   ✅ Pydantic properly validates input data")
            
        # Test valid data works
        report = MarketConditionsReport(
            market_regime="AGGRESSIVE",
            usdt_dominance_percentage=3.2,
            data_source="CoinGecko"
        )
        print("   ✅ Valid data creates model successfully")
        return True
        
    except Exception as e:
        print(f"   ❌ Error testing data contracts: {e}")
        return False

def check_principle_4_fault_tolerance():
    """Principle #4: Fault tolerance - verify graceful error handling."""
    print("\n🔍 Checking Principle #4: Fault Tolerance...")
    
    try:
        from market_conditions.market_agent import analyze_market_conditions
        
        # Test with completely broken API
        with patch('market_conditions.market_agent.fetch_coingecko_global_data') as mock_fetch:
            mock_fetch.side_effect = Exception("Catastrophic failure")
            
            result = analyze_market_conditions()
            
            if result.market_regime == "UNKNOWN" and result.usdt_dominance_percentage == 0.0:
                print("   ✅ Agent handles catastrophic API failure gracefully")
                return True
            else:
                print("   ❌ Agent didn't handle API failure properly")
                return False
                
    except Exception as e:
        print(f"   ❌ Agent crashed instead of handling error: {e}")
        return False

def check_principle_6_observability():
    """Principle #6: Observability - verify logging works."""
    print("\n🔍 Checking Principle #6: Observability...")
    
    try:
        import logging
        import io
        
        # Capture logs
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.INFO)
        
        logger = logging.getLogger('market_conditions.market_agent')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        
        # Run agent
        from market_conditions.market_agent import analyze_market_conditions
        result = analyze_market_conditions()
        
        # Check logs
        log_output = log_capture.getvalue()
        
        required_logs = [
            "Starting market conditions analysis",
        ]
        
        missing_logs = []
        for log_msg in required_logs:
            if log_msg not in log_output:
                missing_logs.append(log_msg)
        
        if missing_logs:
            print(f"   ❌ Missing required log messages: {missing_logs}")
            return False
        else:
            print("   ✅ All required log messages present")
            print(f"   📝 Sample log: {log_output.split('\\n')[0][:80]}...")
            return True
            
        logger.removeHandler(handler)
        
    except Exception as e:
        print(f"   ❌ Error testing observability: {e}")
        return False

def check_principle_7_reproducibility():
    """Principle #7: Reproducibility - verify git hash tracking."""
    print("\n🔍 Checking Principle #7: Reproducibility...")
    
    try:
        from market_conditions.market_agent import get_current_git_hash, analyze_market_conditions
        
        # Test git hash function
        git_hash = get_current_git_hash()
        
        if git_hash and len(git_hash) > 0:
            print(f"   ✅ Git hash captured: {git_hash}")
        else:
            print("   ⚠️  Git hash not available (might be OK in some environments)")
        
        # Test that git hash is included in analysis
        result = analyze_market_conditions()
        
        if hasattr(result, 'git_commit_hash'):
            print("   ✅ Git hash field present in output")
            return True
        else:
            print("   ❌ Git hash field missing from output")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing reproducibility: {e}")
        return False

def check_principle_8_security():
    """Principle #8: Security - verify no hardcoded secrets."""
    print("\n🔍 Checking Principle #8: Security...")
    
    agent_file = os.path.join(os.path.dirname(__file__), '..', 'agents', 'market_conditions', 'market_agent.py')
    
    with open(agent_file, 'r') as f:
        content = f.read()
    
    # Look for potential security issues
    security_issues = []
    
    # Check for hardcoded API keys (common patterns)
    if 'api_key' in content.lower() or 'secret' in content.lower():
        security_issues.append("Potential hardcoded API key/secret")
    
    # Check for hardcoded URLs (should be configurable)
    if content.count('https://') > 1:  # More than one URL might indicate hardcoding
        print("   ⚠️  Multiple hardcoded URLs found - consider making configurable")
    
    if security_issues:
        print(f"   ❌ Security issues found: {security_issues}")
        return False
    else:
        print("   ✅ No obvious security issues detected")
        return True

def check_performance_metrics():
    """Verify performance metrics are captured."""
    print("\n🔍 Checking Performance Metrics...")
    
    try:
        from market_conditions.market_agent import analyze_market_conditions
        
        start_time = time.time()
        result = analyze_market_conditions()
        end_time = time.time()
        
        wall_time = (end_time - start_time) * 1000
        
        checks = []
        
        # Check metrics are present
        if result.processing_time_ms is not None:
            checks.append("✅ Processing time captured")
        else:
            checks.append("❌ Processing time missing")
        
        if result.market_regime != "UNKNOWN" and result.api_response_time_ms is not None:
            checks.append("✅ API response time captured")
        else:
            checks.append("⚠️  API response time not captured (might be due to API failure)")
        
        # Check reasonable performance
        if wall_time < 30000:  # 30 seconds
            checks.append("✅ Execution time reasonable")
        else:
            checks.append("❌ Execution time too slow")
        
        for check in checks:
            print(f"   {check}")
        
        print(f"   📊 Wall time: {wall_time:.1f}ms")
        print(f"   📊 Reported processing: {result.processing_time_ms:.1f}ms")
        
        return all("✅" in check for check in checks)
        
    except Exception as e:
        print(f"   ❌ Error testing performance: {e}")
        return False

def main():
    """Run all architectural principle checks."""
    print("🏗️  Market Conditions Agent - Architectural Principles Check")
    print("=" * 70)
    
    checks = [
        ("Principle #1: Simplicity", check_principle_1_simplicity),
        ("Principle #2: Data Contracts", check_principle_2_data_contracts),
        ("Principle #4: Fault Tolerance", check_principle_4_fault_tolerance),
        ("Principle #6: Observability", check_principle_6_observability),
        ("Principle #7: Reproducibility", check_principle_7_reproducibility),
        ("Principle #8: Security", check_principle_8_security),
        ("Performance Metrics", check_performance_metrics),
    ]
    
    results = []
    
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"   💥 {name} check failed with error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("📋 ARCHITECTURAL COMPLIANCE SUMMARY")
    print("=" * 70)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:<10} {name}")
        if result:
            passed += 1
    
    print("-" * 70)
    print(f"TOTAL: {passed}/{total} checks passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ALL ARCHITECTURAL PRINCIPLES SATISFIED!")
        print("   Agent is ready for production use.")
        return True
    else:
        print(f"\n⚠️  {total-passed} ISSUES NEED ATTENTION")
        print("   Please fix issues before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
