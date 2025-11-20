#!/usr/bin/env python3
"""
Тест Volume Acceleration функциональности
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_volume_acceleration():
    """Тест новой Volume Acceleration функциональности"""
    print("🧪 ТЕСТ VOLUME ACCELERATION SCORING")
    print("=" * 60)
    
    try:
        from agents.pump_analysis.realistic_scoring import RealisticPumpIndicators, RealisticScoringMatrix
        from agents.pump_analysis.pump_models import NarrativeType
        
        print("✅ Импорты успешны")
        
        # Тест 1: Отличный токен с volume acceleration
        print("\n🔥 ТЕСТ 1: Токен с Volume Acceleration")
        indicators_with_volume = RealisticPumpIndicators(
            narrative_type=NarrativeType.AI,
            has_trending_narrative=True,
            coingecko_score=80.0,
            is_honeypot=False,
            is_open_source=True,
            buy_tax_percent=3.0,
            sell_tax_percent=6.0,
            # Volume acceleration данные
            volume_h1=30000,
            volume_h6=90000,
            is_volume_accelerating=True,  # ✅ Объем ускоряется
            volume_ratio_healthy=True,    # ✅ Здоровый ratio
            data_completeness_percent=95.0
        )
        
        matrix_with_volume = RealisticScoringMatrix(indicators=indicators_with_volume)
        analysis_with_volume = matrix_with_volume.get_detailed_analysis()
        
        print(f"   📈 Score: {analysis_with_volume['total_score']}/90")
        print(f"   📊 Breakdown:")
        print(f"      - Narrative: {analysis_with_volume['category_scores']['narrative']}/40")
        print(f"      - Security: {analysis_with_volume['category_scores']['security']}/35")  
        print(f"      - Volume: {analysis_with_volume['category_scores']['volume']}/15")
        print(f"   🎯 Recommendation: {analysis_with_volume['recommendation']}")
        
        # Тест 2: Тот же токен без volume acceleration
        print("\n📊 ТЕСТ 2: Тот же токен БЕЗ Volume Acceleration")
        indicators_no_volume = RealisticPumpIndicators(
            narrative_type=NarrativeType.AI,
            has_trending_narrative=True,
            coingecko_score=80.0,
            is_honeypot=False,
            is_open_source=True,
            buy_tax_percent=3.0,
            sell_tax_percent=6.0,
            # Нет volume acceleration
            volume_h1=5000,
            volume_h6=12000,
            is_volume_accelerating=False,  # ❌ Нет ускорения
            volume_ratio_healthy=False,    # ❌ Низкая активность
            data_completeness_percent=95.0
        )
        
        matrix_no_volume = RealisticScoringMatrix(indicators=indicators_no_volume)
        analysis_no_volume = matrix_no_volume.get_detailed_analysis()
        
        print(f"   📈 Score: {analysis_no_volume['total_score']}/90")
        print(f"   📊 Breakdown:")
        print(f"      - Narrative: {analysis_no_volume['category_scores']['narrative']}/40")
        print(f"      - Security: {analysis_no_volume['category_scores']['security']}/35")  
        print(f"      - Volume: {analysis_no_volume['category_scores']['volume']}/15")
        print(f"   🎯 Recommendation: {analysis_no_volume['recommendation']}")
        
        # Анализ разницы
        volume_boost = analysis_with_volume['total_score'] - analysis_no_volume['total_score']
        print(f"\n⚡ ВЛИЯНИЕ VOLUME ACCELERATION:")
        print(f"   🚀 Boost от volume acceleration: +{volume_boost} баллов")
        print(f"   📈 С volume: {analysis_with_volume['recommendation']}")
        print(f"   📊 Без volume: {analysis_no_volume['recommendation']}")
        
        # Проверяем что система работает как ожидается
        assert analysis_with_volume['total_score'] > analysis_no_volume['total_score'], "Volume acceleration должен повышать score!"
        assert analysis_with_volume['category_scores']['volume'] > 0, "Volume score должен быть > 0!"
        assert analysis_no_volume['category_scores']['volume'] == 0, "Volume score без acceleration должен быть 0!"
        
        print("\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Volume Acceleration работает корректно!")
        
        # Показываем positive signals
        if analysis_with_volume['positive_signals']:
            volume_signals = [s for s in analysis_with_volume['positive_signals'] if '🔥' in s or 'объем' in s.lower()]
            if volume_signals:
                print(f"\n🔥 Volume Acceleration Signals:")
                for signal in volume_signals:
                    print(f"   {signal}")
        
        return True
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_volume_acceleration()
    if success:
        print(f"\n🎉 VOLUME ACCELERATION ГОТОВ К ИСПОЛЬЗОВАНИЮ!")
        print(f"📝 Теперь система анализирует:")
        print(f"   - Ускорение объема (volume_h1 > volume_h6/6)")
        print(f"   - Здоровый volume ratio (0.5-3.0)")
        print(f"   - Подтверждение объемов БЕЗ перегрева")
    else:
        print(f"\n❌ ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ ОШИБОК!")
        sys.exit(1)
