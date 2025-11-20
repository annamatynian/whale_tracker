"""
Обновленная версия Historical Backfiller с поддержкой Storage Manager
"""
import asyncio
import logging
from datetime import datetime
from typing import List

# Импортируем обновленные компоненты
from .hmm_market_data_collector import MarketDataPoint
from .v3_data_sources import V3GraphQLClient
from .historical_config import HISTORICAL_CONFIG, HistoricalDataConfig
from .storage_manager import create_storage_manager

# Настройка логгера
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HistoricalDataBackfillManager:
    """
    Обновленный Historical Data Backfiller с поддержкой Storage Manager.
    
    Преимущества:
    - Использует единую систему хранения данных
    - Поддерживает CSV и SQLite backends
    - Автоматическая батчевая запись для производительности
    -统一 API для всех компонентов системы
    """
    
    def __init__(self, config: HistoricalDataConfig):
        self.config = config
        
        # Инициализация Storage Manager
        self.storage = create_storage_manager()
        
        # HTTP и GraphQL клиенты
        self.http_session = None
        self.graph_client = V3GraphQLClient()
        
        # API endpoints
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        self.binance_base_url = "https://api.binance.com"
        
        logger.info("Historical Data Backfill Manager инициализирован")
    
    async def __aenter__(self):
        """Async context manager entry."""
        import aiohttp
        self.http_session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_sessions()
    
    async def close_sessions(self):
        """Корректно закрывает все сетевые сессии."""
        if self.http_session:
            await self.http_session.close()
        await self.graph_client.close()
        logger.info("Сетевые сессии закрыты")
    
    # ... (все методы сбора данных остаются теми же)
    async def get_historical_eth_prices(self, start_date: datetime, end_date: datetime):
        """Получает исторические цены ETH от CoinGecko."""
        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())
        
        url = f"{self.coingecko_base_url}/coins/ethereum/market_chart/range"
        params = {
            'vs_currency': 'usd',
            'from': start_timestamp,
            'to': end_timestamp
        }
        
        try:
            await asyncio.sleep(self.config.api_delay_seconds)
            
            async with self.http_session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                prices = {}
                for price_data in data.get('prices', []):
                    timestamp_ms, price = price_data
                    date_str = datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d')
                    prices[date_str] = float(price)
                
                logger.info(f"Получено {len(prices)} исторических цен ETH")
                return prices
                
        except Exception as e:
            logger.error(f"Ошибка получения исторических цен: {e}")
            return {}
    
    async def run_backfill_with_storage(self):
        """
        Главная функция для запуска сбора исторических данных 
        с использованием Storage Manager.
        """
        logger.info("Запуск сбора исторических данных с Storage Manager...")
        
        # Получаем диапазон дат
        date_range = self.config.get_date_range()
        logger.info(f"Обработка {len(date_range)} дат от {self.config.start_date} до {self.config.end_date}")
        
        # Получаем все исторические цены одним запросом
        start_date = date_range[0]
        end_date = date_range[-1]
        historical_prices = await self.get_historical_eth_prices(start_date, end_date)
        
        # Обрабатываем данные батчами для лучшей производительности
        batch_size = 100  # Записываем по 100 записей за раз
        data_batch = []
        previous_price = None
        processed_count = 0
        
        for target_date in date_range:
            date_str = target_date.strftime('%Y-%m-%d')
            
            # Получаем цену для этой даты
            eth_price = historical_prices.get(date_str, 0.0)
            if eth_price == 0.0:
                logger.warning(f"Нет данных о цене для {date_str}, пропускаем")
                continue
            
            try:
                # Создаем точку данных (используем существующую логику)
                data_point = await self.create_historical_data_point(
                    target_date, eth_price, previous_price
                )
                data_batch.append(data_point)
                previous_price = eth_price
                processed_count += 1
                
                # Когда набираем полный batch - записываем в storage
                if len(data_batch) >= batch_size:
                    self.storage.write_data_points(data_batch)
                    logger.info(f"Записан batch: {len(data_batch)} записей. Обработано: {processed_count}/{len(date_range)}")
                    data_batch = []
                
            except Exception as e:
                logger.error(f"Ошибка обработки {date_str}: {e}")
                continue
        
        # Записываем оставшиеся данные
        if data_batch:
            self.storage.write_data_points(data_batch)
            logger.info(f"Записан финальный batch: {len(data_batch)} записей")
        
        # Показываем финальную статистику
        stats = self.storage.get_stats()
        logger.info(f"Сбор исторических данных завершен. Статистика: {stats}")
        
        return processed_count
    
    async def create_historical_data_point(self, target_date: datetime, eth_price: float, previous_price):
        """Создает точку исторических данных."""
        # Импортируем методы из оригинального backfiller
        from .historical_backfiller import HistoricalDataBackfiller
        
        # Создаем временный экземпляр для использования методов
        temp_backfiller = HistoricalDataBackfiller(self.config)
        temp_backfiller.http_session = self.http_session
        
        return await temp_backfiller.create_historical_data_point(target_date, eth_price, previous_price)

# Главная функция для запуска
async def main():
    """Точка входа для запуска обновленного historical backfiller."""
    logger.info("=== Historical Data Backfiller с Storage Manager ===")
    logger.info(f"Backend хранения: {HISTORICAL_CONFIG.csv_filename}")
    logger.info(f"Период: {HISTORICAL_CONFIG.start_date} - {HISTORICAL_CONFIG.end_date}")
    
    async with HistoricalDataBackfillManager(HISTORICAL_CONFIG) as manager:
        processed_count = await manager.run_backfill_with_storage()
        
        print(f"\n🎉 Обработано {processed_count} записей!")
        print("📊 Данные готовы для использования в HMM моделях")
        
        # Показываем, как загрузить данные для ML
        print("\n💡 Для использования в ML:")
        print("```python")
        print("import pandas as pd")
        print(f"df = pd.read_csv('{HISTORICAL_CONFIG.csv_filename}')")
        print("# Готово для sklearn, numpy, etc.")
        print("```")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Программа прервана пользователем (Ctrl+C)")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
