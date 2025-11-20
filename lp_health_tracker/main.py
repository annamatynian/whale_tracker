#!/usr/bin/env python3
"""
LP Health Tracker - Main Application
===================================

Main entry point for the LP Health Tracker monitoring system.
Integrates all components into a unified monitoring agent.

Author: Generated for DeFi-RAG Project
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Optional

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.lp_monitor_agent import LPHealthMonitor
from config.settings import Settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/lp_tracker.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Global monitor instance
monitor: Optional[LPHealthMonitor] = None

def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        if monitor and monitor.is_running:
            asyncio.create_task(monitor.stop_monitoring())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main application entry point."""
    global monitor
    
    logger.info("Starting LP Health Tracker")
    logger.info("=" * 40)
    
    try:
        # Initialize monitor
        monitor = LPHealthMonitor()
        
        # Setup signal handlers
        setup_signal_handlers()
        
        # Initialize all components
        success = await monitor.initialize()
        if not success:
            logger.error("Failed to initialize monitor")
            return 1
        
        # Start monitoring
        logger.info("Starting position monitoring loop...")
        await monitor.start_monitoring()
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    finally:
        if monitor:
            await monitor.stop_monitoring()
        logger.info("LP Health Tracker stopped")
    
    return 0

if __name__ == "__main__":
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("Warning: .env file not found!")
        print("Please copy .env.example to .env and configure your settings.")
        print("\nExample:")
        print("   cp .env.example .env")
        print("   # Then edit .env with your API keys")
        sys.exit(1)
    
    # Check if positions are configured
    positions_file = Path("data/positions.json")
    if not positions_file.exists():
        print("Warning: No positions configured!")
        print("Please create positions.json from the example:")
        print("\nExample:")
        print("   cp data/positions.json.example data/positions.json")
        print("   # Then edit data/positions.json with your LP positions")
        print("\nOr use:")
        print("   python run.py --add-position")
        sys.exit(1)
    
    # Run the main application
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Startup error: {e}")
        sys.exit(1)
