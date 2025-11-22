"""
Тест Telegram бота для Whale Tracker
=====================================

Простой скрипт для проверки настройки Telegram бота.
Запустите после настройки TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID в .env файле.

Usage:
    python test_telegram_bot.py
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Добавляем корневую директорию в путь
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def load_env():
    """Загрузка переменных окружения из .env файла."""
    try:
        from dotenv import load_dotenv

        env_path = project_root / '.env'

        if not env_path.exists():
            print("❌ Файл .env не найден!")
            print(f"   Ожидаемый путь: {env_path}")
            print("\n🔧 Создайте .env файл:")
            print("   cp .env.example .env")
            return False

        load_dotenv(env_path)
        print("✅ Файл .env загружен")
        return True

    except ImportError:
        print("⚠️  python-dotenv не установлен, устанавливаю...")
        import subprocess
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'python-dotenv'])
        from dotenv import load_dotenv
        load_dotenv(project_root / '.env')
        print("✅ Файл .env загружен")
        return True
    except Exception as e:
        print(f"❌ Ошибка при загрузке .env: {e}")
        return False


def check_credentials():
    """Проверка наличия и валидности учетных данных Telegram."""
    print("\n🔍 ПРОВЕРКА УЧЕТНЫХ ДАННЫХ:")
    print("-" * 60)

    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')

    all_good = True

    # Проверка токена бота
    if not bot_token or bot_token == 'YOUR_BOT_TOKEN_HERE':
        print("❌ TELEGRAM_BOT_TOKEN не настроен")
        print("   📝 Получите токен:")
        print("   1. Откройте Telegram и найдите @BotFather")
        print("   2. Отправьте команду /newbot")
        print("   3. Следуйте инструкциям для создания бота")
        print("   4. Скопируйте токен и вставьте в .env файл")
        all_good = False
    else:
        # Маскируем токен для безопасности (показываем только первые/последние символы)
        if len(bot_token) > 20:
            masked = f"{bot_token[:8]}...{bot_token[-8:]}"
        else:
            masked = "***"
        print(f"✅ TELEGRAM_BOT_TOKEN: {masked}")

    # Проверка Chat ID
    if not chat_id or chat_id == 'YOUR_CHAT_ID_HERE':
        print("❌ TELEGRAM_CHAT_ID не настроен")
        print("   📝 Получите Chat ID:")
        print("   1. Откройте Telegram и найдите @userinfobot")
        print("   2. Отправьте боту команду /start")
        print("   3. Скопируйте ваш ID и вставьте в .env файл")
        all_good = False
    else:
        print(f"✅ TELEGRAM_CHAT_ID: {chat_id}")

    return all_good


async def test_connection():
    """Тестирование подключения к Telegram API."""
    print("\n🤖 ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ К TELEGRAM:")
    print("-" * 60)

    try:
        from src.notifications.telegram_notifier import TelegramNotifier

        # Создаем экземпляр нотификатора
        notifier = TelegramNotifier()

        # Тестируем соединение
        print("⏳ Подключаюсь к Telegram API...")
        success = await notifier.test_connection()

        if not success:
            print("❌ Не удалось подключиться к Telegram API")
            print("\n🔧 Возможные причины:")
            print("   • Неверный токен бота")
            print("   • Бот был удален")
            print("   • Проблемы с интернет-соединением")
            return False

        print("✅ Подключение успешно!")

        # Отправляем тестовое сообщение
        print("\n📤 Отправляю тестовое сообщение...")

        test_message = f"""
🐋 **Whale Tracker - Тест подключения**

✅ Telegram бот настроен правильно!

🕐 **Время теста:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🤖 **Статус:** Готов к мониторингу китов

