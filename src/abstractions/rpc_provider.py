"""
RPC Provider Abstraction

Abstract base class for blockchain RPC providers (Infura, Alchemy, Ankr, etc.).
Enables failover, load balancing, and multi-provider support.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime


class RPCProvider(ABC):
    """
    Abstract RPC provider interface.

    All RPC implementations (Infura, Alchemy, Ankr, custom nodes, etc.)
    must implement this interface.
    """

    @abstractmethod
    async def get_block_number(self) -> int:
        """
        Get latest block number.

        Returns:
            int: Current block number

        Raises:
            Exception: If RPC call fails
        """
        pass

    @abstractmethod
    async def get_block(self, block_number: int, full_transactions: bool = False) -> Dict[str, Any]:
        """
        Get block data.

        Args:
            block_number: Block number to fetch
            full_transactions: If True, include full transaction objects

        Returns:
            Dict: Block data

        Raises:
            Exception: If RPC call fails
        """
        pass

    @abstractmethod
    async def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get transaction data.

        Args:
            tx_hash: Transaction hash

        Returns:
            Dict: Transaction data

        Raises:
            Exception: If RPC call fails or transaction not found
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
            Exception: If RPC call fails or receipt not found
        """
        pass

    @abstractmethod
    async def get_balance(self, address: str, block_number: Optional[int] = None) -> int:
        """
        Get address balance in Wei.

        Args:
            address: Ethereum address
            block_number: Block number (None for latest)

        Returns:
            int: Balance in Wei

        Raises:
            Exception: If RPC call fails
        """
        pass

    @abstractmethod
    async def get_transaction_count(self, address: str, block_number: Optional[int] = None) -> int:
        """
        Get transaction count (nonce) for address.

        Args:
            address: Ethereum address
            block_number: Block number (None for latest)

        Returns:
            int: Transaction count

        Raises:
            Exception: If RPC call fails
        """
        pass

    @abstractmethod
    async def get_code(self, address: str, block_number: Optional[int] = None) -> str:
        """
        Get contract code.

        Args:
            address: Contract address
            block_number: Block number (None for latest)

        Returns:
            str: Contract bytecode (hex string)

        Raises:
            Exception: If RPC call fails
        """
        pass

    @abstractmethod
    async def call(
        self,
        to_address: str,
        data: str,
        from_address: Optional[str] = None,
        block_number: Optional[int] = None
    ) -> str:
        """
        Execute eth_call (read-only contract call).

        Args:
            to_address: Contract address
            data: Call data (hex string)
            from_address: Optional sender address
            block_number: Block number (None for latest)

        Returns:
            str: Call result (hex string)

        Raises:
            Exception: If RPC call fails
        """
        pass

    @abstractmethod
    async def get_logs(
        self,
        from_block: int,
        to_block: int,
        addresses: Optional[List[str]] = None,
        topics: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get event logs.

        Args:
            from_block: Start block number
            to_block: End block number
            addresses: Optional list of contract addresses
            topics: Optional list of topics

        Returns:
            List[Dict]: List of log entries

        Raises:
            Exception: If RPC call fails
        """
        pass

    @abstractmethod
    async def estimate_gas(
        self,
        to_address: str,
        from_address: Optional[str] = None,
        data: Optional[str] = None,
        value: Optional[int] = None
    ) -> int:
        """
        Estimate gas for transaction.

        Args:
            to_address: Recipient address
            from_address: Optional sender address
            data: Optional transaction data
            value: Optional value in Wei

        Returns:
            int: Estimated gas

        Raises:
            Exception: If estimation fails
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Get provider name.

        Returns:
            str: Provider name (e.g., 'infura', 'alchemy', 'ankr')
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
    def is_healthy(self) -> bool:
        """
        Check if provider is healthy and responsive.

        Returns:
            bool: True if provider is healthy
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test connection to RPC provider.

        Returns:
            bool: True if connection successful
        """
        pass

    @property
    def priority(self) -> int:
        """
        Get provider priority (lower is higher priority).

        Returns:
            int: Priority value (default: 100)
        """
        return 100

    @property
    def rate_limit_per_second(self) -> Optional[int]:
        """
        Get rate limit in requests per second.

        Returns:
            Optional[int]: Rate limit or None if unlimited
        """
        return None

    @property
    def last_error(self) -> Optional[str]:
        """
        Get last error message.

        Returns:
            Optional[str]: Last error or None
        """
        return None

    @property
    def last_success_time(self) -> Optional[datetime]:
        """
        Get timestamp of last successful request.

        Returns:
            Optional[datetime]: Last success time or None
        """
        return None
