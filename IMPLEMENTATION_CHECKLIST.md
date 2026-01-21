# 📋 COLLECTIVE WHALE ANALYSIS - IMPLEMENTATION CHECKLIST

## ✅ STEP 1: Database Layer [COMPLETED]
- [x] PostgreSQL настроен и работает
- [x] Alembic миграция создана (`2025_12_03_1816-66a854bd3a29_add_accumulation_metrics_table.py`)
- [x] Таблица `accumulation_metrics` создана в БД
- [x] SQLAlchemy модель `AccumulationMetric` добавлена в `models/database.py`
- [x] Pydantic schemas добавлены в `models/schemas.py`
- [x] Repository создан: `src/repositories/accumulation_repository.py`

**Статус:** ✅ ЗАВЕРШЕНО

---

## 🔄 STEP 2: Тестирование Repository [IN PROGRESS]

### Что нужно сделать:

- [ ] Запустить тесты: `pytest tests/unit/test_accumulation_repository.py -v`
- [ ] Проверить что все 4 теста проходят:
  - [ ] test_save_metric
  - [ ] test_get_latest_score
  - [ ] test_get_latest_score_nonexistent
  - [ ] test_get_trend

### Команда для запуска:
```bash
cd C:\Users\annam\Documents\DeFi-RAG-Project\whale_tracker
pytest tests/unit/test_accumulation_repository.py -v
```

### Критерий успеха:
✅ Все тесты зелёные (passed)

**Статус:** 🔄 ОЖИДАЕТ ЗАПУСКА ТЕСТОВ

---

## ⏳ STEP 3: MulticallClient [PENDING]

### Что нужно создать:

**Файл:** `src/data/multicall_client.py`

**Зачем:** Batch запросы балансов (1000 адресов за 2 RPC calls вместо 1000)

### Ключевые методы:
- `get_balances_batch(addresses, network)` → Dict[str, int]
- `get_historical_balances(addresses, block_number)` → Dict[str, int]
- `get_latest_block(network)` → int

### Подготовка:
1. [ ] Установить: `pip install multicall`
2. [ ] Создать файл `src/data/multicall_client.py`
3. [ ] Реализовать методы по ТЗ
4. [ ] Протестировать с 3 известными адресами

### Тест вручную:
```python
# test_multicall_manual.py
addresses = [
    "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Vitalik
    "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B",  # Tornado Cash
    "0x00000000219ab540356cBB839Cbe05303d7705Fa",  # ETH2 Deposit
]
balances = await client.get_balances_batch(addresses, "ethereum")
```

### Критерий успеха:
✅ Получены реальные балансы для 3 адресов

**Статус:** ⏳ ОЖИДАЕТ НАЧАЛА

**Время:** 2-3 часа

---

## ⏳ STEP 4: WhaleListProvider [PENDING]

### Что нужно создать:

**Файл:** `src/data/whale_list_provider.py`

**Зачем:** Источник топ-100 holder адресов (для MVP)

### Подход:
1. [ ] Создать класс `WhaleListProvider`
2. [ ] Заполнить `ETHEREUM_TOP_100` список (hardcoded для MVP)
3. [ ] Реализовать `get_top_holders(asset, limit)`
4. [ ] Реализовать `filter_exchanges(addresses)`

### Где взять адреса:
- https://etherscan.io/accounts (топ-100 holders)
- Вручную скопировать адреса
- Убедиться что это НЕ биржи

### Критерий успеха:
✅ Метод `get_top_holders("ETH", 100)` возвращает 100 валидных адресов

**Статус:** ⏳ ОЖИДАЕТ НАЧАЛА

**Время:** 1-2 часа

---

## ⏳ STEP 5: AccumulationScoreCalculator [PENDING]

### Что нужно создать:

**Файл:** `src/analytics/accumulation_score.py`

**Зачем:** Основная бизнес-логика - расчёт accumulation score

### Алгоритм:
1. [ ] Получить список whale адресов (WhaleListProvider)
2. [ ] Получить текущие балансы (MulticallClient)
3. [ ] Получить балансы 30 дней назад (MulticallClient)
4. [ ] Рассчитать score по формуле
5. [ ] Сохранить в БД (AccumulationRepository)

### Формула:
```
score = Σ(Participation_i × BalanceChange_i)

где:
- Participation_i = Balance_i / Total_Supply
- BalanceChange_i = (Balance_now - Balance_30d) / Balance_now
- Нормализация: clamp к [-1, 1]
```

