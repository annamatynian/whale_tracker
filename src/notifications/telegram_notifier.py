"""
Telegram Notifier - Whale Tracker Alert System
===============================================

This module handles all notifications:
- Telegram bot integration
- Whale transaction alerts
- One-hop detection alerts
- Statistical anomaly alerts
- Daily reports

Adapted from: lp_health_tracker/src/notification_manager.py
Enhanced for: Whale Tracker Project

Author: Whale Tracker Project
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import aiohttp
import json


class TelegramNotifier:
    """
    Handles Telegram notifications for the LP Health Tracker.
    """
    
    def __init__(self):
        """Initialize Telegram Notifier."""
        self.logger = logging.getLogger(__name__)
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
    
    async def test_connection(self) -> bool:
        """
        Test Telegram bot connection.
        
        Returns:
            bool: True if connection successful
        """
        try:
            if not self.bot_token or not self.chat_id:
                self.logger.error("Telegram bot token or chat ID not configured")
                return False
            
            # Test by getting bot info
            url = f"{self.base_url}/getMe"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()
            
            # data уже получена выше
            
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
        parse_mode: str = 'Markdown',
        disable_notification: bool = False
    ) -> bool:
        """
        Send message to Telegram.
        
        Args:
            message: Message text
            parse_mode: 'Markdown' or 'HTML'
            disable_notification: Silent notification
            
        Returns:
            bool: True if sent successfully
        """
        try:
            url = f"{self.base_url}/sendMessage"
            
            payload = {
                'chat_id': int(self.chat_id),
                'text': message,
                'disable_notification': disable_notification
            }
            
            # Only add parse_mode if it's not None
            if parse_mode:
                payload['parse_mode'] = parse_mode
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=payload, timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()
            
            # data уже получена выше
            
            if data.get('ok'):
                self.logger.debug("Telegram message sent successfully")
                return True
            else:
                self.logger.error(f"Telegram send error: {data}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending Telegram message: {e}")
            return False
    
    async def send_il_alert(
        self, 
        position_name: str, 
        current_il: float, 
        threshold: float,
        position_data: Dict[str, Any]
    ) -> bool:
        """
        Send Impermanent Loss alert.
        
        Args:
            position_name: Position name
            current_il: Current IL percentage
            threshold: Alert threshold
            position_data: Position analysis data
            
        Returns:
            bool: True if sent successfully
        """
        try:
            # Format IL values
            il_formatted = f"{current_il:.2%}"
            threshold_formatted = f"{threshold:.2%}"
            
            # Determine severity emoji
            severity_emoji = self._get_severity_emoji(abs(current_il))
            
            message = f"""
{severity_emoji} **IMPERMANENT LOSS ALERT**

📊 **Position:** {position_name}
📉 **Current IL:** {il_formatted}
⚠️ **Threshold:** {threshold_formatted}
🕐 **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Current Analysis:**
"""
            
            # Add position details if available
            if 'lp_strategy' in position_data:
                lp_data = position_data['lp_strategy']
                current_value = lp_data.get('current_value_usd', 0)
                pnl = lp_data.get('pnl_usd', 0)
                
                message += f"💰 Current Value: ${current_value:.2f}\n"
                message += f"📈 P&L: ${pnl:.2f} ({pnl/current_value*100:.1f}%)\n"
            
            if 'better_strategy' in position_data:
                better = position_data['better_strategy']
                message += f"🎯 Better Strategy: {better}\n"
            
            message += f"\n🔗 [View Position Details](https://etherscan.io)"
            
            return await self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending IL alert: {e}")
            return False
    
    async def send_daily_report(self, positions: List[Dict[str, Any]]) -> bool:
        """
        Send daily summary report.
        
        Args:
            positions: List of position analysis data
            
        Returns:
            bool: True if sent successfully
        """
        try:
            if not positions:
                message = "📊 **Daily LP Health Report**\n\n❌ No positions to track"
                return await self.send_message(message)
            
            # Calculate summary statistics
            total_positions = len(positions)
            total_value = sum(p.get('lp_strategy', {}).get('current_value_usd', 0) for p in positions)
            total_il = sum(abs(p.get('impermanent_loss', {}).get('percentage', 0)) for p in positions)
            avg_il = total_il / total_positions if total_positions > 0 else 0
            
            # Count positions by IL severity
            low_il = sum(1 for p in positions if abs(p.get('impermanent_loss', {}).get('percentage', 0)) < 0.02)
            medium_il = sum(1 for p in positions if 0.02 <= abs(p.get('impermanent_loss', {}).get('percentage', 0)) < 0.05)
            high_il = sum(1 for p in positions if abs(p.get('impermanent_loss', {}).get('percentage', 0)) >= 0.05)
            
            message = f"""
