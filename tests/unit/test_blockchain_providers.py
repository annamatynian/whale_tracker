"""
Unit Tests for Blockchain Data Providers

Tests BlockchainDataProvider abstraction and implementations.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.abstractions.blockchain_data_provider import BlockchainDataProvider
from src.providers.etherscan_provider import EtherscanProvider
from src.providers.composite_data_provider import CompositeDataProvider


class TestBlockchainDataProviderInterface:
    """Test that BlockchainDataProvider is a proper abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """BlockchainDataProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BlockchainDataProvider()

    def test_abstract_methods_exist(self):
        """All abstract methods are defined."""
        abstract_methods = [
            'get_transaction_count',
            'get_transactions',
            'get_transaction',
            'get_transaction_receipt',
            'get_balance',
            'test_connection',
            'provider_name',
            'network',
            'is_available'
        ]

        for method in abstract_methods:
            assert hasattr(BlockchainDataProvider, method)


class TestEtherscanProvider:
    """Test EtherscanProvider implementation."""

    def test_initialization_ethereum(self):
        """EtherscanProvider initializes for Ethereum."""
        provider = EtherscanProvider(api_key='test_key', network='ethereum')

        assert provider.provider_name == 'etherscan'
        assert provider.network == 'ethereum'
        assert provider.base_url == 'https://api.etherscan.io/api'

    def test_initialization_base(self):
        """EtherscanProvider initializes for Base."""
        provider = EtherscanProvider(api_key='test_key', network='base')

        assert provider.network == 'base'
        assert provider.base_url == 'https://api.basescan.org/api'

    def test_initialization_arbitrum(self):
        """EtherscanProvider initializes for Arbitrum."""
        provider = EtherscanProvider(api_key='test_key', network='arbitrum')

        assert provider.network == 'arbitrum'
        assert provider.base_url == 'https://api.arbiscan.io/api'

    def test_is_available_true(self):
        """is_available returns True when API key is set."""
        provider = EtherscanProvider(api_key='test_key')
        assert provider.is_available is True

    def test_is_available_false(self):
        """is_available returns False when no API key."""
        provider = EtherscanProvider(api_key=None)
        assert provider.is_available is False

    def test_rate_limit_property(self):
        """rate_limit_per_second returns configured value."""
        provider = EtherscanProvider(api_key='test', rate_limit=5)
        assert provider.rate_limit_per_second == 5

    def test_supported_features(self):
        """supported_features lists available features."""
        provider = EtherscanProvider(api_key='test')
        features = provider.supported_features

        assert 'transactions' in features
        assert 'internal_txs' in features
        assert 'token_transfers' in features
        assert 'balance' in features

    @pytest.mark.asyncio
    async def test_get_transaction_count_success(self):
        """get_transaction_count fetches nonce successfully."""
        provider = EtherscanProvider(api_key='test_key')

        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.json = AsyncMock(return_value={
            'status': '1',
            'result': '0x64'  # 100 in hex
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock()

        mock_session = AsyncMock()
        mock_session.get = Mock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        with patch('aiohttp.ClientSession', return_value=mock_session):
            nonce = await provider.get_transaction_count('0x' + '1' * 40)
            assert nonce == 100

    @pytest.mark.asyncio
    async def test_get_transactions_success(self):
        """get_transactions fetches transaction list."""
        provider = EtherscanProvider(api_key='test_key')

        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.json = AsyncMock(return_value={
            'status': '1',
            'result': [
                {
                    'hash': '0xabc',
                    'from': '0x123',
                    'to': '0x456',
                    'value': '1000000000000000000'
                }
            ]
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock()

        mock_session = AsyncMock()
        mock_session.get = Mock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        with patch('aiohttp.ClientSession', return_value=mock_session):
            txs = await provider.get_transactions('0x' + '1' * 40)
            assert len(txs) == 1
            assert txs[0]['hash'] == '0xabc'

    @pytest.mark.asyncio
    async def test_get_balance_success(self):
        """get_balance fetches balance successfully."""
        provider = EtherscanProvider(api_key='test_key')

        # Mock successful API response
        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.json = AsyncMock(return_value={
            'status': '1',
            'result': '1000000000000000000'  # 1 ETH in Wei
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock()

        mock_session = AsyncMock()
        mock_session.get = Mock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        with patch('aiohttp.ClientSession', return_value=mock_session):
            balance = await provider.get_balance('0x' + '1' * 40)
            assert balance == 1000000000000000000

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """API errors are properly handled."""
        provider = EtherscanProvider(api_key='test_key')

        # Mock error API response
        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.json = AsyncMock(return_value={
            'status': '0',
            'message': 'NOTOK',
            'result': 'Error! Invalid address format'
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock()

        mock_session = AsyncMock()
        mock_session.get = Mock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        with patch('aiohttp.ClientSession', return_value=mock_session):
            with pytest.raises(Exception) as exc_info:
                await provider.get_balance('invalid_address')

            assert 'Etherscan API error' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_test_connection_success(self):
        """test_connection succeeds with valid credentials."""
        provider = EtherscanProvider(api_key='test_key')

        # Mock successful connection test
        mock_response = AsyncMock()
        mock_response.raise_for_status = Mock()
        mock_response.json = AsyncMock(return_value={
            'status': '1',
            'result': '0'
        })
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock()

        mock_session = AsyncMock()
        mock_session.get = Mock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        with patch('aiohttp.ClientSession', return_value=mock_session):
            result = await provider.test_connection()
            assert result is True


class TestCompositeDataProvider:
    """Test CompositeDataProvider implementation."""

    def test_initialization(self):
        """CompositeDataProvider initializes with multiple providers."""
        provider1 = Mock(spec=BlockchainDataProvider)
        provider1.provider_name = 'etherscan'
        provider1.network = 'ethereum'

        provider2 = Mock(spec=BlockchainDataProvider)
        provider2.provider_name = 'alchemy'
        provider2.network = 'ethereum'

        composite = CompositeDataProvider([
            (10, provider1),
            (20, provider2)
        ])

        assert composite.provider_name == 'composite[etherscan,alchemy]'
        assert composite.network == 'ethereum'

    def test_providers_sorted_by_priority(self):
        """Providers are sorted by priority (lower first)."""
        provider1 = Mock(spec=BlockchainDataProvider)
        provider1.provider_name = 'provider1'

        provider2 = Mock(spec=BlockchainDataProvider)
        provider2.provider_name = 'provider2'

        provider3 = Mock(spec=BlockchainDataProvider)
        provider3.provider_name = 'provider3'

        # Add in wrong order
        composite = CompositeDataProvider([
            (30, provider3),
            (10, provider1),
            (20, provider2)
        ])

        # Should be sorted: provider1 (10), provider2 (20), provider3 (30)
        assert composite.providers[0][1] == provider1
        assert composite.providers[1][1] == provider2
        assert composite.providers[2][1] == provider3

    def test_is_available_true(self):
        """is_available returns True if any provider is available."""
        provider1 = Mock(spec=BlockchainDataProvider)
        provider1.is_available = False

        provider2 = Mock(spec=BlockchainDataProvider)
        provider2.is_available = True

        composite = CompositeDataProvider([
            (10, provider1),
            (20, provider2)
        ])

        assert composite.is_available is True

    def test_is_available_false(self):
        """is_available returns False if no providers available."""
        provider1 = Mock(spec=BlockchainDataProvider)
        provider1.is_available = False

        provider2 = Mock(spec=BlockchainDataProvider)
        provider2.is_available = False

        composite = CompositeDataProvider([
            (10, provider1),
            (20, provider2)
        ])

        assert composite.is_available is False

    @pytest.mark.asyncio
    async def test_failover_to_second_provider(self):
        """Falls back to second provider when first fails."""
        provider1 = Mock(spec=BlockchainDataProvider)
        provider1.provider_name = 'provider1'
        provider1.is_available = True
        provider1.get_balance = AsyncMock(side_effect=Exception('Provider 1 failed'))

        provider2 = Mock(spec=BlockchainDataProvider)
        provider2.provider_name = 'provider2'
        provider2.is_available = True
        provider2.get_balance = AsyncMock(return_value=1000000)

        composite = CompositeDataProvider([
            (10, provider1),
            (20, provider2)
        ])

        balance = await composite.get_balance('0x123')

        assert balance == 1000000
        provider1.get_balance.assert_called_once()
        provider2.get_balance.assert_called_once()

    @pytest.mark.asyncio
    async def test_all_providers_fail_raises_exception(self):
        """Raises exception when all providers fail."""
        provider1 = Mock(spec=BlockchainDataProvider)
        provider1.provider_name = 'provider1'
        provider1.is_available = True
        provider1.get_balance = AsyncMock(side_effect=Exception('Failed'))

        provider2 = Mock(spec=BlockchainDataProvider)
        provider2.provider_name = 'provider2'
        provider2.is_available = True
        provider2.get_balance = AsyncMock(side_effect=Exception('Failed'))

        composite = CompositeDataProvider([
            (10, provider1),
            (20, provider2)
        ])

        with pytest.raises(Exception) as exc_info:
            await composite.get_balance('0x123')

        assert 'All providers failed' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_skips_unavailable_providers(self):
        """Skips providers that are not available."""
        provider1 = Mock(spec=BlockchainDataProvider)
        provider1.provider_name = 'provider1'
        provider1.is_available = False
        provider1.get_balance = AsyncMock()

        provider2 = Mock(spec=BlockchainDataProvider)
        provider2.provider_name = 'provider2'
        provider2.is_available = True
        provider2.get_balance = AsyncMock(return_value=1000000)

        composite = CompositeDataProvider([
            (10, provider1),
            (20, provider2)
        ])

        balance = await composite.get_balance('0x123')

        assert balance == 1000000
        # Provider1 should not be called (unavailable)
        provider1.get_balance.assert_not_called()
        provider2.get_balance.assert_called_once()

    @pytest.mark.asyncio
    async def test_test_connection_any_provider_succeeds(self):
        """test_connection succeeds if any provider connects."""
        provider1 = Mock(spec=BlockchainDataProvider)
        provider1.test_connection = AsyncMock(return_value=False)

        provider2 = Mock(spec=BlockchainDataProvider)
        provider2.test_connection = AsyncMock(return_value=True)

        composite = CompositeDataProvider([
            (10, provider1),
            (20, provider2)
        ])

        result = await composite.test_connection()
        assert result is True


class TestBlockchainProviderIntegration:
    """Integration tests for blockchain providers."""

    @pytest.mark.asyncio
    async def test_multi_provider_resilience(self):
        """Composite provider provides resilience against failures."""
        # Simulate flaky providers
        provider1 = Mock(spec=BlockchainDataProvider)
        provider1.provider_name = 'flaky1'
        provider1.is_available = True
        call_count = {'count': 0}

        async def flaky_balance(address):
            call_count['count'] += 1
            if call_count['count'] == 1:
                raise Exception('Temporary failure')
            return 1000000

        provider1.get_balance = flaky_balance

        provider2 = Mock(spec=BlockchainDataProvider)
        provider2.provider_name = 'reliable'
        provider2.is_available = True
        provider2.get_balance = AsyncMock(return_value=1000000)

        composite = CompositeDataProvider([
            (10, provider1),
            (20, provider2)
        ])

        # First call - provider1 fails, falls back to provider2
        balance = await composite.get_balance('0x123')
        assert balance == 1000000
        assert call_count['count'] == 1  # Provider1 was tried

        # Second call - provider1 would succeed, but we try it first
        balance = await composite.get_balance('0x456')
        assert balance == 1000000


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
