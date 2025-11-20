#!/usr/bin/env python3
"""
LP Health Monitoring Agent
=========================

Основной агент для мониторинга LP позиций в реальном времени.
Объединяет все компоненты системы в единый workflow.

Author: Generated for DeFi-RAG Project
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.web3_utils import Web3Manager
from src.defi_utils import DeFiAnalyzer
from src.data_analyzer import ImpermanentLossCalculator
from src.price_strategy_manager import get_price_manager
from src.gas_cost_calculator import GasCostCalculator
from src.position_manager import PositionManager
from src.notification_manager import TelegramNotifier
from config.settings import Settings
from src.utils import log_startup, log_error, log_success, log_warning, log_info


class LPHealthMonitor:
    """
    Главный агент для мониторинга LP позиций.
    """
    
    def __init__(self):
        """Initialize LP Health Monitor."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.settings = Settings()
        self.web3_manager = Web3Manager()
        self.defi_analyzer = DeFiAnalyzer()
        self.price_manager = get_price_manager()
        self.il_calculator = ImpermanentLossCalculator()
        self.position_manager = PositionManager()
        self.notifier = TelegramNotifier()
        
        # Gas cost calculator (will be initialized after web3_manager)
        self.gas_calculator = None
        
        # State
        self.is_running = False
        self.last_check_time = None
        
    async def initialize(self) -> bool:
        """
        Initialize all components.
        
        Returns:
            bool: True if initialization successful
        """
        try:
            self.logger.info(log_startup("Initializing LP Health Monitor..."))
            
           
            # Initialize Web3
            if not await self.web3_manager.initialize():
                self.logger.error(log_error("Failed to initialize Web3"))
                return False
            
            # Set Web3 manager for DeFi analyzer
            self.defi_analyzer.set_web3_manager(self.web3_manager)
            
            # Initialize Gas Cost Calculator
            self.gas_calculator = GasCostCalculator(self.web3_manager)
            self.logger.info(log_success("Gas Cost Calculator initialized"))
            
            # Test Telegram connection
            if not await self.notifier.test_connection():
                self.logger.error(log_error("Failed to connect to Telegram"))
                return False
            
            # Load positions
            positions = self.position_manager.load_positions()
            if not positions:
                self.logger.warning(log_warning("No positions configured"))
                return False
            
            self.logger.info(log_success(f"Loaded {len(positions)} position(s)"))
            
            # Send startup notification
            await self._send_startup_notification()
            
            self.logger.info(log_success("LP Health Monitor initialized successfully"))
            return True
            
        except Exception as e:
            self.logger.error(log_error(f"Initialization failed: {e}"))
            return False
    
    async def start_monitoring(self):
        """Start the main monitoring loop."""
        if self.is_running:
            self.logger.warning("Monitor is already running")
            return
        
        self.is_running = True
        self.logger.info(log_info("Starting position monitoring..."))
        
        try:
            while self.is_running:
                await self._monitoring_cycle()
                await asyncio.sleep(self.settings.CHECK_INTERVAL_MINUTES * 60)
                
        except asyncio.CancelledError:
            self.logger.info(log_info("Monitoring cancelled"))
        except Exception as e:
            self.logger.error(log_error(f"Monitoring error: {e}"))
            await self._send_error_notification(e)
        finally:
            self.is_running = False
    
    async def stop_monitoring(self):
        """Stop the monitoring loop."""
        self.logger.info(log_info("Stopping monitoring..."))
        self.is_running = False
        await self._send_shutdown_notification()
    
    async def _monitoring_cycle(self):
        """Execute one monitoring cycle."""
        self.logger.info("🔄 Starting monitoring cycle...")
        self.last_check_time = datetime.now()
        
        # Load current positions
        positions = self.position_manager.load_positions()
        active_positions = [p for p in positions if p.get('active', True)]
        
        # Update gas costs for all positions (periodic)
        updated_positions = await self._update_gas_costs(positions)
        
        # Filter active positions from updated list
        active_positions = [p for p in updated_positions if p.get('active', True)]
        
        self.logger.info(f"📊 Checking {len(active_positions)} active position(s)")
        
        # Check each position
        alerts = []
        for position in active_positions:
            try:
                alert = await self._check_position(position)
                if alert:
                    alerts.append(alert)
            except Exception as e:
                self.logger.error(f"Error checking position {position.get('name', 'Unknown')}: {e}")
                continue
        
        # Send alerts if any
        if alerts:
            await self._send_alerts(alerts)
        
        self.logger.info(f"✅ Monitoring cycle completed. Found {len(alerts)} alert(s)")
    
    async def _check_position(self, position: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check a single position for alerts.
        
        Args:
            position: Position configuration
            
        Returns:
            Optional[Dict]: Alert data if alert triggered
        """
        try:
            position_name = position.get('name', 'Unknown Position')
            pair_address = position.get('pair_address')
            
            if not pair_address:
                self.logger.error(f"No pair address for position {position_name}")
                return None
            
            self.logger.debug(f"Checking position: {position_name}")
            
            # Get current pool data
            pool_data = await self.defi_analyzer.get_uniswap_v2_reserves(pair_address)
            if not pool_data:
                self.logger.error(f"Failed to get pool data for {position_name}")
                return None
            
            # Get current prices
            token_a_symbol = position.get('token_a_symbol', 'TokenA')
            token_b_symbol = position.get('token_b_symbol', 'TokenB')
            
            prices = await self.price_manager.get_multiple_prices_async([token_a_symbol, token_b_symbol])
            current_price_a = prices.get(token_a_symbol) or position.get('initial_price_a_usd', 0)
            current_price_b = prices.get(token_b_symbol) or position.get('initial_price_b_usd', 1)
            
            if current_price_a <= 0 or current_price_b <= 0:
                self.logger.warning(f"Invalid prices for {position_name}: A=${current_price_a}, B=${current_price_b}")
                return None
            
            # Calculate IL
            initial_price_ratio = position.get('initial_price_a_usd', 0) / position.get('initial_price_b_usd', 1)
            current_price_ratio = current_price_a / current_price_b
            
            il_percentage = self.il_calculator.calculate_impermanent_loss(
                initial_price_ratio, current_price_ratio
            )
            
            # Check if alert threshold exceeded
            il_threshold = position.get('il_alert_threshold', self.settings.DEFAULT_IL_THRESHOLD)
            
            if abs(il_percentage / 100) >= il_threshold:
                return {
                    'type': 'il_alert',
                    'position': position,
                    'pool_data': pool_data,
                    'current_prices': {'token_a': current_price_a, 'token_b': current_price_b},
                    'il_percentage': il_percentage,
                    'threshold': il_threshold,
                    'timestamp': datetime.now().isoformat()
                }
            
            # Log status for active monitoring
            self.logger.debug(f"{position_name}: IL {il_percentage:.4f}% (threshold: {il_threshold:.1%})")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking position: {e}")
            return None
    
    async def _send_alerts(self, alerts: List[Dict[str, Any]]):
        """Send alerts via Telegram."""
        try:
            for alert in alerts:
                message = self._format_alert_message(alert)
                success = await self.notifier.send_message(message)
                
                if success:
                    self.logger.info(f"✅ Alert sent for {alert['position']['name']}")
                else:
                    self.logger.error(f"❌ Failed to send alert for {alert['position']['name']}")
                    
        except Exception as e:
            self.logger.error(f"Error sending alerts: {e}")
    
    def _format_alert_message(self, alert: Dict[str, Any]) -> str:
        """Format alert message for Telegram."""
        position = alert['position']
        il_percentage = alert['il_percentage']
        threshold = alert['threshold']
        current_prices = alert['current_prices']
        
        # Determine alert severity
        severity_emoji = "🔴" if abs(il_percentage / 100) >= threshold * 2 else "🟡"
        
        message = f"""
{severity_emoji} IMPERMANENT LOSS ALERT

📊 Position: {position['name']}
📉 Current IL: {il_percentage:.4f}%
⚠️ Threshold: {threshold:.1%}
🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Current Analysis:
💰 {position['token_a_symbol']}: ${current_prices['token_a']:,.2f}
💰 {position['token_b_symbol']}: ${current_prices['token_b']:,.4f}

📈 Initial Prices:
• {position['token_a_symbol']}: ${position.get('initial_price_a_usd', 0):,.2f}
• {position['token_b_symbol']}: ${position.get('initial_price_b_usd', 0):,.4f}

🎯 Recommendation: Consider reviewing your LP position
        """.strip()
        
        return message
    
    async def _send_startup_notification(self):
        """Send startup notification."""
        positions = self.position_manager.load_positions()
        active_count = len([p for p in positions if p.get('active', True)])
        
        message = f"""
🚀 LP Health Tracker STARTED

📊 Monitoring {active_count} active position(s)
🕐 Check interval: {self.settings.CHECK_INTERVAL_MINUTES} minutes
🌐 Network: {self.settings.DEFAULT_NETWORK}

✅ All systems operational
        """.strip()
        
        await self.notifier.send_message(message)
    
    async def _send_shutdown_notification(self):
        """Send shutdown notification."""
        message = f"""
🔴 LP Health Tracker STOPPED

🕐 Last check: {self.last_check_time.strftime('%H:%M:%S') if self.last_check_time else 'N/A'}
👋 Monitor has been shut down
        """.strip()
        
        await self.notifier.send_message(message)
    
    async def _send_error_notification(self, error: Exception):
        """Send error notification."""
        message = f"""
⚠️ LP HEALTH TRACKER ERROR

💥 Error: {str(error)[:200]}
🕐 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🔧 Agent will attempt to restart
        """.strip()
        
        try:
            await self.notifier.send_message(message)
        except:
            self.logger.error("Failed to send error notification")
    
    async def get_status_report(self) -> Dict[str, Any]:
        """Get current status report."""
        positions = self.position_manager.load_positions()
        network_info = self.web3_manager.get_network_info()
        
        return {
            'is_running': self.is_running,
            'last_check': self.last_check_time.isoformat() if self.last_check_time else None,
            'positions_count': len(positions),
            'active_positions': len([p for p in positions if p.get('active', True)]),
            'network': network_info.get('name', 'Unknown'),
            'check_interval_minutes': self.settings.CHECK_INTERVAL_MINUTES
        }
    
    async def manual_check(self, position_name: Optional[str] = None):
        """
        Perform manual check of positions.
        
        Args:
            position_name: Optional specific position to check
        """
        positions = self.position_manager.load_positions()
        
        if position_name:
            # Check specific position
            target_positions = [p for p in positions if p.get('name') == position_name]
            if not target_positions:
                self.logger.error(f"Position '{position_name}' not found")
                return
            positions = target_positions
        
        self.logger.info(f"🔍 Manual check of {len(positions)} position(s)")
        
        alerts = []
        for position in positions:
            if not position.get('active', True):
                continue
                
            alert = await self._check_position(position)
            if alert:
                alerts.append(alert)
        
        # Send results
        if alerts:
            await self._send_alerts(alerts)
            self.logger.info(f"✅ Manual check completed: {len(alerts)} alert(s) sent")
        else:
            message = f"""
✅ MANUAL CHECK COMPLETED

📊 Checked {len(positions)} position(s)
🎯 No alerts triggered
🕐 Time: {datetime.now().strftime('%H:%M:%S')}

All positions within thresholds ✅
            """.strip()
            
            await self.notifier.send_message(message)
            self.logger.info("✅ Manual check completed: No alerts")
    
    async def _update_gas_costs(self, positions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Update gas costs for positions (with intelligent scheduling).
        
        Args:
            positions: List of position dictionaries
            
        Returns:
            List[Dict]: Updated positions with current gas costs
        """
        try:
            if not self.gas_calculator:
                self.logger.warning("Gas calculator not initialized, skipping gas cost update")
                return positions
            
            # Check if gas cost update is needed
            if not self._should_update_gas_costs():
                self.logger.debug("Gas costs update not needed at this time")
                return positions
            
            self.logger.info("💰 Updating gas costs for all positions...")
            
            # Update gas costs using the calculator
            updated_positions = await self.gas_calculator.update_all_positions_gas_costs(positions)
            
            # Save updated positions back to position manager
            success = self.position_manager.save_positions(updated_positions)
            
            if success:
                # Generate summary
                summary = self.gas_calculator.get_gas_cost_summary(updated_positions)
                
                self.logger.info(
                    f"💰 Gas costs updated: {summary.get('calculated_positions', 0)}/{summary.get('total_positions', 0)} " +
                    f"calculated, total: ${summary.get('total_gas_costs_usd', 0):.2f}"
                )
                
                # Send notification if significant changes
                await self._send_gas_cost_notification(summary)
                
                # Update last gas update timestamp
                self._last_gas_update = datetime.now()
                
            else:
                self.logger.error("Failed to save updated positions with gas costs")
            
            return updated_positions
            
        except Exception as e:
            self.logger.error(f"Error updating gas costs: {e}")
            return positions
    
    def _should_update_gas_costs(self) -> bool:
        """
        Determine if gas costs should be updated.
        
        Returns:
            bool: True if gas costs should be updated
        """
        try:
            # Check if we have a last update timestamp
            if not hasattr(self, '_last_gas_update'):
                self._last_gas_update = None
            
            # Always update on first run
            if self._last_gas_update is None:
                return True
            
            # Update gas costs daily (configurable)
            gas_update_interval_hours = getattr(self.settings, 'GAS_UPDATE_INTERVAL_HOURS', 24)
            time_since_update = datetime.now() - self._last_gas_update
            
            should_update = time_since_update.total_seconds() >= (gas_update_interval_hours * 3600)
            
            if should_update:
                self.logger.debug(f"Gas cost update needed: {time_since_update.total_seconds()/3600:.1f} hours since last update")
            
            return should_update
            
        except Exception as e:
            self.logger.error(f"Error checking gas update schedule: {e}")
            return False
    
    async def _send_gas_cost_notification(self, summary: Dict[str, Any]):
        """
        Send notification about gas cost updates.
        
        Args:
            summary: Gas cost summary from calculator
        """
        try:
            # Only send notification if significant updates were made
            calculated_count = summary.get('calculated_positions', 0)
            total_count = summary.get('total_positions', 0)
            
            if calculated_count == 0:
                return
            
            total_gas = summary.get('total_gas_costs_usd', 0)
            calculated_gas = summary.get('calculated_gas_costs_usd', 0)
            
            message = f"""
💰 GAS COSTS UPDATED

📊 Updated {calculated_count}/{total_count} position(s)
💸 Total gas costs: ${total_gas:.2f}
🔍 Real calculations: ${calculated_gas:.2f}
⏰ Updated: {datetime.now().strftime('%H:%M:%S')}

✅ Gas tracking active
            """.strip()
            
            await self.notifier.send_message(message)
            
        except Exception as e:
            self.logger.error(f"Error sending gas cost notification: {e}")


# Global monitor instance
monitor_instance = None

async def get_monitor() -> LPHealthMonitor:
    """Get or create monitor instance."""
    global monitor_instance
    if monitor_instance is None:
        monitor_instance = LPHealthMonitor()
        await monitor_instance.initialize()
    return monitor_instance
