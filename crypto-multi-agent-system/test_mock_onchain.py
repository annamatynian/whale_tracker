"""
Mock test for OnChain analysis integration
Tests the system with fake data to verify pipeline works
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Set mock mode via environment variable
os.environ['MOCK_MODE'] = 'true'

from agents.orchestrator.simple_orchestrator import SimpleOrchestrator

async def test_mock_analysis():
    """Test the analysis pipeline with mock data."""
    print("Starting mock test of OnChain analysis integration...")
    
    try:
        # Initialize orchestrator (will use mock mode due to env var)
        orchestrator = SimpleOrchestrator()
        
        # Run analysis pipeline
        alerts = await orchestrator.run_analysis_pipeline()
        
        print(f"\nMock test results:")
        print(f"Generated alerts: {len(alerts)}")
        
        for i, alert in enumerate(alerts, 1):
            print(f"\nAlert #{i}:")
            print(f"  Token: {alert['token_symbol']}")
            print(f"  Score: {alert['final_score']}")
            print(f"  Recommendation: {alert['recommendation']}")
            print(f"  OnChain Analysis: {'Yes' if alert.get('has_onchain_analysis') else 'No'}")
        
        return len(alerts) > 0
        
    except Exception as e:
        print(f"Mock test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_mock_analysis())
    if result:
        print("\nMock test completed - pipeline functioning")
    else:
        print("\nMock test failed - check configuration")
