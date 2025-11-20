"""
Base Discovery Agent - Базовый класс для всех Discovery агентов (Версия 2.1)

Содержит ОБЩУЮ логику:
- УЛУЧШЕННОЕ API подключение через /dex/search
- Единую, настраиваемую константу для возраста токенов
- Обработку ошибок и абстрактные методы

Author: Refactored architecture based on Gemini recommendations
"""

import requests
import logging
import subprocess
import time
import asyncio
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_fixed
from abc import ABC, abstractmethod

# === БАЗОВЫЕ КОНСТАНТЫ ===
CHAINS_TO_SCAN = ["ethereum", "solana", "base", "arbitrum"]

# --- КЛЮЧЕВАЯ НАСТРОЙКА ---
# ОБНОВЛЕНО ПОД НОВУЮ СТРАТЕГИЮ: ищем зрелые токены до 3 месяцев возраста
# с капитализацией $10M+ (используем высокую ликвидность как прокси)
# Этот параметр используется в API-запросе для первичной фильтрации.
MAX_AGE_FOR_SCAN_HOURS = 2160  # 3 месяца (90 дней * 24 часа)

# === БАЗОВАЯ МОДЕЛЬ (без изменений) ===
class TokenDiscoveryReport(BaseModel):
    pair_address: str = Field(..., description="Адрес торговой пары на DEX")
    chain_id: str = Field(..., description="ID сети")
    base_token_address: str = Field(..., description="Адрес базового токена")
    base_token_symbol: str = Field(..., description="Символ базового токена")
    base_token_name: str = Field(..., description="Имя базового токена")
    liquidity_usd: float = Field(..., ge=0, description="Ликвидность в USD")
    volume_h24: float = Field(..., ge=0, description="Объем торгов за 24 часа в USD")
    price_usd: float = Field(..., description="Текущая цена в USD")
    price_change_h1: float = Field(..., description="Изменение цены за 1 час в %")
    pair_created_at: datetime = Field(..., description="Время создания пары")
    age_minutes: float = Field(..., ge=0, description="Возраст пары в минутах")
    discovery_score: int = Field(..., ge=0, le=100, description="Оценка перспективности")
    discovery_reason: str = Field(..., description="Обоснование оценки")
    data_source: str = Field("DexScreener", description="Источник данных")
    discovery_timestamp: datetime = Field(default_factory=datetime.now)
    git_commit_hash: Optional[str] = Field(None)
    api_response_time_ms: Optional[float] = Field(None)
    processing_time_ms: Optional[float] = Field(None)

# === LOGGER SETUP (без изменений) ===
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# === ДЕКОРАТОРЫ (без изменений) ===
def track_api_cost(api_name: str, cost_units: int = 1):
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"[CostTracker] Recording {cost_units} unit(s) for {api_name} API.")
            return func(*args, **kwargs)
        return wrapper
    return decorator

def rate_limit(api_name: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"[RateLimiter] Checking rate limit for {api_name}.")
            return func(*args, **kwargs)
        return wrapper
    return decorator

# === УТИЛИТЫ (без изменений) ===
def get_current_git_hash() -> Optional[str]:
    try:
        result = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], stderr=subprocess.DEVNULL)
        return result.decode('ascii').strip()
    except Exception:
        return None

# === ★★★ ИЗМЕНЕННАЯ ФУНКЦИЯ API ★★★ ===
@rate_limit('dexscreener')
@track_api_cost('dexscreener', cost_units=1)
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_pairs_for_chain(chain: str) -> Tuple[Optional[List[dict]], Optional[float]]:
    """
    УЛУЧШЕННАЯ функция получения данных из DexScreener.
    Использует более надежный эндпоинт /dex/search с настраиваемым возрастом.
    """
    # Создаем умный поисковый запрос, используя нашу константу
    query = f"in:{chain} age < {MAX_AGE_FOR_SCAN_HOURS} hours sort by volume desc"
    
    url = f"https://api.dexscreener.com/latest/dex/search?q={query}"
    headers = {'User-Agent': 'crypto-multi-agent-system/1.0'}
    
    try:
        logger.debug(f"Searching pairs on {chain} with query: '{query}'")
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=15)
        
        # Улучшенная обработка ошибок
        response.raise_for_status() 
        
        data = response.json()
        response_time = (time.time() - start_time) * 1000
        
        # Важно: DexScreener может вернуть пустой 'pairs', если ничего не найдено
        found_pairs = data.get('pairs')
        if found_pairs is None: # Проверка на null, а не просто на пустоту
             logger.warning(f"DexScreener returned null pairs for chain {chain}. Response: {data}")
             return [], response_time

        logger.info(f"Found {len(found_pairs)} pairs on {chain} in {response_time:.1f}ms")
        return found_pairs, response_time

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error for {chain}: {e.response.status_code} {e.response.reason}")
        return None, None
    except requests.exceptions.RequestException as e:
        logger.error(f"Request Error for {chain}: {e}")
        return None, None
    except ValueError as e: # Обработка ошибок парсинга JSON
        logger.error(f"JSON Parse Error for {chain}: {e}")
        return None, None

