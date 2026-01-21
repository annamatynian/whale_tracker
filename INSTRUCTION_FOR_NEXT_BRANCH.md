# 🚀 ИНСТРУКЦИЯ ДЛЯ CLAUDE В НОВОЙ ВЕТКЕ

## 📍 КОНТЕКСТ: ГДЕ МЫ СЕЙЧАС

### ✅ ЧТО ЗАВЕРШЕНО (STEPS 1-2)

**STEP 1: Database Layer** ✅
- Создана SQLAlchemy модель `AccumulationMetric` в `models/database.py`
- Добавлены Pydantic schemas в `models/schemas.py`
- Создан Repository в `src/repositories/accumulation_repository.py`
- Применена Alembic миграция для таблицы `accumulation_metrics`

**STEP 2: Repository Tests** ✅
- Все 4 теста проходят: `pytest tests/unit/test_accumulation_repository.py -v`
- 0 warnings после исправлений
- Обновлен код до современных стандартов:
  - SQLAlchemy 2.0 (`from sqlalchemy.orm import declarative_base`)
  - Pydantic V2 (`@field_validator` вместо `@validator`)
  - DateTime с UTC (`datetime.now(UTC)` вместо `datetime.utcnow()`)

**Измененные файлы:**
- ✅ `models/database.py` - добавлена модель AccumulationMetric
- ✅ `models/schemas.py` - обновлены все validators на Pydantic V2
- ✅ `src/repositories/accumulation_repository.py` - обновлен datetime
- ✅ `tests/unit/test_accumulation_repository.py` - добавлен import asyncio, обновлен datetime

---

## 🎯 СЛЕДУЮЩИЙ ШАГ: STEP 3 - MulticallClient

### Цель:
Создать клиент для batch запросов балансов Ethereum адресов используя Multicall3 контракт.

### Зачем:
Без Multicall: 1000 адресов = 1000 RPC calls (медленно + rate limits)
С Multicall: 1000 адресов = ~2 RPC calls (быстро + эффективно)

### Что создать:

**Файл:** `src/data/multicall_client.py`

**Ключевые компоненты:**

```python
class MulticallClient:
    """
    Batch blockchain queries используя Multicall3.
    
    Multicall3 Address (универсальный):
    0xcA11bde05977b3631167028862bE2a173976CA11
    """
    
    MULTICALL3_ADDRESS = "0xcA11bde05977b3631167028862bE2a173976CA11"
    
    def __init__(self, web3_manager):
        self.web3_manager = web3_manager
        self.w3 = web3_manager.w3
        # Создать contract instance с Multicall3 ABI
    
    async def get_balances_batch(
        self,
        addresses: List[str],
        network: str = "ethereum",
        chunk_size: int = 500
    ) -> Dict[str, int]:
        """
        Получить ETH балансы для множества адресов.
        
        Args:
            addresses: Список Ethereum адресов
            network: "ethereum" (для MVP)
            chunk_size: Макс адресов за один вызов
        
        Returns:
            {address: balance_in_wei}
        """
        # Разбить на chunks
        # Для каждого chunk создать calls для Multicall3.aggregate3()
        # Вернуть {address: balance}
    
    async def get_historical_balances(
        self,
        addresses: List[str],
        block_number: int,
        network: str = "ethereum"
    ) -> Dict[str, int]:
        """
        Получить балансы на конкретный исторический блок.
        
        ВАЖНО: Требует archive node (Alchemy/Infura paid tier)
        Для MVP: можно возвращать текущие балансы (mock)
        """
    
    async def get_latest_block(self, network: str = "ethereum") -> int:
        """Получить текущий номер блока."""
```

### Технические детали:

**Multicall3 ABI (минимальный):**
```python
MULTICALL3_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"name": "target", "type": "address"},
                    {"name": "allowFailure", "type": "bool"},
                    {"name": "callData", "type": "bytes"}
                ],
                "name": "calls",
                "type": "tuple[]"
            }
        ],
        "name": "aggregate3",
        "outputs": [
            {
                "components": [
                    {"name": "success", "type": "bool"},
                    {"name": "returnData", "type": "bytes"}
                ],
                "name": "returnData",
                "type": "tuple[]"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]
```

