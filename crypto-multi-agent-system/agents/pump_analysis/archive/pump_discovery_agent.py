"""
Pump Discovery Agent - Наследуется от BaseDiscoveryAgent

ПЕРЕОПРЕДЕЛЯЕТ только pump-specific логику:
- should_analyze_pair(): pump фильтры
- calculate_score(): pump probability scoring
- create_report(): PumpAnalysisReport

НАСЛЕДУЕТ всю инфраструктуру:
- API подключения, rate limiting, обработку ошибок, async поддержку

Author: Refactored with inheritance pattern (Gemini recommendations)
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime

# Наследуем от базового класса
from ..discovery.base_discovery_agent import BaseDiscoveryAgent, TokenDiscoveryReport, logger

# Импортируем pump-specific модели
from .pump_models import PumpIndicators, PumpAnalysisReport, ApiUsageTracker, NarrativeType
from .realistic_scoring import RealisticScoringMatrix, RealisticPumpIndicators

# === PUMP-SPECIFIC CONFIGURATION (ОБНОВЛЕНО ПОД СТРАТЕГИЮ) ===
PUMP_FILTERS = {
    # НОВАЯ СТРАТЕГИЯ: зрелые токены с высокой капитализацией
    # ПРИМЕЧАНИЕ: DexScreener не предоставляет market_cap, используем ликвидность как прокси
    'min_liquidity_usd': 200000,      # $200K ликвидность ≈ прокси для $10M+ капитализации
    'min_volume_24h': 100000,         # $100K объем (активная торговля)
    
    # ВОЗРАСТНЫЕ ФИЛЬТРЫ: до 3 месяцев (вместо 2 дней!)
    'min_age_hours': 24,              # Минимум 1 день (для корректных метрик)
    'max_age_hours': 2160,            # Максимум 3 месяца (90 дней * 24ч)
    
    # ТЕХНИЧЕСКИЕ КРИТЕРИИ
    'min_positive_momentum': 5        # Мягче для зрелых токенов
}

# Адаптивные пороги Volume Acceleration по сетям
VOLUME_ACCELERATION_THRESHOLDS = {
    'base': 1000,        # Низкие комиссии
    'solana': 1000,      # Низкие комиссии
    'arbitrum': 1500,    # Средние комиссии
    'polygon': 1200,     # Средние комиссии
    'ethereum': 2500,    # Высокие комиссии
    'bsc': 1200,         # Средние комиссии
    'default': 1500      # Универсальный порог
}

PUMP_SCORING_WEIGHTS_MVP = {
    'basic_screening': 40,          # Проходит базовые фильтры
    'early_detection_bonus': 20,    # Очень свежий токен
    'liquidity_bonus': 15,          # Хорошая ликвидность
    'momentum_bonus': 15,           # Положительная динамика  
    'volume_acceleration_bonus': 15, # Volume Acceleration (увеличено!)
    'multi_chain_bonus': 10         # Присутствие на нескольких сетях
}

class PumpDiscoveryAgent(BaseDiscoveryAgent):
    """
    Specialized Discovery Agent для поиска pump кандидатов
    
    НАСЛЕДУЕТ от BaseDiscoveryAgent:
    ✅ API подключения и сканирование сетей
    ✅ Rate limiting и cost tracking  
    ✅ Обработку ошибок и async поддержку
    ✅ Метрики производительности
    ✅ Общий workflow discover_tokens()
    
    ПЕРЕОПРЕДЕЛЯЕТ pump-specific логику:
    🎯 should_analyze_pair() - pump фильтры
    🎯 calculate_score() - pump probability scoring  
    🎯 create_report() - PumpAnalysisReport
    """
    
    def __init__(self):
        super().__init__()  # Вызываем конструктор базового класса
        self.api_tracker = ApiUsageTracker()
        
        # Дополнительные pump-specific статистики
        self.pump_stats = {
            'pump_candidates_found': 0,
            'high_potential_found': 0,
            'filtered_by_min_age': 0,    # НОВОЕ: слишком молодые токены (<25ч)
            'filtered_by_max_age': 0,    # НОВОЕ: слишком старые токены (>48ч)
            'filtered_by_liquidity': 0,
            # 'filtered_by_dump': 0  # УБРАНО - больше не фильтруем по дампу
        }
    
    def should_analyze_pair(self, pair_data: Dict[str, Any]) -> bool:
        """
        ПЕРЕОПРЕДЕЛЯЕМ: pump-specific фильтры
        
        Отфильтровываем токены, которые не подходят для pump analysis:
        - Слишком низкая ликвидность
        - Уже упавшие (дамп > 50%)  
        - Слишком старые
        - Нет торговой активности
        """
        # Базовая валидация данных
        if not pair_data or not pair_data.get('liquidity'):
            return False
        
        liquidity_usd = pair_data.get('liquidity', {}).get('usd', 0)
        volume_24h = pair_data.get('volume', {}).get('h24', 0)
        price_change_24h = pair_data.get('priceChange', {}).get('h24', 0)
        
        # Фильтр 1: Минимальная ликвидность
        if liquidity_usd < PUMP_FILTERS['min_liquidity_usd']:
            self.pump_stats['filtered_by_liquidity'] += 1
            return False
        
        # Фильтр 2: УБРАН - больше не исключаем токены на дампе
        # Новые токены могут падать перед мощным ростом
        
        # Фильтр 3: Минимальная торговая активность
        if volume_24h < PUMP_FILTERS['min_volume_24h']:
            return False
        
        # Фильтр 4: Возраст токена (окно 25-48 часов для корректных 24ч метрик)
        created_at = pair_data.get('pairCreatedAt', 0)
        if created_at == 0:
            return False
        
        age_hours = (datetime.now().timestamp() - created_at/1000) / 3600
        
        # КРИТИЧЕСКИЙ ФИХ: Проверяем МИНИМАЛЬНЫЙ возраст для корректного volume_h24
        if age_hours < PUMP_FILTERS['min_age_hours']:
            self.pump_stats['filtered_by_min_age'] += 1
            return False
            
        # Проверяем максимальный возраст
        if age_hours > PUMP_FILTERS['max_age_hours']:
            self.pump_stats['filtered_by_max_age'] += 1
            return False
        
        return True  # Прошел все pump фильтры
    
    def _calculate_discovery_score(self, pair_data: Dict[str, Any], age_minutes: float) -> Tuple[int, str]:
        """
        ПЕРЕОПРЕДЕЛЯЕМ: pump probability scoring
        
        Рассчитываем вероятность пампа на основе:
        - Возраста токена (свежесть)
        - Ликвидности (профессиональность)  
        - Momentum (текущая динамика)
        - Активности торгов
        """
        score = 0
        reasons = []
        
        # Данные для анализа
        liquidity_usd = pair_data.get('liquidity', {}).get('usd', 0)
        volume_24h = pair_data.get('volume', {}).get('h24', 0)
        volume_h1 = pair_data.get('volume', {}).get('h1', 0)
        volume_h6 = pair_data.get('volume', {}).get('h6', 0)
        price_change_1h = pair_data.get('priceChange', {}).get('h1', 0)
        price_change_6h = pair_data.get('priceChange', {}).get('h6', 0)
        price_change_24h = pair_data.get('priceChange', {}).get('h24', 0)
        age_hours = age_minutes / 60
        
        # Базовые очки за прохождение фильтров
        score += PUMP_SCORING_WEIGHTS_MVP['basic_screening']
        reasons.append(f"Passed pump filters ({PUMP_SCORING_WEIGHTS_MVP['basic_screening']}pts)")
        
        # Бонус за раннее обнаружение
        if age_hours < 24:
            bonus = PUMP_SCORING_WEIGHTS_MVP['early_detection_bonus']
            score += bonus
            reasons.append(f"Fresh token: {age_hours:.1f}h (+{bonus}pts)")
        elif age_hours < 48:
            bonus = PUMP_SCORING_WEIGHTS_MVP['early_detection_bonus'] // 2
            score += bonus
            reasons.append(f"Recent token: {age_hours:.1f}h (+{bonus}pts)")
        
        # Бонус за ликвидность (профессиональность команды)
        if liquidity_usd > 50000:
            bonus = PUMP_SCORING_WEIGHTS_MVP['liquidity_bonus']
            score += bonus
            reasons.append(f"High liquidity: ${liquidity_usd:,.0f} (+{bonus}pts)")
        elif liquidity_usd > 20000:
            bonus = PUMP_SCORING_WEIGHTS_MVP['liquidity_bonus'] // 2
            score += bonus
            reasons.append(f"Good liquidity: ${liquidity_usd:,.0f} (+{bonus}pts)")
        
        # Бонус за положительную динамику
        if price_change_24h > 50:
            bonus = PUMP_SCORING_WEIGHTS_MVP['momentum_bonus']
            score += bonus
            reasons.append(f"Strong momentum: +{price_change_24h:.1f}% (+{bonus}pts)")
        elif price_change_24h > PUMP_FILTERS['min_positive_momentum']:
            bonus = PUMP_SCORING_WEIGHTS_MVP['momentum_bonus'] // 2
            score += bonus
            reasons.append(f"Positive momentum: +{price_change_24h:.1f}% (+{bonus}pts)")
        
        # Бонус за высокую торговую активность
        volume_ratio = volume_24h / liquidity_usd if liquidity_usd > 0 else 0
        if volume_ratio > 2:  # Объем > 200% ликвидности
            bonus = 10
            score += bonus
            reasons.append(f"High trading activity (+{bonus}pts)")
        
        # === НОВЫЕ МЕТРИКИ ИЗ "VOLUME AND LIQUIDITY CORRECTED" ===
        
        # 1. Volume Acceleration (адаптивные пороги по сетям)
        if volume_h6 > 0 and volume_h1 > 0:
            is_accelerating = volume_h1 > (volume_h6 / 6)
            
            # Получаем чейн из pair_data
            chain_id = pair_data.get('chainId', 'unknown').lower()
            min_threshold = VOLUME_ACCELERATION_THRESHOLDS.get(chain_id, VOLUME_ACCELERATION_THRESHOLDS['default'])
            
            if is_accelerating and volume_h1 > min_threshold:
                bonus = PUMP_SCORING_WEIGHTS_MVP['volume_acceleration_bonus']
                score += bonus
                reasons.append(f"Volume accelerating on {chain_id} (+{bonus}pts)")
        
        # 2. Volume Ratio Range (фильтр качества активности)
        if volume_ratio < 0.5 and volume_ratio > 0:
            # Слишком низкая активность - подозрительно
            penalty = 10
            score -= penalty
            reasons.append(f"⚠️ Low volume ratio ({volume_ratio:.1f}) (-{penalty}pts)")
        elif 0.5 <= volume_ratio <= 3.0:
            # Здоровая активность - небольшой бонус
            bonus = 5
            score += bonus
            reasons.append(f"✅ Healthy volume ratio ({volume_ratio:.1f}) (+{bonus}pts)")
        elif volume_ratio > 3.0:
            # Подозрительно высокая активность - штраф
            penalty = 15  # Больше штраф чем за низкую активность
            score -= penalty
            reasons.append(f"🚨 Suspicious volume ratio ({volume_ratio:.1f}) (-{penalty}pts)")
        
        return max(0, min(score, 100)), " | ".join(reasons)
    
    def create_report(self, pair_data: Dict[str, Any], score: int, reason: str, 
                     age_minutes: float, git_hash: str, api_time: float) -> PumpAnalysisReport:
        """
        ПЕРЕОПРЕДЕЛЯЕМ: создание PumpAnalysisReport
        
        Создаем специализированный отчет для pump analysis
        с дополнительными полями и рекомендациями.
        """
        created_at = datetime.fromtimestamp(pair_data.get('pairCreatedAt', 0) / 1000)
        
        # Создаем pump-specific индикаторы
        indicators = PumpIndicators(
            contract_address=pair_data['baseToken']['address'],
            narrative_alignment=NarrativeType.UNKNOWN,  # Будет заполнено CoinGecko Agent
            is_honeypot=True,  # По умолчанию - будет проверено GoPlus Agent
            is_open_source=False,  # По умолчанию - будет проверено GoPlus Agent
            social_mentions=0,  # Будет заполнено Telegram Agent
            liquidity_usd=pair_data['liquidity']['usd'],
            volume_24h=pair_data['volume']['h24'],
            age_hours=age_minutes / 60,
            pump_probability_score=score
        )
        
        # Определяем следующие шаги на основе score
        next_steps = []
        if score >= 80:
            next_steps.extend([
                "🚀 HIGH PRIORITY: Full pump analysis",
                "🔍 CoinGecko narrative check",
                "🛡️ GoPlus security validation",
                "📱 Telegram social monitoring",
                "💰 Position sizing calculation"
            ])
            self.pump_stats['high_potential_found'] += 1
        elif score >= 60:
            next_steps.extend([
                "🎯 MEDIUM PRIORITY: Extended analysis",
                "🔍 CoinGecko narrative check", 
                "🛡️ GoPlus security validation"
            ])
        elif score >= 40:
            next_steps.extend([
                "👀 WATCH LIST: Monitor for changes",
                "📊 Track price action"
            ])
        else:
            next_steps.append("📉 LOW PRIORITY: Basic monitoring")
        
        # Создаем PumpAnalysisReport
        pump_report = PumpAnalysisReport(
            contract_address=pair_data['baseToken']['address'],
            chain_id=pair_data.get('chainId', 'unknown'),
            token_symbol=pair_data['baseToken']['symbol'],
            token_name=pair_data['baseToken']['name'],
            
            indicators=indicators,
            
            # Пока только базовый score (будет дополнен другими агентами)
            narrative_score=0,  # CoinGecko Agent
            security_score=0,   # GoPlus Agent  
            social_score=0,     # Telegram Agent
            
            reasoning=reason.split(" | "),
            red_flags=[],       # Пока пусто - заполнят другие агенты
            
            data_sources_used=["DexScreener"],
            api_calls_made=1,
            
            final_score=score,
            confidence_level=0.7 if score > 60 else 0.5,  # Уверенность на этапе screening
            next_steps=next_steps
        )
        
        self.pump_stats['pump_candidates_found'] += 1
        
        logger.info(f"🎯 PUMP CANDIDATE: {pair_data['baseToken']['symbol']} "
                   f"(Score: {score}/100, Chain: {pair_data.get('chainId')})")
        
        return pump_report
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Расширенная статистика с pump-specific метриками"""
        base_stats = {
            'pairs_scanned': self.session_stats.get('pairs_scanned', 0),
            'reports_created': self.session_stats.get('reports_created', 0),
            'success_rate': (self.session_stats.get('reports_created', 0) / max(self.session_stats.get('pairs_scanned', 1), 1)) * 100,
            'api_calls_made': 4  # По количеству сетей
        }
        return {
            **base_stats,
            'pump_stats': self.pump_stats,
            'api_usage': self.api_tracker.model_dump()
        }

