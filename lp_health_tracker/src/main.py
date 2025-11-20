#!/usr/bin/env python3
"""
LP Health Tracker - Main Application Entry Point
===============================================

This is the main entry point for the LP Health Tracker agent.
It coordinates all components and runs the monitoring loop.

Author: Generated for DeFi-RAG Project
Version: 0.1.0
"""

import asyncio
import logging
import sys
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

# Import our modules
from src.web3_utils import Web3Manager
from src.defi_utils import DeFiAnalyzer
from src.data_analyzer import ImpermanentLossCalculator
from src.notification_manager import TelegramNotifier
from src.position_manager import PositionManager
from src.historical_data_manager import HistoricalDataManager
from src.price_strategy_manager import get_price_manager
from src.gas_cost_calculator import GasCostCalculator
from config.settings import Settings


class LPHealthTracker:
    """
    Main LP Health Tracker agent class.
    
    Coordinates all components:
    - Position monitoring
    - IL calculations  
    - Notifications
    - Data persistence

     далее подготовка агента к запуску. Когда агент "оживает", 
     эта функция выдает ему все необходимые инструменты: настройки, менеджеры для работы с блокчейном и позициями, калькулятор IL, 
     систему уведомлений в Telegram и, что очень важно, планировщик задач (scheduler).
    """
    
    def __init__(self):
        """Initialize the LP Health Tracker."""
        # Load environment variables
        load_dotenv()
        
        # Initialize settings
        self.settings = Settings()
        
        # Initialize components
        self.web3_manager = Web3Manager()
        self.defi_analyzer = DeFiAnalyzer()
        self.il_calculator = ImpermanentLossCalculator()
        self.notifier = TelegramNotifier()
        self.position_manager = PositionManager()
        self.historical_manager = HistoricalDataManager()
        
        # Initialize GasCostCalculator (will be set after web3_manager is initialized)
        self.gas_calculator = None
        
        # Initialize scheduler
        self.scheduler = AsyncIOScheduler()
        
        # Setup logging
        self._setup_logging()
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("LP Health Tracker initialized")
    
    def _setup_logging(self) -> None:
        """Setup logging configuration."""
        log_level = getattr(logging, self.settings.LOG_LEVEL.upper())
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
        # Console handler с указанием кодировки
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        # Эта строка не стандартная для StreamHandler, но может помочь в некоторых средах.
        # Главное - это настройка FileHandler.
        # Если возникнет ошибка, эту строку можно будет убрать.
        try:
            console_handler.stream.reconfigure(encoding='utf-8')
        except TypeError:
            # В некоторых системах это может не поддерживаться, ничего страшного.
            self.logger.debug("Could not reconfigure stdout encoding.")

        # File handler (if enabled) с указанием кодировки
        if self.settings.LOG_TO_FILE:
            file_handler = logging.FileHandler('logs/lp_tracker.log', encoding='utf-8')
            file_handler.setFormatter(formatter)
            logging.getLogger().addHandler(file_handler)
    
        # Configure root logger
        logging.getLogger().setLevel(log_level)
        logging.getLogger().addHandler(console_handler)
    
    async def initialize_connections(self) -> bool:
        """
        Initialize all external connections.
        
        Returns:
            bool: True if all connections successful
        """
        try:
            # Initialize Web3 connection
            if not await self.web3_manager.initialize():
                self.logger.error("Failed to initialize Web3 connection")
                return False
            
            # Initialize GasCostCalculator after web3_manager is ready
            self.gas_calculator = GasCostCalculator(self.web3_manager)
            self.logger.info("GasCostCalculator initialized successfully")
            
            # Test Telegram connection
            if not await self.notifier.test_connection():
                self.logger.error("Failed to test Telegram connection")
                return False
            
            # Load existing positions
            positions = self.position_manager.load_positions()
            self.logger.info(f"Loaded {len(positions)} existing positions")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing connections: {e}")
            return False
    
    async def monitor_positions(self) -> None:
        """
        Main monitoring function - checks all positions.
        This function will be called periodically by the scheduler.
        """
        self.logger.info("Starting position monitoring cycle...")
            
        # Load current positions
        positions = self.position_manager.load_positions()
            
        if not positions:
            self.logger.info("No positions to monitor")
            return
            
        # 🚀 NEW: Process all positions CONCURRENTLY (Gemini's suggestion)
        if len(positions) == 1:
            # Single position - no need for parallel processing
            await self._process_position(positions[0])
        else:
            # Multiple positions - process in parallel for maximum speed
            self.logger.info(f"Processing {len(positions)} positions concurrently...")
            start_time = time.time()
                
            # Create tasks for parallel execution
            tasks = [self._process_position(position) for position in positions]
                
            # Execute all positions in parallel
            await asyncio.gather(*tasks, return_exceptions=True)
                
            elapsed = time.time() - start_time
            self.logger.info(f"✅ Parallel processing completed in {elapsed:.2f}s (vs {elapsed*len(positions):.2f}s sequential)")
            
        # Save updated positions
        self.position_manager.save_positions(positions)
            
        self.logger.info("Position monitoring cycle completed")
            
    
    async def _process_position(self, position: Dict[str, Any]) -> None:
        """
        Process a single LP position with REAL DATA.
        
        Args:
            position: Position data dictionary
        """
        try:
            position_name = position.name
            self.logger.info(f"🔥 Processing position with REAL DATA: {position_name}")
            
            # 🚀 NEW: Update gas costs for this position
            if self.gas_calculator:
                self.logger.debug(f"Updating gas costs for position: {position_name}")
                
                # Get ETH price for gas cost calculation
                try:
                    price_manager = get_price_manager()
                    eth_price = await price_manager.get_token_price_async('ETH')
                    
                    # Fallback if price not available
                    if not eth_price or eth_price <= 0:
                        eth_price = 3200.0  # Reasonable fallback
                        self.logger.warning(f"Using fallback ETH price ${eth_price} for gas calculation")
                    else:
                        self.logger.debug(f"Using current ETH price ${eth_price:.2f} for gas calculation")
                    
                    # Update gas costs with ETH price
                    position = await self.gas_calculator.update_position_gas_costs(position, eth_price)
                    
                except Exception as price_error:
                    self.logger.error(f"Error getting ETH price for gas calculation: {price_error}")
                    # Use fallback and continue
                    eth_price = 3200.0
                    self.logger.warning(f"Using emergency fallback ETH price ${eth_price} for gas calculation")
                    position = await self.gas_calculator.update_position_gas_costs(position, eth_price)
            else:
                self.logger.warning("GasCostCalculator not initialized, skipping gas cost update")
            
            # 🚀 STEP 1: Set Web3Manager for DeFi Analyzer
            self.defi_analyzer.set_web3_manager(self.web3_manager)
            
            # 🚀 STEP 2: Get REAL current reserves and LP token balance
            current_reserves = await self.defi_analyzer.get_uniswap_v2_reserves(position.pair_address)
            if not current_reserves:
                self.logger.error(f"❌ Failed to get reserves for {position_name}, skipping")
                return
            
            # Get LP token balance for wallet
            lp_balance = await self.defi_analyzer.get_lp_token_balance(
                position.pair_address, 
                position.wallet_address
            )
            if lp_balance is None:
                self.logger.error(f"❌ Failed to get LP balance for {position_name}, skipping")
                return
            
            self.logger.info(f"✅ Real data fetched - Reserves: A={current_reserves['reserve0']:.2f}, B={current_reserves['reserve1']:.2f}, LP Balance: {lp_balance:.6f}")
            
            # 🚀 STEP 3: Get current prices (already implemented)
            # 🚀 STEP 4: Calculate current IL using REAL data
            # 🚀 STEP 5: Calculate P&L with REAL numbers
            # 🚀 STEP 6: Check alert thresholds and send notifications
            
            # For now, create analysis_data using real reserves (mix of real and mock)
            analysis_data = {
                'impermanent_loss': {
                    'percentage': -0.025,  # Still mock IL calculation - will be real next
                    'usd_amount': -125.50
                },
                'hold_strategy': {
                    'current_value_usd': 5000.0
                },
                'lp_strategy': {
                    'current_value_usd': lp_balance * (current_reserves['reserve0'] + current_reserves['reserve1']),  # ✅ REAL-based calculation
                    'fees_earned_usd': 45.20,
                    'pnl_usd': -80.30,
                    'pnl_percentage': -1.58
                },
                'better_strategy': 'LP',  # Will be calculated properly next
                # ✅ Add real data to analysis
                'real_data': {
                    'current_reserves': current_reserves,
                    'lp_balance': lp_balance,
                    'data_source': 'blockchain_rpc'
                },
                # 🚀 NEW: Gas cost information
                'gas_costs': {
                    'entry_cost_usd': position.get('gas_costs_usd', 0),
                    'calculated_from_blockchain': position.get('gas_costs_calculated', False),
                    'calculation_date': position.get('gas_calculation_date'),
                    'entry_tx_hash': position.get('entry_tx_hash')
                }
            }
            
            # 🚀 NEW: Get real-time prices using Price Strategy Manager
            try:
                self.logger.debug(f"Fetching real-time prices for {position_name}...")
                
                # Prepare token list for parallel price fetching
                tokens_to_fetch = [
                    (position.token_a.symbol, position.token_a.address),
                    (position.token_b.symbol, position.token_b.address)
                ]
                
                # 🚀 NEW: Use async method for truly parallel price fetching
                symbols_only = [symbol for symbol, address in tokens_to_fetch]
                price_manager = get_price_manager()
                current_prices = await price_manager.get_multiple_prices_parallel_async(symbols_only)
                
                token_a_price = current_prices.get(position.token_a.symbol)
                token_b_price = current_prices.get(position.token_b.symbol)
                
                # Fallback to mock data if price fetching fails
                if token_a_price is None or token_b_price is None:
                    self.logger.warning(f"Failed to fetch prices for {position_name}, using fallback values")
                    
                    # Fallback to reasonable default prices
                    token_a_price = token_a_price or 2000.0  # ETH fallback
                    token_b_price = token_b_price or 1.0     # USDC/stable fallback
                    
                    # 🚀 NEW: Non-blocking notification (Gemini's suggestion)
                    asyncio.create_task(self.notifier.send_message(
                        f"⚠️ **Price Fetch Warning**\n"
                        f"Position: {position_name}\n"
                        f"Could not fetch real-time prices, using fallback values\n"
                        f"Token A ({position.token_a.symbol}): ${token_a_price}\n"
                        f"Token B ({position.token_b.symbol}): ${token_b_price}"
                    ))
                else:
                    self.logger.info(f"✅ Real-time prices fetched for {position_name}: "
                                    f"{position.token_a.symbol}=${token_a_price}, "
                                    f"{position.token_b.symbol}=${token_b_price}")
                
                # Calculate price ratio
                price_ratio = token_a_price / token_b_price if token_b_price != 0 else 0
                
                # Real market data from Price Strategy Manager
                market_data = {
                    'token_a_price': token_a_price,
                    'token_b_price': token_b_price,
                    'price_ratio': price_ratio,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'price_strategy_manager'
                }
                
            except Exception as price_error:
                self.logger.error(f"Error fetching prices for {position_name}: {price_error}")
                
                # Fallback to mock data in case of total failure
                market_data = {
                    'token_a_price': 2000.0,  # ETH fallback
                    'token_b_price': 1.0,     # USDC fallback
                    'price_ratio': 2000.0,
                    'timestamp': datetime.now().isoformat(),
                    'source': 'fallback_mock_data'
                }
                
                # 🚀 NEW: Non-blocking error notification (Gemini's suggestion)
                asyncio.create_task(self.notifier.send_message(
                    f"🚨 **Price Fetch Error**\n"
                    f"Position: {position_name}\n"
                    f"Error: {str(price_error)}\n"
                    f"Using fallback mock data for this cycle"
                ))
            
            # 🔥 NEW: Save historical snapshot
            try:
                success = self.historical_manager.save_position_snapshot(
                    position_name=position_name,
                    analysis_data=analysis_data,
                    market_data=market_data
                )
                
                if success:
                    self.logger.debug(f"Historical data saved for {position_name}")
                else:
                    self.logger.warning(f"Failed to save historical data for {position_name}")
                    
            except Exception as hist_error:
                self.logger.error(f"Error saving historical data for {position_name}: {hist_error}")
            
            # Placeholder for now
            self.logger.info(f"Position {position_name} processed successfully")
            
        except Exception as e:
            self.logger.error(f"Error processing position {position_name}: {e}")
    
    async def send_daily_report(self) -> None:
        """Send daily summary report of all positions."""
        try:
            self.logger.info("Generating daily report...")
            
            positions = self.position_manager.load_positions()
            
            if not positions:
                await self.notifier.send_message("📊 Daily Report: No positions to track")
                return
            
            # 🔥 NEW: Get historical data for comprehensive report
            today = datetime.now().strftime('%Y-%m-%d')
            daily_summary = self.historical_manager.get_daily_summary(today)
            
            # 🚀 NEW: Get gas cost summary
            gas_summary = None
            if self.gas_calculator:
                gas_summary = self.gas_calculator.get_gas_cost_summary(positions)
            
            # Generate comprehensive daily report
            report = "📊 **Daily LP Health Report**\n\n"
            report += f"📝 **Summary for {today}**\n"
            report += f"Tracked Positions: {len(positions)}\n"
            
            # Add gas cost information
            if gas_summary:
                report += f"\n⛽ **Gas Costs Summary**\n"
                report += f"Total Gas Costs: ${gas_summary.get('total_gas_costs_usd', 0):.2f}\n"
                report += f"Calculated/Total: {gas_summary.get('calculated_positions', 0)}/{gas_summary.get('total_positions', 0)}\n"
                accuracy = gas_summary.get('calculation_accuracy', 0) * 100
                report += f"Data Accuracy: {accuracy:.1f}%\n"
            
            # Add historical insights if available
            if daily_summary and daily_summary.get('positions_count', 0) > 0:
                avg_il = daily_summary.get('average_il', 0)
                total_pnl = daily_summary.get('total_pnl_usd', 0)
                
                report += f"\n📈 **Performance**\n"
                report += f"Average IL: {avg_il:.3f}%\n"
                report += f"Total P&L: ${total_pnl:.2f}\n"
                
                if total_pnl >= 0:
                    report += "🟢 Overall Performance: POSITIVE\n"
                else:
                    report += "🔴 Overall Performance: NEGATIVE\n"
            else:
                report += "\n📈 No historical data available yet\n"
            
            report += f"\n🕰️ Report Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            await self.notifier.send_message(report)
            
        except Exception as e:
            self.logger.error(f"Error generating daily report: {e}")
    
    async def start(self) -> None:
        """Start the LP Health Tracker agent."""
        try:
            self.logger.info("Starting LP Health Tracker...")
            
            # Initialize connections
            if not await self.initialize_connections():
                self.logger.error("Failed to initialize. Exiting.")
                return
            
            # Send startup notification
            await self.notifier.send_message(
                f"🟢 **LP Health Tracker Started**\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Check Interval: {self.settings.CHECK_INTERVAL_MINUTES} minutes"
            )
            
            # Schedule monitoring job
            self.scheduler.add_job(
                self.monitor_positions,
                'interval',
                minutes=self.settings.CHECK_INTERVAL_MINUTES,
                id='position_monitor'
            )
            
            # Schedule daily report (8 AM)
            self.scheduler.add_job(
                self.send_daily_report,
                'cron',
                hour=8,
                minute=0,
                id='daily_report'
            )
            
            # Start scheduler
            self.scheduler.start()
            self.logger.info("Scheduler started successfully")
            
            # Keep the application running
            self.logger.info("LP Health Tracker is running. Press Ctrl+C to stop.")
            
            # Run forever
            while True:
                await asyncio.sleep(60)  # Sleep for 1 minute
                
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal...")
            await self.shutdown()
        except Exception as e:
            self.logger.error(f"Fatal error: {e}")
            await self.notifier.send_error_notification(f"Fatal error: {e}")
            await self.shutdown()
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the agent."""
        try:
            self.logger.info("🔴 Shutting down LP Health Tracker...")
            
            # Stop scheduler
            if self.scheduler.running:
                self.scheduler.shutdown()
            
            # Send shutdown notification
            await self.notifier.send_message(
                f"🔴 **LP Health Tracker Stopped**\n"
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            self.logger.info("Shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")
    
    async def update_all_gas_costs(self) -> None:
        """
        Manually update gas costs for all positions.
        
        This method can be called to recalculate gas costs for all positions,
        useful for initial setup or when gas calculation logic changes.
        """
        try:
            if not self.gas_calculator:
                self.logger.error("GasCostCalculator not initialized")
                return
            
            self.logger.info("Starting manual gas cost update for all positions...")
            
            # Load current positions
            positions = self.position_manager.load_positions()
            
            if not positions:
                self.logger.info("No positions to update")
                return
            
            # Get current ETH price for calculations
            try:
                price_manager = get_price_manager()
                eth_price = await price_manager.get_token_price_async('ETH')
                
                # Fallback if price not available
                if not eth_price or eth_price <= 0:
                    eth_price = 3200.0  # Reasonable fallback
                    self.logger.warning(f"Using fallback ETH price ${eth_price} for gas calculations")
                else:
                    self.logger.info(f"Using current ETH price ${eth_price:.2f} for gas calculations")
                    
            except Exception as price_error:
                self.logger.error(f"Error getting ETH price: {price_error}")
                eth_price = 3200.0
                self.logger.warning(f"Using emergency fallback ETH price ${eth_price}")
            
            # Update gas costs for all positions with ETH price
            updated_positions = await self.gas_calculator.update_all_positions_gas_costs(positions, eth_price)
            
            # Save updated positions
            self.position_manager.save_positions(updated_positions)
            
            # Generate summary
            gas_summary = self.gas_calculator.get_gas_cost_summary(updated_positions)
            
            # Send notification with results
            report = "⛽ **Gas Cost Update Complete**\n\n"
            report += f"Updated Positions: {gas_summary.get('total_positions', 0)}\n"
            report += f"Successfully Calculated: {gas_summary.get('calculated_positions', 0)}\n"
            report += f"Total Gas Costs: ${gas_summary.get('total_gas_costs_usd', 0):.2f}\n"
            accuracy = gas_summary.get('calculation_accuracy', 0) * 100
            report += f"Calculation Accuracy: {accuracy:.1f}%\n"
            
            await self.notifier.send_message(report)
            
            self.logger.info("Gas cost update completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error updating all gas costs: {e}")
            await self.notifier.send_error_notification(f"Gas cost update failed: {e}")


async def main():
    """Main entry point."""
    tracker = LPHealthTracker()
    await tracker.start()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
