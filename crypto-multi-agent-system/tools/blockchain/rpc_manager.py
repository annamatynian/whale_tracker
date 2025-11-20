"""
RPC Manager - Blockchain connectivity for OnChain analysis
Provides unified interface for multiple RPC providers and networks
"""

import os
import time
import logging
from typing import Dict, Optional, Union
from web3 import Web3
from web3.exceptions import Web3Exception, BlockNotFound, TransactionNotFound
from dotenv import load_dotenv

load_dotenv()

class RPCManager:
    """Manages RPC connections for multiple blockchain networks."""
    
    # Network configurations
    NETWORK_CONFIG = {
        "ethereum": {
            "rpc_env": "ETH_RPC_URL",
            "chain_id": 1,
            "name": "Ethereum Mainnet",
            "block_time": 12  # seconds
        },
        "base": {
            "rpc_env": "BASE_RPC_URL", 
            "chain_id": 8453,
            "name": "Base",
            "block_time": 2
        },
        "arbitrum": {
            "rpc_env": "ARBITRUM_RPC_URL",
            "chain_id": 42161,
            "name": "Arbitrum One", 
            "block_time": 1
        },
        "solana": {
            # Solana не поддерживается в этой версии (не EVM)
            "supported": False
        }
    }
    
    # ERC-20 token standard ABI (минимальный набор)
    ERC20_ABI = [
        {
            "constant": True,
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "type": "function"
        },
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

    def __init__(self, mock_mode: bool = False):
        """
        Initialize RPC Manager.
        
        Args:
            mock_mode: If True, return mock data instead of real RPC calls
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.mock_mode = mock_mode
        self.providers: Dict[str, Web3] = {}
        self.call_counts: Dict[str, int] = {}
        self.last_call_time: Dict[str, float] = {}
        
        if not mock_mode:
            self._initialize_providers()
        else:
            self.logger.info("🔧 RPC Manager инициализирован в MOCK режиме")

    def _initialize_providers(self):
        """Initialize Web3 providers for supported networks."""
        for network, config in self.NETWORK_CONFIG.items():
            if config.get("supported", True):  # По умолчанию поддерживается
                rpc_url = os.getenv(config["rpc_env"])
                
                if rpc_url:
                    try:
                        provider = Web3(Web3.HTTPProvider(rpc_url))
                        if provider.is_connected():
                            self.providers[network] = provider
                            self.call_counts[network] = 0
                            self.last_call_time[network] = 0
                            self.logger.info(f"✅ {config['name']} подключен")
                        else:
                            self.logger.warning(f"⚠️ Не удалось подключиться к {config['name']}")
                    except Exception as e:
                        self.logger.error(f"❌ Ошибка подключения к {config['name']}: {e}")
                else:
                    self.logger.warning(f"⚠️ RPC URL для {config['name']} не настроен в .env")
        
        if not self.providers:
            self.logger.warning("⚠️ Ни один RPC провайдер не настроен. Переключение в mock режим.")
            self.mock_mode = True

    def _rate_limit(self, network: str):
        """Simple rate limiting to avoid hitting RPC limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_call_time.get(network, 0)
        
        # Минимальная задержка между вызовами (100ms)
        min_interval = 0.1
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
        
        self.last_call_time[network] = time.time()
        self.call_counts[network] = self.call_counts.get(network, 0) + 1

    def get_provider(self, network: str) -> Optional[Web3]:
        """
        Get Web3 provider for specified network.
        
        Args:
            network: Network name (ethereum, base, arbitrum)
            
        Returns:
            Web3 provider or None if not available
        """
        if self.mock_mode:
            return None
            
        if network not in self.providers:
            self.logger.error(f"❌ Сеть '{network}' не поддерживается или не настроена")
            return None
            
        return self.providers[network]

    def get_transaction_count(self, network: str, address: str) -> int:
        """
        Get transaction count (nonce) for an address.
        
        Args:
            network: Network name
            address: Address to check
            
        Returns:
            Transaction count
        """
        if self.mock_mode:
            # Mock данные для тестирования
            mock_counts = {
                "0xE4cc1B66": 2,  # Стерильный деплоер
                "0x12345678": 50, # Обычный кошелек
                "0xabcdefgh": 1   # Очень новый кошелек
            }
            return mock_counts.get(address[:10], 5)
        
        provider = self.get_provider(network)
        if not provider:
            raise ValueError(f"RPC провайдер для '{network}' недоступен")
        
        try:
            self._rate_limit(network)
            
            # Проверяем что адрес корректный
            if not Web3.is_address(address):
                raise ValueError(f"Некорректный адрес: {address}")
            
            checksum_address = Web3.to_checksum_address(address)
            count = provider.eth.get_transaction_count(checksum_address)
            
            self.logger.debug(f"📊 {network}: {address} имеет {count} транзакций")
            return count
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения количества транзакций для {address}: {e}")
            raise

    def get_token_total_supply(self, network: str, token_address: str) -> int:
        """
        Get total supply of ERC-20 token.
        
        Args:
            network: Network name
            token_address: Token contract address
            
        Returns:
            Total supply in wei (raw units)
        """
        if self.mock_mode:
            # Mock данные
            return 1_000_000_000 * 10**18  # 1B tokens с 18 decimals
        
        provider = self.get_provider(network)
        if not provider:
            raise ValueError(f"RPC провайдер для '{network}' недоступен")
        
        try:
            self._rate_limit(network)
            
            checksum_address = Web3.to_checksum_address(token_address)
            contract = provider.eth.contract(address=checksum_address, abi=self.ERC20_ABI)
            
            total_supply = contract.functions.totalSupply().call()
            self.logger.debug(f"📊 {network}: {token_address} total supply = {total_supply}")
            
            return total_supply
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения total supply для {token_address}: {e}")
            raise

    def get_token_balance(self, network: str, token_address: str, holder_address: str) -> int:
        """
        Get token balance for specific holder.
        
        Args:
            network: Network name
            token_address: Token contract address
            holder_address: Address to check balance for
            
        Returns:
            Token balance in wei (raw units)
        """
        if self.mock_mode:
            # Mock данные - случайные балансы
            mock_balances = {
                "0x000000": 500_000_000 * 10**18,  # 500M tokens (локкер)
                "0x111111": 100_000_000 * 10**18,  # 100M tokens
                "0x222222": 50_000_000 * 10**18    # 50M tokens
            }
            return mock_balances.get(holder_address[:8], 1_000_000 * 10**18)
        
        provider = self.get_provider(network)
        if not provider:
            raise ValueError(f"RPC провайдер для '{network}' недоступен")
        
        try:
            self._rate_limit(network)
            
            token_checksum = Web3.to_checksum_address(token_address)
            holder_checksum = Web3.to_checksum_address(holder_address)
            
            contract = provider.eth.contract(address=token_checksum, abi=self.ERC20_ABI)
            balance = contract.functions.balanceOf(holder_checksum).call()
            
            self.logger.debug(f"📊 {network}: {holder_address} баланс {token_address} = {balance}")
            return balance
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения баланса токена: {e}")
            raise

    def is_contract(self, network: str, address: str) -> bool:
        """
        Check if address is a smart contract (vs EOA wallet).
        
        Args:
            network: Network name
            address: Address to check
            
        Returns:
            True if contract, False if EOA
        """
        if self.mock_mode:
            # Mock данные - простая эвристика по адресу
            contract_indicators = ["0x000000", "0x111111", "0xdead"]
            return any(indicator in address.lower() for indicator in contract_indicators)
        
        provider = self.get_provider(network)
        if not provider:
            raise ValueError(f"RPC провайдер для '{network}' недоступен")
        
        try:
            self._rate_limit(network)
            
            checksum_address = Web3.to_checksum_address(address)
            code = provider.eth.get_code(checksum_address)
            
            # Если есть код, то это контракт
            is_contract = len(code) > 0
            self.logger.debug(f"📊 {network}: {address} is {'contract' if is_contract else 'EOA'}")
            
            return is_contract
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка проверки типа адреса {address}: {e}")
            raise

    def get_network_stats(self) -> Dict[str, Dict]:
        """Get usage statistics for all networks."""
        stats = {}
        
        for network in self.NETWORK_CONFIG.keys():
            if self.NETWORK_CONFIG[network].get("supported", True):
                stats[network] = {
                    "connected": network in self.providers,
                    "api_calls": self.call_counts.get(network, 0),
                    "last_call": self.last_call_time.get(network, 0)
                }
        
        if self.mock_mode:
            stats["mock_mode"] = True
            
        return stats

    def health_check(self) -> Dict[str, bool]:
        """Check health of all RPC connections."""
        health = {}
        
        if self.mock_mode:
            return {"mock_mode": True, "status": "healthy"}
        
        for network, provider in self.providers.items():
            try:
                # Простая проверка - получить последний блок
                latest_block = provider.eth.block_number
                health[network] = latest_block > 0
            except Exception as e:
                self.logger.error(f"❌ Health check failed для {network}: {e}")
                health[network] = False
        
        return health