📊 **Daily LP Health Report**
🗓️ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📈 **Portfolio Summary:**
• Total Positions: {total_positions}
• Total Value: ${total_value:.2f}
• Average IL: {avg_il:.2%}

🚦 **Risk Distribution:**
• 🟢 Low IL (<2%): {low_il} positions
• 🟡 Medium IL (2-5%): {medium_il} positions  
• 🔴 High IL (>5%): {high_il} positions

📋 **Position Details:**
"""
            
            # Add details for each position
            for i, position in enumerate(positions[:5], 1):  # Limit to first 5
                name = position.get('name', f'Position {i}')
                il = position.get('impermanent_loss', {}).get('percentage', 0)
                value = position.get('lp_strategy', {}).get('current_value_usd', 0)
                
                emoji = self._get_severity_emoji(abs(il))
                message += f"{emoji} **{name}**\n"
                message += f"   IL: {il:.2%} | Value: ${value:.2f}\n"
            
            if len(positions) > 5:
                message += f"\n... and {len(positions) - 5} more positions"
            
            return await self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending daily report: {e}")
            return False
    
    async def send_error_notification(self, error_message: str) -> bool:
        """
        Send error notification.
        
        Args:
            error_message: Error description
            
        Returns:
            bool: True if sent successfully
        """
        try:
            message = f"""
🚨 **LP Tracker Error**

❌ **Error:** {error_message}
🕐 **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Please check the logs for more details.
"""
            
            return await self.send_message(message, disable_notification=True)
            
        except Exception as e:
            self.logger.error(f"Error sending error notification: {e}")
            return False
    
    async def send_startup_notification(self, config: Dict[str, Any]) -> bool:
        """
        Send startup notification.
        
        Args:
            config: Configuration details
            
        Returns:
            bool: True if sent successfully
        """
        try:
            check_interval = config.get('check_interval_minutes', 15)
            network = config.get('network', 'Unknown')
            
            message = f"""
🚀 **LP Health Tracker Started**

✅ Agent is now monitoring your LP positions
🕐 **Start Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔄 **Check Interval:** {check_interval} minutes
🌐 **Network:** {network}

The bot will notify you of any significant IL changes.
"""
            
            return await self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending startup notification: {e}")
            return False
    
    async def send_shutdown_notification(self) -> bool:
        """
        Send shutdown notification.
        
        Returns:
            bool: True if sent successfully
        """
        try:
            message = f"""
🔴 **LP Health Tracker Stopped**

⏹️ Agent has been shut down
🕐 **Stop Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Monitoring has been suspended.
"""
            
            return await self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending shutdown notification: {e}")
            return False
    
    async def send_position_summary(self, position_data: Dict[str, Any]) -> bool:
        """
        Send detailed position summary.
        
        Args:
            position_data: Complete position analysis
            
        Returns:
            bool: True if sent successfully
        """
        try:
            name = position_data.get('name', 'Unknown Position')
            
            # Get strategy data
            hold_data = position_data.get('hold_strategy', {})
            lp_data = position_data.get('lp_strategy', {})
            il_data = position_data.get('impermanent_loss', {})
            
            hold_value = hold_data.get('current_value_usd', 0)
            hold_pnl = hold_data.get('pnl_usd', 0)
            
            lp_value = lp_data.get('current_value_usd', 0)
            lp_pnl = lp_data.get('pnl_usd', 0)
            fees_earned = lp_data.get('fees_earned_usd', 0)
            
            il_percentage = il_data.get('percentage', 0)
            il_usd = il_data.get('usd_amount', 0)
            
            better_strategy = position_data.get('better_strategy', 'Unknown')
            
            message = f"""
📊 **Position Analysis: {name}**

💼 **Hold Strategy:**
• Value: ${hold_value:.2f}
• P&L: ${hold_pnl:.2f} ({hold_pnl/hold_value*100:.1f}%)

