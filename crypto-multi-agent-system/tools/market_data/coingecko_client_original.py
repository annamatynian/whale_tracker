"""
CoinGecko API Client

Обертка для CoinGecko API для получения данных о нарративе и сообществе.
- Категории (нарративы)
- Community Score

Author: Crypto Multi-Agent System
"""
import os
import requests
from dotenv import load_dotenv
import logging
import asyncio
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
    """Клиент для взаимодействия с CoinGecko API."""
    def __init__(self):
        self.api_key = os.getenv("COINGECKO_API_KEY")
        self.base_url = "https://api.coingecko.com/api/v3"
        if not self.api_key:
            logger.warning("COINGECКО_API_KEY не найден в .env файле. Клиент будет работать в mock-режиме.")
            self.is_mock = True
        else:
            self.is_mock = False

    def get_token_info_by_contract(self, chain_name: str, contract_address: str) -> Dict[str, any]:
        """
        Получает нарратив и другую информацию о токене.
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
            response = requests.get(url, headers=headers, params=params, timeout=15)
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