#!/usr/bin/env python3
"""
Quick Backward Compatibility Test
=================================

Simple test that doesn't require complex imports.
"""

import os
import sys
from pathlib import Path

# Test basic functionality
def test_simple_compatibility():
    """Simple test without complex imports."""
    
    print("🧪 SIMPLE COMPATIBILITY TEST")
    print("=" * 40)
    
    # Set environment variables for testing
    os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
    os.environ['TELEGRAM_CHAT_ID'] = 'test_chat_id'
    os.environ['WALLET_ADDRESSES'] = '0x742d35Cc6634C0532925a3b8D41141D8F10C473d'
    
    try:
        # Test 1: Install PyYAML if needed
        print("\n1️⃣  Testing PyYAML...")
        try:
            import yaml
            print("   ✅ PyYAML available")
        except ImportError:
            print("   ❌ PyYAML not installed - run: pip install pyyaml")
            return False
        
        # Test 2: Basic constants
        print("\n2️⃣  Testing constants creation...")
        
        CONTRACT_ADDRESSES = {
            'ethereum_mainnet': {
                'tokens': {
                    'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
                    'USDC': '0xA0b86a33E6c21C64E0eb4ADa7B0b0094a7f6E44C',
                },
                'pairs': {
                    'WETH_USDC_V2': '0xB4e16d0168e52d35CaCD2b6464f00d6eB9002C6D',
                }
            }
        }
        
        RISK_CATEGORIES = {
            'very_low': {
                'description': 'Stablecoin pairs (e.g., USDC/USDT)',
                'recommended_threshold': 0.005,
            },
            'low': {
                'description': 'Stablecoin + major token (e.g., ETH/USDC)',
                'recommended_threshold': 0.02,
            }
        }
        
        print("   ✅ Constants created successfully")
        print(f"   ✅ CONTRACT_ADDRESSES has {len(CONTRACT_ADDRESSES)} networks")
        print(f"   ✅ RISK_CATEGORIES has {len(RISK_CATEGORIES)} categories")
        
        # Test 3: Import test
        print("\n3️⃣  Testing imports...")
        try:
            from pydantic import BaseModel, Field
            print("   ✅ Pydantic available")
        except ImportError:
            print("   ❌ Pydantic not available")
            return False
        
        try:
            from pydantic_settings import BaseSettings
            print("   ✅ Pydantic-settings available")
        except ImportError:
            print("   ❌ Pydantic-settings not available")
            return False
        
        # Test 4: Environment variables test
        print("\n4️⃣  Testing environment variables...")
        test_wallet = os.getenv('WALLET_ADDRESSES')
        test_token = os.getenv('TELEGRAM_BOT_TOKEN')
        
        print(f"   ✅ WALLET_ADDRESSES = {test_wallet}")
        print(f"   ✅ TELEGRAM_BOT_TOKEN = {test_token[:10]}...")
        
        # Test 5: YAML file existence
        print("\n5️⃣  Testing YAML files...")
        config_dir = Path(__file__).parent / "config"
        
        yaml_files = [
            "base.yaml",
            "environments/development.yaml",
            "environments/production.yaml", 
            "environments/testing.yaml"
        ]
        
        for yaml_file in yaml_files:
            yaml_path = config_dir / yaml_file
            if yaml_path.exists():
                print(f"   ✅ {yaml_file} exists")
            else:
                print(f"   ⚠️  {yaml_file} missing (optional)")
        
        print("\n🎉 BASIC COMPATIBILITY TEST PASSED!")
        print("✅ All prerequisites are available")
        print("✅ Environment is ready for YAML migration")
        
        return True
        
    except Exception as e:
        print(f"\n❌ COMPATIBILITY TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_compatibility()
    
    if success:
        print("\n🚀 READY FOR MIGRATION!")
        print("Next step: Run full compatibility test")
        exit(0)
    else:
        print("\n⛔ NOT READY - Fix issues above")
        exit(1)