**Важные моменты:**
1. Использовать `asyncio.to_thread()` для синхронных Web3 вызовов
2. Обрабатывать chunks по 500 адресов (избегать RPC limits)
3. Graceful error handling (если один адрес fails, продолжить с другими)
4. Для MVP: `get_historical_balances` может возвращать текущие балансы (mock данные)

### Тестирование:

**Создать:** `test_multicall_manual.py` в корне проекта

```python
import asyncio
from src.core.web3_manager import Web3Manager
from src.data.multicall_client import MulticallClient
from config.settings import Settings

async def test_multicall():
    settings = Settings()
    web3_manager = Web3Manager(settings)
    client = MulticallClient(web3_manager)
    
    # Известные адреса с балансами
    addresses = [
        "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Vitalik
        "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B",  # Tornado Cash
        "0x00000000219ab540356cBB839Cbe05303d7705Fa",  # ETH2 Deposit
    ]
    
    print("Testing Multicall with 3 known addresses...")
    balances = await client.get_balances_batch(addresses, "ethereum")
    
    for addr, balance in balances.items():
        print(f"{addr}: {balance / 10**18:.4f} ETH")
    
    print("\n✅ Success! Multicall is working.")

if __name__ == "__main__":
    asyncio.run(test_multicall())
```

**Запустить:**
```bash
pip install multicall  # Если еще не установлено
python test_multicall_manual.py
```

**Критерий успеха:** Видим реальные балансы для 3 адресов

---

## 📁 СТРУКТУРА ПРОЕКТА

```
whale_tracker/
├── src/
│   ├── data/                    ← СОЗДАТЬ ЭТУ ДИРЕКТОРИЮ
│   │   ├── __init__.py         ← СОЗДАТЬ
│   │   └── multicall_client.py ← СОЗДАТЬ (STEP 3)
│   ├── repositories/
│   │   └── accumulation_repository.py ✅
│   └── core/
│       └── web3_manager.py ✅ (уже существует)
├── tests/
│   └── unit/
│       └── test_accumulation_repository.py ✅
├── test_multicall_manual.py    ← СОЗДАТЬ для ручного теста
└── models/
    ├── database.py ✅
    └── schemas.py ✅
```

---

## 📚 СПРАВОЧНЫЕ ДОКУМЕНТЫ

**Основные файлы в проекте:**
1. `IMPLEMENTATION_CHECKLIST.md` - детальный план всех 6 шагов
2. `QUICK_START.md` - быстрая шпаргалка
3. `BUSINESS_ALIGNMENT_ANALYSIS.md` - анализ соответствия бизнес-стратегии
4. `WARNINGS_FIXED.md` - что было исправлено в STEP 2

**Бизнес-документы:**
1. `docs/COLLECTIVE_WHALE_ANALYSIS_PLAN.md` - полный технический план
2. `/mnt/project/Edge.docx` - бизнес-преимущества
3. `/mnt/project/MVP_PLAN.docx` - MVP стратегия

---

## 🎯 ПРИОРИТЕТЫ И ПОДХОД

### MVP Принципы:
1. ✅ **Фокус на результат**, не на красоту кода
2. ✅ **Начать с малого**: 10 адресов → 100 → 1000
3. ✅ **Iterative development**: поэтапно, с тестами
4. ✅ **Mock данные для MVP**: historical balances можно мокировать

### Для STEP 3 конкретно:
- Начать с 3 известных адресов для теста
- Потом масштабировать до 100
- Для MVP: `get_historical_balances` может возвращать текущие балансы
- Archive node понадобится только для production

---

## ⚠️ ИЗВЕСТНЫЕ ПРОБЛЕМЫ

1. **Multicall library:** Может быть синхронной, нужен `asyncio.to_thread()`
2. **RPC limits:** Chunking по 500 адресов обязателен
3. **Archive node:** Для historical balances нужен платный Alchemy/Infura tier
   - Решение для MVP: mock данные (возвращать текущие балансы)

---

## ✅ КРИТЕРИИ УСПЕХА STEP 3

После завершения должно работать:

