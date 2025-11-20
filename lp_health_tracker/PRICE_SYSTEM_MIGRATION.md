# Price System Migration Guide

## 🔄 Унификация системы получения цен завершена

**Дата:** September 13, 2025  
**Статус:** ✅ COMPLETED

### Что изменилось

**До унификации** (3 отдельных компонента):
- `PriceOracle` (defi_utils.py) - CoinGecko API
- `LiveDataProvider` (data_providers.py) - CoinGecko + DeFi Llama APR  
- `PriceStrategyManager` (price_strategy_manager.py) - fallback логика с заглушками

**После унификации** (1 объединенный компонент):
- ✅ `PriceStrategyManager` - **главный интерфейс** со всей функциональностью
- ⚠️ `PriceOracle` - **DEPRECATED**
- ⚠️ `LiveDataProvider` - **DEPRECATED**

### 🚀 Новая функциональность в PriceStrategyManager

#### Интегрированные возможности:
- ✅ **CoinGecko API** (из PriceOracle)
- ✅ **DeFi Llama APR API** (из LiveDataProvider) 
- ✅ **Кеширование с TTL** (60 секунд)
- ✅ **Fallback логика** между источниками
- ✅ **Параллельное получение цен**
- ✅ **Статистика надежности источников**

#### Новые методы:
```python
# Получение APR для пулов
manager.get_pool_apr('WETH-USDC')  # Возвращает 0.04 (4% APR)

# Отчет о надежности источников  
manager.get_source_reliability_report()  
```

### 📖 Migration Guide

#### Если вы использовали PriceOracle:

**❌ Старый код:**
```python
from src.defi_utils import PriceOracle

oracle = PriceOracle()
price = oracle.get_token_price_coingecko('ETH')
```

**✅ Новый код:**
```python
from src.price_strategy_manager import get_price_manager

manager = get_price_manager()
price = manager.get_token_price('ETH')
```

#### Если вы использовали LiveDataProvider:

**❌ Старый код:**
```python
from src.data_providers import LiveDataProvider

provider = LiveDataProvider()
prices = provider.get_current_prices(pool_config)
apr = provider.get_pool_apr(pool_config)
```

**✅ Новый код:**
```python
from src.price_strategy_manager import get_price_manager

manager = get_price_manager()

# Получение цен
symbols = ['WETH', 'USDC']
prices = manager.get_multiple_prices(symbols)

# Получение APR
apr = manager.get_pool_apr('WETH-USDC')
```

### 🏗️ Архитектурные преимущества

#### Принцип "модули максимально независимы" сохранен:
- ✅ PriceStrategyManager не зависит от YAML конфигурации
- ✅ Разумные defaults встроены в код
- ✅ Конфигурация опциональна через конструктор
- ✅ Zero external dependencies (кроме requests/aiohttp)

#### Fallback последовательность:
1. **on_chain_uniswap** - наиболее актуальные данные
2. **coingecko_api** - реальные рыночные цены ✅ REAL API
3. **coinmarketcap_api** - резервный источник
4. **cached_prices** - кешированные fallback значения

### 📊 Текущее использование в проекте

**✅ main.py уже использует новую систему:**
```python
from src.price_strategy_manager import get_price_manager

price_manager = get_price_manager()
current_prices = await price_manager.get_multiple_prices_parallel_async(symbols_only)
```

### 🧹 Cleanup Status

- ✅ PriceStrategyManager обновлен с реальной функциональностью
- ✅ PriceOracle помечен как DEPRECATED  
- ✅ LiveDataProvider помечен как DEPRECATED
- ✅ Документация обновлена
- ✅ Migration guide создан

### 🚫 Не удаляйте старые классы

**Важно:** PriceOracle и LiveDataProvider пока не удалены, только помечены как deprecated. Это обеспечивает:
- Совместимость с существующим кодом
- Возможность постепенного перехода
- Возможность тестирования новой системы

### ⚡ Performance Benefits

- **Кеширование**: Избегает повторных API вызовов в течение 60 секунд
- **Параллельная обработка**: ThreadPoolExecutor + async для множественных токенов  
- **Smart fallback**: Автоматическое переключение при сбоях API

### 📈 Reliability Benefits

- **Статистика источников**: Отслеживание успешности каждого источника
- **Graceful degradation**: Система продолжает работать даже при сбоях основных API
- **Fallback APR**: Разумные значения по умолчанию основанные на реальных данных

---

**Рекомендация:** Используйте `get_price_manager()` для всех новых разработок. Старые классы поддерживаются для совместимости, но не рекомендуются для нового кода.
