"""
Enhanced Discovery Agent - MVP Pump Detection

Адаптированная версия Discovery Agent с реалистичными pump фильтрами.
Основано на фидбеке Gemini - убраны недоступные проверки.

Author: Crypto Multi-Agent Team (MVP Version)
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..discovery.discovery_agent import TokenDiscoveryReport, discover_new_tokens, logger

# Импорт pump models
from .pump_models import PumpIndicators, NarrativeType
from .realistic_scoring import MVP_SCORING_WEIGHTS

# Настройка логгера
logger = logging.getLogger(__name__)

# === РЕАЛИСТИЧНЫЕ ФИЛЬТРЫ ДЛЯ MVP ===

# Базовые фильтры для отсева мусора
MVP_BASIC_FILTERS = {
    'min_liquidity_usd': 5000,      # Снижен порог для раннего обнаружения
    'min_volume_24h_usd': 2000,     # Минимальная активность
    'max_age_hours': 48,            # Расширен для MVP
    'max_buy_tax': 0.10,            # Максимальный налог 10%
    'max_sell_tax': 0.15            # Максимальный налог 15%
}

# Индикаторы потенциального пампа (доступные через API)
PUMP_POSITIVE_SIGNALS = {
    'rapid_volume_growth': 500,     # Рост объема на 500%+ за час
    'early_age_threshold': 6,       # Очень новые токены (<6 часов)
    'high_price_momentum': 100,     # Рост цены >100% за час
    'liquidity_growth_1h': 200      # Рост ликвидности >200% за час
}


def initial_pump_screening(pair_data: Dict[str, Any]) -> int:
    """
    Реалистичная начальная проверка на pump потенциал.
    
    На основе фидбека Gemini: используем ТОЛЬКО данные из DexScreener,
    без сложных ончейн-вычислений.
    
    Args:
        pair_data: Данные пары из DexScreener
        
    Returns:
        int: Предварительный score (0-60), 60+ идет на дальнейший анализ
    """
    score = 0
    
    try:
        # Базовая проверка ликвидности
        liquidity = pair_data.get('liquidity', {}).get('usd', 0)
        if liquidity < MVP_BASIC_FILTERS['min_liquidity_usd']:
            return 0  # Слишком низкая ликвидность
        
        # Базовая проверка объема
        volume_24h = pair_data.get('volume', {}).get('h24', 0) 
        if volume_24h < MVP_BASIC_FILTERS['min_volume_24h_usd']:
            return 0  # Слишком низкий объем
            
        # Проверка возраста
        created_at = pair_data.get('pairCreatedAt', 0) / 1000
        age_hours = (datetime.now().timestamp() - created_at) / 3600
        if age_hours > MVP_BASIC_FILTERS['max_age_hours']:
            return 0  # Слишком старый
            
        # === PUMP СИГНАЛЫ ===
        
        # Быстрый рост цены (доступно в DexScreener)
        price_change_1h = pair_data.get('priceChange', {}).get('h1', 0)
        if price_change_1h > PUMP_POSITIVE_SIGNALS['high_price_momentum']:
            score += 20  # Сильный momentum
        elif price_change_1h > 50:
            score += 10  # Умеренный momentum
            
        # Очень новый токен
        if age_hours < PUMP_POSITIVE_SIGNALS['early_age_threshold']:
            score += 15  # Ранний этап
        elif age_hours < 24:
            score += 10  # Относительно новый
            
        # Высокая ликвидность для нового токена
        if liquidity > 50000 and age_hours < 24:
            score += 15  # Хорошо финансируемый проект
        elif liquidity > 20000:
            score += 10
            
        # Высокий объем торгов
        liquidity_to_volume_ratio = volume_24h / liquidity if liquidity > 0 else 0
        if liquidity_to_volume_ratio > 2:  # Объем > 200% ликвидности
            score += 15  # Высокая активность торгов
        elif liquidity_to_volume_ratio > 1:
            score += 10
            
        # Базовые очки за прохождение фильтров
        score += 20
        
        logger.debug(f"Initial screening score: {score} for {pair_data.get('baseToken', {}).get('symbol')}")
        
        return min(score, 100)
        
    except Exception as e:
        logger.error(f"Error in initial_pump_screening: {e}")
        return 0


def analyze_pump_potential_realistic(discovery_report: TokenDiscoveryReport) -> PumpIndicators:
    """
    Реалистичный анализ pump потенциала.
    
    Использует ТОЛЬКО данные из TokenDiscoveryReport,
    без дополнительных API вызовов на этом этапе.
    
    Args:
        discovery_report: Отчет от базового Discovery Agent
        
    Returns:
        PumpIndicators: Структурированные pump индикаторы
    """
    indicators = PumpIndicators()
    
    try:
        # Заполняем доступные данные
        indicators.contract_address = discovery_report.base_token_address
        indicators.liquidity_usd = discovery_report.liquidity_usd
        indicators.volume_24h = discovery_report.volume_h24
        indicators.age_hours = discovery_report.age_minutes / 60
        
        # Простые эвристики на основе доступных данных
        
        # Высокая активность для нового токена
        if (discovery_report.age_minutes < 360 and  # < 6 часов
            discovery_report.volume_h24 > 10000):   # > $10k объем
            indicators.social_mentions += 1  # Эмуляция раннего обнаружения
            
        # Хорошее соотношение объем/ликвидность
        if discovery_report.liquidity_usd > 0:
            volume_ratio = discovery_report.volume_h24 / discovery_report.liquidity_usd
            if volume_ratio > 1.5:  # Высокая торговая активность
                indicators.social_mentions += 1
                
        # Предварительная оценка
        preliminary_score = min(
            (indicators.social_mentions * 30) + 
            (40 if discovery_report.discovery_score > 70 else 20),
            100
        )
        
        indicators.pump_probability_score = preliminary_score
        # Удаляем confidence_level - его нет в PumpIndicators
        
        logger.info(f"Pump potential analysis: {preliminary_score} for {discovery_report.base_token_symbol}")
        
        return indicators
        
    except Exception as e:
        logger.error(f"Error in analyze_pump_potential_realistic: {e}")
        return PumpIndicators()  # Возвращаем пустой объект при ошибке


def enhanced_discovery_with_pump_filter() -> List[TokenDiscoveryReport]:
    """
    Улучшенный discovery с pump фильтрами.
    
    Workflow:
    1. Базовый discovery (существующая функция)
    2. Pump screening для каждого найденного токена
    3. Фильтрация по pump потенциалу
    4. Возврат только перспективных токенов
    
    Returns:
        List[TokenDiscoveryReport]: Отфильтрованные токены с pump потенциалом
    """
    logger.info("🚀 Starting enhanced discovery with pump filters...")
    
    try:
        # 1. Базовый discovery (используем существующую функцию)
        all_discovered_tokens = discover_new_tokens()
        
        logger.info(f"Base discovery found {len(all_discovered_tokens)} tokens")
        
        # 2. Применяем pump фильтры
        pump_potential_tokens = []
        
        for token_report in all_discovered_tokens:
            try:
                # Эмулируем pair_data для screening
                pair_data = {
                    'liquidity': {'usd': token_report.liquidity_usd},
                    'volume': {'h24': token_report.volume_h24},
                    'priceChange': {'h1': token_report.price_change_h1},
                    'pairCreatedAt': token_report.pair_created_at.timestamp() * 1000,
                    'baseToken': {
                        'symbol': token_report.base_token_symbol,
                        'address': token_report.base_token_address
                    }
                }
                
                # Проводим pump screening
                pump_score = initial_pump_screening(pair_data)
                
                # Фильтруем по минимальному порогу (MVP threshold: 35 баллов)
                if pump_score >= 35:
                    # Обновляем discovery_score с учетом pump потенциала
                    token_report.discovery_score = max(token_report.discovery_score, pump_score)
                    token_report.discovery_reason += f" | Pump Score: {pump_score}"
                    
                    pump_potential_tokens.append(token_report)
                    
                    logger.info(f"✅ Token {token_report.base_token_symbol} passed pump filter with score {pump_score}")
                else:
                    logger.debug(f"❌ Token {token_report.base_token_symbol} filtered out: pump score {pump_score}")
                    
            except Exception as e:
                logger.error(f"Error processing token {token_report.base_token_symbol}: {e}")
                continue
        
        logger.info(f"🎯 Enhanced discovery completed: {len(pump_potential_tokens)}/{len(all_discovered_tokens)} tokens have pump potential")
        
        # Сортируем по pump потенциалу
        pump_potential_tokens.sort(key=lambda x: x.discovery_score, reverse=True)
        
        return pump_potential_tokens
        
    except Exception as e:
        logger.error(f"Error in enhanced_discovery_with_pump_filter: {e}")
        return []


def should_proceed_to_deep_analysis(token_report: TokenDiscoveryReport) -> bool:
    """
    Определить, стоит ли тратить API calls на глубокий анализ токена.
    
    Используется для оптимизации CoinGecko Demo calls (323/день).
    
    Args:
        token_report: Отчет от discovery
        
    Returns:
        bool: True если токен достоин дальнейшего анализа
    """
    try:
        # Высокий discovery score
        if token_report.discovery_score >= 70:
            return True
            
        # Очень новый + активный
        if (token_report.age_minutes < 120 and  # < 2 часов
            token_report.volume_h24 > 20000):   # > $20k объем
            return True
            
        # Высокий momentum
        if token_report.price_change_h1 > 200:  # > 200% рост за час
            return True
            
        # По умолчанию не тратим API calls
        return False
        
    except Exception as e:
        logger.error(f"Error in should_proceed_to_deep_analysis: {e}")
        return False


# === ТЕСТИРОВАНИЕ ===

async def test_enhanced_discovery():
    """Тестирование enhanced discovery с pump фильтрами"""
    print("🔍 Testing Enhanced Discovery with Pump Filters")
    print("=" * 60)
    
    try:
        # Тестовый запуск
        pump_tokens = enhanced_discovery_with_pump_filter()
        
        print(f"\n📊 Found {len(pump_tokens)} tokens with pump potential:")
        
        for i, token in enumerate(pump_tokens[:5]):  # Топ 5
            print(f"\n#{i+1}: {token.base_token_name} ({token.base_token_symbol})")
            print(f"   Score: {token.discovery_score}/100")
            print(f"   Age: {token.age_minutes:.1f} minutes")
            print(f"   Liquidity: ${token.liquidity_usd:,.0f}")
            print(f"   Reason: {token.discovery_reason}")
            print(f"   Deep Analysis: {'✅' if should_proceed_to_deep_analysis(token) else '❌'}")
            
    except Exception as e:
        logger.error(f"Error in test_enhanced_discovery: {e}")
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_enhanced_discovery())
