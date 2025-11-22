# Phase 5 Selective Pull Guide

## 🎯 Цель
Подтянуть **только** новые файлы Phase 5 (AI Analyzer + Market Data) **БЕЗ** перезаписи сохраненных данных.

## 📁 Что будет обновлено

### ✅ НОВЫЕ ФАЙЛЫ (создаются впервые)
```
src/services/
  ├── market_data_service.py    ← Market Data Service (CoinGecko, DefiLlama, Fear&Greed)
  └── __init__.py               ← Exports для сервисов

tests/unit/
  ├── test_market_data_service.py  ← 18 unit tests для MarketDataService
  └── test_whale_statistics.py     ← 7 unit tests для whale statistics

tests/integration/
  └── test_e2e_phase5.py          ← 2 E2E теста полного пайплайна
```

### 🔄 ОБНОВЛЕННЫЕ ФАЙЛЫ (безопасные изменения)
```
src/ai/
  ├── whale_ai_analyzer.py      ← Добавлена автоматическая enrichment функция
  ├── __init__.py               ← Lazy loading для Gemini
  └── providers/__init__.py     ← Lazy loading фикс

src/repositories/
  ├── in_memory_detection_repository.py  ← get_whale_statistics() метод
  ├── sql_detection_repository.py        ← get_whale_statistics() метод
  └── __init__.py                         ← Новые exports

src/abstractions/
  └── detection_repository.py   ← Документация для get_whale_statistics()

main.py                         ← async setup(), MarketDataService инициализация

config/base.yaml                ← Phase 5 конфигурация (market_data settings)

tests/unit/
  ├── test_repositories.py      ← Исправлены regression failures
  └── test_blockchain_providers.py  ← Исправлены старые тесты
```

## 🛡️ Что НЕ ТРОГАЕТСЯ (ваши данные в безопасности)

### ❌ НЕ ОБНОВЛЯЕТСЯ
```
database/                       ← База данных с детекциями
  └── whale_tracker.db

.env                           ← API ключи и секреты
.env.local

data/                          ← Любые сохраненные данные
logs/                          ← Логи
cache/                         ← Кеш

config/
  ├── local.yaml               ← Локальные переопределения (если есть)
  └── production.yaml          ← Production конфиг (если есть)

models/                        ← Database models (не изменялись)
src/monitors/                  ← SimpleWhaleWatcher (не изменялся)
```

## 🚀 Как использовать

### Вариант 1: Автоматический pull (рекомендуется)
```bash
# Windows
pull_phase5_files.bat

# Linux/Mac
chmod +x pull_phase5_files.bat
./pull_phase5_files.bat
```

### Вариант 2: Ручной pull (для продвинутых)
```bash
# 1. Fetch изменения
git fetch origin claude/whale-stats-market-data-01Ef7fuKFCHUVsJbcVFf4Sg5

# 2. Pull конкретные файлы
git checkout origin/claude/whale-stats-market-data-01Ef7fuKFCHUVsJbcVFf4Sg5 -- src/services/
git checkout origin/claude/whale-stats-market-data-01Ef7fuKFCHUVsJbcVFf4Sg5 -- src/ai/whale_ai_analyzer.py
# ... и т.д. (см. pull_phase5_files.bat)
```

### Вариант 3: Проверить изменения ДО pull
```bash
# Посмотреть что изменится
git fetch origin claude/whale-stats-market-data-01Ef7fuKFCHUVsJbcVFf4Sg5
git diff origin/claude/whale-stats-market-data-01Ef7fuKFCHUVsJbcVFf4Sg5 -- main.py
git diff origin/claude/whale-stats-market-data-01Ef7fuKFCHUVsJbcVFf4Sg5 -- config/base.yaml
```

## ✅ После Pull

### 1. Проверка изменений
```bash
git status
git diff
```

### 2. Запуск тестов
```bash
# E2E тесты Phase 5
python -m pytest tests/integration/test_e2e_phase5.py -v

# Все unit тесты
python -m pytest tests/unit/ -v
```

### 3. Обновление конфигурации (опционально)
```yaml
# config/base.yaml - новые настройки
phases:
  phase5_market_data:
    enabled: true              # Включить market data
    update_interval: 300       # Обновлять каждые 5 минут
    request_timeout: 30        # Таймаут API запросов
    max_retries: 3            # Количество повторов
```

### 4. Проверка работы
```bash
# Запустить систему
python main.py

# Проверить в логах:
# - "MarketDataService started (background updates every 5min)"
# - "WhaleAIAnalyzer initialized: whale_history=enabled, market_data=enabled"
```

## 📊 Архитектурные изменения

### До Phase 5:
```
SimpleWhaleWatcher → AI Analyzer → Decision
                     (без контекста)
```

### После Phase 5:
```
SimpleWhaleWatcher → Context (пустой)
                          ↓
                    AI Analyzer (автоматически обогащает)
                          ↓
                    _enrich_context()
                     ├─→ DetectionRepository (whale history)
                     └─→ MarketDataService (market data)
                          ↓
                    AI Analysis (с полным контекстом)
                          ↓
                    Decision (BUY/SELL/MONITOR)
```

## 🔧 Troubleshooting

### Проблема: "git checkout: error: pathspec 'src/services' did not match"
```bash
# Решение: убедитесь что сделали fetch
git fetch origin claude/whale-stats-market-data-01Ef7fuKFCHUVsJbcVFf4Sg5
```

### Проблема: "Conflict: local changes would be overwritten"
```bash
# Решение: сохраните свои изменения
git stash
# Выполните pull
./pull_phase5_files.bat
# Восстановите свои изменения
git stash pop
```

### Проблема: Тесты падают после pull
```bash
# 1. Проверьте зависимости
pip install -r requirements.txt

# 2. Проверьте database
python -c "from models.db_connection import DatabaseManager; print('DB OK')"

# 3. Запустите только новые тесты
python -m pytest tests/integration/test_e2e_phase5.py -v
```

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте `git status` и `git diff`
2. Убедитесь что база данных не повреждена
3. Проверьте логи: `logs/whale_tracker.log`
4. Запустите тесты для диагностики

## ✨ Что получите после Pull

✅ **Market Data Service**
- Автоматическое обновление цен ETH каждые 5 минут
- Fear & Greed Index
- Market sentiment и trend detection
- Graceful degradation при сбоях API

✅ **AI Analyzer с автоматическим обогащением**
- Whale history из базы данных
- Market data для контекста
- Улучшенная точность AI решений

✅ **Comprehensive E2E тесты**
- Полный пайплайн протестирован
- Graceful degradation проверен
- Моки для надежного тестирования

---

**Итого:** Безопасный pull всех Phase 5 улучшений без риска потери данных! 🎉
