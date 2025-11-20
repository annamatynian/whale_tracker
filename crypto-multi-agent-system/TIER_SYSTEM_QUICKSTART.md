# Tier + Tags System - QUICK START 🚀

## ✅ Готово к использованию!

Новая система **tier'ов + тегов** создана и протестирована.

---

## 🧪 Быстрый тест

```bash
cd C:\Users\annam\Documents\DeFi-RAG-Project\crypto-multi-agent-system

# Запустить все тесты
python test_tier_system_comprehensive.py
```

**Ожидаемый результат:** 6/6 tests passed ✅

---

## 💡 Базовое использование

```python
from agents.pump_analysis import TierScoringMatrix

# Создать анализатор
matrix = TierScoringMatrix()

# Проанализировать токен
result = matrix.analyze(
    volume_ratio=2.0,
    ratio_healthy=True,
    is_accelerating=True,
    acceleration_factor=2.5,
    volume_h1=50000,
    is_honeypot=False,
    is_open_source=True,
    buy_tax=2.0,
    sell_tax=5.0,
    data_completeness=0.95,
    token_symbol="TOKEN"
)

# Посмотреть результат
print(f"Tier: {result.tier}")
print(result.get_detailed_report())
```

---

## 📊 Что получаете

### Вместо одной цифры (балл):
```
Score: 85/105  # Непонятно, почему этот балл
```

### Теперь видите ВСЁ:
```
🏆 TIER: PREMIUM

📊 VOLUME:
  ✅ HEALTHY_VOLUME_RATIO    (2.0 in range 0.5-3.0)
  ✅ STRONG_ACCELERATION     (2.5x momentum)

📊 SECURITY:
  ✅ NOT_HONEYPOT           (Safe to trade)
  ✅ VERIFIED_CONTRACT      (Open source)
  ✅ LOW_TAXES              (2% / 5%)

📊 LIQUIDITY:
  ✅ LP_LOCKED_90%+         (95% locked)

📊 ONCHAIN:
  ✅ LOW_CONCENTRATION      (15% in top-10)

🎯 ACTION: 🚀 IMMEDIATE WATCH
```

---

## 🎯 Критерии Tier'ов

### 🏆 PREMIUM
**ВСЕ критерии:**
- LP locked 90%+
- Healthy volume ratio (0.5-3.0)
- Acceleration 2.0x+
- Not honeypot
- Low concentration (<20%)
- Verified contract
- Low taxes

### 💪 STRONG
**Минимум 5 из 7:**
- LP locked 50%+
- Healthy volume ratio
- Acceleration 1.5x+
- Not honeypot
- Moderate concentration (<40%)
- Verified contract
- Moderate taxes

### ⚡ SPECULATIVE
**Есть потенциал, но риски:**
- Acceleration есть
- LP частично locked
- Overheated ratio или high concentration
- Not honeypot
- High taxes

### 🚫 AVOID
**Хотя бы один критичный флаг:**
- Dead token (ratio < 0.5)
- Honeypot
- LP not locked (<20%)
- Critical concentration (>60%)
- No acceleration
- Extreme taxes (>50%)

---

## 🔄 Интеграция с Volume Analysis

В `volume_integration_patch.py` добавить:

```python
from agents.pump_analysis import TierScoringMatrix

# После получения volume метрик:
matrix = TierScoringMatrix()

tier_result = matrix.analyze(
    volume_ratio=metrics['volume_ratio'],
    ratio_healthy=metrics['volume_ratio_healthy'],
    ratio_overheated=metrics['volume_ratio_overheated'],
    ratio_dead=metrics['volume_ratio_dead'],
    is_accelerating=metrics['is_accelerating'],
    acceleration_factor=metrics['acceleration_factor'],
    volume_h1=volume_h1,
    
    # Security data (from GoPlus)
    is_honeypot=goplus_data['is_honeypot'],
    is_open_source=goplus_data['is_open_source'],
    buy_tax=goplus_data['buy_tax'],
    sell_tax=goplus_data['sell_tax'],
    
    # OnChain data (if available)
    onchain_analysis=onchain_result,
    
    # Metadata
    data_completeness=0.85,
    token_symbol=token_symbol,
    token_address=token_address
)

# Сохранить в report
discovery_report.tier_analysis = tier_result
```

---

## 📁 Файлы системы

```
agents/pump_analysis/
├── tier_system.py              # Базовые модели
├── tier_scoring_matrix.py      # Основная логика
└── realistic_scoring.py        # Legacy (баллы)

test_tier_system_comprehensive.py  # Тесты

docs/
└── TIER_SYSTEM_MIGRATION_COMPLETE.md  # Полная документация
```

---

## 🎉 Готово!

**Система tier'ов + тегов полностью работает.**

Запустите тест и посмотрите результаты:
```bash
python test_tier_system_comprehensive.py
```

После этого можем:
1. Интегрировать с Volume Analysis
2. Добавить в Telegram алерты
3. Сохранять в базу данных

**Что делаем дальше?** 🚀
