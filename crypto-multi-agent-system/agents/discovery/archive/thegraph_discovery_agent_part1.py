"""
TheGraph Discovery Agent - Часть 1: Базовая структура класса
Заменяет DexScreener на The Graph для исторического поиска токенов
Использует temporal slicing + pagination для сбора ВСЕХ токенов возрастом 45-75 дней

Author: Production-ready integration of proven prototype logic
Version: 1.0 - Part 1 (Base Structure)
"""

import os
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_fixed
import requests

# Import from current directory structure
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.discovery.base_discovery_agent import TokenDiscoveryReport


class TheGraphConfig(BaseModel):
    """Configuration model for The Graph discovery settings."""
    
    # API Configuration
    graph_api_key: str = Field(..., description="The Graph API Gateway key")
    graph_gateway_base: str = Field(
        default="https://gateway-arbitrum.network.thegraph.com/api",
        description="The Graph Gateway base URL"
    )
    
    # Subgraph IDs - these should be in .env
    uniswap_v2_id: Optional[str] = Field(None, description="Uniswap V2 subgraph ID")
    sushiswap_id: Optional[str] = Field(None, description="SushiSwap subgraph ID")
    
    # Time Range Configuration (replaces DexScreener approach)
    min_age_days: int = Field(default=45, description="Minimum token age in days")
    max_age_days: int = Field(default=75, description="Maximum token age in days")
    slice_duration_days: int = Field(default=5, description="Duration of each time slice")
    
    # Pagination Settings
    max_results_per_query: int = Field(default=1000, description="GraphQL query limit")
    pagination_delay_sec: float = Field(default=0.5, description="Delay between requests")
    
    # DEX-specific Thresholds (adaptive filtering based on diagnostic results)
    liquidity_thresholds: Dict[str, str] = Field(
        default={
            "uniswap_v2": "1000",    # Higher threshold - Uniswap has more liquidity
            "sushiswap": "1"         # Lower threshold - needed for SushiSwap
        },
        description="Liquidity thresholds by DEX in USD"
    )


class TheGraphSubgraphConfig(BaseModel):
    """Configuration for individual subgraph source."""
    
    subgraph_id: str = Field(..., description="The Graph subgraph ID")
    name: str = Field(..., description="Human-readable DEX name")
    chain: str = Field(..., description="Blockchain name")
    liquidity_threshold: str = Field(..., description="Minimum liquidity in USD")
    active: bool = Field(default=True, description="Whether to use this subgraph")


class TheGraphDiscoveryAgent:
    """
    The Graph-based discovery agent that replaces DexScreener.
    
    Key improvements over DexScreener:
    - Collects ALL historical tokens (not limited to ~30)
    - Uses temporal slicing for reliable data collection
    - Implements pagination to ensure completeness
    - Adaptive filtering per DEX based on diagnostic results
    - Production-ready error handling and logging
    """
    
    def __init__(self, config: Optional[TheGraphConfig] = None):
        """Initialize The Graph Discovery Agent."""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Load configuration
        self.config = config if config else self._load_config_from_env()
        
        # Validate configuration
        self._validate_config()
        
        # Build subgraph configurations
        self.subgraphs = self._build_subgraph_configs()
        
        # Stats tracking
        self.stats = {
            "total_pairs_discovered": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "discovery_start_time": None,
            "discovery_end_time": None
        }
        
        self.logger.info(f"TheGraphDiscoveryAgent initialized with {len(self.subgraphs)} active subgraphs")
    
    def _load_config_from_env(self) -> TheGraphConfig:
        """Load configuration from environment variables."""
        from dotenv import load_dotenv
        load_dotenv()
        
        return TheGraphConfig(
            graph_api_key=os.getenv("GRAPH_API_KEY", ""),
            uniswap_v2_id=os.getenv("UNISWAP_V2_ID"),
            sushiswap_id=os.getenv("SUSHISWAP_ID")
        )
    
    def _validate_config(self) -> None:
        """Validate that required configuration is present."""
        if not self.config.graph_api_key:
            raise ValueError("GRAPH_API_KEY is required in environment variables")
        
        if not self.config.uniswap_v2_id and not self.config.sushiswap_id:
            raise ValueError("At least one subgraph ID must be provided")
        
        if self.config.min_age_days >= self.config.max_age_days:
            raise ValueError("min_age_days must be less than max_age_days")
    
    def _build_subgraph_configs(self) -> List[TheGraphSubgraphConfig]:
        """Build list of active subgraph configurations."""
        subgraphs = []
        
        # Add Uniswap V2 if configured
        if self.config.uniswap_v2_id:
            subgraphs.append(TheGraphSubgraphConfig(
                subgraph_id=self.config.uniswap_v2_id,
                name="Uniswap V2",
                chain="Ethereum",
                liquidity_threshold=self.config.liquidity_thresholds["uniswap_v2"]
            ))
        
        # Add SushiSwap if configured
        if self.config.sushiswap_id:
            subgraphs.append(TheGraphSubgraphConfig(
                subgraph_id=self.config.sushiswap_id,
                name="SushiSwap",
                chain="Ethereum", 
                liquidity_threshold=self.config.liquidity_thresholds["sushiswap"]
            ))
        
        return subgraphs
    
    def _build_subgraph_url(self, subgraph_id: str) -> str:
        """Build complete subgraph URL from ID."""
        return f"{self.config.graph_gateway_base}/{self.config.graph_api_key}/subgraphs/id/{subgraph_id}"
    
    def get_discovery_stats(self) -> Dict[str, any]:
        """Get current discovery statistics."""
        stats = self.stats.copy()
        
        if stats["discovery_start_time"] and stats["discovery_end_time"]:
            duration = (stats["discovery_end_time"] - stats["discovery_start_time"]).total_seconds()
            stats["total_duration_seconds"] = duration
            
            if duration > 0:
                stats["pairs_per_second"] = stats["total_pairs_discovered"] / duration
        
        return stats
    
    def reset_stats(self) -> None:
        """Reset discovery statistics."""
        self.stats = {
            "total_pairs_discovered": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "discovery_start_time": None,
            "discovery_end_time": None
        }
        
        self.logger.info("Discovery statistics reset")


# === ЧАСТЬ 1 ЗАВЕРШЕНА ===
# Следующие части:
# - Часть 2: Temporal slicing logic  
# - Часть 3: Pagination implementation
# - Часть 4: Data transformation to TokenDiscoveryReport
# - Часть 5: Integration with orchestrator

if __name__ == "__main__":
    # Simple test to verify Part 1 structure
    try:
        agent = TheGraphDiscoveryAgent()
        print(f"✅ Part 1 successful: {len(agent.subgraphs)} subgraphs configured")
        print(f"   Config: {agent.config.min_age_days}-{agent.config.max_age_days} days")
        print(f"   Stats: {agent.get_discovery_stats()}")
    except Exception as e:
        print(f"❌ Part 1 error: {e}")
