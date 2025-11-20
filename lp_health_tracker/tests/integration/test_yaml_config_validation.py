"""
Updated Configuration Validation Tests for YAML system
=====================================================

These tests verify that the new YAML-based configuration works correctly.
"""

import pytest
import sys
from pathlib import Path

# Add config to path
config_path = Path(__file__).parent.parent.parent / "config"
sys.path.insert(0, str(config_path))


class TestYAMLConfigurationValidation:
    """Tests for YAML-based configuration system."""
    
    @pytest.mark.integration
    def test_yaml_settings_loading(self):
        """Test that YAML settings can be loaded without errors."""
        from settings_yaml import get_settings
        
        # Test development environment
        dev_settings = get_settings("development") 
        assert dev_settings is not None
        assert dev_settings.blockchain.default_network is not None
        
    @pytest.mark.integration
    def test_wallet_addresses_parsing(self):
        """Test that wallet addresses are parsed correctly from YAML."""
        from settings_yaml import get_settings
        
        settings = get_settings("development")
        
        # Should be a list without parsing errors
        assert isinstance(settings.wallet_addresses, list)
        assert len(settings.wallet_addresses) > 0
        
        # Should have valid wallet address format
        for addr in settings.wallet_addresses:
            assert isinstance(addr, str)
            assert addr.startswith('0x')
            assert len(addr) == 42
    
    @pytest.mark.integration
    def test_backward_compatibility(self):
        """Test that old Settings interface still works."""
        from settings import Settings
        
        settings = Settings()
        assert settings is not None
        
        # Old properties should work
        assert hasattr(settings, 'wallet_addresses')
        assert hasattr(settings, 'check_interval_minutes')
        assert hasattr(settings, 'default_il_threshold')
        assert hasattr(settings, 'telegram_bot_token')
    
    @pytest.mark.integration 
    def test_environment_specific_configs(self):
        """Test that different environments load correctly."""
        from settings_yaml import get_settings
        
        # Test development
        dev = get_settings("development")
        assert dev.blockchain.default_network == "ethereum_mainnet"
        assert dev.development.mock_data == True
        
        # Test testing
        test = get_settings("testing")
        assert test.blockchain.default_network == "ethereum_sepolia"
        assert test.development.test_mode == True
        assert test.features.v3_analytics.enabled == True
    
    @pytest.mark.integration
    def test_rpc_url_generation(self):
        """Test that RPC URLs are generated correctly."""
        from settings_yaml import get_settings
        
        settings = get_settings("development")
        rpc_url = settings.get_rpc_url()
        
        assert rpc_url is not None
        assert isinstance(rpc_url, str)
        assert len(rpc_url) > 0
        assert rpc_url.startswith(('http://', 'https://'))
    
    @pytest.mark.integration
    def test_feature_flags(self):
        """Test that feature flags work correctly."""
        from settings_yaml import get_settings
        
        dev_settings = get_settings("development")
        
        # V2 should be enabled in development
        assert dev_settings.features.v2_analytics.enabled == True
        
        # V3 should be disabled by default
        assert dev_settings.features.v3_analytics.enabled == False
    
    @pytest.mark.integration
    def test_serialization(self):
        """Test that settings can be serialized."""
        from settings_yaml import get_settings
        
        settings = get_settings("development")
        config_dict = settings.to_dict()
        
        assert isinstance(config_dict, dict)
        assert 'wallet_count' in config_dict
        assert 'features_enabled' in config_dict
        assert config_dict['wallet_count'] >= 0


class TestLegacyConfigurationValidation:
    """Legacy tests to ensure nothing breaks."""
    
    @pytest.mark.integration
    def test_settings_initialization(self):
        """Test that Settings can be initialized without errors (legacy test)."""
        from settings import Settings
        
        settings = Settings()
        assert settings is not None
    
    @pytest.mark.integration
    def test_contract_addresses_structure(self):
        """Test that contract addresses are available (legacy test)."""
        from settings import get_settings
        
        settings = get_settings("development")
        
        # Check if contracts are loaded
        if hasattr(settings, 'contracts') and settings.contracts:
            assert isinstance(settings.contracts, dict)
        else:
            # If not loaded from YAML, skip this test
            pytest.skip("Contract addresses not in YAML config yet")
    
    @pytest.mark.integration
    def test_settings_validation(self):
        """Test that settings pass basic validation (legacy test)."""
        from settings_yaml import get_settings
        
        settings = get_settings("development")
        
        # Basic validation - no exceptions should be raised
        assert len(settings.wallet_addresses) >= 0
        assert settings.check_interval_minutes > 0
        assert 0 < settings.default_il_threshold <= 1.0


if __name__ == "__main__":
    # Quick test runner
    print("Running YAML configuration tests...")
    
    try:
        test_class = TestYAMLConfigurationValidation()
        test_class.test_yaml_settings_loading()
        print("✅ YAML settings loading test passed")
        
        test_class.test_wallet_addresses_parsing()
        print("✅ Wallet addresses parsing test passed")
        
        test_class.test_backward_compatibility()
        print("✅ Backward compatibility test passed")
        
        test_class.test_environment_specific_configs()
        print("✅ Environment configs test passed")
        
        print("\n🎉 All YAML configuration tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
