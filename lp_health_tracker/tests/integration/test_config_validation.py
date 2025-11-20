"""
Configuration Validation Integration Tests
=========================================

Интеграционные тесты для валидации настроек проекта.
Интегрирован из check_settings.py в pytest структуру.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from config.settings import Settings, CONTRACT_ADDRESSES


class TestConfigurationValidation:
    """Тесты валидации конфигурации проекта."""
    
    @pytest.mark.integration
    def test_settings_initialization(self):
        """Test that Settings can be initialized without errors."""
        settings = Settings()
        assert settings is not None
    
    @pytest.mark.integration
    def test_contract_addresses_structure(self):
        """Test that contract addresses are properly structured."""
        assert 'ethereum_mainnet' in CONTRACT_ADDRESSES
        ethereum_config = CONTRACT_ADDRESSES['ethereum_mainnet']
        assert 'pairs' in ethereum_config
        
        pairs = ethereum_config['pairs']
        assert isinstance(pairs, dict)
        assert len(pairs) > 0
    
    @pytest.mark.integration
    def test_weth_usdc_v2_address(self):
        """Test that WETH_USDC_V2 pool address is correct."""
        expected_pool = "0x397FF1542f962076d0BFE58eA045FfA2d347ACa0"
        ethereum_pairs = CONTRACT_ADDRESSES.get('ethereum_mainnet', {}).get('pairs', {})
        
        weth_usdc_address = ethereum_pairs.get('WETH_USDC_V2')
        assert weth_usdc_address is not None, "WETH_USDC_V2 address not found in config"
        assert weth_usdc_address == expected_pool, f"Expected {expected_pool}, got {weth_usdc_address}"
    
    @pytest.mark.integration 
    def test_settings_validation(self):
        """Test that settings pass validation."""
        settings = Settings()
        errors = settings.validate()
        
        assert isinstance(errors, list), "validate() should return a list"
        assert len(errors) == 0, f"Settings validation failed with errors: {errors}"
    
    @pytest.mark.integration
    def test_rpc_url_configuration(self):
        """Test that RPC URL is properly configured."""
        settings = Settings()
        rpc_url = settings.get_rpc_url()
        
        assert rpc_url is not None, "RPC URL should not be None"
        assert isinstance(rpc_url, str), "RPC URL should be a string"
        assert len(rpc_url) > 0, "RPC URL should not be empty"
        # Should be valid URL format
        assert rpc_url.startswith(('http://', 'https://')), "RPC URL should start with http:// or https://"
    
    @pytest.mark.integration
    def test_all_pool_addresses_format(self):
        """Test that all pool addresses have correct format."""
        ethereum_pairs = CONTRACT_ADDRESSES.get('ethereum_mainnet', {}).get('pairs', {})
        
        for pool_name, address in ethereum_pairs.items():
            assert isinstance(address, str), f"{pool_name} address should be string"
            assert address.startswith('0x'), f"{pool_name} address should start with 0x"
            assert len(address) == 42, f"{pool_name} address should be 42 characters long"
            # Check if it's valid hex
            try:
                int(address, 16)
            except ValueError:
                pytest.fail(f"{pool_name} address {address} is not valid hex")
    
    @pytest.mark.integration
    def test_emoji_unicode_handling(self):
        """Test that emoji and unicode logging works correctly (important for Windows)."""
        try:
            from src.utils import log_startup, log_success, log_error, log_info
            
            # Test all emoji/unicode helper functions
            test_messages = [
                log_startup("Test startup message"),
                log_success("Test success message"), 
                log_error("Test error message"),
                log_info("Test info message")
            ]
            
            # All should return strings without Unicode errors
            for msg in test_messages:
                assert isinstance(msg, str), "Log helper should return string"
                assert len(msg) > 0, "Log message should not be empty"
                
        except UnicodeEncodeError:
            pytest.fail("Unicode/emoji handling failed - this can cause Windows console issues")
        except ImportError:
            pytest.skip("src.utils not available - skipping emoji test")
    
    @pytest.mark.integration
    def test_web3_manager_initialization(self):
        """Test that Web3Manager can be initialized with correct network settings."""
        try:
            from src.web3_utils import Web3Manager
            
            web3_manager = Web3Manager()
            
            # Should have a network attribute
            assert hasattr(web3_manager, 'network'), "Web3Manager should have network attribute"
            
            # Network should be one of supported networks
            supported_networks = ['ethereum_mainnet', 'ethereum_sepolia', 'polygon', 'arbitrum']
            assert web3_manager.network in supported_networks, f"Network {web3_manager.network} not in supported list"
            
        except ImportError:
            pytest.skip("src.web3_utils not available - skipping Web3Manager test")
    
    @pytest.mark.integration
    def test_rpc_url_generation_detailed(self):
        """Test detailed RPC URL generation for different networks."""
        settings = Settings()
        
        # Test different networks
        test_networks = [
            'ethereum_mainnet',
            'ethereum_sepolia', 
            'polygon',
            'arbitrum'
        ]
        
        for network in test_networks:
            rpc_url = settings.get_rpc_url(network)
            
            assert rpc_url is not None, f"RPC URL for {network} should not be None"
            assert isinstance(rpc_url, str), f"RPC URL for {network} should be string"
            assert rpc_url.startswith(('http://', 'https://')), f"RPC URL for {network} should be valid URL"
            
            # Network-specific checks
            if network == 'ethereum_mainnet':
                assert 'mainnet' in rpc_url or 'eth-mainnet' in rpc_url or 'rpc.ankr.com/eth' in rpc_url
            elif network == 'ethereum_sepolia':
                assert 'sepolia' in rpc_url or 'eth_sepolia' in rpc_url
            elif network == 'polygon':
                assert 'polygon' in rpc_url
            elif network == 'arbitrum':
                assert 'arbitrum' in rpc_url or 'arb-mainnet' in rpc_url
