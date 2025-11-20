# 🤝 Contributing Guide - LP Health Tracker

Welcome to the LP Health Tracker development team! This guide will help you contribute effectively to the project.

## 🎯 Project Philosophy

### Core Principles

**1. Incremental Development**
- Small, testable modules over monolithic features
- Each commit should be immediately functional
- Avoid "big bang" integrations that are hard to debug

**2. Test-Driven Quality**
- All new features must include comprehensive tests
- Use pytest fixtures for isolation and repeatability
- Integration tests for end-to-end workflows

**3. Real-World Practicality**
- Focus on actual user problems in DeFi
- Prioritize features that provide measurable value
- Validate assumptions with real data

**4. Professional Standards**
- Production-ready code quality
- Comprehensive documentation
- Proper error handling and logging

## 🛠️ Development Setup

### Prerequisites

```bash
# Required software
Python 3.9+
Git 2.20+
VS Code or PyCharm (recommended)

# Recommended tools
pytest
black (code formatting)
mypy (type checking)
pre-commit (git hooks)
```

### Initial Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd lp_health_tracker

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -r test_requirements.txt

# 4. Setup environment
cp .env.example .env
# Edit .env with your API keys

# 5. Run initial tests
pytest

# 6. Verify setup
python run.py --test-config
```

## 📁 Project Structure

### Directory Layout

```
lp_health_tracker/
├── src/                          # Core application code
│   ├── main.py                   # Main agent entry point
│   ├── simple_multi_pool.py      # Multi-pool manager
│   ├── data_analyzer.py          # IL calculation engine
│   ├── data_providers.py         # Price data integration
│   ├── notification_manager.py   # Alert system
│   ├── position_manager.py       # Position persistence
│   ├── web3_utils.py            # Blockchain integration
│   └── defi_utils.py            # DeFi protocol utilities
├── tests/                        # Test suite
│   ├── conftest.py              # Shared test fixtures
│   ├── fixtures/                # Test data files
│   ├── test_*.py               # Unit and integration tests
│   └── test_future_features.py # Placeholder for new features
├── config/                       # Configuration management
│   └── settings.py              # Application settings
├── data/                        # Runtime data
│   ├── positions.json          # User positions
│   └── *.example               # Example configurations
├── docs/                        # Documentation
├── logs/                        # Application logs
└── *.md                         # Project documentation
```

### Module Responsibilities

**Core Engine (`src/`)**
- `main.py`: AsyncIO agent coordination
- `simple_multi_pool.py`: Multi-pool position management
- `data_analyzer.py`: Mathematical IL calculations

**Data Layer (`src/`)**
- `data_providers.py`: External API integration
- `position_manager.py`: JSON persistence and validation
- `web3_utils.py`: Blockchain connectivity

**Integration (`src/`)**
- `notification_manager.py`: Telegram and future alert channels
- `defi_utils.py`: Protocol-specific logic

## 🧪 Testing Guidelines

### Test Structure

```python
# tests/test_new_feature.py

import pytest
from src.new_feature import NewFeature

class TestNewFeature:
    \"\"\"Test suite for NewFeature functionality.\"\"\"
    
    def test_basic_functionality(self, sample_data):
        \"\"\"Test basic feature operation.\"\"\"
        feature = NewFeature()
        result = feature.process(sample_data)
        
        assert result is not None
        assert isinstance(result, dict)
        assert 'expected_field' in result
    
    @pytest.mark.parametrize("input_value,expected", [
        (1.0, 0.0),
        (1.5, 0.02),
        (2.0, 0.057),
    ])
    def test_edge_cases(self, input_value, expected):
        \"\"\"Test various input scenarios.\"\"\"
        feature = NewFeature()
        result = feature.calculate(input_value)
        assert abs(result - expected) < 0.001
    
    @pytest.mark.integration
    def test_integration_with_existing_system(self, multi_pool_manager):
        \"\"\"Test integration with existing components.\"\"\"
        feature = NewFeature()
        result = feature.integrate_with(multi_pool_manager)
        assert result.success is True
```

### Testing Best Practices

**1. Use Fixtures for Data**
```python
# In conftest.py
@pytest.fixture
def sample_position():
    return {
        'name': 'Test Position',
        'initial_liquidity_a': 1.0,
        'initial_liquidity_b': 2000.0,
        'initial_price_a_usd': 2000.0,
        'initial_price_b_usd': 1.0
    }
```

**2. Mark Integration Tests**
```python
@pytest.mark.integration
@pytest.mark.slow
def test_live_api_integration():
    \"\"\"Tests that require external APIs.\"\"\"
    pass
```

**3. Test Error Conditions**
```python
def test_handles_invalid_input():
    \"\"\"Verify proper error handling.\"\"\"
    feature = NewFeature()
    
    with pytest.raises(ValueError, match="Invalid input"):
        feature.process(None)
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_data_analyzer.py

# Run with coverage
pytest --cov=src

# Run only integration tests
pytest -m integration

