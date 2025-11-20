"""
CoinGecko API Client - ИСПРАВЛЕННАЯ ВЕРСИЯ с Rate Limiting

Обертка для CoinGecko API с улучшенным управлением rate limiting:
- Задержки между вызовами (4 сек)
- Retry с exponential backoff
- Обработка 429 ошибок

Author: Crypto Multi-Agent System - Fixed Version
"""
import os
import requests
from dotenv import load_dotenv
import logging
import time
from typing import Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

# Загружаем переменные из .env файла
load_dotenv()
logger = logging.getLogger(__name__)

# Словарь для маппинга ID сетей (можно расширять)
CHAIN_ID_MAP = {
    'ethereum': 'ethereum',
    'bsc': 'binance-smart-chain',
    'polygon': 'polygon-pos',
    'arbitrum': 'arbitrum-one',
    'base': 'base',
    'solana': 'solana'
}

class CoinGeckoClient:
    """Клиент для взаимодействия с CoinGecko API с улучшенным rate limiting."""
    def __init__(self):
        self.api_key = os.getenv("COINGECKO_API_KEY")
        self.base_url = "https://api.coingecko.com/api/v3"
        
        # Rate limiting configuration - КОНСЕРВАТИВНЫЕ НАСТРОЙКИ
        self.last_request_time = 0
        self.min_delay_between_calls = 4.0  # 4 секунды между вызовами
        
        if not self.api_key:
            logger.warning("COINGECKO_API_KEY не найден в .env файле. Клиент будет работать в mock-режиме.")
            self.is_mock = True
        else:
            self.is_mock = False
            logger.info(f"CoinGecko клиент инициализирован с rate limiting: {self.min_delay_between_calls}s между вызовами")
    
    def _enforce_rate_limit(self):
        """Принудительно соблюдать rate limit с задержкой между вызовами."""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_delay_between_calls:
            sleep_time = self.min_delay_between_calls - time_since_last_request
            logger.debug(f"Rate limiting: ожидание {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        reraise=True
    )
    def _make_request_with_retry(self, url: str, params: dict, headers: dict) -> requests.Response:
        """Выполняет HTTP запрос с retry логикой и exponential backoff."""
        self._enforce_rate_limit()
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            # Проверяем на rate limiting
            if response.status_code == 429:
                logger.warning("CoinGecko rate limit exceeded, will retry with exponential backoff")
                raise requests.exceptions.RequestException("Rate limit exceeded")
                
            return response
            
        except requests.exceptions.Timeout:
            logger.warning("CoinGecko request timeout, retrying...")
            raise
        except requests.exceptions.ConnectionError:
            logger.warning("CoinGecko connection error, retrying...")
            raise

    def get_token_info_by_contract(self, chain_name: str, contract_address: str) -> Dict[str, any]:
        """
        Получает нарратив и другую информацию о токене с улучшенным error handling.
        chain_name должен быть в формате DexScreener (e.g., 'ethereum', 'base').
        """
        if self.is_mock:
            logger.debug(f"[CoinGecko MOCK] Получение данных для {contract_address} на {chain_name}")
            # Возвращаем mock-данные, чтобы тесты проходили
            return {
                "categories": ["artificial-intelligence", "layer-1"], 
                "community_score": 65.5
            }
        
        coingecko_chain_id = CHAIN_ID_MAP.get(chain_name.lower())
        if not coingecko_chain_id:
            logger.error(f"Неизвестный chain_name для CoinGecko: {chain_name}")
            return {}
        
        url = f"{self.base_url}/coins/{coingecko_chain_id}/contract/{contract_address}"
        # Для Demo API ключ передается как параметр, а не заголовок
        params = {'x_cg_demo_api_key': self.api_key}
        headers = {'accept': 'application/json'}
        
        try:
            # Используем новый метод с retry логикой
            response = self._make_request_with_retry(url, params, headers)
            
            if response.status_code == 404:
                logger.warning(f"Токен {contract_address} не найден на CoinGecko.")
                return {}
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Сетевая ошибка при запросе к CoinGecko: {e}")
            return {}
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при обработке ответа CoinGecko: {e}")
            return {}

    def extract_token_metadata(self, response_json: Dict[str, any]) -> Dict[str, any]:
        """
        Извлекает ключевые метаданные токена из ответа CoinGecko.
        """
        if not response_json:
            return {}
        
        try:
            metadata = {
                "categories": response_json.get("categories", []),
                "community_score": response_json.get("community_score", 0),
                "market_cap": response_json.get("market_data", {}).get("market_cap", {}).get("usd", 0),
                "total_volume": response_json.get("market_data", {}).get("total_volume", {}).get("usd", 0),
                "price_change_24h": response_json.get("market_data", {}).get("price_change_percentage_24h", 0)
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении метаданных: {e}")
            return {}
