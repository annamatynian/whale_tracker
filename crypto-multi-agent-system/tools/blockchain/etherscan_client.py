"""
Etherscan Client - API integration for token holder data
Provides access to token holder lists and contract creation info
"""

import os
import time
import asyncio
import aiohttp
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class TokenHolder:
    """Represents a token holder with balance information."""
    address: str
    balance: str          # Raw balance (wei)
    percentage: float     # Percentage of total supply
    is_contract: Optional[bool] = None  # Will be determined by RPC

@dataclass
class ContractCreation:
    """Contract creation transaction information."""
    creator_address: str
    creation_tx_hash: str
    creation_block: int
    creation_timestamp: int

class EtherscanClient:
    """Client for Etherscan-like APIs across different networks."""
    
    # API endpoints for different networks
    NETWORK_APIS = {
        "ethereum": {
            "base_url": "https://api.etherscan.io/api",
            "api_key_env": "ETHERSCAN_API_KEY"
        },
        "base": {
            "base_url": "https://api.basescan.org/api", 
            "api_key_env": "BASE_ETHERSCAN_API_KEY"  # ИСПРАВЛЕНО: совпадает с .env
        },
        "arbitrum": {
            "base_url": "https://api.arbiscan.io/api",
            "api_key_env": "ARBITRUM_ETHERSCAN_API_KEY"  # ИСПРАВЛЕНО: совпадает с .env
        },
        "polygon": {
            "base_url": "https://api.polygonscan.com/api",
            "api_key_env": "POLYGON_ETHERSCAN_API_KEY"  # ИСПРАВЛЕНО: совпадает с .env
        }
    }

    def __init__(self, mock_mode: bool = False):
        """
        Initialize Etherscan client.
        
        Args:
            mock_mode: If True, return mock data instead of real API calls
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.mock_mode = mock_mode
        self.api_keys = {}
        self.call_counts = {}
        self.last_call_time = {}
        
        if not mock_mode:
            self._load_api_keys()
        else:
            self.logger.info("🔧 Etherscan Client инициализирован в MOCK режиме")

    def _load_api_keys(self):
        """Load API keys from environment variables."""
        for network, config in self.NETWORK_APIS.items():
            api_key = os.getenv(config["api_key_env"])
            if api_key:
                self.api_keys[network] = api_key
                self.call_counts[network] = 0
                self.last_call_time[network] = 0
                self.logger.info(f"✅ {network.title()} API ключ загружен")
            else:
                self.logger.warning(f"⚠️ API ключ для {network} не найден в .env")

    def _rate_limit(self, network: str):
        """
        Rate limiting for Etherscan APIs.
        Free tier: 5 calls/second, 100,000 calls/day
        """
        current_time = time.time()
        time_since_last = current_time - self.last_call_time.get(network, 0)
        
        # Минимальная задержка 200ms между вызовами (5 calls/sec)
        min_interval = 0.2
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
        
        self.last_call_time[network] = time.time()
        self.call_counts[network] = self.call_counts.get(network, 0) + 1

    async def _make_request(self, network: str, params: Dict) -> Dict:
        """
        Make async HTTP request to Etherscan API.
        
        Args:
            network: Network name
            params: API parameters
            
        Returns:
            API response as dict
        """
        if self.mock_mode:
            return self._get_mock_response(params)
        
        if network not in self.api_keys:
            raise ValueError(f"API ключ для {network} не настроен")
        
        config = self.NETWORK_APIS[network]
        params["apikey"] = self.api_keys[network]
        
        self._rate_limit(network)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(config["base_url"], params=params) as response:
                    if response.status != 200:
                        raise Exception(f"HTTP {response.status}: {await response.text()}")
                    
                    data = await response.json()
                    
                    if data.get("status") != "1":
                        error_msg = data.get("message", "Unknown error")
                        if "No transactions found" in error_msg:
                            return {"status": "1", "result": []}
                        raise Exception(f"API Error: {error_msg}")
                    
                    return data
                    
        except Exception as e:
            self.logger.error(f"❌ Ошибка API запроса к {network}: {e}")
            raise

    def _get_mock_response(self, params: Dict) -> Dict:
        """Generate mock response for testing."""
        action = params.get("action", "")
        
        if action == "tokenholderslist":
            # Mock список держателей токена
            return {
                "status": "1",
                "result": [
                    {
                        "TokenHolderAddress": "0x000000000000000000000000000000000000dead",
                        "TokenHolderQuantity": "500000000000000000000000000",  # 500M tokens
                        "Percentage": "50.00"
                    },
                    {
                        "TokenHolderAddress": "0x663A5C229c09b049E36dCc11a9B0d4a8Eb9db214",  # Unicrypt
                        "TokenHolderQuantity": "300000000000000000000000000",  # 300M tokens
                        "Percentage": "30.00"
                    },
                    {
                        "TokenHolderAddress": "0x1234567890123456789012345678901234567890",  # EOA
                        "TokenHolderQuantity": "100000000000000000000000000",  # 100M tokens
                        "Percentage": "10.00"
                    },
                    {
                        "TokenHolderAddress": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",  # EOA
                        "TokenHolderQuantity": "50000000000000000000000000",   # 50M tokens
                        "Percentage": "5.00"
                    }
                ]
            }
        
        elif action == "getcontractcreation":
            # Mock данные о создании контракта
            return {
                "status": "1", 
                "result": [{
                    "contractAddress": params.get("contractaddresses", ""),
                    "contractCreator": "0xE4cc1B66123456789012345678901234567890",
                    "txHash": "0x123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef01"
                }]
            }
        
        return {"status": "1", "result": []}

    async def get_token_holders(self, network: str, token_address: str, 
                               limit: int = 50) -> List[TokenHolder]:
        """
        Get top token holders for specified token.
        
        Args:
            network: Network name (ethereum, base, etc.)
            token_address: Token contract address
            limit: Maximum number of holders to return (max 50 for free tier)
            
        Returns:
            List of TokenHolder objects
        """
        try:
            params = {
                "module": "token",
                "action": "tokenholderslist", 
                "contractaddress": token_address,
                "page": 1,
                "offset": min(limit, 50)  # Etherscan limit
            }
            
            response = await self._make_request(network, params)
            holders = []
            
            for item in response.get("result", []):
                holder = TokenHolder(
                    address=item.get("TokenHolderAddress", ""),
                    balance=item.get("TokenHolderQuantity", "0"),
                    percentage=float(item.get("Percentage", "0"))
                )
                holders.append(holder)
            
            self.logger.info(f"📊 {network}: Получено {len(holders)} держателей для {token_address}")
            return holders
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения держателей токена {token_address}: {e}")
            # Возвращаем пустой список вместо исключения для продолжения анализа
            return []

    async def get_contract_creation(self, network: str, 
                                  contract_address: str) -> Optional[ContractCreation]:
        """
        Get contract creation information.
        
        Args:
            network: Network name
            contract_address: Contract address
            
        Returns:
            ContractCreation object or None if not found
        """
        try:
            params = {
                "module": "contract",
                "action": "getcontractcreation",
                "contractaddresses": contract_address
            }
            
            response = await self._make_request(network, params)
            result = response.get("result", [])
            
            if not result:
                self.logger.warning(f"⚠️ Информация о создании контракта {contract_address} не найдена")
                return None
            
            creation_data = result[0]
            creation = ContractCreation(
                creator_address=creation_data.get("contractCreator", ""),
                creation_tx_hash=creation_data.get("txHash", ""),
                creation_block=int(creation_data.get("creationBlock", 0)),
                creation_timestamp=int(creation_data.get("creationTimestamp", 0))
            )
            
            self.logger.info(f"📊 {network}: Контракт {contract_address} создан {creation.creator_address}")
            return creation
            
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения информации о создании контракта: {e}")
            return None

    def get_api_stats(self) -> Dict[str, Dict]:
        """Get API usage statistics."""
        stats = {}
        
        for network in self.NETWORK_APIS.keys():
            stats[network] = {
                "api_key_configured": network in self.api_keys,
                "api_calls": self.call_counts.get(network, 0),
                "last_call": self.last_call_time.get(network, 0)
            }
        
        if self.mock_mode:
            stats["mock_mode"] = True
            
        return stats

    # Utility methods for known addresses
    
    KNOWN_DEAD_ADDRESSES = {
        "0x000000000000000000000000000000000000dead",
        "0x0000000000000000000000000000000000000000",
        "0x000000000000000000000000000000000000dEaD"  # Alternative capitalization
    }
    
    def is_dead_address(self, address: str) -> bool:
        """Check if address is a known 'dead' address."""
        return address.lower() in {addr.lower() for addr in self.KNOWN_DEAD_ADDRESSES}

    def classify_holder_type(self, holder: TokenHolder) -> str:
        """
        Classify holder type based on address patterns.
        
        Returns:
            "DEAD_ADDRESS", "LIKELY_EXCHANGE", "UNKNOWN_CONTRACT", "EOA", "UNKNOWN"
        """
        address = holder.address.lower()
        
        # Check for dead addresses
        if self.is_dead_address(address):
            return "DEAD_ADDRESS"
        
        # Simple heuristics for exchange detection
        # (В реальной системе должна быть более полная база)
        exchange_patterns = [
            "binance", "coinbase", "kraken", "okex", "huobi", 
            "bitfinex", "kucoin", "gate", "bybit"
        ]
        
        if any(pattern in address for pattern in exchange_patterns):
            return "LIKELY_EXCHANGE"
        
        # Если определен как контракт через RPC
        if holder.is_contract is True:
            return "UNKNOWN_CONTRACT"
        elif holder.is_contract is False:
            return "EOA"
        
        return "UNKNOWN"
