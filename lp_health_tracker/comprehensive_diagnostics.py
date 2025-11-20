#!/usr/bin/env python3
"""
Check if all required modules can be imported successfully
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test if we can import all required modules."""
    print("🔍 Testing module imports...")
    print("=" * 40)
    
    modules_to_test = [
        ('simple_multi_pool', 'SimpleMultiPoolManager'),
        ('data_providers', 'MockDataProvider'),
        ('data_providers', 'LiveDataProvider'), 
        ('data_analyzer', 'NetPnLCalculator'),
        ('datetime_helpers', 'ensure_timezone_aware'),
        ('datetime_helpers', 'safe_datetime_diff_days'),
    ]
    
    failed_imports = []
    
    for module_name, class_or_func in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_or_func])
            obj = getattr(module, class_or_func)
            print(f"✅ {module_name}.{class_or_func}")
        except ImportError as e:
            print(f"❌ {module_name}.{class_or_func}: ImportError - {e}")
            failed_imports.append((module_name, class_or_func, e))
        except AttributeError as e:
            print(f"❌ {module_name}.{class_or_func}: AttributeError - {e}")
            failed_imports.append((module_name, class_or_func, e))
        except Exception as e:
            print(f"❌ {module_name}.{class_or_func}: {type(e).__name__} - {e}")
            failed_imports.append((module_name, class_or_func, e))
    
    if failed_imports:
        print(f"\n⚠️ {len(failed_imports)} import failures found:")
        for module_name, class_or_func, error in failed_imports:
            print(f"  {module_name}.{class_or_func}: {error}")
        return False
    else:
        print(f"\n✅ All {len(modules_to_test)} imports successful!")
        return True

def test_simple_json_loading():
    """Test JSON loading directly without pytest."""
    print("\n🔍 Testing JSON loading directly...")
    print("=" * 40)
    
    try:
        from simple_multi_pool import SimpleMultiPoolManager
        
        # Create manager
        manager = SimpleMultiPoolManager()
        print("✅ SimpleMultiPoolManager created")
        
        # Test file exists
        json_path = Path('data/positions.json')
        if not json_path.exists():
            print(f"❌ File not found: {json_path.absolute()}")
            return False
        print(f"✅ Found {json_path.absolute()}")
        
        # Load positions
        success = manager.load_positions_from_json('data/positions.json')
        if not success:
            print("❌ Failed to load positions")
            return False
        print("✅ Positions loaded successfully")
        
        # Check loaded data
        count = manager.count_pools()
        print(f"✅ Loaded {count} positions")
        
        # Check structure of loaded positions
        for i, pool in enumerate(manager.pools):
            name = pool.get('name', f'Pool {i+1}')
            required_fields = ['token_a_symbol', 'token_b_symbol', 'gas_costs_usd']
            missing_fields = [field for field in required_fields if field not in pool]
            
            if missing_fields:
                print(f"❌ {name} missing fields: {missing_fields}")
                return False
            else:
                print(f"✅ {name} has all required fields")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in JSON loading test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fixture_compatibility():
    """Test if our JSON data is compatible with pytest fixtures."""
    print("\n🔍 Testing fixture compatibility...")
    print("=" * 40)
    
    try:
        import json
        
        # Load our positions.json
        with open('data/positions.json', 'r') as f:
            positions = json.load(f)
        
        # Test each position against expected fixture format
        for i, position in enumerate(positions):
            print(f"Checking position {i+1}: {position.get('name', 'Unnamed')}")
            
            # Stage 1 requirements
            stage1_fields = ['gas_costs_usd', 'days_held_mock']
            stage1_ok = all(field in position for field in stage1_fields)
            print(f"  Stage 1 fields: {'✅' if stage1_ok else '❌'}")
            
            # Stage 2 requirements  
            stage2_fields = ['entry_date']
            stage2_ok = all(field in position for field in stage2_fields)
            print(f"  Stage 2 fields: {'✅' if stage2_ok else '❌'}")
            
            # Token symbol fields
            token_fields = ['token_a_symbol', 'token_b_symbol']
            token_ok = all(field in position for field in token_fields)
            print(f"  Token fields: {'✅' if token_ok else '❌'}")
            
            if not (stage1_ok and stage2_ok and token_ok):
                print(f"❌ Position {i+1} missing required fields")
                return False
        
        print("✅ All positions compatible with fixtures")
        return True
        
    except Exception as e:
        print(f"❌ Error in fixture compatibility test: {e}")
        return False

def main():
    """Run all diagnostic tests."""
    print("🚀 Comprehensive diagnostics for JSON loading issue")
    print("=" * 60)
    
    results = []
    
    # Test 1: Imports
    results.append(("Module Imports", test_imports()))
    
    # Test 2: Direct JSON loading
    results.append(("Direct JSON Loading", test_simple_json_loading()))
    
    # Test 3: Fixture compatibility
    results.append(("Fixture Compatibility", test_fixture_compatibility()))
    
    # Summary
    print("\n📊 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All diagnostics PASSED!")
        print("The JSON loading issue should be resolved.")
        print("Try running the integration tests now.")
    else:
        print("\n⚠️ Some diagnostics FAILED.")
        print("Additional fixes may be needed.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
