"""
Pump Discovery Agent - Specialized for Pump Detection

Наследует всю ценную архитектуру из базового Discovery Agent
и добавляет pump-specific логику на основе исследования.

Переиспользует:
- Multi-chain scanning
- Rate limiting & cost tracking decorators  
- Async/sync hybrid pattern
- Performance metrics & MLOps tracking
- Robust error handling

Author: Based on existing discovery_agent.py + Gemini corrected approach
"""

import asyncio
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Импортируем всю ценную инфраструктуру из базового Discovery Agent
from ..discovery.discovery_agent import (
    fetch_pairs_for_chain,
    get_current_git_hash, 
    rate_limit,
    track_api_cost,
    CHAINS_TO_SCAN,
    logger
)

# Импортируем наши pump-specific модели
from .pump_models import (
    PumpIndicators, 
    PumpAnalysisReport,
    ApiUsageTracker,
    NarrativeType
)
from .realistic_scoring import RealisticScoringMatrix, RealisticPumpIndicators

# === PUMP-SPECIFIC CONFIGURATION ===
# Основано на исследовании и реалистичных возможностях бесплатных API

PUMP_FILTERS = {
    'min_liquidity_usd': 5000,      # Снижен для раннего обнаружения
    'min_volume_24h': 1000,         # Минимальная активность
    'max_age_hours': 48,            # Окно для pump detection
    'max_dump_percent': -50,        # Избегаем уже упавшие токены
    'min_positive_momentum': 10     # Минимальный рост для интереса
}

PUMP_SCORING_WEIGHTS_MVP = {
    'basic_screening': 40,          # Проходит базовые фильтры
    'early_detection_bonus': 20,    # Очень свежий токен
    'liquidity_bonus': 15,          # Хорошая ликвидность
    'momentum_bonus': 15,           # Положительная динамика
    'multi_chain_bonus': 10         # Присутствие на нескольких сетях
}

