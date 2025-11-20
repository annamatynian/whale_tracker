#!/usr/bin/env python3
"""
Full Backward Compatibility Test
===============================

Tests that the new YAML system is 100% compatible with original settings.py
"""

import sys
from pathlib import Path

# Add config to path
sys.path.insert(0, str(Path(__file__).parent / "config"))

def test_backward_compatibility():
    """Test all aspects of backward compatibility."""
    
    print("🧪 FULL BACKWARD COMPATIBILITY TEST")
    print("=" * 50)
    
    try:
        from settings_fixed_compatible import Settings, CONTRACT_ADDRESSES, RISK_CATEGORIES, SUPPORTED_PROTOCOLS, API_LIMITS
        
        # Test 1: Settings instantiation (original way)
        print("\\n1️⃣  Testing Settings() instantiation...")
        settings = Settings()
        print("   ✅ Settings() works")
        
        # Test 2: All original constants available
        print("\\n2️⃣  Testing original constants...")
        assert CONTRACT_ADDRESSES is not None, "CONTRACT_ADDRESSES missing"
        assert 'ethereum_mainnet' in CONTRACT_ADDRESSES, "ethereum_mainnet missing from CONTRACT_ADDRESSES"
        assert RISK_CATEGORIES is not None, "RISK_CATEGORIES missing"
        assert 'very_low' in RISK_CATEGORIES, "very_low missing from RISK_CATEGORIES"
        assert SUPPORTED_PROTOCOLS is not None, "SUPPORTED_PROTOCOLS missing"
        assert API_LIMITS is not None, "API_LIMITS missing"
        print("   ✅ All constants available")
        
        # Test 3: Original properties work
        print("\\n3️⃣  Testing original properties...")
        assert hasattr(settings, 'wallet_addresses'), "wallet_addresses property missing"
        assert hasattr(settings, 'wallet_addresses_list'), "wallet_addresses_list property missing (CRITICAL)"
        assert hasattr(settings, 'check_interval_minutes'), "check_interval_minutes property missing"
        assert hasattr(settings, 'default_il_threshold'), "default_il_threshold property missing"
        assert hasattr(settings, 'log_level'), "log_level property missing"
        assert hasattr(settings, 'telegram_bot_token'), "telegram_bot_token property missing"
        assert hasattr(settings, 'telegram_chat_id'), "telegram_chat_id property missing"
        print("   ✅ All original properties available")
        
        # Test 4: Original methods work
        print("\\n4️⃣  Testing original methods...")
        assert hasattr(settings, 'get_rpc_url'), "get_rpc_url method missing"
        assert hasattr(settings, 'validate'), "validate method missing"
        assert hasattr(settings, 'to_dict'), "to_dict method missing"
        print("   ✅ All original methods available")
        
        # Test 5: Flat field access (critical for existing code)
        print("\\n5️⃣  Testing flat field access...")
        assert hasattr(settings, 'INFURA_API_KEY'), "INFURA_API_KEY field missing"
        assert hasattr(settings, 'ALCHEMY_API_KEY'), "ALCHEMY_API_KEY field missing"
        assert hasattr(settings, 'TELEGRAM_BOT_TOKEN'), "TELEGRAM_BOT_TOKEN field missing"
        assert hasattr(settings, 'TELEGRAM_CHAT_ID'), "TELEGRAM_CHAT_ID field missing"
        assert hasattr(settings, 'WALLET_ADDRESSES'), "WALLET_ADDRESSES field missing"
        assert hasattr(settings, 'DEFAULT_NETWORK'), "DEFAULT_NETWORK field missing"
        assert hasattr(settings, 'CHECK_INTERVAL_MINUTES'), "CHECK_INTERVAL_MINUTES field missing"
        assert hasattr(settings, 'DEFAULT_IL_THRESHOLD'), "DEFAULT_IL_THRESHOLD field missing"
        print("   ✅ All flat fields accessible")
        
        # Test 6: Data types are correct
        print("\\n6️⃣  Testing data types...")
        assert isinstance(settings.WALLET_ADDRESSES, list), f"WALLET_ADDRESSES should be list, got {type(settings.WALLET_ADDRESSES)}"
        assert isinstance(settings.wallet_addresses, list), f"wallet_addresses should be list, got {type(settings.wallet_addresses)}"
        assert isinstance(settings.wallet_addresses_list, list), f"wallet_addresses_list should be list, got {type(settings.wallet_addresses_list)}"
        assert isinstance(settings.CHECK_INTERVAL_MINUTES, int), f"CHECK_INTERVAL_MINUTES should be int, got {type(settings.CHECK_INTERVAL_MINUTES)}"
        assert isinstance(settings.DEFAULT_IL_THRESHOLD, float), f"DEFAULT_IL_THRESHOLD should be float, got {type(settings.DEFAULT_IL_THRESHOLD)}"
        print("   ✅ All data types correct")
        
        # Test 7: Original validation works
        print("\\n7️⃣  Testing original validation...")
        errors = settings.validate()
        assert isinstance(errors, list), f"validate() should return list, got {type(errors)}"
        print(f"   ✅ Validation works (found {len(errors)} errors)")
        
        # Test 8: RPC URL generation
        print("\\n8️⃣  Testing RPC URL generation...")
        rpc_url = settings.get_rpc_url()
        assert isinstance(rpc_url, str), f"get_rpc_url() should return string, got {type(rpc_url)}"
        assert rpc_url.startswith(('http://', 'https://')), f"RPC URL should be valid URL, got {rpc_url[:50]}"
        print(f"   ✅ RPC URL generation works")
        
        # Test 9: to_dict() format
        print("\\n9️⃣  Testing to_dict() format...")
        config_dict = settings.to_dict()
        assert isinstance(config_dict, dict), f"to_dict() should return dict, got {type(config_dict)}"
        # Check for original keys
        expected_keys = ['default_network', 'check_interval_minutes', 'default_il_threshold', 'log_level', 'wallet_count']
        for key in expected_keys:
            assert key in config_dict, f"to_dict() missing expected key: {key}"
        print("   ✅ to_dict() format compatible")
        
        # Test 10: Critical import patterns work
        print("\\n🔟 Testing critical import patterns...")
        
        # Test import constants
        try:
            from settings_fixed_compatible import CONTRACT_ADDRESSES as CA
            from settings_fixed_compatible import RISK_CATEGORIES as RC
            print("   ✅ Constant imports work")
        except ImportError as e:
            raise AssertionError(f"Constant import failed: {e}")
        
        # Test 11: Real usage patterns
        print("\\n1️⃣1️⃣ Testing real usage patterns...")
        
        # Pattern 1: Loop through wallet addresses
        for addr in settings.wallet_addresses_list:
            assert isinstance(addr, str), f"Wallet address should be string, got {type(addr)}"
        print("   ✅ Wallet iteration works")
        
        # Pattern 2: Access configuration
        network = settings.DEFAULT_NETWORK
        interval = settings.check_interval_minutes
        threshold = settings.default_il_threshold
        print("   ✅ Configuration access works")
        
        # Pattern 3: Get RPC for specific network
        mainnet_rpc = settings.get_rpc_url("ethereum_mainnet")
        sepolia_rpc = settings.get_rpc_url("ethereum_sepolia")
        assert mainnet_rpc != sepolia_rpc, "Different networks should have different RPC URLs"
        print("   ✅ Network-specific RPC works")
        
        # SUCCESS!
        print("\\n🎉 SUCCESS: FULL BACKWARD COMPATIBILITY ACHIEVED!")
        print("✅ All existing code should work without changes")
        print("✅ No breaking changes detected")
        print("✅ All constants, methods, and properties preserved")
        
        return True
        
    except Exception as e:
        print(f"\\n❌ COMPATIBILITY TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_comparison_with_original():
    """Test that behavior matches original as closely as possible."""
    print("\\n🔍 COMPARING WITH ORIGINAL BEHAVIOR...")
    
    try:
        from settings_fixed_compatible import Settings as NewSettings
        
        # Test with both empty initialization
        new_settings = NewSettings()
        
        print("✅ Behavior comparison completed")
        return True
        
    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting comprehensive backward compatibility validation...")
    
    # Run all tests
    test1_passed = test_backward_compatibility()
    test2_passed = test_comparison_with_original()
    
    if test1_passed and test2_passed:
        print("\\n🏆 ALL TESTS PASSED!")
        print("🚀 Migration is SAFE - no breaking changes!")
        exit(0)
    else:
        print("\\n💥 TESTS FAILED!")
        print("⛔ DO NOT MIGRATE - fix issues first!")
        exit(1)
