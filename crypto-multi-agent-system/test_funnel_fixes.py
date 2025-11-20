"""
Быстрый тест исправлений воронки - проверяем что алерты генерируются

ИСПРАВЛЕНИЯ:
1. Добавлена переменная top_candidates = enriched_candidates  
2. Понижен min_score_for_alert с 50 до 40 баллов
3. Токены с 60 баллами теперь должны проходить до алертов

ОЖИДАЕМЫЙ РЕЗУЛЬТАТ: хотя бы 1 алерт для токена с 60 баллами
"""
import asyncio
import logging
import sys
import os
from datetime import datetime

# Fix imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('test_funnel_fix.log', mode='w', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

async def test_funnel_fixes():
    """Тестирует исправления воронки - должны получить алерты."""
    logger.info("🔧 ТЕСТ ИСПРАВЛЕНИЙ ВОРОНКИ")
    logger.info("=" * 50)
    
    try:
        # Импортируем исправленный оркестратор
        from agents.orchestrator.simple_orchestrator import SimpleOrchestrator, FUNNEL_CONFIG
        
        # Проверяем конфигурацию
        logger.info("📋 КОНФИГУРАЦИЯ ПОСЛЕ ИСПРАВЛЕНИЙ:")
        logger.info(f"   top_n_for_enrichment: {FUNNEL_CONFIG['top_n_for_enrichment']}")
        logger.info(f"   min_score_for_alert: {FUNNEL_CONFIG['min_score_for_alert']} (ПОНИЖЕН!)")
        logger.info(f"   max_onchain_candidates: {FUNNEL_CONFIG['max_onchain_candidates']}")
        
        # Создаем оркестратор
        logger.info("\n🔧 ИНИЦИАЛИЗАЦИЯ ОРКЕСТРАТОРА...")
        orchestrator = SimpleOrchestrator()
        
        # Запускаем ОДИН цикл анализа
        logger.info("\n🚀 ЗАПУСК ЦИКЛА С ИСПРАВЛЕНИЯМИ...")
        logger.info("   ОЖИДАЕМ: токены с 60 баллами → алерты")
        
        start_time = datetime.now()
        alerts = await orchestrator.run_analysis_pipeline()
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        
        # === РЕЗУЛЬТАТЫ ТЕСТА ===
        logger.info("\n" + "=" * 50)
        logger.info("📊 РЕЗУЛЬТАТЫ ИСПРАВЛЕНИЙ:")
        logger.info(f"   Время выполнения: {duration:.1f} секунд")
        logger.info(f"   Количество алертов: {len(alerts)}")
        
        # Проверяем алерты
        if len(alerts) > 0:
            logger.info("🎉 УСПЕХ! Алерты генерируются:")
            for i, alert in enumerate(alerts):
                logger.info(f"   {i+1}. {alert['token_symbol']}: {alert['final_score']} баллов ({alert['recommendation']})")
            test_passed = True
        else:
            logger.warning("⚠️ Алертов нет. Возможно нужны дополнительные исправления.")
            test_passed = False
        
        # Проверяем API calls
        coingecko_calls = orchestrator.api_tracker.coingecko_calls_today
        logger.info(f"   CoinGecko API calls: {coingecko_calls}")
        
        return test_passed, len(alerts)
        
    except Exception as e:
        logger.error(f"❌ ОШИБКА В ТЕСТЕ: {e}")
        import traceback
        logger.error(f"Трассировка: {traceback.format_exc()}")
        return False, 0

async def main():
    """Главная функция теста."""
    success, alert_count = await test_funnel_fixes()
    
    print(f"\n🎯 РЕЗЮМЕ ТЕСТА ИСПРАВЛЕНИЙ:")
    if success:
        print(f"✅ ИСПРАВЛЕНИЯ РАБОТАЮТ! Получено {alert_count} алертов")
        print("🚀 Воронка работает от начала до конца!")
        exit(0)
    else:
        print(f"⚠️ Исправления частично работают, но алертов нет")
        print("🔍 Возможно, нужны дополнительные настройки")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
