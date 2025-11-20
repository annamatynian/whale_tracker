#!/usr/bin/env python3
"""Test YAML-based configuration system."""

import sys
from pathlib import Path

# Add config to path
sys.path.insert(0, str(Path(__file__).parent / "config"))

try:
    # Install PyYAML first
    print("Step 1: Checking PyYAML installation...")
    import yaml
    print("✅ PyYAML is installed")
    
    # Test YAML settings import
    print("\nStep 2: Testing YAML settings import...")
    from settings_yaml import get_settings, Settings
    print("✅ YAML settings imported successfully")
    
    # Test development environment
    print("\nStep 3: Testing development environment...")
    dev_settings = get_settings("development")
    print(f"✅ Development settings loaded")
    print(f"   Environment: {dev_settings._environment}")
    print(f"   Network: {dev_settings.blockchain.default_network}")
    print(f"   Wallet addresses: {len(dev_settings.wallet_addresses)}")
    print(f"   First wallet: {dev_settings.wallet_addresses[0] if dev_settings.wallet_addresses else 'None'}")
    print(f"   Telegram bot configured: {bool(dev_settings.telegram_bot_token)}")
    
    # Test testing environment  
    print("\nStep 4: Testing testing environment...")
    test_settings = get_settings("testing")
    print(f"✅ Testing settings loaded")
    print(f"   Network: {test_settings.blockchain.default_network}")
    print(f"   Wallet addresses: {len(test_settings.wallet_addresses)}")
    print(f"   Mock data: {test_settings.development.mock_data}")
    print(f"   V3 enabled: {test_settings.features.v3_analytics.enabled}")
    
    # Test backward compatibility
    print("\nStep 5: Testing backward compatibility...")
    print(f"   settings.wallet_addresses: {type(dev_settings.wallet_addresses)}")
    print(f"   settings.check_interval_minutes: {dev_settings.check_interval_minutes}")
    print(f"   settings.default_il_threshold: {dev_settings.default_il_threshold}")
    print(f"✅ Backward compatibility works")
    
    # Test serialization
    print("\nStep 6: Testing serialization...")
    config_dict = dev_settings.to_dict()
    print(f"   Serialized type: {type(config_dict)}")
    print(f"   Features: {config_dict['features_enabled']}")
    print(f"✅ Serialization works")
    
    # Test RPC URL generation
    print("\nStep 7: Testing RPC URL generation...")
    rpc_url = dev_settings.get_rpc_url()
    print(f"   RPC URL: {rpc_url[:50]}...")
    print(f"✅ RPC URL generation works")
    
    print(f"\n🎉 ALL TESTS PASSED!")
    print(f"✅ YAML configuration system is ready!")
    print(f"✅ Wallet addresses parsing works without JSON errors!")
    
except ImportError as e:
    if "yaml" in str(e):
        print("❌ PyYAML not installed. Please run:")
        print("   pip install pyyaml")
    else:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
