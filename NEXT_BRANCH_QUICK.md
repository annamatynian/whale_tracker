# 🎯 QUICK START для новой ветки

## ТЫ ЗДЕСЬ:
✅ STEP 1-2 DONE (Database + Tests)
⏳ STEP 3 NEXT (MulticallClient)

## ЧТО ДЕЛАТЬ:

### 1. Создать файл:
```
src/data/multicall_client.py
```

### 2. Класс MulticallClient с методами:
- `get_balances_batch(addresses, network)` → Dict[str, int]
- `get_historical_balances(addresses, block_number)` → Dict[str, int] (MVP: mock)
- `get_latest_block(network)` → int

### 3. Multicall3 Address:
```
0xcA11bde05977b3631167028862bE2a173976CA11
```

### 4. Тест:
```python
# test_multicall_manual.py
addresses = [
    "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Vitalik
    "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B",  # Tornado
]
balances = await client.get_balances_batch(addresses)
print(balances)  # Should show real balances
```

## ВАЖНЫЕ ФАЙЛЫ:
- `INSTRUCTION_FOR_NEXT_BRANCH.md` ← ПОЛНАЯ ИНСТРУКЦИЯ
- `IMPLEMENTATION_CHECKLIST.md` ← ДЕТАЛЬНЫЙ ПЛАН
- `docs/COLLECTIVE_WHALE_ANALYSIS_PLAN.md` Section 8.2 ← CODE EXAMPLES

## КРИТЕРИЙ УСПЕХА:
✅ Получить реальные балансы для 3 Ethereum адресов

## ВРЕМЯ: 2-3 часа

## КОМАНДЫ:
```bash
pip install multicall
mkdir -p src/data
touch src/data/__init__.py
touch src/data/multicall_client.py
python test_multicall_manual.py
```

**Вперед! 🚀**