# === TESTING & STANDALONE USAGE ===
async def main():
    """Тестирование нового PumpDiscoveryAgent с наследованием"""
    print("🎯 Pump Discovery Agent - Inheritance Architecture Test")
    print("=" * 60)
    
    # Создаем экземпляр нового агента
    agent = PumpDiscoveryAgent()
    
    try:
        # Запускаем async discovery
        pump_candidates = await agent.discover_tokens_async()
        
        print(f"\n📊 Found {len(pump_candidates)} PUMP CANDIDATES")
        
        if not pump_candidates:
            print("\n😔 No pump candidates found in current scan.")
            return
        
        print("\n🚀 === TOP PUMP CANDIDATES ===")
        for i, candidate in enumerate(pump_candidates[:5]):
            print(f"\n#{i+1}: {candidate.token_name} ({candidate.token_symbol})")
            print("-" * 40)
            print(f"   🎯 Pump Score: {candidate.final_score}/100")
            print(f"   💰 Liquidity: ${candidate.indicators.liquidity_usd:,.0f}")
            print(f"   📊 Volume 24h: ${candidate.indicators.volume_24h:,.0f}")
            print(f"   🕒 Age: {candidate.indicators.age_hours:.1f} hours")
            print(f"   💡 Reasoning: {' | '.join(candidate.reasoning[:2])}")
            print(f"   📋 Next Steps: {', '.join(candidate.next_steps[:2])}")
        
        if len(pump_candidates) > 5:
            print(f"\n...and {len(pump_candidates) - 5} more candidates")
        
        # Показать расширенную статистику
        stats = agent.get_session_stats()
        print(f"\n📈 Session Stats:")
        print(f"   Pairs Scanned: {stats['pairs_scanned']}")
        print(f"   Pump Candidates: {stats['pump_stats']['pump_candidates_found']}")
        print(f"   High Potential: {stats['pump_stats']['high_potential_found']}")
        print(f"   Success Rate: {stats['success_rate']:.1f}%")
        print(f"   API Calls: {stats['api_calls_made']}")
        
    except Exception as e:
        logger.error(f"❌ Error in pump discovery: {e}", exc_info=True)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