```python
client = MulticallClient(web3_manager)

# 1. Получить балансы 3 адресов
balances = await client.get_balances_batch(addresses=[...], network="ethereum")
print(balances)  # {addr: balance_in_wei, ...}

# 2. Получить текущий блок
block = await client.get_latest_block("ethereum")
print(block)  # 18500000 (example)

# 3. Historical balances (для MVP - mock)
hist_balances = await client.get_historical_balances(addresses, block_number)
print(hist_balances)  # {addr: balance_in_wei, ...}
```

---

## 🚀 ДЕЙСТВИЯ ДЛЯ НОВОЙ ВЕТКИ

1. **Прочитать этот файл полностью** ✅
2. **Создать директорию** `src/data/`
3. **Создать файл** `src/data/multicall_client.py`
4. **Реализовать** класс `MulticallClient` с 3 методами
5. **Создать** `test_multicall_manual.py` для ручного теста
6. **Запустить тест** с 3 известными адресами
7. **Масштабировать** до 10, потом 100 адресов

---

## 💡 КОНТЕКСТ ДЛЯ ПОНИМАНИЯ

### Бизнес-проблема:
```
Сейчас: Индивидуальные whale alerts → 70% шум
Решение: Collective analysis → 90% точность

Пример:
- Кит A купил 50 ETH
- Без контекста: "Покупай!" (может быть ошибкой)
- С контекстом: "Collective score = 0.82" = HIGH CONFIDENCE
```

### Что мы строим:
```
STEP 1-2 ✅: Database для хранения collective scores
STEP 3 ⏳: MulticallClient для получения балансов
STEP 4: WhaleListProvider для списка китов
STEP 5: Calculator для расчета score (КЛЮЧЕВОЙ!)
STEP 6: Integration в main.py для automation
```

### MVP подход:
- 100 адресов (не 1000)
- Ethereum only (не BTC/USDT)
- Mock historical data (не archive node)
- Hourly updates (не real-time)

**Потом масштабируем!**

---

## 📊 PROGRESS TRACKER

```
[████████░░░░░░░░░░░░] 33% Complete

✅ STEP 1: Database Layer       - DONE
✅ STEP 2: Repository Tests     - DONE
⏳ STEP 3: MulticallClient      - CURRENT (2-3 hrs)
⏳ STEP 4: WhaleListProvider    - TODO (1-2 hrs)
⏳ STEP 5: Calculator           - TODO (3-4 hrs) ⭐ KEY
⏳ STEP 6: Integration          - TODO (1 hr)
```

---

## 🎯 ВРЕМЯ НА РЕАЛИЗАЦИЮ

**STEP 3 (MulticallClient):** 2-3 часа чистой работы

**Breakdown:**
- 1 час: Создание класса + основные методы
- 30 мин: Multicall3 ABI + contract integration
- 30 мин: Chunking logic
- 30 мин: Тестирование с реальными адресами
- 30 мин: Error handling + polish

---

## 📞 ЕСЛИ ВОЗНИКНУТ ВОПРОСЫ

**Справочные файлы:**
- `IMPLEMENTATION_CHECKLIST.md` - детальный план
- `QUICK_START.md` - быстрые команды
- `docs/COLLECTIVE_WHALE_ANALYSIS_PLAN.md` - полная спецификация (Section 8 - Code Examples)

**Ключевые концепции:**
- Multicall3 = универсальный контракт для batch queries
- Address: `0xcA11bde05977b3631167028862bE2a173976CA11`
- Работает на всех major EVM chains

---

## ✅ CHECKLIST ДЛЯ НАЧАЛА РАБОТЫ

- [ ] Прочитал этот файл
- [ ] Понял цель STEP 3 (batch balance queries)
- [ ] Знаю структуру проекта
- [ ] Знаю критерии успеха
- [ ] Готов создавать `src/data/multicall_client.py`

---

**🚀 ГОТОВ? START STEP 3!**

**Удачи, Claude из будущей ветки! Ты можешь! 💪**

---

**P.S.** Если нужно больше деталей по Multicall3, смотри:
- `docs/COLLECTIVE_WHALE_ANALYSIS_PLAN.md` Section 8.2
- Там есть полные примеры кода!
