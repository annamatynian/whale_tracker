"""
Windows-compatible quick system test - ASCII only
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def quick_test():
    """Quick test of main components - Windows compatible"""
    
    print("QUICK SYSTEM TEST")
    print("=" * 50)
    
    results = {}
    
    # Test 1: Basic imports
    try:
        from agents.orchestrator.simple_orchestrator import SimpleOrchestrator
        from agents.pump_analysis.pump_discovery_agent import PumpDiscoveryAgent
        from agents.pump_analysis.realistic_scoring import RealisticScoringMatrix
        results['imports'] = True
        print("OK Imports: PASS")
    except Exception as e:
        results['imports'] = False
        print(f"ERROR Imports: {e}")
    
    # Test 2: Orchestrator initialization
    try:
        orchestrator = SimpleOrchestrator()
        results['orchestrator'] = True
        print("OK Orchestrator: PASS")
    except Exception as e:
        results['orchestrator'] = False
        print(f"ERROR Orchestrator: {e}")
    
    # Test 3: Discovery agent initialization
    try:
        discovery = PumpDiscoveryAgent()
        results['discovery'] = True
        print("OK Discovery Agent: PASS")
    except Exception as e:
        results['discovery'] = False
        print(f"ERROR Discovery Agent: {e}")
    
    # Test 4: Scoring system
    try:
        from agents.pump_analysis.realistic_scoring import RealisticPumpIndicators
        from agents.pump_analysis.pump_models import NarrativeType
        
        indicators = RealisticPumpIndicators(
            narrative_type=NarrativeType.AI,
            has_trending_narrative=True,
            coingecko_score=8.0,
            is_honeypot=False,
            is_open_source=True,
            buy_tax_percent=1.0,
            sell_tax_percent=1.0
        )
        
        matrix = RealisticScoringMatrix(indicators=indicators)
        analysis = matrix.get_detailed_analysis()
        
        if analysis['total_score'] > 0:
            results['scoring'] = True
            print(f"OK Scoring System: PASS ({analysis['total_score']}/105 points)")
        else:
            results['scoring'] = False
            print("ERROR Scoring System: Zero score")
            
    except Exception as e:
        results['scoring'] = False
        print(f"ERROR Scoring System: {e}")
    
    # Test 5: Configuration
    try:
        from agents.orchestrator.simple_orchestrator import FUNNEL_CONFIG
        if all(key in FUNNEL_CONFIG for key in ['top_n_for_onchain', 'min_score_for_alert', 'api_calls_threshold']):
            results['config'] = True
            print("OK Configuration: PASS")
        else:
            results['config'] = False
            print("ERROR Configuration: Missing keys")
    except Exception as e:
        results['config'] = False
        print(f"ERROR Configuration: {e}")
    
    # Summary
    passed = sum(results.values())
    total = len(results)
    success_rate = (passed / total) * 100
    
    print(f"\nQUICK TEST RESULTS:")
    print(f"   Passed: {passed}/{total}")
    print(f"   Success Rate: {success_rate:.1f}%")
    
    if passed == total:
        print(f"\nSUCCESS: ALL BASIC COMPONENTS WORKING!")
        print("   System ready for detailed testing")
        print("   Run: python test_master_suite.py")
        
    elif passed >= total * 0.8:
        print(f"\nPARTIAL SUCCESS: SYSTEM MOSTLY WORKING!")
        print("   Minor issues but critical components OK")
        print("   Can continue testing")
        
    else:
        print(f"\nFAILED: SERIOUS PROBLEMS!")
        print("   Critical components not working")
        print("   Fix errors before continuing")
    
    return passed == total

if __name__ == "__main__":
    success = quick_test()
    exit(0 if success else 1)
