"""
Telegram Notifier - Отправляет алерты в Telegram

Использует библиотеку python-telegram-bot.
Установите ее: pip install python-telegram-bot
"""
import os
import logging
from typing import Dict, Any, Optional

# Убедитесь, что библиотека установлена: pip install python-telegram-bot
try:
    from telegram import Bot
    from telegram.error import TelegramError
except ImportError:
    print("❌ ОШИБКА: Библиотека 'python-telegram-bot' не установлена.")
    print("   Пожалуйста, выполните команду: pip install python-telegram-bot")
    # Создаем "пустышку", чтобы остальная система могла импортироваться
    Bot = None
    TelegramError = Exception

from config.settings import get_settings

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """Отправляет структурированные сообщения в Telegram."""
    def __init__(self):
        settings = get_settings()
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.dry_run = settings.DRY_RUN

        if not self.bot_token or not self.chat_id:
            logger.warning("Токен Telegram бота или ID чата не настроены. Уведомления будут отключены.")
            self.bot = None
        elif Bot is None:
             self.bot = None # Библиотека не установлена
        else:
            self.bot = Bot(token=self.bot_token)

    def _format_alert(self, alert_data: Dict[str, Any]) -> str:
        """Форматирует данные алерта в красивое сообщение."""
        try:
            # Парсим JSON строку с информацией о токене
            import json
            token_info = json.loads(alert_data.get('token_info', '{}'))

            symbol = token_info.get('base_token_symbol', 'N/A')
            chain = token_info.get('chain_id', 'N/A')
            score = alert_data.get('total_score', 0)
            recommendation = alert_data.get('recommendation', 'N/A')
            
            positive_signals = "\n".join([f"  {s}" for s in alert_data.get('positive_signals', [])])
            red_flags = "\n".join([f"  {s}" for s in alert_data.get('red_flags', [])])

            message = (
                f"🔥 *Pump Candidate Alert* 🔥\n\n"
                f"Токен: *${symbol}* ({chain})\n"
                f"Итоговый балл: *{score}/100*\n"
                f"Рекомендация: *{recommendation}*\n\n"
                f"✅ *Позитивные сигналы:*\n{positive_signals}\n\n"
                f"🚨 *Красные флаги:*\n{red_flags}\n\n"
                f"🔗 [DexScreener](https://dexscreener.com/{chain}/{token_info.get('base_token_address')})"
            )
            return message
        except Exception as e:
            logger.error(f"Ошибка форматирования сообщения: {e}")
            return f"Ошибка форматирования алерта: {alert_data}"

    async def send_alert(self, alert_data: Dict[str, Any]):
        """Отправляет алерт в Telegram."""
        if not self.bot:
            logger.debug("Пропуск отправки алерта: Telegram не настроен.")
            return

        message = self._format_alert(alert_data)

        if self.dry_run:
            print("\n--- 💧 DRY RUN: Telegram Alert ---")
            print(message)
            print("---------------------------------\n")
            logger.info(f"DRY RUN: Имитация отправки алерта для {alert_data.get('token_info', {}).get('base_token_symbol')}")
            return

        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='Markdown'
            )
            logger.info(f"✅ Алерт для {alert_data.get('token_info', {}).get('base_token_symbol')} успешно отправлен.")
        except TelegramError as e:
            logger.error(f"❌ Ошибка отправки алерта в Telegram: {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при отправке в Telegram: {e}")

    async def test_connection(self) -> bool:
        """Проверяет соединение с API Telegram."""
        if not self.bot:
            return False
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"Успешное подключение к Telegram как '{bot_info.username}'.")
            return True
        except Exception as e:
            logger.error(f"Не удалось подключиться к Telegram: {e}")
            return False
