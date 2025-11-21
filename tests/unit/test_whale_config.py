"""
Unit Tests for Whale Configuration
====================================

Tests for whale address database and classification system.
"""

import pytest
from src.core.whale_config import (
    WhaleConfig,
    WhaleCategory,
    WhaleMetadata,
    get_whale_config,
    is_exchange_address,
    classify_address,
    get_address_name,
    EXCHANGE_ADDRESSES,
    DEFI_PROTOCOL_ADDRESSES,
    KNOWN_WHALE_ADDRESSES,
    BRIDGE_ADDRESSES
)


class TestWhaleMetadata:
    """Test WhaleMetadata dataclass."""

    def test_metadata_creation(self):
        """Test creating whale metadata."""
        metadata = WhaleMetadata(
            address='0x123',
            name='Test Whale',
            category=WhaleCategory.EXCHANGE,
            tags=['test', 'exchange']
        )

        assert metadata.address == '0x123'
        assert metadata.name == 'Test Whale'
        assert metadata.category == WhaleCategory.EXCHANGE
        assert metadata.tags == ['test', 'exchange']

    def test_metadata_to_dict(self):
        """Test converting metadata to dictionary."""
        metadata = WhaleMetadata(
            address='0x123',
            name='Test Whale',
            category=WhaleCategory.EXCHANGE,
            tags=['test']
        )

        result = metadata.to_dict()

        assert result['address'] == '0x123'
        assert result['name'] == 'Test Whale'
        assert result['category'] == 'exchange'
        assert result['tags'] == ['test']


class TestWhaleAddressConstants:
    """Test whale address constant dictionaries."""

    def test_exchange_addresses_exist(self):
        """Test that exchange addresses are defined."""
        assert len(EXCHANGE_ADDRESSES) > 0
        assert all(addr.startswith('0x') for addr in EXCHANGE_ADDRESSES.keys())

    def test_exchange_addresses_have_metadata(self):
        """Test that all exchange addresses have proper metadata."""
        for address, metadata in EXCHANGE_ADDRESSES.items():
            assert metadata.address == address
            assert metadata.name
            assert metadata.category == WhaleCategory.EXCHANGE
            assert 'exchange' in [tag.lower() for tag in metadata.tags] or \
                   any(exchange in [tag.lower() for tag in metadata.tags]
                       for exchange in ['binance', 'coinbase', 'kraken', 'bitfinex', 'okx', 'huobi', 'gateio'])

    def test_major_exchanges_covered(self):
        """Test that major exchanges are covered."""
        all_tags = []
        for metadata in EXCHANGE_ADDRESSES.values():
            all_tags.extend(metadata.tags)

        all_tags_lower = [tag.lower() for tag in all_tags]

        # Check major exchanges
        assert any('binance' in tag for tag in all_tags_lower)
        assert any('coinbase' in tag for tag in all_tags_lower)
        assert any('kraken' in tag for tag in all_tags_lower)

    def test_defi_protocols_exist(self):
        """Test that DeFi protocol addresses are defined."""
        assert len(DEFI_PROTOCOL_ADDRESSES) > 0

        for address, metadata in DEFI_PROTOCOL_ADDRESSES.items():
            assert metadata.category == WhaleCategory.DEFI_PROTOCOL

    def test_known_whales_exist(self):
        """Test that known whale addresses are defined."""
        assert len(KNOWN_WHALE_ADDRESSES) > 0

    def test_eth2_deposit_contract_included(self):
        """Test that ETH2 deposit contract is included."""
        eth2_address = '0x00000000219ab540356cBB839Cbe05303d7705Fa'
        assert eth2_address in KNOWN_WHALE_ADDRESSES

        metadata = KNOWN_WHALE_ADDRESSES[eth2_address]
        assert 'eth2' in [tag.lower() for tag in metadata.tags]