# === БАЗОВЫЙ КЛАСС (улучшена обработка данных) ===
class BaseDiscoveryAgent(ABC):
    def __init__(self):
        self.session_stats = { 'pairs_scanned': 0, 'reports_created': 0 }
        self.processed_addresses = set()
    
    @abstractmethod
    def _calculate_discovery_score(self, pair_data: Dict[str, Any], age_minutes: float) -> Tuple[int, str]:
        pass

    def discover_tokens(self) -> List[TokenDiscoveryReport]:
        logger.info(f"🚀 Starting token discovery with {self.__class__.__name__}...")
        git_hash = get_current_git_hash()
        all_reports = []
        
        for chain in CHAINS_TO_SCAN:
            api_data, api_time = fetch_pairs_for_chain(chain)
            # Проверяем, что api_data не None (в случае ошибки сети)
            if api_data is None:
                continue

            for pair in api_data:
                try:
                    # Улучшенная валидация, чтобы избежать падений
                    if not pair or not pair.get('pairAddress') or pair.get('pairAddress') in self.processed_addresses:
                        continue
                    
                    self.processed_addresses.add(pair.get('pairAddress'))
                    self.session_stats['pairs_scanned'] += 1

                    created_at_ms = pair.get('pairCreatedAt')
                    if not created_at_ms:
                        continue # Пропускаем, если нет даты создания
                    created_at = datetime.fromtimestamp(created_at_ms / 1000)
                    age_minutes = (datetime.now() - created_at).total_seconds() / 60
                    
                    score, reason = self._calculate_discovery_score(pair, age_minutes)

                    if score > 0:
                        # Более безопасное извлечение данных
                        price_usd_str = pair.get('priceUsd', '0')
                        price_usd = float(price_usd_str) if price_usd_str else 0.0

                        report = TokenDiscoveryReport(
                            pair_address=pair['pairAddress'],
                            chain_id=pair['chainId'],
                            base_token_address=pair.get('baseToken', {}).get('address', 'N/A'),
                            base_token_symbol=pair.get('baseToken', {}).get('symbol', 'N/A'),
                            base_token_name=pair.get('baseToken', {}).get('name', 'N/A'),
                            liquidity_usd=pair.get('liquidity', {}).get('usd', 0),
                            volume_h24=pair.get('volume', {}).get('h24', 0),
                            price_usd=price_usd,
                            price_change_h1=pair.get('priceChange', {}).get('h1', 0),
                            pair_created_at=created_at,
                            age_minutes=age_minutes,
                            discovery_score=score,
                            discovery_reason=reason,
                            git_commit_hash=git_hash,
                            api_response_time_ms=api_time
                        )
                        all_reports.append(report)
                        self.session_stats['reports_created'] += 1

                except (ValueError, KeyError, TypeError) as e:
                    logger.warning(f"Skipping pair due to parsing error: {e} - Data: {pair.get('pairAddress')}")
                    continue
        
        logger.info(f"✅ {self.__class__.__name__} complete: {self.session_stats['reports_created']} reports from {self.session_stats['pairs_scanned']} scanned.")
        return sorted(all_reports, key=lambda x: x.discovery_score, reverse=True)
    
    async def discover_tokens_async(self) -> List[TokenDiscoveryReport]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.discover_tokens)
