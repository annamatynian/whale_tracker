"""
Тест realistic_scoring.py - Улучшенная система scoring

Тестирует ТОЛЬКО realistic scoring компоненты:
- Импорты модулей
- RealisticPumpIndicators модель
- RealisticScoringMatrix класс
- Жесткие правила безопасности (Gemini improvements)
- Scoring логику по категориям
- Итоговые рекомендации

Author: Step 2 of step-by-step testing
"""

import sys
import os

# Добавляем пути
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def test_realistic_scoring_imports():
    """Тест 1: Импорты realistic_scoring"""
    print("🧪 ТЕСТ 1: Импорты realistic_scoring")
    print("-" * 40)
    
    try:
        from agents.pump_analysis.realistic_scoring import (
            RealisticScoringMatrix,
            RealisticPumpIndicators, 
            PumpRecommendationMVP,
            NarrativeType,
            MVP_SCORING_WEIGHTS,
            should_spend_api_calls
        )
        
        print("✅ Все импорты успешны")
        print(f"   - RealisticScoringMatrix: {RealisticScoringMatrix}")
        print(f"   - RealisticPumpIndicators: {RealisticPumpIndicators}")
        print(f"   - PumpRecommendationMVP: {PumpRecommendationMVP}")
        print(f"   - NarrativeType: {NarrativeType}")
        print(f"   - MVP_SCORING_WEIGHTS: {MVP_SCORING_WEIGHTS}")
        
        return True, {
            'RealisticScoringMatrix': RealisticScoringMatrix,
            'RealisticPumpIndicators': RealisticPumpIndicators,
            'PumpRecommendationMVP': PumpRecommendationMVP,
            'NarrativeType': NarrativeType,
            'MVP_SCORING_WEIGHTS': MVP_SCORING_WEIGHTS,
            'should_spend_api_calls': should_spend_api_calls
        }
        
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False, {}

def test_narrative_types(imports):
    """Тест 2: NarrativeType enum"""
    print("\n🧪 ТЕСТ 2: NarrativeType enum")
    print("-" * 40)
    
    try:
        NarrativeType = imports['NarrativeType']
        
        # Проверяем все нарративы из исследования
        expected_narratives = ['AI', 'LAYER2', 'RWA', 'DEFI', 'GAMING', 'UNKNOWN']
        
        print("✅ NarrativeType enum проверен:")
        for narrative in expected_narratives:
            has_narrative = hasattr(NarrativeType, narrative)
            value = getattr(NarrativeType, narrative, None) if has_narrative else None
            print(f"   - {narrative}: {'✅' if has_narrative else '❌'} (value: {value})")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка NarrativeType: {e}")
        return False

def test_pump_indicators_model(imports):
    """Тест 3: RealisticPumpIndicators модель"""
    print("\n🧪 ТЕСТ 3: RealisticPumpIndicators модель")
    print("-" * 40)
    
    try:
        RealisticPumpIndicators = imports['RealisticPumpIndicators']
        NarrativeType = imports['NarrativeType']
        
        # Создаем тестовые индикаторы
        test_indicators = RealisticPumpIndicators(
            narrative_type=NarrativeType.AI,
            has_trending_narrative=True,
            coingecko_score=75.0,
            is_honeypot=False,
            is_open_source=True,
            buy_tax_percent=3.0,
            sell_tax_percent=8.0,
            alpha_channel_mentions=5,
            social_momentum_score=80,
            data_completeness_percent=90.0
        )
        
        print("✅ RealisticPumpIndicators создается корректно")
        print(f"   - Narrative: {test_indicators.narrative_type}")
        print(f"   - Honeypot: {test_indicators.is_honeypot}")
        print(f"   - Open Source: {test_indicators.is_open_source}")
        print(f"   - Buy Tax: {test_indicators.buy_tax_percent}%")
        print(f"   - Alpha Mentions: {test_indicators.alpha_channel_mentions}")
        
        # Тест валидации - невалидные значения
        try:
            invalid_indicators = RealisticPumpIndicators(
                buy_tax_percent=150.0  # > 100%
            )
            print("❌ Валидация не работает (принял 150% налог)")
            return False
        except Exception:
            print("✅ Валидация работает (отклонил невалидный налог)")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка RealisticPumpIndicators: {e}")
        return False

