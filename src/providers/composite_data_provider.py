"""
Composite Data Provider

Combines multiple blockchain data providers with failover.
"""

import logging
from typing import List, Tuple, Dict, Any, Optional

from src.abstractions.blockchain_data_provider import BlockchainDataProvider


class CompositeDataProvider(BlockchainDataProvider):
    """
    Composite blockchain data provider.

    Uses multiple providers with priority-based failover.
    """

    def __init__(self, providers: List[Tuple[int, BlockchainDataProvider]]):
        """
        Initialize composite provider.

        Args:
            providers: List of (priority, provider) tuples
        """
        self.logger = logging.getLogger(__name__)
        self.providers = sorted(providers, key=lambda x: x[0])
        self._primary_provider = self.providers[0][1] if self.providers else None

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        names = [p.provider_name for _, p in self.providers]
        return f"composite[{','.join(names)}]"

    @property
    def network(self) -> str:
        """Get network."""
        return self._primary_provider.network if self._primary_provider else 'unknown'

    @property
    def is_available(self) -> bool:
        """Check availability."""
        return any(p.is_available for _, p in self.providers)

    async def _execute_with_failover(self, method_name: str, *args, **kwargs):
        """Execute method with failover."""
        last_error = None

        for priority, provider in self.providers:
            if not provider.is_available:
                continue

            try:
                method = getattr(provider, method_name)
                return await method(*args, **kwargs)
            except Exception as e:
                self.logger.warning(f"Provider {provider.provider_name} failed: {e}")
                last_error = e
                continue

        raise Exception(f"All providers failed. Last error: {last_error}")

    # Delegate all methods to _execute_with_failover
    async def get_transaction_count(self, address: str, block_number: Optional[int] = None) -> int:
        """Get transaction count."""
        return await self._execute_with_failover('get_transaction_count', address, block_number)

    async def get_transactions(self, address: str, start_block: Optional[int] = None, end_block: Optional[int] = None, sort: str = 'asc', page: int = 1, offset: int = 100) -> List[Dict[str, Any]]:
        """Get transactions."""
        return await self._execute_with_failover('get_transactions', address, start_block, end_block, sort, page, offset)

    async def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """Get transaction."""
        return await self._execute_with_failover('get_transaction', tx_hash)

    async def get_transaction_receipt(self, tx_hash: str) -> Dict[str, Any]:
        """Get receipt."""
        return await self._execute_with_failover('get_transaction_receipt', tx_hash)

    async def get_internal_transactions(self, address: Optional[str] = None, tx_hash: Optional[str] = None, start_block: Optional[int] = None, end_block: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get internal transactions."""
        return await self._execute_with_failover('get_internal_transactions', address, tx_hash, start_block, end_block)

    async def get_token_transfers(self, address: Optional[str] = None, contract_address: Optional[str] = None, start_block: Optional[int] = None, end_block: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get token transfers."""
        return await self._execute_with_failover('get_token_transfers', address, contract_address, start_block, end_block)

    async def get_balance(self, address: str, block_number: Optional[int] = None) -> int:
        """Get balance."""
        return await self._execute_with_failover('get_balance', address, block_number)

    async def get_balance_history(self, address: str, start_block: int, end_block: int) -> List[Dict[str, Any]]:
        """Get balance history."""
        return await self._execute_with_failover('get_balance_history', address, start_block, end_block)

    async def get_contract_abi(self, address: str) -> List[Dict[str, Any]]:
        """Get ABI."""
        return await self._execute_with_failover('get_contract_abi', address)

    async def get_contract_source_code(self, address: str) -> Dict[str, Any]:
        """Get source code."""
        return await self._execute_with_failover('get_contract_source_code', address)

    async def get_block_timestamp(self, block_number: int):
        """Get block timestamp."""
        return await self._execute_with_failover('get_block_timestamp', block_number)

    async def get_block_by_timestamp(self, timestamp: int, closest: str = 'before') -> int:
        """Get block by timestamp."""
        return await self._execute_with_failover('get_block_by_timestamp', timestamp, closest)

    async def get_gas_oracle(self) -> Dict[str, Any]:
        """Get gas prices."""
        return await self._execute_with_failover('get_gas_oracle')

    async def test_connection(self) -> bool:
        """Test connection."""
        for _, provider in self.providers:
            if await provider.test_connection():
                return True
        return False
