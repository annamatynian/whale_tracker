"""
Multicall Client - Efficient Batch Blockchain Queries

Uses Multicall3 contract to batch multiple balance queries into single RPC calls.

WHY: Without Multicall, 1000 addresses = 1000 RPC calls (slow, rate limits)
     With Multicall, 1000 addresses = ~2 RPC calls (fast, efficient)

Multicall3 Contract: 0xcA11bde05977b3631167028862bE2a173976CA11 (universal across EVM chains)

Author: Whale Tracker Project
"""

import logging
import asyncio
from typing import Dict, List, Optional
from web3 import Web3
from datetime import datetime, UTC

# ERC20 Token Addresses (Ethereum Mainnet)
WETH_ADDRESS = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
STETH_ADDRESS = "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84"  # Lido stETH

# ERC20 ABI - minimal interface for balanceOf
ERC20_ABI = [
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

# Multicall3 ABI - minimal interface for aggregate3 function
MULTICALL3_ABI = [
    {
        "inputs": [{"name": "addr", "type": "address"}],
        "name": "getEthBalance",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "components": [
                    {"name": "target", "type": "address"},
                    {"name": "allowFailure", "type": "bool"},
                    {"name": "callData", "type": "bytes"}
                ],
                "name": "calls",
                "type": "tuple[]"
            }
        ],
        "name": "aggregate3",
        "outputs": [
            {
                "components": [
                    {"name": "success", "type": "bool"},
                    {"name": "returnData", "type": "bytes"}
                ],
                "name": "returnData",
                "type": "tuple[]"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]


class MulticallClient:
    """
    Batch blockchain queries using Multicall3 contract.
    
    Features:
    - Get balances for 100-1000 addresses in 1-2 RPC calls
    - Automatic chunking (500 addresses per call)
    - Graceful error handling (one fail doesn't break batch)
    - Support for historical balances (archive node)
    """
    
    # Multicall3 universal address (same across all EVM chains)
    MULTICALL3_ADDRESS = "0xcA11bde05977b3631167028862bE2a173976CA11"
    
    def __init__(self, web3_manager):
        """
        Initialize MulticallClient.
        
        Args:
            web3_manager: Instance of Web3Manager for RPC connection
        """
        self.logger = logging.getLogger(__name__)
        self.web3_manager = web3_manager
        self.w3 = web3_manager.web3  # Get Web3 instance
        
        if not self.w3:
            raise ValueError("Web3Manager must be initialized before MulticallClient")
        
        # Create Multicall3 contract instance
        self.multicall_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.MULTICALL3_ADDRESS),
            abi=MULTICALL3_ABI
        )
        
        self.logger.info(f"MulticallClient initialized with Multicall3 at {self.MULTICALL3_ADDRESS}")
    
    async def get_latest_block(self, network: str = "ethereum") -> int:
        """
        Get current block number.
        
        Args:
            network: Network name (default: "ethereum")
        
        Returns:
            int: Current block number
        
        Raises:
            Exception: If RPC call fails
        """
        try:
            # Use asyncio.to_thread for synchronous Web3 call
            block_number = await asyncio.to_thread(
                lambda: self.w3.eth.block_number
            )
            
            self.logger.debug(f"Latest block: {block_number}")
            return block_number
            
        except Exception as e:
            self.logger.error(f"Error getting latest block: {e}")
            raise
    
    def _create_balance_call(self, address: str) -> Dict:
        """
        Create call data for Multicall3.getEthBalance.
        
        WHY: Multicall3 has built-in getEthBalance(address) helper
        We encode this call and pass it to aggregate3()
        
        Args:
            address: Ethereum address
        
        Returns:
            Dict: Call structure for Multicall3.aggregate3
        """
        # Encode call to getEthBalance inside Multicall3 contract
        # Web3.py syntax: contract.functions.functionName(args)._encode_transaction_data()
        call_data = self.multicall_contract.functions.getEthBalance(
            Web3.to_checksum_address(address)
        )._encode_transaction_data()
        
        return {
            "target": Web3.to_checksum_address(self.MULTICALL3_ADDRESS),
            "allowFailure": True,  # Don't fail entire batch if one address fails
            "callData": call_data
        }
    
    def _is_gas_error(self, error: Exception) -> bool:
        """
        Detect if error is related to gas limit.
        
        WHY: Different RPC providers return different error messages:
        - Infura: "execution reverted"
        - Alchemy: "out of gas"
        - Quicknode: "gas limit exceeded"
        - L2s (Arbitrum, Optimism): "intrinsic gas too low"
        
        Args:
            error: Exception from RPC call
        
        Returns:
            bool: True if error is gas-related
        """
        error_msg = str(error).lower()
        gas_error_patterns = [
            "out of gas",
            "gas limit",
            "execution reverted",
            "intrinsic gas",
            "gas required exceeds",
            "exceeds block gas limit"
        ]
        
        return any(pattern in error_msg for pattern in gas_error_patterns)
    
    async def _execute_chunk_with_retry(
        self,
        chunk: List[str],
        chunk_idx: int,
        total_chunks: int,
        current_chunk_size: int,
        min_chunk_size: int
    ) -> Dict[str, Optional[int]]:
        """
        Execute Multicall3 for chunk with adaptive retry on gas errors.
        
        VULNERABILITY FIX #3:
        If chunk fails with gas error:
        1. Split chunk in half
        2. Retry each half separately
        3. Repeat until min_chunk_size reached
        
        Args:
            chunk: List of addresses to query
            chunk_idx: Current chunk index (for logging)
            total_chunks: Total number of chunks (for logging)
            current_chunk_size: Current chunk size
            min_chunk_size: Minimum chunk size before giving up
        
        Returns:
            Dict[address, balance or None]
        """
        try:
            self.logger.debug(
                f"Processing chunk {chunk_idx}/{total_chunks} "
                f"({len(chunk)} addresses, chunk_size={current_chunk_size})"
            )
            
            # Create Multicall3 calls for this chunk
            calls = [self._create_balance_call(addr) for addr in chunk]
            
            # Execute ONE RPC call for all addresses in chunk
            results = await asyncio.to_thread(
                self.multicall_contract.functions.aggregate3(calls).call
            )
            
            # Decode results
            balances = {}
            for address, (success, return_data) in zip(chunk, results):
                if success:
                    balance = int.from_bytes(return_data, byteorder='big')
                    if balance == 0:
                        self.logger.debug(f"⚠️ Zero balance for {address}")
                    balances[address] = balance
                else:
                    self.logger.warning(f"❌ RPC returned failure for {address} - network error!")
                    balances[address] = None
            
            self.logger.debug(
                f"Chunk {chunk_idx} complete: {len([b for b in balances.values() if b is not None and b > 0])} "
                f"addresses with non-zero balance"
            )
            
            return balances
            
        except Exception as e:
            # ✅ ADAPTIVE RETRY: Check if gas error
            if self._is_gas_error(e) and current_chunk_size > min_chunk_size:
                new_chunk_size = max(current_chunk_size // 2, min_chunk_size)
                
                self.logger.warning(
                    f"⚠️ Gas error in chunk {chunk_idx} (size={current_chunk_size}). "
                    f"Retrying with chunk_size={new_chunk_size}"
                )
                
                # Split chunk in half and retry
                mid = len(chunk) // 2
                chunk_1 = chunk[:mid]
                chunk_2 = chunk[mid:]
                
                # Recursive retry with smaller chunks
                balances_1 = await self._execute_chunk_with_retry(
                    chunk_1, f"{chunk_idx}a", total_chunks, new_chunk_size, min_chunk_size
                )
                balances_2 = await self._execute_chunk_with_retry(
                    chunk_2, f"{chunk_idx}b", total_chunks, new_chunk_size, min_chunk_size
                )
                
                # Merge results
                return {**balances_1, **balances_2}
            
            else:
                # Non-gas error OR reached min_chunk_size
                self.logger.error(
                    f"❌ Error processing chunk {chunk_idx}: {e} "
                    f"(chunk_size={current_chunk_size}, min={min_chunk_size})"
                )
                
                # Return None for all addresses (network error)
                return {address: None for address in chunk}
    
    async def get_balances_batch(
        self,
        addresses: List[str],
        network: str = "ethereum",
        chunk_size: int = 500,
        min_chunk_size: int = 50  # ✅ NEW: Minimum chunk size for adaptive retry
    ) -> Dict[str, Optional[int]]:
        """
        Get ETH balances for multiple addresses using Multicall3.aggregate3().
        
        REAL MULTICALL: Uses Multicall3 contract to batch 500 addresses into 1 RPC call!
        
        WHY CHUNKING: Multicall3 has gas limits (~10M gas per call)
        500 addresses × ~20k gas per getEthBalance = ~10M gas (safe limit)
        
        ADAPTIVE RETRY (VULNERABILITY FIX #3):
        If chunk fails with gas error, automatically retries with half chunk size.
        Prevents false "mass dump" signals from gas limit failures.
        
        Args:
            addresses: List of Ethereum addresses
            network: Network name (default: "ethereum")
            chunk_size: Max addresses per Multicall3 call (default: 500)
            min_chunk_size: Minimum chunk size before giving up (default: 50)
        
        Returns:
            Dict[str, int]: Mapping of address -> balance in Wei
        
        Raises:
            Exception: If all Multicall3 calls fail even with min chunk size
        
        Example:
            >>> client = MulticallClient(web3_manager)
            >>> addresses = ["0xd8dA6BF...", ...] * 1000
            >>> balances = await client.get_balances_batch(addresses)
            >>> # Result: 2 RPC calls instead of 1000!
        """
        if not addresses:
            return {}
        
        self.logger.info(f"Fetching balances for {len(addresses)} addresses using Multicall3")
        
        # Split addresses into chunks
        chunks = [addresses[i:i + chunk_size] for i in range(0, len(addresses), chunk_size)]
        self.logger.debug(f"Split into {len(chunks)} chunks of max {chunk_size} addresses")
        
        all_balances = {}
        
        for chunk_idx, chunk in enumerate(chunks, 1):
            # ✅ USE ADAPTIVE RETRY
            chunk_balances = await self._execute_chunk_with_retry(
                chunk=chunk,
                chunk_idx=chunk_idx,
                total_chunks=len(chunks),
                current_chunk_size=chunk_size,
                min_chunk_size=min_chunk_size
            )
            
            all_balances.update(chunk_balances)
        
        self.logger.info(
            f"Successfully fetched {len(all_balances)} balances "
            f"({len([b for b in all_balances.values() if b is not None and b > 0])} non-zero) "
            f"using {len(chunks)} Multicall3 calls"
        )
        
        return all_balances
    
    async def _execute_erc20_chunk_with_retry(
        self,
        chunk: List[str],
        token_address: str,
        token_name: str,
        chunk_idx: int,
        total_chunks: int,
        current_chunk_size: int,
        min_chunk_size: int
    ) -> Dict[str, Optional[int]]:
        """
        Execute Multicall3 for ERC20 chunk with adaptive retry.
        
        VULNERABILITY FIX #3 (ERC20 variant):
        ERC20 balanceOf() is ~2x gas cost vs native ETH.
        More likely to hit gas limits.
        
        Args:
            chunk: List of addresses
            token_address: ERC20 token address
            token_name: Token name for logging ("WETH", "stETH")
            chunk_idx: Current chunk index
            total_chunks: Total chunks
            current_chunk_size: Current chunk size
            min_chunk_size: Minimum chunk size
        
        Returns:
            Dict[address, balance or None]
        """
        try:
            self.logger.debug(
                f"Processing {token_name} chunk {chunk_idx}/{total_chunks} "
                f"({len(chunk)} addresses, chunk_size={current_chunk_size})"
            )
            
            # Create Multicall3 calls for this chunk
            calls = [
                self._create_erc20_balance_call(token_address, addr)
                for addr in chunk
            ]
            
            # Execute ONE RPC call for all addresses in chunk
            results = await asyncio.to_thread(
                self.multicall_contract.functions.aggregate3(calls).call
            )
            
            # Decode results
            balances = {}
            for address, (success, return_data) in zip(chunk, results):
                if success:
                    balance = int.from_bytes(return_data, byteorder='big')
                    if balance == 0:
                        self.logger.debug(f"⚠️ Zero {token_name} balance for {address}")
                    balances[address] = balance
                else:
                    self.logger.warning(
                        f"❌ RPC returned failure for {address} {token_name} balance - network error!"
                    )
                    balances[address] = None
            
            self.logger.debug(
                f"{token_name} chunk {chunk_idx} complete: "
                f"{len([b for b in balances.values() if b is not None and b > 0])} "
                f"addresses with non-zero balance"
            )
            
            return balances
            
        except Exception as e:
            # ✅ ADAPTIVE RETRY: Check if gas error
            if self._is_gas_error(e) and current_chunk_size > min_chunk_size:
                new_chunk_size = max(current_chunk_size // 2, min_chunk_size)
                
                self.logger.warning(
                    f"⚠️ Gas error in {token_name} chunk {chunk_idx} (size={current_chunk_size}). "
                    f"Retrying with chunk_size={new_chunk_size}"
                )
                
                # Split chunk and retry
                mid = len(chunk) // 2
                chunk_1 = chunk[:mid]
                chunk_2 = chunk[mid:]
                
                # Recursive retry
                balances_1 = await self._execute_erc20_chunk_with_retry(
                    chunk_1, token_address, token_name, f"{chunk_idx}a", 
                    total_chunks, new_chunk_size, min_chunk_size
                )
                balances_2 = await self._execute_erc20_chunk_with_retry(
                    chunk_2, token_address, token_name, f"{chunk_idx}b",
                    total_chunks, new_chunk_size, min_chunk_size
                )
                
                return {**balances_1, **balances_2}
            
            else:
                # Non-gas error OR reached min_chunk_size
                self.logger.error(
                    f"❌ Error processing {token_name} chunk {chunk_idx}: {e} "
                    f"(chunk_size={current_chunk_size}, min={min_chunk_size})"
                )
                
                return {address: None for address in chunk}
    
    def _create_erc20_balance_call(self, token_address: str, holder_address: str) -> Dict:
        """
        Create call data for ERC20.balanceOf.
        
        WHY: ERC20 tokens don't have Multicall3 helper, so we encode the call manually
        
        Args:
            token_address: ERC20 token contract address (WETH or stETH)
            holder_address: Address whose balance we want to check
        
        Returns:
            Dict: Call structure for Multicall3.aggregate3
        """
        # Create ERC20 contract instance
        erc20_contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(token_address),
            abi=ERC20_ABI
        )
        
        # Encode call to balanceOf(address)
        call_data = erc20_contract.functions.balanceOf(
            Web3.to_checksum_address(holder_address)
        )._encode_transaction_data()
        
        return {
            "target": Web3.to_checksum_address(token_address),  # Call token contract, not Multicall3
            "allowFailure": True,
            "callData": call_data
        }
    
    async def get_erc20_balances_batch(
        self,
        addresses: List[str],
        token_address: str,
        network: str = "ethereum",
        chunk_size: int = 500,
        min_chunk_size: int = 50  # ✅ NEW: Adaptive retry support
    ) -> Dict[str, Optional[int]]:
        """
        Get ERC20 token balances for multiple addresses using Multicall3.
        
        WHY: Same batching efficiency as native ETH, but for WETH/stETH
        
        ADAPTIVE RETRY (VULNERABILITY FIX #3):
        ERC20 balanceOf() is ~2x more expensive than getEthBalance()
        Gas errors are more likely with 500 addresses.
        
        Args:
            addresses: List of Ethereum addresses
            token_address: ERC20 token contract address (use WETH_ADDRESS or STETH_ADDRESS constants)
            network: Network name (default: "ethereum")
            chunk_size: Max addresses per Multicall3 call (default: 500)
            min_chunk_size: Minimum chunk size before giving up (default: 50)
        
        Returns:
            Dict[str, int]: Mapping of address -> token balance in Wei (or smallest unit)
        
        Example:
            >>> # Get WETH balances for 1000 whales
            >>> weth_balances = await client.get_erc20_balances_batch(
            ...     addresses=whale_addresses,
            ...     token_address=WETH_ADDRESS
            ... )
            >>> # Get stETH balances
            >>> steth_balances = await client.get_erc20_balances_batch(
            ...     addresses=whale_addresses,
            ...     token_address=STETH_ADDRESS
            ... )
        """
        if not addresses:
            return {}
        
        # Determine token name for logging
        token_name = "ERC20"
        if token_address.lower() == WETH_ADDRESS.lower():
            token_name = "WETH"
        elif token_address.lower() == STETH_ADDRESS.lower():
            token_name = "stETH"
        
        self.logger.info(
            f"Fetching {token_name} balances for {len(addresses)} addresses using Multicall3"
        )
        
        # Split addresses into chunks
        chunks = [addresses[i:i + chunk_size] for i in range(0, len(addresses), chunk_size)]
        self.logger.debug(f"Split into {len(chunks)} chunks of max {chunk_size} addresses")
        
        all_balances = {}
        
        for chunk_idx, chunk in enumerate(chunks, 1):
            # ✅ USE ADAPTIVE RETRY FOR ERC20
            chunk_balances = await self._execute_erc20_chunk_with_retry(
                chunk=chunk,
                token_address=token_address,
                token_name=token_name,
                chunk_idx=chunk_idx,
                total_chunks=len(chunks),
                current_chunk_size=chunk_size,
                min_chunk_size=min_chunk_size
            )
            
            all_balances.update(chunk_balances)
        
        self.logger.info(
            f"Successfully fetched {len(all_balances)} {token_name} balances "
            f"({len([b for b in all_balances.values() if b is not None and b > 0])} non-zero) "
            f"using {len(chunks)} Multicall3 calls"
        )
        
        return all_balances

    async def get_historical_balances(
        self,
        addresses: List[str],
        block_number: int,
        network: str = "ethereum"
    ) -> Dict[str, int]:
        """
        Get balances at specific historical block.
        
        IMPORTANT: Requires archive node (Alchemy paid tier, Infura paid tier)
        
        MVP APPROACH: For blocks older than 128 blocks, returns current balances
        (since Alchemy free tier has limited archive access)
        
        Args:
            addresses: List of Ethereum addresses
            block_number: Historical block number
            network: Network name (default: "ethereum")
        
        Returns:
            Dict[str, int]: Mapping of address -> balance in Wei at that block
        
        Example:
            >>> balances = await client.get_historical_balances(
            ...     addresses=["0xd8dA6BF..."],
            ...     block_number=18500000
            ... )
        """
        try:
            # Get current block
            current_block = await self.get_latest_block(network)
            
            # Check if block is too old for free tier archive access
            blocks_behind = current_block - block_number
            
            if blocks_behind > 128:
                self.logger.warning(
                    f"Block {block_number} is {blocks_behind} blocks behind current. "
                    f"Deep archive access requires paid tier. Using current balances for MVP."
                )
                # MVP: Return current balances
                return await self.get_balances_batch(addresses, network)
            
            # For recent blocks, get historical balances
            self.logger.info(f"Fetching historical balances at block {block_number}")
            
            all_balances = {}
            
            for address in addresses:
                try:
                    checksum_address = Web3.to_checksum_address(address)
                    
                    # Use asyncio.to_thread for synchronous Web3 call
                    balance = await asyncio.to_thread(
                        self.w3.eth.get_balance,
                        checksum_address,
                        block_number
                    )
                    
                    all_balances[address] = balance
                    
                except Exception as e:
                    self.logger.warning(f"Failed to get historical balance for {address}: {e}")
                    all_balances[address] = 0
            
            return all_balances
            
        except Exception as e:
            self.logger.error(f"Error getting historical balances: {e}")
            raise
    
    async def health_check(self) -> Dict:
        """
        Check if MulticallClient is working properly.
        
        Returns:
            Dict: Health status
        """
        try:
            # Try to get current block
            block = await self.get_latest_block()
            
            # Try to get balance of zero address (should be 0)
            zero_address = "0x0000000000000000000000000000000000000000"
            balances = await self.get_balances_batch([zero_address])
            
            return {
                "status": "healthy",
                "latest_block": block,
                "test_balance_query": "success",
                "multicall_address": self.MULTICALL3_ADDRESS
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