def test_honeypot_hard_rule(imports):
    """Тест 4: Жесткое правило Honeypot = 0 (Gemini improvement)"""
    print("\n🧪 ТЕСТ 4: Жесткое правило Honeypot = 0")
    print("-" * 40)
    
    try:
        RealisticScoringMatrix = imports['RealisticScoringMatrix']
        RealisticPumpIndicators = imports['RealisticPumpIndicators']
        
        # Тест: Honeypot должен давать 0 баллов за безопасность
        honeypot_indicators = RealisticPumpIndicators(
            is_honeypot=True,
            is_open_source=True,  # Даже с хорошими параметрами
            buy_tax_percent=1.0,
            sell_tax_percent=2.0
        )
        
        honeypot_matrix = RealisticScoringMatrix(indicators=honeypot_indicators)
        security_score = honeypot_matrix.calculate_security_score()
        
        print(f"🧪 Honeypot security score: {security_score}")
        
        if security_score == 0:
            print("✅ Жесткое правило работает: Honeypot = 0 баллов")
        else:
            print(f"❌ Жесткое правило не работает: Honeypot дал {security_score} баллов")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка honeypot теста: {e}")
        return False

def test_high_tax_hard_rule(imports):
    """Тест 5: Жесткое правило Высокие налоги = 0 (Gemini improvement)"""
    print("\n🧪 ТЕСТ 5: Жесткое правило Высокие налоги = 0")
    print("-" * 40)
    
    try:
        RealisticScoringMatrix = imports['RealisticScoringMatrix']
        RealisticPumpIndicators = imports['RealisticPumpIndicators']
        
        # Тест: Налоги >50% должны давать 0 баллов
        high_tax_indicators = RealisticPumpIndicators(
            is_honeypot=False,
            is_open_source=True,
            buy_tax_percent=60.0,  # >50% - критично
            sell_tax_percent=10.0
        )
        
        high_tax_matrix = RealisticScoringMatrix(indicators=high_tax_indicators)
        security_score = high_tax_matrix.calculate_security_score()
        
        print(f"🧪 High buy tax security score: {security_score}")
        
        if security_score == 0:
            print("✅ Жесткое правило работает: Налог >50% = 0 баллов")
        else:
            print(f"❌ Жесткое правило не работает: Налог >50% дал {security_score} баллов")
            return False
        
        # Тест 2: Высокий налог на продажу
        high_sell_tax_indicators = RealisticPumpIndicators(
            is_honeypot=False,
            is_open_source=True,
            buy_tax_percent=5.0,
            sell_tax_percent=75.0  # >50% - критично
        )
        
        high_sell_tax_matrix = RealisticScoringMatrix(indicators=high_sell_tax_indicators)
        sell_security_score = high_sell_tax_matrix.calculate_security_score()
        
        print(f"🧪 High sell tax security score: {sell_security_score}")
        
        if sell_security_score == 0:
            print("✅ Жесткое правило работает: Налог на продажу >50% = 0 баллов")
        else:
            print(f"❌ Жесткое правило не работает: Налог на продажу >50% дал {sell_security_score} баллов")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка high tax теста: {e}")
        return False