### Тест вручную:
```python
score = await calculator.calculate_score("ethereum", period_days=30, limit=10)
print(f"Score: {score:.4f}")  # Должно быть 0.0-1.0
```

### Критерий успеха:
✅ Получен score для Ethereum (например 0.65), сохранен в repository

**Статус:** ⏳ ОЖИДАЕТ НАЧАЛА

**Время:** 3-4 часа

---

## ⏳ STEP 6: Integration в main.py [PENDING]

### Что нужно изменить:

**Файлы:**
1. `main.py` - добавить collective analysis
2. `config/settings.py` - добавить настройки

### Изменения в main.py:
1. [ ] Инициализация компонентов в `WhaleTrackerOrchestrator.__init__()`
2. [ ] Создать метод `run_collective_analysis()`
3. [ ] Добавить в scheduler (каждый час)

### Изменения в config/settings.py:
```python
# Collective Whale Analysis
ACCUMULATION_ANALYSIS_ENABLED: bool = True
ACCUMULATION_ANALYSIS_INTERVAL_HOURS: int = 1
ACCUMULATION_WHALE_LIMIT: int = 100
ACCUMULATION_PERIOD_DAYS: int = 30

# Alert thresholds
ACCUMULATION_ALERT_HIGH: float = 0.7
ACCUMULATION_ALERT_LOW: float = 0.3
```

### Запуск:
```bash
# Test mode
python main.py --once

# Production mode
python main.py
```

### Критерий успеха:
✅ Видим в логах: "🐋 Running collective whale analysis..."
✅ Видим: "✅ ETH Accumulation Score: 0.XXXX"
✅ Данные сохраняются в PostgreSQL

**Статус:** ⏳ ОЖИДАЕТ НАЧАЛА

**Время:** 1 час

---

## 📊 ИТОГОВАЯ ПРОВЕРКА

### После завершения всех шагов:

**1. Проверить систему:**
```bash
python main.py
```

**2. Ожидаемые логи (каждый час):**
```
🐋 Running collective whale analysis...
Step 1: Fetching whale addresses...
Step 2: Fetching current balances...
Step 3: Calculating historical block number...
Step 4: Fetching historical balances...
Step 5: Computing accumulation score...
✅ Score: 0.7823, Total change: 45678.12
✅ Metric saved to database
✅ ETH Accumulation Score: 0.7823 (accumulating)
```

**3. Проверить БД:**
```sql
SELECT * FROM accumulation_metrics 
ORDER BY calculated_at DESC 
LIMIT 10;
```

**4. Проверить Telegram:**
- Если score > 0.7: "🐋 ETHEREUM STRONG ACCUMULATION"
- Если score < 0.3: "⚠️ ETHEREUM DISTRIBUTION ALERT"

---

## 🚀 PROGRESS TRACKER

| Step | Статус | Время | Приоритет |
|------|--------|-------|-----------|
| STEP 1: Database Layer | ✅ DONE | - | HIGH |
| STEP 2: Repository Tests | 🔄 IN PROGRESS | 30 min | HIGH |
| STEP 3: MulticallClient | ⏳ TODO | 2-3 hrs | HIGH |
| STEP 4: WhaleListProvider | ⏳ TODO | 1-2 hrs | HIGH |
| STEP 5: Calculator | ⏳ TODO | 3-4 hrs | HIGH |
| STEP 6: Integration | ⏳ TODO | 1 hr | HIGH |

**Общее время:** 8-10 часов (можно разбить на 2-3 дня)

---

## 📝 NOTES

### Важные замечания:
1. **MVP подход:** Начинаем с 100 адресов, потом масштабируем до 1000
2. **Historical balances:** Для MVP можно использовать mock данные
3. **Archive node:** Нужен только для production (исторические балансы)
4. **RPC limits:** Начинаем с малого (10 адресов), потом увеличиваем

### Возможные проблемы:
- ❌ Нет Etherscan API key → Hardcoded list
- ❌ RPC rate limits → Начать с 10-100 адресов
- ❌ Historical balances → Mock данные для MVP

---

## 🎯 NEXT ACTION

**СЕЙЧАС:** Запустить тесты STEP 2

```bash
cd C:\Users\annam\Documents\DeFi-RAG-Project\whale_tracker
pytest tests/unit/test_accumulation_repository.py -v
```

Если тесты проходят → Переходим к STEP 3 (MulticallClient)
