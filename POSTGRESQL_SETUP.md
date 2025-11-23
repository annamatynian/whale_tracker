# PostgreSQL Setup Guide

## 🎉 Хорошие новости: PostgreSQL УЖЕ ИНТЕГРИРОВАН!

PostgreSQL поддержка полностью реализована в обеих ветках:
- ✅ `claude/create-new-branch-01DNkMvr3wgmDyXprLxsQvAb` (текущая)
- ✅ `claude/whale-stats-market-data-01C8bzF8ssV6r4s5SkvBMXGf`

Просто нужно **активировать** PostgreSQL вместо SQLite!

## 📂 Файлы PostgreSQL инфраструктуры

Все эти файлы УЖЕ ЕСТЬ в вашем проекте:

```
whale_tracker/
├── models/
│   ├── database.py          # 5 SQLAlchemy моделей (PostgreSQL/SQLite)
│   │   ├── OneHopDetection  (29 полей)
│   │   ├── IntermediateAddress (25 полей)
│   │   ├── Transaction (19 полей)
│   │   ├── WhaleAlert (14 полей)
│   │   └── SignalMetrics (13 полей)
│   │
│   ├── db_connection.py     # Connection manager (sync + async)
│   │   ├── DatabaseConfig
│   │   ├── DatabaseManager (sync)
│   │   └── AsyncDatabaseManager (async)
│   │
│   ├── schemas.py           # Pydantic validation schemas
│   └── README.md           # Документация
│
├── alembic/                 # Database migrations
│   ├── env.py              # Migration environment
│   ├── versions/           # Migration scripts
│   └── README.md
│
├── init_database.py        # ✅ SQLite initialization
└── init_postgres.py        # ✅ PostgreSQL initialization (только что создан)
```

## 🔄 Переключение на PostgreSQL

### Шаг 1: Установите PostgreSQL

**Windows:**
```bash
# Скачайте с https://www.postgresql.org/download/windows/
# Или используйте Chocolatey:
choco install postgresql
```

**Linux:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

### Шаг 2: Создайте базу данных

```bash
# Windows (PowerShell):
psql -U postgres -c "CREATE DATABASE whale_tracker;"

# Linux/Mac:
sudo -u postgres psql -c "CREATE DATABASE whale_tracker;"
```

### Шаг 3: Обновите .env файл

Откройте ваш `.env` файл и измените:

```bash
# БЫЛО (SQLite):
DB_TYPE=sqlite
SQLITE_PATH=data/database/whale_tracker.db

# СТАЛО (PostgreSQL):
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=whale_tracker
DB_USER=postgres
DB_PASSWORD=ваш_пароль_postgres  # ← ВАЖНО!

# Connection pool (опционально)
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_ECHO=false  # true для debug
```

### Шаг 4: Инициализируйте PostgreSQL

```bash
python init_postgres.py
```

**Ожидаемый вывод:**
```
================================================================================
🐘 INITIALIZING WHALE TRACKER DATABASE (PostgreSQL)
================================================================================

1️⃣ Database Configuration:
   Type: PostgreSQL
   Host: localhost:5432
   Database: whale_tracker
   User: postgres

2️⃣ Testing PostgreSQL connection...
   ✅ Connected successfully!
   PostgreSQL version: PostgreSQL 15.3

3️⃣ Creating database tables...
   ✅ Tables created successfully!

4️⃣ Created Tables (5 total):
   📋 one_hop_detections (29 columns)
   📋 intermediate_addresses (25 columns)
   📋 whale_alerts (14 columns)
   📋 transactions (19 columns)
   📋 signal_metrics (13 columns)

5️⃣ Table Status:
   📊 one_hop_detections: 0 rows
   📊 intermediate_addresses: 0 rows
   📊 whale_alerts: 0 rows
   📊 transactions: 0 rows
   📊 signal_metrics: 0 rows

================================================================================
✅ POSTGRESQL DATABASE INITIALIZATION COMPLETE
================================================================================
```

### Шаг 5: Запустите мониторинг

```bash
python main.py
```

Все whale detections будут автоматически сохраняться в PostgreSQL! 🎉

## 📊 Просмотр данных в PostgreSQL

### Подключение к базе данных

```bash
psql -U postgres -d whale_tracker
```

### Полезные SQL запросы