class PumpDiscoveryAgent:
    """
    Специализированный агент для поиска pump-потенциальных токенов.
    Наследует архитектуру базового Discovery Agent.
    """
    
    def __init__(self):
        self.api_tracker = ApiUsageTracker()
        self.processed_addresses = set()
        self.session_stats = {
            'tokens_scanned': 0,
            'pump_candidates_found': 0,
            'api_calls_made': 0,
            'processing_start_time': None
        }
    
    def pump_initial_screening(self, pair_data: Dict[str, Any]) -> tuple[int, List[str]]:
        """
        Pump-specific screening с детальными причинами.
        Основан на реалистичных данных из DexScreener API.
        """
        reasons = []
        
        # Базовая валидация данных
        if not pair_data or not pair_data.get('liquidity'):
            return 0, ["Missing basic data"]
        
        liquidity_usd = pair_data.get('liquidity', {}).get('usd', 0)
        volume_24h = pair_data.get('volume', {}).get('h24', 0)
        price_change_24h = pair_data.get('priceChange', {}).get('h24', 0)
        price_change_1h = pair_data.get('priceChange', {}).get('h1', 0)
        
        # === ФИЛЬТРЫ ИСКЛЮЧЕНИЯ (из исследования) ===
        
        if liquidity_usd < PUMP_FILTERS['min_liquidity_usd']:
            return 0, [f"Low liquidity: ${liquidity_usd:,.0f} < ${PUMP_FILTERS['min_liquidity_usd']:,}"]
        
        if price_change_24h < PUMP_FILTERS['max_dump_percent']:
            return 0, [f"Already dumped: {price_change_24h:.1f}% < {PUMP_FILTERS['max_dump_percent']}%"]
        
        if volume_24h < PUMP_FILTERS['min_volume_24h']:
            return 0, [f"No trading activity: ${volume_24h:,.0f} < ${PUMP_FILTERS['min_volume_24h']:,}"]
        
        # Проверка возраста
        created_at = pair_data.get('pairCreatedAt', 0)
        if created_at == 0:
            return 20, ["Unknown age - low priority"]
        
        age_hours = (time.time() - created_at/1000) / 3600
        if age_hours > PUMP_FILTERS['max_age_hours']:
            return 0, [f"Too old: {age_hours:.1f}h > {PUMP_FILTERS['max_age_hours']}h"]
        
        # === PUMP POTENTIAL SCORING ===
        
        score = PUMP_SCORING_WEIGHTS_MVP['basic_screening']  # Базовые 40 очков
        reasons.append(f"Passed screening ({score}pts)")
        
        # Бонус за раннее обнаружение
        if age_hours < 24:
            score += PUMP_SCORING_WEIGHTS_MVP['early_detection_bonus']
            reasons.append(f"Very fresh: {age_hours:.1f}h (+{PUMP_SCORING_WEIGHTS_MVP['early_detection_bonus']}pts)")
        
        # Бонус за ликвидность
        if liquidity_usd > 20000:
            score += PUMP_SCORING_WEIGHTS_MVP['liquidity_bonus']
            reasons.append(f"Good liquidity: ${liquidity_usd:,.0f} (+{PUMP_SCORING_WEIGHTS_MVP['liquidity_bonus']}pts)")
        
        # Бонус за позитивную динамику
        if price_change_24h > PUMP_FILTERS['min_positive_momentum']:
            score += PUMP_SCORING_WEIGHTS_MVP['momentum_bonus']
            reasons.append(f"Positive momentum: +{price_change_24h:.1f}% (+{PUMP_SCORING_WEIGHTS_MVP['momentum_bonus']}pts)")
        
        return min(score, 90), reasons  # Резерв 10 очков для premium данных
    
    def create_pump_analysis_report(self, pair_data: Dict[str, Any], screening_score: int, 
                                  screening_reasons: List[str], git_hash: str) -> PumpAnalysisReport:
        """
        Создает детальный отчет анализа pump потенциала.
        """
        created_at = datetime.fromtimestamp(pair_data.get('pairCreatedAt', 0) / 1000)
        age_hours = (time.time() - pair_data.get('pairCreatedAt', 0)/1000) / 3600
        
        # Базовые индикаторы из доступных данных
        indicators = PumpIndicators(
            contract_address=pair_data['baseToken']['address'],
            
            # DexScreener данные
            liquidity_usd=pair_data['liquidity']['usd'],
            volume_24h=pair_data['volume']['h24'],
            age_hours=age_hours,
            
            # Предварительная оценка (будет обновлена другими агентами)
            pump_probability_score=screening_score,
            recommendation="NEEDS_FURTHER_ANALYSIS" if screening_score > 60 else "LOW_PRIORITY"
        )
        
        # Определяем следующие шаги
        next_steps = []
        if screening_score > 70:
            next_steps.extend([
                "🔍 CoinGecko narrative analysis",
                "🛡️ GoPlus security check", 
                "📱 Telegram social monitoring"
            ])
        elif screening_score > 50:
            next_steps.extend([
                "🔍 CoinGecko narrative analysis",
                "🛡️ GoPlus security check"
            ])
        else:
            next_steps.append("📊 Monitor for changes")
        
        return PumpAnalysisReport(
            contract_address=pair_data['baseToken']['address'],
            token_symbol=pair_data['baseToken']['symbol'],
            token_name=pair_data['baseToken']['name'],
            
            indicators=indicators,
            
            # Scoring breakdown
            narrative_score=0,  # Будет заполнено CoinGecko Agent
            security_score=0,   # Будет заполнено Security Agent
            social_score=0,     # Будет заполнено Social Agent
            
            reasoning=screening_reasons,
            red_flags=[],  # Пока пусто, заполнят другие агенты
            
            data_sources_used=["DexScreener"],
            api_calls_made=1,
            
            final_score=screening_score,
            confidence_level=0.6,  # Средняя уверенность на этапе screening
            next_steps=next_steps
        )
    
    @rate_limit('dexscreener')
    @track_api_cost('dexscreener', cost_units=1)
    def discover_pump_candidates(self) -> List[PumpAnalysisReport]:
        """
        Основная функция поиска pump кандидатов.
        Переиспользует архитектуру базового Discovery Agent.
        """
        self.session_stats['processing_start_time'] = time.time()
        logger.info("🎯 Starting PUMP-specific token discovery...")
        
        git_hash = get_current_git_hash()
        pump_candidates = []
        total_api_time = 0
        
        for chain in CHAINS_TO_SCAN:
            try:
                logger.debug(f"🔍 Scanning {chain} for pump candidates...")
                
                api_data, api_time = fetch_pairs_for_chain(chain)
                if not api_data:
                    logger.warning(f"❌ No data from {chain}")
                    continue
                
                total_api_time += api_time or 0
                self.session_stats['api_calls_made'] += 1
                
                for pair in api_data:
                    if not pair or pair.get('pairAddress') in self.processed_addresses:
                        continue
                    
                    self.processed_addresses.add(pair.get('pairAddress'))
                    self.session_stats['tokens_scanned'] += 1
                    
                    # Pump-specific screening
                    screening_score, screening_reasons = self.pump_initial_screening(pair)
                    
                    if screening_score >= 50:  # Порог для pump кандидатов
                        pump_report = self.create_pump_analysis_report(
                            pair, screening_score, screening_reasons, git_hash
                        )
                        pump_candidates.append(pump_report)
                        self.session_stats['pump_candidates_found'] += 1
                        
                        logger.info(f"🎯 PUMP CANDIDATE: {pair['baseToken']['symbol']} "
                                  f"(Score: {screening_score}/100, Chain: {chain})")
                
            except Exception as e:
                logger.error(f"❌ Error scanning {chain}: {e}")
                continue
        
        # Финальная статистика
        processing_time = time.time() - self.session_stats['processing_start_time']
        
        logger.info(
            f"✅ Pump discovery complete: "
            f"{self.session_stats['pump_candidates_found']} candidates from "
            f"{self.session_stats['tokens_scanned']} scanned "
            f"({processing_time:.1f}s total, {total_api_time:.1f}ms API)"
        )
        
        # Сортируем по pump potential score
        return sorted(pump_candidates, key=lambda x: x.final_score, reverse=True)
    
    async def discover_pump_candidates_async(self) -> List[PumpAnalysisReport]:
        """
        Async wrapper для pump discovery.
        Переиспользует паттерн из базового Discovery Agent.
        """
        logger.info("🔄 Running pump discovery in async executor...")
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.discover_pump_candidates)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Статистика текущей сессии"""
        return {
            **self.session_stats,
            'api_usage': self.api_tracker.model_dump(),
            'success_rate': (
                self.session_stats['pump_candidates_found'] / 
                max(self.session_stats['tokens_scanned'], 1) * 100
            )
        }

# === TESTING & STANDALONE USAGE ===

async def main():
    """Тестирование Pump Discovery Agent"""
    print("🎯 Pump Discovery Agent - Testing Mode")
    print("=" * 50)
    
    agent = PumpDiscoveryAgent()
    
    try:
        pump_candidates = await agent.discover_pump_candidates_async()
        
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
        
        # Показать статистику
        stats = agent.get_session_stats()
        print(f"\n📈 Session Stats:")
        print(f"   Tokens Scanned: {stats['tokens_scanned']}")
        print(f"   Pump Candidates: {stats['pump_candidates_found']}")
        print(f"   Success Rate: {stats['success_rate']:.1f}%")
        print(f"   API Calls: {stats['api_calls_made']}")
        
    except Exception as e:
        logger.error(f"❌ Error in pump discovery: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
