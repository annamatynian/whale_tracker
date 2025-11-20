# 🚀 PUMP DISCOVERY TELEGRAM - БЫСТРЫЙ СТАРТ

## 📱 Настройка (выполнить один раз)

```bash
# 1. Скопировать пример настроек
cp .env.example .env

# 2. Отредактировать .env файл своими данными:
# - Получить токен у @BotFather
# - Получить Chat ID через @userinfobot  
# - Заменить YOUR_BOT_TOKEN_HERE и YOUR_CHAT_ID_HERE

# 3. Протестировать настройку
python test_telegram.py
```

## 🎯 Запуск системы

```bash
# Интерактивный запуск (рекомендуется)
python telegram_pump_runner.py

# Или напрямую одноразовое сканирование
python -c "
import asyncio
from agents.social_intelligence.telegram_agent import TelegramIntegratedPumpAgent

async def scan():
    agent = TelegramIntegratedPumpAgent()
    candidates = await agent.discover_and_alert()
    print(f'Найдено {len(candidates)} кандидатов')

asyncio.run(scan())
"
```

## 🔧 Полезные команды

```bash
# Тест только Telegram (без pump поиска)
python agents/social_intelligence/telegram_agent.py

# Проверка системы без Telegram
python test_mock_data.py

# Полное тестирование
python test_full_suite.py
```

## 📊 Что будете получать в Telegram

### 🚀 High Priority (80+ баллов):
```
🚀 PUMP CANDIDATE FOUND!

SampleToken (SAMPLE)
🎯 Score: 87/100
📊 Priority: HIGH PRIORITY

💰 Liquidity: $85,000
📈 Volume 24h: $45,000
🕒 Age: 18.0 hours
📍 Contract: 0x123...abc

💡 Key Signals:
• Fresh token: 18.0h (+20pts)
• High liquidity: $85,000 (+15pts)
• Strong momentum: +67.8% (+15pts)

📋 Next Steps:
• 🚀 HIGH PRIORITY: Full pump analysis
• 🔍 CoinGecko narrative check

⏰ Found at 15:30:45
```

### 📊 Summary после каждого скана:
```
📊 SCAN STATISTICS

🔍 Discovery:
• Pairs scanned: 156
• Candidates found: 3
• Success rate: 1.9%

📱 Telegram:
• Alerts sent: 3/3
• API calls: 4
• Success rate: 100.0%
```

## ⚙️ Настройка частоты

В `.env` файле:
```env
SCAN_INTERVAL_MINUTES=30    # Интервал сканирования
MIN_PUMP_SCORE=60          # Минимальный score для алерта
MAX_ALERTS_PER_HOUR=10     # Лимит алертов в час
```

## 🆘 Решение проблем

### Не приходят сообщения:
```bash
# Проверить настройки
python test_telegram.py
```

### "Bot not found":
- Проверьте токен от @BotFather
- Убедитесь что бот не удален

### "403 Forbidden":
- Отправьте боту `/start` 
- Проверьте Chat ID через @userinfobot

---

**🎉 Готово! Теперь вы будете получать уведомления о pump кандидатах прямо в Telegram!**
