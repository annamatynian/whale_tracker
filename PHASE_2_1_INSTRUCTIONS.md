# ФАЗА 2.1 COMPLETE ✅ - AccumulationScoreCalculator Refactor

## ЧТО СДЕЛАНО

### 1. Файлы изменены:
- ✅ `src/analyzers/accumulation_score_calculator.py` - REFACTORED
- ✅ `tests/unit/test_accumulation_calculator.py` - UPDATED

### 2. Ключевые изменения:

#### В `accumulation_score_calculator.py`:
1. **Добавлен `SnapshotRepository`** в `__init__`
2. **Устранён Survival Bias** - UNION подход:
   ```python
   # БЫЛО: Только current whales
   whale_addresses = [w['address'] for w in current_whales]
   
   # СТАЛО: UNION (current OR historical)
   current_addresses = {w['address'] for w in current_whales}
   historical_top = await snapshot_repo.get_addresses_in_top_at_time(...)
   all_addresses = current_addresses | historical_top  # FIX!
   ```
3. **Убрана зависимость от archive node**:
   ```python
   # БЫЛО: archive node
   historical_balances = await multicall.get_historical_balances(
       addresses=whale_addresses,
       block_number=historical_block  # ← Requires archive node!
   )
   
   # СТАЛО: snapshots
   historical_snapshots = await snapshot_repo.get_snapshots_batch_at_time(
       addresses=list(all_addresses),
       timestamp=lookback_time,
       tolerance_hours=1
   )
   ```

#### В `test_accumulation_calculator.py`:
1. Добавлен `snapshot_repo` в фикстуры
2. Обновлены все тесты под новый API
3. Добавлен тест для проверки UNION логики

## СЛЕДУЮЩИЕ ШАГИ (В ТЕКУЩЕЙ СЕССИИ)

### ⚠️ КРИТИЧНО - ЗАПУСТИ ТЕСТЫ:
```bash
cd C:\Users\annam\Documents\DeFi-RAG-Project\whale_tracker
pytest tests/unit/test_accumulation_calculator.py -v
```

### 🔴 Если тесты падают:
1. **Скопируй ПОЛНЫЙ output pytest** и покажи Claude
2. Claude исправит проблемы
3. Повторяй пока все тесты не пройдут

### ✅ Если тесты проходят:
1. Коммит изменений:
   ```bash
   git add src/analyzers/accumulation_score_calculator.py
   git add tests/unit/test_accumulation_calculator.py
   git commit -m "feat: Fix Survival Bias in AccumulationScoreCalculator
   
   - Add snapshot_repo for historical balances
   - Implement UNION approach (current ∪ historical addresses)
   - Eliminate archive node dependency
   - Update tests for new API
   
   GEMINI: 'Survival Bias is critical flaw - you miss whales who exited'
   "
   ```

2. Переходи к **ФАЗЕ 2.2 - Hourly Snapshot Job**

## ТЕХНИЧЕСКИЕ ДЕТАЛИ

### Старый подход (BROKEN - Survival Bias):
```python
current_whales = get_top_1000()  # [Alice, Bob, Charlie]
# Анализируем ТОЛЬКО current whales
# ❌ ПРОБЛЕМА: Не видим Dave, который ВЫШЕЛ из топа (продал!)
```

### Новый подход (FIXED):
```python
current_whales = get_top_1000()      # {Alice, Bob, Charlie}
historical_whales = get_top_1000_24h_ago()  # {Alice, Bob, Dave}

all_addresses = current | historical  # {Alice, Bob, Charlie, Dave}
# ✅ Теперь видим что Dave продал и вышел!
```

## ПРОВЕРКА

Прежде чем идти дальше, убедись что:
- ✅ pytest tests/unit/test_accumulation_calculator.py проходит
- ✅ Синтаксис Python правильный
- ✅ Git коммит сделан

---

## NEXT: ФАЗА 2.2 - Hourly Snapshot Job
См. `PHASE_2_2_INSTRUCTIONS.md` (будет создан после тестов)
