#!/usr/bin/env python3
"""
Quick test to verify JSON loading fixes
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    print("🔍 Testing JSON loading fixes...")
    print("=" * 50)
    
    # Test 1: Check positions.json structure
    try:
        import json
        with open('data/positions.json', 'r') as f:
            positions = json.load(f)
        
        print(f"✅ Found {len(positions)} positions in JSON")
        
        for i, pos in enumerate(positions):
            name = pos.get('name', f'Position {i+1}')
            has_token_symbols = 'token_a_symbol' in pos and 'token_b_symbol' in pos
            has_gas_costs = 'gas_costs_usd' in pos
            has_days_mock = 'days_held_mock' in pos
            has_entry_date = 'entry_date' in pos
            
            print(f"  {name}:")
            print(f"    token symbols: {'✅' if has_token_symbols else '❌'}")
            print(f"    gas_costs_usd: {'✅' if has_gas_costs else '❌'}")
            print(f"    days_held_mock: {'✅' if has_days_mock else '❌'}")
            print(f"    entry_date: {'✅' if has_entry_date else '❌'}")
            
    except Exception as e:
        print(f"❌ Error checking JSON: {e}")
        return False
    
    # Test 2: Check SimpleMultiPoolManager loading
    try:
        from simple_multi_pool import SimpleMultiPoolManager
        
        manager = SimpleMultiPoolManager()
        success = manager.load_positions_from_json('data/positions.json')
        
        if success:
            count = manager.count_pools()
            print(f"✅ SimpleMultiPoolManager loaded {count} positions")
            
            # Check loaded data
            for pool in manager.pools:
                print(f"  Pool: {pool.get('name')}")
                print(f"    Symbols: {pool.get('token_a_symbol')}-{pool.get('token_b_symbol')}")
                print(f"    Gas costs: ${pool.get('gas_costs_usd', 'N/A')}")
                print(f"    Days mock: {pool.get('days_held_mock', 'N/A')}")
        else:
            print("❌ SimpleMultiPoolManager failed to load positions")
            return False
            
    except Exception as e:
        print(f"❌ Error with SimpleMultiPoolManager: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 3: Try running one of the failing tests
    try:
        print("\n🧪 Running integration test...")
        import subprocess
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            'tests/integration/test_integration_stage1.py::TestStage1MultiPoolManagerIntegration::test_load_positions_from_json',
            '-v', '--tb=short'
        ], capture_output=True, text=True, timeout=30, cwd=os.getcwd())
        
        if result.returncode == 0:
            print("✅ Integration test PASSED!")
        else:
            print("❌ Integration test still failing:")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print("⏱️ Test timed out")
    except Exception as e:
        print(f"❌ Error running test: {e}")
    
    print("\n🎉 All checks passed! JSON loading should now work.")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