Теперь вы будете получать уведомления о:
• Прямых переводах на биржи
• Скрытых переводах через промежуточные адреса
• Статистических аномалиях
"""

        send_success = await notifier.send_message(test_message)

        if send_success:
            print("✅ Тестовое сообщение отправлено!")
            print("   📱 Проверьте ваш Telegram")
            return True
        else:
            print("❌ Не удалось отправить сообщение")
            print("\n🔧 Возможные причины:")
            print("   • Неверный Chat ID")
            print("   • Вы не отправили боту команду /start")
            print("   • Бот заблокирован")
            print("\n💡 Решение:")
            print("   1. Найдите вашего бота в Telegram")
            print("   2. Отправьте ему команду /start")
            print("   3. Запустите этот скрипт снова")
            return False

    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("\n🔧 Установите зависимости:")
        print("   pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_whale_alerts():
    """Тестирование различных типов whale алертов."""
    print("\n🐋 ТЕСТИРОВАНИЕ WHALE АЛЕРТОВ:")
    print("-" * 60)

    try:
        from src.notifications.telegram_notifier import TelegramNotifier

        notifier = TelegramNotifier()

        # Тест 1: Прямой перевод на биржу
        print("\n1️⃣  Тест: Whale → Exchange (прямой перевод)")
        await notifier.send_whale_direct_transfer_alert(
            whale_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
            tx_data={
                'value_usd': 1500000,
                'hash': '0xtest123abc456def'
            },
            destination_info={
                'name': 'Binance Hot Wallet',
                'type': 'exchange'
            },
            current_price=3500.50
        )
        print("   ✅ Алерт отправлен")
        await asyncio.sleep(2)  # Небольшая задержка между сообщениями

        # Тест 2: One-hop обнаружение
        print("\n2️⃣  Тест: Whale → Unknown → Exchange (one-hop)")
        await notifier.send_whale_onehop_alert(
            whale_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
            whale_tx={
                'value_usd': 2000000,
                'hash': '0xtest789ghi012jkl'
            },
            intermediate_address="0x123456789abcdef123456789abcdef123456789a",
            onehop_result={
                'exchange_name': 'Coinbase',
                'time_delay_minutes': 25
            },
            current_price=3500.50
        )
        print("   ✅ Алерт отправлен")
        await asyncio.sleep(2)

        # Тест 3: Статистическая аномалия
        print("\n3️⃣  Тест: Statistical Anomaly (аномально большая транзакция)")
        await notifier.send_anomaly_alert(
            whale_address="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0",
            tx_data={
                'value_usd': 5000000
            },
            anomaly_info={
                'average_amount': 800000,
                'threshold': 1040000
            }
        )
        print("   ✅ Алерт отправлен")

        print("\n✅ Все тестовые алерты отправлены!")
        print("   📱 Проверьте ваш Telegram - должно быть 4 сообщения")

    except Exception as e:
        print(f"❌ Ошибка при отправке алертов: {e}")
        import traceback
        traceback.print_exc()


def show_next_steps():
    """Показать следующие шаги после успешной настройки."""
    print("\n" + "=" * 60)
    print("🎉 ПОЗДРАВЛЯЕМ! Telegram бот настроен и готов к работе!")
    print("=" * 60)
    print("\n🚀 СЛЕДУЮЩИЕ ШАГИ:\n")
    print("1️⃣  Настройте адреса китов в .env файле:")
    print("   WHALE_ADDRESSES=0xАдрес1,0xАдрес2,0xАдрес3\n")
    print("2️⃣  Настройте RPC провайдеры:")
    print("   INFURA_URL=https://mainnet.infura.io/v3/YOUR_API_KEY")
    print("   (получить бесплатно на https://infura.io)\n")
    print("3️⃣  Запустите Whale Tracker:")
    print("   python main.py\n")
    print("4️⃣  Или запустите один раз для теста:")
    print("   python main.py --once\n")
    print("📚 Документация: docs/\n")


async def main():
    """Главная функция."""
    print("\n" + "=" * 60)
    print("🐋 WHALE TRACKER - Тест Telegram Бота")
    print("=" * 60)

    # Шаг 1: Загрузка .env
    if not load_env():
        return

    # Шаг 2: Проверка учетных данных
    if not check_credentials():
        print("\n" + "=" * 60)
        print("⚠️  ТРЕБУЕТСЯ НАСТРОЙКА")
        print("=" * 60)
        print("\n📋 Инструкции по настройке .env файла:")
        print("   1. Откройте файл .env в текстовом редакторе")
        print("   2. Найдите строки TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID")
        print("   3. Замените значения согласно инструкциям выше")
        print("   4. Сохраните файл и запустите этот скрипт снова\n")
        return

    # Шаг 3: Тест подключения
    connection_ok = await test_connection()

    if not connection_ok:
        return

    # Шаг 4: Спросить, хотят ли протестировать whale алерты
    print("\n" + "-" * 60)
    try:
        response = input("\n❓ Хотите протестировать whale алерты? (y/n): ").strip().lower()

        if response in ['y', 'yes', 'д', 'да']:
            await test_whale_alerts()
    except (EOFError, KeyboardInterrupt):
        print("\n\n⏩ Пропускаем тест whale алертов")

    # Шаг 5: Показать следующие шаги
    show_next_steps()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Тест прерван. До свидания!")
    except Exception as e:
        print(f"\n❌ Фатальная ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
