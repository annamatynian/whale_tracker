# Historical Data Backfiller - Руководство по использованию

## Обзор

Historical Data Backfiller — это специализированный модуль для загрузки исторических макро-данных рынка. Он позволяет быстро создать датасет для обучения HMM-моделей без ожидания в несколько месяцев.

## Архитектура

### Что МОЖНО получить исторически:
✅ **eth_price_usd** - цены ETH (CoinGecko API)  
✅ **dex_volume_usd** - объемы DEX (The Graph API)  
✅ **cex_volume_usd** - объемы CEX (Binance API)  
✅ **tvl_usd** - заблокированная стоимость (The Graph API)  
✅ **log_return** - вычисляется из цен  
✅ **dex_cex_volume_ratio** - вычисляется из объемов  

### Что НЕЛЬЗЯ получить исторически:
❌ **net_liquidity_change_usd** - требует анализ mint/burn событий  
❌ **avg_priority_fee_gwei** - микроструктурная метрика газа  
❌ **var_priority_fee_gwei** - дисперсия газовых комиссий  
❌ **outlier_detected** - детекция выбросов газа  
❌ **max_priority_fee_gwei** - максимальные комиссии  
❌ **outlier_percentage** - процент выбросов  

Эти метрики заполняются **разумными значениями по умолчанию** из YAML конфигурации.

## Быстрый старт

### 1. Установка зависимостей
```bash
pip install pyyaml aiohttp
```

### 2. Тестирование
```bash
python test_historical_backfiller.py
```

### 3. Настройка диапазона дат
Отредактируйте `config/historical_data.yaml`:
```yaml
historical_data:
  date_range:
    start_date: "2023-01-01"  # Начальная дата
    end_date: "2025-09-14"    # Конечная дата
```

### 4. Запуск полного сбора
```bash
python src/V3/historical_backfiller.py
```

## Конфигурация

### Основные настройки (config/historical_data.yaml)

```yaml
historical_data:
  date_range:
    start_date: "2023-01-01"
    end_date: "2025-09-14"
    
  intervals:
    time_interval: "daily"        # "daily" или "hourly"
    api_delay_seconds: 2          # Задержка между API запросами
    
  output:
    csv_filename: "historical_macro_data.csv"
    backup_existing: true         # Создавать backup существующего файла
```

### Default значения для недоступных метрик

```yaml
default_values:
  gas_metrics:
    avg_priority_fee_gwei: 20.0   # Типичное историческое среднее
    var_priority_fee_gwei: 0.0    # Нет данных о дисперсии
    outlier_detected: false       # Консервативное значение
    max_priority_fee_gwei: 0.0    # Нет данных о максимуме
    outlier_percentage: 0.0       # Нет данных о выбросах
```

## Использование с существующими API ключами

Backfiller автоматически использует API ключи из ваших environment конфигураций:

- **CoinGecko**: `config/environments/development.yaml` → `apis.coingecko.api_key`
- **Infura**: Для The Graph запросов → `blockchain.providers.infura.api_key`
- **Binance**: Публичные endpoints, ключ не требуется

## Производительность и Rate Limits

### Временные оценки:
- **1 год daily данных**: ~15-20 минут
- **2 года daily данных**: ~30-40 минут
- **1 год hourly данных**: ~6-8 часов

### Rate Limits:
- CoinGecko Free: 50 запросов/минуту
- The Graph: Без жестких лимитов
- Binance: 1200 запросов/минуту

Скрипт автоматически соблюдает лимиты через `api_delay_seconds`.

## Интеграция с HMM моделями

### Формат выходных данных
Создается CSV файл, **полностью совместимый** с `hmm_market_data_collector.py`:

```csv
timestamp,datetime,eth_price_usd,log_return,dex_volume_usd,cex_volume_usd,...
1672531200,2023-01-01 00:00:00,1200.50,0.0,1500000.0,5000000.0,...
```

### Рабочий процесс:
1. **Запустите historical_backfiller.py** → получите `historical_macro_data.csv`
2. **Начните обучение HMM** на исторических данных
3. **Параллельно запустите hmm_market_data_collector.py** → накапливайте полные данные
4. **Через несколько недель** переобучите модель на полных данных

## Troubleshooting

### Ошибка: "Нет данных о цене для YYYY-MM-DD"
- Проверьте доступность CoinGecko API
- Возможно, выбрана слишком старая дата (до 2015 года)

### Ошибка: "The Graph connection failed"
- Проверьте Infura API ключ в `config/environments/development.yaml`
- Проверьте подключение к интернету

### Ошибка: "Binance API error"
- Binance иногда блокирует запросы. Увеличьте `api_delay_seconds` до 5-10

### Файл создается пустой
- Проверьте, что диапазон дат корректный
- Запустите тест: `python test_historical_backfiller.py`

## Кастомизация

### Изменение пула для анализа
В `src/V3/historical_backfiller.py` найдите:
```python
pool: "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"  # USDC/ETH 0.05%
```

### Добавление новых источников данных
1. Создайте новый метод `get_historical_XXX()`
2. Добавьте вызов в `create_historical_data_point()`
3. Обновите YAML конфигурацию

### Изменение default значений
Отредактируйте `config/historical_data.yaml` → `default_values`

## Мониторинг прогресса

Скрипт выводит подробные логи:
```
INFO - Обработано 50/365 дат
INFO - Записано 50 точек данных в CSV
INFO - Получено 365 исторических цен ETH
```

Для детального дебага установите в коде:
```python
logging.basicConfig(level=logging.DEBUG)
```

## Совместимость

- ✅ Python 3.7+
- ✅ Windows/Linux/macOS
- ✅ Async/await архитектура
- ✅ Pydantic валидация
- ✅ YAML конфигурация
- ✅ Полная совместимость с существующим кодом

---

**Готово к использованию!** Запустите тест и начинайте собирать исторические данные для ваших HMM моделей.
