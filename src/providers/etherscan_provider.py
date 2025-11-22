"""
Etherscan Provider

Blockchain data provider using Etherscan API.
Supports Ethereum, Base, Arbitrum, and other EVM chains.
"""

import os
import logging
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.abstractions.blockchain_data_provider import BlockchainDataProvider


class EtherscanProvider(BlockchainDataProvider):
    """
    Etherscan blockchain data provider.

    Supports multiple networks through different API endpoints.
    """

    # API base URLs for different networks
    BASE_URLS = {
        'ethereum': 'https://api.etherscan.io/api',
        'base': 'https://api.basescan.org/api',
        'arbitrum': 'https://api.arbiscan.io/api',
        'optimism': 'https://api-optimistic.etherscan.io/api',
        'polygon': 'https://api.polygonscan.com/api',
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        network: str = 'ethereum',
        rate_limit: int = 5
    ):
        """
        Initialize Etherscan provider.

        Args:
            api_key: Etherscan API key (defaults to ETHERSCAN_API_KEY env var)
            network: Network name (ethereum, base, arbitrum, etc.)
            rate_limit: Rate limit in requests per second
        """
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key or os.getenv('ETHERSCAN_API_KEY')
        self._network = network
        self._rate_limit = rate_limit
        self.base_url = self.BASE_URLS.get(network)

        if not self.base_url:
            self.logger.warning(f"Unknown network: {network}, using ethereum")
            self.base_url = self.BASE_URLS['ethereum']

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return 'etherscan'

    @property
    def network(self) -> str:
        """Get network name."""
        return self._network

    @property
    def is_available(self) -> bool:
        """Check if provider is configured."""
        return bool(self.api_key and self.base_url)

    @property
    def rate_limit_per_second(self) -> Optional[int]:
        """Get rate limit."""
        return self._rate_limit

    async def _make_request(
        self,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make API request to Etherscan."""
        params['apikey'] = self.api_key

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params, timeout=30) as response:
                    response.raise_for_status()
                    data = await response.json()

                    if data.get('status') == '1':
                        return data.get('result', {})
                    else:
                        error_msg = data.get('message', 'Unknown error')
                        raise Exception(f"Etherscan API error: {error_msg}")

        except Exception as e:
            self.logger.error(f"Etherscan request failed: {e}")
            raise

    async def get_transaction_count(
        self,
        address: str,
        block_number: Optional[int] = None
    ) -> int:
        """Get transaction count for address."""
        params = {
            'module': 'proxy',
            'action': 'eth_getTransactionCount',
            'address': address,
            'tag': hex(block_number) if block_number else 'latest'
        }

        result = await self._make_request(params)
        return int(result, 16)

    async def get_transactions(
        self,
        address: str,
        start_block: Optional[int] = None,
        end_block: Optional[int] = None,
        sort: str = 'asc',
        page: int = 1,
        offset: int = 100
    ) -> List[Dict[str, Any]]:
        """Get transactions for address."""
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'startblock': start_block or 0,
            'endblock': end_block or 99999999,
            'page': page,
            'offset': offset,
            'sort': sort
        }

        result = await self._make_request(params)
        return result if isinstance(result, list) else []

    async def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """Get transaction details."""
        params = {
            'module': 'proxy',
            'action': 'eth_getTransactionByHash',
            'txhash': tx_hash
        }

        return await self._make_request(params)

    async def get_transaction_receipt(self, tx_hash: str) -> Dict[str, Any]:
        """Get transaction receipt."""
        params = {
            'module': 'proxy',
            'action': 'eth_getTransactionReceipt',
            'txhash': tx_hash
        }

        return await self._make_request(params)

    async def get_internal_transactions(
        self,
        address: Optional[str] = None,
        tx_hash: Optional[str] = None,
        start_block: Optional[int] = None,
        end_block: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get internal transactions."""
        params = {
            'module': 'account',
            'action': 'txlistinternal'
        }

        if tx_hash:
            params['txhash'] = tx_hash
        elif address:
            params['address'] = address
            params['startblock'] = start_block or 0
            params['endblock'] = end_block or 99999999
        else:
            raise ValueError("Either address or tx_hash must be provided")

        result = await self._make_request(params)
        return result if isinstance(result, list) else []

    async def get_token_transfers(
        self,
        address: Optional[str] = None,
        contract_address: Optional[str] = None,
        start_block: Optional[int] = None,
        end_block: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get token transfers."""
        params = {
            'module': 'account',
            'action': 'tokentx',
            'startblock': start_block or 0,
            'endblock': end_block or 99999999
        }

        if address:
            params['address'] = address
        if contract_address:
            params['contractaddress'] = contract_address

        result = await self._make_request(params)
        return result if isinstance(result, list) else []

    async def get_balance(
        self,
        address: str,
        block_number: Optional[int] = None
    ) -> int:
        """Get ETH balance."""
        params = {
            'module': 'account',
            'action': 'balance',
            'address': address,
            'tag': hex(block_number) if block_number else 'latest'
        }

        result = await self._make_request(params)
        return int(result)

    async def get_balance_history(
        self,
        address: str,
        start_block: int,
        end_block: int
    ) -> List[Dict[str, Any]]:
        """Get balance history (not directly supported by Etherscan)."""
        raise NotImplementedError("Balance history not supported by Etherscan API")

    async def get_contract_abi(self, address: str) -> List[Dict[str, Any]]:
        """Get contract ABI."""
        params = {
            'module': 'contract',
            'action': 'getabi',
            'address': address
        }

        result = await self._make_request(params)
        import json
        return json.loads(result)

    async def get_contract_source_code(self, address: str) -> Dict[str, Any]:
        """Get contract source code."""
        params = {
            'module': 'contract',
            'action': 'getsourcecode',
            'address': address
        }

        result = await self._make_request(params)
        return result[0] if isinstance(result, list) and result else {}

    async def get_block_timestamp(self, block_number: int) -> datetime:
        """Get block timestamp."""
        params = {
            'module': 'block',
            'action': 'getblockreward',
            'blockno': block_number
        }

        result = await self._make_request(params)
        timestamp = int(result.get('timeStamp', 0))
        return datetime.fromtimestamp(timestamp)

    async def get_block_by_timestamp(
        self,
        timestamp: int,
        closest: str = 'before'
    ) -> int:
        """Get block number by timestamp."""
        params = {
            'module': 'block',
            'action': 'getblocknobytime',
            'timestamp': timestamp,
            'closest': closest
        }

        result = await self._make_request(params)
        return int(result)

    async def get_gas_oracle(self) -> Dict[str, Any]:
        """Get gas prices."""
        params = {
            'module': 'gastracker',
            'action': 'gasoracle'
        }

        return await self._make_request(params)

    async def test_connection(self) -> bool:
        """Test connection to Etherscan."""
        try:
            # Test with simple balance query for null address
            params = {
                'module': 'account',
                'action': 'balance',
                'address': '0x0000000000000000000000000000000000000000',
                'tag': 'latest',
                'apikey': self.api_key
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params, timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()

                    if data.get('status') == '1':
                        self.logger.info(f"Etherscan connection successful ({self._network})")
                        return True
                    else:
                        self.logger.error(f"Etherscan API error: {data.get('message')}")
                        return False

        except Exception as e:
            self.logger.error(f"Etherscan connection test failed: {e}")
            return False

    @property
    def supported_features(self) -> List[str]:
        """Get supported features."""
        return [
            'transactions',
            'internal_txs',
            'token_transfers',
            'balance',
            'contract_abi',
            'gas_oracle'
        ]
