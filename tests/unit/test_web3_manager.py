"""
Unit tests for Web3Manager
===========================

Tests Web3 connection, RPC failover, mock mode, and rate limiting.
"""

import pytest
import asyncio
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.web3_manager import Web3Manager


class TestWeb3ManagerInit:
    """Test Web3Manager initialization."""

    def test_init_default_mode(self):
        """Test initialization in default (non-mock) mode."""
        manager = Web3Manager(mock_mode=False)

        assert manager.mock_mode == False
        assert manager.network == "ethereum_mainnet"
        assert isinstance(manager.networks, dict)
        assert len(manager.networks) == 4  # Ethereum, Sepolia, Polygon, Arbitrum

    def test_init_mock_mode(self):
        """Test initialization in mock mode."""
        manager = Web3Manager(mock_mode=True)

        assert manager.mock_mode == True
        assert manager.web3 is None  # Not connected in mock mode

    def test_network_configurations(self):
        """Test that all networks are configured."""
        manager = Web3Manager()

        required_networks = [
            'ethereum_mainnet',
            'ethereum_sepolia',
            'polygon',
            'arbitrum'
        ]

        for network in required_networks:
            assert network in manager.networks
            assert 'name' in manager.networks[network]
            assert 'chain_id' in manager.networks[network]
            assert 'rpc_url' in manager.networks[network]


class TestWeb3ManagerRPC:
    """Test RPC URL generation and failover."""

    def test_get_rpc_url_priority(self, monkeypatch):
        """Test RPC URL priority (Infura → Alchemy → Ankr)."""
        monkeypatch.setenv("INFURA_API_KEY", "test_infura_key")
        monkeypatch.setenv("ALCHEMY_API_KEY", "test_alchemy_key")

        manager = Web3Manager()
        rpc_url = manager._get_rpc_url('ethereum_mainnet')

        # Should prioritize Infura
        assert 'infura' in rpc_url.lower()
        assert 'test_infura_key' in rpc_url

    def test_get_rpc_url_alchemy_fallback(self, monkeypatch):
        """Test fallback to Alchemy when Infura not available."""
        monkeypatch.setenv("INFURA_API_KEY", "")
        monkeypatch.setenv("ALCHEMY_API_KEY", "test_alchemy_key")

        manager = Web3Manager()
        rpc_url = manager._get_rpc_url('ethereum_mainnet')

        # Should use Alchemy
        assert 'alchemy' in rpc_url.lower()
        assert 'test_alchemy_key' in rpc_url

    def test_get_rpc_url_ankr_fallback(self, monkeypatch):
        """Test fallback to Ankr public endpoints."""
        monkeypatch.setenv("INFURA_API_KEY", "")
        monkeypatch.setenv("ALCHEMY_API_KEY", "")

        manager = Web3Manager()
        rpc_url = manager._get_rpc_url('ethereum_mainnet')

        # Should use Ankr public endpoint
        assert 'ankr.com' in rpc_url.lower()


class TestWeb3ManagerMockMode:
    """Test mock mode functionality."""

    @pytest.mark.asyncio
    async def test_is_contract_mock(self):
        """Test is_contract in mock mode."""
        manager = Web3Manager(mock_mode=True)

        # Should return True for contract indicators
        assert await manager.is_contract("0x000000123") == True
        assert await manager.is_contract("0x111111456") == True

        # Should return False for regular addresses
        assert await manager.is_contract("0xabc123def") == False

    @pytest.mark.asyncio
    async def test_get_transaction_count_mock(self):
        """Test get_transaction_count in mock mode."""
        manager = Web3Manager(mock_mode=True)

        count = await manager.get_transaction_count("0x123456789")

        assert isinstance(count, int)
        assert count > 0

    @pytest.mark.asyncio
    async def test_get_recent_transactions_mock(self):
        """Test get_recent_transactions in mock mode."""
        manager = Web3Manager(mock_mode=True)

        txs = await manager.get_recent_transactions(
            "0x123456789",
            limit=5,
            direction='outgoing'
        )

        assert isinstance(txs, list)
        assert len(txs) > 0
        assert 'hash' in txs[0]
        assert 'from' in txs[0]
        assert 'to' in txs[0]

    @pytest.mark.asyncio
    async def test_health_check_mock(self):
        """Test health_check in mock mode."""
        manager = Web3Manager(mock_mode=True)

        health = await manager.health_check()

        assert health['mock_mode'] == True
        assert health['status'] == 'healthy'


class TestWeb3ManagerRateLimiting:
    """Test rate limiting functionality."""

    def test_rate_limit_tracking(self):
        """Test that rate limiting tracks calls."""
        manager = Web3Manager()

        # Initial state
        assert len(manager.call_counts) == 0

        # Simulate calls
        manager._rate_limit('test_operation')
        manager._rate_limit('test_operation')

        assert manager.call_counts['test_operation'] == 2

    def test_rate_limit_different_operations(self):
        """Test rate limiting for different operations."""
        manager = Web3Manager()

        manager._rate_limit('operation_a')
        manager._rate_limit('operation_b')
        manager._rate_limit('operation_a')

        assert manager.call_counts['operation_a'] == 2
        assert manager.call_counts['operation_b'] == 1


class TestWeb3ManagerValidation:
    """Test address validation."""

    def test_is_valid_address_valid(self):
        """Test validation of valid Ethereum address."""
        manager = Web3Manager()

        # Valid address (checksum format)
        valid_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0"
        assert manager.is_valid_address(valid_address) == True

    def test_is_valid_address_invalid(self):
        """Test validation of invalid addresses."""
        manager = Web3Manager()

        # Too short
        assert manager.is_valid_address("0x123") == False

        # Not hex
        assert manager.is_valid_address("not_an_address") == False

        # Missing 0x prefix
        assert manager.is_valid_address("742d35Cc6634C0532925a3b844Bc9e7595f0bEb") == False


class TestWeb3ManagerNetworkInfo:
    """Test network information retrieval."""

    def test_get_network_info_default(self):
        """Test getting default network info."""
        manager = Web3Manager()

        info = manager.get_network_info()

        assert 'name' in info
        assert 'chain_id' in info
        assert 'rpc_url' in info
        assert info['name'] == 'Ethereum Mainnet'
        assert info['chain_id'] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
