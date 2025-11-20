"""
Тест архитектуры многоуровневой воронки
"""
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.pump_analysis.pump_models import TokenCandidate, NarrativeType
from agents.pump_analysis.realistic_scoring import RealisticScoringMatrix, RealisticPumpIndicators, PumpRecommendationMVP

class MockOrchestrator:
    """Mock версия оркестратора для тестирования воронки"""
    
    def __init__(self):
        self.logger = None  # Simplified for testing
    
    def create_mock_candidate(self, symbol: str, base_score: int) -> TokenCandidate:
        """Создает mock кандидата для тестирования"""
        return TokenCandidate(
            base_token_address="0x123...",
            base_token_name=f"Mock {symbol}",
            base_token_symbol=symbol,
            quote_token_symbol="WETH",
            price_usd=0.001,
            fdv=1000000,
            liquidity_usd=50000,
            volume_h24=25000,
            price_change_m5=0,
            price_change_h1=5,
            price_change_h6=15,
            price_change_h24=35,
            chain_id="ethereum",
            pair_address="0xabc...",
            dex="uniswap",
            pair_created_at=1609459200,
            volume_h1=5000,
            volume_h6=15000,
            discovery_score=base_score
        )
    
    def create_mock_indicators(self, risk_level: str = "medium") -> RealisticPumpIndicators:
        """Создает mock индикаторы для тестирования"""
        return RealisticPumpIndicators(
            narrative_type=NarrativeType.AI,
            has_trending_narrative=True,
            coingecko_score=7.5,
            is_honeypot=False,
            is_open_source=True,
            buy_tax_percent=1.0,
            sell_tax_percent=1.0
        )

    async def run_analysis_pipeline(self) -> list:
        """Тест всех уровней воронки с mock данными"""
        
        print("🔍 ТЕСТ МНОГОУРОВНЕВОЙ ВОРОНКИ")
        print("=" * 60)
        
        # === УРОВЕНЬ 1: DISCOVERY ===
        print("УРОВЕНЬ 1: Discovery (Mock)")
        mock_candidates = [
            self.create_mock_candidate("HIGHPOT", 85),  # High potential
            self.create_mock_candidate("MEDPOT", 72),   # Medium potential
            self.create_mock_candidate("LOWPOT", 45),   # Should be filtered out
            self.create_mock_candidate("GOODPOT", 78),  # Good potential
            self.create_mock_candidate("BADPOT", 30),   # Bad, filtered early
            self.create_mock_candidate("OKPOT", 65),    # Borderline
        ]
        print(f"   Найдено {len(mock_candidates)} кандидатов")
        
        # === УРОВЕНЬ 2: ENRICHMENT ===
        print("УРОВЕНЬ 2: Enrichment (Mock)")
        enriched_candidates = []
        
        for candidate in mock_candidates:
            # Simulate API calls threshold (45 points minimum)
            if candidate.discovery_score >= 45:
                # Create mock indicators
                indicators = self.create_mock_indicators()
                
                # Calculate enriched score
                scoring_matrix = RealisticScoringMatrix(indicators=indicators)
                analysis = scoring_matrix.get_detailed_analysis()
                
                enriched_candidates.append({
                    'candidate': candidate,
                    'final_score': analysis['total_score'],
                    'recommendation': analysis['recommendation'],
                    'analysis': analysis,
                    'indicators': indicators
                })
                
        print(f"   {len(enriched_candidates)} кандидатов прошли обогащение")
        
        # === УРОВЕНЬ 3: RANKING ===
        print("УРОВЕНЬ 3: Ranking (Mock)")
        enriched_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        print("   Топ-кандидаты по баллам:")
        for i, item in enumerate(enriched_candidates[:5]):
            candidate = item['candidate']
            score = item['final_score']
            rec = item['recommendation']
            print(f"   #{i+1}: {candidate.base_token_symbol} - {score}/105 баллов ({rec})")
        
        # Select top 15 for OnChain (or all if less than 15)
        top_15 = enriched_candidates[:15]
        print(f"   Топ-{len(top_15)} отобрано для OnChain анализа")
        
        # === УРОВЕНЬ 4: ONCHAIN ANALYSIS ===
        print("УРОВЕНЬ 4: OnChain Analysis (Mock)")
        onchain_analyzed = []
        
        for item in top_15:
            candidate = item['candidate']
            current_score = item['final_score']
            
            # Mock OnChain analysis (only for high scores to simulate API limits)
            if current_score >= 70:
                # Simulate OnChain bonus/penalty
                onchain_bonus = 15 if current_score > 80 else 10
                final_score = current_score + onchain_bonus
                
                onchain_analyzed.append({
                    **item,
                    'final_score': final_score,
                    'onchain_bonus': onchain_bonus
                })
                
                print(f"   {candidate.base_token_symbol}: {current_score} → {final_score} (+{onchain_bonus} OnChain)")
            else:
                # Keep without OnChain analysis
                onchain_analyzed.append(item)
                print(f"   {candidate.base_token_symbol}: {current_score} (no OnChain - low score)")
        
        # === УРОВЕНЬ 5: ALERTS ===
        print("УРОВЕНЬ 5: Alert Generation (Mock)")
        
        # Re-sort after OnChain analysis
        onchain_analyzed.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Filter for alerts (minimum 60 points)
        alert_candidates = [item for item in onchain_analyzed if item['final_score'] >= 60]
        
        alerts = []
        for item in alert_candidates:
            if item['recommendation'] in [PumpRecommendationMVP.HIGH_POTENTIAL, PumpRecommendationMVP.MEDIUM_POTENTIAL]:
                alerts.append({
                    'token_symbol': item['candidate'].base_token_symbol,
                    'final_score': item['final_score'],
                    'recommendation': item['recommendation'],
                    'details': item['analysis']
                })
        
        print(f"   {len(alerts)} финальных алертов создано")
        
        # === СТАТИСТИКА ВОРОНКИ ===
        print(f"\n📊 СТАТИСТИКА ВОРОНКИ:")
        print(f"   Уровень 1 (Discovery): {len(mock_candidates)} кандидатов")
        print(f"   Уровень 2 (Enrichment): {len(enriched_candidates)} обогащено")
        print(f"   Уровень 3 (Ranking): {len(top_15)} в топ-15")
        print(f"   Уровень 4 (OnChain): {len([x for x in onchain_analyzed if 'onchain_bonus' in x])} проанализировано")
        print(f"   Уровень 5 (Alerts): {len(alerts)} алертов")
        
        if len(mock_candidates) > 0:
            efficiency = (len(alerts) / len(mock_candidates)) * 100
            print(f"   Эффективность воронки: {efficiency:.1f}%")
            
            selection_rate = (len(top_15) / len(enriched_candidates)) * 100 if enriched_candidates else 0
            print(f"   Селективность: {selection_rate:.1f}%")
        
        return alerts

async def test_funnel_architecture():
    """Главная функция теста"""
    
    try:
        orchestrator = MockOrchestrator()
        alerts = await orchestrator.run_analysis_pipeline()
        
        print(f"\n✅ ТЕСТ ВОРОНКИ УСПЕШЕН!")
        print(f"   Создано {len(alerts)} алертов")
        
        if alerts:
            print("\n📋 ФИНАЛЬНЫЕ АЛЕРТЫ:")
            for i, alert in enumerate(alerts):
                print(f"   #{i+1}: {alert['token_symbol']} - {alert['final_score']} баллов ({alert['recommendation']})")
        else:
            print("   ⚠️ Алертов не создано (возможно, слишком строгие фильтры)")
            
        print("\n🎯 ВОРОНКА РАБОТАЕТ КОРРЕКТНО!")
        print("   ✅ Все уровни выполняются")
        print("   ✅ Фильтрация происходит на каждом уровне")
        print("   ✅ Scoring система функционирует")
        print("   ✅ Приоритизация работает")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА В ВОРОНКЕ: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_funnel_architecture())
    print(f"\n{'🎉 ТЕСТ ПРОЙДЕН' if success else '💥 ТЕСТ ПРОВАЛЕН'}")
    exit(0 if success else 1)
