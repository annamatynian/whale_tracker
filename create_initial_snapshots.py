"""
Create initial whale balance snapshots

Run this script to populate snapshot table with current balances.
This enables historical comparison in accumulation score calculator.

Usage:
    python create_initial_snapshots.py
"""

import asyncio
import logging
import os
from datetime import datetime, UTC
from decimal import Decimal

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.core.web3_manager import Web3Manager
from src.data.multicall_client import MulticallClient
from src.data.whale_list_provider import WhaleListProvider
from src.repositories.snapshot_repository import SnapshotRepository
from src.schemas.snapshot_schemas import WhaleBalanceSnapshotCreate


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def create_snapshots():
    """Create snapshots for current top whales."""
    
    logger.info("=" * 70)
    logger.info("🔧 CREATING INITIAL WHALE BALANCE SNAPSHOTS")
    logger.info("=" * 70)
    
    # Initialize components
    logger.info("\n📊 Step 1: Initializing components...")
    
    web3_manager = Web3Manager()
    await web3_manager.initialize()
    
    multicall = MulticallClient(web3_manager)
    
    whale_provider = WhaleListProvider(
        multicall_client=multicall,
        min_balance_eth=1000.0  # Same as main script
    )
    
    # Create database session
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'whale_tracker')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', 'Jayaasiri2185')
    
    db_url = f'postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        snapshot_repo = SnapshotRepository(session)
        
        # Get current top whales
        logger.info("\n🐋 Step 2: Fetching top whales...")
        whales = await whale_provider.get_top_whales(limit=20, network="ethereum")
        
        if not whales:
            logger.error("❌ No whales found!")
            return
        
        logger.info(f"✅ Found {len(whales)} whales")
        
        # Get current balances
        logger.info("\n💰 Step 3: Fetching current balances...")
        addresses = [w['address'] for w in whales]
        balances = await multicall.get_balances_batch(addresses, network="ethereum")
        
        # Get current block
        current_block = await multicall.get_latest_block("ethereum")
        timestamp = datetime.now(UTC)
        
        logger.info(f"✅ Block: {current_block}, Time: {timestamp}")
        
        # Create snapshots
        logger.info("\n💾 Step 4: Creating snapshots...")
        created_count = 0
        
        for address, balance_wei in balances.items():
            balance_eth = Decimal(str(balance_wei)) / Decimal('1e18')
            
            try:
                # Create Pydantic schema object
                snapshot_data = WhaleBalanceSnapshotCreate(
                    address=address,
                    balance_wei=str(balance_wei),
                    balance_eth=balance_eth,
                    block_number=current_block,
                    snapshot_timestamp=timestamp,
                    network="ethereum"
                )
                
                # Save to database
                await snapshot_repo.save_snapshot(snapshot_data)
                created_count += 1
                logger.info(
                    f"  ✅ {address[:10]}... → {balance_eth:,.2f} ETH"
                )
            
            except Exception as e:
                logger.error(f"  ❌ Failed {address[:10]}...: {e}")
        
        logger.info(f"\n✅ Created {created_count}/{len(balances)} snapshots")
        
        # Commit
        await session.commit()
        logger.info("✅ Committed to database")
    
    logger.info("\n" + "=" * 70)
    logger.info("🎉 SNAPSHOT CREATION COMPLETE")
    logger.info("=" * 70)
    logger.info("\n💡 Now you can run: python run_collective_analysis.py")


if __name__ == "__main__":
    asyncio.run(create_snapshots())
