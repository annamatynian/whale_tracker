"""
Whale Configuration - Known Whale Addresses and Metadata
==========================================================

This module contains curated lists of known whale addresses organized by:
- Exchange wallets
- DeFi protocols
- Known individual whales
- Institutional holders

These addresses are used for:
1. Monitoring whale activity
2. Classifying transaction destinations (exchange vs unknown)
3. One-hop tracking validation

Author: Whale Tracker Project
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class WhaleCategory(Enum):
    """Categories of whale addresses."""
    EXCHANGE = "exchange"
    DEFI_PROTOCOL = "defi_protocol"
    KNOWN_WHALE = "known_whale"
    INSTITUTIONAL = "institutional"
    MINER = "miner"
    BRIDGE = "bridge"
    UNKNOWN = "unknown"


@dataclass
class WhaleMetadata:
    """Metadata for a whale address."""
    address: str
    name: str
    category: WhaleCategory
    tags: List[str]
    min_balance_eth: Optional[float] = None
    last_seen: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'address': self.address,
            'name': self.name,
            'category': self.category.value,
            'tags': self.tags,
            'min_balance_eth': self.min_balance_eth,
            'last_seen': self.last_seen,
            'notes': self.notes
        }


# Exchange Addresses - These are KNOWN destinations for whale dumps
EXCHANGE_ADDRESSES = {
    # Binance
    '0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE': WhaleMetadata(
        address='0x3f5CE5FBFe3E9af3971dD833D26bA9b5C936f0bE',
        name='Binance Hot Wallet',
        category=WhaleCategory.EXCHANGE,
        tags=['binance', 'hot-wallet', 'high-volume'],
        notes='Primary Binance hot wallet - huge trading volume'
    ),
    '0x28C6c06298d514Db089934071355E5743bf21d60': WhaleMetadata(
        address='0x28C6c06298d514Db089934071355E5743bf21d60',
        name='Binance Cold Wallet',
        category=WhaleCategory.EXCHANGE,
        tags=['binance', 'cold-wallet'],
        notes='Binance cold storage'
    ),
    '0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8': WhaleMetadata(
        address='0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8',
        name='Binance Wallet 3',
        category=WhaleCategory.EXCHANGE,
        tags=['binance'],
        notes='Another Binance wallet'
    ),

    # Coinbase
    '0x71660c4005BA85c37ccec55d0C4493E66Fe775d3': WhaleMetadata(
        address='0x71660c4005BA85c37ccec55d0C4493E66Fe775d3',
        name='Coinbase Cold Wallet',
        category=WhaleCategory.EXCHANGE,
        tags=['coinbase', 'cold-wallet'],
        notes='Coinbase primary cold storage'
    ),
    '0x503828976D22510aad0201ac7EC88293211D23Da': WhaleMetadata(
        address='0x503828976D22510aad0201ac7EC88293211D23Da',
        name='Coinbase Hot Wallet',
        category=WhaleCategory.EXCHANGE,
        tags=['coinbase', 'hot-wallet'],
        notes='Coinbase hot wallet for withdrawals'
    ),
    '0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43': WhaleMetadata(
        address='0xA9D1e08C7793af67e9d92fe308d5697FB81d3E43',
        name='Coinbase Wallet 3',
        category=WhaleCategory.EXCHANGE,
        tags=['coinbase'],
        notes='Coinbase wallet 3'
    ),

    # Kraken
    '0x2910543Af39abA0Cd09dBb2D50200b3E800A63D2': WhaleMetadata(
        address='0x2910543Af39abA0Cd09dBb2D50200b3E800A63D2',
        name='Kraken Wallet 1',
        category=WhaleCategory.EXCHANGE,
        tags=['kraken'],
        notes='Kraken exchange wallet'
    ),
    '0x0A869d79a7052C7f1b55a8EbAbbEa3420F0D1E13': WhaleMetadata(
        address='0x0A869d79a7052C7f1b55a8EbAbbEa3420F0D1E13',
        name='Kraken Wallet 2',
        category=WhaleCategory.EXCHANGE,
        tags=['kraken'],
        notes='Kraken wallet 2'
    ),

    # Bitfinex
    '0x1151314c646Ce4E0eFD76d1aF4760aE66a9Fe30F': WhaleMetadata(
        address='0x1151314c646Ce4E0eFD76d1aF4760aE66a9Fe30F',
        name='Bitfinex Wallet 1',
        category=WhaleCategory.EXCHANGE,
        tags=['bitfinex'],
        notes='Bitfinex exchange wallet'
    ),
    '0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0': WhaleMetadata(
        address='0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0',
        name='Bitfinex Wallet 2',
        category=WhaleCategory.EXCHANGE,
        tags=['bitfinex'],
        notes='Bitfinex wallet 2'
    ),

    # OKX
    '0x98ec059Dc3aDFBdd63429454aEB0c990FBA4A128': WhaleMetadata(
        address='0x98ec059Dc3aDFBdd63429454aEB0c990FBA4A128',
        name='OKX Wallet 1',
        category=WhaleCategory.EXCHANGE,
        tags=['okx'],
        notes='OKX exchange wallet'
    ),
    '0x6cC5F688a315f3dC28A7781717a9A798a59fDA7b': WhaleMetadata(
        address='0x6cC5F688a315f3dC28A7781717a9A798a59fDA7b',
        name='OKX Wallet 2',
        category=WhaleCategory.EXCHANGE,
        tags=['okx'],
        notes='OKX wallet 2'
    ),

    # Huobi
    '0xDc76CD25977E0a5Ae17155770273aD58648900D3': WhaleMetadata(
        address='0xDc76CD25977E0a5Ae17155770273aD58648900D3',
        name='Huobi Wallet 1',
        category=WhaleCategory.EXCHANGE,
        tags=['huobi'],
        notes='Huobi exchange wallet'
    ),

    # Gate.io
    '0x0D0707963952f2fBA59dD06f2b425ace40b492Fe': WhaleMetadata(
        address='0x0D0707963952f2fBA59dD06f2b425ace40b492Fe',
        name='Gate.io Wallet',
        category=WhaleCategory.EXCHANGE,
        tags=['gateio'],
        notes='Gate.io exchange wallet'
    ),
}


# Known DeFi Protocol Addresses
DEFI_PROTOCOL_ADDRESSES = {
    # Uniswap
    '0x1F98431c8aD98523631AE4a59f267346ea31F984': WhaleMetadata(
        address='0x1F98431c8aD98523631AE4a59f267346ea31F984',
        name='Uniswap V3 Factory',
        category=WhaleCategory.DEFI_PROTOCOL,
        tags=['uniswap', 'dex', 'v3'],
        notes='Uniswap V3 factory contract'
    ),
    '0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45': WhaleMetadata(
        address='0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45',
        name='Uniswap Universal Router',
        category=WhaleCategory.DEFI_PROTOCOL,
        tags=['uniswap', 'dex', 'router'],
        notes='Uniswap universal router for swaps'
    ),

    # Aave
    '0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2': WhaleMetadata(
        address='0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2',
        name='Aave V3 Pool',
        category=WhaleCategory.DEFI_PROTOCOL,
        tags=['aave', 'lending'],
        notes='Aave V3 lending pool'
    ),

    # Curve
    '0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7': WhaleMetadata(
        address='0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7',
        name='Curve 3pool',
        category=WhaleCategory.DEFI_PROTOCOL,
        tags=['curve', 'stableswap'],
        notes='Curve 3pool (DAI/USDC/USDT)'
    ),
}


# Known Whale Addresses (Public whales with significant holdings)
KNOWN_WHALE_ADDRESSES = {
    '0x00000000219ab540356cBB839Cbe05303d7705Fa': WhaleMetadata(
        address='0x00000000219ab540356cBB839Cbe05303d7705Fa',
        name='Ethereum 2.0 Deposit Contract',
        category=WhaleCategory.INSTITUTIONAL,
        tags=['eth2', 'staking', 'beacon-chain'],
        min_balance_eth=30000000.0,  # Over 30M ETH
        notes='ETH2 staking deposit contract - largest ETH holder'
    ),

    '0xDA9dfA130Df4dE4673b89022EE50ff26f6EA73Cf': WhaleMetadata(
        address='0xDA9dfA130Df4dE4673b89022EE50ff26f6EA73Cf',
        name='Vitalik Buterin',
        category=WhaleCategory.KNOWN_WHALE,
        tags=['vitalik', 'founder', 'ethereum'],
        notes='Ethereum co-founder - movements watched closely'
    ),
}


# Bridge Addresses (for cross-chain tracking)
BRIDGE_ADDRESSES = {
    '0x3ee18B2214AFF97000D974cf647E7C347E8fa585': WhaleMetadata(
        address='0x3ee18B2214AFF97000D974cf647E7C347E8fa585',
        name='Wormhole Bridge',
        category=WhaleCategory.BRIDGE,
        tags=['bridge', 'wormhole', 'multichain'],
        notes='Wormhole cross-chain bridge'
    ),
}


class WhaleConfig:
    """
    Centralized configuration for whale addresses and metadata.

    Provides:
    - Address lookup
    - Category classification
    - Metadata retrieval
    """

    def __init__(self):
        """Initialize whale configuration."""
        self.exchanges = EXCHANGE_ADDRESSES
        self.defi_protocols = DEFI_PROTOCOL_ADDRESSES
        self.known_whales = KNOWN_WHALE_ADDRESSES
        self.bridges = BRIDGE_ADDRESSES

        # Combine all addresses
        self.all_addresses = {
            **self.exchanges,
            **self.defi_protocols,
            **self.known_whales,
            **self.bridges
        }

    def is_exchange(self, address: str) -> bool:
        """Check if address is a known exchange."""
        return address in self.exchanges

    def is_defi_protocol(self, address: str) -> bool:
        """Check if address is a DeFi protocol."""
        return address in self.defi_protocols

    def is_known_whale(self, address: str) -> bool:
        """Check if address is a known whale."""
        return address in self.known_whales

    def is_bridge(self, address: str) -> bool:
        """Check if address is a bridge."""
        return address in self.bridges

    def get_metadata(self, address: str) -> Optional[WhaleMetadata]:
        """Get metadata for an address."""
        return self.all_addresses.get(address)

    def get_name(self, address: str) -> str:
        """Get human-readable name for address."""
        metadata = self.get_metadata(address)
        if metadata:
            return metadata.name
        return f"Unknown ({address[:10]}...)"

    def get_category(self, address: str) -> WhaleCategory:
        """Get category for an address."""
        metadata = self.get_metadata(address)
        if metadata:
            return metadata.category
        return WhaleCategory.UNKNOWN

    def get_all_exchange_addresses(self) -> List[str]:
        """Get list of all exchange addresses."""
        return list(self.exchanges.keys())

    def get_all_known_addresses(self) -> List[str]:
        """Get list of all known addresses (any category)."""
        return list(self.all_addresses.keys())

    def classify_transaction_destination(self, address: str) -> Dict:
        """
        Classify a transaction destination.

        Returns:
            Dict with classification details:
            - is_known: bool
            - category: WhaleCategory
            - name: str
            - is_dump_risk: bool (True if exchange)
        """
        metadata = self.get_metadata(address)

        if not metadata:
            return {
                'is_known': False,
                'category': WhaleCategory.UNKNOWN,
                'name': 'Unknown Address',
                'is_dump_risk': False
            }

        return {
            'is_known': True,
            'category': metadata.category,
            'name': metadata.name,
            'is_dump_risk': metadata.category == WhaleCategory.EXCHANGE,
            'tags': metadata.tags
        }

    def get_addresses_by_tag(self, tag: str) -> List[str]:
        """Get all addresses with a specific tag."""
        return [
            addr for addr, metadata in self.all_addresses.items()
            if tag in metadata.tags
        ]

    def get_addresses_by_category(self, category: WhaleCategory) -> List[str]:
        """Get all addresses in a category."""
        return [
            addr for addr, metadata in self.all_addresses.items()
            if metadata.category == category
        ]

    def to_dict(self) -> Dict:
        """Export all configuration to dictionary."""
        return {
            'exchanges': {k: v.to_dict() for k, v in self.exchanges.items()},
            'defi_protocols': {k: v.to_dict() for k, v in self.defi_protocols.items()},
            'known_whales': {k: v.to_dict() for k, v in self.known_whales.items()},
            'bridges': {k: v.to_dict() for k, v in self.bridges.items()},
        }


# Global instance
_whale_config_instance = None


def get_whale_config() -> WhaleConfig:
    """Get singleton whale configuration instance."""
    global _whale_config_instance
    if _whale_config_instance is None:
        _whale_config_instance = WhaleConfig()
    return _whale_config_instance


# Convenience functions
def is_exchange_address(address: str) -> bool:
    """Check if address is a known exchange."""
    return get_whale_config().is_exchange(address)


def classify_address(address: str) -> Dict:
    """Classify an address (exchange, DeFi, whale, etc.)."""
    return get_whale_config().classify_transaction_destination(address)


def get_address_name(address: str) -> str:
    """Get human-readable name for address."""
    return get_whale_config().get_name(address)
