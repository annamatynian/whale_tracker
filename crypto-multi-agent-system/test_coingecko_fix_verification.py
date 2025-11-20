"""
Тест проверки исправления критического бага CoinGecko API

Этот тест проверяет:
1. Правильное ограничение токенов для enrichment
2. Корректный расчет API calls
3. Соблюдение FUNNEL_CONFIG лимитов

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: максимум 5 CoinGecko API calls за цикл
"""
import asyncio
import logging
import sys
import os
from typing import List
from datetime import datetime

# Fix imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_coingecko_fix.log', mode='w', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

async def test_coingecko_limit_fix():
    """Тестирует исправление лимитов CoinGecko API calls."""
    logger.info("🧪 НАЧИНАЕМ ТЕСТ ИСПРАВЛЕНИЯ COINGECKO API ЛИМИТОВ")
    logger.info("=" * 60)
    
    try:
        # Импортируем исправленный оркестратор
        from agents.orchestrator.simple_orchestrator import SimpleOrchestrator, FUNNEL_CONFIG
        
        # Проверяем конфигурацию
        logger.info("📋 ПРОВЕРКА КОНФИГУРАЦИИ:")
        logger.info(f"   top_n_for_enrichment: {FUNNEL_CONFIG['top_n_for_enrichment']}")
        logger.info(f"   max_onchain_candidates: {FUNNEL_CONFIG['max_onchain_candidates']}")
        logger.info(f"   min_score_for_alert: {FUNNEL_CONFIG['min_score_for_alert']}")
        
        # Проверяем ожидаемые лимиты
        expected_coingecko_calls = FUNNEL_CONFIG['top_n_for_enrichment']
        logger.info(f"🎯 ОЖИДАЕМО максимум {expected_coingecko_calls} CoinGecko API calls")
        
        # Создаем оркестратор
        logger.info("\n🔧 ИНИЦИАЛИЗАЦИЯ ОРКЕСТРАТОРА...")
        orchestrator = SimpleOrchestrator()
        
        # Сохраняем изначальное количество calls
        initial_coingecko_calls = orchestrator.api_tracker.coingecko_calls_today
        initial_rpc_calls = orchestrator.api_tracker.rpc_calls_today
        
        logger.info(f"   Изначальные CoinGecko calls: {initial_coingecko_calls}")
        logger.info(f"   Изначальные RPC calls: {initial_rpc_calls}")
        
        # Запускаем ОДИН цикл анализа
        logger.info("\n🚀 ЗАПУСК ОДНОГО ЦИКЛА АНАЛИЗА...")
        logger.info("   Отслеживаем количество API calls...")
        
        start_time = datetime.now()
        alerts = await orchestrator.run_analysis_pipeline()
        end_time = datetime.now()
        
        # Проверяем финальное количество calls
        final_coingecko_calls = orchestrator.api_tracker.coingecko_calls_today
        final_rpc_calls = orchestrator.api_tracker.rpc_calls_today
        
        coingecko_calls_used = final_coingecko_calls - initial_coingecko_calls
        rpc_calls_used = final_rpc_calls - initial_rpc_calls
        
        duration = (end_time - start_time).total_seconds()
        
        # === РЕЗУЛЬТАТЫ ТЕСТА ===
        logger.info("\n" + "=" * 60)
        logger.info("📊 РЕЗУЛЬТАТЫ ТЕСТА:")
        logger.info(f"   Время выполнения: {duration:.1f} секунд")
        logger.info(f"   Количество алертов: {len(alerts)}")
        logger.info(f"   CoinGecko API calls использовано: {coingecko_calls_used}")
        logger.info(f"   RPC calls использовано: {rpc_calls_used}")
        
        # === ПРОВЕРКА ЛИМИТОВ ===
        logger.info("\n🔍 ПРОВЕРКА СОБЛЮДЕНИЯ ЛИМИТОВ:")
        
        if coingecko_calls_used <= expected_coingecko_calls:
            logger.info(f"   ✅ CoinGecko лимит СОБЛЮДЕН: {coingecko_calls_used} <= {expected_coingecko_calls}")
            test_passed = True
        else:
            logger.error(f"   ❌ CoinGecko лимит НАРУШЕН: {coingecko_calls_used} > {expected_coingecko_calls}")
            test_passed = False
        
        # Проверяем разумность RPC calls
        max_reasonable_rpc = FUNNEL_CONFIG['max_onchain_candidates'] * 10  # ~10 calls на токен
        if rpc_calls_used <= max_reasonable_rpc:
            logger.info(f"   ✅ RPC лимит разумен: {rpc_calls_used} <= {max_reasonable_rpc}")
        else:
            logger.warning(f"   ⚠️ RPC calls высоки: {rpc_calls_used} > {max_reasonable_rpc}")
        
        # === РАСЧЕТ ЭКОНОМИИ ===
        logger.info("\n💰 РАСЧЕТ ЭКОНОМИИ:")
        old_calls_per_cycle = 200  # До исправления
        new_calls_per_cycle = coingecko_calls_used
        
        if new_calls_per_cycle > 0:
            savings_factor = old_calls_per_cycle / new_calls_per_cycle
            logger.info(f"   До исправления: ~{old_calls_per_cycle} calls за цикл")
            logger.info(f"   После исправления: {new_calls_per_cycle} calls за цикл")
            logger.info(f"   Экономия: {savings_factor:.1f}x меньше API calls!")
            
            # Расчет количества запусков в месяц
            monthly_limit = 10000
            cycles_per_month_old = monthly_limit // old_calls_per_cycle
            cycles_per_month_new = monthly_limit // new_calls_per_cycle if new_calls_per_cycle > 0 else monthly_limit
            
            logger.info(f"   Запусков в месяц (до): {cycles_per_month_old}")
            logger.info(f"   Запусков в месяц (после): {cycles_per_month_new}")
        
        # === ВЫВОДЫ ===
        logger.info("\n" + "=" * 60)
        if test_passed:
            logger.info("🎉 ТЕСТ ПРОЙДЕН! Исправление CoinGecko лимитов работает корректно.")
            logger.info("✅ Система готова к безопасному тестированию с ограниченными API calls.")
        else:
            logger.error("❌ ТЕСТ НЕ ПРОЙДЕН! Требуется дополнительная отладка.")
        
        # Показываем детали алертов если есть
        if alerts:
            logger.info(f"\n📢 СГЕНЕРИРОВАННЫЕ АЛЕРТЫ ({len(alerts)}):")
            for i, alert in enumerate(alerts[:3]):  # Показываем первые 3
                logger.info(f"   {i+1}. {alert['token_symbol']}: {alert['final_score']} баллов ({alert['recommendation']})")
            if len(alerts) > 3:
                logger.info(f"   ... и еще {len(alerts) - 3} алертов")
        
        return test_passed
        
    except Exception as e:
        logger.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА В ТЕСТЕ: {e}")
        import traceback
        logger.error(f"Трассировка: {traceback.format_exc()}")
        return False
    
    finally:
        logger.info("\n🏁 ТЕСТ ЗАВЕРШЕН")

async def main():
    """Главная функция теста."""
    success = await test_coingecko_limit_fix()
    
    if success:
        print("\n🎯 РЕЗЮМЕ: Исправление работает! Можно продолжать тестирование.")
        exit(0)
    else:
        print("\n⚠️ РЕЗЮМЕ: Требуется дополнительная отладка.")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
