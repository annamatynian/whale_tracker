

import requests
import logging
import subprocess
import time
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, ValidationError
from tenacity import retry, stop_after_attempt, wait_fixed

# --- 1. UPDATED Configuration Constants ---
# Импортируем обновленные константы из центрального config (Principle #4)
from config.constants import (
    MIN_LIQUIDITY_USD, MIN_VOLUME_H24_USD, MIN_DISCOVERY_SCORE,
    LIQUIDITY_SCORING_TIERS, VOLUME_MULTIPLIERS, TEMP_SCORING_THRESHOLDS,
    AGE_THRESHOLD_VERY_NEW_MINUTES, AGE_THRESHOLD_NEW_HOURS,
    PRICE_CHANGE_THRESHOLD_HIGH, PRICE_CHANGE_THRESHOLD_MEDIUM
)

CHAINS_TO_SCAN = ["ethereum", "solana", "base", "arbitrum"]

# ОБНОВЛЕННЫЕ ФИЛЬТРЫ (синхронизированы с constants.py)
MAX_PAIR_AGE_HOURS = 2160  # 3 месяца (как в constants.py)
LIQUIDITY_THRESHOLD_HIGH = 50000
VOLUME_THRESHOLD_HIGH = 100000

# === ОПТИМИЗИРОВАННЫЕ PUMP DETECTION FILTERS ===
# Используем обновленные значения из constants.py
PUMP_MIN_LIQUIDITY = MIN_LIQUIDITY_USD  # 30000 (было 5000)
PUMP_MAX_AGE_HOURS = 2160    # 3 месяца (было 48 часов) 
PUMP_MIN_VOLUME_24H = MIN_VOLUME_H24_USD  # 10000 (было 1000)
SCAM_DUMP_THRESHOLD = -50  # Avoid tokens that already dumped >50%


# --- 2. Pydantic Model (Data Contract) ---
class TokenDiscoveryReport(BaseModel):
    """
    Строгий контракт для результатов Discovery Agent.
    Описывает найденный токен и его ключевые метрики.
    """
    pair_address: str = Field(..., description="Адрес торговой пары на DEX")
    chain_id: str = Field(..., description="ID сети (e.g., 'ethereum', 'solana')")
    base_token_address: str = Field(..., description="Адрес базового токена")
    base_token_symbol: str = Field(..., description="Символ базового токена")
    base_token_name: str = Field(..., description="Имя базового токена")
    
    liquidity_usd: float = Field(..., ge=0, description="Ликвидность в USD")
    volume_h24: float = Field(..., ge=0, description="Объем торгов за 24 часа в USD")
    price_usd: float = Field(..., gt=0, description="Текущая цена в USD")
    price_change_h1: float = Field(..., description="Изменение цены за 1 час в %")
    
    pair_created_at: datetime = Field(..., description="Время создания пары")
    age_minutes: float = Field(..., ge=0, description="Возраст пары в минутах")
    
    discovery_score: int = Field(..., ge=0, le=100, description="Оценка перспективности от 0 до 100")
    discovery_reason: str = Field(..., description="Краткое обоснование оценки")
    
    data_source: str = Field("DexScreener", description="Источник данных")
    discovery_timestamp: datetime = Field(default_factory=datetime.now, description="Время обнаружения")
    
    git_commit_hash: Optional[str] = Field(None, description="Git commit hash для воспроизводимости кода")
    api_response_time_ms: Optional[float] = Field(None, description="Время ответа API в миллисекундах")
    processing_time_ms: Optional[float] = Field(None, description="Общее время обработки в миллисекундах")

# --- 3. Logging Setup ---
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

# --- 4. Placeholder Tools (for Cost Management & Rate Limiting) ---
# In a real project, these would be imported from a shared `tools` module.
# This is a placeholder to demonstrate architecture without having the actual files.

def track_api_cost(api_name: str, cost_units: int = 1):
    """Placeholder decorator for Principle #8: Cost Management."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"[CostTracker] Recording {cost_units} unit(s) for {api_name} API.")
            return func(*args, **kwargs)
        return wrapper
    return decorator

def rate_limit(api_name: str):
    """Placeholder decorator for API Rate Limiting."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"[RateLimiter] Checking rate limit for {api_name}.")
            # In a real implementation, this would contain logic to sleep if needed.
            return func(*args, **kwargs)
        return wrapper
    return decorator

# --- 5. Utility & Core Functions ---
def get_current_git_hash() -> Optional[str]:
    """Gets the short hash of the current git commit."""
    try:
        result = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], stderr=subprocess.DEVNULL)
        return result.decode('ascii').strip()
    except Exception as e:
        logger.warning(f"Could not get git hash: {e}")
        return None

