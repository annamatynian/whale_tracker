import asyncio
import aiohttp
import csv
import logging
import numpy as np
import os
import time
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List
from web3 import Web3

# Убедитесь, что файл v3_data_sources.py находится в той же папке
from .v3_data_sources import V3GraphQLClient
# Убедитесь, что файл collector_config.py находится в той же папке
from .collector_config import HMMCollectorConfig, CONFIG

# Настройка базового логгера
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === PYDANTIC MODELS FOR API RESPONSES ===

class GasStatsResponse(BaseModel):
    """Модель для ответа функции анализа газа."""
    avg_fee: float = Field(ge=0.0, description="Средняя приоритетная комиссия в Gwei")
    var_fee: float = Field(ge=0.0, description="Дисперсия приоритетной комиссии")
    outlier_detected: bool = Field(description="Обнаружены ли выбросы ('прыжковые ставки')")
    max_fee: float = Field(ge=0.0, description="Максимальная приоритетная комиссия в Gwei")
    outlier_percentage: float = Field(ge=0.0, le=100.0, description="Процент транзакций-выбросов")

class V3PoolDataResponse(BaseModel):
    """Модель для ответа функции получения данных V3 пула."""
    current_hourly_volume: float = Field(ge=0.0, description="Текущий часовой объем в USD")
    avg_24h_hourly_volume: float = Field(ge=0.0, description="Средний часовой объем за 24ч в USD")
    net_liquidity_change_usd: float = Field(description="Чистое изменение ликвидности в USD")
    tvl_usd: float = Field(ge=0.0, description="Общая заблокированная стоимость в USD")

class MarketDataPoint(BaseModel):
    """Модель для итогового data point, который записывается в CSV."""
    timestamp: int = Field(..., description="Unix timestamp")
    datetime: str = Field(..., description="Человекочитаемая дата и время")
    eth_price_usd: float = Field(ge=0.0, description="Цена ETH в USD")
    log_return: float = Field(description="Логарифмическая доходность")
    dex_volume_usd: float = Field(ge=0.0, description="Объем DEX в USD")
    cex_volume_usd: float = Field(ge=0.0, description="Объем CEX в USD") 
    dex_cex_volume_ratio: float = Field(ge=0.0, description="Соотношение объемов DEX/CEX")
    hourly_volume_vs_24h_avg_pct: float = Field(ge=0.0, description="Процент от среднего объема за 24ч")
    tvl_usd: float = Field(ge=0.0, description="TVL пула в USD")
    net_liquidity_change_usd: float = Field(description="Чистое изменение ликвидности в USD")
    avg_priority_fee_gwei: float = Field(ge=0.0, description="Средняя приоритетная комиссия")
    var_priority_fee_gwei: float = Field(ge=0.0, description="Дисперсия приоритетной комиссии")
    outlier_detected: bool = Field(description="Обнаружены ли выбросы газа")
    max_priority_fee_gwei: float = Field(ge=0.0, description="Максимальная приоритетная комиссия")
    outlier_percentage: float = Field(ge=0.0, le=100.0, description="Процент транзакций-выбросов")
    
    @field_validator('datetime')
    @classmethod
    def validate_datetime_format(cls, v):
        """Проверяем формат datetime строки."""
        try:
            datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
            return v
        except ValueError:
            raise ValueError('datetime должен быть в формате YYYY-MM-DD HH:MM:SS')

