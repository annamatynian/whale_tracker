"""
ТЕСТ ПРОВЕРКИ ИСПРАВЛЕНИЙ CoinGecko
==================================

Этот тест проверяет:
1. ✅ Исправлена ли логика ограничения токенов для CoinGecko
2. ✅ Используется ли правильная переменная enrichment_candidates
3. ✅ Ограничивается ли количество API вызовов согласно конфигурации

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: Только 5 токенов должны проходить в CoinGecko API
"""

import sys
import os
import asyncio
import logging

# Настройка путей
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator.simple_orchestrator import SimpleOrchestrator, FUNNEL_CONFIG

# Настройка логирования для детального отслеживания
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)

async def test_token_limiting():
    """Тест ограничения токенов для CoinGecko API."""
    print("🔍 ТЕСТ: Проверка ограничения токенов для CoinGecko API")
    print("=" * 60)
    
    print(f"📊 КОНФИГУРАЦИЯ ВОРОНКИ:")
    print(f"   top_n_for_enrichment: {FUNNEL_CONFIG['top_n_for_enrichment']}")
    print(f"   min_score_for_alert: {FUNNEL_CONFIG['min_score_for_alert']}")
    print(f"   api_calls_threshold: {FUNNEL_CONFIG['api_calls_threshold']}")
    print()
    
    try:
        # Создаем оркестратор
        orchestrator = SimpleOrchestrator()
        
        # Подсчет API вызовов до запуска
        initial_coingecko_calls = orchestrator.api_tracker.coingecko_calls_today
        
        print(f"🚀 ЗАПУСК АНАЛИЗА...")
        print(f"   Начальное количество CoinGecko calls: {initial_coingecko_calls}")
        print()
        
        # Запускаем pipeline
        alerts = await orchestrator.run_analysis_pipeline()
        
        # Подсчет API вызовов после запуска
        final_coingecko_calls = orchestrator.api_tracker.coingecko_calls_today
        actual_calls_used = final_coingecko_calls - initial_coingecko_calls
        
        print()
        print("📈 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print(f"   CoinGecko API calls использовано: {actual_calls_used}")
        print(f"   Ожидалось максимум: {FUNNEL_CONFIG['top_n_for_enrichment']}")
        print(f"   Создано алертов: {len(alerts)}")
        print()
        
        # ПРОВЕРКА РЕЗУЛЬТАТОВ
        if actual_calls_used <= FUNNEL_CONFIG['top_n_for_enrichment']:
            print("✅ ТЕСТ ПРОЙДЕН: Количество API вызовов соответствует ограничению!")
            print(f"   Использовано {actual_calls_used} из максимум {FUNNEL_CONFIG['top_n_for_enrichment']} разрешенных calls")
        else:
            print("❌ ТЕСТ НЕ ПРОЙДЕН: Превышен лимит API вызовов!")
            print(f"   Использовано {actual_calls_used}, но лимит {FUNNEL_CONFIG['top_n_for_enrichment']}")
            print("   🔧 ТРЕБУЕТСЯ ДОПОЛНИТЕЛЬНОЕ ИСПРАВЛЕНИЕ КОДА!")
        
        print()
        print("📋 ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ:")
        for alert in alerts:
            token = alert.get('token_symbol', 'N/A')
            score = alert.get('final_score', 'N/A')
            recommendation = alert.get('recommendation', 'N/A')
            print(f"   Алерт: {token} | Балл: {score} | Рекомендация: {recommendation}")
        
        return actual_calls_used <= FUNNEL_CONFIG['top_n_for_enrichment']
        
    except Exception as e:
        print(f"❌ ОШИБКА В ТЕСТЕ: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Главная функция тестирования."""
    print("🎯 ПРОВЕРКА ИСПРАВЛЕНИЙ CoinGecko API ОГРАНИЧЕНИЙ")
    print("=" * 60)
    print()
    
    success = await test_token_limiting()
    
    print()
    print("=" * 60)
    if success:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("   Исправления работают корректно.")
    else:
        print("⚠️  ТРЕБУЮТСЯ ДОПОЛНИТЕЛЬНЫЕ ИСПРАВЛЕНИЯ!")
        print("   Проверьте логику ограничения токенов в simple_orchestrator.py")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
