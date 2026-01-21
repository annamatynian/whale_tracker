"""
Whale Balance Snapshot Repository

Manages hourly balance snapshots for historical analysis without archive nodes.

GEMINI: "Snapshot system is industry standard for avoiding expensive archive nodes"
"""

import logging
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import WhaleBalanceSnapshot
from src.schemas.snapshot_schemas import (
    WhaleBalanceSnapshotCreate,
    SnapshotQuery,
    SnapshotSummary
)
from src.exceptions import StaleSnapshotError, InsufficientSnapshotCoverageError


class SnapshotRepository:
    """
    Repository for whale balance snapshots.
    
    Purpose: Store and retrieve hourly snapshots to enable historical
    balance comparisons without requiring archive node access.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize SnapshotRepository.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
        self.logger = logging.getLogger(__name__)
    
    async def save_snapshot(
        self,
        snapshot: WhaleBalanceSnapshotCreate
    ) -> WhaleBalanceSnapshot:
        """
        Save a single balance snapshot.
        
        Args:
            snapshot: Snapshot data
        
        Returns:
            WhaleBalanceSnapshot: Saved snapshot with ID
        
        Raises:
            IntegrityError: If duplicate snapshot exists
        """
        db_snapshot = WhaleBalanceSnapshot(
            address=snapshot.address,
            balance_wei=snapshot.balance_wei,
            balance_eth=snapshot.balance_eth,
            block_number=snapshot.block_number,
            snapshot_timestamp=snapshot.snapshot_timestamp,
            network=snapshot.network,
            created_at=datetime.now(timezone.utc)
        )
        
        self.session.add(db_snapshot)
        await self.session.commit()
        await self.session.refresh(db_snapshot)
        
        self.logger.debug(
            f"Saved snapshot: {snapshot.address[:10]}... "
            f"@ {snapshot.snapshot_timestamp} = {snapshot.balance_eth:.4f} ETH"
        )
        
        return db_snapshot
    
    async def save_snapshots_batch(
        self,
        snapshots: List[WhaleBalanceSnapshotCreate]
    ) -> int:
        """
        Save multiple snapshots in batch (efficient).
        
        Args:
            snapshots: List of snapshots to save
        
        Returns:
            int: Number of snapshots saved
        
        Note: Ignores duplicates (on conflict do nothing)
        """
        if not snapshots:
            return 0
        
        db_snapshots = [
            WhaleBalanceSnapshot(
                address=s.address,
                balance_wei=s.balance_wei,
                balance_eth=s.balance_eth,
                block_number=s.block_number,
                snapshot_timestamp=s.snapshot_timestamp,
                network=s.network,
                created_at=datetime.now(timezone.utc)
            )
            for s in snapshots
        ]
        
        self.session.add_all(db_snapshots)
        
        try:
            await self.session.commit()
            saved_count = len(db_snapshots)
            
            self.logger.info(
                f"Saved {saved_count} snapshots "
                f"(timestamp: {snapshots[0].snapshot_timestamp})"
            )
            
            return saved_count
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error saving snapshots batch: {e}")
            raise
    
    async def get_snapshot_at_time(
        self,
        address: str,
        timestamp: datetime,
        tolerance_hours: int = 1,
        network: str = "ethereum"
    ) -> Optional[WhaleBalanceSnapshot]:
        """
        Get snapshot closest to target timestamp within tolerance.
        
        Args:
            address: Whale address
            timestamp: Target timestamp
            tolerance_hours: Search window (±hours)
            network: Network name
        
        Returns:
            WhaleBalanceSnapshot or None if not found
        
        Example:
            # Get balance ~24 hours ago (±1 hour tolerance)
            snapshot = await repo.get_snapshot_at_time(
                address="0x123...",
                timestamp=datetime.now(UTC) - timedelta(hours=24),
                tolerance_hours=1
            )
        """
        time_min = timestamp - timedelta(hours=tolerance_hours)
        time_max = timestamp + timedelta(hours=tolerance_hours)
        
        stmt = select(WhaleBalanceSnapshot).where(
            and_(
                WhaleBalanceSnapshot.address == address.lower(),
                WhaleBalanceSnapshot.network == network,
                WhaleBalanceSnapshot.snapshot_timestamp >= time_min,
                WhaleBalanceSnapshot.snapshot_timestamp <= time_max
            )
        ).order_by(
            # Find closest to target timestamp
            func.abs(
                func.extract('epoch', WhaleBalanceSnapshot.snapshot_timestamp) -
                func.extract('epoch', timestamp)
            )
        ).limit(1)
        
        result = await self.session.execute(stmt)
        snapshot = result.scalar_one_or_none()
        
        if snapshot:
            self.logger.debug(
                f"Found snapshot for {address[:10]}... "
                f"at {snapshot.snapshot_timestamp} "
                f"(target: {timestamp})"
            )
        else:
            self.logger.warning(
                f"No snapshot found for {address[:10]}... "
                f"near {timestamp} (±{tolerance_hours}h)"
            )
        
        return snapshot
    
    def _validate_snapshot_freshness(
        self,
        requested_timestamp: datetime,
        found_timestamp: datetime,
        max_drift_pct: float = 10.0
    ) -> None:
        """
        Validate that snapshot is not too old (CRITICAL VULNERABILITY FIX).
        
        WHY: Prevents accumulation score from being calculated over wrong time period.
        
        GEMINI VULNERABILITY:
        - If create_initial_snapshots.py fails for 24h
        - System may return 48h old snapshot within tolerance window
        - Result: Score calculated over 48h instead of 24h → false [High Conviction]
        
        Args:
            requested_timestamp: When we wanted the snapshot
            found_timestamp: When snapshot was actually taken
            max_drift_pct: Max acceptable drift (default: 10%)
        
        Raises:
            StaleSnapshotError: If drift > max_drift_pct
        
        Example:
            Requested: now - 24h
            Found: now - 48h
            Drift: |48h - 24h| / 24h = 24h / 24h = 100%
            → Raises StaleSnapshotError (exceeds 10% threshold)
        """
        # Calculate absolute time difference
        time_diff_seconds = abs((found_timestamp - requested_timestamp).total_seconds())
        
        # Calculate expected lookback period (from now to requested)
        now = datetime.now(timezone.utc)
        lookback_period_seconds = abs((now - requested_timestamp).total_seconds())
        
        # Drift as % of lookback period
        # Example: requested 24h ago, found 48h ago
        # → time_diff = 24h, lookback = 24h → drift = 100%
        drift_pct = (time_diff_seconds / lookback_period_seconds) * 100 if lookback_period_seconds > 0 else 0
        
        if drift_pct >= max_drift_pct:  # ✅ CHANGED: >= instead of > (boundary inclusive)
            raise StaleSnapshotError(
                requested_timestamp=requested_timestamp,
                found_timestamp=found_timestamp,
                max_drift_pct=max_drift_pct,
                actual_drift_pct=drift_pct
            )
        
        self.logger.debug(
            f"Snapshot freshness OK: drift {drift_pct:.1f}% (max: {max_drift_pct}%)"
        )
    
    async def get_snapshots_batch_at_time(
        self,
        addresses: List[str],
        timestamp: datetime,
        tolerance_hours: int = 1,
        network: str = "ethereum",
        max_drift_pct: float = 10.0
    ) -> Dict[str, WhaleBalanceSnapshot]:
        """
        Get snapshots for multiple addresses at once (efficient).
        
        Args:
            addresses: List of whale addresses
            timestamp: Target timestamp
            tolerance_hours: Search window
            network: Network name
            max_drift_pct: Max acceptable timestamp drift (default: 10%)
        
        Returns:
            Dict[address, snapshot] - Only addresses with found snapshots
        
        Raises:
            StaleSnapshotError: If snapshots are too old (VULNERABILITY FIX)
        
        WHY: Much faster than querying one-by-one
        """
        if not addresses:
            return {}
        
        time_min = timestamp - timedelta(hours=tolerance_hours)
        time_max = timestamp + timedelta(hours=tolerance_hours)
        
        # Normalize addresses
        addresses_lower = [addr.lower() for addr in addresses]
        
        stmt = select(WhaleBalanceSnapshot).where(
            and_(
                WhaleBalanceSnapshot.address.in_(addresses_lower),
                WhaleBalanceSnapshot.network == network,
                WhaleBalanceSnapshot.snapshot_timestamp >= time_min,
                WhaleBalanceSnapshot.snapshot_timestamp <= time_max
            )
        )
        
        result = await self.session.execute(stmt)
        all_snapshots = result.scalars().all()
        
        # Group by address, keep closest to target timestamp
        snapshots_by_address: Dict[str, WhaleBalanceSnapshot] = {}
        
        for snapshot in all_snapshots:
            addr = snapshot.address
            
            if addr not in snapshots_by_address:
                snapshots_by_address[addr] = snapshot
            else:
                # Keep snapshot closer to target time
                existing = snapshots_by_address[addr]
                existing_diff = abs((existing.snapshot_timestamp - timestamp).total_seconds())
                new_diff = abs((snapshot.snapshot_timestamp - timestamp).total_seconds())
                
                if new_diff < existing_diff:
                    snapshots_by_address[addr] = snapshot
        
        # ✅ CRITICAL FIX: Validate snapshot freshness (Gemini vulnerability #2)
        if snapshots_by_address:
            # Check the first snapshot as representative (all should be same timestamp)
            first_snapshot = next(iter(snapshots_by_address.values()))
            self._validate_snapshot_freshness(
                requested_timestamp=timestamp,
                found_timestamp=first_snapshot.snapshot_timestamp,
                max_drift_pct=max_drift_pct
            )
        
        self.logger.info(
            f"Found {len(snapshots_by_address)}/{len(addresses)} snapshots "
            f"near {timestamp} (±{tolerance_hours}h)"
        )
        
        return snapshots_by_address
    
    async def get_addresses_in_top_at_time(
        self,
        timestamp: datetime,
        limit: int = 1000,
        tolerance_hours: int = 1,
        network: str = "ethereum"
    ) -> Set[str]:
        """
        Get addresses that were in top N at given timestamp.
        
        WHY: For Survival Bias fix - need to track who WAS in top,
        not just who IS in top now.
        
        GEMINI: "Union (объединение) адресов, которые были в топе 24 часа назад 
        И которые находятся там сейчас"
        
        Args:
            timestamp: Historical timestamp
            limit: Top N addresses
            tolerance_hours: Search window
            network: Network name
        
        Returns:
            Set of addresses that were in top at that time
        """
        time_min = timestamp - timedelta(hours=tolerance_hours)
        time_max = timestamp + timedelta(hours=tolerance_hours)
        
        # Get all snapshots near target time
        stmt = select(WhaleBalanceSnapshot).where(
            and_(
                WhaleBalanceSnapshot.network == network,
                WhaleBalanceSnapshot.snapshot_timestamp >= time_min,
                WhaleBalanceSnapshot.snapshot_timestamp <= time_max
            )
        )
        
        result = await self.session.execute(stmt)
        all_snapshots = result.scalars().all()
        
        # Group by address, keep snapshot closest to target
        best_snapshots: Dict[str, WhaleBalanceSnapshot] = {}
        
        for snapshot in all_snapshots:
            addr = snapshot.address
            
            if addr not in best_snapshots:
                best_snapshots[addr] = snapshot
            else:
                existing = best_snapshots[addr]
                existing_diff = abs((existing.snapshot_timestamp - timestamp).total_seconds())
                new_diff = abs((snapshot.snapshot_timestamp - timestamp).total_seconds())
                
                if new_diff < existing_diff:
                    best_snapshots[addr] = snapshot
        
        # Sort by balance and take top N
        sorted_snapshots = sorted(
            best_snapshots.values(),
            key=lambda s: s.balance_eth,
            reverse=True
        )[:limit]
        
        top_addresses = {s.address for s in sorted_snapshots}
        
        self.logger.info(
            f"Found {len(top_addresses)} addresses in top-{limit} "
            f"at {timestamp} (±{tolerance_hours}h)"
        )
        
        return top_addresses
    
    async def validate_snapshot_density(
        self,
        addresses: List[str],
        lookback_hours: int = 24,
        min_coverage_pct: float = 85.0,
        network: str = "ethereum"
    ) -> tuple[bool, float, int, int]:
        """
        Validate snapshot density (GEMINI FIX #7: "Блокировка прогресса").
        
        WHY: Prevents [High Conviction] on incomplete data after bot downtime.
        
        VULNERABILITY:
        - Bot crashes for 12h → missing 50% of hourly snapshots
        - `get_snapshot_at_time` still finds 24h snapshot (drift OK)
        - But score calculated over INCOMPLETE history → false signal
        
        SOLUTION:
        - Count ACTUAL snapshots vs EXPECTED snapshots
        - If coverage < 85% → raise InsufficientSnapshotCoverageError
        
        Args:
            addresses: List of whale addresses to check
            lookback_hours: Period to validate (default: 24h)
            min_coverage_pct: Minimum required coverage (default: 85%)
            network: Network name
        
        Returns:
            tuple[is_valid, coverage_pct, found_snapshots, expected_snapshots]
        
        Raises:
            InsufficientSnapshotCoverageError: If coverage < min_coverage_pct
        
        Example:
            >>> is_valid, coverage, found, expected = await repo.validate_snapshot_density(
            ...     addresses=whale_addresses,
            ...     lookback_hours=24,
            ...     min_coverage_pct=85.0
            ... )
            >>> print(f"Coverage: {coverage:.1f}% ({found}/{expected} snapshots)")
        """
        if not addresses:
            return True, 100.0, 0, 0
        
        now = datetime.now(timezone.utc)
        time_start = now - timedelta(hours=lookback_hours)
        
        # Expected: 1 snapshot per hour per address
        expected_snapshots = lookback_hours * len(addresses)
        
        # Count ACTUAL snapshots in time range
        stmt = select(func.count(WhaleBalanceSnapshot.id)).where(
            and_(
                WhaleBalanceSnapshot.address.in_([addr.lower() for addr in addresses]),
                WhaleBalanceSnapshot.network == network,
                WhaleBalanceSnapshot.snapshot_timestamp >= time_start,
                WhaleBalanceSnapshot.snapshot_timestamp <= now
            )
        )
        
        result = await self.session.execute(stmt)
        found_snapshots = result.scalar_one()
        
        # Calculate coverage
        coverage_pct = (found_snapshots / expected_snapshots * 100) if expected_snapshots > 0 else 0
        
        # ✅ CRITICAL: Strictly greater than threshold (not >=)
        # WHY: 85% boundary should fail (incomplete data), only >85% passes
        is_valid = coverage_pct > min_coverage_pct
        
        if not is_valid:
            self.logger.error(
                f"❌ INSUFFICIENT SNAPSHOT COVERAGE: {coverage_pct:.1f}% "
                f"({found_snapshots}/{expected_snapshots} snapshots found), "
                f"required {min_coverage_pct}%. "
                f"Likely bot downtime in last {lookback_hours}h!"
            )
            
            raise InsufficientSnapshotCoverageError(
                found_snapshots=found_snapshots,
                expected_snapshots=expected_snapshots,
                coverage_pct=coverage_pct,
                min_coverage_pct=min_coverage_pct,
                lookback_hours=lookback_hours
            )
        
        self.logger.info(
            f"✅ Snapshot density OK: {coverage_pct:.1f}% "
            f"({found_snapshots}/{expected_snapshots} snapshots)"
        )
        
        return is_valid, coverage_pct, found_snapshots, expected_snapshots
    
    async def get_latest_snapshot_time(
        self,
        network: str = "ethereum"
    ) -> Optional[datetime]:
        """
        Get timestamp of most recent snapshot.
        
        Args:
            network: Network name
        
        Returns:
            datetime or None if no snapshots exist
        """
        stmt = select(
            func.max(WhaleBalanceSnapshot.snapshot_timestamp)
        ).where(
            WhaleBalanceSnapshot.network == network
        )
        
        result = await self.session.execute(stmt)
        latest_time = result.scalar_one_or_none()
        
        return latest_time
    
    async def get_summary(
        self,
        timestamp: datetime,
        network: str = "ethereum"
    ) -> Optional[SnapshotSummary]:
        """
        Get summary statistics for snapshots at given time.
        
        Args:
            timestamp: Snapshot timestamp
            network: Network name
        
        Returns:
            SnapshotSummary with aggregate stats
        """
        stmt = select(
            func.count(WhaleBalanceSnapshot.id).label('total'),
            func.count(func.distinct(WhaleBalanceSnapshot.address)).label('unique_addresses'),
            func.sum(WhaleBalanceSnapshot.balance_eth).label('total_balance'),
            func.avg(WhaleBalanceSnapshot.balance_eth).label('avg_balance'),
            func.min(WhaleBalanceSnapshot.balance_eth).label('min_balance'),
            func.max(WhaleBalanceSnapshot.balance_eth).label('max_balance')
        ).where(
            and_(
                WhaleBalanceSnapshot.snapshot_timestamp == timestamp,
                WhaleBalanceSnapshot.network == network
            )
        )
        
        result = await self.session.execute(stmt)
        row = result.one_or_none()
        
        if not row or row.total == 0:
            return None
        
        return SnapshotSummary(
            total_snapshots=row.total,
            total_addresses=row.unique_addresses,
            total_balance_eth=Decimal(str(row.total_balance)),
            avg_balance_eth=Decimal(str(row.avg_balance)),
            min_balance_eth=Decimal(str(row.min_balance)),
            max_balance_eth=Decimal(str(row.max_balance)),
            snapshot_timestamp=timestamp,
            network=network
        )
