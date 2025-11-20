"""
DeFi Utilities - Protocol Interaction
====================================

This module handles interactions with DeFi protocols:
- Uniswap V2/V3 pools
- Pool reserves and LP token information
- Protocol data integration

Note: Price fetching functionality moved to PriceStrategyManager

Author: Generated for DeFi-RAG Project
"""

import logging
import aiohttp
from typing import Dict, Any, Optional, List, Tuple
from web3 import Web3

from src.web3_utils import Web3Manager, UNISWAP_V2_PAIR_ABI, ERC20_ABI


class DeFiAnalyzer:
    """
    Analyzes DeFi protocols and LP positions.
    """
    
    def __init__(self):
        """Initialize DeFi Analyzer."""
        self.logger = logging.getLogger(__name__)
        self.web3_manager = None
    
    def set_web3_manager(self, web3_manager: Web3Manager):
        """Set Web3Manager instance."""
        self.web3_manager = web3_manager
    
    async def get_uniswap_v2_reserves(self, pair_address: str) -> Optional[Dict[str, Any]]:
        """
        Get reserves from Uniswap V2 pair contract.
        
        Args:
            pair_address: Uniswap V2 pair contract address
            
        Returns:
            Optional[Dict]: Reserves data or None if error
        """
        try:
            if not self.web3_manager or not self.web3_manager.web3:
                self.logger.error("Web3Manager not initialized")
                return None
            
            # Get reserves using contract call
            reserves_result = await self.web3_manager.call_contract_function(
                pair_address,
                UNISWAP_V2_PAIR_ABI,
                'getReserves'
            )
            
            if not reserves_result:
                return None
            
            reserve0, reserve1, timestamp = reserves_result
            
            # Get total supply
            total_supply = await self.web3_manager.call_contract_function(
                pair_address,
                UNISWAP_V2_PAIR_ABI,
                'totalSupply'
            )
            
            # Get token addresses
            token0_address = await self.web3_manager.call_contract_function(
                pair_address,
                UNISWAP_V2_PAIR_ABI,
                'token0'
            )
            
            token1_address = await self.web3_manager.call_contract_function(
                pair_address,
                UNISWAP_V2_PAIR_ABI,
                'token1'
            )
            
            # Get token decimals
            token0_decimals = await self.web3_manager.call_contract_function(
                token0_address,
                ERC20_ABI,
                'decimals'
            )
            
            token1_decimals = await self.web3_manager.call_contract_function(
                token1_address,
                ERC20_ABI,
                'decimals'
            )
            
            # Convert to human readable format
            reserve0_formatted = reserve0 / (10 ** token0_decimals) if token0_decimals else 0
            reserve1_formatted = reserve1 / (10 ** token1_decimals) if token1_decimals else 0
            total_supply_formatted = total_supply / (10 ** 18) if total_supply else 0  # LP tokens are 18 decimals
            
            result = {
                'pair_address': pair_address,
                'reserve0': reserve0_formatted,
                'reserve1': reserve1_formatted,
                'reserve0_raw': reserve0,
                'reserve1_raw': reserve1,
                'total_supply': total_supply_formatted,
                'total_supply_raw': total_supply,
                'token0_address': token0_address,
                'token1_address': token1_address,
                'token0_decimals': token0_decimals,
                'token1_decimals': token1_decimals,
                'last_update_timestamp': timestamp
            }
            
            self.logger.debug(f"Retrieved reserves for pair {pair_address}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error getting Uniswap V2 reserves for {pair_address}: {e}")
            return None
    
    async def get_lp_token_balance(self, pair_address: str, wallet_address: str) -> Optional[float]:
        """
        Get LP token balance for a wallet.
        
        Args:
            pair_address: LP token contract address (same as pair address)
            wallet_address: Wallet address
            
        Returns:
            Optional[float]: LP token balance or None if error
        """
        try:
            if not self.web3_manager:
                return None
            
            # LP tokens are ERC20 tokens with 18 decimals
            balance_raw = await self.web3_manager.call_contract_function(
                pair_address,
                ERC20_ABI,
                'balanceOf',
                wallet_address
            )
            
            if balance_raw is None:
                return None
            
            # Convert to human readable (18 decimals)
            balance = balance_raw / (10 ** 18)
            
            self.logger.debug(f"LP token balance: {balance}")
            return balance
            
        except Exception as e:
            self.logger.error(f"Error getting LP token balance: {e}")
            return None
    
    async def get_token_info(self, token_address: str) -> Optional[Dict[str, Any]]:
        """
        Get token information (symbol, name, decimals).
        
        Args:
            token_address: Token contract address
            
        Returns:
            Optional[Dict]: Token info or None if error
        """
        try:
            if not self.web3_manager:
                return None
            
            symbol = await self.web3_manager.call_contract_function(
                token_address,
                ERC20_ABI,
                'symbol'
            )
            
            name = await self.web3_manager.call_contract_function(
                token_address,
                ERC20_ABI,
                'name'
            )
            
            decimals = await self.web3_manager.call_contract_function(
                token_address,
                ERC20_ABI,
                'decimals'
            )
            
            return {
                'address': token_address,
                'symbol': symbol,
                'name': name,
                'decimals': decimals
            }
            
        except Exception as e:
            self.logger.error(f"Error getting token info for {token_address}: {e}")
            return None