@rate_limit('dexscreener')
@track_api_cost('dexscreener', cost_units=1)
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def fetch_pairs_for_chain(chain: str) -> tuple[Optional[List[dict]], Optional[float]]:
    """
    Fetches the latest pairs for a specific chain from the Dex Screener API.
    This is a more reliable endpoint than a complex search query.
    """
    url = f"https://api.dexscreener.com/latest/dex/pairs/{chain}"
    headers = {'User-Agent': 'crypto-multi-agent-system/1.0'}
    
    try:
        logger.debug(f"Fetching pairs for chain: {chain}")
        start_time = time.time()
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        data = response.json()
        response_time = (time.time() - start_time) * 1000
        logger.debug(f"Fetched {len(data.get('pairs', []))} pairs from {chain} in {response_time:.1f}ms")
        return data.get('pairs'), response_time
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching data from Dex Screener for chain {chain}: {e}")
        return None, None
    except ValueError as e:
        logger.error(f"Error parsing JSON for chain {chain}: {e}")
        return None, None

def initial_screening(pair_data: Dict[str, Any]) -> int:
    """
    ОБНОВЛЕННЫЙ pump screening с новыми оптимизированными фильтрами.
    Использует константы из constants.py для консистентности.
    Returns 0-100 score for further analysis priority.
    """
    # Basic data validation
    if not pair_data or not pair_data.get('liquidity'):
        return 0
    
    liquidity_usd = pair_data.get('liquidity', {}).get('usd', 0)
    volume_24h = pair_data.get('volume', {}).get('h24', 0)
    price_change_24h = pair_data.get('priceChange', {}).get('h24', 0)
    
    # Filter out obvious scam/dump tokens using UPDATED thresholds
    if liquidity_usd < PUMP_MIN_LIQUIDITY:  # Now 30k instead of 5k
        return 0  # Too low liquidity, not interesting
    
    if price_change_24h < SCAM_DUMP_THRESHOLD:
        return 0  # Already dumped >50%, too late
    
    if volume_24h < PUMP_MIN_VOLUME_24H:  # Now 10k instead of 1k
        return 0  # No trading activity
    
    # Calculate age
    created_at = pair_data.get('pairCreatedAt', 0)
    if created_at == 0:
        return 10  # Unknown age, low priority
    
    age_hours = (time.time() - created_at/1000) / 3600
    if age_hours > PUMP_MAX_AGE_HOURS:  # Now allows up to 3 months
        return 0  # Too old for our strategy
    
    # Используем временные пороги для получения результатов
    base_score = TEMP_SCORING_THRESHOLDS.get('min_discovery_score', 30)
    
    # Bonus points for favorable conditions (обновленная логика)
    if liquidity_usd > 100000:  # $100k+ = premium tier
        base_score += 20  # Higher bonus for premium liquidity
    elif liquidity_usd > 50000:  # $50k+ = high tier 
        base_score += 15  # Good liquidity
    
    # Возрастные бонусы адаптированы под новую стратегию (до 3 месяцев)
    if age_hours < 24:  # Очень свежие
        base_score += 15
    elif age_hours < 168:  # До недели
        base_score += 10
    elif age_hours < 720:  # До месяца
        base_score += 5
    
    if price_change_24h > 20:
        base_score += 15  # Positive momentum
    
    return min(base_score, 90)  # Reserve 10 points for premium data

def calculate_discovery_score(token_data: Dict[str, Any], age_minutes: float) -> tuple[int, str]:
    """Обновленная функция с многоуровневой системой скоринга ликвидности"""
    # First run initial screening
    screening_score = initial_screening(token_data)
    if screening_score == 0:
        return 0, "Failed initial screening"
    
    score = screening_score
    reasons = [f"Screen={screening_score}"]

    # === НОВАЯ МНОГОУРОВНЕВАЯ СИСТЕМА СКОРИНГА ЛИКВИДНОСТИ ===
    liquidity = token_data.get('liquidity', {}).get('usd', 0)
    volume_24h = token_data.get('volume', {}).get('h24', 0)
    
    # Применяем уровни ликвидности из constants.py
    liquidity_bonus = 0
    liquidity_tier = "low"
    for tier_name, tier_data in LIQUIDITY_SCORING_TIERS.items():
        if liquidity >= tier_data['min_liquidity']:
            liquidity_bonus = max(liquidity_bonus, tier_data['bonus_points'])
            liquidity_tier = tier_name
    
    score += liquidity_bonus
    reasons.append(f"Liq=${liquidity/1000:.0f}k({liquidity_tier}:+{liquidity_bonus})")
    
    # Применяем множители объема из constants.py
    volume_multiplier = 1.0
    volume_tier = "base"
    for tier_name, tier_data in VOLUME_MULTIPLIERS.items():
        if volume_24h >= tier_data['min_volume']:
            volume_multiplier = max(volume_multiplier, tier_data['multiplier'])
            volume_tier = tier_name
    
    # Применяем множитель к базовому бонусу за объем
    base_volume_bonus = 5 if volume_24h > MIN_VOLUME_H24_USD else 0
    final_volume_bonus = int(base_volume_bonus * volume_multiplier)
    score += final_volume_bonus
    reasons.append(f"Vol=${volume_24h/1000:.0f}k({volume_tier}:x{volume_multiplier}=+{final_volume_bonus})")

    return min(score, 100), " | ".join(reasons)