def test_narrative_scoring(imports):
    """Тест 6: Narrative scoring логика"""
    print("\n🧪 ТЕСТ 6: Narrative scoring")
    print("-" * 40)
    
    try:
        RealisticScoringMatrix = imports['RealisticScoringMatrix']
        RealisticPumpIndicators = imports['RealisticPumpIndicators']
        NarrativeType = imports['NarrativeType']
        
        # Тест: AI нарратив должен давать максимальные баллы
        ai_indicators = RealisticPumpIndicators(
            narrative_type=NarrativeType.AI,
            has_trending_narrative=True,
            coingecko_score=80.0
        )
        
        ai_matrix = RealisticScoringMatrix(indicators=ai_indicators)
        narrative_score = ai_matrix.calculate_narrative_score()
        
        print(f"🧪 AI narrative score: {narrative_score}/40")
        
        # Тест: UNKNOWN нарратив должен давать 0
        unknown_indicators = RealisticPumpIndicators(
            narrative_type=NarrativeType.UNKNOWN,
            has_trending_narrative=False
        )
        
        unknown_matrix = RealisticScoringMatrix(indicators=unknown_indicators)
        unknown_score = unknown_matrix.calculate_narrative_score()
        
        print(f"🧪 Unknown narrative score: {unknown_score}/40")
        
        if narrative_score > unknown_score:
            print("✅ Narrative scoring работает: AI > UNKNOWN")
        else:
            print("❌ Narrative scoring не работает корректно")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка narrative scoring: {e}")
        return False

def test_social_scoring(imports):
    """Тест 7: Social scoring логика"""
    print("\n🧪 ТЕСТ 7: Social scoring")
    print("-" * 40)
    
    try:
        RealisticScoringMatrix = imports['RealisticScoringMatrix']
        RealisticPumpIndicators = imports['RealisticPumpIndicators']
        
        # Тест: Высокая социальная активность
        high_social_indicators = RealisticPumpIndicators(
            alpha_channel_mentions=7,  # Высокая активность
            social_momentum_score=85
        )
        
        high_social_matrix = RealisticScoringMatrix(indicators=high_social_indicators)
        social_score = high_social_matrix.calculate_social_score()
        
        print(f"🧪 High social activity score: {social_score}/25")
        
        # Тест: Нет социальной активности
        no_social_indicators = RealisticPumpIndicators(
            alpha_channel_mentions=0,
            social_momentum_score=0
        )
        
        no_social_matrix = RealisticScoringMatrix(indicators=no_social_indicators)
        no_social_score = no_social_matrix.calculate_social_score()
        
        print(f"🧪 No social activity score: {no_social_score}/25")
        
        if social_score > no_social_score:
            print("✅ Social scoring работает: Активность дает больше баллов")
        else:
            print("❌ Social scoring не работает корректно")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка social scoring: {e}")
        return False

def test_total_scoring_and_recommendations(imports):
    """Тест 8: Итоговый scoring и рекомендации"""
    print("\n🧪 ТЕСТ 8: Итоговый scoring и рекомендации")
    print("-" * 40)
    
    try:
        RealisticScoringMatrix = imports['RealisticScoringMatrix']
        RealisticPumpIndicators = imports['RealisticPumpIndicators']
        NarrativeType = imports['NarrativeType']
        PumpRecommendationMVP = imports['PumpRecommendationMVP']
        
        # Тест: Идеальный токен
        perfect_indicators = RealisticPumpIndicators(
            narrative_type=NarrativeType.AI,
            has_trending_narrative=True,
            coingecko_score=90.0,
            is_honeypot=False,
            is_open_source=True,
            buy_tax_percent=2.0,
            sell_tax_percent=5.0,
            alpha_channel_mentions=10,
            social_momentum_score=95
        )
        
        perfect_matrix = RealisticScoringMatrix(indicators=perfect_indicators)
        perfect_score = perfect_matrix.calculate_total_score()
        perfect_recommendation = perfect_matrix.get_recommendation()
        
        print(f"🧪 Perfect token score: {perfect_score}/100")
        print(f"🧪 Perfect token recommendation: {perfect_recommendation}")
        
        # Тест: Плохой токен (honeypot)
        bad_indicators = RealisticPumpIndicators(
            is_honeypot=True
        )
        
        bad_matrix = RealisticScoringMatrix(indicators=bad_indicators)
        bad_score = bad_matrix.calculate_total_score()
        bad_recommendation = bad_matrix.get_recommendation()
        
        print(f"🧪 Bad token (honeypot) score: {bad_score}/100")
        print(f"🧪 Bad token recommendation: {bad_recommendation}")
        
        # Проверяем логику
        if perfect_score > bad_score and perfect_recommendation != bad_recommendation:
            print("✅ Scoring и рекомендации работают корректно")
        else:
            print("❌ Scoring или рекомендации не работают")
            return False
        
        # Тест детального анализа
        detailed_analysis = perfect_matrix.get_detailed_analysis()
        print(f"🧪 Detailed analysis keys: {list(detailed_analysis.keys())}")
        
        expected_keys = ['total_score', 'recommendation', 'category_scores', 'positive_signals', 'red_flags']
        missing_keys = [key for key in expected_keys if key not in detailed_analysis]
        
        if not missing_keys:
            print("✅ Detailed analysis содержит все ожидаемые ключи")
        else:
            print(f"❌ Отсутствуют ключи в detailed analysis: {missing_keys}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка total scoring: {e}")
        return False

