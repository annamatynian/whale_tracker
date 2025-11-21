# Whale Tracker Abstractions

## Overview

This document describes the abstraction layer introduced to solve critical architecture problems in Whale Tracker.

## Problems Solved

### ❌ Before: Tight Coupling
- Hardcoded Telegram API → can't add Discord/Email
- Hardcoded Etherscan API → can't support multi-chain
- In-memory cooldown → lost on restart
- No RPC failover → single point of failure
- Business logic mixed with data access

### ✅ After: Abstraction Layer
- **Pluggable providers** → easy to add new services
- **Multi-provider support** → automatic failover
- **Distributed-ready** → Redis/Database support
- **Testable** → mock implementations
- **Clean architecture** → separation of concerns

---

## Architecture

```
src/
├── abstractions/          # Abstract base classes (interfaces)
│   ├── notification_provider.py       # Notifications interface
│   ├── rpc_provider.py                # RPC interface
│   ├── cooldown_storage.py            # Cooldown storage interface
│   ├── blockchain_data_provider.py    # Blockchain data interface
│   ├── detection_repository.py        # Data persistence interface
│   └── price_provider.py              # Price data interface
│
├── providers/             # Concrete implementations
│   ├── telegram_provider.py           # Telegram notifications
│   ├── multi_channel_notifier.py      # Multi-channel sender
│   ├── etherscan_provider.py          # Etherscan blockchain data
│   ├── infura_provider.py             # Infura RPC
│   ├── alchemy_provider.py            # Alchemy RPC
│   ├── rpc_failover_manager.py        # RPC failover
│   ├── coingecko_provider.py          # CoinGecko prices
│   └── composite_data_provider.py     # Multi-provider data
│
├── storages/              # Cooldown storage implementations
│   ├── in_memory_cooldown.py          # In-memory (dev/testing)
│   ├── redis_cooldown.py              # Redis (production)
│   └── database_cooldown.py           # PostgreSQL (production)
│
└── repositories/          # Data persistence implementations
    ├── sql_detection_repository.py    # PostgreSQL
    └── in_memory_detection_repository.py  # In-memory (testing)
```

---

## Abstractions Reference

### 1. NotificationProvider

**Purpose:** Send alerts to various channels (Telegram, Discord, Email, etc.)

**Implementations:**
- `TelegramProvider` - Telegram Bot API
- `MultiChannelNotifier` - Send to multiple channels simultaneously

**Key Methods:**
```python
async def send_message(message: str) -> bool
async def send_whale_onehop_alert(...) -> bool
async def send_daily_report(stats: Dict) -> bool
```

**Usage Example:**
```python
from src.providers import TelegramProvider, MultiChannelNotifier

# Single channel
telegram = TelegramProvider()
await telegram.send_message("🚨 Whale alert!")

# Multiple channels
notifier = MultiChannelNotifier([
    TelegramProvider(),
    # DiscordProvider(),  # Can add more
    # EmailProvider()
])
await notifier.send_whale_onehop_alert(...)
```

---

### 2. CooldownStorage

**Purpose:** Track alert cooldowns with persistence

**Implementations:**
- `InMemoryCooldownStorage` - Dev/testing (lost on restart)
- `RedisCooldownStorage` - Production (distributed)
- `DatabaseCooldownStorage` - Production (persistent)

**Key Methods:**
```python
async def was_sent_recently(alert_key: str, cooldown_seconds: int) -> bool
async def mark_sent(alert_key: str) -> None
```

**Usage Example:**
```python
from src.storages import RedisCooldownStorage

storage = RedisCooldownStorage(redis_client)

# Check cooldown
if not await storage.was_sent_recently('whale_0x123', 3600):
    await send_alert()
    await storage.mark_sent('whale_0x123')
```

---

### 3. BlockchainDataProvider

**Purpose:** Fetch blockchain data from various APIs

**Implementations:**
- `EtherscanProvider` - Etherscan, Basescan, Arbiscan, etc.
- `CompositeDataProvider` - Multi-provider with failover

**Key Methods:**
```python
async def get_transaction_count(address: str, block: int) -> int
async def get_transactions(address: str, start_block: int, end_block: int) -> List
async def get_balance(address: str) -> int
```

**Usage Example:**
```python
from src.providers import EtherscanProvider, CompositeDataProvider

# Single provider
etherscan = EtherscanProvider(network='ethereum')
txs = await etherscan.get_transactions(address)

# Multi-provider with failover
provider = CompositeDataProvider([
    (10, EtherscanProvider()),    # Priority 10
    (20, AlchemyProvider()),      # Priority 20 (fallback)
])
txs = await provider.get_transactions(address)
```

---

### 4. RPCProvider

**Purpose:** Interact with blockchain via RPC

**Implementations:**
- `InfuraProvider` - Infura RPC
- `AlchemyProvider` - Alchemy RPC
- `RPCFailoverManager` - Multi-provider failover

**Key Methods:**
```python
async def get_block_number() -> int
async def get_transaction(tx_hash: str) -> Dict
async def get_balance(address: str) -> int
```

**Usage Example:**
```python
from src.providers import InfuraProvider, RPCFailoverManager

# Failover setup
manager = RPCFailoverManager([
    (10, InfuraProvider()),
    (20, AlchemyProvider()),
    (30, AnkrProvider())
])

# Automatic failover
block_number = await manager.execute_with_failover('get_block_number')
```