🏊 **LP Strategy:**
• Value: ${lp_value:.2f}
• Fees: ${fees_earned:.2f}
• P&L: ${lp_pnl:.2f} ({lp_pnl/lp_value*100:.1f}%)

📉 **Impermanent Loss:**
• Percentage: {il_percentage:.2%}
• USD Amount: ${il_usd:.2f}

🎯 **Better Strategy:** {better_strategy}

🕐 **Updated:** {datetime.now().strftime('%H:%M:%S')}
"""
            
            return await self.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending position summary: {e}")
            return False
    
    def _get_severity_emoji(self, il_abs: float) -> str:
        """
        Get emoji based on IL severity.

        Args:
            il_abs: Absolute IL value

        Returns:
            str: Appropriate emoji
        """
        if il_abs < 0.01:  # < 1%
            return "🟢"
        elif il_abs < 0.02:  # < 2%
            return "🟡"
        elif il_abs < 0.05:  # < 5%
            return "🟠"
        else:  # >= 5%
            return "🔴"

    # ============================================
    # WHALE TRACKER SPECIFIC METHODS
    # ============================================

    async def send_whale_direct_transfer_alert(
        self,
        whale_address: str,
        tx_data: Dict[str, Any],
        destination_info: Dict[str, Any],
        current_price: Optional[float] = None
    ) -> bool:
        """
        Send alert for direct whale → exchange transfer.

        Args:
            whale_address: Whale wallet address
            tx_data: Transaction data
            destination_info: Information about destination (exchange)
            current_price: Current token price (optional)

        Returns:
            bool: True if sent successfully
        """
        try:
            amount_usd = tx_data.get('value_usd', 0)
            exchange_name = destination_info.get('name', 'Unknown Exchange')
            tx_hash = tx_data.get('hash', '')

            message = f"""
🚨 **WHALE → EXCHANGE DIRECT**

🐋 **Whale:** `{whale_address[:10]}...{whale_address[-8:]}`
💰 **Amount:** ${amount_usd:,.0f}
💱 **Exchange:** {exchange_name}
"""

            if current_price:
                message += f"💹 **Price:** ${current_price:,.2f}\n"

            message += f"""
⚠️ **POTENTIAL DUMP SIGNAL**

