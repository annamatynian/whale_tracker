# 🔌 API Reference - LP Health Tracker

## Core Classes and Methods

### ImpermanentLossCalculator

**Purpose**: Mathematical engine for IL and P&L calculations

```python
from src.data_analyzer import ImpermanentLossCalculator

calculator = ImpermanentLossCalculator()
```

#### Methods

**`calculate_impermanent_loss(initial_price_ratio, current_price_ratio) -> float`**

Calculate IL based on price ratio changes.

```python
# Example: ETH price doubles relative to USDC
initial_ratio = 2000.0 / 1.0  # ETH/USDC = 2000
current_ratio = 4000.0 / 1.0   # ETH/USDC = 4000

il = calculator.calculate_impermanent_loss(initial_ratio, current_ratio)
print(f"IL: {il:.2%}")  # Output: IL: 5.72%
```

**Parameters:**
- `initial_price_ratio` (float): Initial price ratio (token_a_price / token_b_price)
- `current_price_ratio` (float): Current price ratio (token_a_price / token_b_price)

**Returns:**
- `float`: IL as positive decimal (0.0572 for 5.72% loss)

---

**`calculate_lp_position_value(lp_tokens_held, total_lp_supply, reserve_a, reserve_b, price_a_usd, price_b_usd) -> Dict`**

Calculate current USD value of LP position.

```python
position_value = calculator.calculate_lp_position_value(
    lp_tokens_held=10.5,
    total_lp_supply=1000000,
    reserve_a=500.0,        # WETH reserves
    reserve_b=1000000.0,    # USDC reserves  
    price_a_usd=2000.0,     # WETH price
    price_b_usd=1.0         # USDC price
)

print(f"Total Value: ${position_value['total_value_usd']:.2f}")
```

**Returns:**
```python
{
    'total_value_usd': 31500.0,
    'token_a_amount': 5.25,
    'token_b_amount': 10500.0,
    'token_a_value_usd': 10500.0,
    'token_b_value_usd': 10500.0,
    'ownership_percentage': 0.0105
}
```

---

**`compare_strategies(position_data, current_reserves, current_prices, estimated_fees_earned=0.0) -> Dict`**

Compare LP strategy vs HODL strategy with comprehensive analysis.

```python
comparison = calculator.compare_strategies(
    position_data={
        'initial_liquidity_a': 1.0,
        'initial_liquidity_b': 2000.0,
        'initial_price_a_usd': 2000.0,
        'initial_price_b_usd': 1.0,
        'lp_tokens_held': 44.72
    },
    current_reserves={
        'reserve_a': 500.0,
        'reserve_b': 1000000.0,
        'total_lp_supply': 1000000
    },
    current_prices={
        'token_a_usd': 2500.0,
        'token_b_usd': 1.0
    },
    estimated_fees_earned=50.0
)

print(f"Better Strategy: {comparison['better_strategy']}")
print(f"IL: {comparison['impermanent_loss']['percentage']:.2%}")
```

### SimpleMultiPoolManager

**Purpose**: Coordinate multiple LP position monitoring

```python
from src.simple_multi_pool import SimpleMultiPoolManager
from src.data_providers import LiveDataProvider

manager = SimpleMultiPoolManager(LiveDataProvider())
```

#### Methods

**`add_position(position_config) -> bool`**

Add new LP position to monitoring.

```python
position = {
    'name': 'WETH-USDC Uniswap V2',
    'pair_address': '0xB4e16d0168e52d35CaCD2b6464f00d6eB9002C6D',
    'token_a_symbol': 'WETH',
    'token_b_symbol': 'USDC',
    'initial_liquidity_a': 1.0,
    'initial_liquidity_b': 2000.0,
    'initial_price_a_usd': 2000.0,
    'initial_price_b_usd': 1.0,
    'wallet_address': '0x...',
    'network': 'ethereum_mainnet',
    'il_alert_threshold': 0.05,
    'protocol': 'uniswap_v2',
    'active': True
}

success = manager.add_position(position)
```

---

**`analyze_all_pools_with_fees() -> List[Dict]`**

Analyze all monitored positions with fees and gas costs.

