#!/usr/bin/env python3
"""
Crypto Multi-Agent Analysis System - Main Entry Point
====================================================

This is the main launcher for the crypto multi-agent system.
Implements the Konenkov strategy through specialized AI agents.

Usage:
    python main.py                    # Start the system
    python main.py --config-check     # Test configuration
    python main.py --dry-run          # Run without real alerts
    python main.py --test-mode        # Use mock data

Author: Crypto Multi-Agent Team
"""

import asyncio
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import configuration first
from config.settings import Settings, setup_logging, get_settings
from config.validation import validate_environment

# Import agents and orchestrator
from agents.orchestrator.simple_orchestrator import SimpleOrchestrator
# 2. Импортируем настройки и логгер
from tools.notifications.telegram_notifier import TelegramNotifier


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Crypto Multi-Agent Analysis System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py                    # Start normal operation
    python main.py --config-check     # Validate configuration
    python main.py --dry-run          # Test mode without alerts
    python main.py --test-mode        # Use mock data
        """
    )
    
    parser.add_argument(
        "--config-check",
        action="store_true",
        help="Validate configuration and exit"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true", 
        help="Run system without sending real alerts or making real API calls"
    )
    
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Use mock data instead of real API calls"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level"
    )
    
    parser.add_argument(
        "--config-file",
        type=str,
        default=".env",
        help="Path to configuration file"
    )
    
    return parser.parse_args()


async def check_configuration(settings: Settings) -> bool:
    """
    Validate system configuration and dependencies.
    
    Returns:
        bool: True if configuration is valid
    """
    logger = logging.getLogger(__name__)
    
    print("🔍 Checking Crypto Multi-Agent System Configuration...")
    print("=" * 60)
    
    # Check environment variables
    validation_errors = validate_environment()
    if validation_errors:
        print("❌ Configuration Errors:")
        for error in validation_errors:
            print(f"   • {error}")
        return False
    
    print("✅ Environment variables: OK")
    
    # Test API connections
    try:
        # Test Telegram connection
        telegram = TelegramNotifier()
        telegram_ok = await telegram.test_connection()
        print(f"{'✅' if telegram_ok else '❌'} Telegram Bot: {'OK' if telegram_ok else 'FAILED'}")
        
        # Test blockchain connections
        try:
            from tools.blockchain.rpc_manager import RPCManager
            rpc_manager = RPCManager()
            # RPCManager already initializes connections, just check if it exists
            rpc_ok = hasattr(rpc_manager, 'providers') and len(rpc_manager.providers) > 0
            print(f"{'✅' if rpc_ok else '❌'} Blockchain RPC: {'OK' if rpc_ok else 'FAILED'}")
        except Exception as e:
            print(f"⚠️ Blockchain RPC: Cannot test ({str(e)[:50]}...)")
            rpc_ok = True  # Don't fail config check on this
        
        # Test market data APIs - simplified check
        try:
            from tools.market_data.coingecko_client import CoinGeckoClient
            cg_client = CoinGeckoClient()
            print(f"✅ Market Data APIs: CoinGecko client initialized")
        except Exception as e:
            print(f"⚠️ Market Data APIs: {str(e)[:50]}...")
        
    except Exception as e:
        logger.error(f"Configuration check failed: {e}")
        print(f"❌ System check failed: {e}")
        return False
    
    print("\n🎯 System Configuration Summary:")
    print(f"   • Environment: {settings.ENV}")
    print(f"   • Log Level: {settings.LOG_LEVEL}")
    print(f"   • Dry Run: {settings.DRY_RUN}")
    print(f"   • Test Mode: {settings.TEST_MODE}")
    print(f"   • USDT Dominance Threshold: {settings.USDT_DOMINANCE_THRESHOLD}%")
    print(f"   • Discovery Check Interval: {settings.DISCOVERY_CHECK_INTERVAL}s")
    
    return True


async def initialize_system(settings: Settings) -> SimpleOrchestrator:
    """
    Initialize the multi-agent system.
    
    Args:
        settings: Application settings
        
    Returns:
        MainOrchestrator: Initialized orchestrator
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Initializing Crypto Multi-Agent System...")
        
        # Initialize orchestrator
        orchestrator = SimpleOrchestrator()
        
        # Initialize all agents
        #await orchestrator.initialize()
        
        logger.info("System initialization completed successfully")
        return orchestrator
        
    except Exception as e:
        logger.error(f"System initialization failed: {e}")
        raise