class ProtocolDataFetcher:
    """
    Fetches data from DeFi protocols (using DeFiLlama and other APIs).
    
    Based on the getProtocols() function from impermanent_loss.ipynb
    """
    
    def __init__(self):
        """Initialize Protocol Data Fetcher."""
        self.logger = logging.getLogger(__name__)
        self.defillama_base_url = "https://api.llama.fi"
    
    async def get_protocols(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get list of all DeFi protocols (from DeFiLlama).
        
        Based on getProtocols() function from notebook.
        
        Returns:
            Optional[List]: List of protocols or None if error
        """
        try:
            url = f"{self.defillama_base_url}/protocols"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    response.raise_for_status()
                    protocols = await response.json()
            
            self.logger.info(f"Retrieved {len(protocols)} protocols from DeFiLlama")
            return protocols
            
        except Exception as e:
            self.logger.error(f"Error fetching protocols: {e}")
            return None
    
    async def get_protocol_info(self, protocol_name: str) -> Optional[Dict[str, Any]]:
        """
        Get specific protocol information.
        
        Args:
            protocol_name: Protocol name (e.g., 'uniswap')
            
        Returns:
            Optional[Dict]: Protocol info or None if error
        """
        try:
            protocols = await self.get_protocols()
            
            if not protocols:
                return None
            
            # Find protocol by name (case insensitive)
            for protocol in protocols:
                if protocol.get('name', '').lower() == protocol_name.lower():
                    return protocol
            
            self.logger.warning(f"Protocol {protocol_name} not found")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting protocol info: {e}")
            return None
    
    async def get_pool_apy_estimate(self, protocol: str, pool_name: str) -> Optional[float]:
        """
        Get estimated APY for a pool (placeholder implementation).
        
        Args:
            protocol: Protocol name
            pool_name: Pool identifier
            
        Returns:
            Optional[float]: Estimated APY or None
        """
        try:
            # This is a placeholder - real implementation would depend on
            # specific APIs for each protocol
            
            self.logger.info(f"APY estimation not implemented for {protocol}/{pool_name}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting pool APY: {e}")
            return None


# Common contract addresses (Ethereum Mainnet)
COMMON_CONTRACTS = {
    'ethereum_mainnet': {
        'WETH': '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
        'USDC': '0xA0b86a33E6c21C64E0eb4ADa7B0b0094a7f6E44C',
        'USDT': '0xdAC17F958D2ee523a2206206994597C13D831ec7',
        'DAI': '0x6B175474E89094C44Da98b954EedeAC495271d0F',
        'WBTC': '0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599',
        'UNI': '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984',
        
        # Uniswap V2 pairs
        'WETH_USDC_V2': '0xB4e16d0168e52d35CaCD2b6464f00d6eB9002C6D',
        'WETH_USDT_V2': '0x0d4a11d5EEaaC28EC3F61d100daF4d40471f1852',
        'WETH_DAI_V2': '0xA478c2975Ab1Ea89e8196811F51A7B7Ade33eB11'
    },
    'ethereum_sepolia': {
        # Sepolia testnet addresses would go here
        # These are placeholders - real testnet contracts needed
        'WETH': '0x...',
        'USDC': '0x...'
    }
}

def get_contract_address(network: str, token_symbol: str) -> Optional[str]:
    """
    Get contract address for a token on specific network.
    
    Args:
        network: Network name
        token_symbol: Token symbol
        
    Returns:
        Optional[str]: Contract address or None
    """
    return COMMON_CONTRACTS.get(network, {}).get(token_symbol)
