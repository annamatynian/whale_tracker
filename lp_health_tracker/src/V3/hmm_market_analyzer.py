#!/usr/bin/env python3
"""
HMM Market Data Collector
=========================

Скрипт для периодического сбора рыночных данных для Uniswap V2 пула ETH/USDC.
Собирает информацию о цене, волатильности, ликвидности и объеме торгов
и сохраняет её в CSV-файл для последующего анализа.

Зависимости:
pip install requests numpy
"""

import requests
import numpy as np
import time
import csv
import os
import logging
from datetime import datetime
from collections import deque
from typing import Dict, Optional, List

# --- КОНФИГУРАЦИЯ ---
CONFIG = {
    'CSV_FILENAME': 'market_data.csv',
    'COLLECTION_INTERVAL_SECONDS': 60,  # Собирать данные раз в минуту
    'POOL_ADDRESS': '0xb4e16d0168e52d35cacd2c6185b44281ec28c9dc', # Uniswap V2: WETH-USDC
    'PRICE_HISTORY_MINUTES': 5, # Сколько минут хранить историю цен для расчета волатильности
}

class HMMDataCollector:
    """
    Класс для сбора и сохранения рыночных данных.
    """
    def __init__(self, config: Dict):
        self.config = config
        self.csv_filename = self.config['CSV_FILENAME']
        
        # Настройка логирования
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)

        # Очередь для хранения недавних цен для расчета волатильности
        history_size = int((self.config['PRICE_HISTORY_MINUTES'] * 60) / self.config['COLLECTION_INTERVAL_SECONDS'])
        self.price_history = deque(maxlen=history_size)
        
        # Заголовки для CSV-файла
        self.csv_headers = [
            'timestamp', 'datetime', 'eth_price_usd', 'usdc_price_usd', 
            'price_ratio', 'price_change_1min', 'volatility_5min',
            'trend_direction', 'pool_liquidity_usd', 'reserve_eth', 
            'reserve_usdc', 'volume_24h_usd', 'volume_1h_usd',
            'liquidity_regime', 'market_regime'
        ]
        self._setup_csv_file()

    def _setup_csv_file(self):
        """Создает CSV-файл с заголовками, если он еще не существует."""
        if not os.path.exists(self.csv_filename):
            with open(self.csv_filename, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.csv_headers)
                writer.writeheader()
            self.logger.info(f"CSV файл '{self.csv_filename}' создан с заголовками.")

    def get_token_price(self, token_id: str = 'ethereum') -> Optional[float]:
        """Получить текущую цену токена через API CoinGecko."""
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={token_id}&vs_currencies=usd"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data[token_id]['usd']
        except requests.RequestException as e:
            self.logger.warning(f"Не удалось получить цену для {token_id}: {e}")
            return None

    def get_pool_liquidity_data(self) -> Dict[str, float]:
        """Получить данные о ликвидности пула через API DeFiLlama."""
        try:
            url = f"https://api.llama.fi/pool/{self.config['POOL_ADDRESS']}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json().get('data', {})
            
            # API может возвращать резервы в токенах, а не в USD. 
            # Для простоты используем TVL (Total Value Locked) как общую ликвидность.
            return {
                'pool_liquidity_usd': data.get('tvlUsd', 0),
                'reserve_eth': 0,  # Требует доп. логики для конвертации
                'reserve_usdc': 0
            }
        except requests.RequestException as e:
            self.logger.warning(f"Не удалось получить данные о ликвидности: {e}")
            return {'pool_liquidity_usd': 0, 'reserve_eth': 0, 'reserve_usdc': 0}

    def get_trading_volume_data(self) -> Dict[str, float]:
        """Получить данные об объеме торгов через API CoinGecko."""
        try:
            # Ищем тикеры для биржи Uniswap V2
            url = "https://api.coingecko.com/api/v3/exchanges/uniswap_v2/tickers"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            tickers = response.json().get('tickers', [])
            
            # Ищем наш пул по адресу контракта
            for ticker in tickers:
                if ticker.get('pool_id', '').lower() == self.config['POOL_ADDRESS'].lower():
                    return {
                        'volume_24h_usd': float(ticker.get('converted_volume', {}).get('usd', 0)),
                        'volume_1h_usd': 0  # CoinGecko API не предоставляет часовой объем
                    }
            self.logger.warning("Тикер для пула не найден в API CoinGecko.")
            return {'volume_24h_usd': 0, 'volume_1h_usd': 0}
        except requests.RequestException as e:
            self.logger.warning(f"Не удалось получить данные об объеме: {e}")
            return {'volume_24h_usd': 0, 'volume_1h_usd': 0}

    def _calculate_metrics(self, current_price: float) -> (float, float):
        """Рассчитывает изменение цены и волатильность."""
        self.price_history.append(current_price)
        
        # Изменение цены за 1 минуту
        price_change_1min = 0.0
        if len(self.price_history) > 1:
            # Берем предпоследний элемент (цена минуту назад)
            prev_price = self.price_history[-2]
            price_change_1min = ((current_price / prev_price) - 1) * 100

        # Волатильность за 5 минут (стандартное отклонение изменений)
        volatility_5min = 0.0
        if len(self.price_history) > 2:
            prices = np.array(list(self.price_history))
            returns = (prices[1:] / prices[:-1]) - 1
            volatility_5min = np.std(returns) * 100
            
        return price_change_1min, volatility_5min

    def _determine_trend(self, price_change: float) -> str:
        """Определяет простое направление тренда."""
        if price_change > 0.01: return 'Up'
        elif price_change < -0.01: return 'Down'
        else: return 'Sideways'

    def determine_liquidity_regime(self, liquidity_usd: float, volume_24h: float) -> str:
        """Определяет режим ликвидности на основе оборота."""
        if liquidity_usd == 0: return 'Unknown'
        turnover_ratio = volume_24h / liquidity_usd
        if turnover_ratio > 1.5: return 'High_Activity'
        elif turnover_ratio > 0.5: return 'Medium_Activity'
        elif turnover_ratio > 0.1: return 'Low_Activity'
        else: return 'Stagnant'

    def get_current_market_data(self) -> Optional[Dict]:
        """Собирает все метрики и формирует единый словарь."""
        self.logger.info("Сбор нового набора данных...")
        eth_price = self.get_token_price('ethereum')
        if not eth_price: return None

        liquidity_data = self.get_pool_liquidity_data()
        volume_data = self.get_trading_volume_data()
        
        price_change, volatility = self._calculate_metrics(eth_price)
        trend = self._determine_trend(price_change)
        liquidity_regime = self.determine_liquidity_regime(
            liquidity_data['pool_liquidity_usd'],
            volume_data['volume_24h_usd']
        )
        
        current_time = datetime.now()
        data_point = {
            'timestamp': int(current_time.timestamp()),
            'datetime': current_time.strftime('%Y-%m-%d %H:%M:%S'),
            'eth_price_usd': round(eth_price, 2),
            'usdc_price_usd': 1.0, # Принимаем цену USDC за 1.0
            'price_ratio': round(eth_price, 2),
            'price_change_1min': round(price_change, 5),
            'volatility_5min': round(volatility, 5),
            'trend_direction': trend,
            'pool_liquidity_usd': round(liquidity_data['pool_liquidity_usd'], 2),
            'reserve_eth': round(liquidity_data['reserve_eth'], 4),
            'reserve_usdc': round(liquidity_data['reserve_usdc'], 2),
            'volume_24h_usd': round(volume_data['volume_24h_usd'], 2),
            'volume_1h_usd': round(volume_data['volume_1h_usd'], 2),
            'liquidity_regime': liquidity_regime,
            'market_regime': ''  # Это поле будет заполнено анализатором
        }
        return data_point

    def write_to_csv(self, data: Dict):
        """Дописывает строку данных в CSV-файл."""
        try:
            with open(self.csv_filename, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.csv_headers)
                writer.writerow(data)
            self.logger.info(f"Данные успешно сохранены в {self.csv_filename}")
        except IOError as e:
            self.logger.error(f"Ошибка записи в файл: {e}")

    def run(self):
        """Главный цикл работы сборщика."""
        self.logger.info("Запуск сборщика данных...")
        while True:
            try:
                market_data = self.get_current_market_data()
                if market_data:
                    self.write_to_csv(market_data)
                
                self.logger.info(f"Пауза на {self.config['COLLECTION_INTERVAL_SECONDS']} секунд...")
                time.sleep(self.config['COLLECTION_INTERVAL_SECONDS'])

            except KeyboardInterrupt:
                self.logger.info("Сборщик остановлен вручную.")
                break
            except Exception as e:
                self.logger.error(f"Произошла ошибка в главном цикле: {e}")
                time.sleep(self.config['COLLECTION_INTERVAL_SECONDS'])


if __name__ == "__main__":
    collector = HMMDataCollector(config=CONFIG)
    collector.run()