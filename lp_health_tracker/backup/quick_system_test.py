#!/usr/bin/env python3
"""
Quick System Test - LP Health Tracker
====================================

Quick validation that system works after recent changes.
Tests basic functionality without requiring API keys.
"""

import sys
import os
import json
from pathlib import Path

# Add project path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all core imports work."""
    print("🔍 Testing imports...")
    
    try:
        from src.data_analyzer import ImpermanentLossCalculator
        from src.simple_multi_pool import SimpleMultiPoolManager  
        from src.data_providers import MockDataProvider
        from config.settings import Settings
        print("✅ All core imports successful!")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_il_calculation():
    """Test IL calculation accuracy."""
    print("🔍 Testing IL calculation...")
    
    try:
        from src.data_analyzer import ImpermanentLossCalculator
        
        calc = ImpermanentLossCalculator()
        
        # Test known scenarios
        test_cases = [
            (2000.0, 2000.0, 0.0),      # No change
            (2000.0, 2500.0, 0.0062),   # +25% = ~0.62% IL
            (2000.0, 4000.0, 0.0572),   # +100% = ~5.72% IL
        ]
        
        for initial, current, expected in test_cases:
            il = calc.calculate_impermanent_loss(initial, current)
            if abs(il - expected) < 0.001:  # 0.1% tolerance
                print(f"✅ IL test passed: {initial}->{current} = {il:.4f}")
            else:
                print(f"❌ IL test failed: {initial}->{current} = {il:.4f}, expected {expected:.4f}")
                return False
        
        print("✅ IL calculation tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ IL calculation test failed: {e}")
        return False

def test_position_loading():
    """Test position loading from JSON."""
    print("🔍 Testing position loading...")
    
    try:
        # Test loading example positions
        positions_file = project_root / "data" / "positions.json.example"
        with open(positions_file, 'r') as f:
            positions = json.load(f)
        
        print(f"✅ Loaded {len(positions)} example positions")
        
        # Test production positions
        prod_positions_file = project_root / "data" / "positions.json"
        if prod_positions_file.exists():
            with open(prod_positions_file, 'r') as f:
                prod_positions = json.load(f)
            print(f"✅ Loaded {len(prod_positions)} production positions")
        else:
            print("ℹ️ No production positions file (normal for new setup)")
        
        return True
        
    except Exception as e:
        print(f"❌ Position loading failed: {e}")
        return False

def test_mock_provider():
    """Test mock data provider."""
    print("🔍 Testing mock data provider...")
    
    try:
        from src.data_providers import MockDataProvider
        from src.simple_multi_pool import SimpleMultiPoolManager
        
        # Create mock provider
        mock_provider = MockDataProvider({
            'WETH': 2500.0,  # +25% from usual 2000
            'USDC': 1.0,
            'USDT': 1.0
        })
        
        # Test price retrieval
        eth_price = mock_provider.get_token_price('WETH')
        usdc_price = mock_provider.get_token_price('USDC')
        
        if eth_price == 2500.0 and usdc_price == 1.0:
            print(f"✅ Mock provider working: ETH=${eth_price}, USDC=${usdc_price}")
        else:
            print(f"❌ Mock provider failed: ETH=${eth_price}, USDC=${usdc_price}")
            return False
        
        # Test manager with mock provider
        manager = SimpleMultiPoolManager(mock_provider)
        print("✅ Multi-pool manager created with mock provider")
        
        return True
        
    except Exception as e:
        print(f"❌ Mock provider test failed: {e}")
        return False

def test_settings():
    """Test settings loading."""
    print("🔍 Testing settings...")
    
    try:
        from config.settings import Settings
        
        settings = Settings()
        
        # Test basic settings
        print(f"✅ Settings loaded - Network: {settings.DEFAULT_NETWORK}")
        print(f"✅ Check interval: {settings.CHECK_INTERVAL_MINUTES} minutes")
        print(f"✅ IL threshold: {settings.DEFAULT_IL_THRESHOLD}")
        
        return True
        
    except Exception as e:
        print(f"❌ Settings test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 LP Health Tracker - Quick System Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_il_calculation,
        test_position_loading,
        test_mock_provider,
        test_settings
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Empty line between tests
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            print()
    
    print("=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! System is ready.")
        print("\nNext steps:")
        print("1. Copy .env.example to .env and add your API keys")
        print("2. Run: python run.py --test-config")
        print("3. Run: python run.py --list-positions")
        print("4. Ready for Stage 3: Web3Manager integration!")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
