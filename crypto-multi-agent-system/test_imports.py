"""
Quick test to verify the orchestrator imports work correctly
"""
import os
import sys

# Fix Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    print("Testing TheGraph Discovery Agent import...")
    from agents.discovery.thegraph_discovery_agent_part5 import TheGraphPumpDiscoveryAgent
    print("✓ TheGraphPumpDiscoveryAgent import successful")
    
    print("Testing other required imports...")
    from tools.market_data.coingecko_client import CoinGeckoClient
    from tools.security.goplus_client import GoPlusClient
    from agents.pump_analysis.realistic_scoring import RealisticScoringMatrix
    from agents.onchain.onchain_agent import OnChainAgent
    from database.database_manager import DatabaseManager
    print("✓ All imports successful")
    
    print("Testing orchestrator class...")
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from agents.orchestrator.simple_orchestrator import SimpleOrchestrator
    print("✓ SimpleOrchestrator import successful")
    
    print("\n🎯 All imports working correctly!")
    print("Your production deployment is ready to run.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Need to fix import paths")
except Exception as e:
    print(f"❌ Other error: {e}")
