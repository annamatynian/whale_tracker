#!/usr/bin/env python3
"""
Crypto Pump Scanner - Автоматический запуск раз в час

Этот скрипт оптимизирован для:
- Запуска раз в час (а не постоянно)
- Эффективного использования API лимитов
- Анализа 15-20 токенов за запуск

Использование:
    python hourly_pump_scanner.py          # Запуск один раз
    python hourly_pump_scanner.py --loop   # Бесконечный цикл каждый час
"""

import asyncio
import sys
import time
import schedule
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.orchestrator.simple_orchestrator import SimpleOrchestrator
from config.settings import setup_logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hourly_pump_scanner.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def run_pump_scan():
    """Запуск одного цикла pump сканирования"""
    try:
        logger.info("🚀 Запуск часового pump сканирования...")
        
        # Инициализация оркестратора
        orchestrator = SimpleOrchestrator()
        
        # Запуск анализа
        alerts = await orchestrator.run_analysis_pipeline()
        
        # Логирование результатов
        if alerts:
            logger.info(f"✅ Найдено {len(alerts)} pump кандидатов:")
            for alert in alerts:
                logger.info(f"   🎯 {alert['token_symbol']}: {alert['final_score']}/100 ({alert['recommendation']})")
        else:
            logger.info("📉 Pump кандидаты не найдены в этом часе")
            
        logger.info("✅ Часовое сканирование завершено")
        return alerts
        
    except Exception as e:
        logger.error(f"❌ Ошибка при сканировании: {e}", exc_info=True)
        return []

def job():
    """Wrapper для schedule библиотеки"""
    try:
        results = asyncio.run(run_pump_scan())
        return results
    except Exception as e:
        logger.error(f"❌ Ошибка в job: {e}")
        return []

def run_hourly_loop():
    """Запуск бесконечного цикла каждый час"""
    logger.info("🔄 Запуск в режиме hourly loop...")
    logger.info("📅 Следующий запуск каждый час в :00 минут")
    
    # Планируем запуск каждый час
    schedule.every().hour.at(":00").do(job)
    
    # Первый запуск сразу
    logger.info("▶️ Первый запуск сейчас...")
    job()
    
    # Бесконечный цикл
    while True:
        schedule.run_pending()
        time.sleep(60)  # Проверяем каждую минуту

async def run_single_scan():
    """Запуск одного сканирования и выход"""
    logger.info("🎯 Запуск одиночного сканирования...")
    alerts = await run_pump_scan()
    
    if alerts:
        print(f"\n🎉 РЕЗУЛЬТАТЫ: Найдено {len(alerts)} pump кандидатов")
        print("=" * 60)
        for i, alert in enumerate(alerts, 1):
            print(f"{i}. {alert['token_symbol']}")
            print(f"   Score: {alert['final_score']}/100")
            print(f"   Recommendation: {alert['recommendation']}")
            print()
    else:
        print("\n📉 Pump кандидаты не найдены")
        print("Возможные причины:")
        print("- Рынок спокойный, нет активности")
        print("- Настройки фильтров слишком строгие") 
        print("- Все найденные токены не прошли security проверки")

def main():
    """Главная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Crypto Pump Scanner - Hourly Mode")
    parser.add_argument(
        "--loop", 
        action="store_true", 
        help="Запуск в режиме hourly loop (бесконечно каждый час)"
    )
    
    args = parser.parse_args()
    
    print("💎 CRYPTO PUMP SCANNER v2.0")
    print("🕐 Оптимизирован для запуска раз в час")
    print("📊 Анализирует до 20 токенов за запуск")
    print("🎯 Пороги: 45+ баллов для API calls")
    print("=" * 50)
    
    if args.loop:
        try:
            run_hourly_loop()
        except KeyboardInterrupt:
            logger.info("👋 Остановка по Ctrl+C")
    else:
        asyncio.run(run_single_scan())

if __name__ == "__main__":
    main()