🔗 [View Transaction](https://etherscan.io/tx/{tx_hash})
🕐 **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

            return await self.send_message(message)

        except Exception as e:
            self.logger.error(f"Error sending direct transfer alert: {e}")
            return False

    async def send_whale_onehop_alert(
        self,
        whale_address: str,
        whale_tx: Dict[str, Any],
        intermediate_address: str,
        onehop_result: Dict[str, Any],
        current_price: Optional[float] = None
    ) -> bool:
        """
        Send alert for one-hop detection (whale → unknown → exchange).

        Args:
            whale_address: Whale wallet address
            whale_tx: Initial whale transaction
            intermediate_address: Intermediate address
            onehop_result: One-hop detection result
            current_price: Current token price (optional)

        Returns:
            bool: True if sent successfully
        """
        try:
            whale_amount = whale_tx.get('value_usd', 0)
            exchange_name = onehop_result.get('exchange_name', 'Unknown Exchange')
            time_delay = onehop_result.get('time_delay_minutes', 0)
            whale_tx_hash = whale_tx.get('hash', '')

            message = f"""
🔍 **WHALE → UNKNOWN → EXCHANGE**

🐋 **Whale:** `{whale_address[:10]}...{whale_address[-8:]}`

**Step 1:**
💰 ${whale_amount:,.0f} → Unknown address
📍 `{intermediate_address[:10]}...{intermediate_address[-8:]}`

**Step 2:**
💱 Found transfer to **{exchange_name}**
⏱️ Time delay: {time_delay:.0f} minutes
"""

            if current_price:
                message += f"💹 **Price:** ${current_price:,.2f}\n"

            message += f"""
🚨 **HIDDEN DUMP DETECTED!**

🔗 [View Whale TX](https://etherscan.io/tx/{whale_tx_hash})
🕐 **Detected:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

            return await self.send_message(message)

        except Exception as e:
            self.logger.error(f"Error sending one-hop alert: {e}")
            return False

    async def send_anomaly_alert(
        self,
        whale_address: str,
        tx_data: Dict[str, Any],
        anomaly_info: Dict[str, Any]
    ) -> bool:
        """
        Send alert for statistical anomaly (unusually large transaction).

        Args:
            whale_address: Whale wallet address
            tx_data: Transaction data
            anomaly_info: Anomaly detection info (avg, threshold, etc.)

        Returns:
            bool: True if sent successfully
        """
        try:
            current_amount = tx_data.get('value_usd', 0)
            avg_amount = anomaly_info.get('average_amount', 0)
            threshold = anomaly_info.get('threshold', 0)
            multiplier = current_amount / avg_amount if avg_amount > 0 else 0

            message = f"""
⚡ **STATISTICAL ANOMALY DETECTED**

🐋 **Whale:** `{whale_address[:10]}...{whale_address[-8:]}`

📊 **Transaction Analysis:**
• Current Amount: ${current_amount:,.0f}
• Average Amount: ${avg_amount:,.0f}
• **{multiplier:.1f}x above average!**

🎯 **This is {multiplier:.1f}x larger than typical transactions from this whale**

🕐 **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

            return await self.send_message(message)

        except Exception as e:
            self.logger.error(f"Error sending anomaly alert: {e}")
            return False


class AlertManager:
    """
    Manages alert rules and notifications.
    """
    
    def __init__(self, notifier: TelegramNotifier):
        """Initialize Alert Manager."""
        self.logger = logging.getLogger(__name__)
        self.notifier = notifier
        self.last_alerts = {}  # Prevent spam
    
    async def check_and_send_alerts(
        self, 
        position_name: str, 
        analysis: Dict[str, Any],
        config: Dict[str, Any]
    ) -> bool:
        """
        Check if any alerts should be triggered and send them.
        
        Args:
            position_name: Position identifier
            analysis: Position analysis data
            config: Position configuration
            
        Returns:
            bool: True if any alerts were sent
        """
        try:
            alerts_sent = False
            
            # Check IL threshold
            il_percentage = analysis.get('impermanent_loss', {}).get('percentage', 0)
            il_threshold = config.get('il_alert_threshold', 0.05)
            
            if abs(il_percentage) > il_threshold:
                # Check if we already sent this alert recently
                alert_key = f"{position_name}_il_{abs(il_percentage):.2f}"
                
                if not self._was_alert_sent_recently(alert_key):
                    await self.notifier.send_il_alert(
                        position_name,
                        il_percentage,
                        il_threshold,
                        analysis
                    )
                    self._mark_alert_sent(alert_key)
                    alerts_sent = True
            
            # Add more alert types here (e.g., large price movements, etc.)
            
            return alerts_sent
            
        except Exception as e:
            self.logger.error(f"Error checking alerts: {e}")
            return False
    
    def _was_alert_sent_recently(self, alert_key: str, cooldown_minutes: int = 60) -> bool:
        """Check if alert was sent recently (to prevent spam)."""
        last_sent = self.last_alerts.get(alert_key)
        
        if not last_sent:
            return False
        
        # Check if cooldown period has passed
        time_diff = datetime.now() - last_sent
        return time_diff.total_seconds() < (cooldown_minutes * 60)
    
    def _mark_alert_sent(self, alert_key: str) -> None:
        """Mark alert as sent."""
        self.last_alerts[alert_key] = datetime.now()

        # Clean up old alerts (keep only last 24 hours)
        cutoff = datetime.now() - timedelta(hours=24)

        self.last_alerts = {
            k: v for k, v in self.last_alerts.items()
            if v > cutoff
        }


# Message formatting utilities
class MessageFormatter:
    """
    Utilities for formatting messages.
    """
    
    @staticmethod
    def format_currency(amount: float) -> str:
        """Format currency amount."""
        if abs(amount) >= 1000000:
            return f"${amount/1000000:.2f}M"
        elif abs(amount) >= 1000:
            return f"${amount/1000:.1f}K"
        else:
            return f"${amount:.2f}"
    
    @staticmethod
    def format_percentage(value: float) -> str:
        """Format percentage with appropriate precision."""
        if abs(value) < 0.01:
            return f"{value:.3%}"
        else:
            return f"{value:.2%}"
    
    @staticmethod
    def format_change(current: float, previous: float) -> str:
        """Format change with arrow indicator."""
        if previous == 0:
            return "N/A"
        
        change = (current - previous) / previous
        arrow = "📈" if change > 0 else "📉" if change < 0 else "➡️"
        
        return f"{arrow} {change:.2%}"
