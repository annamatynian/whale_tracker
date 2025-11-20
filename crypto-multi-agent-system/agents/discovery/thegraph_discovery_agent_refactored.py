"""
TheGraph Discovery Agent - Часть 1 РЕФАКТОРИНГ: Расширяемая архитектура
Абстрактная, легко расширяемая система для множественных субграфов и типов DEX

Key improvements:
- Список субграфов вместо жестко закодированных переменных  
- Абстракции для легкого добавления новых типов DEX
- Конфигурация через .env с автодискавери

Author: Extensible architecture for production scalability
Version: 1.1 - Refactored (Extensible)
"""

import os
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from pydantic import BaseModel, Field, validator
from tenacity import retry, stop_after_attempt, wait_fixed
from abc import ABC, abstractmethod
from enum import Enum
import requests

# Import base model
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.discovery.discovery_models import TokenDiscoveryReport


class DEXType(Enum):
    """Supported DEX types with different schemas."""
    UNISWAP_V2 = "uniswap_v2"      # pairs schema
    UNISWAP_V3 = "uniswap_v3"      # pools schema  
    SUSHISWAP = "sushiswap"        # pairs schema (V2 fork)
    PANCAKESWAP_V2 = "pancakeswap_v2"  # pairs schema (V2 fork)
    CURVE = "curve"                 # different schema
    BALANCER = "balancer"          # different schema


class Blockchain(Enum):
    """Supported blockchains."""
    ETHEREUM = "ethereum"
    BSC = "bsc"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    AVALANCHE = "avalanche"
    FANTOM = "fantom"


class SubgraphConfig(BaseModel):
    """Configuration for individual subgraph source."""
    
    # Identification
    name: str = Field(..., description="Human-readable DEX name")
    subgraph_id: str = Field(..., description="The Graph subgraph ID")
    dex_type: DEXType = Field(..., description="Type of DEX (determines schema)")
    blockchain: Blockchain = Field(..., description="Blockchain network")
    
    # Filtering parameters
    liquidity_threshold_usd: str = Field(..., description="Minimum liquidity in USD")
    
    # Configuration
    active: bool = Field(default=True, description="Whether to use this subgraph")
    priority: int = Field(default=1, description="Processing priority (1=highest)")
    max_retries: int = Field(default=3, description="Max retries for failed requests")
    
    # Optional metadata
    description: Optional[str] = Field(None, description="Optional description")
    added_date: datetime = Field(default_factory=datetime.now)


class AbstractDEXAdapter(ABC):
    """Abstract base class for different DEX types."""
    
    @abstractmethod
    def build_pairs_query(self, liquidity_threshold: str) -> str:
        """Build GraphQL query for this DEX type."""
        pass
    
    @abstractmethod
    def parse_pair_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse DEX-specific pair data into standardized format."""
        pass
    
    @abstractmethod
    def get_schema_fields(self) -> List[str]:
        """Get required fields for this DEX type."""
        pass


class UniswapV2Adapter(AbstractDEXAdapter):
    """Adapter for Uniswap V2 and its forks (SushiSwap, PancakeSwap V2)."""
    
    def build_pairs_query(self, liquidity_threshold: str) -> str:
        """Build pairs query for V2-style DEX."""
        return f'''
        query($start: BigInt!, $end: BigInt!, $first: Int!, $skip: Int!) {{
          pairs(
            where: {{ 
              createdAtTimestamp_gte: $start,
              createdAtTimestamp_lte: $end,
              reserveUSD_gte: "{liquidity_threshold}"
            }}
            first: $first
            skip: $skip
            orderBy: createdAtTimestamp
            orderDirection: asc
          ) {{
            id
            token0 {{
              id
              symbol
              name
            }}
            token1 {{
              id
              symbol  
              name
            }}
            createdAtTimestamp
            reserveUSD
            volumeUSD
            txCount
          }}
        }}
        '''
    
    def parse_pair_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse V2 pair data into standardized format."""
        return {
            'pair_address': raw_data.get('id', ''),
            'base_token_address': raw_data.get('token0', {}).get('id', ''),
            'base_token_symbol': raw_data.get('token0', {}).get('symbol', ''),
            'base_token_name': raw_data.get('token0', {}).get('name', ''),
            'quote_token_address': raw_data.get('token1', {}).get('id', ''),
            'quote_token_symbol': raw_data.get('token1', {}).get('symbol', ''),
            'quote_token_name': raw_data.get('token1', {}).get('name', ''),
            'liquidity_usd': float(raw_data.get('reserveUSD', 0)),
            'volume_usd': float(raw_data.get('volumeUSD', 0)),
            'created_at_timestamp': int(raw_data.get('createdAtTimestamp', 0)),
            'tx_count': int(raw_data.get('txCount', 0))
        }
    
    def get_schema_fields(self) -> List[str]:
        """Get required fields for V2 pairs."""
        return ['id', 'token0', 'token1', 'createdAtTimestamp', 'reserveUSD', 'volumeUSD', 'txCount']


