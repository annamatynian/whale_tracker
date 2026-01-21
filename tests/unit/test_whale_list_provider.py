"""
Unit Tests for WhaleListProvider

Tests whale discovery, filtering, and balance fetching.

Run: pytest tests/unit/test_whale_list_provider.py -v
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, UTC

from src.data.whale_list_provider import WhaleListProvider


@pytest.fixture
def mock_multicall_client():
    """Create mock MulticallClient."""
    client = Mock()
    client.get_balances_batch = AsyncMock()
    return client


@pytest.fixture
def whale_provider(mock_multicall_client):
    """Create WhaleListProvider with mocked dependencies."""
    return WhaleListProvider(
        multicall_client=mock_multicall_client,
        min_balance_eth=1000  # 1000 ETH minimum
    )


class TestWhaleListProviderInitialization:
    """Test WhaleListProvider initialization."""
    
    def test_init_success(self, mock_multicall_client):
        """Test successful initialization."""
        provider = WhaleListProvider(
            multicall_client=mock_multicall_client,
            min_balance_eth=500
        )
        
        assert provider.multicall_client == mock_multicall_client
        assert provider.min_balance_wei == int(500 * 1e18)
        assert len(provider.EXCLUDED_ADDRESSES) > 0
    
    def test_init_default_min_balance(self, mock_multicall_client):
        """Test default minimum balance."""
        provider = WhaleListProvider(multicall_client=mock_multicall_client)
        
        assert provider.min_balance_wei == int(1000 * 1e18)


class TestGetTopWhales:
    """Test get_top_whales method."""
    
    @pytest.mark.asyncio
    async def test_get_top_whales_basic(self, whale_provider, mock_multicall_client):
        """Test basic whale fetching."""
        # Mock balance response (3 addresses with varying balances)
        mock_balances = {
            "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045": int(5000 * 1e18),  # 5000 ETH
            "0x73BCEb1Cd57C711feaC4224D062b0F6ff338501e": int(2000 * 1e18),  # 2000 ETH
            "0x6262998Ced04146fA42253a5C0AF90CA02dfd2A3": int(500 * 1e18),   # 500 ETH (below min)
        }
        
        mock_multicall_client.get_balances_batch.return_value = mock_balances
        
        whales = await whale_provider.get_top_whales(limit=10)
        
        # Should return 2 whales (500 ETH is below 1000 ETH minimum)
        assert len(whales) == 2
        
        # Should be sorted by balance (descending)
        assert whales[0]['balance_eth'] == 5000
        assert whales[1]['balance_eth'] == 2000
        
        # Each whale should have required fields
        for whale in whales:
            assert 'address' in whale
            assert 'balance_wei' in whale
            assert 'balance_eth' in whale
            assert 'fetched_at' in whale
            assert isinstance(whale['fetched_at'], datetime)
    
    @pytest.mark.asyncio
    async def test_get_top_whales_excludes_exchanges(self, whale_provider, mock_multicall_client):
        """Test that known exchanges are excluded."""
        # Mock balance response including Binance address
        mock_balances = {
            "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045": int(5000 * 1e18),  # Vitalik
            "0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE": int(600000 * 1e18),  # Binance (should be excluded)
        }
        
        mock_multicall_client.get_balances_batch.return_value = mock_balances
        
        whales = await whale_provider.get_top_whales(limit=10)
        
        # Binance address should be excluded BEFORE fetching balances
        # So multicall should only be called with Vitalik's address
        call_args = mock_multicall_client.get_balances_batch.call_args
        addresses_fetched = call_args[1]['addresses']
        
        assert "0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE" not in addresses_fetched
    
    @pytest.mark.asyncio
    async def test_get_top_whales_respects_limit(self, whale_provider, mock_multicall_client):
        """Test that limit parameter is respected."""
        # Mock 5 whales all above minimum
        mock_balances = {
            f"0x{'0' * (39 - len(str(i)))}{i}0": int((5000 - i*100) * 1e18)
            for i in range(5)
        }
        
        mock_multicall_client.get_balances_batch.return_value = mock_balances
        
        whales = await whale_provider.get_top_whales(limit=3)
        
        # Should return only 3 whales even though 5 qualify
        assert len(whales) <= 3
    
    @pytest.mark.asyncio
    async def test_get_top_whales_filters_by_min_balance(self, whale_provider, mock_multicall_client):
        """Test minimum balance filtering."""
        # Create provider with 2000 ETH minimum
        provider = WhaleListProvider(
            multicall_client=mock_multicall_client,
            min_balance_eth=2000
        )
        
        mock_balances = {
            "0xAddress1": int(5000 * 1e18),  # Above min
            "0xAddress2": int(1500 * 1e18),  # Below min
            "0xAddress3": int(2500 * 1e18),  # Above min
        }
        
        mock_multicall_client.get_balances_batch.return_value = mock_balances
        
        whales = await provider.get_top_whales(limit=10)
        
        # Should only return addresses above 2000 ETH
        assert len(whales) == 2
        assert all(w['balance_eth'] >= 2000 for w in whales)
    
    @pytest.mark.asyncio
    async def test_get_top_whales_empty_result(self, whale_provider, mock_multicall_client):
        """Test when no whales meet criteria."""
        # All balances below minimum
        mock_balances = {
            "0xAddress1": int(500 * 1e18),
            "0xAddress2": int(300 * 1e18),
        }
        
        mock_multicall_client.get_balances_batch.return_value = mock_balances
        
        whales = await whale_provider.get_top_whales(limit=10)
        
        assert len(whales) == 0


class TestGetCandidateAddresses:
    """Test _get_candidate_addresses helper method."""
    
    def test_get_candidate_addresses_returns_list(self, whale_provider):
        """Test that method returns list of addresses."""
        candidates = whale_provider._get_candidate_addresses(limit=10)
        
        assert isinstance(candidates, list)
        assert len(candidates) <= 10
        assert all(addr.startswith('0x') for addr in candidates)
    
    def test_get_candidate_addresses_respects_limit(self, whale_provider):
        """Test that limit is respected."""
        candidates = whale_provider._get_candidate_addresses(limit=5)
        
        assert len(candidates) <= 5
    
    def test_get_candidate_addresses_contains_known_holders(self, whale_provider):
        """Test that hardcoded list contains expected addresses."""
        candidates = whale_provider._get_candidate_addresses(limit=50)
        
        # Should contain ETH2 staking contract
        assert "0x00000000219ab540356cBB839Cbe05303d7705Fa" in candidates
        
        # Should contain Vitalik (for testing)
        assert "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045" in candidates


class TestHealthCheck:
    """Test health_check method."""
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, whale_provider, mock_multicall_client):
        """Test successful health check."""
        # Mock successful whale fetch
        mock_balances = {
            f"0x{'0' * (39 - len(str(i)))}{i}0": int(2000 * 1e18)
            for i in range(10)
        }
        
        mock_multicall_client.get_balances_batch.return_value = mock_balances
        
        health = await whale_provider.health_check()
        
        assert health["status"] == "healthy"
        assert health["whales_found"] > 0
        assert health["min_balance_eth"] == 1000
        assert health["excluded_addresses"] > 0
    
    @pytest.mark.asyncio
    async def test_health_check_failure(self, whale_provider, mock_multicall_client):
        """Test health check failure."""
        # Mock failure
        mock_multicall_client.get_balances_batch.side_effect = Exception("RPC connection failed")
        
        health = await whale_provider.health_check()
        
        assert health["status"] == "unhealthy"
        assert "error" in health


class TestExcludedAddresses:
    """Test excluded addresses filtering."""
    
    def test_excluded_addresses_not_empty(self, whale_provider):
        """Test that there are excluded addresses."""
        assert len(whale_provider.EXCLUDED_ADDRESSES) > 0
    
    def test_excluded_addresses_contains_major_exchanges(self, whale_provider):
        """Test that major exchanges are in excluded list."""
        excluded = whale_provider.EXCLUDED_ADDRESSES
        
        # Binance
        assert "0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE" in excluded
        
        # Kraken
        assert "0xdfd5293d8e347dfe59e90efd55b2956a1343963d" in excluded
        
        # ETH2 Staking
        assert "0x00000000219ab540356cBB839Cbe05303d7705Fa" in excluded


# ============================================
# INTEGRATION-STYLE TESTS (require real RPC)
# ============================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_real_whale_provider_integration():
    """
    Integration test with real blockchain (requires RPC connection).
    
    Run with: pytest tests/unit/test_whale_list_provider.py -v -m integration
    """
    from src.core.web3_manager import Web3Manager
    from src.data.multicall_client import MulticallClient
    
    # Initialize real dependencies
    web3_manager = Web3Manager(mock_mode=False)
    success = await web3_manager.initialize()
    assert success, "Failed to initialize Web3Manager"
    
    multicall_client = MulticallClient(web3_manager)
    provider = WhaleListProvider(
        multicall_client=multicall_client,
        min_balance_eth=100  # Lower threshold for testing
    )
    
    # Get top 10 whales
    whales = await provider.get_top_whales(limit=10)
    
    # Should find some whales
    assert len(whales) > 0
    
    # All whales should have >= 100 ETH
    assert all(w['balance_eth'] >= 100 for w in whales)
    
    # Should be sorted by balance
    for i in range(len(whales) - 1):
        assert whales[i]['balance_eth'] >= whales[i+1]['balance_eth']
    
    print(f"✅ Found {len(whales)} whales")
    print(f"Top whale: {whales[0]['address'][:10]}... with {whales[0]['balance_eth']:.2f} ETH")
