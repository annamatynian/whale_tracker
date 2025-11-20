"""
Improved Telegram Client for Social Signal Analysis

Исправленная версия с улучшенным поиском адресов и обработкой ошибок.
"""
import asyncio
import logging
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict

from dotenv import load_dotenv

# Попытка импорта pyrogram
try:
    from pyrogram import Client
    from pyrogram.errors import UserNotParticipant, FloodWait
    PYROGRAM_AVAILABLE = True
except ImportError:
    PYROGRAM_AVAILABLE = False
    logging.warning("Pyrogram не установлен. Telegram функционал будет работать в mock-режиме.")

load_dotenv()

# --- УЛУЧШЕННАЯ КОНФИГУРАЦИЯ ---
ALPHA_CHANNELS = [
    "dumbmoney_gems",
    "Gems_Radar", 
    "gem_calls",
    "cryptogems_signals",  # Добавил больше каналов
    "early_gems_calls"
]

SCAN_HOURS_BACK = 6  # Уменьшил с 12 до 6 часов для начала
MAX_MESSAGES_PER_CHANNEL = 100  # Лимит сообщений

# Regex для поиска Ethereum адресов (более точный)
ETH_ADDRESS_PATTERN = re.compile(r'\b0x[a-fA-F0-9]{40}\b')

class TelegramSocialAgent:
    """Улучшенный агент для сканирования Telegram каналов."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.api_id = os.getenv("TELEGRAM_API_ID")
        self.api_hash = os.getenv("TELEGRAM_API_HASH")
        
        # Проверяем доступность pyrogram
        if not PYROGRAM_AVAILABLE:
            self.logger.warning("Pyrogram не доступен. Работаю в mock-режиме.")
            self.app = None
            self.is_mock = True
            return

        if not all([self.api_id, self.api_hash]):
            self.logger.warning("TELEGRAM_API_ID или TELEGRAM_API_HASH не найдены. Работаю в mock-режиме.")
            self.app = None
            self.is_mock = True
        else:
            self.app = Client("crypto_agent_session", api_id=int(self.api_id), api_hash=self.api_hash)
            self.is_mock = False

    def extract_contract_addresses(self, text: str) -> List[str]:
        """Извлекает адреса контрактов из текста используя regex."""
        if not text:
            return []
        return ETH_ADDRESS_PATTERN.findall(text)

    async def scan_channels_for_mentions(self, contract_addresses: List[str]) -> Dict[str, int]:
        """
        Сканирует каналы на упоминание контрактов с улучшенным поиском.
        """
        if self.is_mock or not contract_addresses:
            # Mock данные для тестирования
            mock_mentions = {}
            for addr in contract_addresses:
                # Симулируем случайные упоминания для тестирования
                import random
                mock_mentions[addr.lower()] = random.randint(0, 3)
            self.logger.info(f"🎭 MOCK MODE: Сгенерированы тестовые упоминания")
            return mock_mentions

        mentions_count = defaultdict(int)
        normalized_addresses = {addr.lower(): addr for addr in contract_addresses}
        since_date = datetime.now() - timedelta(hours=SCAN_HOURS_BACK)

        try:
            await self.app.start()
            self.logger.info(f"📱 Подключен к Telegram. Сканирую {len(ALPHA_CHANNELS)} каналов...")

            for channel in ALPHA_CHANNELS:
                try:
                    message_count = 0
                    channel_mentions = 0
                    
                    # Используем iter_history для более эффективного сканирования
                    async for message in self.app.iter_history(
                        channel, 
                        limit=MAX_MESSAGES_PER_CHANNEL,
                        offset_date=since_date
                    ):
                        message_count += 1
                        
                        if not message.text:
                            continue
                            
                        # Извлекаем все адреса из сообщения
                        found_addresses = self.extract_contract_addresses(message.text)
                        
                        for found_addr in found_addresses:
                            if found_addr.lower() in normalized_addresses:
                                mentions_count[found_addr.lower()] += 1
                                channel_mentions += 1
                                self.logger.info(
                                    f"🔥 Найдено упоминание {found_addr} в {channel} "
                                    f"({message.date.strftime('%H:%M')})"
                                )

                    self.logger.debug(f"✅ {channel}: {message_count} сообщений, {channel_mentions} упоминаний")

                except UserNotParticipant:
                    self.logger.warning(f"❌ Не состоите в канале {channel}")
                except FloodWait as e:
                    self.logger.warning(f"⏱️ Rate limit для {channel}, ждем {e.value} сек")
                    await asyncio.sleep(e.value)
                except Exception as e:
                    self.logger.error(f"❌ Ошибка сканирования {channel}: {e}")
        
        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка Telegram клиента: {e}")
        finally:
            if self.app and self.app.is_initialized:
                await self.app.stop()

        # Конвертируем обратно к оригинальным адресам
        result = {}
        for addr in contract_addresses:
            result[addr] = mentions_count.get(addr.lower(), 0)
        
        total_mentions = sum(result.values())
        self.logger.info(f"📊 Сканирование завершено. Всего упоминаний: {total_mentions}")
        return result

    async def get_social_momentum_score(self, contract_addresses: List[str]) -> Dict[str, int]:
        """
        Получает социальный momentum score для адресов.
        
        Returns:
            Dict с momentum score (0-100) для каждого адреса
        """
        mentions = await self.scan_channels_for_mentions(contract_addresses)
        
        momentum_scores = {}
        for addr, mention_count in mentions.items():
            # Конвертируем упоминания в score (0-100)
            if mention_count >= 5:
                score = 100
            elif mention_count >= 3:
                score = 80
            elif mention_count >= 1:
                score = 50
            else:
                score = 0
                
            momentum_scores[addr] = score
            
        return momentum_scores

# === ТЕСТИРОВАНИЕ ===
async def test_telegram_agent():
    """Быстрый тест агента."""
    print("🧪 Тестирование TelegramSocialAgent...")
    
    # Тестовые адреса (известные токены)
    test_addresses = [
        "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",  # WBTC
        "0xa0b86a33e6441d9c2b9c1d3c0d8d4e2f8ad9f1e5"   # Вымышленный
    ]
    
    agent = TelegramSocialAgent()
    
    # Тест 1: Поиск упоминаний
    mentions = await agent.scan_channels_for_mentions(test_addresses)
    print(f"\n📊 Упоминания найдены:")
    for addr, count in mentions.items():
        print(f"   {addr}: {count} упоминаний")
    
    # Тест 2: Momentum score
    momentum = await agent.get_social_momentum_score(test_addresses)
    print(f"\n🚀 Momentum scores:")
    for addr, score in momentum.items():
        print(f"   {addr}: {score}/100")

if __name__ == "__main__":
    asyncio.run(test_telegram_agent())
