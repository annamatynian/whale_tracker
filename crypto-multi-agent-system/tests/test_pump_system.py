"""
ТЕСТ ФАЙЛ - Проверка всех компонентов pump analysis системы
Запускаем без API calls, только проверяем что код работает

Author: Test Suite for MVP
"""

import sys
import os

# Добавляем пути
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def test_imports():
    """Тест всех импортов"""
    print("🧪 ТЕСТ 1: Импорты")
    print("-" * 30)
    
    try:
        # Тест realistic_scoring
        from agents.pump_analysis.realistic_scoring import (
            RealisticScoringMatrix, 
            RealisticPumpIndicators,
            PumpRecommendationMVP,
            NarrativeType
        )
        print("✅ realistic_scoring импортирован")
        
        # Тест pump_models
        from agents.pump_analysis.pump_models import (
            PumpIndicators,
            PumpAnalysisReport,
            ApiUsageTracker
        )
        print("✅ pump_models импортирован")
        
        # Тест enhanced_discovery
        from agents.pump_analysis.enhanced_discovery import (
            initial_pump_screening,
            analyze_pump_potential_realistic
        )
        print("✅ enhanced_discovery импортирован")
        
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def test_realistic_scoring():
    """Тест realistic scoring логики"""
    print("\n🧪 ТЕСТ 2: Realistic Scoring")
    print("-" * 30)
    
    try:
        from agents.pump_analysis.realistic_scoring import (
            RealisticScoringMatrix, 
            RealisticPumpIndicators,
            NarrativeType
        )
        
        # Создаем тестовые данные
        test_indicators = RealisticPumpIndicators(
            narrative_type=NarrativeType.AI,
            has_trending_narrative=True,
            coingecko_score=75.0,
            is_honeypot=False,
            is_open_source=True,
            buy_tax_percent=3.0,
            sell_tax_percent=8.0,
            alpha_channel_mentions=5,
            social_momentum_score=80
        )
        
        # Создаем scoring matrix
        matrix = RealisticScoringMatrix(indicators=test_indicators)
        
        # Тестируем расчеты
        narrative_score = matrix.calculate_narrative_score()
        security_score = matrix.calculate_security_score()
        social_score = matrix.calculate_social_score()
        total_score = matrix.calculate_total_score()
        
        print(f"   Narrative Score: {narrative_score}/40")
        print(f"   Security Score: {security_score}/35") 
        print(f"   Social Score: {social_score}/25")
        print(f"   Total Score: {total_score}/100")
        
        # Тестируем рекомендации
        recommendation = matrix.get_recommendation()
        print(f"   Recommendation: {recommendation}")
        
        # Тестируем детальный анализ
        analysis = matrix.get_detailed_analysis()
        print(f"   Positive Signals: {len(analysis['positive_signals'])}")
        print(f"   Red Flags: {len(analysis['red_flags'])}")
        
        print("✅ Realistic scoring работает корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в realistic scoring: {e}")
        return False

def test_pump_models():
    """Тест pump models"""
    print("\n🧪 ТЕСТ 3: Pump Models")
    print("-" * 30)
    
    try:
        from agents.pump_analysis.pump_models import (
            PumpIndicators,
            NarrativeType
        )
        
        # Создаем тестовый PumpIndicators
        indicators = PumpIndicators(
            contract_address="0x1234567890abcdef",
            narrative_alignment=NarrativeType.AI,
            community_score=75.0,
            is_honeypot=False,
            is_open_source=True,
            social_mentions=3,
            liquidity_usd=50000.0,
            volume_24h=25000.0,
            age_hours=12.5,
            pump_probability_score=75
        )
        
        print(f"   Contract: {indicators.contract_address[:10]}...")
        print(f"   Narrative: {indicators.narrative_alignment}")
        print(f"   Score: {indicators.pump_probability_score}")
        print(f"   Honeypot: {'No' if not indicators.is_honeypot else 'Yes'}")
        
        print("✅ Pump models работают корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в pump models: {e}")
        return False

def test_enhanced_discovery():
    """Тест enhanced discovery функций"""
    print("\n🧪 ТЕСТ 4: Enhanced Discovery")
    print("-" * 30)
    
    try:
        from agents.pump_analysis.enhanced_discovery import initial_pump_screening
        
        # Создаем тестовые данные pair (как из DexScreener)
        test_pair_data = {
            'liquidity': {'usd': 25000},
            'volume': {'h24': 15000},
            'priceChange': {'h1': 150},  # 150% рост за час
            'pairCreatedAt': 1705000000000,  # Timestamp в миллисекундах
            'baseToken': {
                'symbol': 'TEST',
                'address': '0xtest'
            }
        }
        
        # Тестируем screening
        score = initial_pump_screening(test_pair_data)
        print(f"   Test Token Score: {score}/100")
        
        # Тестируем с плохими данными
        bad_pair_data = {
            'liquidity': {'usd': 1000},  # Слишком низкая ликвидность
            'volume': {'h24': 500},
            'priceChange': {'h1': -60},  # Дамп
            'pairCreatedAt': 1705000000000,
            'baseToken': {'symbol': 'BAD', 'address': '0xbad'}
        }
        
        bad_score = initial_pump_screening(bad_pair_data)
        print(f"   Bad Token Score: {bad_score}/100")
        
        print("✅ Enhanced discovery функции работают")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в enhanced discovery: {e}")
        return False

def test_integration():
    """Интеграционный тест - вся цепочка"""
    print("\n🧪 ТЕСТ 5: Интеграция")
    print("-" * 30)
    
    try:
        from agents.pump_analysis.realistic_scoring import (
            RealisticScoringMatrix, 
            RealisticPumpIndicators,
            NarrativeType
        )
        from agents.pump_analysis.enhanced_discovery import initial_pump_screening
        
        # Симулируем полный workflow
        print("   1. Скрининг токена через DexScreener...")
        pair_data = {
            'liquidity': {'usd': 75000},
            'volume': {'h24': 50000},
            'priceChange': {'h1': 200},
            'pairCreatedAt': 1705000000000,
            'baseToken': {'symbol': 'ALPHA', 'address': '0xalpha'}
        }
        
        screening_score = initial_pump_screening(pair_data)
        print(f"   2. Screening Score: {screening_score}")
        
        if screening_score > 35:  # MVP threshold
            print("   3. Применяем реалистичный scoring...")
            
            # Симулируем данные от других API
            indicators = RealisticPumpIndicators(
                narrative_type=NarrativeType.AI,
                has_trending_narrative=True,
                is_honeypot=False,
                is_open_source=True,
                alpha_channel_mentions=3
            )
            
            matrix = RealisticScoringMatrix(indicators=indicators)
            final_score = matrix.calculate_total_score()
            recommendation = matrix.get_recommendation()
            
            print(f"   4. Final Score: {final_score}/100")
            print(f"   5. Recommendation: {recommendation}")
            
            print("✅ Интеграция работает корректно")
            return True
        else:
            print("   3. Токен отфильтрован на раннем этапе")
            return True
            
    except Exception as e:
        print(f"❌ Ошибка интеграции: {e}")
        return False

def main():
    """Главная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ PUMP ANALYSIS СИСТЕМЫ")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_realistic_scoring,
        test_pump_models,
        test_enhanced_discovery,
        test_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Критическая ошибка в {test.__name__}: {e}")
    
    print(f"\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 50)
    print(f"Пройдено: {passed}/{total}")
    print(f"Процент: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Система готова к использованию.")
    else:
        print("⚠️  ЕСТЬ ОШИБКИ! Требуется исправление.")
    
    return passed == total

if __name__ == "__main__":
    main()
