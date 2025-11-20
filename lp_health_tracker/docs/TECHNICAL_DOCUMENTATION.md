# 🔧 Technical Documentation - LP Health Tracker

## Architecture Overview

### System Components

```
LP Health Tracker
├── Core Engine
│   ├── main.py - AsyncIO agent with scheduler
│   ├── simple_multi_pool.py - Multi-pool manager
│   └── data_analyzer.py - IL mathematical engine
├── Data Layer
│   ├── data_providers.py - Live data integration
│   ├── position_manager.py - Position persistence
│   └── historical_data_manager.py - Time series data
├── Integration Layer
│   ├── web3_utils.py - Blockchain connectivity
│   ├── notification_manager.py - Telegram alerts
│   └── price_strategy_manager.py - Price feed strategy
└── Configuration
    ├── settings.py - Environment management
    └── config/ - Application settings
```

### Key Design Patterns

**1. Strategy Pattern - Data Providers**
```python
class DataProvider(ABC):
    @abstractmethod
    async def get_token_price(self, symbol: str) -> float:
        pass

class LiveDataProvider(DataProvider):
    # Real API implementation
    
class MockDataProvider(DataProvider):
    # Testing implementation
```

**2. Manager Pattern - Multi-Pool Handling**
```python
class SimpleMultiPoolManager:
    def __init__(self, data_provider: DataProvider):
        self.data_provider = data_provider
        self.pools = []
    
    def analyze_all_pools_with_fees(self) -> List[Dict]:
        # Coordinates analysis across multiple pools
```

**3. Calculator Pattern - IL Mathematics**
```python
class ImpermanentLossCalculator:
    def calculate_impermanent_loss(self, initial_ratio: float, current_ratio: float) -> float:
        # Core IL formula: 2 * (√(price_ratio) / (1 + price_ratio)) - 1
        price_ratio = current_ratio / initial_ratio
        return abs(2 * (math.sqrt(price_ratio) / (1 + price_ratio)) - 1)
```

## Data Flow Architecture

### 1. Position Loading
```
JSON Config → PositionManager → MultiPoolManager → Individual Pool Objects
```

### 2. Price Data Flow
```
External APIs → DataProvider → Price Strategy Manager → Pool Analysis
```

### 3. Analysis Pipeline
```
Pool State → IL Calculator → Net P&L Calculator → Risk Assessment → Notifications
```

## Core Mathematical Models

### Impermanent Loss Formula
```python
# Price ratio calculation
price_ratio = current_price_ratio / initial_price_ratio

# IL formula (returns positive value for losses)
il = 2 * (sqrt(price_ratio) / (1 + price_ratio)) - 1
il_loss_amount = abs(il) if il < 0 else 0.0
```

### Net P&L Calculation
```python
# Master Plan Formula
total_income = current_lp_value_usd + earned_fees_usd
total_costs = initial_investment_usd + gas_costs_usd
net_pnl = total_income - total_costs
```

### Fee Estimation
```python
# APR-based fee calculation
fees_earned = initial_investment * (apr / 365) * days_held
```

## Testing Architecture

### Test Structure
```
tests/
├── conftest.py - Shared fixtures
├── fixtures/ - Test data
│   ├── mock_responses.json
│   ├── sample_positions.json
│   └── sample_prices.json
├── Unit Tests
│   ├── test_data_analyzer.py
│   ├── test_simple_multi_pool_manager.py
│   └── test_live_data_provider.py
├── Integration Tests
│   ├── test_integration_end_to_end.py
│   └── test_extensions.py
└── Future Tests
    └── test_future_features.py
```

### Key Testing Strategies

**1. Fixture-Based Isolation**
```python
@pytest.fixture
def mock_data_provider():
    return MockDataProvider({
        'WETH': 2000.0,
        'USDC': 1.0,
        'WBTC': 45000.0
    })

@pytest.fixture
def sample_position():
    return {
        'name': 'Test WETH-USDC',
        'initial_liquidity_a': 1.0,
        'initial_liquidity_b': 2000.0,
        # ... other fields
    }
```

**2. Parametrized Testing**
```python
@pytest.mark.parametrize("price_change,expected_il", [
    (1.0, 0.0),      # No change
    (1.25, 0.0062),  # 25% increase
    (2.0, 0.0572),   # 100% increase
])
def test_il_calculation_scenarios(price_change, expected_il):
    # Test different IL scenarios
```

