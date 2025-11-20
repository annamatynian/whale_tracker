"""
Тестовый скрипт для проверки Historical Data Backfiller
"""
import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.V3.historical_config import HISTORICAL_CONFIG
from src.V3.historical_backfiller import HistoricalDataBackfiller

async def test_configuration():
    """Тестируем загрузку конфигурации."""
    print("=== Тестирование конфигурации ===")
    print(f"Start date: {HISTORICAL_CONFIG.start_date}")
    print(f"End date: {HISTORICAL_CONFIG.end_date}")
    print(f"Interval: {HISTORICAL_CONFIG.time_interval}")
    print(f"CSV filename: {HISTORICAL_CONFIG.csv_filename}")
    print(f"Enabled metrics: {HISTORICAL_CONFIG.enabled_metrics}")
    print(f"Default gas fee: {HISTORICAL_CONFIG.default_avg_priority_fee_gwei}")
    
    # Тестируем получение диапазона дат
    date_range = HISTORICAL_CONFIG.get_date_range()
    print(f"Total dates to process: {len(date_range)}")
    print(f"First date: {date_range[0]}")
    print(f"Last date: {date_range[-1]}")
    
    print("✅ Конфигурация загружена успешно")

async def test_api_connections():
    """Тестируем подключения к API."""
    print("\n=== Тестирование API подключений ===")
    
    async with HistoricalDataBackfiller(HISTORICAL_CONFIG) as backfiller:
        # Тестируем получение одной исторической цены
        from datetime import datetime, timedelta
        test_date = datetime.now() - timedelta(days=7)  # Неделю назад
        
        print("Тестируем CoinGecko API...")
        prices = await backfiller.get_historical_eth_prices(test_date, test_date + timedelta(days=1))
        if prices:
            print(f"✅ CoinGecko: получена цена {list(prices.values())[0]}")
        else:
            print("❌ CoinGecko: ошибка получения данных")
        
        print("Тестируем The Graph API...")
        pool_data = await backfiller.get_historical_pool_data(test_date)
        if pool_data.get('tvl_usd', 0) > 0:
            print(f"✅ The Graph: TVL = {pool_data['tvl_usd']}")
        else:
            print("❌ The Graph: ошибка получения данных")
        
        print("Тестируем Binance API...")
        cex_volume = await backfiller.get_historical_cex_volume(test_date)
        if cex_volume > 0:
            print(f"✅ Binance: Volume = {cex_volume}")
        else:
            print("❌ Binance: ошибка получения данных")

async def test_small_backfill():
    """Тестируем сбор данных за короткий период."""
    print("\n=== Тестирование сбора данных ===")
    
    # Создаем временную конфигурацию для теста (только 3 дня)
    from datetime import datetime, timedelta
    test_config = HISTORICAL_CONFIG.model_copy()
    test_end = datetime.now() - timedelta(days=1)
    test_start = test_end - timedelta(days=2)
    
    test_config.start_date = test_start.strftime('%Y-%m-%d')
    test_config.end_date = test_end.strftime('%Y-%m-%d')
    test_config.csv_filename = "test_historical_data.csv"
    
    print(f"Тестовый период: {test_config.start_date} - {test_config.end_date}")
    
    async with HistoricalDataBackfiller(test_config) as backfiller:
        await backfiller.run_backfill()
    
    # Проверяем результат
    if os.path.exists("test_historical_data.csv"):
        with open("test_historical_data.csv", 'r') as f:
            lines = f.readlines()
            print(f"✅ Создан тестовый CSV с {len(lines)} строками (включая заголовок)")
        
        # Очищаем тестовый файл
        os.remove("test_historical_data.csv")
        print("🗑️ Тестовый файл удален")
    else:
        print("❌ Тестовый CSV файл не создан")

async def main():
    """Запуск всех тестов."""
    print("🧪 ТЕСТИРОВАНИЕ HISTORICAL DATA BACKFILLER")
    print("=" * 50)
    
    try:
        await test_configuration()
        await test_api_connections()
        await test_small_backfill()
        
        print("\n" + "=" * 50)
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("\nТеперь вы можете:")
        print("1. Настроить диапазон дат в config/historical_data.yaml")
        print("2. Запустить полный сбор: python src/V3/historical_backfiller.py")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА ТЕСТИРОВАНИЯ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