# --- 6. Core Agent Logic (Sync & Async) ---
def analyze_pump_potential(pair_data: Dict[str, Any]) -> int:
    """
    Pump potential analysis using REALISTIC data only.
    Based on Gemini's corrected approach.
    """
    return initial_screening(pair_data)

def discover_new_tokens() -> List[TokenDiscoveryReport]:
    """
    Core synchronous function of the Discovery Agent. It fetches, filters,
    scores, and reports on new token pairs across multiple chains.
    """
    start_processing = time.time()
    logger.info("🚀 Starting new token discovery process...")
    git_hash = get_current_git_hash()
    
    all_reports = []
    total_api_time = 0
    scanned_pairs_count = 0
    processed_addresses = set()

    for chain in CHAINS_TO_SCAN:
        api_data, api_time = fetch_pairs_for_chain(chain)
        if not api_data:
            continue
        
        total_api_time += api_time or 0
        scanned_pairs_count += len(api_data)

        for pair in api_data:
            try:
                if not pair or pair.get('pairAddress') in processed_addresses:
                    continue
                processed_addresses.add(pair.get('pairAddress'))

                created_at = datetime.fromtimestamp(pair.get('pairCreatedAt', 0) / 1000)
                age_minutes = (datetime.now() - created_at).total_seconds() / 60
                
                # Apply filters after fetching
                if not (
                    age_minutes <= MAX_PAIR_AGE_HOURS * 60 and
                    pair.get('liquidity', {}).get('usd', 0) >= MIN_LIQUIDITY_USD and
                    pair.get('volume', {}).get('h24', 0) >= MIN_VOLUME_H24_USD
                ):
                    continue

                score, reason = calculate_discovery_score(pair, age_minutes)
                if score < MIN_DISCOVERY_SCORE:
                    continue

                report_data = {
                    "pair_address": pair['pairAddress'], "chain_id": pair['chainId'],
                    "base_token_address": pair['baseToken']['address'], "base_token_symbol": pair['baseToken']['symbol'],
                    "base_token_name": pair['baseToken']['name'], "liquidity_usd": pair['liquidity']['usd'],
                    "volume_h24": pair['volume']['h24'], "price_usd": float(pair.get('priceUsd', 0)),
                    "price_change_h1": pair['priceChange']['h1'], "pair_created_at": created_at,
                    "age_minutes": age_minutes, "discovery_score": score, "discovery_reason": reason,
                    "git_commit_hash": git_hash, "api_response_time_ms": api_time,
                }
                all_reports.append(TokenDiscoveryReport(**report_data))
            except (ValidationError, TypeError, KeyError) as e:
                logger.warning(f"⚠️ Skipping pair {pair.get('pairAddress')} due to validation/parsing error: {e}")

    processing_time = (time.time() - start_processing) * 1000
    for report in all_reports:
        report.processing_time_ms = processing_time

    logger.info(
        f"✅ Discovery complete. Found {len(all_reports)} promising tokens from {scanned_pairs_count} scanned. "
        f"(Total API: {total_api_time:.1f}ms, Total Processing: {processing_time:.1f}ms)"
    )
    return all_reports

async def discover_new_tokens_async() -> List[TokenDiscoveryReport]:
    """
    Async wrapper for the core discovery logic.
    This allows the synchronous, blocking code to be run in a separate thread
    without blocking an asyncio event loop, which is ideal for an orchestrator.
    """
    logger.info("Running synchronous discovery logic in a separate thread...")
    loop = asyncio.get_running_loop()
    # Use loop.run_in_executor for CPU-bound or blocking I/O tasks
    return await loop.run_in_executor(None, discover_new_tokens)

# --- 7. Example Usage & Testing ---
async def main():
    """Main async function for testing the Discovery Agent."""
    print("🔍 Discovery Agent - Testing Mode (v2)")
    print("=" * 50)
    
    try:
        reports = await discover_new_tokens_async()
        print(f"\n📊 Found {len(reports)} promising tokens.")
        
        if not reports:
            print("\nNo tokens met the discovery criteria.")
            return

        sorted_reports = sorted(reports, key=lambda r: r.discovery_score, reverse=True)
        
        print("\n--- Top Discoveries ---")
        for i, report in enumerate(sorted_reports[:5]):
            print(f"\n#{i+1}: {report.base_token_name} ({report.base_token_symbol}) on {report.chain_id}")
            print("-" * 30)
            print(f"   📈 Score: {report.discovery_score}/100 | 💡 Reason: {report.discovery_reason}")
            print(f"   💰 Price: ${report.price_usd} | 💧 Liquidity: ${report.liquidity_usd:,.0f} | 📊 Vol(24h): ${report.volume_h24:,.0f}")
            print(f"   🕒 Age: {report.age_minutes:.1f} minutes | 🔗 Pair: ...{report.pair_address[-6:]}")
        
        if len(sorted_reports) > 5: print(f"\n...and {len(sorted_reports) - 5} more.")

    except Exception as e:
        logger.error(f"❌ Unexpected error in main(): {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())