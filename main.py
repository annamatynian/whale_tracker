"""
Whale Tracker - Main Orchestrator
==================================

This is the MAIN ENTRY POINT for the Whale Tracker application.

Responsibilities:
- Initialize all components (Web3, Config, Analyzer, Notifier, Watcher)
- Schedule periodic monitoring jobs using APScheduler
- Handle graceful shutdown
- Manage logging and error handling
- Provide CLI interface for manual runs

Author: Whale Tracker Project
"""

import asyncio
import logging
import sys
import signal
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config.settings import Settings
from src.core.web3_manager import Web3Manager
from src.core.whale_config import WhaleConfig
from src.analyzers.whale_analyzer import WhaleAnalyzer
from src.notifications.telegram_notifier import TelegramNotifier
from src.monitors.simple_whale_watcher import SimpleWhaleWatcher


# Setup logging
def setup_logging(settings: Settings) -> None:
    """
    Configure logging based on settings.

    Args:
        settings: Configuration settings
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format
    )

    # File logging if enabled
    if settings.LOG_TO_FILE:
        from logging.handlers import RotatingFileHandler
        import os

        # Create logs directory if needed
        logs_dir = 'logs'
        os.makedirs(logs_dir, exist_ok=True)

        # Rotating file handler
        file_handler = RotatingFileHandler(
            f'{logs_dir}/whale_tracker.log',
            maxBytes=10_000_000,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(log_format, date_format))

        logging.getLogger().addHandler(file_handler)

    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")
    logger.info(f"Log level: {settings.LOG_LEVEL}")
    logger.info(f"File logging: {settings.LOG_TO_FILE}")


class WhaleTrackerOrchestrator:
    """
    Main orchestrator for Whale Tracker application.

    Manages:
    - Component initialization
    - Scheduled monitoring jobs
    - Graceful shutdown
    - Error handling
    """

    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize orchestrator.

        Args:
            settings: Configuration settings (optional, will load if None)
        """
        self.logger = logging.getLogger(__name__)
        self.settings = settings or Settings()

        # Setup logging
        setup_logging(self.settings)

        # Components (initialized in setup())
        self.web3_manager: Optional[Web3Manager] = None
        self.whale_config: Optional[WhaleConfig] = None
        self.analyzer: Optional[WhaleAnalyzer] = None
        self.notifier: Optional[TelegramNotifier] = None
        self.watcher: Optional[SimpleWhaleWatcher] = None

        # Scheduler
        self.scheduler: Optional[AsyncIOScheduler] = None

        # Shutdown flag
        self.shutdown_requested = False

        self.logger.info("WhaleTrackerOrchestrator initialized")

    def setup(self) -> None:
        """
        Initialize all components.

        This method creates instances of all required components:
        - Web3Manager for blockchain interaction
        - WhaleConfig for address classification
        - WhaleAnalyzer for statistical analysis
        - TelegramNotifier for alerts
        - SimpleWhaleWatcher for monitoring
        """
        try:
            self.logger.info("Setting up components...")

            # Initialize Web3Manager
            self.logger.info("Initializing Web3Manager...")
            mock_mode = self.settings.development.mock_data
            self.web3_manager = Web3Manager(mock_mode=mock_mode)
            self.logger.info(f"Web3Manager initialized (mock_mode={mock_mode})")

            # Initialize WhaleConfig
            self.logger.info("Initializing WhaleConfig...")
            self.whale_config = WhaleConfig()
            self.logger.info(f"WhaleConfig initialized ({len(self.whale_config.all_addresses)} known addresses)")

            # Initialize WhaleAnalyzer
            self.logger.info("Initializing WhaleAnalyzer...")
            self.analyzer = WhaleAnalyzer(
                anomaly_multiplier=self.settings.whale_monitoring.thresholds.anomaly_multiplier,
                rolling_window_size=10,
                min_history_required=5
            )
            self.logger.info("WhaleAnalyzer initialized")

            # Initialize TelegramNotifier
            self.logger.info("Initializing TelegramNotifier...")
            self.notifier = TelegramNotifier()
            self.logger.info("TelegramNotifier initialized")

            # Initialize SimpleWhaleWatcher
            self.logger.info("Initializing SimpleWhaleWatcher...")
            self.watcher = SimpleWhaleWatcher(
                web3_manager=self.web3_manager,
                whale_config=self.whale_config,
                analyzer=self.analyzer,
                notifier=self.notifier,
                settings=self.settings
            )
            self.logger.info("SimpleWhaleWatcher initialized")

            # Log configuration
            whale_count = len(self.settings.WHALE_ADDRESSES)
            check_interval = self.settings.CHECK_INTERVAL_MINUTES
            self.logger.info(f"Monitoring {whale_count} whales every {check_interval} minutes")
            self.logger.info(f"Minimum alert threshold: ${self.settings.MIN_AMOUNT_USD:,.0f}")

            self.logger.info("All components initialized successfully!")

        except Exception as e:
            self.logger.error(f"Error during setup: {str(e)}")
            raise

    async def run_monitoring_cycle(self) -> None:
        """
        Run a single monitoring cycle.

        This is the main monitoring job that gets scheduled.
        It checks all configured whales and generates alerts.
        """
        try:
            self.logger.info("=" * 80)
            self.logger.info(f"Starting monitoring cycle at {datetime.now()}")
            self.logger.info("=" * 80)

            if not self.watcher:
                self.logger.error("Watcher not initialized! Run setup() first.")
                return

            # Check if any whales configured
            if not self.settings.WHALE_ADDRESSES:
                self.logger.warning("No whale addresses configured - nothing to monitor")
                return

            # Run monitoring
            result = await self.watcher.monitor_all_whales()

            # Log results
            self.logger.info("-" * 80)
            self.logger.info(f"Monitoring cycle completed:")
            self.logger.info(f"  Status: {result.get('status', 'unknown')}")
            self.logger.info(f"  Whales checked: {result.get('whales_checked', 0)}")
            self.logger.info(f"  Total alerts: {result.get('total_alerts', 0)}")
            self.logger.info("-" * 80)

            # Detailed results
            if self.settings.LOG_LEVEL == 'DEBUG':
                for i, whale_result in enumerate(result.get('results', [])):
                    self.logger.debug(f"Whale {i+1}: {whale_result}")

        except Exception as e:
            self.logger.error(f"Error in monitoring cycle: {str(e)}")
            self.logger.exception("Full traceback:")

    def setup_scheduler(self) -> None:
        """
        Setup APScheduler for periodic monitoring.

        Schedules:
        - Periodic whale monitoring every CHECK_INTERVAL_MINUTES
        """
        try:
            self.logger.info("Setting up scheduler...")

            # Create scheduler
            self.scheduler = AsyncIOScheduler()

            # Add monitoring job
            check_interval_minutes = self.settings.CHECK_INTERVAL_MINUTES

            self.scheduler.add_job(
                self.run_monitoring_cycle,
                trigger=IntervalTrigger(minutes=check_interval_minutes),
                id='whale_monitoring',
                name='Whale Monitoring Cycle',
                max_instances=1,  # Only one instance at a time
                replace_existing=True
            )

            self.logger.info(f"Scheduled monitoring job: every {check_interval_minutes} minutes")
            self.logger.info("Scheduler setup complete")

        except Exception as e:
            self.logger.error(f"Error setting up scheduler: {str(e)}")
            raise

    def start(self) -> None:
        """
        Start the scheduler.

        This begins the periodic monitoring cycles.
        """
        if not self.scheduler:
            raise RuntimeError("Scheduler not initialized! Run setup_scheduler() first.")

        try:
            self.logger.info("Starting scheduler...")
            self.scheduler.start()
            self.logger.info("Scheduler started successfully!")
            self.logger.info("Whale Tracker is now running...")

        except Exception as e:
            self.logger.error(f"Error starting scheduler: {str(e)}")
            raise

    async def run_once(self) -> None:
        """
        Run a single monitoring cycle without scheduling.

        Useful for:
        - Testing
        - Manual runs
        - One-off checks
        """
        self.logger.info("Running single monitoring cycle...")
        await self.run_monitoring_cycle()
        self.logger.info("Single cycle complete")

    def stop(self) -> None:
        """
        Stop the scheduler gracefully.
        """
        if self.scheduler and self.scheduler.running:
            self.logger.info("Stopping scheduler...")
            self.scheduler.shutdown(wait=True)
            self.logger.info("Scheduler stopped")

        self.shutdown_requested = True
        self.logger.info("Orchestrator stopped")

    def signal_handler(self, signum, frame):
        """
        Handle shutdown signals (SIGINT, SIGTERM).

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        sig_name = signal.Signals(signum).name
        self.logger.info(f"Received signal {sig_name} - initiating graceful shutdown...")
        self.stop()


async def main_async():
    """
    Async main function.

    Creates orchestrator, sets up components, and runs monitoring.
    """
    # Create orchestrator
    orchestrator = WhaleTrackerOrchestrator()

    # Setup signal handlers
    signal.signal(signal.SIGINT, orchestrator.signal_handler)
    signal.signal(signal.SIGTERM, orchestrator.signal_handler)

    try:
        # Initialize components
        orchestrator.setup()

        # Check if running in test mode
        if '--once' in sys.argv:
            # Run once and exit (for testing)
            orchestrator.logger.info("Running in '--once' mode (single cycle then exit)")
            await orchestrator.run_once()
            return

        # Setup and start scheduler
        orchestrator.setup_scheduler()
        orchestrator.start()

        # Run first cycle immediately
        orchestrator.logger.info("Running initial monitoring cycle...")
        await orchestrator.run_monitoring_cycle()

        # Keep running until shutdown
        while not orchestrator.shutdown_requested:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        orchestrator.logger.info("Keyboard interrupt received")
    except Exception as e:
        orchestrator.logger.error(f"Fatal error: {str(e)}")
        orchestrator.logger.exception("Full traceback:")
        raise
    finally:
        orchestrator.stop()


def main():
    """
    Main entry point.

    Runs the async event loop.
    """
    print("=" * 80)
    print("Whale Tracker - Cryptocurrency Whale Monitoring System")
    print("=" * 80)
    print()

    try:
        # Run async main
        asyncio.run(main_async())

    except KeyboardInterrupt:
        print("\nShutdown complete. Goodbye!")
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
