"""
Step-by-step test to find where the system hangs
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

print("Step 1: Setting up mock mode...")
os.environ['MOCK_MODE'] = 'true'
print("   Mock mode set")

print("\nStep 2: Importing SimpleOrchestrator...")
from agents.orchestrator.simple_orchestrator import SimpleOrchestrator
print("   Import successful")

print("\nStep 3: Creating orchestrator instance...")
try:
    orchestrator = SimpleOrchestrator()
    print("   Orchestrator created successfully")
except Exception as e:
    print(f"   FAILED to create orchestrator: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\nStep 4: Testing individual components...")

# Test discovery agent
try:
    print("   Testing discovery agent...")
    discovery_agent = orchestrator.discovery_agent
    print("   Discovery agent: OK")
except Exception as e:
    print(f"   Discovery agent FAILED: {e}")

# Test onchain agent  
try:
    print("   Testing onchain agent...")
    onchain_agent = orchestrator.onchain_agent
    print("   OnChain agent: OK")
except Exception as e:
    print(f"   OnChain agent FAILED: {e}")

print("\nStep 5: Testing simple async operation...")
async def simple_test():
    print("   Inside async function")
    await asyncio.sleep(0.1)
    print("   Async operation completed")
    return "success"

try:
    result = asyncio.run(simple_test())
    print(f"   Async test result: {result}")
except Exception as e:
    print(f"   Async test FAILED: {e}")

print("\nAll steps completed. If you see this, the basic setup works.")
print("The issue is likely in the run_analysis_pipeline method.")
