# 🐋 Whale Tracker - AWS EC2 Deployment Guide

Production-ready DeFi whale tracking system with automated alerts.

---

## 🎯 БЫСТРЫЙ СТАРТ (15 минут)

### На вашем EC2 инстансе:

```bash
# 1. Скачайте deployment script
wget https://raw.githubusercontent.com/YOUR_REPO/whale-tracker/main/deploy.sh
chmod +x deploy.sh

# 2. Запустите автоматический деплой
./deploy.sh

# 3. Настройте .env
nano .env
# Вставьте свои credentials (см. ниже)

# 4. Запустите
pm2 restart whale-tracker-scheduler
```

**Готово!** Вы будете получать push уведомления в Telegram.

---

## 📋 ЧТО НУЖНО ДЛЯ .ENV

```bash
# AWS RDS (ваша существующая база)
DB_HOST=your-db.rds.amazonaws.com
DB_PORT=5432
DB_NAME=whale_tracker  # Создайте новую БД!
DB_USER=postgres
DB_PASSWORD=your_password

# Ethereum RPC (бесплатный Alchemy)
ETH_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY

# Telegram (уже настроено)
TELEGRAM_BOT_TOKEN=8450952201:AAGbnQ6lhcI-fBSO-Vwmxyi-BjPx7nHwKsE
TELEGRAM_CHAT_ID=764547167
ENABLE_TELEGRAM=True
```

### Как создать новую БД без нового RDS:

```sql
-- Подключитесь к существующему RDS через psql или DBeaver:
psql -h your-db.rds.amazonaws.com -U postgres

-- Создайте изолированную БД:
CREATE DATABASE whale_tracker;

-- Выйдите
\q
```

**Это НЕ создаёт новый инстанс!** Просто новая схема внутри существующего RDS.

---

## 🚀 УПРАВЛЕНИЕ ЧЕРЕЗ PM2

```bash
# Проверить статус
pm2 status

# Просмотр логов в реальном времени
pm2 logs whale-tracker-scheduler

# Перезапуск после изменений
pm2 restart whale-tracker-scheduler

# Остановка
pm2 stop whale-tracker-scheduler

# Удалить из PM2
pm2 delete whale-tracker-scheduler
```

---

## 📊 ЧТО БУДЕТ РАБОТАТЬ

### Job 1: Data Quality Monitor (каждый час)
- Проверяет здоровье БД
- Push ТОЛЬКО если проблемы
- Тихо работает если всё ОК

### Job 2: Whale Analysis (каждые 6 часов)
- Анализ накопления китов
- Push с market signals
- Запуск ТОЛЬКО если data quality = HEALTHY

---

## 📱 ПРИМЕРЫ УВЕДОМЛЕНИЙ

**Data Quality Alert (если проблемы):**
```
🚨 DATA QUALITY ALERT

📊 Score: 87.5/100
❌ Issues: 1

Primary:
Incomplete Data - Only 4.2% coverage

Action:
python run_manual_snapshot.py
```

**Whale Analysis (каждые 6ч):**
```
📈 WHALE ANALYSIS UPDATE

Signal: 🟢 STRONG ACCUMULATION
📊 Score: +3.5%
🐋 Whales: 20

⬆️ Accumulating: 15
⬇️ Distributing: 3
```

---

## 💰 ПОТРЕБЛЕНИЕ РЕСУРСОВ

```
RAM: ~150-200 MB (Python + PM2)
CPU: <5% (idle), ~20% (analysis run)
Disk: ~500 MB (код + venv + logs)
Network: ~10 MB/hour (RPC calls)
```

**Подходит для:** t2.micro / t3.micro Free Tier ✅

---

## 🔧 TROUBLESHOOTING

### Проблема: PM2 не стартует
```bash
# Проверьте логи
pm2 logs whale-tracker-scheduler --lines 50

# Проверьте .env
cat .env

# Проверьте Python
source ~/whale-tracker/venv/bin/activate
python3 -c "import asyncio; print('OK')"
```

### Проблема: Нет уведомлений в Telegram
```bash
# Тест Telegram прямо из Python
cd ~/whale-tracker
source venv/bin/activate
python3 -c "
import asyncio
from src.notifications.telegram_notifier import TelegramNotifier
import os
from dotenv import load_dotenv
load_dotenv()

async def test():
    t = TelegramNotifier(os.getenv('TELEGRAM_BOT_TOKEN'), os.getenv('TELEGRAM_CHAT_ID'))
    await t.send_alert('🧪 Test from server!')

asyncio.run(test())
"
```

### Проблема: Database connection failed
```bash
# Проверьте доступ к RDS
psql -h $DB_HOST -U $DB_USER -d $DB_NAME

# Проверьте Security Group в AWS Console:
# - Должен разрешать входящие на порт 5432 от вашего EC2
```

---

## 📈 МОНИТОРИНГ

```bash
# CPU/RAM usage
pm2 monit

# Логи последние 100 строк
pm2 logs --lines 100

# Restart count (должен быть 0)
pm2 status
```

---

## 🔄 ОБНОВЛЕНИЕ КОДА

```bash
cd ~/whale-tracker
git pull
source venv/bin/activate
pip install -r requirements.txt
pm2 restart whale-tracker-scheduler
```

---

## 🛑 ПОЛНОЕ УДАЛЕНИЕ

```bash
pm2 delete whale-tracker-scheduler
pm2 save
rm -rf ~/whale-tracker

# Удалить БД (опционально)
psql -h $DB_HOST -U $DB_USER -c "DROP DATABASE whale_tracker;"
```

---

## 📞 SUPPORT

- Логи: `pm2 logs whale-tracker-scheduler`
- Status: `pm2 status`
- Restart: `pm2 restart whale-tracker-scheduler`

**Всё работает автоматически после деплоя!** 🚀