class AdvancedDataCollector:
    """
    Продвинутый сборщик данных, использующий микроструктурные
    и межрыночные метрики.
    """
    
    def __init__(self, config: HMMCollectorConfig):
        self.config = config
        self.csv_filename = self.config.CSV_FILENAME
        
        # Инициализация Web3 провайдера для подключения к Infura
        self.w3 = Web3(Web3.HTTPProvider(self.config.INFURA_URL))
        if not self.w3.is_connected():
            logger.error("Не удалось подключиться к Infura. Проверьте INFURA_URL и API ключ.")
            raise ConnectionError("Infura connection failed")
            
        # Инициализация клиента The Graph
        self.graph_client = V3GraphQLClient()
        
        # Асинхронная сессия для запросов к CEX API
        self.http_session = aiohttp.ClientSession()
        self.previous_price = None
        
        # Итоговый список заголовков
        self.csv_headers = list(MarketDataPoint.model_fields.keys())
        
        self._setup_csv_file()
        logger.info("Продвинутый сборщик данных инициализирован.")
    
    def _setup_csv_file(self):
        """Создает CSV-файл с заголовками, если он еще не существует."""
        if not os.path.exists(self.csv_filename):
            with open(self.csv_filename, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.csv_headers)
                writer.writeheader()
            logger.info(f"CSV файл '{self.csv_filename}' создан.")
    
    async def close_sessions(self):
        """Корректно закрывает все сетевые сессии при завершении работы."""
        await self.graph_client.close()
        await self.http_session.close()
        logger.info("Сетевые сессии закрыты.")

    async def _get_eth_price_async(self) -> float:
        """Получает текущую цену ETH в USD с CoinGecko."""
        url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
        try:
            async with self.http_session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                return float(data.get('ethereum', {}).get('usd', 0.0))
        except Exception as e:
            logger.warning(f"Не удалось получить цену ETH: {e}")
            return 0.0

    async def _get_cex_volume_async(self) -> float:
        """Получает объем торгов по паре ETH/USDT с Binance."""
        try:
            async with self.http_session.get(self.config.CEX_API_URL) as response:
                response.raise_for_status()
                data = await response.json()
                if data and isinstance(data, list) and len(data[0]) > 7:
                    return float(data[0][7])
        except Exception as e:
            logger.warning(f"Не удалось получить объем с CEX: {e}")
            return 0.0

    async def _get_onchain_gas_stats_async(self) -> GasStatsResponse:
        """Получает и рассчитывает статистику по приоритетным комиссиям."""
        loop = asyncio.get_running_loop()
        priority_fees = []
        try:
            latest_block_number = await loop.run_in_executor(
                None, self.w3.eth.get_block_number
            )
            for i in range(self.config.BLOCKS_FOR_GAS_ANALYSIS):
                block_number = latest_block_number - i
                block = await loop.run_in_executor(
                    None, lambda: self.w3.eth.get_block (block_number, full_transactions=True)
                )
                base_fee_per_gas = block.get('baseFeePerGas', 0)
                if not base_fee_per_gas: 
                    continue
                for tx in block.get('transactions', []):
                    if 'maxPriorityFeePerGas' in tx:
                        priority_fees.append(tx['maxPriorityFeePerGas'])
                    else:
                        priority_fees.append(tx['gasPrice'] - base_fee_per_gas)
            if len(priority_fees) < 4:
                return GasStatsResponse(
                    avg_fee=0.0, 
                    var_fee=0.0, 
                    outlier_detected=False, 
                    max_fee=0.0,
                    outlier_percentage=0.0
                )

            priority_fees_gwei = np.array([fee / 10**9 for fee in priority_fees])
            avg_fee = np.mean(priority_fees_gwei)
            var_fee = np.var(priority_fees_gwei)
            std_dev = np.std(priority_fees_gwei)
            max_fee = np.max(priority_fees_gwei)

            # параллельный расчет всех выбросов для точной статистики
            outlier_masks = []

            # z-score критерий
            if std_dev > 0:
                z_scores = (priority_fees_gwei - avg_fee) / std_dev
                outlier_masks.append(z_scores > 3.0)

            # IQR критерий (пересчитываем для параллельного подхода)
            q1 = np.percentile(priority_fees_gwei, 25)
            q3 = np.percentile(priority_fees_gwei, 75)
            iqr = q3 - q1
            upper_bound = q3 + (1.5 * iqr)
            outlier_masks.append(priority_fees_gwei > upper_bound)

            # Объединяем все критерии через ИЛИ 
            #np.logical_or берет два списка с True/False 
            # и создает один итоговый список. Результат будет True, если значение есть хотя бы в одном списке.
            
            # Объединяем и считаем метрики
            if outlier_masks:
                combined_outliers = np.logical_or.reduce(outlier_masks)
                outlier_count = np.sum(combined_outliers)
                outlier_percentage = (outlier_count / len(priority_fees_gwei)) * 100
                outlier_detected = (outlier_count > 0)  # Простая логика
            else:
                outlier_percentage = 0.0
                outlier_detected = False

            return GasStatsResponse(
                avg_fee=avg_fee,
                var_fee=var_fee,
                outlier_detected=outlier_detected,
                max_fee=max_fee,
                outlier_percentage=outlier_percentage
            )
            

        except Exception as e:
            logger.warning(f"Failed to get gas stats: {e}")
            return GasStatsResponse(
                avg_fee=0.0, 
                var_fee=0.0,
                outlier_detected=False,
                max_fee=0.0,
                outlier_percentage=0.0
            )
        
    async def _get_v3_pool_data_async(self) -> V3PoolDataResponse:
        """Получает данные по пулу V3, включая объем за последний час и средний за 24 часа."""
        interval_seconds = self.config.COLLECTION_INTERVAL_SECONDS
        current_timestamp = int(time.time())
        start_timestamp = current_timestamp - interval_seconds
        
        # mints(..., where: {..., timestamp_gt: $startTime}, ...): 
        # Это самая интересная часть. Мы просим: "Дай мне все события добавления 
        # ликвидности (mints), которые произошли в этом пуле (pool: $poolId) 
        # ПОСЛЕ (gt - greater than) нашего времени начала 
        # (timestamp_gt: $startTime)". Для каждого такого события 
        # нам нужно поле amountUSD.
        query = """
        query PoolData($poolId: String!, $startTime: Int!) {
            pool(id: $poolId) {
                tvlUSD
            }
            # Запрашиваем 24 последних часовых среза для расчета среднего
            poolHourDatas(first: 24, where: {pool: $poolId}, orderBy: periodStartUnix, orderDirection: desc) {
                volumeUSD
            }
            mints(first: 1000, where: {pool: $poolId, timestamp_gt: $startTime}, orderBy: timestamp, orderDirection: desc) {
                amountUSD
            }
            burns(first: 1000, where: {pool: $poolId, timestamp_gt: $startTime}, orderBy: timestamp, orderDirection: desc) {
                amountUSD
            }
        }
        """
        variables = {"poolId": self.config.POOL_ADDRESS_V3, "startTime": start_timestamp}
        try:
            data = await self.graph_client.query(query, variables)
            tvl_usd = float(data.get('pool', {}).get('tvlUSD', 0))
            hourly_data = data.get('poolHourDatas', [])

            current_hourly_volume = 0.0
            avg_24h_hourly_volume = 0.0

            if hourly_data:
                # Текущий объем - это объем из самого свежего часового среза
                current_hourly_volume = float(hourly_data[0].get('volumeUSD', 0))

                # Средний объем - среднее значение по всем полученным срезам
                all_volumes = [float(h.get('volumeUSD', 0)) for h in hourly_data]

                if all_volumes:
                    avg_24h_hourly_volume = np.mean(all_volumes) 
                

            mints = data.get('mints', [])
            burns = data.get('burns', [])
            total_mint_usd = sum(float(m['amountUSD']) for m in mints)
            total_burn_usd = sum(float(b['amountUSD']) for b in burns)
            net_liquidity_change = total_mint_usd - total_burn_usd

            return V3PoolDataResponse(
                current_hourly_volume=current_hourly_volume,
                avg_24h_hourly_volume=avg_24h_hourly_volume,
                net_liquidity_change_usd=net_liquidity_change,
                tvl_usd=tvl_usd
            )
        except Exception as e:
            logger.warning(f"Не удалось получить данные с The Graph: {e}")
            return V3PoolDataResponse(
                current_hourly_volume=0.0 , 
                avg_24h_hourly_volume=0.0, 
                net_liquidity_change_usd=0.0, 
                tvl_usd=0.0
            )

    def write_to_csv(self, data:MarketDataPoint):
        """Дописывает строку данных в CSV-файл."""
        try:
            with open(self.csv_filename, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.csv_headers)
                data_dict = data.model_dump()
                writer.writerow(data_dict)
            logger.info(f"Данные успешно сохранены.")
        except IOError as e:
            logger.error(f"Ошибка записи в файл: {e}")

    async def get_current_market_data(self) -> Optional[MarketDataPoint]:
        """
        Запускает все сборщики данных параллельно, вычисляет финальные
        метрики и формирует единый словарь для записи.
        """
        logger.info("Сбор нового набора данных...")
        
        results = await asyncio.gather(
            self._get_cex_volume_async(),
            self._get_onchain_gas_stats_async(),
            self._get_v3_pool_data_async(),
            self._get_eth_price_async()
        )
        
        cex_volume, gas_stats, v3_pool_data, eth_price = results

        # --- NEW CALCULATION FOR LOG RETURN ---
        log_return = 0.0
        if self.previous_price and eth_price > 0 and self.previous_price > 0:
            log_return = np.log(eth_price / self.previous_price)
        self.previous_price = eth_price # Update the price for the next run
        
        tvl_usd = v3_pool_data.tvl_usd
        current_hourly_volume = v3_pool_data.current_hourly_volume
        avg_24h_hourly_volume = v3_pool_data.avg_24h_hourly_volume # 1.0 чтобы избежать деления на ноль
        dex_cex_ratio = current_hourly_volume / cex_volume if cex_volume > 0 else 0
        
        hourly_volume_vs_avg_pct = (current_hourly_volume / avg_24h_hourly_volume) * 100 if avg_24h_hourly_volume > 0 else 0
        current_time = datetime.now()

        return MarketDataPoint(
            timestamp=int(current_time.timestamp()),
            datetime=current_time.strftime('%Y-%m-%d %H:%M:%S'),
            eth_price_usd=round(eth_price, 2),
            log_return=round(log_return, 6),
            dex_volume_usd=round(current_hourly_volume, 2),
            cex_volume_usd=round(cex_volume, 2),
            dex_cex_volume_ratio=round(dex_cex_ratio, 4),
            hourly_volume_vs_24h_avg_pct=round(hourly_volume_vs_avg_pct, 2),
            tvl_usd=round(tvl_usd, 2),
            net_liquidity_change_usd=round(v3_pool_data.net_liquidity_change_usd, 2),
            avg_priority_fee_gwei=round(gas_stats.avg_fee, 2),
            var_priority_fee_gwei=round(gas_stats.var_fee, 2),
            outlier_detected=gas_stats.outlier_detected,
            max_priority_fee_gwei=round(gas_stats.max_fee, 2),
            outlier_percentage=round(gas_stats.outlier_percentage, 2)
        )
        

    async def run(self):
        """Главный цикл работы сборщика."""
        logger.info("Запуск сборщика данных...")
        try:
            while True:
                market_data = await self.get_current_market_data()
                if market_data:
                    self.write_to_csv(market_data)
                interval = self.config.COLLECTION_INTERVAL_SECONDS
                logger.info(f"Пауза на {interval} секунд...")
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            logger.info("Сборщик остановлен.")
        finally:
            await self.close_sessions()

# --- Точка входа для запуска скрипта ---
if __name__ == "__main__":
    collector = AdvancedDataCollector(config=CONFIG)
    try:
        asyncio.run(collector.run())
    except KeyboardInterrupt:
        logger.info("Программа прервана пользователем (Ctrl+C).")