**3. Integration Test Markers**
```python
@pytest.mark.integration
@pytest.mark.slow
def test_live_api_integration():
    # Tests that hit real APIs
```

## Error Handling Strategy

### Graceful Degradation
```python
async def get_token_price_with_fallback(self, symbol: str) -> float:
    for provider in self.providers:
        try:
            price = await provider.get_price(symbol)
            if price > 0:
                return price
        except Exception as e:
            logger.warning(f"Provider {provider} failed: {e}")
            continue
    
    # Fallback to cached price
    return self.get_cached_price(symbol)
```

### Validation Layers
```python
def validate_position_data(self, position: Dict) -> List[str]:
    errors = []
    required_fields = ['name', 'initial_liquidity_a', 'initial_liquidity_b']
    
    for field in required_fields:
        if field not in position:
            errors.append(f"Missing required field: {field}")
    
    return errors
```

## Performance Considerations

### Async Architecture
- **AsyncIO scheduler** for non-blocking operations
- **Concurrent API calls** for multiple price feeds
- **Rate limiting** for API providers

### Caching Strategy
- **Price data caching** to reduce API calls
- **Historical data persistence** for trend analysis
- **Configuration caching** for repeated runs

### Memory Management
- **Streaming data processing** for large datasets
- **Lazy loading** of historical data
- **Garbage collection** of old analysis results

## Security Considerations

### API Key Management
```python
# Environment-based configuration
INFURA_API_KEY = os.getenv('INFURA_API_KEY', '')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')

# No private keys required - read-only operations
```

### Input Validation
```python
def validate_wallet_address(address: str) -> bool:
    return Web3.isAddress(address)

def sanitize_position_data(position: Dict) -> Dict:
    # Remove any potentially dangerous fields
    safe_fields = ['name', 'pair_address', 'initial_liquidity_a', ...]
    return {k: v for k, v in position.items() if k in safe_fields}
```

## Monitoring and Logging

### Structured Logging
```python
logger.info("Position analysis completed", extra={
    'position_name': position['name'],
    'current_il': il_percentage,
    'net_pnl': net_pnl_usd,
    'analysis_duration_ms': duration
})
```

### Health Checks
```python
async def health_check(self) -> Dict[str, Any]:
    return {
        'web3_connection': await self.web3_manager.test_connection(),
        'telegram_bot': await self.notifier.test_connection(),
        'data_provider': await self.data_provider.health_check(),
        'last_successful_analysis': self.last_analysis_time
    }
```

## Extension Points

### Adding New Protocols
```python
class UniswapV3Analyzer(ProtocolAnalyzer):
    def calculate_position_value(self, position: Dict) -> Dict:
        # V3-specific concentrated liquidity logic
        pass

# Register in protocol factory
PROTOCOL_ANALYZERS = {
    'uniswap_v2': UniswapV2Analyzer,
    'uniswap_v3': UniswapV3Analyzer,
    'sushiswap': SushiswapAnalyzer
}
```

### Adding New Data Providers
```python
class DeFiLlamaProvider(DataProvider):
    async def get_pool_apy(self, pool_address: str) -> float:
        # DeFiLlama APY integration
        pass
```

### Adding New Notification Channels
```python
class DiscordNotifier(NotificationProvider):
    async def send_alert(self, message: str) -> bool:
        # Discord webhook integration
        pass
```

## Deployment Considerations

### Environment Configuration
```bash
# Production environment
DEFAULT_NETWORK=ethereum_mainnet
CHECK_INTERVAL_MINUTES=15
LOG_LEVEL=INFO

# Development environment  
DEFAULT_NETWORK=ethereum_sepolia
CHECK_INTERVAL_MINUTES=5
LOG_LEVEL=DEBUG
```

### Resource Requirements
- **Memory**: ~50MB for basic operation
- **CPU**: Minimal (mostly I/O bound)
- **Network**: ~100 API calls/hour per monitored position
- **Storage**: ~1MB per month per position for historical data

### Scaling Considerations
- **Horizontal scaling**: Multiple instances for different wallets
- **Vertical scaling**: Increase check frequency or position count
- **Database migration**: Currently JSON, can migrate to PostgreSQL/MongoDB