```python
results = manager.analyze_all_pools_with_fees()

for result in results:
    position_name = result['position_info']['name']
    net_pnl = result['net_pnl']['net_pnl_usd']
    il_percentage = result['current_status']['il_percentage']
    
    print(f"{position_name}: Net P&L ${net_pnl:.2f}, IL {il_percentage:.2%}")
```

**Returns:**
```python
[
    {
        'position_info': {
            'name': 'WETH-USDC Uniswap V2',
            'initial_investment_usd': 4000.0,
            'days_held': 30,
            'gas_costs_usd': 25.0
        },
        'current_status': {
            'current_lp_value_usd': 3950.0,
            'earned_fees_usd': 120.0,
            'total_lp_value_usd': 4070.0,
            'il_percentage': 0.0125,
            'il_usd': 50.0
        },
        'net_pnl': {
            'net_pnl_usd': 45.0,
            'net_pnl_percentage': 0.0112,
            'is_profitable': True
        },
        'strategy_comparison': {
            'better_strategy': 'LP'
        }
    }
]
```

---

**`load_positions_from_json(file_path) -> bool`**

Load positions from JSON configuration file.

```python
success = manager.load_positions_from_json('data/positions.json')
print(f"Loaded {manager.count_pools()} positions")
```

### DataProvider Interface

**Purpose**: Abstract interface for price data sources

#### LiveDataProvider

```python
from src.data_providers import LiveDataProvider

provider = LiveDataProvider()
```

**`async get_token_price(symbol) -> float`**

Get current token price in USD.

```python
import asyncio

async def get_prices():
    eth_price = await provider.get_token_price('WETH')
    usdc_price = await provider.get_token_price('USDC')
    return eth_price, usdc_price

prices = asyncio.run(get_prices())
print(f"ETH: ${prices[0]:.2f}, USDC: ${prices[1]:.4f}")
```

**`async get_multiple_prices(symbols) -> Dict[str, float]`**

Get multiple token prices efficiently.

```python
symbols = ['WETH', 'USDC', 'WBTC', 'UNI']
prices = await provider.get_multiple_prices(symbols)

for symbol, price in prices.items():
    print(f"{symbol}: ${price:.2f}")
```

#### MockDataProvider

```python
from src.data_providers import MockDataProvider

# For testing with fixed prices
mock_provider = MockDataProvider({
    'WETH': 2000.0,
    'USDC': 1.0,
    'WBTC': 45000.0
})
```

### NotificationManager

**Purpose**: Handle alerts and notifications

```python
from src.notification_manager import TelegramNotifier

notifier = TelegramNotifier()
```

**`async send_message(message) -> bool`**

Send simple text message.

```python
success = await notifier.send_message("🚀 LP Health Tracker started!")
```

**`async send_il_alert(position_data, il_data) -> bool`**

Send formatted IL alert.

```python
alert_sent = await notifier.send_il_alert(
    position_data={
        'name': 'WETH-USDC Uniswap V2',
        'il_alert_threshold': 0.05
    },
    il_data={
        'current_il': 0.0572,
        'current_value_usd': 3950.0,
        'initial_investment_usd': 4000.0
    }
)
```

### Settings

**Purpose**: Configuration management

```python
from config.settings import Settings

settings = Settings()
```

**Properties:**
- `TELEGRAM_BOT_TOKEN`: Telegram bot token
- `TELEGRAM_CHAT_ID`: Chat ID for notifications
- `INFURA_API_KEY`: Infura API key
- `DEFAULT_NETWORK`: Default blockchain network
- `CHECK_INTERVAL_MINUTES`: Monitoring frequency
- `DEFAULT_IL_THRESHOLD`: Default IL alert threshold

**Methods:**

**`validate() -> List[str]`**

Validate configuration and return errors.

```python
errors = settings.validate()
if errors:
    for error in errors:
        print(f"❌ {error}")
else:
    print("✅ Configuration valid")
```

**`get_rpc_url(network=None) -> str`**

Get RPC URL for specified network.

```python
mainnet_url = settings.get_rpc_url('ethereum_mainnet')
sepolia_url = settings.get_rpc_url('ethereum_sepolia')
```

