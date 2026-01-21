"""
Manual Snapshot Runner - Run snapshot job once manually

Usage:
    python run_manual_snapshot.py

This script:
1. Connects to database
2. Initializes WhaleListProvider and MulticallClient
3. Runs SnapshotJob once
4. Saves top 1000 whale balances to DB

Used for:
- Testing snapshot system
- Manual snapshot creation
- Initial data population
"""

import asyncio
import logging
from datetime import datetime, timezone

from config.settings import Settings
from models.db_connection import DatabaseConfig, AsyncDatabaseManager
from src.data.whale_list_provider import WhaleListProvider
from src.data.multicall_client import MulticallClient
from src.repositories.snapshot_repository import SnapshotRepository
from src.jobs.snapshot_job import SnapshotJob


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """
    Run snapshot job once manually.
    """
    logger.info("=" * 80)
    logger.info("MANUAL SNAPSHOT RUNNER")
    logger.info("=" * 80)
    
    try:
        # Load settings
        logger.info("Loading settings...")
        settings = Settings()
        
        # Setup database
        logger.info("Connecting to database...")
        db_config = DatabaseConfig(
            host=settings.database.db_host,
            port=settings.database.db_port,
            database=settings.database.db_name,
            user=settings.database.db_user,
            password=settings.database.db_password,
            pool_size=settings.database.db_pool_size,
            max_overflow=settings.database.db_max_overflow,
            echo=settings.database.db_echo
        )
        db_manager = AsyncDatabaseManager(config=db_config)
        
        # Test connection
        async with db_manager.session() as session:
            logger.info("✅ Database connection successful")
        
        # Initialize components
        logger.info("Initializing components...")
        
        # Get RPC URL
        rpc_url = settings.get_rpc_url(network="ethereum_mainnet")
        logger.info(f"Using RPC: {rpc_url[:50]}...")
        
        # Web3Manager
        from src.core.web3_manager import Web3Manager
        web3_manager = Web3Manager(mock_mode=False)
        
        # Initialize Web3 connection
        await web3_manager.initialize()
        logger.info("✅ Web3Manager initialized")
        
        # MulticallClient (uses web3_manager)
        multicall_client = MulticallClient(web3_manager=web3_manager)
        logger.info("✅ MulticallClient initialized")
        
        # WhaleListProvider (uses multicall_client)
        whale_provider = WhaleListProvider(
            multicall_client=multicall_client,
            min_balance_eth=1000
        )
        logger.info("✅ WhaleListProvider initialized")
        
        # Get async session for SnapshotRepository
        async with db_manager.session() as session:
            # SnapshotRepository
            snapshot_repo = SnapshotRepository(session=session)
            logger.info("✅ SnapshotRepository initialized")
            
            # Create SnapshotJob
            snapshot_job = SnapshotJob(
                whale_provider=whale_provider,
                multicall_client=multicall_client,
                snapshot_repo=snapshot_repo,
                whale_limit=1000,
                network="ethereum"
            )
            logger.info("✅ SnapshotJob initialized")
            
            # Run snapshot
            logger.info("")
            logger.info("🚀 Starting snapshot job...")
            logger.info("")
            
            start_time = datetime.now(timezone.utc)
            saved_count = await snapshot_job.run_hourly_snapshot()
            end_time = datetime.now(timezone.utc)
            
            duration = (end_time - start_time).total_seconds()
            
            logger.info("")
            logger.info("=" * 80)
            logger.info("✅ SNAPSHOT COMPLETE")
            logger.info("=" * 80)
            logger.info(f"Snapshots saved: {saved_count}")
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info(f"Timestamp: {start_time.isoformat()}")
            logger.info("=" * 80)
            
            # Verify in database
            logger.info("")
            logger.info("Verifying data in database...")
            latest_time = await snapshot_repo.get_latest_snapshot_time(network="ethereum")
            
            if latest_time:
                logger.info(f"✅ Latest snapshot time: {latest_time.isoformat()}")
                
                # Get summary
                summary = await snapshot_repo.get_summary(
                    timestamp=latest_time,
                    network="ethereum"
                )
                
                if summary:
                    logger.info(f"✅ Total snapshots: {summary.total_snapshots}")
                    logger.info(f"✅ Unique addresses: {summary.total_addresses}")
                    logger.info(f"✅ Total ETH: {summary.total_balance_eth:,.2f}")
                    logger.info(f"✅ Avg balance: {summary.avg_balance_eth:,.2f} ETH")
            else:
                logger.warning("⚠️ No snapshots found in database")
        
        logger.info("")
        logger.info("Done! ✅")
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
