"""
Hourly Snapshot Job - Save whale balances every hour

Runs every hour to capture current state of top 1000 whale balances.
Enables historical analysis without archive node.

GEMINI: "Snapshot system is industry standard for avoiding expensive archive nodes"
"""

import logging
from typing import List
from datetime import datetime, timezone
from decimal import Decimal

from src.data.whale_list_provider import WhaleListProvider
from src.data.multicall_client import MulticallClient
from src.repositories.snapshot_repository import SnapshotRepository
from src.schemas.snapshot_schemas import WhaleBalanceSnapshotCreate


class SnapshotJob:
    """
    Hourly job to save whale balance snapshots.
    
    Purpose: Create hourly snapshots of top whale balances to enable
    historical comparison without archive node access.
    
    Usage:
        job = SnapshotJob(whale_provider, multicall_client, snapshot_repo)
        await job.run_hourly_snapshot()
    """
    
    def __init__(
        self,
        whale_provider: WhaleListProvider,
        multicall_client: MulticallClient,
        snapshot_repo: SnapshotRepository,
        whale_limit: int = 1000,
        network: str = "ethereum"
    ):
        """
        Initialize SnapshotJob.
        
        Args:
            whale_provider: WhaleListProvider for getting current top whales
            multicall_client: MulticallClient for getting current balances
            snapshot_repo: SnapshotRepository for saving snapshots
            whale_limit: Number of top whales to snapshot (default: 1000)
            network: Network name (default: "ethereum")
        """
        self.logger = logging.getLogger(__name__)
        self.whale_provider = whale_provider
        self.multicall_client = multicall_client
        self.snapshot_repo = snapshot_repo
        self.whale_limit = whale_limit
        self.network = network
        
        self.logger.info(
            f"SnapshotJob initialized: {whale_limit} whales, {network} network"
        )
    
    async def run_hourly_snapshot(self) -> int:
        """
        Save current balances for top whales.
        
        Steps:
        1. Get current top whales from WhaleListProvider
        2. Get current block number
        3. Save snapshots to database
        
        Returns:
            int: Number of snapshots saved
        
        Raises:
            ValueError: If no whales found
            Exception: If save operation fails
        
        Example:
            >>> job = SnapshotJob(...)
            >>> saved_count = await job.run_hourly_snapshot()
            >>> print(f"Saved {saved_count} snapshots")
        """
        self.logger.info("🕐 Starting hourly snapshot job...")
        
        try:
            # Step 1: Get current top whales
            self.logger.info(f"Step 1: Fetching top {self.whale_limit} whales...")
            whales = await self.whale_provider.get_top_whales(
                limit=self.whale_limit,
                network=self.network
            )
            
            if not whales:
                raise ValueError(
                    f"No whales found for {self.network} - cannot create snapshots"
                )
            
            self.logger.info(f"Found {len(whales)} whales")
            
            # Step 2: Get current block number
            self.logger.info("Step 2: Getting current block number...")
            current_block = await self.multicall_client.get_latest_block(self.network)
            self.logger.info(f"Current block: {current_block}")
            
            # Step 3: Create snapshot objects
            self.logger.info("Step 3: Creating snapshot objects...")
            now = datetime.now(timezone.utc)
            
            snapshots: List[WhaleBalanceSnapshotCreate] = []
            
            for whale in whales:
                # CRITICAL: Skip whales with None balance (RPC error)
                if whale['balance_wei'] is None:
                    self.logger.warning(
                        f"❌ Skipping {whale['address']} - RPC error (None balance)"
                    )
                    continue
                
                # Convert balance to Decimal for ETH
                balance_eth = Decimal(str(whale['balance_wei'])) / Decimal('1e18')
                
                snapshot = WhaleBalanceSnapshotCreate(
                    address=whale['address'],
                    balance_wei=str(whale['balance_wei']),
                    balance_eth=balance_eth,
                    block_number=current_block,
                    snapshot_timestamp=now,
                    network=self.network
                )
                snapshots.append(snapshot)
            
            self.logger.info(f"Created {len(snapshots)} snapshot objects")
            
            # Step 4: Save to database (batch)
            self.logger.info("Step 4: Saving snapshots to database...")
            saved_count = await self.snapshot_repo.save_snapshots_batch(snapshots)
            
            self.logger.info(
                f"✅ Hourly snapshot complete: "
                f"{saved_count} snapshots saved @ {now} (block {current_block})"
            )
            
            return saved_count
            
        except Exception as e:
            self.logger.error(f"❌ Hourly snapshot job FAILED: {e}", exc_info=True)
            raise
    
    async def health_check(self) -> dict:
        """
        Check if SnapshotJob is working properly.
        
        Returns:
            dict: Health status
        """
        try:
            # Check whale provider
            whale_health = await self.whale_provider.health_check()
            if whale_health["status"] != "healthy":
                return {
                    "status": "unhealthy",
                    "error": "WhaleListProvider unhealthy",
                    "details": whale_health
                }
            
            # Check multicall client
            multicall_health = await self.multicall_client.health_check()
            if multicall_health["status"] != "healthy":
                return {
                    "status": "unhealthy",
                    "error": "MulticallClient unhealthy",
                    "details": multicall_health
                }
            
            # Check if snapshots exist in DB
            latest_snapshot_time = await self.snapshot_repo.get_latest_snapshot_time(
                network=self.network
            )
            
            return {
                "status": "healthy",
                "whale_provider": "ok",
                "multicall_client": "ok",
                "snapshot_repo": "ok",
                "whale_limit": self.whale_limit,
                "network": self.network,
                "latest_snapshot": (
                    latest_snapshot_time.isoformat() 
                    if latest_snapshot_time 
                    else "No snapshots yet"
                )
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Example usage:
# from src.jobs.snapshot_job import SnapshotJob
# 
# job = SnapshotJob(whale_provider, multicall_client, snapshot_repo)
# await job.run_hourly_snapshot()