```sql
-- Все one-hop detections с высокой уверенностью
SELECT
    whale_address,
    intermediate_address,
    total_confidence,
    whale_amount_eth,
    detected_at
FROM one_hop_detections
WHERE total_confidence >= 80
ORDER BY detected_at DESC
LIMIT 10;

-- Статистика по китам
SELECT
    whale_address,
    COUNT(*) as total_detections,
    AVG(total_confidence) as avg_confidence,
    SUM(whale_amount_eth) as total_volume_eth
FROM one_hop_detections
GROUP BY whale_address
ORDER BY total_detections DESC;

-- Недавние алерты
SELECT * FROM whale_alerts
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;

-- Top промежуточные адреса
SELECT
    address,
    total_tx_count,
    confidence_score,
    first_seen,
    last_seen
FROM intermediate_addresses
ORDER BY total_tx_count DESC
LIMIT 20;
```

## 🔧 Различия SQLite vs PostgreSQL

| Функция | SQLite | PostgreSQL |
|---------|--------|------------|
| **Установка** | ✅ Не требуется | ❌ Требует сервера |
| **Файл** | ✅ Один файл .db | ❌ Сервер + данные |
| **Concurrent access** | ❌ Один писатель | ✅ Множественные |
| **Производительность** | ✅ Быстрый (< 100K записей) | ✅ Масштабируемый (миллионы) |
| **Full-text search** | ⚠️ Базовый | ✅ Продвинутый |
| **JSON queries** | ⚠️ Ограниченный | ✅ Полный |
| **Indexes** | ✅ Базовые | ✅ Продвинутые (BRIN, GiST, GIN) |
| **Replication** | ❌ Нет | ✅ Есть |
| **Use case** | Development/Testing | Production |

## 🎯 Когда использовать PostgreSQL

**Используйте PostgreSQL если:**
- ✅ Планируете хранить > 100,000 whale detections
- ✅ Нужен доступ с нескольких машин одновременно
- ✅ Требуется high availability
- ✅ Планируете analytics/reporting/dashboards
- ✅ Production deployment
- ✅ Интеграция с BI tools (Metabase, Grafana, etc.)

**Используйте SQLite если:**
- ✅ Development/testing
- ✅ MVP/прототип
- ✅ Один пользователь
- ✅ Небольшой объем данных (< 100K записей)
- ✅ Не нужна высокая нагрузка

## 🔄 Миграция данных SQLite → PostgreSQL

Если у вас уже есть данные в SQLite и вы хотите перенести в PostgreSQL:

```bash
# 1. Export SQLite to CSV
sqlite3 data/database/whale_tracker.db <<EOF
.headers on
.mode csv
.output one_hop_detections.csv
SELECT * FROM one_hop_detections;
.output intermediate_addresses.csv
SELECT * FROM intermediate_addresses;
.quit
EOF

# 2. Import to PostgreSQL
psql -U postgres -d whale_tracker <<EOF
COPY one_hop_detections FROM '/path/to/one_hop_detections.csv' DELIMITER ',' CSV HEADER;
COPY intermediate_addresses FROM '/path/to/intermediate_addresses.csv' DELIMITER ',' CSV HEADER;
EOF
```

## 📝 Alembic Migrations (Advanced)

Для управления схемой базы данных через миграции:

```bash
# Создать новую миграцию
alembic revision --autogenerate -m "Add new field to OneHopDetection"

# Применить миграцию
alembic upgrade head

# Откатить миграцию
alembic downgrade -1

# Посмотреть историю миграций
alembic history
```

## ✅ Проверка работы

После настройки PostgreSQL, запустите тесты:

```bash
# Тесты должны работать с обеими базами данных
python test_real_api.py
```

Тест #9 (Database Operations) проверит:
- ✅ Создание записей (CREATE)
- ✅ Чтение записей (READ)
- ✅ Обновление записей (UPDATE)
- ✅ Валидацию Pydantic схем

## 🚨 Troubleshooting

### Ошибка: "FATAL: password authentication failed"

```bash
# Проверьте пароль в .env
DB_PASSWORD=ваш_пароль

# Сбросьте пароль (Windows):
psql -U postgres
ALTER USER postgres PASSWORD 'новый_пароль';
```

### Ошибка: "could not connect to server"

```bash
# Проверьте что PostgreSQL запущен
# Windows:
services.msc  # Найдите postgresql-x64-15

# Linux:
sudo systemctl status postgresql
sudo systemctl start postgresql
```

### Ошибка: "database 'whale_tracker' does not exist"

```bash
# Создайте базу данных
psql -U postgres -c "CREATE DATABASE whale_tracker;"
```

## 📚 Дополнительные ресурсы

- **PostgreSQL документация**: https://www.postgresql.org/docs/
- **SQLAlchemy ORM**: https://docs.sqlalchemy.org/
- **Alembic migrations**: https://alembic.sqlalchemy.org/
- **Pydantic validation**: https://docs.pydantic.dev/

---

**Резюме:** PostgreSQL УЖЕ ГОТОВ к использованию! Просто измените `DB_TYPE=postgresql` в `.env` и запустите `init_postgres.py`. 🚀
