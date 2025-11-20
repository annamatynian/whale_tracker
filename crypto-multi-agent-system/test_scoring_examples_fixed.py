"""
Исправленный Scoring Test - без Unicode символов
Тестирование на реальных примерах из PDF исследования

Анализирует токены $AVNT, $SAPIEN, $OPENX, $BTR из исследования
"Анатомия спекулятивного пампа" с использованием RealisticScoringMatrix
"""

from agents.pump_analysis.realistic_scoring import (
    RealisticScoringMatrix, 
    RealisticPumpIndicators, 
    PumpRecommendationMVP
)
from agents.pump_analysis.pump_models import NarrativeType

def test_avnt_case():
    """
    Тест $AVNT (Avantis)
    
    Из PDF: Base ecosystem, RWA Perps DEX, Coinbase/Bybit листинги
    Pump: $0.30 → $1.50+ (+400%)
    """
    print("=== КЕЙС 1: $AVNT (Avantis) ===")
    print("-" * 40)
    
    # Данные из исследования
    avnt_indicators = RealisticPumpIndicators(
        # Нарратив (сильный)
        narrative_type=NarrativeType.RWA,  # RWA Perps - актуальный нарратив
        has_trending_narrative=True,
        coingecko_score=72.0,  # Имитируем хороший community score
        
        # Безопасность (отличная)
        is_honeypot=False,      # Залистился на Tier-1 CEX = не скам
        is_open_source=True,    # Серьезный проект
        buy_tax_percent=0.0,    # Нет налогов
        sell_tax_percent=0.0,
    )
    
    scoring_matrix = RealisticScoringMatrix(indicators=avnt_indicators)
    analysis = scoring_matrix.get_detailed_analysis()
    
    print(f"=== РЕЗУЛЬТАТ ===")
    print(f"   Total Score: {analysis['total_score']}/105")
    print(f"   Recommendation: {analysis['recommendation']}")
    print(f"   Breakdown:")
    print(f"     Narrative: {analysis['scores']['narrative']}/35")
    print(f"     Security: {analysis['scores']['security']}/45") 
    print(f"     Social: {analysis['scores']['social']}/25")
    
    return analysis

def test_sapien_case():
    """
    Тест $SAPIEN 
    
    Из PDF: AI нарратив, $15.5M VC funding, TGE + airdrop
    """
    print("\n=== КЕЙС 2: $SAPIEN ===")
    print("-" * 40)
    
    sapien_indicators = RealisticPumpIndicators(
        # Нарратив (очень сильный)
        narrative_type=NarrativeType.AI,
        has_trending_narrative=True,
        coingecko_score=78.0,
        
        # Безопасность (хорошая)
        is_honeypot=False,
        is_open_source=True,
        buy_tax_percent=1.0,
        sell_tax_percent=1.0,
    )
    
    scoring_matrix = RealisticScoringMatrix(indicators=sapien_indicators)
    analysis = scoring_matrix.get_detailed_analysis()
    
    print(f"=== РЕЗУЛЬТАТ ===")
    print(f"   Total Score: {analysis['total_score']}/105")
    print(f"   Recommendation: {analysis['recommendation']}")
    print(f"   Breakdown:")
    print(f"     Narrative: {analysis['scores']['narrative']}/35")
    print(f"     Security: {analysis['scores']['security']}/45")
    print(f"     Social: {analysis['scores']['social']}/25")
    
    return analysis

def test_openx_case():
    """
    Тест $OPENX (OpenxAI)
    
    Из PDF: AI нарратив, поддержка CEO Coinbase, +224% рост
    """
    print("\n=== КЕЙС 3: $OPENX (OpenxAI) ===")
    print("-" * 40)
    
    openx_indicators = RealisticPumpIndicators(
        # Нарратив (очень сильный)
        narrative_type=NarrativeType.AI,
        has_trending_narrative=True,
        coingecko_score=85.0,  # CEO support = высокий score
        
        # Безопасность (отличная)
        is_honeypot=False,
        is_open_source=True,
        buy_tax_percent=0.5,
        sell_tax_percent=0.5,
    )
    
    scoring_matrix = RealisticScoringMatrix(indicators=openx_indicators)
    analysis = scoring_matrix.get_detailed_analysis()
    
    print(f"=== РЕЗУЛЬТАТ ===")
    print(f"   Total Score: {analysis['total_score']}/105")
    print(f"   Recommendation: {analysis['recommendation']}")
    print(f"   Breakdown:")
    print(f"     Narrative: {analysis['scores']['narrative']}/35")
    print(f"     Security: {analysis['scores']['security']}/45")
    print(f"     Social: {analysis['scores']['social']}/25")
    
    return analysis

