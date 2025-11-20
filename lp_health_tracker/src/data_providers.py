"""
Data Providers for LP Health Tracker
===================================

Abstract interface and mock implementation for data sources.
Live data functionality moved to PriceStrategyManager.

Note: LiveDataProvider functionality moved to PriceStrategyManager
"""

from abc import ABC, abstractmethod
from typing import Dict, Tuple, List
import logging
import time
import random


class DataProvider(ABC):
    """Abstract base class for data providers."""
    
    @abstractmethod
    def get_current_prices(self, pool_config: Dict) -> Tuple[float, float]:
        """Get current prices for tokens in pool.
        
        Returns:
            Tuple[float, float]: (token_a_price, token_b_price)
        """
        pass
    
    @abstractmethod
    def get_pool_apr(self, pool_config: Dict) -> float:
        """Get the estimated annual percentage rate (APR) for the pool.
        
        Args:
            pool_config: Pool configuration dictionary
            
        Returns:
            float: Annual percentage rate as decimal (e.g., 0.15 for 15% APR)
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """Get provider name for logging."""
        pass


class MockDataProvider(DataProvider):
    """Mock data provider for testing and demonstration.
    
    Supports different market scenarios:
    - mixed_volatility: Default scenario with realistic mixed movements
    - bull_market: Strong upward trend with different growth rates
    - bear_market: Downward trend with different decline rates
    - extreme_volatility: High volatility scenario for stress testing
    - stablecoin_depeg: Stablecoin depeg scenario
    """
    
    def __init__(self, scenario: str = "mixed_volatility"):
        self.scenario = scenario
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"MockDataProvider initialized with scenario: {scenario}")
        
        # Mock APR data for different market scenarios
        # Updated with REAL Uniswap V2 data from DeFi Llama API (2025)
        self.mock_aprs = {
            "mixed_volatility": {
                "USDC-USDT": 0.001,    # 0.1% APR - based on real V2 data (0.12%)
                "WETH-USDC": 0.04,     # 4% APR - based on real V2 data (4.13%)
                "WETH-WBTC": 0.035,    # 3.5% APR - similar to WETH-USDC
                "ETH-USDC": 0.04,      # Same as WETH-USDC
                "ETH-WBTC": 0.035,     # Same as WETH-WBTC
            },
            "bull_market": {
                "USDC-USDT": 0.0005,   # 0.05% APR - lower activity in bull run
                "WETH-USDC": 0.08,     # 8% APR - doubled activity and volume
                "WETH-WBTC": 0.07,     # 7% APR - strong crypto activity
                "ETH-USDC": 0.08,      # Same as WETH-USDC
                "ETH-WBTC": 0.07,      # Same as WETH-WBTC
            },
            "bear_market": {
                "USDC-USDT": 0.002,    # 0.2% APR - flight to stables increases activity
                "WETH-USDC": 0.025,    # 2.5% APR - lower volume
                "WETH-WBTC": 0.02,     # 2% APR - reduced activity
                "ETH-USDC": 0.025,     # Same as WETH-USDC
                "ETH-WBTC": 0.02,      # Same as WETH-WBTC
            },
            "extreme_volatility": {
                "USDC-USDT": 0.005,    # 0.5% APR - even stables see activity
                "WETH-USDC": 0.15,     # 15% APR - extreme spreads and volume
                "WETH-WBTC": 0.12,     # 12% APR - high volatility = high fees
                "ETH-USDC": 0.15,      # Same as WETH-USDC
                "ETH-WBTC": 0.12,      # Same as WETH-WBTC
            },
            "stablecoin_depeg": {
                "USDC-USDT": 0.10,     # 10% APR - massive arbitrage opportunities
                "WETH-USDC": 0.06,     # 6% APR - increased activity
                "WETH-WBTC": 0.05,     # 5% APR - some spillover effect
                "ETH-USDC": 0.06,      # Same as WETH-USDC
                "ETH-WBTC": 0.05,      # Same as WETH-WBTC
            }
        }
        
        # Price simulation state
        self._price_state = {}
        self._last_update = 0
        
    def get_current_prices(self, pool_config: Dict) -> Tuple[float, float]:
        """Simulate price changes based on market scenario and pool type."""
        pool_name = pool_config.get('name', 'Unknown')
        initial_price_a = pool_config.get('initial_price_a_usd', 1.0)
        initial_price_b = pool_config.get('initial_price_b_usd', 1.0)
        
        # Initialize state if needed
        if pool_name not in self._price_state:
            self._price_state[pool_name] = {
                'price_a': initial_price_a,
                'price_b': initial_price_b,
                'last_update': time.time()
            }
        
        state = self._price_state[pool_name]
        current_time = time.time()
        time_delta = current_time - state['last_update']
        
        # Update prices based on scenario
        if time_delta > 1:  # Update every second
            state['price_a'], state['price_b'] = self._simulate_price_movement(
                state['price_a'], state['price_b'], pool_name, time_delta
            )
            state['last_update'] = current_time
        
        return state['price_a'], state['price_b']
    
    def _simulate_price_movement(self, price_a: float, price_b: float, pool_name: str, time_delta: float) -> Tuple[float, float]:
        """Simulate realistic price movements based on scenario."""
        
        # Get scenario parameters
        if self.scenario == "mixed_volatility":
            volatility_a = 0.02  # 2% volatility per update
            volatility_b = 0.005 if 'USDC' in pool_name or 'USDT' in pool_name else 0.015
            trend_a = random.uniform(-0.001, 0.001)  # Small random trend
            trend_b = random.uniform(-0.0005, 0.0005)
            
        elif self.scenario == "bull_market":
            volatility_a = 0.015
            volatility_b = 0.003 if 'USDC' in pool_name or 'USDT' in pool_name else 0.01
            trend_a = 0.002  # Positive trend
            trend_b = 0.001 if 'BTC' in pool_name or 'ETH' in pool_name else 0.0002
            
        elif self.scenario == "bear_market":
            volatility_a = 0.025
            volatility_b = 0.008 if 'USDC' in pool_name or 'USDT' in pool_name else 0.02
            trend_a = -0.0015  # Negative trend
            trend_b = -0.0008 if 'BTC' in pool_name or 'ETH' in pool_name else -0.0002
            
        elif self.scenario == "extreme_volatility":
            volatility_a = 0.05  # 5% volatility
            volatility_b = 0.01 if 'USDC' in pool_name or 'USDT' in pool_name else 0.03
            trend_a = random.uniform(-0.003, 0.003)  # High random trend
            trend_b = random.uniform(-0.002, 0.002)
            
        elif self.scenario == "stablecoin_depeg":
            if 'USDC' in pool_name and 'USDT' in pool_name:
                # Stablecoin depeg scenario
                volatility_a = 0.02
                volatility_b = 0.02
                trend_a = random.uniform(-0.005, 0.005)  # High instability
                trend_b = random.uniform(-0.005, 0.005)
            else:
                volatility_a = 0.01
                volatility_b = 0.01
                trend_a = random.uniform(-0.001, 0.001)
                trend_b = random.uniform(-0.001, 0.001)
        else:
            # Default mixed volatility
            volatility_a = 0.02
            volatility_b = 0.01
            trend_a = 0
            trend_b = 0
        
        # Apply price changes
        change_a = (random.gauss(0, volatility_a) + trend_a) * time_delta
        change_b = (random.gauss(0, volatility_b) + trend_b) * time_delta
        
        new_price_a = max(price_a * (1 + change_a), 0.01)  # Prevent negative prices
        new_price_b = max(price_b * (1 + change_b), 0.01)
        
        return new_price_a, new_price_b
    
    def get_pool_apr(self, pool_config: Dict) -> float:
        """Get mock APR based on scenario and pool type."""
        pool_name = pool_config.get('name', 'Unknown')
        
        # Normalize pool name for lookup
        normalized_name = pool_name.upper()
        
        # Get APR for current scenario
        scenario_aprs = self.mock_aprs.get(self.scenario, self.mock_aprs["mixed_volatility"])
        
        # Try direct lookup
        apr = scenario_aprs.get(normalized_name)
        if apr is not None:
            return apr
        
        # Try with ETH/WETH normalization
        normalized_name = normalized_name.replace('WETH', 'ETH')
        apr = scenario_aprs.get(normalized_name)
        if apr is not None:
            return apr
        
        # Try reverse order
        if '-' in normalized_name:
            token_a, token_b = normalized_name.split('-', 1)
            reversed_name = f"{token_b}-{token_a}"
            apr = scenario_aprs.get(reversed_name)
            if apr is not None:
                return apr
        
        # Default APR based on pool type
        if 'USDC' in normalized_name and 'USDT' in normalized_name:
            return 0.001  # 0.1% for stablecoin pairs
        elif any(token in normalized_name for token in ['ETH', 'WETH', 'BTC', 'WBTC']):
            return 0.035  # 3.5% for major crypto pairs
        else:
            return 0.02   # 2% default
    
    def get_provider_name(self) -> str:
        return f"Mock Data Provider ({self.scenario})"
