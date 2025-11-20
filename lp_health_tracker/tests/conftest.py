"""
Pytest Configuration and Fixtures
================================

Shared fixtures and configuration for all tests.

Author: Generated for DeFi-RAG Project
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from decimal import Decimal
from datetime import datetime
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.position_models import LPPosition, TokenInfo, SupportedNetwork, SupportedProtocol
from src.position_manager import PositionManager


@pytest.fixture
def temp_data_dir():
    """Create temporary directory for test data."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_token_a():
    """Sample TokenInfo for token A."""
    return TokenInfo(
        symbol="WETH",
        address="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        decimals=18
    )


@pytest.fixture
def sample_token_b():
    """Sample TokenInfo for token B."""
    return TokenInfo(
        symbol="USDC",
        address="0xA0b86a33E6c21C64E0eb4ADa7B0b0094a7f6E44C",
        decimals=6
    )


@pytest.fixture
def sample_lp_position(sample_token_a, sample_token_b):
    """Sample LP position using Pydantic model."""
    return LPPosition(
        name="WETH-USDC Test Position",
        pair_address="0xB4e16d0168e52d35CaCD2b6464f00d1e8d5362C6",
        token_a=sample_token_a,
        token_b=sample_token_b,
        initial_liquidity_a=Decimal('0.1'),
        initial_liquidity_b=Decimal('200.0'),
        initial_price_a_usd=Decimal('2000.0'),
        initial_price_b_usd=Decimal('1.0'),
        wallet_address="0x742d35Cc6634C0532925a3b8e0b9D5a3dE62a1B0",
        network=SupportedNetwork.ETHEREUM_MAINNET,
        protocol=SupportedProtocol.UNISWAP_V2,
        il_alert_threshold=Decimal('0.05'),
        notes="Test position for pytest"
    )


@pytest.fixture
def position_manager_with_temp_dir(temp_data_dir):
    """PositionManager with temporary directory."""
    return PositionManager(data_dir=temp_data_dir)


@pytest.fixture
def sample_position_dict():
    """Sample position as dictionary (legacy format)."""
    return {
        "name": "Test Position Dict",
        "pair_address": "0xB4e16d0168e52d35CaCD2b6464f00d1e8d5362C6",
        "token_a_symbol": "WETH",
        "token_b_symbol": "USDC", 
        "token_a_address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "token_b_address": "0xA0b86a33E6c21C64E0eb4ADa7B0b0094a7f6E44C",
        "initial_liquidity_a": 0.1,
        "initial_liquidity_b": 200.0,
        "initial_price_a_usd": 2000.0,
        "initial_price_b_usd": 1.0,
        "wallet_address": "0x742d35Cc6634C0532925a3b8e0b9D5a3dE62a1B0",
        "network": "ethereum_mainnet",
        "protocol": "uniswap_v2",
        "il_alert_threshold": 0.05,
        "active": True,
        "notes": "Test position dictionary"
    }


@pytest.fixture
def mock_price_data():
    """Mock price data for testing."""
    return {
        "WETH": 2500.0,
        "USDC": 1.0,
        "ETH": 2500.0
    }


@pytest.fixture 
def mock_pool_data():
    """Mock pool data for testing."""
    return {
        "pair_address": "0xB4e16d0168e52d35CaCD2b6464f00d1e8d5362C6",
        "reserve_a": "1000.5",
        "reserve_b": "2500000.0",
        "total_supply": "50000.0",
        "current_price": 2500.0
    }


@pytest.fixture
def il_test_cases():
    """Comprehensive IL test cases covering all scenarios from IL_BASICS.md.
    
    These test cases represent the standard IL scenarios and are used to validate
    that our IL calculation functions produce mathematically correct results.
    """
    return [
        {
            "price_ratio": 1.0,
            "expected_il": 0.0,
            "description": "No price change - 0% IL"
        },
        {
            "price_ratio": 1.25,
            "expected_il": 0.006,  # ~0.6% IL
            "description": "25% price increase"
        },
        {
            "price_ratio": 1.5,
            "expected_il": 0.020,  # ~2.0% IL
            "description": "50% price increase"
        },
        {
            "price_ratio": 2.0,
            "expected_il": 0.057,  # ~5.7% IL
            "description": "100% price increase (doubled)"
        },
        {
            "price_ratio": 3.0,
            "expected_il": 0.134,  # ~13.4% IL (corrected: was 0.127)
            "description": "200% price increase (tripled)"
        },
        {
            "price_ratio": 4.0,
            "expected_il": 0.200,  # ~20% IL
            "description": "300% price increase (4x)"
        },
        {
            "price_ratio": 5.0,
            "expected_il": 0.255,  # ~25.5% IL (corrected: was 0.276)
            "description": "400% price increase (5x)"
        },
        {
            "price_ratio": 0.8,
            "expected_il": 0.006,  # ~0.6% IL (symmetric)
            "description": "20% price decrease"
        },
        {
            "price_ratio": 0.5,
            "expected_il": 0.057,  # ~5.7% IL (symmetric with 2x)
            "description": "50% price decrease (halved)"
        },
        {
            "price_ratio": 0.25,
            "expected_il": 0.200,  # ~20% IL (symmetric with 4x)
            "description": "75% price decrease (quartered)"
        },
        {
            "price_ratio": 0.1,
            "expected_il": 0.425,  # ~42.5% IL (corrected: was 0.488)
            "description": "90% price decrease (extreme case)"
        }
    ]


