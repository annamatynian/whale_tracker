#!/usr/bin/env python3
"""
Test Pydantic Integration - LP Health Tracker
============================================

Quick test to verify Pydantic models work correctly with position_manager.py

Author: Generated for DeFi-RAG Project
"""

import sys
import json
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.position_manager import PositionManager, create_example_position
from src.position_models import LPPosition, TokenInfo, SupportedNetwork, SupportedProtocol


def test_pydantic_integration():
    """Test Pydantic integration with PositionManager."""
    
    print("🧪 Testing Pydantic Integration...")
    print("=" * 50)
    
    # Test 1: Create example position using Pydantic model
    print("1. Creating example position...")
    example_position = create_example_position()
    print(f"   ✅ Created position: {example_position.name}")
    print(f"   ✅ Type: {type(example_position)}")
    
    # Test 2: Initialize PositionManager
    print("\n2. Initializing PositionManager...")
    pm = PositionManager("data")
    print("   ✅ PositionManager initialized")
    
    # Test 3: Add position using Pydantic model
    print("\n3. Adding position using Pydantic model...")
    success = pm.add_position(example_position)
    print(f"   {'✅' if success else '❌'} Position added: {success}")
    
    # Test 4: Load positions and verify they are Pydantic models
    print("\n4. Loading positions...")
    positions = pm.load_positions()
    print(f"   ✅ Loaded {len(positions)} positions")
    
    if positions:
        first_position = positions[0]
        print(f"   ✅ Position type: {type(first_position)}")
        print(f"   ✅ Position name: {first_position.name}")
        print(f"   ✅ Token A: {first_position.token_a.symbol}")
        print(f"   ✅ Token B: {first_position.token_b.symbol}")
    
    # Test 5: Test dictionary conversion
    print("\n5. Testing dictionary conversion...")
    if positions:
        position_dict = positions[0].model_dump()
        print(f"   ✅ Converted to dict: {type(position_dict)}")
        print(f"   ✅ Dict keys: {list(position_dict.keys())}")
        
        # Test round-trip conversion
        reconstructed = LPPosition.model_validate(position_dict)
        print(f"   ✅ Reconstructed: {reconstructed.name}")
    
    # Test 6: Test position validation
    print("\n6. Testing position validation...")
    from src.position_manager import PositionValidator
    
    if positions:
        is_valid = PositionValidator.is_valid_position(positions[0])
        print(f"   {'✅' if is_valid else '❌'} Position validation: {is_valid}")
        
        risk_level = PositionValidator.get_position_risk_level(positions[0])
        print(f"   ✅ Risk level: {risk_level}")
    
    # Test 7: Test token info validation
    print("\n7. Testing token validation...")
    try:
        valid_token = TokenInfo(
            symbol="WETH",
            address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        )
        print(f"   ✅ Valid token created: {valid_token.symbol}")
    except Exception as e:
        print(f"   ❌ Token validation failed: {e}")
    
    try:
        invalid_token = TokenInfo(
            symbol="",  # Invalid: empty symbol
            address="invalid_address"  # Invalid: not proper format
        )
        print(f"   ❌ Should have failed but created: {invalid_token.symbol}")
    except Exception as e:
        print(f"   ✅ Correctly rejected invalid token: {str(e)[:50]}...")
    
    # Test 8: Export/Import test
    print("\n8. Testing export/import...")
    export_path = "test_export.json"
    
    export_success = pm.export_data(export_path)
    print(f"   {'✅' if export_success else '❌'} Export: {export_success}")
    
    if export_success:
        # Verify export file structure
        with open(export_path, 'r') as f:
            export_data = json.load(f)
        
        print(f"   ✅ Export file has keys: {list(export_data.keys())}")
        print(f"   ✅ Exported {len(export_data.get('positions', []))} positions")
        
        # Clean up
        Path(export_path).unlink(missing_ok=True)
        print("   ✅ Cleanup completed")
    
    print("\n" + "=" * 50)
    print("🎉 Pydantic Integration Test Completed!")


if __name__ == "__main__":
    test_pydantic_integration()
