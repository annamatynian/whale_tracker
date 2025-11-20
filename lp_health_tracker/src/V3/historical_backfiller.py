import asyncio
import aiohttp
import csv
import logging
import numpy as np
import os
import shutil
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Импортируем существующие компоненты для переиспользования
from .hmm_market_data_collector import MarketDataPoint
from .v3_data_sources import V3GraphQLClient
from .historical_config import HISTORICAL_CONFIG, HistoricalDataConfig

# Настройка логгера
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HistoricalDataBackfiller:
    """
    Сборщик исторических данных для создания базового датасета.
    
    Особенности:
    - Получает ТОЛЬКО макро-данные (цены, объемы, TVL)
    - Заполняет микроструктурные метрики (газ) значениями по умолчанию
    - Совместим по формату с hmm_market_data_collector.py
    - Использует YAML конфигурацию
    - Соблюдает rate limits API
    """
    
    def __init__(self, config: HistoricalDataConfig):
        self.config = config
        self.csv_filename = self.config.csv_filename
        
        # Инициализация HTTP сессии для API запросов
        self.http_session = None
        
        # Инициализация GraphQL клиента для The Graph
        self.graph_client = V3GraphQLClient()
        
        # API endpoints из базовой конфигурации 
        self.coingecko_base_url = "https://api.coingecko.com/api/v3"
        self.binance_base_url = "https://api.binance.com"
        
        # Заголовки CSV (те же, что и в основном сборщике)
        self.csv_headers = list(MarketDataPoint.model_fields.keys())
        
        logger.info("Historical Data Backfiller инициализирован с YAML конфигурацией")
    
    async def __aenter__(self):
        """Async context manager entry."""
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
    
    def setup_csv_file(self):
        """Создает CSV-файл с заголовками, опционально делает backup."""
        if os.path.exists(self.csv_filename) and self.config.backup_existing:
            backup_name = f"{self.csv_filename}.backup_{int(time.time())}"
            shutil.copy2(self.csv_filename, backup_name)
            logger.info(f"Создан backup существующего файла: {backup_name}")
        
        with open(self.csv_filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.csv_headers)
            writer.writeheader()
        logger.info(f"CSV файл '{self.csv_filename}' подготовлен")
    
    async def get_historical_eth_prices(self, start_date: datetime, end_date: datetime) -> Dict[str, float]:
        """
        Получает исторические цены ETH от CoinGecko.
        
        Returns:
            Dict[str, float]: Словарь {дата: цена} в формате 'YYYY-MM-DD': price
        """
        start_timestamp = int(start_date.timestamp())
        end_timestamp = int(end_date.timestamp())
        
        url = f"{self.coingecko_base_url}/coins/ethereum/market_chart/range"
        params = {
            'vs_currency': 'usd',
            'from': start_timestamp,
            'to': end_timestamp
        }
        
        try:
            await asyncio.sleep(self.config.api_delay_seconds)  # Rate limit
            
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
    
    async def get_historical_pool_data(self, target_date: datetime) -> Dict[str, float]:
        """
        Получает исторические данные пула (TVL, объемы) для указанной даты.
        
        Returns:
            Dict с ключами: tvl_usd, dex_volume_usd
        """
        # Для daily данных используем poolDayDatas
        date_timestamp = int(target_date.timestamp())
        
        query = """
        query PoolDayData($date: Int!) {
            poolDayDatas(
                first: 1,
                where: {
                    pool: "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
                    date: $date
                }
            ) {
                tvlUSD
                volumeUSD
            }
        }
        """
        
        variables = {"date": date_timestamp}
        
        try:
            await asyncio.sleep(self.config.api_delay_seconds)  # Rate limit
            
            data = await self.graph_client.query(query, variables)
            pool_data = data.get('poolDayDatas', [])
            
            if pool_data:
                return {
                    'tvl_usd': float(pool_data[0].get('tvlUSD', 0)),
                    'dex_volume_usd': float(pool_data[0].get('volumeUSD', 0))
                }
            else:
                return {'tvl_usd': 0.0, 'dex_volume_usd': 0.0}
                
        except Exception as e:
            logger.warning(f"Ошибка получения данных пула для {target_date.strftime('%Y-%m-%d')}: {e}")
            return {'tvl_usd': 0.0, 'dex_volume_usd': 0.0}
    
    async def get_historical_cex_volume(self, target_date: datetime) -> float:
        """
        Получает исторический объем торгов ETH/USDT с Binance для указанной даты.
        
        Returns:
            float: Объем торгов за день
        """
        # Binance klines для получения дневного объема
        start_time = int(target_date.timestamp() * 1000)  # Milliseconds
        end_time = int((target_date + timedelta(days=1)).timestamp() * 1000)
        
        url = f"{self.binance_base_url}/api/v3/klines"
        params = {
            'symbol': 'ETHUSDT',
            'interval': '1d',
            'startTime': start_time,
            'endTime': end_time,
            'limit': 1
        }
        
        try:
            await asyncio.sleep(self.config.api_delay_seconds)  # Rate limit
            
            async with self.http_session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                if data and len(data[0]) > 7:
                    return float(data[0][7])  # Volume is at index 7
                return 0.0
                
        except Exception as e:
            logger.warning(f"Ошибка получения CEX объема для {target_date.strftime('%Y-%m-%d')}: {e}")
            return 0.0
    
    def calculate_log_return(self, current_price: float, previous_price: Optional[float]) -> float:
        """Вычисляет логарифмическую доходность."""
        if previous_price and previous_price > 0 and current_price > 0:
            return np.log(current_price / previous_price)
        return 0.0
    
    def calculate_ratios(self, dex_volume: float, cex_volume: float) -> Dict[str, float]:
        """Вычисляет производные метрики."""
        dex_cex_ratio = dex_volume / cex_volume if cex_volume > 0 else 0.0
        
        # Для исторических данных у нас нет 24h average, поэтому используем константу
        hourly_volume_vs_avg = self.config.default_hourly_volume_vs_24h_avg_pct
        
        return {
            'dex_cex_volume_ratio': dex_cex_ratio,
            'hourly_volume_vs_24h_avg_pct': hourly_volume_vs_avg
        }
    
    async def create_historical_data_point(self, target_date: datetime, eth_price: float, 
                                         previous_price: Optional[float]) -> MarketDataPoint:
        """Создает полную точку данных для указанной даты."""
        
        # Параллельно получаем данные пула и CEX
        pool_data, cex_volume = await asyncio.gather(
            self.get_historical_pool_data(target_date),
            self.get_historical_cex_volume(target_date)
        )
        
        # Вычисляем производные метрики
        log_return = self.calculate_log_return(eth_price, previous_price)
        ratios = self.calculate_ratios(pool_data['dex_volume_usd'], cex_volume)
        
        # Создаем точку данных с default значениями для недоступных метрик
        return MarketDataPoint(
            timestamp=int(target_date.timestamp()),
            datetime=target_date.strftime('%Y-%m-%d %H:%M:%S'),
            eth_price_usd=round(eth_price, 2),
            log_return=round(log_return, 6),
            dex_volume_usd=round(pool_data['dex_volume_usd'], 2),
            cex_volume_usd=round(cex_volume, 2),
            dex_cex_volume_ratio=round(ratios['dex_cex_volume_ratio'], 4),
            hourly_volume_vs_24h_avg_pct=round(ratios['hourly_volume_vs_24h_avg_pct'], 2),
            tvl_usd=round(pool_data['tvl_usd'], 2),
            # Используем default значения для недоступных исторических метрик
            net_liquidity_change_usd=self.config.default_net_liquidity_change_usd,
            avg_priority_fee_gwei=self.config.default_avg_priority_fee_gwei,
            var_priority_fee_gwei=self.config.default_var_priority_fee_gwei,
            outlier_detected=self.config.default_outlier_detected,
            max_priority_fee_gwei=self.config.default_max_priority_fee_gwei,
            outlier_percentage=self.config.default_outlier_percentage
        )
    
    def write_data_points_to_csv(self, data_points: List[MarketDataPoint]):
        """Записывает список точек данных в CSV файл."""
        try:
            with open(self.csv_filename, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.csv_headers)
                for data_point in data_points:
                    writer.writerow(data_point.model_dump())
            
            logger.info(f"Записано {len(data_points)} точек данных в CSV")
            
        except IOError as e:
            logger.error(f"Ошибка записи в CSV: {e}")
    
    async def run_backfill(self):
        """Главная функция для запуска сбора исторических данных."""
        logger.info("Запуск сбора исторических данных...")
        
        # Подготавливаем CSV файл
        self.setup_csv_file()
        
        # Получаем диапазон дат
        date_range = self.config.get_date_range()
        logger.info(f"Обработка {len(date_range)} дат от {self.config.start_date} до {self.config.end_date}")
        
        # Получаем все исторические цены одним запросом (для эффективности)
        start_date = date_range[0]
        end_date = date_range[-1]
        historical_prices = await self.get_historical_eth_prices(start_date, end_date)
        
        # Обрабатываем каждую дату
        data_points = []
        previous_price = None
        
        for i, target_date in enumerate(date_range):
            date_str = target_date.strftime('%Y-%m-%d')
            
            # Получаем цену для этой даты
            eth_price = historical_prices.get(date_str, 0.0)
            if eth_price == 0.0:
                logger.warning(f"Нет данных о цене для {date_str}, пропускаем")
                continue
            
            try:
                # Создаем точку данных
                data_point = await self.create_historical_data_point(
                    target_date, eth_price, previous_price
                )
                data_points.append(data_point)
                previous_price = eth_price
                
                # Логгируем прогресс
                if (i + 1) % 10 == 0:
                    logger.info(f"Обработано {i + 1}/{len(date_range)} дат")
                
                # Периодически записываем данные в файл (батчами по 50)
                if len(data_points) >= 50:
                    self.write_data_points_to_csv(data_points)
                    data_points = []
                
            except Exception as e:
                logger.error(f"Ошибка обработки {date_str}: {e}")
                continue
        
        # Записываем оставшиеся данные
        if data_points:
            self.write_data_points_to_csv(data_points)
        
        logger.info(f"Сбор исторических данных завершен. Файл: {self.csv_filename}")

# Главная функция для запуска скрипта
async def main():
    """Точка входа для запуска historical backfiller."""
    logger.info("=== Historical Data Backfiller ===")
    logger.info(f"Конфигурация загружена из YAML файлов")
    logger.info(f"Период: {HISTORICAL_CONFIG.start_date} - {HISTORICAL_CONFIG.end_date}")
    logger.info(f"Интервал: {HISTORICAL_CONFIG.time_interval}")
    logger.info(f"Выходной файл: {HISTORICAL_CONFIG.csv_filename}")
    
    async with HistoricalDataBackfiller(HISTORICAL_CONFIG) as backfiller:
        await backfiller.run_backfill()

# Точка входа для запуска скрипта
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Программа прервана пользователем (Ctrl+C)")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