def test_bad_token_case():
    """
    Тест плохого токена (для проверки защиты от скама)
    """
    print("\n=== КЕЙС 4: BAD TOKEN (Honeypot Protection Test) ===")
    print("-" * 40)
    
    bad_indicators = RealisticPumpIndicators(
        # Нарратив (отсутствует)
        narrative_type=NarrativeType.UNKNOWN,
        has_trending_narrative=False,
        coingecko_score=None,  # Нет данных
        
        # Безопасность (критические проблемы)
        is_honeypot=True,       # HONEYPOT!
        is_open_source=False,   # Не верифицирован
        buy_tax_percent=15.0,   # Высокие налоги
        sell_tax_percent=25.0,  # Очень высокие налоги продажи
    )
    
    scoring_matrix = RealisticScoringMatrix(indicators=bad_indicators)
    analysis = scoring_matrix.get_detailed_analysis()
    
    print(f"=== РЕЗУЛЬТАТ ===")
    print(f"   Total Score: {analysis['total_score']}/105")
    print(f"   Recommendation: {analysis['recommendation']}")
    print(f"   Breakdown:")
    print(f"     Narrative: {analysis['scores']['narrative']}/35")
    print(f"     Security: {analysis['scores']['security']}/45")
    print(f"     Social: {analysis['scores']['social']}/25")
    
    if analysis['total_score'] == 0:
        print("   [OK] Honeypot protection working!")
    else:
        print("   [ERROR] Honeypot should get 0 score!")
    
    return analysis

def main():
    """Главная функция тестирования"""
    
    print("=== SCORING TEST - РЕАЛЬНЫЕ ПРИМЕРЫ ИЗ PDF ИССЛЕДОВАНИЯ ===")
    print("=" * 80)
    print("Тестирование RealisticScoringMatrix на известных кейсах")
    print("=" * 80)
    
    # Запуск тестов
    results = []
    
    try:
        # Тест успешных токенов
        avnt_result = test_avnt_case()
        results.append(("$AVNT", avnt_result))
        
        sapien_result = test_sapien_case()
        results.append(("$SAPIEN", sapien_result))
        
        openx_result = test_openx_case()  
        results.append(("$OPENX", openx_result))
        
        # Тест защиты от скама
        bad_result = test_bad_token_case()
        results.append(("BAD TOKEN", bad_result))
        
        # Итоговый анализ
        print("\n" + "="*80)
        print("=== ИТОГОВЫЕ РЕЗУЛЬТАТЫ ===")
        print("="*80)
        
        for token_name, result in results:
            score = result['total_score']
            rec = result['recommendation']
            print(f"   {token_name}: {score}/105 - {rec}")
        
        # Проверка логики
        print("\n=== ПРОВЕРКА ЛОГИКИ СИСТЕМЫ ===")
        
        # Хорошие токены должны иметь высокие баллы
        good_tokens = [r for name, r in results if name in ["$AVNT", "$SAPIEN", "$OPENX"]]
        avg_good_score = sum(r['total_score'] for r in good_tokens) / len(good_tokens)
        
        # Плохой токен должен иметь 0 баллов
        bad_score = next(r['total_score'] for name, r in results if name == "BAD TOKEN")
        
        print(f"   Средний балл хороших токенов: {avg_good_score:.1f}/105")
        print(f"   Балл плохого токена: {bad_score}/105")
        
        # Валидация
        validation_passed = True
        
        if avg_good_score < 60:
            print("   [ERROR] Хорошие токены получили слишком низкие баллы!")
            validation_passed = False
        else:
            print("   [OK] Хорошие токены правильно оценены")
        
        if bad_score > 0:
            print("   [ERROR] Плохой токен должен получить 0 баллов!")
            validation_passed = False
        else:
            print("   [OK] Honeypot защита работает корректно")
        
        # Проверка различий в оценках
        scores = [r['total_score'] for _, r in results if r['total_score'] > 0]
        if len(set(scores)) > 1:
            print("   [OK] Система различает качество токенов")
        else:
            print("   [WARNING] Все токены получили одинаковые оценки")
            validation_passed = False
        
        # Финальное заключение
        print("\n" + "="*80)
        if validation_passed:
            print("[SUCCESS] ВСЕ SCORING ТЕСТЫ ПРОЙДЕНЫ!")
            print("   [OK] Система корректно оценивает качественные токены")
            print("   [OK] Honeypot защита функционирует")
            print("   [OK] Различные токены получают разные оценки")
            print("   [INFO] RealisticScoringMatrix готова к продакшену")
        else:
            print("[ERROR] ЕСТЬ ПРОБЛЕМЫ В SCORING СИСТЕМЕ!")
            print("   [ACTION] Проверьте логику RealisticScoringMatrix")
            print("   [ACTION] Исправьте найденные проблемы")
        
        return validation_passed
        
    except Exception as e:
        print(f"[CRITICAL] Критическая ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