---

### 5. DetectionRepository

**Purpose:** Persist detection data (clean architecture)

**Implementations:**
- `SQLDetectionRepository` - PostgreSQL
- `InMemoryDetectionRepository` - Testing

**Key Methods:**
```python
async def save_detection(detection: OneHopDetectionCreate) -> int
async def get_detections(filters: OneHopDetectionFilter) -> List
async def save_intermediate_address(address_data: IntermediateAddressCreate) -> str
```

**Usage Example:**
```python
from src.repositories import SQLDetectionRepository
from models.schemas import OneHopDetectionCreate

repo = SQLDetectionRepository(db_manager)

# Save detection
detection = OneHopDetectionCreate(
    whale_address=whale,
    intermediate_address=intermediate,
    confidence=85,
    ...
)
detection_id = await repo.save_detection(detection)
```

---

### 6. PriceProvider

**Purpose:** Fetch token prices

**Implementations:**
- `CoinGeckoProvider` - CoinGecko API

**Key Methods:**
```python
async def get_price(token_address: str, vs_currency: str = 'usd') -> Decimal
async def get_eth_price() -> Decimal
```

**Usage Example:**
```python
from src.providers import CoinGeckoProvider

prices = CoinGeckoProvider()
eth_price = await prices.get_eth_price()
token_price = await prices.get_price('0x...')
```

---

## Migration Guide

### Migrating from TelegramNotifier to NotificationProvider

**Before:**
```python
from src.notifications.telegram_notifier import TelegramNotifier

notifier = TelegramNotifier()
await notifier.send_whale_onehop_alert(...)
```

**After:**
```python
from src.providers import TelegramProvider

notifier = TelegramProvider()
await notifier.send_whale_onehop_alert(...)
```

**Benefits:**
- ✅ Can easily add Discord/Email
- ✅ Can use MultiChannelNotifier
- ✅ Same interface across all providers

---

## Configuration Examples

### Production Setup with All Features

```python
import redis.asyncio as aioredis
from models.db_connection import create_async_db_manager

from src.providers import (
    TelegramProvider,
    MultiChannelNotifier,
    EtherscanProvider,
    CompositeDataProvider,
    RPCFailoverManager,
    InfuraProvider,
    AlchemyProvider,
    CoinGeckoProvider
)
from src.storages import RedisCooldownStorage
from src.repositories import SQLDetectionRepository

# Notifications
telegram = TelegramProvider()
# discord = DiscordProvider()  # Can add
notifier = MultiChannelNotifier([telegram])

# Cooldown storage (Redis for distributed)
redis_client = await aioredis.from_url('redis://localhost')
cooldown = RedisCooldownStorage(redis_client)

# Blockchain data (multi-provider)
data_provider = CompositeDataProvider([
    (10, EtherscanProvider(network='ethereum')),
    (20, AlchemyProvider(network='ethereum'))
])

# RPC (failover)
rpc = RPCFailoverManager([
    (10, InfuraProvider()),
    (20, AlchemyProvider())
])

# Prices
prices = CoinGeckoProvider()

# Repository
db = create_async_db_manager(settings)
repo = SQLDetectionRepository(db)

# Use in whale watcher
watcher = SimpleWhaleWatcher(
    notifier=notifier,
    data_provider=data_provider,
    rpc_provider=rpc,
    repository=repo,
    cooldown_storage=cooldown,
    price_provider=prices
)
```

### Development/Testing Setup

```python
from src.providers import TelegramProvider
from src.storages import InMemoryCooldownStorage
from src.repositories import InMemoryDetectionRepository

# Simple in-memory setup
notifier = TelegramProvider()
cooldown = InMemoryCooldownStorage()
repo = InMemoryDetectionRepository()

watcher = SimpleWhaleWatcher(
    notifier=notifier,
    data_provider=EtherscanProvider(),
    repository=repo,
    cooldown_storage=cooldown
)
```

---

## Benefits Summary

| Problem | Before | After |
|---------|--------|-------|
| **Add Discord** | Copy entire TelegramNotifier | Create DiscordProvider |
| **Multi-chain** | Hardcoded Etherscan URLs | EtherscanProvider('base') |
| **Cooldown persistence** | Lost on restart | RedisCooldownStorage |
| **RPC failover** | Single provider | RPCFailoverManager |
| **Testing** | Mock entire classes | Use InMemory implementations |
| **Distributed** | Not possible | Redis/Database storage |

---

## Next Steps

1. **Integrate abstractions into SimpleWhaleWatcher**
   - Update constructor to accept providers
   - Replace direct TelegramNotifier calls

2. **Add more providers**
   - DiscordProvider
   - EmailProvider
   - SlackProvider

3. **Enhance existing providers**
   - Add full Web3.py integration to RPC providers
   - Add batch operations to price providers

4. **Add metrics**
   - Track provider success/failure rates
   - Monitor failover events
   - Alert on provider health issues

---

## References

- **Design Patterns:** Strategy, Repository, Composite
- **Architecture:** Clean Architecture, Dependency Injection
- **Testing:** Test doubles (mocks, stubs, fakes)
