"""
Data Quality Validator - Cyberpunk Edition 🔥⚡

Validates data integrity for WhaleBalanceSnapshots and AccumulationMetrics tables.
Detects critical anomalies that could poison collective whale analysis signals.

WHY: Multicall errors, RPC failures, and LST de-pegs create "dirty data" that triggers
     false positives in our whale tracking system. This validator catches corruption BEFORE
     it reaches production alerts.

INSPIRED BY: WHALES_ANALYSIS.docx - Section "Exchange Shuffle & Technical Noise Filtering"
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum

from sqlalchemy import select, func, and_, or_, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import WhaleBalanceSnapshot, AccumulationMetric

# ═══════════════════════════════════════════════════════════════════════════
# CYBERPUNK LOGGING CONFIG 🌆
# ═══════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """System health levels"""
    HEALTHY = "healthy"       # All systems nominal ✅
    DEGRADED = "degraded"     # Minor issues detected ⚠️
    CRITICAL = "critical"     # Major corruption found 🚨


@dataclass
class ValidationResult:
    """Result from a single validation check"""
    check_name: str
    status: HealthStatus
    score: float  # 0-100 (100 = perfect)
    issues: List[str]
    metrics: Dict[str, float]
    timestamp: datetime


class DataQualityValidator:
    """
    High-precision data quality monitor for Whale Tracker.
    
    Validates database integrity across multiple dimensions:
    
    1. DENSITY CHECK: Detects "holes" in hourly snapshot coverage
       - Target: >85% coverage for top-1000 whales in last 24h
       - WHY: Missing snapshots break historical delta calculations
    
    2. PRECISION CHECK: Identifies zero-balance corruption
       - Target: Zero active whales with balance = 0 (RPC error signature)
       - WHY: Multicall failures return 0x0 instead of real balance
    
    3. TIME DRIFT: Validates block timestamp vs snapshot timestamp alignment
       - Target: <10% deviation from expected block time
       - WHY: Stale blocks poison time-series correlation analysis
    
    4. STATISTICAL OUTLIERS: Detects impossible balance spikes
       - Target: <50% hourly change without on-chain transaction proof
       - WHY: Parser bugs or RPC cache corruption create false "whale dumps"
    
    5. LST CONSISTENCY: Validates stETH/ETH rate sanity
       - Target: 0.90 ≤ rate ≤ 1.10 (historical range post-merge)
       - WHY: Rate outside bounds blocks Depeg Risk tag calculation
    
    REFERENCE: AAVE_COMPOUND.docx - "LST-Correction: Mathematical Noise Filtering"
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize validator.
        
        Args:
            session: Active async database session
        """
        self.session = session
        self.results: List[ValidationResult] = []
        
    async def run_all_checks(self) -> Dict[str, any]:
        """
        Execute all validation checks and return health status.
        
        Returns:
            {
                "overall_status": "healthy" | "degraded" | "critical",
                "overall_score": 0-100,
                "checks": [ValidationResult, ...],
                "summary": {
                    "total_issues": int,
                    "critical_issues": int,
                    "warnings": int
                },
                "timestamp": datetime
            }
        """
        logger.info("🔍 INITIATING DATA QUALITY SCAN...")
        logger.info("━" * 60)
        
        # Run all checks SEQUENTIALLY to avoid session conflicts
        # WHY: AsyncSession doesn't support concurrent operations
        self.results.append(await self.check_snapshot_density())
        self.results.append(await self.check_precision_integrity())
        self.results.append(await self.check_time_drift())
        self.results.append(await self.check_statistical_outliers())
        self.results.append(await self.check_lst_consistency())
        
        # Calculate overall health
        overall_status = self._calculate_overall_status()
        overall_score = self._calculate_overall_score()
        
        summary = self._generate_summary()
        
        logger.info("━" * 60)
        logger.info(f"🎯 SCAN COMPLETE - STATUS: {overall_status.value.upper()}")
        logger.info(f"📊 OVERALL SCORE: {overall_score:.1f}/100")
        logger.info(f"⚠️  TOTAL ISSUES: {summary['total_issues']}")
        
        return {
            "overall_status": overall_status.value,
            "overall_score": overall_score,
            "checks": [self._result_to_dict(r) for r in self.results],
            "summary": summary,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def check_snapshot_density(self) -> ValidationResult:
        """
        Validate snapshot coverage density for last 24 hours.
        
        DETECTION: Missing snapshots create "holes" in time-series data.
        
        Algorithm:
        1. Get distinct whale addresses from last 24h
        2. Expected snapshots = whale_count * 24 hours
        3. Actual snapshots = COUNT(*) in time range
        4. Density = actual / expected
        
        THRESHOLD: Density >= 85% = HEALTHY
                   Density 70-85% = DEGRADED
                   Density < 70% = CRITICAL
        
        Returns:
            ValidationResult with density metrics
        """
        logger.info("🔬 CHECK 1/5: Snapshot Density Analysis...")
        
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(hours=24)
        issues = []
        
        try:
            # Get unique whales in last 24h
            unique_whales_query = select(
                func.count(distinct(WhaleBalanceSnapshot.address))
            ).where(
                WhaleBalanceSnapshot.snapshot_timestamp >= start_time
            )
            result = await self.session.execute(unique_whales_query)
            unique_whale_count = result.scalar() or 0
            
            # Get total snapshots
            total_snapshots_query = select(
                func.count(WhaleBalanceSnapshot.id)
            ).where(
                WhaleBalanceSnapshot.snapshot_timestamp >= start_time
            )
            result = await self.session.execute(total_snapshots_query)
            actual_snapshots = result.scalar() or 0
            
            # Calculate expected (24 snapshots per whale)
            expected_snapshots = unique_whale_count * 24
            
            # Calculate density
            if expected_snapshots > 0:
                density_pct = (actual_snapshots / expected_snapshots) * 100
            else:
                density_pct = 0.0
                issues.append("[CRITICAL] No snapshots found in last 24h")
            
            # Determine status
            if density_pct >= 85.0:
                status = HealthStatus.HEALTHY
                score = 100.0
            elif density_pct >= 70.0:
                status = HealthStatus.DEGRADED
                score = 75.0
                issues.append(
                    f"[WARNING] Snapshot coverage at {density_pct:.1f}% "
                    f"(target: 85%+). Missing {expected_snapshots - actual_snapshots} snapshots."
                )
            else:
                status = HealthStatus.CRITICAL
                score = 50.0
                issues.append(
                    f"[CRITICAL] Incomplete Data - Only {density_pct:.1f}% coverage. "
                    f"Expected {expected_snapshots}, got {actual_snapshots}. "
                    f"Historical delta calculations unreliable!"
                )
            
            logger.info(
                f"  ├─ Unique Whales: {unique_whale_count:,}"
            )
            logger.info(
                f"  ├─ Expected Snapshots: {expected_snapshots:,}"
            )
            logger.info(
                f"  ├─ Actual Snapshots: {actual_snapshots:,}"
            )
            logger.info(
                f"  └─ Density: {density_pct:.2f}% [{status.value.upper()}]"
            )
            
            return ValidationResult(
                check_name="snapshot_density",
                status=status,
                score=score,
                issues=issues,
                metrics={
                    "density_pct": density_pct,
                    "unique_whales": unique_whale_count,
                    "expected_snapshots": expected_snapshots,
                    "actual_snapshots": actual_snapshots,
                    "missing_snapshots": max(0, expected_snapshots - actual_snapshots)
                },
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"  └─ ❌ FAILED: {e}")
            return ValidationResult(
                check_name="snapshot_density",
                status=HealthStatus.CRITICAL,
                score=0.0,
                issues=[f"Check failed: {str(e)}"],
                metrics={},
                timestamp=datetime.now(timezone.utc)
            )
    
    async def check_precision_integrity(self) -> ValidationResult:
        """
        Detect zero-balance corruption from RPC failures.
        
        DETECTION: Known whales should NEVER have balance_eth = 0
        
        Root Cause: Multicall failures return 0x0 instead of throwing error.
        This creates "false whale exits" in our accumulation score.
        
        THRESHOLD: 0 zero-balance whales = HEALTHY
                   1-5 zero balances = DEGRADED (recent RPC issues)
                   >5 zero balances = CRITICAL (systemic RPC failure)
        
        Returns:
            ValidationResult with zero-balance detection metrics
        """
        logger.info("🔬 CHECK 2/5: Precision Integrity Validation...")
        
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(hours=24)
        issues = []
        
        try:
            # Find snapshots with zero balance in last 24h
            zero_balance_query = select(
                WhaleBalanceSnapshot.address,
                func.count(WhaleBalanceSnapshot.id).label('zero_count')
            ).where(
                and_(
                    WhaleBalanceSnapshot.snapshot_timestamp >= start_time,
                    WhaleBalanceSnapshot.balance_eth == 0
                )
            ).group_by(
                WhaleBalanceSnapshot.address
            )
            
            result = await self.session.execute(zero_balance_query)
            zero_balance_whales = result.all()
            zero_whale_count = len(zero_balance_whales)
            
            # Determine status
            if zero_whale_count == 0:
                status = HealthStatus.HEALTHY
                score = 100.0
            elif zero_whale_count <= 5:
                status = HealthStatus.DEGRADED
                score = 70.0
                for whale_addr, count in zero_balance_whales:
                    issues.append(
                        f"[WARNING] Whale {whale_addr[:10]}... has {count} "
                        f"zero-balance snapshots (likely RPC cache miss)"
                    )
            else:
                status = HealthStatus.CRITICAL
                score = 30.0
                issues.append(
                    f"[CRITICAL] {zero_whale_count} whales with zero balance detected! "
                    f"Systemic Multicall failure - verify RPC provider health."
                )
                # Show top 3 affected whales
                for whale_addr, count in zero_balance_whales[:3]:
                    issues.append(
                        f"  └─ {whale_addr[:10]}... ({count} zero snapshots)"
                    )
            
            logger.info(
                f"  ├─ Zero-Balance Whales: {zero_whale_count}"
            )
            logger.info(
                f"  └─ Status: [{status.value.upper()}]"
            )
            
            return ValidationResult(
                check_name="precision_integrity",
                status=status,
                score=score,
                issues=issues,
                metrics={
                    "zero_balance_whale_count": zero_whale_count,
                    "affected_addresses": [w[0] for w in zero_balance_whales[:10]]
                },
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"  └─ ❌ FAILED: {e}")
            return ValidationResult(
                check_name="precision_integrity",
                status=HealthStatus.CRITICAL,
                score=0.0,
                issues=[f"Check failed: {str(e)}"],
                metrics={},
                timestamp=datetime.now(timezone.utc)
            )
    
    async def check_time_drift(self) -> ValidationResult:
        """
        Validate block timestamp vs snapshot timestamp alignment.
        
        DETECTION: "Stale" data from archive node or cache hits
        
        Ethereum blocks arrive ~12 seconds apart (post-merge).
        Expected drift: snapshot_timestamp ≈ block_timestamp ± 1 minute
        
        Algorithm:
        1. Sample recent 100 snapshots
        2. For each: Calculate |snapshot_time - expected_block_time|
        3. Flag if drift > 10% of expected block interval
        
        THRESHOLD: Avg drift <5% = HEALTHY
                   Avg drift 5-10% = DEGRADED
                   Avg drift >10% = CRITICAL
        
        Returns:
            ValidationResult with time drift statistics
        """
        logger.info("🔬 CHECK 3/5: Time Drift Analysis...")
        
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(hours=24)
        issues = []
        
        try:
            # Get sample of recent snapshots with block numbers
            sample_query = select(
                WhaleBalanceSnapshot
            ).where(
                and_(
                    WhaleBalanceSnapshot.snapshot_timestamp >= start_time,
                    WhaleBalanceSnapshot.block_number.isnot(None)
                )
            ).order_by(
                WhaleBalanceSnapshot.snapshot_timestamp.desc()
            ).limit(100)
            
            result = await self.session.execute(sample_query)
            snapshots = result.scalars().all()
            
            if not snapshots:
                return ValidationResult(
                    check_name="time_drift",
                    status=HealthStatus.DEGRADED,
                    score=50.0,
                    issues=["[WARNING] No snapshots with block numbers found"],
                    metrics={"sample_size": 0},
                    timestamp=datetime.now(timezone.utc)
                )
            
            # Calculate drift for each snapshot
            # Assumption: Ethereum post-merge block time ≈ 12 seconds
            EXPECTED_BLOCK_TIME_SECONDS = 12.0
            
            drift_percentages = []
            stale_count = 0
            
            # We need to estimate block timestamp from block number
            # For simplicity, use first snapshot as reference point
            if len(snapshots) > 1:
                ref_snapshot = snapshots[0]
                ref_block = ref_snapshot.block_number
                ref_time = ref_snapshot.snapshot_timestamp
                
                for snapshot in snapshots:
                    # Estimate block time
                    block_diff = ref_block - snapshot.block_number
                    expected_time_diff = timedelta(
                        seconds=block_diff * EXPECTED_BLOCK_TIME_SECONDS
                    )
                    expected_block_time = ref_time - expected_time_diff
                    
                    # Calculate drift
                    actual_drift = abs(
                        (snapshot.snapshot_timestamp - expected_block_time).total_seconds()
                    )
                    drift_pct = (actual_drift / (EXPECTED_BLOCK_TIME_SECONDS * 60)) * 100
                    
                    drift_percentages.append(drift_pct)
                    
                    if drift_pct > 10.0:
                        stale_count += 1
            
            # Calculate statistics
            if drift_percentages:
                avg_drift_pct = sum(drift_percentages) / len(drift_percentages)
                max_drift_pct = max(drift_percentages)
            else:
                avg_drift_pct = 0.0
                max_drift_pct = 0.0
            
            # Determine status
            if avg_drift_pct < 5.0:
                status = HealthStatus.HEALTHY
                score = 100.0
            elif avg_drift_pct < 10.0:
                status = HealthStatus.DEGRADED
                score = 75.0
                issues.append(
                    f"[WARNING] Average time drift at {avg_drift_pct:.2f}% "
                    f"(target: <5%). {stale_count} stale snapshots detected."
                )
            else:
                status = HealthStatus.CRITICAL
                score = 40.0
                issues.append(
                    f"[CRITICAL] High time drift detected - {avg_drift_pct:.2f}% "
                    f"average deviation. Max drift: {max_drift_pct:.2f}%. "
                    f"Possible archive node cache pollution!"
                )
            
            logger.info(
                f"  ├─ Sample Size: {len(snapshots)}"
            )
            logger.info(
                f"  ├─ Average Drift: {avg_drift_pct:.2f}%"
            )
            logger.info(
                f"  ├─ Max Drift: {max_drift_pct:.2f}%"
            )
            logger.info(
                f"  └─ Status: [{status.value.upper()}]"
            )
            
            return ValidationResult(
                check_name="time_drift",
                status=status,
                score=score,
                issues=issues,
                metrics={
                    "sample_size": len(snapshots),
                    "avg_drift_pct": avg_drift_pct,
                    "max_drift_pct": max_drift_pct,
                    "stale_count": stale_count
                },
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"  └─ ❌ FAILED: {e}")
            return ValidationResult(
                check_name="time_drift",
                status=HealthStatus.CRITICAL,
                score=0.0,
                issues=[f"Check failed: {str(e)}"],
                metrics={},
                timestamp=datetime.now(timezone.utc)
            )
    
    async def check_statistical_outliers(self) -> ValidationResult:
        """
        Detect impossible balance spikes without on-chain proof.
        
        DETECTION: Balance changes >50% per hour without transaction evidence
        
        Root Cause: Parser bugs or RPC response corruption create phantom "dumps"
        
        Algorithm:
        1. For each whale, get balance at t and t-1 hour
        2. Calculate delta_pct = |balance_t - balance_t-1| / balance_t-1 * 100
        3. Flag if delta_pct > 50% (physiologically impossible without tx)
        
        THRESHOLD: 0 outliers = HEALTHY
                   1-3 outliers = DEGRADED (isolated parser glitch)
                   >3 outliers = CRITICAL (systemic corruption)
        
        Returns:
            ValidationResult with outlier detection metrics
        """
        logger.info("🔬 CHECK 4/5: Statistical Outlier Detection...")
        
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours=1)
        two_hours_ago = now - timedelta(hours=2)
        issues = []
        
        try:
            # Get snapshots from 1 hour ago
            recent_query = select(
                WhaleBalanceSnapshot
            ).where(
                WhaleBalanceSnapshot.snapshot_timestamp >= one_hour_ago
            ).order_by(
                WhaleBalanceSnapshot.address,
                WhaleBalanceSnapshot.snapshot_timestamp.desc()
            )
            
            result = await self.session.execute(recent_query)
            recent_snapshots = result.scalars().all()
            
            # Get snapshots from 2 hours ago (for comparison)
            historical_query = select(
                WhaleBalanceSnapshot
            ).where(
                and_(
                    WhaleBalanceSnapshot.snapshot_timestamp >= two_hours_ago,
                    WhaleBalanceSnapshot.snapshot_timestamp < one_hour_ago
                )
            ).order_by(
                WhaleBalanceSnapshot.address,
                WhaleBalanceSnapshot.snapshot_timestamp.desc()
            )
            
            result = await self.session.execute(historical_query)
            historical_snapshots = result.scalars().all()
            
            # Build lookup dict for historical balances
            historical_balances = {}
            for snap in historical_snapshots:
                if snap.address not in historical_balances:
                    historical_balances[snap.address] = snap.balance_eth
            
            # Check for outliers
            outliers = []
            OUTLIER_THRESHOLD = 50.0  # 50% change
            
            for snap in recent_snapshots:
                if snap.address in historical_balances:
                    old_balance = historical_balances[snap.address]
                    new_balance = snap.balance_eth
                    
                    if old_balance > 0:
                        change_pct = abs(
                            (new_balance - old_balance) / old_balance * 100
                        )
                        
                        if change_pct > OUTLIER_THRESHOLD:
                            outliers.append({
                                "address": snap.address,
                                "old_balance": float(old_balance),
                                "new_balance": float(new_balance),
                                "change_pct": change_pct
                            })
            
            # Determine status
            outlier_count = len(outliers)
            
            if outlier_count == 0:
                status = HealthStatus.HEALTHY
                score = 100.0
            elif outlier_count <= 3:
                status = HealthStatus.DEGRADED
                score = 70.0
                for outlier in outliers:
                    issues.append(
                        f"[WARNING] Suspicious {outlier['change_pct']:.1f}% balance change "
                        f"for {outlier['address'][:10]}... "
                        f"({outlier['old_balance']:.2f} → {outlier['new_balance']:.2f} ETH)"
                    )
            else:
                status = HealthStatus.CRITICAL
                score = 30.0
                issues.append(
                    f"[CRITICAL] {outlier_count} whales with extreme balance changes detected! "
                    f"Possible parser corruption or RPC data poisoning."
                )
                for outlier in outliers[:3]:
                    issues.append(
                        f"  └─ {outlier['address'][:10]}... "
                        f"({outlier['change_pct']:.1f}% change)"
                    )
            
            logger.info(
                f"  ├─ Whales Checked: {len(recent_snapshots)}"
            )
            logger.info(
                f"  ├─ Outliers Found: {outlier_count}"
            )
            logger.info(
                f"  └─ Status: [{status.value.upper()}]"
            )
            
            return ValidationResult(
                check_name="statistical_outliers",
                status=status,
                score=score,
                issues=issues,
                metrics={
                    "whales_checked": len(recent_snapshots),
                    "outliers_found": outlier_count,
                    "outlier_threshold_pct": OUTLIER_THRESHOLD,
                    "outlier_details": outliers[:5]  # Top 5
                },
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"  └─ ❌ FAILED: {e}")
            return ValidationResult(
                check_name="statistical_outliers",
                status=HealthStatus.CRITICAL,
                score=0.0,
                issues=[f"Check failed: {str(e)}"],
                metrics={},
                timestamp=datetime.now(timezone.utc)
            )
    
    async def check_lst_consistency(self) -> ValidationResult:
        """
        Validate stETH/ETH rate sanity bounds.
        
        DETECTION: Corrupted LST rates that block Depeg Risk tag
        
        Historical Range (post-merge 2022-2025):
        - Lowest: 0.9329 (during Terra/Luna crisis 2022)
        - Highest: 1.0012 (normal operations)
        - Safety bounds: 0.90 ≤ rate ≤ 1.10
        
        If rate outside bounds, AccumulationMetric.tags cannot include [Depeg Risk]
        
        THRESHOLD: All rates in bounds = HEALTHY
                   1-2 violations = DEGRADED
                   >2 violations = CRITICAL
        
        REFERENCE: STETH_COMPLETION_REPORT.md - "LST Rate Validation"
        
        Returns:
            ValidationResult with LST rate validation metrics
        """
        logger.info("🔬 CHECK 5/5: LST Consistency Validation...")
        
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(hours=24)
        issues = []
        
        try:
            # Get recent accumulation metrics with LST rates
            lst_query = select(
                AccumulationMetric
            ).where(
                and_(
                    AccumulationMetric.created_at >= start_time,
                    AccumulationMetric.steth_eth_rate.isnot(None)
                )
            ).order_by(
                AccumulationMetric.created_at.desc()
            )
            
            result = await self.session.execute(lst_query)
            metrics = result.scalars().all()
            
            if not metrics:
                return ValidationResult(
                    check_name="lst_consistency",
                    status=HealthStatus.DEGRADED,
                    score=50.0,
                    issues=["[WARNING] No LST rates found in last 24h"],
                    metrics={"sample_size": 0},
                    timestamp=datetime.now(timezone.utc)
                )
            
            # Check rate bounds
            MIN_RATE = Decimal("0.90")
            MAX_RATE = Decimal("1.10")
            
            violations = []
            rates = []
            
            for metric in metrics:
                rate = metric.steth_eth_rate
                rates.append(float(rate))
                
                if rate < MIN_RATE or rate > MAX_RATE:
                    violations.append({
                        "metric_id": metric.id,
                        "rate": float(rate),
                        "timestamp": metric.created_at.isoformat(),
                        "tags": metric.tags
                    })
            
            # Calculate statistics
            if rates:
                avg_rate = sum(rates) / len(rates)
                min_rate = min(rates)
                max_rate = max(rates)
            else:
                avg_rate = 0.0
                min_rate = 0.0
                max_rate = 0.0
            
            # Determine status
            violation_count = len(violations)
            
            if violation_count == 0:
                status = HealthStatus.HEALTHY
                score = 100.0
            elif violation_count <= 2:
                status = HealthStatus.DEGRADED
                score = 70.0
                for v in violations:
                    issues.append(
                        f"[WARNING] LST rate {v['rate']:.4f} outside bounds "
                        f"(0.90-1.10) at {v['timestamp'][:19]}. "
                        f"[Depeg Risk] tag blocked for this metric."
                    )
            else:
                status = HealthStatus.CRITICAL
                score = 30.0
                issues.append(
                    f"[CRITICAL] {violation_count} LST rate violations detected! "
                    f"Verify CoinGecko API connection or consider manual rate override."
                )
                for v in violations[:3]:
                    issues.append(
                        f"  └─ Rate: {v['rate']:.4f} at {v['timestamp'][:19]}"
                    )
            
            logger.info(
                f"  ├─ Metrics Checked: {len(metrics)}"
            )
            logger.info(
                f"  ├─ Avg Rate: {avg_rate:.4f}"
            )
            logger.info(
                f"  ├─ Rate Range: {min_rate:.4f} - {max_rate:.4f}"
            )
            logger.info(
                f"  ├─ Violations: {violation_count}"
            )
            logger.info(
                f"  └─ Status: [{status.value.upper()}]"
            )
            
            return ValidationResult(
                check_name="lst_consistency",
                status=status,
                score=score,
                issues=issues,
                metrics={
                    "sample_size": len(metrics),
                    "avg_rate": avg_rate,
                    "min_rate": min_rate,
                    "max_rate": max_rate,
                    "violations_count": violation_count,
                    "violation_details": violations[:5]
                },
                timestamp=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            logger.error(f"  └─ ❌ FAILED: {e}")
            return ValidationResult(
                check_name="lst_consistency",
                status=HealthStatus.CRITICAL,
                score=0.0,
                issues=[f"Check failed: {str(e)}"],
                metrics={},
                timestamp=datetime.now(timezone.utc)
            )
    
    def _calculate_overall_status(self) -> HealthStatus:
        """Calculate overall system health from check results"""
        if not self.results:
            return HealthStatus.CRITICAL
        
        # If any check is CRITICAL, overall is CRITICAL
        if any(r.status == HealthStatus.CRITICAL for r in self.results):
            return HealthStatus.CRITICAL
        
        # If any check is DEGRADED, overall is DEGRADED
        if any(r.status == HealthStatus.DEGRADED for r in self.results):
            return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY
    
    def _calculate_overall_score(self) -> float:
        """Calculate weighted overall score"""
        if not self.results:
            return 0.0
        
        # Weight critical checks more heavily
        weights = {
            "snapshot_density": 0.25,
            "precision_integrity": 0.25,
            "time_drift": 0.20,
            "statistical_outliers": 0.20,
            "lst_consistency": 0.10
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for result in self.results:
            weight = weights.get(result.check_name, 0.20)
            total_score += result.score * weight
            total_weight += weight
        
        if total_weight > 0:
            return total_score / total_weight
        return 0.0
    
    def _generate_summary(self) -> Dict[str, int]:
        """Generate issue summary"""
        total_issues = sum(len(r.issues) for r in self.results)
        critical_issues = sum(
            len(r.issues) for r in self.results
            if r.status == HealthStatus.CRITICAL
        )
        warnings = sum(
            len(r.issues) for r in self.results
            if r.status == HealthStatus.DEGRADED
        )
        
        return {
            "total_issues": total_issues,
            "critical_issues": critical_issues,
            "warnings": warnings,
            "checks_passed": sum(
                1 for r in self.results if r.status == HealthStatus.HEALTHY
            ),
            "checks_failed": sum(
                1 for r in self.results if r.status == HealthStatus.CRITICAL
            )
        }
    
    @staticmethod
    def _result_to_dict(result: ValidationResult) -> Dict:
        """Convert ValidationResult to JSON-serializable dict"""
        return {
            "check_name": result.check_name,
            "status": result.status.value,
            "score": result.score,
            "issues": result.issues,
            "metrics": result.metrics,
            "timestamp": result.timestamp.isoformat()
        }


# ═══════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

async def main():
    """
    Run data quality validation and output JSON report.
    
    Usage:
        python data_quality_validator.py
        
    Output:
        JSON report to stdout with:
        - overall_status: "healthy" | "degraded" | "critical"
        - overall_score: 0-100
        - checks: detailed results for each validation
        - summary: aggregated metrics
    """
    logger.info("╔═══════════════════════════════════════════════════════════╗")
    logger.info("║   WHALE TRACKER - DATA QUALITY VALIDATION SYSTEM          ║")
    logger.info("║   Cyberpunk Edition 🔥⚡                                  ║")
    logger.info("╚═══════════════════════════════════════════════════════════╝")
    logger.info("")
    
    async with get_session() as session:
        validator = DataQualityValidator(session)
        report = await validator.run_all_checks()
        
        # Output JSON report
        import json
        print("\n" + "=" * 60)
        print("DATA QUALITY REPORT (JSON)")
        print("=" * 60)
        print(json.dumps(report, indent=2))
        print("=" * 60)
        
        # Return status code for automation
        if report["overall_status"] == "critical":
            logger.error("🚨 CRITICAL ISSUES DETECTED - MANUAL INTERVENTION REQUIRED")
            return 2
        elif report["overall_status"] == "degraded":
            logger.warning("⚠️  DEGRADED DATA QUALITY - MONITORING RECOMMENDED")
            return 1
        else:
            logger.info("✅ ALL SYSTEMS NOMINAL - DATA QUALITY EXCELLENT")
            return 0


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
