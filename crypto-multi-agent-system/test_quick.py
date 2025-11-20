"""
Быстрая проверка системы - минимальный тест за 30 секунд
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def quick_test():
    """Быстрая проверка основных компонентов"""
    
    print("[QUICK] БЫСТРАЯ ПРОВЕРКА СИСТЕМЫ")
    print("=" * 50)
    
    results = {}
    
    # Test 1: Basic imports
    try:
        from agents.orchestrator.simple_orchestrator import SimpleOrchestrator
        from agents.pump_analysis.pump_discovery_agent import PumpDiscoveryAgent
        from agents.pump_analysis.realistic_scoring import RealisticScoringMatrix
        results['imports'] = True
        print("✅ Импорты: OK")
    except Exception as e:
        results['imports'] = False
        print(f"❌ Импорты: {e}")
    
    # Test 2: Orchestrator initialization
    try:
        orchestrator = SimpleOrchestrator()
        results['orchestrator'] = True
        print("✅ Оркестратор: OK")
    except Exception as e:
        results['orchestrator'] = False
        print(f"❌ Оркестратор: {e}")
    
    # Test 3: Discovery agent initialization
    try:
        discovery = PumpDiscoveryAgent()
        results['discovery'] = True
        print("✅ Discovery Agent: OK")
    except Exception as e:
        results['discovery'] = False
        print(f"❌ Discovery Agent: {e}")
    
    # Test 4: Scoring system
    try:
        from agents.pump_analysis.realistic_scoring import RealisticPumpIndicators
        from agents.pump_analysis.pump_models import NarrativeType
        
        indicators = RealisticPumpIndicators(
            narrative_type=NarrativeType.AI,
            has_trending_narrative=True,
            coingecko_score=8.0,
            is_honeypot=False,
            is_open_source=True,
            buy_tax_percent=1.0,
            sell_tax_percent=1.0
        )
        
        matrix = RealisticScoringMatrix(indicators=indicators)
        analysis = matrix.get_detailed_analysis()
        
        if analysis['total_score'] > 0:
            results['scoring'] = True
            print(f"✅ Scoring System: OK ({analysis['total_score']}/105 баллов)")
        else:
            results['scoring'] = False
            print("❌ Scoring System: Нулевой балл")
            
    except Exception as e:
        results['scoring'] = False
        print(f"❌ Scoring System: {e}")
    
    # Test 5: Configuration
    try:
        from agents.orchestrator.simple_orchestrator import FUNNEL_CONFIG
        if all(key in FUNNEL_CONFIG for key in ['top_n_for_onchain', 'min_score_for_alert', 'api_calls_threshold']):
            results['config'] = True
            print("✅ Конфигурация: OK")
        else:
            results['config'] = False
            print("❌ Конфигурация: Отсутствуют ключи")
    except Exception as e:
        results['config'] = False
        print(f"❌ Конфигурация: {e}")
    
    # Summary
    passed = sum(results.values())
    total = len(results)
    success_rate = (passed / total) * 100
    
    print(f"\n📊 РЕЗУЛЬТАТ БЫСТРОЙ ПРОВЕРКИ:")
    print(f"   ✅ Пройдено: {passed}/{total}")
    print(f"   📈 Успешность: {success_rate:.1f}%")
    
    if passed == total:
        print(f"\n🚀 ВСЕ БАЗОВЫЕ КОМПОНЕНТЫ РАБОТАЮТ!")
        print("   Система готова к детальному тестированию")
        print("   Запустите: python test_master_suite.py")
        
    elif passed >= total * 0.8:
        print(f"\n⚡ СИСТЕМА В ОСНОВНОМ РАБОТАЕТ!")
        print("   Есть минорные проблемы, но критические компоненты OK")
        print("   Можно продолжать тестирование")
        
    else:
        print(f"\n🔧 ЕСТЬ СЕРЬЕЗНЫЕ ПРОБЛЕМЫ!")
        print("   Критические компоненты не работают")
        print("   Исправьте ошибки перед продолжением")
    
    return passed == total

if __name__ == "__main__":
    success = quick_test()
    exit(0 if success else 1)