class TestWhaleConfig:
    """Test WhaleConfig class."""

    def test_whale_config_initialization(self):
        """Test WhaleConfig initialization."""
        config = WhaleConfig()

        assert len(config.exchanges) > 0
        assert len(config.all_addresses) > 0
        assert len(config.all_addresses) >= len(config.exchanges)

    def test_is_exchange(self):
        """Test exchange address detection."""
        config = WhaleConfig()

        # Binance hot wallet
        binance_address = '0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE'
        assert config.is_exchange(binance_address) == True

        # Random address
        assert config.is_exchange('0x1234567890123456789012345678901234567890') == False

    def test_is_defi_protocol(self):
        """Test DeFi protocol detection."""
        config = WhaleConfig()

        # Uniswap V3 Factory
        uniswap_address = '0x1F98431c8aD98523631AE4a59f267346ea31F984'
        assert config.is_defi_protocol(uniswap_address) == True

        # Random address
        assert config.is_defi_protocol('0x1234567890123456789012345678901234567890') == False

    def test_is_known_whale(self):
        """Test known whale detection."""
        config = WhaleConfig()

        # ETH2 deposit contract
        eth2_address = '0x00000000219ab540356cBB839Cbe05303d7705Fa'
        assert config.is_known_whale(eth2_address) == True

        # Random address
        assert config.is_known_whale('0x1234567890123456789012345678901234567890') == False

    def test_get_metadata(self):
        """Test metadata retrieval."""
        config = WhaleConfig()

        # Binance address
        binance_address = '0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE'
        metadata = config.get_metadata(binance_address)

        assert metadata is not None
        assert metadata.name == 'Binance Hot Wallet'
        assert metadata.category == WhaleCategory.EXCHANGE

    def test_get_metadata_unknown(self):
        """Test metadata retrieval for unknown address."""
        config = WhaleConfig()

        metadata = config.get_metadata('0x1234567890123456789012345678901234567890')
        assert metadata is None

    def test_get_name(self):
        """Test name retrieval."""
        config = WhaleConfig()

        # Known address
        binance_address = '0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE'
        name = config.get_name(binance_address)
        assert name == 'Binance Hot Wallet'

        # Unknown address
        unknown_address = '0x1234567890123456789012345678901234567890'
        name = config.get_name(unknown_address)
        assert 'Unknown' in name

    def test_get_category(self):
        """Test category retrieval."""
        config = WhaleConfig()

        # Exchange
        binance_address = '0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE'
        assert config.get_category(binance_address) == WhaleCategory.EXCHANGE

        # Unknown
        unknown_address = '0x1234567890123456789012345678901234567890'
        assert config.get_category(unknown_address) == WhaleCategory.UNKNOWN

    def test_get_all_exchange_addresses(self):
        """Test getting all exchange addresses."""
        config = WhaleConfig()

        addresses = config.get_all_exchange_addresses()

        assert len(addresses) > 0
        assert all(addr.startswith('0x') for addr in addresses)
        assert '0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE' in addresses

    def test_get_all_known_addresses(self):
        """Test getting all known addresses."""
        config = WhaleConfig()

        addresses = config.get_all_known_addresses()

        assert len(addresses) > 0
        assert len(addresses) >= len(config.get_all_exchange_addresses())

    def test_classify_transaction_destination_exchange(self):
        """Test classification of exchange destination."""
        config = WhaleConfig()

        binance_address = '0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE'
        result = config.classify_transaction_destination(binance_address)

        assert result['is_known'] == True
        assert result['category'] == WhaleCategory.EXCHANGE
        assert result['name'] == 'Binance Hot Wallet'
        assert result['is_dump_risk'] == True  # Exchange = dump risk
        assert 'binance' in result['tags']

    def test_classify_transaction_destination_defi(self):
        """Test classification of DeFi protocol destination."""
        config = WhaleConfig()

        uniswap_address = '0x1F98431c8aD98523631AE4a59f267346ea31F984'
        result = config.classify_transaction_destination(uniswap_address)

        assert result['is_known'] == True
        assert result['category'] == WhaleCategory.DEFI_PROTOCOL
        assert result['is_dump_risk'] == False  # DeFi != dump risk

    def test_classify_transaction_destination_unknown(self):
        """Test classification of unknown destination."""
        config = WhaleConfig()

        unknown_address = '0x1234567890123456789012345678901234567890'
        result = config.classify_transaction_destination(unknown_address)

        assert result['is_known'] == False
        assert result['category'] == WhaleCategory.UNKNOWN
        assert result['name'] == 'Unknown Address'
        assert result['is_dump_risk'] == False

    def test_get_addresses_by_tag(self):
        """Test filtering addresses by tag."""
        config = WhaleConfig()

        binance_addresses = config.get_addresses_by_tag('binance')

        assert len(binance_addresses) > 0
        assert all(config.get_metadata(addr).name.startswith('Binance')
                   for addr in binance_addresses)

    def test_get_addresses_by_category(self):
        """Test filtering addresses by category."""
        config = WhaleConfig()

        exchange_addresses = config.get_addresses_by_category(WhaleCategory.EXCHANGE)

        assert len(exchange_addresses) > 0
        assert all(config.get_metadata(addr).category == WhaleCategory.EXCHANGE
                   for addr in exchange_addresses)

    def test_to_dict(self):
        """Test exporting configuration to dictionary."""
        config = WhaleConfig()

        result = config.to_dict()

        assert 'exchanges' in result
        assert 'defi_protocols' in result
        assert 'known_whales' in result
        assert 'bridges' in result

        # Check structure
        binance_address = '0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE'
        assert binance_address in result['exchanges']
        assert result['exchanges'][binance_address]['name'] == 'Binance Hot Wallet'


class TestSingletonAndConvenience:
    """Test singleton pattern and convenience functions."""

    def test_get_whale_config_singleton(self):
        """Test that get_whale_config returns singleton."""
        config1 = get_whale_config()
        config2 = get_whale_config()

        assert config1 is config2

    def test_is_exchange_address_convenience(self):
        """Test is_exchange_address convenience function."""
        binance_address = '0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE'
        assert is_exchange_address(binance_address) == True

        unknown_address = '0x1234567890123456789012345678901234567890'
        assert is_exchange_address(unknown_address) == False

    def test_classify_address_convenience(self):
        """Test classify_address convenience function."""
        binance_address = '0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE'
        result = classify_address(binance_address)

        assert result['is_known'] == True
        assert result['category'] == WhaleCategory.EXCHANGE
        assert result['is_dump_risk'] == True

    def test_get_address_name_convenience(self):
        """Test get_address_name convenience function."""
        binance_address = '0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE'
        name = get_address_name(binance_address)

        assert name == 'Binance Hot Wallet'


class TestWhaleCategory:
    """Test WhaleCategory enum."""

    def test_category_values(self):
        """Test category enum values."""
        assert WhaleCategory.EXCHANGE.value == "exchange"
        assert WhaleCategory.DEFI_PROTOCOL.value == "defi_protocol"
        assert WhaleCategory.KNOWN_WHALE.value == "known_whale"
        assert WhaleCategory.INSTITUTIONAL.value == "institutional"
        assert WhaleCategory.UNKNOWN.value == "unknown"

    def test_category_comparison(self):
        """Test category comparison."""
        assert WhaleCategory.EXCHANGE == WhaleCategory.EXCHANGE
        assert WhaleCategory.EXCHANGE != WhaleCategory.DEFI_PROTOCOL
