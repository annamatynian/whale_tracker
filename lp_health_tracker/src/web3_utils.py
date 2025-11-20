"""
Web3 Utilities - Blockchain Interaction
=======================================

This module handles all Web3 interactions including:
- RPC connections
- Contract calls
- Gas price monitoring
- Network management

Author: Generated for DeFi-RAG Project
"""

import os
import logging
from typing import Optional, Dict, Any, List
from web3 import Web3
from web3.exceptions import Web3Exception
import aiohttp
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Web3Manager:
    """
    Manages Web3 connections and blockchain interactions.
    """
    
    def __init__(self):
        """Initialize Web3Manager."""
        self.logger = logging.getLogger(__name__)
        self.web3 = None #создаем пустое место куда после подключения запишем объект для связи с блокчейном
        self.network = os.getenv('DEFAULT_NETWORK', 'ethereum_mainnet')  #определяем сеть для подключения
        
        # Network configurations. Self.networks - словарь-"записная книжка" с конфигурациями сетей
        #Метод _get_rpc_url находит лучший URL-адрес для подключения к сети.
        self.networks = {
            'ethereum_mainnet': {
                'name': 'Ethereum Mainnet',
                'chain_id': 1,
                'rpc_url': self._get_rpc_url('ethereum_mainnet'),
                'explorer': 'https://etherscan.io'
            },
            'ethereum_sepolia': {
                'name': 'Ethereum Sepolia Testnet',
                'chain_id': 11155111,
                'rpc_url': self._get_rpc_url('ethereum_sepolia'),
                'explorer': 'https://sepolia.etherscan.io'
            },
            'polygon': {
                'name': 'Polygon',
                'chain_id': 137,
                'rpc_url': self._get_rpc_url('polygon'),
                'explorer': 'https://polygonscan.com'
            },
            'arbitrum': {
                'name': 'Arbitrum One',
                'chain_id': 42161,
                'rpc_url': self._get_rpc_url('arbitrum'),
                'explorer': 'https://arbiscan.io'
            }
        }
    
    def _get_rpc_url(self, network: str) -> str:
        """
        Get RPC URL for specified network.
        
        Args:
            network: Network name
            
        Returns:
            str: RPC URL
        """
        infura_key = os.getenv('INFURA_API_KEY')
        alchemy_key = os.getenv('ALCHEMY_API_KEY')
        ankr_key = os.getenv('ANKR_API_KEY')
        
        # Infura URLs
        if infura_key:
            infura_urls = {
                'ethereum_mainnet': f'https://mainnet.infura.io/v3/{infura_key}',
                'ethereum_sepolia': f'https://sepolia.infura.io/v3/{infura_key}',
                'polygon': f'https://polygon-mainnet.infura.io/v3/{infura_key}',
                'arbitrum': f'https://arbitrum-mainnet.infura.io/v3/{infura_key}'
            }
            if network in infura_urls:
                return infura_urls[network]
        
        # Alchemy URLs
        if alchemy_key:
            alchemy_urls = {
                'ethereum_mainnet': f'https://eth-mainnet.alchemyapi.io/v2/{alchemy_key}',
                'ethereum_sepolia': f'https://eth-sepolia.alchemyapi.io/v2/{alchemy_key}',
                'polygon': f'https://polygon-mainnet.alchemyapi.io/v2/{alchemy_key}',
                'arbitrum': f'https://arb-mainnet.alchemyapi.io/v2/{alchemy_key}'
            }
            if network in alchemy_urls:
                return alchemy_urls[network]
        
        # Ankr URLs (free public endpoints)
        ankr_urls = {
            'ethereum_mainnet': 'https://rpc.ankr.com/eth',
            'ethereum_sepolia': 'https://rpc.ankr.com/eth_sepolia',
            'polygon': 'https://rpc.ankr.com/polygon',
            'arbitrum': 'https://rpc.ankr.com/arbitrum'
        }
        
        return ankr_urls.get(network, ankr_urls['ethereum_sepolia'])
    
    async def initialize(self) -> bool:
        """
        Initialize Web3 connection.
        
        Returns:
            bool: True if connection successful
        """
        try:
            network_config = self.networks.get(self.network)
            if not network_config:
                self.logger.error(f"Unknown network: {self.network}")
                return False
            
            rpc_url = network_config['rpc_url']
            self.logger.info(f"Connecting to {network_config['name']} at {rpc_url}")
            
            # Initialize Web3 ключевой момент! 
            # Здесь мы создаём главный объект Web3 из библиотеки web3.py, 
            # передавая ему наш URL. 
            # Именно этот объект self.web3 и будет нашим "мостом" к блокчейну.
            self.web3 = Web3(Web3.HTTPProvider(rpc_url))
            
            # Test connection, проверяем удалось ли подключиться к блокчейну
            if not self.web3.is_connected():
                self.logger.error("Failed to connect to Web3 provider")
                return False
            
            # Verify network
            chain_id = self.web3.eth.chain_id  #Мы спрашиваем у сети, какой у неё ID.
            expected_chain_id = network_config['chain_id']
            
            if chain_id != expected_chain_id:
                self.logger.error(
                    f"Chain ID mismatch. Expected {expected_chain_id}, got {chain_id}"
                )
                return False
            
            self.logger.info(f"Successfully connected to {network_config['name']} (Chain ID: {chain_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing Web3: {e}")
            return False
    
    async def get_current_gas_price(self) -> Optional[int]:
        """
        Get current gas price.
        
        Returns:
            Optional[int]: Gas price in Wei, None if error
        """
        try:
            if not self.web3:
                return None
            
            gas_price = self.web3.eth.gas_price
            #ы обращаемся к нашему объекту подключения self.web3, 
            # заходим в его модуль для работы с Ethereum (eth) и запрашиваем свойство gas_price. 
            # В этот момент ваша программа отправляет запрос в блокчейн и получает в ответ 
            # текущую цену газа. Цена возвращается в самой маленькой единице, называемой Wei.
            self.logger.debug(f"Current gas price: {Web3.from_wei(gas_price, 'gwei')} Gwei")
            #Эта строка не обязательна для работы, она нужна для отладки. 
            # Она записывает в журнал цену, которую мы получили, но переводит её из Wei 
            # в более читаемый формат Gwei (это как перевести копейки в рубли, чтобы было понятнее).

            return gas_price
            
        except Exception as e:
            self.logger.error(f"Error getting gas price: {e}")
            return None
    
    async def get_eth_balance(self, address: str) -> Optional[float]:
        """
        Get ETH balance for address.
        
        Args:
            address: Wallet address
            
        Returns:
            Optional[float]: Balance in ETH, None if error
        """
        try:
            if not self.web3:
                return None
            
            # Convert to checksum address #приводим адрес к стандартному формату
            address = Web3.to_checksum_address(address)
            
            # Get balance in Wei
            balance_wei = self.web3.eth.get_balance(address)
            
            # Convert to ETH для удобства чтения
            balance_eth = Web3.from_wei(balance_wei, 'ether')
            
            return float(balance_eth)
            
        except Exception as e:
            self.logger.error(f"Error getting ETH balance for {address}: {e}")
            return None
    
    async def get_erc20_balance(self, token_address: str, wallet_address: str) -> Optional[float]:
        """
        Эта функция сложнее: она проверяет баланс не основной монеты, 
        а любого стандартного токена (ERC20), например USDC, USDT или UNI. 
        Для этого ей нужно взаимодействовать со смарт-контрактом этого токена.

        Get ERC20 token balance.
        
        Args:
            token_address: Token contract address
            wallet_address: Wallet address
            
        Returns:
            Optional[float]: Token balance, None if error
        """
        try:
            if not self.web3:
                return None
            """
            
            # Standard ERC20 ABI (balanceOf and decimals)
            #определена "инструкция" (ABI) для стандартного токена. 
            # Она говорит программе, какие функции есть у контракта (например, balanceOf и decimals).

            #constant: True: Указывает, что эта функция не изменяет состояние блокчейна. 
            Она только читает данные, поэтому для её вызова не требуется платить за газ 
            (транзакционную комиссию).

            "name": "balanceOf": Имя функции

            "outputs": [...]: Описывает, что функция возвращает. 
            В данном случае это одно значение с именем balance и типом uint256 (256-битное целое число без знака), которое представляет баланс токенов.
            """
            erc20_abi = [
                {
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "type": "function"
                }
            ]
            
            # Convert addresses to checksum
            token_address = Web3.to_checksum_address(token_address)
            wallet_address = Web3.to_checksum_address(wallet_address)
            
            # Create contract instance # Создаём объект контракта, с которым будем общаться
            contract = self.web3.eth.contract(
                address=token_address,
                abi=erc20_abi
            )
            
            # Get balance and decimals
            #contract.functions.balanceOf(wallet_address).call(): 
            # Вызывается функция balanceOf из контракта. 
            # Мы передаём ей адрес кошелька и получаем в ответ баланс токена 
            # в его минимальных единицах.
            balance = contract.functions.balanceOf(wallet_address).call()
            decimals = contract.functions.decimals().call()
            
            # Convert to human readable format
            return balance / (10 ** decimals)
            
        except Exception as e:
            self.logger.error(f"Error getting ERC20 balance: {e}")
            return None
        
    
    async def call_contract_function(
        self, 
        contract_address: str, 
        abi: List[Dict[str, Any]], 
        function_name: str, 
        *args
    ) -> Optional[Any]:
        """
        Call a contract function.
        
        Args:
            contract_address: Contract address
            abi: Contract ABI
            function_name: Function name to call
            *args: Function arguments
            
        Returns:
            Optional[Any]: Function result, None if error
        """
        try:
            if not self.web3:
                return None
            
            # Convert address to checksum
            contract_address = Web3.to_checksum_address(contract_address)
            
            # Create contract instance
            contract = self.web3.eth.contract(
                address=contract_address,
                abi=abi
            )
            
            # Get function
            function = getattr(contract.functions, function_name)
            
            # Call function
            result = function(*args).call()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error calling contract function {function_name}: {e}")
            return None
    
    def get_transaction_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction receipt.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Optional[Dict]: Transaction receipt, None if error
        """
        try:
            if not self.web3:
                return None
            
            receipt = self.web3.eth.get_transaction_receipt(tx_hash)
            return dict(receipt)
            
        except Exception as e:
            self.logger.error(f"Error getting transaction receipt: {e}")
            return None
    
    def is_valid_address(self, address: str) -> bool:
        """
        Check if address is valid Ethereum address.
        
        Args:
            address: Address to check
            
        Returns:
            bool: True if valid
        """
        try:
            Web3.to_checksum_address(address)
            return True
        except:
            return False
    
    def get_network_info(self) -> Dict[str, Any]:
        """
        Get current network information.
        
        Returns:
            Dict: Network information
        """
        return self.networks.get(self.network, {})


# Uniswap V2 Pair Contract ABI (minimal)
UNISWAP_V2_PAIR_ABI = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [
            {"name": "_reserve0", "type": "uint112"},
            {"name": "_reserve1", "type": "uint112"},
            {"name": "_blockTimestampLast", "type": "uint32"}
        ],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token0",
        "outputs": [{"name": "", "type": "address"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "token1",
        "outputs": [{"name": "", "type": "address"}],
        "type": "function"
    }
]

# ERC20 Token ABI (minimal)
ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function"
    }
]
