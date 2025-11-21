"""
Blockchain Data Provider Abstraction

Abstract base class for blockchain data APIs (Etherscan, Alchemy, The Graph, etc.).
Enables multi-chain support and provider fallback.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime


class BlockchainDataProvider(ABC):
    """
    Abstract blockchain data provider interface.

    Implementations can use Etherscan, Basescan, Arbiscan, Alchemy, Moralis,
    The Graph, or any other blockchain data API.
    """

    @abstractmethod
    async def get_transaction_count(
        self,
        address: str,
        block_number: Optional[int] = None
    ) -> int:
        """
        Get transaction count (nonce) for address at specific block.

        Args:
            address: Ethereum address
            block_number: Block number (None for latest)

        Returns:
            int: Transaction count

        Raises:
            Exception: If API call fails
        """
        pass

    @abstractmethod
    async def get_transactions(
        self,
        address: str,
        start_block: Optional[int] = None,
        end_block: Optional[int] = None,
        sort: str = 'asc',
        page: int = 1,
        offset: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get transactions for address.

        Args:
            address: Ethereum address
            start_block: Starting block number (None for genesis)
            end_block: Ending block number (None for latest)
            sort: Sort order ('asc' or 'desc')
            page: Page number for pagination
            offset: Number of transactions per page

        Returns:
            List[Dict]: List of transaction dictionaries

        Raises:
            Exception: If API call fails
        """
        pass

    @abstractmethod
    async def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get transaction details.

        Args:
            tx_hash: Transaction hash

        Returns:
            Dict: Transaction details

        Raises:
            Exception: If API call fails or transaction not found
        """
        pass

    @abstractmethod
    async def get_transaction_receipt(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get transaction receipt.

        Args:
            tx_hash: Transaction hash

        Returns:
            Dict: Transaction receipt

        Raises:
            Exception: If API call fails or receipt not found
        """
        pass

    @abstractmethod
    async def get_internal_transactions(
        self,
        address: Optional[str] = None,
        tx_hash: Optional[str] = None,
        start_block: Optional[int] = None,
        end_block: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get internal transactions.

        Args:
            address: Address to filter by (optional)
            tx_hash: Transaction hash to filter by (optional)
            start_block: Starting block number
            end_block: Ending block number

        Returns:
            List[Dict]: List of internal transactions

        Raises:
            Exception: If API call fails
        """
        pass

    @abstractmethod
    async def get_token_transfers(
        self,
        address: Optional[str] = None,
        contract_address: Optional[str] = None,
        start_block: Optional[int] = None,
        end_block: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get ERC20 token transfers.

        Args:
            address: Address to filter by (optional)
            contract_address: Token contract address (optional)
            start_block: Starting block number
            end_block: Ending block number

        Returns:
            List[Dict]: List of token transfer events

        Raises:
            Exception: If API call fails
        """
        pass

    @abstractmethod
    async def get_balance(
        self,
        address: str,
        block_number: Optional[int] = None
    ) -> int:
        """
        Get ETH balance for address.

        Args:
            address: Ethereum address
            block_number: Block number (None for latest)

        Returns:
            int: Balance in Wei

        Raises:
            Exception: If API call fails
        """
        pass

    @abstractmethod
    async def get_balance_history(
        self,
        address: str,
        start_block: int,
        end_block: int
    ) -> List[Dict[str, Any]]:
        """
        Get balance history over block range.

        Args:
            address: Ethereum address
            start_block: Starting block number
            end_block: Ending block number

        Returns:
            List[Dict]: List of {block_number, balance, timestamp}

        Raises:
            Exception: If API call fails or not supported
        """
        pass

    @abstractmethod
    async def get_contract_abi(self, address: str) -> List[Dict[str, Any]]:
        """
        Get contract ABI.

        Args:
            address: Contract address

        Returns:
            List[Dict]: Contract ABI

        Raises:
            Exception: If API call fails or contract not verified
        """
        pass

    @abstractmethod
    async def get_contract_source_code(self, address: str) -> Dict[str, Any]:
        """
        Get verified contract source code.

        Args:
            address: Contract address

        Returns:
            Dict: Source code and metadata

        Raises:
            Exception: If API call fails or contract not verified
        """
        pass

    @abstractmethod
    async def get_block_timestamp(self, block_number: int) -> datetime:
        """
        Get block timestamp.

        Args:
            block_number: Block number

        Returns:
            datetime: Block timestamp

        Raises:
            Exception: If API call fails
        """
        pass

    @abstractmethod
    async def get_block_by_timestamp(
        self,
        timestamp: int,
        closest: str = 'before'
    ) -> int:
        """
        Get block number closest to timestamp.

        Args:
            timestamp: Unix timestamp
            closest: 'before' or 'after'

        Returns:
            int: Block number

        Raises:
            Exception: If API call fails
        """
        pass

    @abstractmethod
    async def get_gas_oracle(self) -> Dict[str, Any]:
        """
        Get current gas prices.

        Returns:
            Dict: Gas prices (safe, propose, fast)

        Raises:
            Exception: If API call fails
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Get provider name.

        Returns:
            str: Provider name (e.g., 'etherscan', 'alchemy', 'thegraph')
        """
        pass

    @property
    @abstractmethod
    def network(self) -> str:
        """
        Get network name.

        Returns:
            str: Network name (e.g., 'ethereum', 'base', 'arbitrum')
        """
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if provider is available and configured.

        Returns:
            bool: True if provider can be used
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test connection to data provider.

        Returns:
            bool: True if connection successful
        """
        pass

    @property
    def rate_limit_per_second(self) -> Optional[int]:
        """
        Get rate limit in requests per second.

        Returns:
            Optional[int]: Rate limit or None if unlimited
        """
        return None

    @property
    def supports_batch_requests(self) -> bool:
        """
        Check if provider supports batch requests.

        Returns:
            bool: True if batch requests are supported
        """
        return False

    @property
    def supported_features(self) -> List[str]:
        """
        Get list of supported features.

        Returns:
            List[str]: Feature list (e.g., ['transactions', 'internal_txs', 'token_transfers'])
        """
        return ['transactions', 'balance']