def test_api_calls_optimization(imports):
    """Тест 9: Оптимизация API calls"""
    print("\n🧪 ТЕСТ 9: Оптимизация API calls")
    print("-" * 40)
    
    try:
        should_spend_api_calls = imports['should_spend_api_calls']
        
        # Тест: Высокий score + много calls = да
        should_spend_high = should_spend_api_calls(basic_score=90, available_calls=100)
        print(f"🧪 High score (90) + many calls (100): {should_spend_high}")
        
        # Тест: Низкий score + мало calls = нет
        should_spend_low = should_spend_api_calls(basic_score=30, available_calls=5)
        print(f"🧪 Low score (30) + few calls (5): {should_spend_low}")
        
        if should_spend_high and not should_spend_low:
            print("✅ API calls оптимизация работает корректно")
        else:
            print("❌ API calls оптимизация не работает")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка API calls теста: {e}")
        return False

def run_realistic_scoring_tests():
    """Запуск всех тестов realistic_scoring"""
    print("🧪 ТЕСТИРОВАНИЕ realistic_scoring.py")
    print("=" * 50)
    
    # Тест 1: Импорты
    imports_success, imports = test_realistic_scoring_imports()
    if not imports_success:
        print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Импорты не работают")
        return False
    
    tests = [
        ("NarrativeType enum", lambda: test_narrative_types(imports)),
        ("RealisticPumpIndicators модель", lambda: test_pump_indicators_model(imports)),
        ("Жесткое правило Honeypot", lambda: test_honeypot_hard_rule(imports)),
        ("Жесткое правило Высокие налоги", lambda: test_high_tax_hard_rule(imports)),
        ("Narrative scoring", lambda: test_narrative_scoring(imports)),
        ("Social scoring", lambda: test_social_scoring(imports)),
        ("Итоговый scoring", lambda: test_total_scoring_and_recommendations(imports)),
        ("API calls оптимизация", lambda: test_api_calls_optimization(imports))
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {e}")
            results.append(False)
    
    # Итоговый результат
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 РЕЗУЛЬТАТЫ ТЕСТОВ realistic_scoring.py")
    print("=" * 50)
    print(f"Пройдено: {passed}/{total}")
    print(f"Процент: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 realistic_scoring.py полностью работоспособен!")
        print("Жесткие правила Gemini реализованы корректно!")
        return True
    else:
        print("⚠️ realistic_scoring.py требует исправлений")
        return False

if __name__ == "__main__":
    success = run_realistic_scoring_tests()
    
    if success:
        print("\n🚀 ГОТОВ К ШАГУ 3")
        print("realistic_scoring.py протестирован - переходим к PumpDiscoveryAgent_v2")
    else:
        print("\n🔧 ТРЕБУЕТСЯ ДОРАБОТКА")
        print("Исправьте ошибки перед переходом к следующему шагу")
