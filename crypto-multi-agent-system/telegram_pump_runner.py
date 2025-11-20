"""
Pump Discovery с Telegram алертами - главный скрипт

Интегрированная система поиска pump кандидатов с уведомлениями в Telegram
"""

import asyncio
import os
import sys
from datetime import datetime

# Добавляем путь к корню проекта
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def load_environment():
    """Загружает переменные окружения"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Переменные окружения загружены")
    except ImportError:
        print("📦 Устанавливаем python-dotenv...")
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'python-dotenv'])
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ Переменные окружения загружены")

async def run_pump_discovery_with_telegram():
    """Запуск Pump Discovery с Telegram алертами"""
    
    print("🚀 PUMP DISCOVERY SYSTEM + TELEGRAM")
    print("=" * 60)
    print(f"Запуск: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Проверяем настройку Telegram
        telegram_enabled = os.getenv('ENABLE_TELEGRAM_ALERTS', 'true').lower() == 'true'
        
        if telegram_enabled:
            print("🤖 Telegram алерты: ВКЛЮЧЕНЫ")
            
            # Проверяем наличие настроек
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            chat_id = os.getenv('TELEGRAM_CHAT_ID')
            
            if not bot_token or not chat_id or bot_token == 'YOUR_BOT_TOKEN_HERE':
                print("⚠️ Telegram не настроен. Запуск без алертов...")
                print("   Для настройки запустите: python test_telegram.py")
                telegram_enabled = False
        else:
            print("📵 Telegram алерты: ОТКЛЮЧЕНЫ")
        
        # Создаем агента
        if telegram_enabled:
            from agents.social_intelligence.telegram_agent import TelegramIntegratedPumpAgent
            agent = TelegramIntegratedPumpAgent(enable_telegram=True)
            print("✅ Система с Telegram алертами готова")
        else:
            from agents.pump_analysis.pump_discovery_agent import PumpDiscoveryAgent
            agent = PumpDiscoveryAgent()
            print("✅ Система без Telegram готова")
        
        print("\n🔍 Начинаю поиск pump кандидатов...")
        
        # Запускаем поиск
        if telegram_enabled:
            candidates = await agent.discover_and_alert()
        else:
            candidates = await agent.discover_tokens_async()
        
        # Выводим результаты в консоль
        print(f"\n📊 РЕЗУЛЬТАТЫ СКАНИРОВАНИЯ:")
        print(f"   Найдено кандидатов: {len(candidates)}")
        
        if candidates:
            print(f"\n🎯 ТОП КАНДИДАТЫ:")
            
            # Сортируем по score
            sorted_candidates = sorted(candidates, key=lambda x: x.final_score, reverse=True)
            
            for i, candidate in enumerate(sorted_candidates[:5], 1):
                emoji = "🚀" if candidate.final_score >= 80 else "🎯" if candidate.final_score >= 60 else "👀"
                print(f"   {i}. {emoji} {candidate.token_symbol}: {candidate.final_score}/100")
                print(f"      💰 ${candidate.indicators.liquidity_usd:,.0f} liquidity")
                print(f"      🕒 {candidate.indicators.age_hours:.1f}h old")
        
        else:
            print("   😔 Кандидаты не найдены в текущем скане")
        
        # Статистика сессии
        if hasattr(agent, 'pump_agent'):
            stats = agent.pump_agent.get_session_stats()
        else:
            stats = agent.get_session_stats()
        
        print(f"\n📈 СТАТИСТИКА СЕССИИ:")
        print(f"   Пар просканировано: {stats['pairs_scanned']}")
        print(f"   Время выполнения: {stats.get('execution_time_ms', 0):.0f}ms")
        print(f"   API вызовов: {stats['api_calls_made']}")
        
        if telegram_enabled and hasattr(agent, 'telegram_agent'):
            telegram_stats = agent.telegram_agent.get_stats()
            print(f"   Telegram алертов: {telegram_stats['alerts_sent']}")
        
        print(f"\n✅ Сканирование завершено успешно!")
        
        return candidates
        
    except KeyboardInterrupt:
        print("\n⏹️ Остановлено пользователем")
        return []
    except Exception as e:
        print(f"\n❌ Ошибка выполнения: {e}")
        import traceback
        traceback.print_exc()
        return []

async def run_continuous_monitoring():
    """Непрерывный мониторинг с интервалами"""
    
    # Интервал сканирования (в минутах)
    scan_interval = int(os.getenv('SCAN_INTERVAL_MINUTES', '30'))
    
    print(f"🔄 НЕПРЕРЫВНЫЙ МОНИТОРИНГ")
    print(f"Интервал сканирования: {scan_interval} минут")
    print("Нажмите Ctrl+C для остановки")
    
    scan_count = 0
    
    try:
        while True:
            scan_count += 1
            print(f"\n{'='*60}")
            print(f"СКАН #{scan_count} - {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}")
            
            # Запускаем сканирование
            candidates = await run_pump_discovery_with_telegram()
            
            # Ждем до следующего скана
            print(f"\n⏳ Следующий скан через {scan_interval} минут...")
            await asyncio.sleep(scan_interval * 60)
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Мониторинг остановлен после {scan_count} сканов")

def show_menu():
    """Показывает меню выбора режима"""
    print("\n🎯 ВЫБЕРИТЕ РЕЖИМ РАБОТЫ:")
    print("   1. Одноразовое сканирование")
    print("   2. Непрерывный мониторинг")
    print("   3. Тест Telegram подключения")
    print("   4. Выход")
    
    while True:
        try:
            choice = input("\nВведите номер (1-4): ").strip()
            if choice in ['1', '2', '3', '4']:
                return int(choice)
            print("❌ Введите число от 1 до 4")
        except KeyboardInterrupt:
            return 4

async def main():
    """Главная функция"""
    
    # Загружаем окружение
    load_environment()
    
    # Показываем меню
    choice = show_menu()
    
    if choice == 1:
        # Одноразовое сканирование
        await run_pump_discovery_with_telegram()
        
    elif choice == 2:
        # Непрерывный мониторинг
        await run_continuous_monitoring()
        
    elif choice == 3:
        # Тест Telegram
        from test_telegram import main as test_telegram_main
        test_telegram_main()
        
    elif choice == 4:
        print("👋 До свидания!")
        return
    
    print("\n🎉 Программа завершена")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Программа остановлена пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
