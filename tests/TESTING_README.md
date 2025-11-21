# Abstraction Tests

Comprehensive test suite for Whale Tracker abstractions.

## Test Files

### Unit Tests (`tests/unit/`)

- **`test_notification_providers.py`** - NotificationProvider abstraction and implementations
  - TelegramProvider tests
  - MultiChannelNotifier tests
  - Message formatting tests

- **`test_cooldown_storage.py`** - CooldownStorage abstraction and implementations
  - InMemoryCooldownStorage tests
  - Cooldown logic tests
  - Cleanup and expiration tests

- **`test_repositories.py`** - DetectionRepository abstraction and implementations
  - InMemoryDetectionRepository tests
  - Detection CRUD operations
  - Filtering and pagination tests
  - Statistics tests

- **`test_blockchain_providers.py`** - BlockchainDataProvider abstraction and implementations
  - EtherscanProvider tests
  - CompositeDataProvider tests
  - Failover logic tests

### Smoke Tests (`tests/`)

- **`test_abstractions_smoke.py`** - Quick validation tests
  - Import verification
  - Basic instantiation
  - Simple operations
  - Integration smoke tests

## Running Tests

### All Tests

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/abstractions --cov=src/providers --cov=src/storages --cov=src/repositories
```

### Specific Test Files

```bash
# Notification providers only
pytest tests/unit/test_notification_providers.py -v

# Cooldown storage only
pytest tests/unit/test_cooldown_storage.py -v

# Repositories only
pytest tests/unit/test_repositories.py -v

# Blockchain providers only
pytest tests/unit/test_blockchain_providers.py -v

# Smoke tests only (fast)
pytest tests/test_abstractions_smoke.py -v
```

### Quick Smoke Test

```bash
# Run only smoke tests for fast validation
pytest tests/test_abstractions_smoke.py -v --tb=short
```

### By Test Class

```bash
# Test only TelegramProvider
pytest tests/unit/test_notification_providers.py::TestTelegramProvider -v

# Test only InMemoryCooldownStorage
pytest tests/unit/test_cooldown_storage.py::TestInMemoryCooldownStorage -v
```

### By Test Method

```bash
# Test specific functionality
pytest tests/unit/test_notification_providers.py::TestTelegramProvider::test_send_message_success -v
```

## Test Coverage

Expected coverage:
- **Abstractions**: 100% (all are interfaces)
- **Providers**: 80-90% (excluding network I/O)
- **Storages**: 95%+ (in-memory fully tested)
- **Repositories**: 95%+ (in-memory fully tested)

## Test Statistics

```
Total Tests: 100+
- Notification tests: 20+
- Cooldown tests: 25+
- Repository tests: 30+
- Blockchain provider tests: 20+
- Smoke tests: 15+
```

## Writing New Tests

### Template for New Provider Tests

```python
import pytest
from src.abstractions.your_abstraction import YourAbstraction
from src.providers.your_provider import YourProvider

class TestYourProvider:
    """Test YourProvider implementation."""

    def test_initialization(self):
        """Provider initializes correctly."""
        provider = YourProvider()
        assert provider.provider_name == 'your_provider'

    @pytest.mark.asyncio
    async def test_basic_operation(self):
        """Basic operation works."""
        provider = YourProvider()
        result = await provider.some_method()
        assert result is not None
```

## CI/CD Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# .github/workflows/test.yml
- name: Run Abstraction Tests
  run: |
    pytest tests/test_abstractions_smoke.py -v
    pytest tests/unit/ -v --cov=src
```

## Mocking External Services

Tests use mocks for external services:

```python
from unittest.mock import Mock, AsyncMock, patch

# Mock HTTP requests
with patch('aiohttp.ClientSession'):
    result = await provider.some_api_call()

# Mock async functions
provider.some_method = AsyncMock(return_value=expected_value)
```

## Test Data

Sample test data:
- Ethereum addresses: `'0x' + '1' * 40`
- Transaction hashes: `'0x' + 'a' * 64`
- Timestamps: `datetime.utcnow()`
- Amounts: `Decimal('100.0')`

## Debugging Tests

```bash
# Run with print statements visible
pytest tests/unit/test_notification_providers.py -v -s

# Run with PDB on failure
pytest tests/unit/test_notification_providers.py --pdb

# Run last failed tests only
pytest tests/ --lf
```

## Performance Tests

```bash
# Run with timing information
pytest tests/ --durations=10

# Run with performance profiling
pytest tests/ --profile
```

## Known Issues

None currently.

## Contributing

When adding new abstractions:
1. Create abstract base class in `src/abstractions/`
2. Create concrete implementation in `src/providers/` or `src/storages/`
3. Add unit tests in `tests/unit/`
4. Add smoke test in `tests/test_abstractions_smoke.py`
5. Update this README

## Questions?

See main documentation: `src/ABSTRACTIONS_README.md`