async def run_system(orchestrator: SimpleOrchestrator) -> None:
    """
    Run the main system loop with continuous monitoring.
    
    Args:
        orchestrator: Initialized orchestrator
    """
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("🚀 Starting Crypto Multi-Agent Analysis System...")
        
        # Send startup notification
        try:
            from tools.notifications.telegram_notifier import TelegramNotifier
            telegram = TelegramNotifier()
            await telegram.send_notification(
                "🚀 Crypto Multi-Agent System Started",
                "System is now monitoring blockchain networks for pump opportunities."
            )
            logger.info("✅ Startup notification sent")
        except Exception as e:
            logger.warning(f"⚠️ Could not send startup notification: {e}")
        
        # Get monitoring interval from settings (default 1 hour)
        from config.settings import get_settings
        settings = get_settings()
        interval = settings.DISCOVERY_CHECK_INTERVAL  # seconds
        
        logger.info(f"🔄 Starting continuous monitoring (interval: {interval}s / {interval//60}min)")
        
        cycle_count = 0
        
        # Main monitoring loop
        while True:
            cycle_count += 1
            cycle_start_time = asyncio.get_event_loop().time()
            
            logger.info(f"\n{'='*80}")
            logger.info(f"🔄 MONITORING CYCLE #{cycle_count} STARTED")
            logger.info(f"{'='*80}")
            
            try:
                # Run analysis pipeline
                alerts = await orchestrator.run_analysis_pipeline()
                
                # Log cycle results
                cycle_duration = asyncio.get_event_loop().time() - cycle_start_time
                logger.info(f"\n📊 CYCLE #{cycle_count} COMPLETED:")
                logger.info(f"   ⏱️ Duration: {cycle_duration:.1f}s")
                logger.info(f"   🚨 Alerts generated: {len(alerts)}")
                
                # Send summary notification if there were alerts
                if alerts:
                    try:
                        telegram = TelegramNotifier()
                        summary_text = f"Cycle #{cycle_count} completed: {len(alerts)} alerts generated"
                        await telegram.send_notification(
                            f"📊 Analysis Cycle Complete",
                            summary_text
                        )
                    except Exception as e:
                        logger.warning(f"Could not send cycle summary: {e}")
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring cycle #{cycle_count}: {e}")
                # Don't break the loop on errors, just log and continue
            
            logger.info(f"\n⏳ Waiting {interval}s until next cycle...")
            logger.info(f"   Next cycle at: {asyncio.get_event_loop().time() + interval:.0f}")
            
            # Wait for next cycle
            await asyncio.sleep(interval)
        
    except KeyboardInterrupt:
        logger.info("\n👋 Received shutdown signal (Ctrl+C)")
        print("\n👋 Shutting down Crypto Multi-Agent System...")
        
        # Send shutdown notification
        try:
            telegram = TelegramNotifier()
            await telegram.send_notification(
                "🛑 System Shutdown",
                f"Crypto Multi-Agent System stopped after {cycle_count} monitoring cycles."
            )
        except Exception as e:
            logger.warning(f"Could not send shutdown notification: {e}")
        
    except Exception as e:
        logger.error(f"💥 Fatal system error: {e}")
        print(f"\n💥 Fatal error: {e}")
        
        # Send error notification
        try:
            telegram = TelegramNotifier()
            await telegram.send_notification(
                "💥 System Error",
                f"Fatal error occurred: {str(e)[:200]}..."
            )
        except:
            pass
        
    finally:
        # Cleanup
        logger.info("🔄 System shutdown completed")


async def main() -> int:
    """
    Main entry point.
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    args = parse_arguments()
    
    try:
        # Load settings
        settings = Settings(config_file=args.config_file)
        
        # Override settings from command line
        if args.dry_run:
            settings.DRY_RUN = True
        if args.test_mode:
            settings.TEST_MODE = True
        if args.log_level:
            settings.LOG_LEVEL = args.log_level
            
        # Setup logging
        setup_logging(settings)
        logger = logging.getLogger(__name__)
        
        # Configuration check mode
        if args.config_check:
            config_ok = await check_configuration(settings)
            if config_ok:
                print("\n🎉 Configuration is valid! Ready to start the system.")
                print("Run 'python main.py' to begin crypto analysis.")
                return 0
            else:
                print("\n❌ Please fix configuration errors before starting.")
                return 1
        
        # Normal operation mode
        logger.info("Starting Crypto Multi-Agent Analysis System")
        
        # Initialize system
        orchestrator = await initialize_system(settings)
        
        # Run system
        await run_system(orchestrator)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n👋 Shutdown requested by user")
        return 0
        
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    # Run the system
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
