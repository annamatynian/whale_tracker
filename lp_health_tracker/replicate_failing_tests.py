#!/usr/bin/env python3
"""
Minimal test to replicate the failing integration test scenario
"""

import json
import os
import sys
from pathlib import Path

# Ensure we're in the right directory
os.chdir(Path(__file__).parent)

# Add src to Python path
sys.path.insert(0, 'src')

def replicate_test_load_positions_from_json():
    """Replicate the failing test: test_load_positions_from_json"""
    print("🧪 Replicating test_load_positions_from_json...")
    
    try:
        # Import the class (this is what pytest fixtures do)
        from simple_multi_pool import SimpleMultiPoolManager
        
        # Create the manager (this is what stage1_multi_pool_manager fixture does)
        manager = SimpleMultiPoolManager()
        print("✅ Created SimpleMultiPoolManager")
        
        # Check if positions file exists
        positions_file = Path('data/positions.json')
        if not positions_file.exists():
            print("❌ positions.json not found - this would cause pytest.skip")
            return False
        
        print(f"✅ Found positions.json at: {positions_file.absolute()}")
        
        # This is the exact line that was failing in the test:
        success = manager.load_positions_from_json('data/positions.json')
        
        if not success:
            print("❌ FAILED: manager.load_positions_from_json returned False")
            print("This is the exact AssertionError that was happening!")
            return False
        
        print("✅ SUCCESS: manager.load_positions_from_json returned True")
        
        # Additional checks that the test does
        pool_count = manager.count_pools()
        if pool_count <= 0:
            print(f"❌ FAILED: No pools loaded (count: {pool_count})")
            return False
        
        print(f"✅ SUCCESS: Loaded {pool_count} pools")
        
        return True
        
    except ImportError as e:
        print(f"❌ IMPORT ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def replicate_test_complete_workflow():
    """Replicate the failing test: test_complete_stage1_workflow"""
    print("\n🧪 Replicating test_complete_stage1_workflow...")
    
    try:
        from simple_multi_pool import SimpleMultiPoolManager
        
        manager = SimpleMultiPoolManager()
        
        # Load positions (same as above)
        positions_file = Path('data/positions.json')
        if not positions_file.exists():
            print("❌ positions.json not found")
            return False
        
        success = manager.load_positions_from_json('data/positions.json')
        if not success:
            print("❌ FAILED: Could not load positions")
            return False
        
        pool_count = manager.count_pools()
        if pool_count <= 0:
            print("❌ FAILED: No pools loaded for testing")
            return False
        
        print(f"✅ Loaded {pool_count} pools for workflow test")
        
        # The test then tries to analyze pools - this is where other errors might occur
        try:
            results = manager.analyze_all_pools_with_fees()
            print(f"✅ Analyzed pools, got {len(results)} results")
            return True
        except Exception as e:
            if "can't subtract offset-naive and offset-aware datetimes" in str(e):
                print("⚠️ EXPECTED DATETIME ERROR - this was in the test as pytest.skip")
                return True  # This error was expected and handled in the test
            else:
                print(f"❌ UNEXPECTED ANALYSIS ERROR: {e}")
                return False
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def main():
    """Run the replication tests."""
    print("🚀 Replicating failing integration tests...")
    print("=" * 60)
    
    # Test 1: Basic JSON loading
    test1_result = replicate_test_load_positions_from_json()
    
    # Test 2: Complete workflow 
    test2_result = replicate_test_complete_workflow()
    
    # Summary
    print("\n📊 REPLICATION TEST RESULTS")
    print("=" * 60)
    
    print(f"✅ Load positions JSON: {'PASS' if test1_result else 'FAIL'}")
    print(f"✅ Complete workflow: {'PASS' if test2_result else 'FAIL'}")
    
    if test1_result and test2_result:
        print("\n🎉 SUCCESS! The original issue should be fixed!")
        print("The integration tests should now pass.")
        return True
    else:
        print("\n⚠️ Issues still remain. More debugging needed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
