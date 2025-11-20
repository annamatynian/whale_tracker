"""
Тест Telegram подключения - проверка настройки бота

Запустите этот скрипт после настройки .env файла
"""

import os
import sys

# Добавляем путь к корню проекта
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def load_env_file():
    """Загружает .env файл"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .env файл загружен")
        return True
    except ImportError:
        print("⚠️ Устанавливаем python-dotenv...")
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'python-dotenv'])
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ .env файл загружен")
        return True
    except Exception as e:
        print(f"❌ Ошибка загрузки .env: {e}")
        return False

def check_env_variables():
    """Проверяет наличие необходимых переменных"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    print("\n🔍 ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ:")
    
    if not bot_token or bot_token == 'YOUR_BOT_TOKEN_HERE':
        print("❌ TELEGRAM_BOT_TOKEN не настроен")
        print("   Получите токен у @BotFather и добавьте в .env файл")
        return False
    else:
        # Маскируем токен для безопасности
        masked_token = bot_token[:10] + "..." + bot_token[-10:]
        print(f"✅ TELEGRAM_BOT_TOKEN: {masked_token}")
    
    if not chat_id or chat_id == 'YOUR_CHAT_ID_HERE':
        print("❌ TELEGRAM_CHAT_ID не настроен")
        print("   Получите Chat ID через @userinfobot и добавьте в .env файл")
        return False
    else:
        print(f"✅ TELEGRAM_CHAT_ID: {chat_id}")
    
    return True

def test_telegram_connection():
    """Тестирует подключение к Telegram"""
    try:
        from agents.social_intelligence.telegram_agent import TelegramAlertAgent
        
        print("\n🤖 ТЕСТИРОВАНИЕ TELEGRAM БОТА...")
        
        # Создаем агента
        telegram_agent = TelegramAlertAgent()
        
        # Тестируем подключение
        success = telegram_agent.test_connection()
        
        if success:
            print("\n🎉 УСПЕХ! Telegram бот настроен правильно!")
            print("   Проверьте ваш Telegram - должно прийти тестовое сообщение")
            
            # Показываем статистику
            stats = telegram_agent.get_stats()
            print(f"\n📊 Статистика:")
            print(f"   API вызовов: {stats['api_calls']}")
            print(f"   Сообщений отправлено: {stats['alerts_sent']}")
            print(f"   Успешность: {stats['success_rate']:.1f}%")
            
            return True
        else:
            print("\n❌ ОШИБКА подключения к Telegram")
            return False
            
    except Exception as e:
        print(f"\n❌ ОШИБКА при тестировании: {e}")
        return False

def show_next_steps():
    """Показывает следующие шаги"""
    print("\n🚀 СЛЕДУЮЩИЕ ШАГИ:")
    print("   1. Запустите: python telegram_pump_runner.py")
    print("   2. Или интегрируйте с вашими скриптами:")
    print("      from agents.social_intelligence.telegram_agent import TelegramIntegratedPumpAgent")
    print("      agent = TelegramIntegratedPumpAgent()")
    print("      candidates = await agent.discover_and_alert()")

def main():
    """Главная функция тестирования"""
    print("🤖 ТЕСТ TELEGRAM НАСТРОЙКИ")
    print("=" * 50)
    
    # Шаг 1: Загрузка .env
    if not load_env_file():
        return
    
    # Шаг 2: Проверка переменных
    if not check_env_variables():
        print("\n🔧 ИНСТРУКЦИИ ПО НАСТРОЙКЕ:")
        print("   1. Скопируйте .env.example в .env")
        print("   2. Замените YOUR_BOT_TOKEN_HERE на токен от @BotFather")
        print("   3. Замените YOUR_CHAT_ID_HERE на ваш Chat ID")
        print("   4. Запустите этот скрипт снова")
        return
    
    # Шаг 3: Тестирование подключения
    if test_telegram_connection():
        show_next_steps()
    else:
        print("\n🔧 ВОЗМОЖНЫЕ РЕШЕНИЯ:")
        print("   • Проверьте правильность токена и Chat ID")
        print("   • Отправьте боту сообщение /start")
        print("   • Убедитесь что бот не заблокирован")

if __name__ == "__main__":
    main()
