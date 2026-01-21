# 🔒 FLOATING POINT PRECISION VULNERABILITY - ИСПРАВЛЕНИЕ

## Проблема (выявлена Gemini)

В `accumulation_score_calculator.py::_detect_lst_migration()` найдены две критические ошибки:

### 1. Логическая ошибка (строки 447-451)
```python
# ❌ НЕПРАВИЛЬНО - берется только текущий баланс, а не изменение!
weth_delta = Decimal(str(weth_now)) / Decimal('1e18')
steth_delta = Decimal(str(steth_now)) / Decimal('1e18') * steth_rate
```

**WHY BAD:** Функция должна детектировать МИГРАЦИЮ (изменение балансов), но код считает абсолютные значения.

### 2. Precision Vulnerability

```python
# Даже с Decimal, сравнение с допуском 0.01 ETH может давать false positives
gas_tolerance_eth = Decimal('0.01')  # ~$35
```

**WHY BAD:** 
- Wei = 256-bit int, но конвертация в float64 теряет младшие биты
- Накопленная ошибка округления может превысить 0.01 ETH для крупных балансов
- Пример: 10,000 ETH × 10^-16 (float64 epsilon) = 0.001 ETH ошибка → ложный пропуск миграции

## Исправление

### Шаг 1: Исправить логику расчета дельт

```python
async def _detect_lst_migration(
    self,
    addresses: List[str],
    eth_current: Dict[str, int],
    eth_historical: Dict[str, int],
    weth_current: Dict[str, int],
    steth_current: Dict[str, int],
    weth_historical: Dict[str, int],  # ✅ ДОБАВИТЬ
    steth_historical: Dict[str, int],  # ✅ ДОБАВИТЬ
    steth_rate: Decimal,
    time_window_hours: int = 1
) -> int:
    """Detect LST migration with ACCURATE delta calculation."""
    
    migration_count = 0
    
    # ✅ КРИТИЧНО: Все расчеты в Wei, конвертация в ETH только для display
    gas_tolerance_wei = int(Decimal('0.01') * Decimal('1e18'))  # 0.01 ETH in Wei
    
    for address in addresses:
        # Get balances in Wei
        eth_now_wei = eth_current.get(address, 0) or 0
        eth_before_wei = eth_historical.get(address, 0) or 0
        weth_now_wei = weth_current.get(address, 0) or 0
        weth_before_wei = weth_historical.get(address, 0) or 0  # ✅ ИСПРАВЛЕНО
        steth_now_wei = steth_current.get(address, 0) or 0
        steth_before_wei = steth_historical.get(address, 0) or 0  # ✅ ИСПРАВЛЕНО
        
        # ✅ ПРАВИЛЬНО: Рассчитываем ИЗМЕНЕНИЯ в Wei (без float!)
        eth_delta_wei = eth_now_wei - eth_before_wei
        weth_delta_wei = weth_now_wei - weth_before_wei
        
        # stETH конвертация с Decimal precision
        steth_now_eth_wei = int(Decimal(str(steth_now_wei)) * steth_rate)
        steth_before_eth_wei = int(Decimal(str(steth_before_wei)) * steth_rate)
        steth_delta_wei = steth_now_eth_wei - steth_before_eth_wei
        
        # Total wealth change (в Wei!)
        total_delta_wei = eth_delta_wei + weth_delta_wei + steth_delta_wei
        
        # ✅ КРИТИЧНО: Сравнение в Wei, без float!
        # Migration pattern: ETH↓, LST↑, net≈0
        if (eth_delta_wei < 0 and  # ETH went down
            (weth_delta_wei > 0 or steth_delta_wei > 0) and  # LST went up
            abs(total_delta_wei) < gas_tolerance_wei):  # Net change ≈ 0 (в Wei!)
            
            migration_count += 1
            
            # Display conversion (только для логов!)
            self.logger.info(
                f"LST Migration detected for {address[:10]}... "
                f"(ETH: {Decimal(eth_delta_wei)/Decimal('1e18'):+.4f}, "
                f"WETH: {Decimal(weth_delta_wei)/Decimal('1e18'):+.4f}, "
                f"stETH: {Decimal(steth_delta_wei)/Decimal('1e18'):+.4f} → "
                f"net: {Decimal(total_delta_wei)/Decimal('1e18'):+.4f})"
            )
    
    return migration_count
```

## Почему это исправление работает

### Precision Protection:
1. **Все сравнения в Wei** (256-bit int) → нет float округления
2. **Decimal только для stETH rate** → контролируемая precision
3. **Float только для display** → не влияет на логику

### Математическая точность:
```python
# ❌ ПЛОХО (старый код):
weth_delta = Decimal(str(weth_now)) / Decimal('1e18')  # ВСЕГДА > 0 если есть баланс!
# → Ложные миграции для всех адресов с WETH

# ✅ ХОРОШО (новый код):
weth_delta_wei = weth_now_wei - weth_before_wei  # Может быть < 0, = 0, > 0
# → Точно детектирует только ИЗМЕНЕНИЯ
```

### Test Cases:

```python
# Case 1: Реальная миграция (должна детектиться)
eth_before = 1000 ETH
eth_now = 0 ETH
steth_before = 0 stETH
steth_now = 1000 stETH
# → eth_delta = -1000, steth_delta = +1000, total = 0 ✅ МИГРАЦИЯ

# Case 2: Покупка stETH (НЕ миграция)
eth_before = 1000 ETH
eth_now = 500 ETH
steth_before = 0 stETH
steth_now = 400 stETH  # Купил меньше из-за slippage
# → eth_delta = -500, steth_delta = +400, total = -100 ❌ НЕ миграция

# Case 3: Precision edge case
eth_before = 10000.123456789012345678 ETH  # Все 18 знаков
eth_now = 0.123456789012345678 ETH
steth_now = 10000 stETH
# → В Wei: точно 10000000000000000000000 - 123456789012345678 = -9999876543210987654322
# → Никаких ошибок округления!
```

## Требуемые изменения в `calculate_accumulation_score()`

Добавить историческое получение WETH/stETH:

```python
# Шаг 5.5: Fetch HISTORICAL LST balances
historical_weth, historical_steth = await self._fetch_historical_lst_balances(
    addresses=list(all_addresses),
    timestamp=lookback_time,
    network=network
)

# Шаг 4.6: Update call
lst_migration_count = await self._detect_lst_migration(
    addresses=list(all_addresses),
    eth_current=current_balances,
    eth_historical=historical_balances,
    weth_current=weth_balances,
    weth_historical=historical_weth,  # ✅ ДОБАВИТЬ
    steth_current=steth_balances,
    steth_historical=historical_steth,  # ✅ ДОБАВИТЬ
    steth_rate=steth_rate,
    time_window_hours=1
)
```

## Статус

- [x] Проблема идентифицирована
- [ ] Код исправлен
- [ ] Unit тесты добавлены
- [ ] Integration тест с реальными Wei значениями

## References

- Ethereum Yellow Paper: Wei precision requirements
- Python Decimal documentation: Arbitrary precision arithmetic
- Gemini analysis: Floating point vulnerability report
