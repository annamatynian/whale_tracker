#!/usr/bin/env python3
"""
Regression Test - Windows Compatible Version
===========================================

Quick regression test to verify that Pydantic integration didn't break anything.
Windows console compatible version without Unicode emoji.

Author: Generated for DeFi-RAG Project  
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test that all modules can be imported."""
    print("1. Testing module imports...")
    
    try:
        from src.position_models import LPPosition, TokenInfo
        print("   [OK] position_models imports successfully")
    except Exception as e:
        print(f"   [ERROR] position_models import error: {e}")
        return False
    
    try:
        from src.position_manager import PositionManager, create_example_position
        print("   [OK] position_manager imports successfully")
    except Exception as e:
        print(f"   [ERROR] position_manager import error: {e}")
        return False
    
    return True

def test_pydantic_models():
    """Test Pydantic model creation and validation."""
    print("2. Testing Pydantic models...")
    
    try:
        from src.position_models import LPPosition, TokenInfo, create_example_position_model
        
        # Test TokenInfo creation
        token = TokenInfo(
            symbol="WETH",
            address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        )
        print(f"   [OK] TokenInfo created: {token.symbol}")
        
        # Test example position model
        position = create_example_position_model()
        print(f"   [OK] Example position created: {position.name}")
        
        # Test validation (should fail)
        try:
            invalid_token = TokenInfo(symbol="", address="invalid")
            print("   [ERROR] Validation should have failed")
            return False
        except Exception:
            print("   [OK] Validation correctly rejected invalid data")
        
        return True
        
    except Exception as e:
        print(f"   [ERROR] Pydantic model error: {e}")
        return False

def test_position_manager():
    """Test PositionManager functionality."""
    print("3. Testing PositionManager...")
    
    try:
        from src.position_manager import PositionManager, create_example_position
        
        # Create manager with temp directory
        import tempfile
        temp_dir = tempfile.mkdtemp()
        pm = PositionManager(data_dir=temp_dir)
        print("   [OK] PositionManager created")
        
        # Test example position creation
        example_dict = create_example_position()
        print(f"   [OK] Example position dict: {example_dict['name']}")
        
        # Test adding position
        success = pm.add_position(example_dict)
        print(f"   [OK] Position added: {success}")
        
        # Test loading positions
        positions = pm.load_positions()
        print(f"   [OK] Loaded {len(positions)} positions")
        
        if positions:
            pos = positions[0]
            print(f"   [OK] Position type: {type(pos)}")
            print(f"   [OK] Position name: {pos.name}")
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        print("   [OK] Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"   [ERROR] PositionManager error: {e}")
        return False

def test_existing_data():
    """Test loading existing position data."""
    print("4. Testing existing data compatibility...")
    
    try:
        from src.position_manager import PositionManager
        
        # Test with actual data directory
        pm = PositionManager()
        positions = pm.load_positions()
        print(f"   [OK] Loaded {len(positions)} existing positions")
        
        for i, pos in enumerate(positions):
            print(f"   [OK] Position {i+1}: {pos.name} ({type(pos)})")
        
        return True
        
    except Exception as e:
        print(f"   [ERROR] Existing data error: {e}")
        return False

def main():
    """Run all regression tests."""
    print("RUNNING Regression Tests for Pydantic Integration")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_pydantic_models, 
        test_position_manager,
        test_existing_data
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
                print("   [PASSED]")
            else:
                failed += 1
                print("   [FAILED]")
        except Exception as e:
            failed += 1
            print(f"   [FAILED] with exception: {e}")
        print()
    
    print("=" * 60)
    print(f"Regression Test Results:")
    print(f"   [OK] Passed: {passed}")
    print(f"   [ERROR] Failed: {failed}")
    print(f"   Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\nALL REGRESSION TESTS PASSED! Pydantic integration is stable.")
        return 0
    else:
        print(f"\n{failed} regression test(s) FAILED! Please review.")
        return 1

if __name__ == "__main__":
    exit(main())
