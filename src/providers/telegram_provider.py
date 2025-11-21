"""
Telegram Provider Implementation

Concrete implementation of NotificationProvider for Telegram.
Refactored from src/notifications/telegram_notifier.py
"""

import os
import logging
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime

from src.abstractions.notification_provider import NotificationProvider


class TelegramProvider(NotificationProvider):
    """
    Telegram notification provider implementation.

    Uses Telegram Bot API to send alerts and notifications.
    """

    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None
    ):
        """
        Initialize Telegram provider.

        Args:
            bot_token: Telegram bot token (defaults to TELEGRAM_BOT_TOKEN env var)
            chat_id: Telegram chat ID (defaults to TELEGRAM_CHAT_ID env var)
        """
        self.logger = logging.getLogger(__name__)
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None

    @property
    def provider_name(self) -> str:
        """Get provider name."""
        return 'telegram'

    @property
    def is_configured(self) -> bool:
        """Check if provider is configured."""
        return bool(self.bot_token and self.chat_id)

    async def test_connection(self) -> bool:
        """
        Test Telegram bot connection.

        Returns:
            bool: True if connection successful
        """
        try:
            if not self.is_configured:
                self.logger.error("Telegram bot token or chat ID not configured")
                return False

            url = f"{self.base_url}/getMe"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()

            if data.get('ok'):
                bot_info = data.get('result', {})
                bot_name = bot_info.get('username', 'Unknown')
                self.logger.info(f"Telegram bot connected: @{bot_name}")
                return True
            else:
                self.logger.error(f"Telegram API error: {data}")
                return False

        except Exception as e:
            self.logger.error(f"Error testing Telegram connection: {e}")
            return False

    async def send_message(
        self,
        message: str,
        parse_mode: Optional[str] = 'Markdown'
    ) -> bool:
        """
        Send simple text message.

        Args:
            message: Message text
            parse_mode: Formatting mode ('Markdown', 'HTML', or None)

        Returns:
            bool: True if sent successfully
        """
        try:
            if not self.is_configured:
                self.logger.error("Telegram not configured")
                return False

            url = f"{self.base_url}/sendMessage"

            payload = {
                'chat_id': int(self.chat_id),
                'text': message,
                'disable_notification': False
            }

            if parse_mode:
                payload['parse_mode'] = parse_mode

            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=payload, timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()

            if data.get('ok'):
                self.logger.debug("Telegram message sent successfully")
                return True
            else:
                self.logger.error(f"Telegram send error: {data}")
                return False

        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
            return False

    async def send_whale_direct_transfer_alert(
        self,
        from_address: str,
        to_address: str,
        amount_eth: float,
        tx_hash: str,
        block_number: int,
        timestamp: datetime,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send whale direct transfer alert.

        Args:
            from_address: Whale address
            to_address: Destination address (exchange)
            amount_eth: Amount in ETH
            tx_hash: Transaction hash
            block_number: Block number
            timestamp: Transaction timestamp
            additional_data: Optional data (exchange_name, price_usd, etc.)

        Returns:
            bool: True if sent successfully
        """
        try:
            additional_data = additional_data or {}
            exchange_name = additional_data.get('exchange_name', 'Unknown Exchange')
            amount_usd = additional_data.get('amount_usd', 0)
            current_price = additional_data.get('current_price')

            message = f"""
🚨 **WHALE → EXCHANGE DIRECT**

🐋 **Whale:** `{from_address[:10]}...{from_address[-8:]}`
💰 **Amount:** {amount_eth:.4f} ETH (${amount_usd:,.0f})
💱 **Exchange:** {exchange_name}
📍 **To:** `{to_address[:10]}...{to_address[-8:]}`
"""

            if current_price:
                message += f"💹 **Price:** ${current_price:,.2f}\n"

            message += f"""
⚠️ **POTENTIAL DUMP SIGNAL**

🔗 [View Transaction](https://etherscan.io/tx/{tx_hash})
📦 **Block:** #{block_number:,}
🕐 **Time:** {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
"""

            return await self.send_message(message)

        except Exception as e:
            self.logger.error(f"Error sending direct transfer alert: {e}")
            return False

    async def send_whale_onehop_alert(
        self,
        whale_address: str,
        intermediate_address: str,
        exchange_address: Optional[str],
        whale_amount_eth: float,
        exchange_amount_eth: Optional[float],
        whale_tx_hash: str,
        exchange_tx_hash: Optional[str],
        confidence: int,
        signal_scores: Dict[str, int],
        intermediate_profile: Optional[Dict[str, Any]] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send whale one-hop detection alert.

        Args:
            whale_address: Whale address
            intermediate_address: Intermediate address
            exchange_address: Exchange address (if detected)
            whale_amount_eth: Amount sent by whale
            exchange_amount_eth: Amount sent to exchange (if detected)
            whale_tx_hash: Whale transaction hash
            exchange_tx_hash: Exchange transaction hash (if detected)
            confidence: Overall confidence score (0-100)
            signal_scores: Individual signal scores
            intermediate_profile: Intermediate address profile
            additional_data: Additional data

        Returns:
            bool: True if sent successfully
        """
        try:
            additional_data = additional_data or {}
            exchange_name = additional_data.get('exchange_name', 'Unknown Exchange')
            whale_amount_usd = additional_data.get('whale_amount_usd', 0)
            time_delay_minutes = additional_data.get('time_delay_minutes', 0)
            current_price = additional_data.get('current_price')

            # Confidence emoji
            if confidence >= 90:
                confidence_emoji = "🔴"
            elif confidence >= 75:
                confidence_emoji = "🟠"
            elif confidence >= 60:
                confidence_emoji = "🟡"
            else:
                confidence_emoji = "🟢"

            message = f"""
🔍 **WHALE → UNKNOWN → EXCHANGE**

{confidence_emoji} **Confidence:** {confidence}%

🐋 **Whale:** `{whale_address[:10]}...{whale_address[-8:]}`

**Step 1: Whale → Intermediate**
💰 {whale_amount_eth:.4f} ETH (${whale_amount_usd:,.0f})
📍 **Intermediate:** `{intermediate_address[:10]}...{intermediate_address[-8:]}`
"""

            # Add intermediate profile info
            if intermediate_profile:
                profile_type = intermediate_profile.get('profile_type', 'unknown')
                message += f"🎯 **Profile:** {profile_type.replace('_', ' ').title()}\n"

            if exchange_address and exchange_amount_eth:
                exchange_amount_usd = additional_data.get('exchange_amount_usd', 0)
                message += f"""
**Step 2: Intermediate → Exchange**
💱 **Exchange:** {exchange_name}
💰 {exchange_amount_eth:.4f} ETH (${exchange_amount_usd:,.0f})
⏱️ **Time delay:** {time_delay_minutes:.0f} minutes
"""
            else:
                message += "\n**Step 2:** ⏳ Monitoring for exchange transfer...\n"

            # Add signal scores
            message += "\n**Signal Analysis:**\n"
            for signal_name, score in signal_scores.items():
                if score is not None:
                    signal_emoji = "✅" if score >= 70 else "⚠️" if score >= 50 else "❌"
                    message += f"{signal_emoji} {signal_name.replace('_', ' ').title()}: {score}%\n"

            if current_price:
                message += f"\n💹 **Price:** ${current_price:,.2f}\n"

            message += f"""
🚨 **HIDDEN DUMP DETECTED!**

🔗 [View Whale TX](https://etherscan.io/tx/{whale_tx_hash})
"""

            if exchange_tx_hash:
                message += f"🔗 [View Exchange TX](https://etherscan.io/tx/{exchange_tx_hash})\n"

            message += f"🕐 **Detected:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            return await self.send_message(message)

        except Exception as e:
            self.logger.error(f"Error sending one-hop alert: {e}")
            return False

    async def send_statistical_alert(
        self,
        alert_type: str,
        title: str,
        details: Dict[str, Any],
        severity: str = 'medium'
    ) -> bool:
        """
        Send statistical anomaly alert.

        Args:
            alert_type: Type of alert
            title: Alert title
            details: Alert details
            severity: Severity level

        Returns:
            bool: True if sent successfully
        """
        try:
            # Severity emoji
            severity_emojis = {
                'low': '🟢',
                'medium': '🟡',
                'high': '🟠',
                'critical': '🔴'
            }
            emoji = severity_emojis.get(severity, '⚡')

            message = f"{emoji} **{title}**\n\n"

            # Add details
            for key, value in details.items():
                formatted_key = key.replace('_', ' ').title()
                if isinstance(value, float):
                    message += f"• **{formatted_key}:** {value:.2f}\n"
                elif isinstance(value, int):
                    message += f"• **{formatted_key}:** {value:,}\n"
                else:
                    message += f"• **{formatted_key}:** {value}\n"

            message += f"\n🕐 **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            return await self.send_message(message)

        except Exception as e:
            self.logger.error(f"Error sending statistical alert: {e}")
            return False

    async def send_daily_report(
        self,
        date: datetime,
        stats: Dict[str, Any]
    ) -> bool:
        """
        Send daily report with statistics.

        Args:
            date: Report date
            stats: Statistics dictionary

        Returns:
            bool: True if sent successfully
        """
        try:
            message = f"""
📊 **DAILY WHALE TRACKER REPORT**
📅 {date.strftime('%Y-%m-%d')}

**Detection Summary:**
• Total Detections: {stats.get('total_detections', 0):,}
• Direct Transfers: {stats.get('direct_transfers', 0):,}
• One-Hop Detections: {stats.get('onehop_detections', 0):,}
• High Confidence (≥80%): {stats.get('high_confidence', 0):,}

**Volume:**
• Total Volume: {stats.get('total_volume_eth', 0):.2f} ETH
• Total USD Value: ${stats.get('total_volume_usd', 0):,.0f}
• Average Transaction: {stats.get('avg_transaction_eth', 0):.2f} ETH

**Top Whales:**
"""

            top_whales = stats.get('top_whales', [])
            for i, whale in enumerate(top_whales[:5], 1):
                address = whale.get('address', '')
                count = whale.get('count', 0)
                volume = whale.get('volume_eth', 0)
                message += f"{i}. `{address[:10]}...` - {count} txs, {volume:.2f} ETH\n"

            message += f"\n🕐 **Report Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            return await self.send_message(message)

        except Exception as e:
            self.logger.error(f"Error sending daily report: {e}")
            return False
