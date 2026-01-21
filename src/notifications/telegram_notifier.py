"""
Telegram Notifier - Circuit Breaker Alerts

Sends push notifications for CRITICAL data quality issues.
"""

import asyncio
import logging
from typing import Optional
import aiohttp

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Send Telegram alerts for critical events"""
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialize Telegram notifier.
        
        Args:
            bot_token: Telegram bot token from @BotFather
            chat_id: Your Telegram chat ID
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    async def send_alert(self, message: str) -> bool:
        """
        Send alert message.
        
        Args:
            message: Alert text
            
        Returns:
            True if sent successfully
        """
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
                
                async with session.post(self.api_url, json=payload) as resp:
                    if resp.status == 200:
                        logger.info("✅ Telegram alert sent")
                        return True
                    else:
                        error = await resp.text()
                        logger.error(f"❌ Telegram failed: {error}")
                        return False
                        
        except Exception as e:
            logger.error(f"❌ Telegram error: {e}")
            return False