def check_il_close(calculated_il, expected_il, tolerance=0.005):
    """Custom assertion helper for IL comparisons.
    
    Args:
        calculated_il: The IL value calculated by our function
        expected_il: The expected IL value from theory
        tolerance: Acceptable difference (default 0.5%)
    """
    difference = abs(calculated_il - expected_il)
    assert difference < tolerance, (
        f"IL calculation mismatch: expected {expected_il:.4f}, "
        f"got {calculated_il:.4f}, difference: {difference:.4f}"
    )


@pytest.fixture
def il_checker():
    """Fixture providing IL comparison function."""
    return check_il_close


@pytest.fixture
def sample_current_data():
    """Current market data for position analysis."""
    return {
        "token_a_price_usd": 2500.0,  # WETH at $2500 (up from $2000)
        "token_b_price_usd": 1.0,     # USDC stable
        "current_reserves_a": 950.0,   # Less WETH in pool
        "current_reserves_b": 2375000.0,  # More USDC in pool
        "total_lp_supply": 50000.0,
        "user_lp_balance": 100.0,
        "block_timestamp": int(datetime.now().timestamp())
    }


@pytest.fixture
def sample_position_data(sample_lp_position, sample_current_data):
    """Complete position data for comprehensive testing."""
    return {
        "position": sample_lp_position,
        "current_market_data": sample_current_data,
        "initial_total_value_usd": float(sample_lp_position.initial_value_usd),
        "current_timestamp": datetime.now()
    }


# ==============================================================================
# STAGE 1 & STAGE 2 FIXTURES - Added to resolve missing fixture errors
# ==============================================================================

@pytest.fixture
def stage1_position_data():
    """Sample position data for Stage 1 tests with required fields."""
    return {
        "name": "Test-WETH-USDC-Stage1",
        "token_a_symbol": "WETH",
        "token_b_symbol": "USDC",
        "initial_liquidity_a": 0.1,
        "initial_liquidity_b": 200.0,
        "initial_price_a_usd": 2000.0,
        "initial_price_b_usd": 1.0,
        "gas_costs_usd": 75.0,
        "days_held_mock": 30,
        "il_alert_threshold": 0.05,
        "protocol": "uniswap_v2",
        "network": "ethereum_mainnet"
    }

@pytest.fixture
def stage2_position_data():
    """Sample position data for Stage 2 tests with entry_date."""
    return {
        "name": "Test-WETH-USDC-Stage2",
        "token_a_symbol": "WETH",
        "token_b_symbol": "USDC",
        "initial_liquidity_a": 0.1,
        "initial_liquidity_b": 200.0,
        "initial_price_a_usd": 2000.0,
        "initial_price_b_usd": 1.0,
        "gas_costs_usd": 75.0,
        "entry_date": "2024-06-01T00:00:00Z",
        "il_alert_threshold": 0.05,
        "protocol": "uniswap_v2",
        "network": "ethereum_mainnet"
    }

@pytest.fixture
def mock_data_provider():
    """Mock data provider for testing."""
    try:
        from src.data_providers import MockDataProvider
        return MockDataProvider("extreme_volatility")  # Using 15% APR scenario
    except ImportError:
        pytest.skip("MockDataProvider not available")

@pytest.fixture  
def live_data_provider():
    """Live data provider for integration tests."""
    try:
        from src.data_providers import LiveDataProvider
        return LiveDataProvider()
    except ImportError:
        pytest.skip("LiveDataProvider not available")

@pytest.fixture
def net_pnl_calculator():
    """Net P&L calculator instance."""
    try:
        from src.data_analyzer import NetPnLCalculator
        return NetPnLCalculator()
    except ImportError:
        pytest.skip("NetPnLCalculator not available")

@pytest.fixture
def stage1_multi_pool_manager(mock_data_provider):
    """Multi-pool manager for Stage 1 tests."""
    try:
        from src.simple_multi_pool import SimpleMultiPoolManager
        return SimpleMultiPoolManager(mock_data_provider)
    except ImportError:
        pytest.skip("SimpleMultiPoolManager not available")

@pytest.fixture
def stage2_multi_pool_manager(live_data_provider):
    """Multi-pool manager for Stage 2 tests."""
    try:
        from src.simple_multi_pool import SimpleMultiPoolManager
        return SimpleMultiPoolManager(live_data_provider)
    except ImportError:
        pytest.skip("SimpleMultiPoolManager not available")

@pytest.fixture
def stage1_test_calculations():
    """Sample calculation data for Stage 1 tests."""
    # Updated for extreme_volatility scenario (15% APR)
    return {
        'initial_investment': 2000.0,
        'current_lp_value': 2100.0,
        'expected_apr': 0.15,  # 15% APR in extreme_volatility scenario
        'gas_costs': 75.0,
        'expected_fees_30_days': 24.66  # 2000 * (0.15/365) * 30 = 24.66
    }


# Rate limit handling for API tests
@pytest.fixture
def skip_if_rate_limited():
    """Skip tests if API rate limits are hit."""
    def _skip_on_rate_limit(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if "429" in str(e) or "rate limit" in str(e).lower() or "too many requests" in str(e).lower():
                    pytest.skip(f"Skipping due to API rate limit: {e}")
                raise
        return wrapper
    return _skip_on_rate_limit