class UniswapV3Adapter(AbstractDEXAdapter):
    """Adapter for Uniswap V3 (pools instead of pairs)."""
    
    def build_pairs_query(self, liquidity_threshold: str) -> str:
        """Build pools query for V3-style DEX."""
        return f'''
        query($start: BigInt!, $end: BigInt!, $first: Int!, $skip: Int!) {{
          pools(
            where: {{ 
              createdAtTimestamp_gte: $start,
              createdAtTimestamp_lte: $end,
              totalValueLockedUSD_gte: "{liquidity_threshold}"
            }}
            first: $first
            skip: $skip
            orderBy: createdAtTimestamp
            orderDirection: asc
          ) {{
            id
            token0 {{
              id
              symbol
              name
            }}
            token1 {{
              id
              symbol  
              name
            }}
            createdAtTimestamp
            totalValueLockedUSD
            volumeUSD
            feeTier
            txCount
          }}
        }}
        '''
    
    def parse_pair_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse V3 pool data into standardized format."""
        return {
            'pair_address': raw_data.get('id', ''),
            'base_token_address': raw_data.get('token0', {}).get('id', ''),
            'base_token_symbol': raw_data.get('token0', {}).get('symbol', ''),
            'base_token_name': raw_data.get('token0', {}).get('name', ''),
            'quote_token_address': raw_data.get('token1', {}).get('id', ''),
            'quote_token_symbol': raw_data.get('token1', {}).get('symbol', ''),
            'quote_token_name': raw_data.get('token1', {}).get('name', ''),
            'liquidity_usd': float(raw_data.get('totalValueLockedUSD', 0)),
            'volume_usd': float(raw_data.get('volumeUSD', 0)),
            'created_at_timestamp': int(raw_data.get('createdAtTimestamp', 0)),
            'fee_tier': int(raw_data.get('feeTier', 0)),
            'tx_count': int(raw_data.get('txCount', 0))
        }
    
    def get_schema_fields(self) -> List[str]:
        """Get required fields for V3 pools."""
        return ['id', 'token0', 'token1', 'createdAtTimestamp', 'totalValueLockedUSD', 'volumeUSD', 'feeTier', 'txCount']


class TheGraphConfig(BaseModel):
    """Configuration model for The Graph discovery settings."""
    
    # API Configuration
    graph_api_key: str = Field(..., description="The Graph API Gateway key")
    graph_gateway_base: str = Field(
        default="https://gateway.thegraph.com/api",
        description="The Graph Gateway base URL"
    )
    
    # Subgraph Sources - НОВАЯ РАСШИРЯЕМАЯ АРХИТЕКТУРА
    subgraphs: List[SubgraphConfig] = Field(
        default_factory=list, 
        description="List of configured subgraph sources"
    )
    
    # Time Range Configuration - ОБНОВЛЕНО ПОД СТРАТЕГИЮ "ПОДТВЕРЖДЕНИЕ ОБЪЕМОВ"
    min_age_days: int = Field(default=30, description="Minimum token age in days - начинаем с месяца для стабильных метрик")
    max_age_days: int = Field(default=90, description="Maximum token age in days - до 3 месяцев для зрелых токенов") 
    slice_duration_days: int = Field(default=10, description="Duration of each time slice - увеличено для меньшего количества запросов")
    
    # Pagination Settings
    max_results_per_query: int = Field(default=1000, description="GraphQL query limit")
    pagination_delay_sec: float = Field(default=0.5, description="Delay between requests")
    
    @validator('subgraphs')
    def validate_at_least_one_active(cls, v):
        """Ensure at least one active subgraph is configured."""
        active_subgraphs = [s for s in v if s.active]
        if not active_subgraphs:
            raise ValueError("At least one active subgraph must be configured")
        return v


def create_dex_adapter(dex_type: DEXType) -> AbstractDEXAdapter:
    """Factory function to create appropriate DEX adapter."""
    adapters = {
        DEXType.UNISWAP_V2: UniswapV2Adapter,
        DEXType.SUSHISWAP: UniswapV2Adapter,        # Fork of V2
        DEXType.PANCAKESWAP_V2: UniswapV2Adapter,   # Fork of V2
        DEXType.UNISWAP_V3: UniswapV3Adapter,
        # Add more adapters as needed
    }
    
    adapter_class = adapters.get(dex_type)
    if not adapter_class:
        raise ValueError(f"No adapter available for DEX type: {dex_type}")
    
    return adapter_class()


class TheGraphDiscoveryAgent:
    """
    The Graph-based discovery agent with extensible architecture.
    
    Key improvements:
    - Supports multiple subgraphs through configuration
    - Abstract adapters for different DEX types
    - Easy to add new blockchains and DEX protocols
    - Production-ready error handling and logging
    """
    
    def __init__(self, config: Optional[TheGraphConfig] = None):
        """Initialize The Graph Discovery Agent."""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Load configuration
        self.config = config if config else self._load_config_from_env()
        
        # Validate configuration
        self._validate_config()
        
        # Create DEX adapters for each subgraph
        self.adapters = {}
        for subgraph in self.config.subgraphs:
            if subgraph.active:
                self.adapters[subgraph.name] = create_dex_adapter(subgraph.dex_type)
        
        # Stats tracking
        self.stats = {
            "total_pairs_discovered": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "discovery_start_time": None,
            "discovery_end_time": None,
            "subgraph_stats": {}
        }
        
        active_count = len([s for s in self.config.subgraphs if s.active])
        self.logger.info(f"TheGraphDiscoveryAgent initialized with {active_count} active subgraphs")
    
    def _load_config_from_env(self) -> TheGraphConfig:
        """Load configuration from environment variables with auto-discovery."""
        from dotenv import load_dotenv
        load_dotenv()
        
        # Base configuration
        config = TheGraphConfig(
            graph_api_key=os.getenv("GRAPH_API_KEY", "")
        )
        
        # Auto-discover subgraphs from environment
        subgraphs = []
        
        # Known subgraph patterns
        subgraph_patterns = [
            {
                "env_var": "UNISWAP_V2_ID",
                "name": "Uniswap V2",
                "dex_type": DEXType.UNISWAP_V2,
                "blockchain": Blockchain.ETHEREUM,
                "threshold": "1000"
            },
            {
                "env_var": "SUSHISWAP_ID", 
                "name": "SushiSwap",
                "dex_type": DEXType.SUSHISWAP,
                "blockchain": Blockchain.ETHEREUM,
                "threshold": "1"
            },
            # ВРЕМЕННО ОТКЛЮЧЕН: PancakeSwap V2 из-за GraphQL ошибки "Type Query has no field pairs"
            # {
            #     "env_var": "PANCAKESWAP_V2_ID",
            #     "name": "PancakeSwap V2", 
            #     "dex_type": DEXType.PANCAKESWAP_V2,
            #     "blockchain": Blockchain.BSC,
            #     "threshold": "100"
            # },
            {
                "env_var": "UNISWAP_V3_ID",
                "name": "Uniswap V3",
                "dex_type": DEXType.UNISWAP_V3, 
                "blockchain": Blockchain.ETHEREUM,
                "threshold": "1000"
            }
        ]
        
        # Add configured subgraphs
        for pattern in subgraph_patterns:
            subgraph_id = os.getenv(pattern["env_var"])
            if subgraph_id:
                subgraph = SubgraphConfig(
                    name=pattern["name"],
                    subgraph_id=subgraph_id,
                    dex_type=pattern["dex_type"],
                    blockchain=pattern["blockchain"],
                    liquidity_threshold_usd=pattern["threshold"]
                )
                subgraphs.append(subgraph)
        
        config.subgraphs = subgraphs
        return config
    
    def _validate_config(self) -> None:
        """Validate that required configuration is present."""
        if not self.config.graph_api_key:
            raise ValueError("GRAPH_API_KEY is required in environment variables")
        
        active_subgraphs = [s for s in self.config.subgraphs if s.active]
        if not active_subgraphs:
            raise ValueError("At least one active subgraph must be configured")
        
        if self.config.min_age_days >= self.config.max_age_days:
            raise ValueError("min_age_days must be less than max_age_days")
    
    def _build_subgraph_url(self, subgraph_id: str) -> str:
        """Build complete subgraph URL from ID."""
        return f"{self.config.graph_gateway_base}/{self.config.graph_api_key}/subgraphs/id/{subgraph_id}"
    
    def get_active_subgraphs(self) -> List[SubgraphConfig]:
        """Get list of active subgraphs ordered by priority."""
        active = [s for s in self.config.subgraphs if s.active]
        return sorted(active, key=lambda x: x.priority)
    
    def get_discovery_stats(self) -> Dict[str, Any]:
        """Get current discovery statistics."""
        stats = self.stats.copy()
        
        if stats["discovery_start_time"] and stats["discovery_end_time"]:
            duration = (stats["discovery_end_time"] - stats["discovery_start_time"]).total_seconds()
            stats["total_duration_seconds"] = duration
            
            if duration > 0:
                stats["pairs_per_second"] = stats["total_pairs_discovered"] / duration
        
        return stats
    
    def add_subgraph(self, subgraph: SubgraphConfig) -> None:
        """Add new subgraph configuration dynamically."""
        self.config.subgraphs.append(subgraph)
        
        if subgraph.active:
            self.adapters[subgraph.name] = create_dex_adapter(subgraph.dex_type)
        
        self.logger.info(f"Added subgraph: {subgraph.name} ({subgraph.blockchain.value})")
    
    def list_supported_dex_types(self) -> List[str]:
        """List all supported DEX types."""
        return [dex_type.value for dex_type in DEXType]
    
    def reset_stats(self) -> None:
        """Reset discovery statistics."""
        self.stats = {
            "total_pairs_discovered": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "discovery_start_time": None,
            "discovery_end_time": None,
            "subgraph_stats": {}
        }
        
        self.logger.info("Discovery statistics reset")


# === ЧАСТЬ 1 РЕФАКТОРИНГ ЗАВЕРШЕН ===
# Новые возможности:
# - Легко добавлять новые субграфы через .env
# - Поддержка разных типов DEX (V2, V3, Curve, etc.)
# - Абстракции для будущих расширений
# - Динамическое добавление источников

if __name__ == "__main__":
    # Test refactored Part 1
    try:
        agent = TheGraphDiscoveryAgent()
        active_subgraphs = agent.get_active_subgraphs()
        
        print(f"✅ Part 1 Refactored successful: {len(active_subgraphs)} active subgraphs")
        
        for subgraph in active_subgraphs:
            print(f"   - {subgraph.name} ({subgraph.dex_type.value}) on {subgraph.blockchain.value}")
            print(f"     Threshold: ${subgraph.liquidity_threshold_usd}")
        
        print(f"\nSupported DEX types: {agent.list_supported_dex_types()}")
        print(f"Config: {agent.config.min_age_days}-{agent.config.max_age_days} days")
        
    except Exception as e:
        print(f"❌ Part 1 Refactored error: {e}")
