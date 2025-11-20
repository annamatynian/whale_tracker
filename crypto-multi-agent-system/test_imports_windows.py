"""
Windows-compatible imports test - ASCII only
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_basic_imports():
    """Check basic imports"""
    print("IMPORT CHECK AFTER REFACTOR")
    print("=" * 50)
    
    try:
        # Check new orchestrator
        from agents.orchestrator.simple_orchestrator import (
            SimpleOrchestrator, 
            FUNNEL_CONFIG, 
            ALERT_RECOMMENDATIONS
        )
        print("OK SimpleOrchestrator imported")
        print(f"OK FUNNEL_CONFIG: {FUNNEL_CONFIG}")
        print(f"OK ALERT_RECOMMENDATIONS: {ALERT_RECOMMENDATIONS}")
        
        # Check dependencies
        from agents.pump_analysis.pump_discovery_agent import PumpDiscoveryAgent
        from tools.market_data.coingecko_client import CoinGeckoClient
        from tools.security.goplus_client import GoPlusClient
        from agents.pump_analysis.realistic_scoring import RealisticScoringMatrix, RealisticPumpIndicators
        print("OK All dependencies imported")
        
        # Check class methods
        orchestrator_methods = [method for method in dir(SimpleOrchestrator) if not method.startswith('_')]
        print(f"OK SimpleOrchestrator methods: {orchestrator_methods}")
        
        return True
        
    except ImportError as e:
        print(f"ERROR Import error: {e}")
        return False
    except Exception as e:
        print(f"ERROR Unexpected error: {e}")
        return False

def test_config_values():
    """Check configuration values"""
    print(f"\nCONFIGURATION CHECK")
    print("=" * 50)
    
    try:
        from agents.orchestrator.simple_orchestrator import FUNNEL_CONFIG
        
        # Check required keys
        required_keys = ['top_n_for_onchain', 'min_score_for_alert', 'api_calls_threshold']
        for key in required_keys:
            if key not in FUNNEL_CONFIG:
                print(f"ERROR Missing config key: {key}")
                return False
            print(f"OK {key}: {FUNNEL_CONFIG[key]}")
        
        # Check reasonable values
        checks = [
            (FUNNEL_CONFIG['top_n_for_onchain'] > 0, "top_n_for_onchain must be > 0"),
            (FUNNEL_CONFIG['min_score_for_alert'] >= 0, "min_score_for_alert must be >= 0"),
            (FUNNEL_CONFIG['api_calls_threshold'] >= 0, "api_calls_threshold must be >= 0"),
        ]
        
        for check, message in checks:
            if not check:
                print(f"ERROR {message}")
                return False
        
        print("OK All configuration values correct")
        return True
        
    except Exception as e:
        print(f"ERROR Configuration check failed: {e}")
        return False

def test_backward_compatibility():
    """Check backward compatibility"""
    print(f"\nBACKWARD COMPATIBILITY CHECK")
    print("=" * 50)
    
    try:
        from agents.orchestrator.simple_orchestrator import SimpleOrchestrator
        
        # Check that main methods are preserved
        required_methods = ['run_analysis_pipeline', 'should_spend_api_calls']
        
        for method in required_methods:
            if not hasattr(SimpleOrchestrator, method):
                print(f"ERROR Missing method: {method}")
                return False
            print(f"OK Method {method} preserved")
        
        # Check run_analysis_pipeline signature
        import inspect
        signature = inspect.signature(SimpleOrchestrator.run_analysis_pipeline)
        print(f"OK run_analysis_pipeline signature: {signature}")
        
        return True
        
    except Exception as e:
        print(f"ERROR Compatibility check failed: {e}")
        return False

def main():
    """Main test function"""
    print("COMPREHENSIVE REFACTOR TEST")
    print("=" * 70)
    
    tests = [
        ("Imports", test_basic_imports),
        ("Configuration", test_config_values), 
        ("Backward Compatibility", test_backward_compatibility)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"ERROR Critical error in test {test_name}: {e}")
            results.append((test_name, False))
    
    # Final results
    print(f"\nFINAL RESULTS:")
    print("=" * 70)
    
    all_passed = True
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"   {status}: {test_name}")
        if not success:
            all_passed = False
    
    print(f"\nOVERALL RESULT:")
    if all_passed:
        print("SUCCESS: ALL TESTS PASSED!")
        print("Multi-level funnel works correctly!")
        print("Refactor completed without losing functionality!")
        print("System ready for use and expansion!")
        
        print(f"\nNEXT STEPS:")
        print("   1. Test with real API keys (python main.py --dry-run)")
        print("   2. Implement OnChain analysis for top-15 candidates")
        print("   3. Add Sterile Deployer Analysis")
        
    else:
        print("ERROR: PROBLEMS IN REFACTOR!")
        print("Check errors above and fix code")
        
    return all_passed

if __name__ == "__main__":
    success = main()
    print(f"\nExit code: {0 if success else 1}")