## Usage Patterns

### Basic Position Monitoring

```python
import asyncio
from src.simple_multi_pool import SimpleMultiPoolManager
from src.data_providers import LiveDataProvider

async def monitor_positions():
    # Initialize manager with live data
    manager = SimpleMultiPoolManager(LiveDataProvider())
    
    # Load positions from JSON
    manager.load_positions_from_json('data/positions.json')
    
    # Analyze all positions
    results = manager.analyze_all_pools_with_fees()
    
    # Check for alerts
    for result in results:
        il = result['current_status']['il_percentage']
        threshold = 0.05  # 5%
        
        if il > threshold:
            print(f"🚨 IL Alert: {result['position_info']['name']}")
            print(f"   Current IL: {il:.2%}")
            print(f"   Threshold: {threshold:.2%}")

# Run monitoring
asyncio.run(monitor_positions())
```

### Custom IL Analysis

```python
from src.data_analyzer import ImpermanentLossCalculator

def analyze_price_scenarios():
    calculator = ImpermanentLossCalculator()
    
    # Test different price change scenarios
    initial_ratio = 2000.0 / 1.0  # ETH/USDC
    
    scenarios = [
        ("No change", 1.0),
        ("ETH +25%", 1.25),
        ("ETH +50%", 1.5),
        ("ETH doubles", 2.0),
        ("ETH -20%", 0.8),
        ("ETH -50%", 0.5)
    ]
    
    print("Price Change Scenario | Impermanent Loss")
    print("-" * 40)
    
    for name, multiplier in scenarios:
        new_ratio = initial_ratio * multiplier
        il = calculator.calculate_impermanent_loss(initial_ratio, new_ratio)
        print(f"{name:20} | {il:12.2%}")

analyze_price_scenarios()
```

### Integration with External Systems

```python
import asyncio
from src.main import LPHealthTracker

class CustomLPTracker(LPHealthTracker):
    """Extended tracker with custom functionality."""
    
    async def custom_analysis(self):
        """Add your custom analysis logic here."""
        positions = self.position_manager.load_positions()
        
        for position in positions:
            # Custom logic for position analysis
            # Send to external system, database, etc.
            pass
    
    async def monitor_positions(self):
        """Override to add custom monitoring."""
        # Call parent method
        await super().monitor_positions()
        
        # Add custom analysis
        await self.custom_analysis()

# Use custom tracker
async def main():
    tracker = CustomLPTracker()
    await tracker.start()

# Run custom tracker
asyncio.run(main())
```

## Error Handling

### Common Exceptions

**`ValueError`**: Invalid input parameters
```python
try:
    il = calculator.calculate_impermanent_loss(-1.0, 2.0)  # Negative ratio
except ValueError as e:
    print(f"Invalid input: {e}")
```

**`ConnectionError`**: API connection issues
```python
try:
    price = await provider.get_token_price('WETH')
except ConnectionError as e:
    print(f"API connection failed: {e}")
    # Use fallback provider or cached price
```

**`FileNotFoundError`**: Configuration file missing
```python
try:
    manager.load_positions_from_json('missing_file.json')
except FileNotFoundError:
    print("Position file not found, creating empty configuration")
    manager.save_positions_to_json('data/positions.json')
```

### Best Practices

1. **Always use async/await** for data provider calls
2. **Validate inputs** before calculations
3. **Handle network failures** gracefully with fallbacks
4. **Use proper logging** for debugging
5. **Test with mock data** before live deployment

## Testing Utilities

### Test Fixtures

```python
import pytest
from src.data_providers import MockDataProvider

@pytest.fixture
def mock_provider():
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
        'initial_price_a_usd': 2000.0,
        'initial_price_b_usd': 1.0
    }

def test_il_calculation(mock_provider, sample_position):
    calculator = ImpermanentLossCalculator()
    il = calculator.calculate_impermanent_loss(2000.0, 2500.0)
    assert abs(il - 0.0125) < 0.001  # ~1.25% IL
```

## Version Information

**Current Version**: 0.3.0  
**API Stability**: Beta - expect minor changes  
**Python Support**: 3.9+  
**Last Updated**: January 2025