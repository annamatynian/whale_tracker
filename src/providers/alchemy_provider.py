"""
Alchemy RPC Provider

Similar to Infura, structure only for brevity.
Full implementation would mirror InfuraProvider with Alchemy URLs.
"""

from src.providers.infura_provider import InfuraProvider


class AlchemyProvider(InfuraProvider):
    """Alchemy RPC provider (extends InfuraProvider structure)."""

    NETWORK_URLS = {
        'ethereum': 'https://eth-mainnet.g.alchemy.com/v2',
        'base': 'https://base-mainnet.g.alchemy.com/v2',
        'arbitrum': 'https://arb-mainnet.g.alchemy.com/v2',
        'optimism': 'https://opt-mainnet.g.alchemy.com/v2',
        'polygon': 'https://polygon-mainnet.g.alchemy.com/v2',
    }

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return 'alchemy'