# Run excluding slow tests
pytest -m "not slow"

# Verbose output
pytest -v
```

## 🔄 Development Workflow

### 1. Planning Phase

**Before Starting Development:**
- Create GitHub issue describing the feature/bug
- Discuss approach in issue comments
- Break down large features into smaller tasks
- Identify affected components and tests

### 2. Implementation Phase

**Branch Naming Convention:**
```bash
feature/description-of-feature
bugfix/description-of-bug
improvement/description-of-improvement

# Examples:
git checkout -b feature/uniswap-v3-support
git checkout -b bugfix/il-calculation-precision
git checkout -b improvement/telegram-message-formatting
```

**Commit Message Format:**
```
type(scope): description

[optional body explaining the change]

[optional footer with breaking changes]
```

**Examples:**
```bash
feat(analyzer): add Uniswap V3 concentrated liquidity support

- Implement tick-based IL calculation
- Add position range tracking
- Update tests for V3 scenarios

fix(notifications): correct IL percentage formatting in alerts

- Fix decimal precision in Telegram messages
- Add unit tests for message formatting
- Resolve issue #23

refactor(tests): migrate validation scripts to pytest

- Convert test_stage1_final.py to proper pytest
- Add fixtures for isolation
- Remove deprecated validation scripts
```

### 3. Code Quality Standards

**Code Formatting:**
```bash
# Format code with black
black src/ tests/

# Check type hints
mypy src/

# Lint code
flake8 src/ tests/
```

**Code Review Checklist:**
- [ ] All tests pass (`pytest`)
- [ ] Code follows black formatting
- [ ] Type hints are present and correct
- [ ] Error handling is comprehensive
- [ ] Documentation is updated
- [ ] No breaking changes without discussion

### 4. Pull Request Process

**PR Template:**
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Integration tests updated if needed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Ready for review
```

## 🚀 Feature Development Guidelines

### Adding New Protocols

**1. Create Protocol Analyzer**
```python
# src/protocols/curve_analyzer.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class ProtocolAnalyzer(ABC):
    @abstractmethod
    def calculate_position_value(self, position: Dict) -> Dict[str, float]:
        pass
    
    @abstractmethod
    def calculate_fees_earned(self, position: Dict, days: int) -> float:
        pass

class CurveAnalyzer(ProtocolAnalyzer):
    def calculate_position_value(self, position: Dict) -> Dict[str, float]:
        # Curve-specific logic
        pass
```

**2. Register in Factory**
```python
# src/defi_utils.py
PROTOCOL_ANALYZERS = {
    'uniswap_v2': UniswapV2Analyzer,
    'curve': CurveAnalyzer,  # New protocol
    'balancer': BalancerAnalyzer
}
```

**3. Add Tests**
```python
# tests/test_curve_analyzer.py
def test_curve_position_calculation():
    analyzer = CurveAnalyzer()
    # Test curve-specific scenarios
```

### Adding New Data Providers

**1. Implement Provider Interface**
```python
# src/providers/defillama_provider.py
class DeFiLlamaProvider(DataProvider):
    async def get_token_price(self, symbol: str) -> float:
        # DeFiLlama API implementation
        pass
    
    async def get_pool_apy(self, pool_id: str) -> float:
        # APY data from DeFiLlama
        pass
```

**2. Add to Provider Strategy**
```python
# src/price_strategy_manager.py
class PriceStrategyManager:
    def __init__(self):
        self.providers = [
            CoinGeckoProvider(),
            DeFiLlamaProvider(),  # New provider
            MockDataProvider()    # Fallback
        ]
```

### Adding New Notification Channels

**1. Implement Notification Interface**
```python
# src/notifications/discord_notifier.py
class DiscordNotifier(NotificationProvider):
    async def send_message(self, message: str) -> bool:
        # Discord webhook implementation
        pass
    
    async def send_alert(self, alert_data: Dict) -> bool:
        # Format alert for Discord
        pass
```

**2. Add to Notification Manager**
```python
# src/notification_manager.py
class NotificationManager:
    def __init__(self):
        self.channels = [
            TelegramNotifier(),
            DiscordNotifier(),  # New channel
            EmailNotifier()
        ]
```

## 🐛 Debugging Guidelines

### Common Issues and Solutions

**1. Import Errors**
```python
# Problem: Module not found
# Solution: Check PYTHONPATH and relative imports

# Correct import pattern:
from src.data_analyzer import ImpermanentLossCalculator

# Not:
from data_analyzer import ImpermanentLossCalculator
```

**2. API Rate Limiting**
```python
# Problem: API calls failing
# Solution: Implement exponential backoff

import asyncio
import random

async def api_call_with_retry(self, func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await func()
        except RateLimitError:
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            await asyncio.sleep(wait_time)
    raise Exception("Max retries exceeded")
```

