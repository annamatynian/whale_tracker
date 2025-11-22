# Whale Tracker - Project Plan

## Оглавление
- [Vision & Edge](#vision--edge)
- [Архитектура системы](#архитектура-системы)
- [Согласованные технические решения](#согласованные-технические-решения)
- [Модульная структура](#модульная-структура)
- [Фазы развития](#фазы-развития)

---

## Vision & Edge

### Основная идея
Whale Tracker - это система мониторинга активности крупных держателей криптовалюты с **уникальным фокусом на one-hop tracking** как конкурентное преимущество.

### Наш Edge (конкурентное преимущество)

**Проблема с существующими решениями (включая Arkham):**
```
Обычный трекер показывает:
"Vitalik отправил 1000 ETH на адрес 0xabc123..."

НО НЕ показывает автоматически:
"...и 0xabc123 отправил 1000 ETH на Binance через 15 минут"
```

**Наше решение:**
- Автоматическое отслеживание транзакций через промежуточные адреса
- ~80% опытных китов используют промежуточные адреса
- Мы даем **заблаговременное предупреждение** о возможном дампе

### Ключевые принципы

1. **Максимальная модульность** - каждый компонент работает независимо и тестируется отдельно
2. **YAML-first конфигурация** - немедленная реализация для избежания болезненного рефакторинга
3. **Тестирование на каждом шаге** - unit тесты перед переходом к следующей части
4. **Инфраструктура на будущее** - создаем структуру для Фаз 2-4 даже если сейчас не используем

---

## Архитектура системы

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Main Orchestrator                        │
│                    (main.py + APScheduler)                   │
└──────────────┬──────────────────────────────────────────────┘
               │
       ┌───────┴────────┐
       │                │
       ▼                ▼
┌─────────────┐  ┌──────────────┐
│ Config      │  │ Web3Manager  │
│ (YAML+.env) │  │ (RPC failover)│
└─────────────┘  └──────────────┘
                        │
       ┌────────────────┼────────────────┐
       │                │                │
       ▼                ▼                ▼
┌──────────────┐ ┌─────────────┐ ┌──────────────┐
│ WhaleConfig  │ │WhaleAnalyzer│ │SimpleWhale   │
│ (Exchanges DB)│ │(Statistics) │ │Watcher (MVP) │
└──────────────┘ └─────────────┘ └──────┬───────┘
                                         │
                                         ▼
                                  ┌──────────────┐
                                  │ Telegram     │
                                  │ Notifier     │
                                  └──────────────┘
```

### Data Flow

```
1. APScheduler trigger (каждые 15 минут)
           ↓
2. SimpleWhaleWatcher.monitor_all_whales()
           ↓
3. Для каждого кита:
   ├─ Web3Manager.get_balance()
   ├─ Web3Manager.get_recent_transactions()
   └─ WhaleAnalyzer.detect_anomaly()
           ↓
4. Если anomaly detected:
   ├─ WhaleConfig.classify_destination()
   ├─ One-hop detection (check intermediate addresses)
   └─ TelegramNotifier.send_alert()
```

---

## Согласованные технические решения

### 1. Конфигурация: YAML + .env

**Почему YAML:**
- Иерархическая структура
- Environment-specific overrides (dev/prod)
- Легко читается и редактируется
- Избегаем болезненного рефакторинга в будущем

**Структура:**
```
config/
├── base.yaml              # Базовая конфигурация
├── environments/
│   ├── development.yaml   # Dev overrides
│   └── production.yaml    # Prod overrides
└── settings.py            # Pydantic models + загрузка
```

**Приоритет переменных:**
```
.env variables > environment YAML > base.yaml
```

### 2. Web3 RPC: Cascading Failover

**Схема:**
```
Primary: Infura → Fallback: Alchemy → Last resort: Ankr
```

**Реализовано в:** `src/core/web3_manager.py`

**Преимущества:**
- High availability (99.9%+)
- Автоматическое переключение при сбоях
- Mock mode для тестирования без API кредитов

### 3. Уведомления: Telegram-first

**Почему Telegram:**
- Instant notifications на мобильный
- Бесплатно и надежно
- API простой и стабильный
- Whale-specific форматирование алертов

**Реализовано в:** `src/notifications/telegram_notifier.py`

### 4. Статистический анализ: Rolling Average + Threshold Multiplier

**Алгоритм** (из whale_agent):
```python
avg_amount = mean(last_10_transactions)
threshold = avg_amount * 1.3  # 30% выше среднего
is_anomaly = current_amount > threshold
```

**Реализовано в:** `src/analyzers/whale_analyzer.py`

**Почему это работает:**
- Адаптируется к активности кита
- Не требует machine learning
- Низкий false positive rate

---

## Модульная структура

### Core Modules

#### 1. Web3Manager (`src/core/web3_manager.py`)
**Ответственность:**
- RPC connection management с failover
- Получение балансов, транзакций, блоков
- Mock mode для тестирования

**Тесты:** 15 unit tests ✓

#### 2. WhaleConfig (`src/core/whale_config.py`)
**Ответственность:**
- База данных известных exchange адресов (30+ адресов)
- Классификация destination адресов
- Оценка dump risk

**Тесты:** 30 unit tests ✓

### Analyzers

#### 3. WhaleAnalyzer (`src/analyzers/whale_analyzer.py`)
**Ответственность:**
- Детекция аномалий через rolling average
- Confidence scoring
- Transaction history tracking

**Тесты:** 27 unit tests ✓

### Monitors

#### 4. SimpleWhaleWatcher (`src/monitors/simple_whale_watcher.py`)
**Ответственность:**
- Основной мониторинг китов
- One-hop detection (MVP + roadmap для advanced)
- Координация между компонентами

**Особенности:**
- 950+ строк кода
- 570+ строк подробной документации по one-hop
- 10 advanced signals для будущих фаз

**Тесты:** 19 unit tests ✓

### Notifications

#### 5. TelegramNotifier (`src/notifications/telegram_notifier.py`)
**Ответственность:**
- Отправка whale-specific алертов
- Alert cooldown (предотвращение спама)
- Форматирование сообщений

**Тесты:** 13 unit tests ✓

### Orchestration

#### 6. Main Orchestrator (`main.py`)
**Ответственность:**
- Component initialization
- APScheduler integration (periodic monitoring)
- Graceful shutdown (SIGINT/SIGTERM)
- CLI interface

**Тесты:** 19 unit tests ✓

---

## Фазы развития

### Phase 1: Simple Whale Tracker (MVP) - ТЕКУЩАЯ ✓

**Цель:** Базовый мониторинг с простым one-hop detection

**Функционал:**
- Периодическая проверка балансов китов
- Детекция больших транзакций
- Статистические аномалии
- Базовый one-hop (time correlation)
- Telegram alerts

**Статус:** РЕАЛИЗОВАНО
- Все компоненты созданы
- 139 unit тестов (все passing)
- Готово к первому запуску

### Phase 2: Advanced One-Hop + Price Impact

**Цель:** Sophisticated one-hop detection + отслеживание влияния на цену

**Новый функционал:**
- 10 advanced signals для one-hop:
  1. Time correlation (adaptive 5-30 min window)
  2. Gas price correlation
  3. Nonce tracking (strongest signal)
  4. Amount correlation + split detection
  5. Intermediate address profiling
  6. Network clustering (graph analysis)
  7. Multi-hop detection (2-3-4 hops)
  8. DEX interaction patterns
  9. Cross-chain bridge tracking
  10. Privacy protocol detection

- Price impact tracking:
  - Цена токена до транзакции
  - Цена через 1h, 6h, 24h после
  - Корреляция с китовой активностью

**Требует:**
- Database (PostgreSQL для graph queries)
- CoinGecko/DEXScreener API
- Graph analysis библиотеки (NetworkX)

**Документация:** См. `docs/ONE_HOP_TRACKING.md` (подробно)

### Phase 3: Pattern Recognition

**Цель:** Machine learning для распознавания паттернов поведения китов

**Функционал:**
- Классификация китов по behavior patterns:
  - "Accumulator" (покупает на падениях)
  - "Dumper" (продает на росте)
  - "Market Maker" (двусторонняя активность)
  - "Wash Trader" (круговые транзакции)

- Предсказание действий на основе истории
- Кластеризация связанных адресов

**Требует:**
- Historical data (минимум 3+ месяца)
- Scikit-learn / TensorFlow
- Feature engineering

### Phase 4: AI Analysis

**Цель:** LLM-based анализ и insights

**Функционал:**
- Автоматическая генерация инсайтов о поведении китов
- Natural language alerts
- Correlation с внешними событиями (новости, social sentiment)
- Рекомендации по торговым действиям

**Требует:**
- OpenAI/Anthropic API
- News aggregation APIs
- Social sentiment APIs

---

## Текущий статус и next steps

См. `docs/IMPLEMENTATION_STATUS.md` для детального статуса.

**Immediate next steps:**
1. Первый запуск MVP и проверка
2. Создание .env с реальными ключами
3. Мониторинг 2-3 китов в dev режиме
4. Сбор первых данных для Phase 2

**Medium term (1-2 недели):**
1. Реализация database layer (PostgreSQL)
2. Начало работы над advanced one-hop signals
3. Integration с CoinGecko для цен

**Long term (1-2 месяца):**
1. Pattern recognition (Phase 3)
2. Расширение списка мониторимых китов
3. Multi-chain support (Base, Arbitrum)

---

## Ключевые решения и их обоснование

### Почему APScheduler вместо Celery?
- Легче в setup
- Достаточно для MVP
- Можем мигрировать на Celery позже если нужна distributed система

### Почему Telegram вместо Discord/Slack?
- Мгновенные push notifications
- Проще API
- Удобнее для личного использования

### Почему PostgreSQL для Phase 2?
- Нужны graph queries для network analysis
- JSON support для гибких schema
- Production-ready и масштабируемый

### Почему YAML + Pydantic?
- Type safety с Pydantic models
- Валидация на старте приложения
- IDE autocomplete работает

---

**Версия документа:** 1.0
**Дата создания:** 2025-11-21
**Последнее обновление:** 2025-11-21
**Автор:** Claude (на основе обсуждения с пользователем)