**3. Precision Issues in IL Calculation**
```python
# Problem: Floating point precision errors
# Solution: Use Decimal for financial calculations

from decimal import Decimal, getcontext

getcontext().prec = 28  # Set precision

def calculate_il_precise(initial_ratio: Decimal, current_ratio: Decimal) -> Decimal:
    price_ratio = current_ratio / initial_ratio
    il = 2 * (price_ratio.sqrt() / (1 + price_ratio)) - 1
    return abs(il) if il < 0 else Decimal('0')
```

### Debugging Tools

**1. Logging Configuration**
```python
# Debug mode setup
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.debug("Debugging information here")
```

**2. Test Debugging**
```bash
# Debug specific test
pytest tests/test_specific.py -v -s

# Debug with pdb
pytest tests/test_specific.py -v -s --pdb

# Debug on first failure
pytest tests/test_specific.py -v -x --pdb
```

## 📖 Documentation Standards

### Code Documentation

**1. Module Docstrings**
```python
\"\"\"
Module Name - Brief Description
==============================

Longer description of module purpose and functionality.

This module handles X, Y, and Z operations for the LP Health Tracker.
It provides the following key classes and functions:

- ClassName: Description of what it does
- function_name(): Description of key function

Author: Your Name
Version: 1.0.0
\"\"\"
```

**2. Class Documentation**
```python
class ImpermanentLossCalculator:
    \"\"\"
    Handles IL and P&L calculations for LP positions.
    
    This class implements the mathematical models for calculating
    Impermanent Loss based on price movements of token pairs in
    constant product AMM pools.
    
    Attributes:
        logger: Logger instance for debugging
        
    Example:
        >>> calculator = ImpermanentLossCalculator()
        >>> il = calculator.calculate_impermanent_loss(1.0, 1.5)
        >>> print(f"IL: {il:.2%}")
        IL: 0.62%
    \"\"\"
```

**3. Function Documentation**
```python
def calculate_impermanent_loss(
    self, 
    initial_price_ratio: float, 
    current_price_ratio: float
) -> float:
    \"\"\"
    Calculate Impermanent Loss based on price ratio change.
    
    Uses the standard IL formula for constant product AMMs:
    IL = 2 * (√(price_ratio) / (1 + price_ratio)) - 1
    
    Args:
        initial_price_ratio: Initial price ratio (token_a/token_b)
        current_price_ratio: Current price ratio (token_a/token_b)
        
    Returns:
        IL as positive decimal (0.05 for 5% loss)
        
    Raises:
        ValueError: If price ratios are negative or zero
        
    Example:
        >>> calc = ImpermanentLossCalculator()
        >>> il = calc.calculate_impermanent_loss(1.0, 2.0)
        >>> assert abs(il - 0.0572) < 0.001
    \"\"\"
```

### README Updates

When adding major features, update the main README.md:

1. **Features section**: Add new capabilities
2. **Installation**: Update if new dependencies added
3. **Configuration**: Document new settings
4. **Examples**: Add usage examples for new features

## 🚀 Release Process

### Version Numbering

Follow Semantic Versioning (SemVer):
- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **Major**: Breaking changes
- **Minor**: New features, backwards compatible
- **Patch**: Bug fixes, backwards compatible

### Release Checklist

**Pre-Release:**
- [ ] All tests pass
- [ ] Documentation updated
- [ ] Version number bumped
- [ ] CHANGELOG.md updated
- [ ] Security review completed

**Release:**
- [ ] Create release branch
- [ ] Final testing in staging environment
- [ ] Create GitHub release with notes
- [ ] Deploy to production
- [ ] Monitor for issues

## 🤝 Community Guidelines

### Getting Help

**Channels:**
- **GitHub Issues**: Bug reports and feature requests
- **Discussions**: Questions and general discussion
- **Discord/Telegram**: Real-time chat (if available)

**When Asking Questions:**
1. Check existing issues and documentation
2. Provide minimal reproducible example
3. Include relevant logs and error messages
4. Specify your environment (Python version, OS, etc.)

### Code of Conduct

**Expected Behavior:**
- Be respectful and inclusive
- Focus on constructive feedback
- Help others learn and grow
- Acknowledge contributions of others

**Unacceptable Behavior:**
- Harassment or discrimination
- Trolling or inflammatory comments
- Sharing private information without permission
- Any behavior that would be inappropriate in a professional setting

## 🎯 Contribution Opportunities

### Good First Issues

**Documentation:**
- Improve code comments and docstrings
- Add examples to README
- Create tutorial content

**Testing:**
- Add test cases for edge conditions
- Improve test coverage
- Add integration tests

**Features:**
- Small utility functions
- Additional data providers
- UI/UX improvements

### Advanced Contributions

**Core Features:**
- New protocol support (Uniswap V3, Curve, Balancer)
- Advanced analytics and ML models
- Performance optimizations

**Infrastructure:**
- CI/CD pipeline improvements
- Monitoring and alerting
- Scaling and deployment automation

---

Thank you for contributing to LP Health Tracker! Your efforts help make DeFi safer and more accessible for everyone. 🚀