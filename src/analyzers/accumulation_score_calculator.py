"""
Accumulation Score Calculator - Collective Whale Behavior Analysis

Analyzes collective whale accumulation/distribution patterns by comparing
current vs historical balances across top holders.

Core Insight: Individual whale movements = noise
              Collective whale movements = signal

Author: Whale Tracker Project
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta, UTC
from decimal import Decimal

from src.data.whale_list_provider import WhaleListProvider
from src.data.multicall_client import MulticallClient
from src.repositories.accumulation_repository import AccumulationRepository
from src.repositories.snapshot_repository import SnapshotRepository
from src.schemas.accumulation_schemas import (
    AccumulationMetricCreate,
    AccumulationMetric
)


class AccumulationScoreCalculator:
    """
    Calculate collective whale accumulation scores.
    
    Process:
    1. Get current whale balances (WhaleListProvider)
    2. Fetch historical balances (24h ago via MulticallClient)
    3. Calculate aggregate changes
    4. Compute accumulation score
    5. Store in database (AccumulationRepository)
    
    Accumulation Score Formula:
        score = (total_current - total_historical) / total_historical × 100
        
        Positive score = Net accumulation (whales buying)
        Negative score = Net distribution (whales selling)
    """
    
    def __init__(
        self,
        whale_provider: WhaleListProvider,
        multicall_client: MulticallClient,
        repository: AccumulationRepository,
        snapshot_repo: SnapshotRepository,
        price_provider,  # Add: For stETH rate and historical prices
        lookback_hours: int = 24
    ):
        """
        # ============================================
        # STEP 1: AGGREGATE BALANCES (ETH + WETH + stETH)
        # ============================================
        
        self.logger.info("STEP 1: Aggregating LST balances (ETH + WETH + stETH)...")
        
        # Calculate aggregated balances for CURRENT state
        aggregated_current = {}
        for address in current_balances:
            eth_wei = current_balances.get(address, 0) or 0
            weth_wei = weth_balances.get(address, 0) or 0
            steth_wei = steth_balances.get(address, 0) or 0
            
            # Convert stETH to ETH equivalent
            steth_in_eth_wei = int(Decimal(str(steth_wei)) * steth_rate)
            
            # Aggregate
            total_wealth_wei = eth_wei + weth_wei + steth_in_eth_wei
            aggregated_current[address] = total_wealth_wei
        
        # Calculate aggregated balances for HISTORICAL state
        # NOTE: For MVP, we assume WETH/stETH holdings were same (simplified)
        # TODO Phase 3: Fetch historical WETH/stETH balances via archive node
        aggregated_historical = {}
        for address in historical_balances:
            eth_wei = historical_balances.get(address, 0) or 0
            # MVP: Assume LST holdings unchanged (conservative estimate)
            weth_wei = weth_balances.get(address, 0) or 0
            steth_wei = steth_balances.get(address, 0) or 0
            steth_in_eth_wei = int(Decimal(str(steth_wei)) * steth_rate)
            
            total_wealth_wei = eth_wei + weth_wei + steth_in_eth_wei
            aggregated_historical[address] = total_wealth_wei
        
        # ============================================
        # STEP 2: CALCULATE STANDARD METRICS (Native ETH)
        # ============================================
        Initialize AccumulationScoreCalculator.
        
        Args:
            whale_provider: WhaleListProvider for getting current whales
            multicall_client: MulticallClient for CURRENT balances only
            repository: AccumulationRepository for storing results
            snapshot_repo: SnapshotRepository for historical balances (NO archive node!)
            lookback_hours: Hours to look back for comparison (default: 24)
        
        GEMINI: "Use snapshots instead of archive node - industry standard"
        """
        self.logger = logging.getLogger(__name__)
        self.whale_provider = whale_provider
        self.multicall_client = multicall_client
        self.repository = repository
        self.snapshot_repo = snapshot_repo
        self.price_provider = price_provider
        self.lookback_hours = lookback_hours
        
        self.logger.info(
            f"AccumulationScoreCalculator initialized with {lookback_hours}h lookback "
            f"(snapshot-based, no archive node, LST correction enabled)"
        )
    
    async def calculate_accumulation_score(
        self,
        token_symbol: str = "ETH",
        whale_limit: int = 1000,
        network: str = "ethereum"
    ) -> AccumulationMetric:
        """
        Calculate and store accumulation score for top whales.
        
        Args:
            token_symbol: Token to analyze (default: "ETH")
            whale_limit: Number of top whales to analyze (default: 1000)
            network: Network name (default: "ethereum")
        
        Returns:
            AccumulationMetric: Calculated metrics with score
        
        Example:
            >>> calculator = AccumulationScoreCalculator(...)
            >>> metric = await calculator.calculate_accumulation_score()
            >>> print(f"Score: {metric.accumulation_score}%")
            Score: 2.5%  # Whales are accumulating
        """
        self.logger.info(
            f"Calculating accumulation score for {token_symbol} "
            f"(top {whale_limit} whales, {self.lookback_hours}h lookback) "
            f"[SURVIVAL BIAS FIX: UNION approach]"
        )
        
        # Step 1: Get CURRENT top whales
        self.logger.info("Step 1: Fetching current top whale addresses...")
        current_whales = await self.whale_provider.get_top_whales(
            limit=whale_limit,
            network=network
        )
        
        if not current_whales:
            raise ValueError("No whales found - cannot calculate accumulation score")
        
        current_addresses = {w['address'] for w in current_whales}
        self.logger.info(f"Found {len(current_addresses)} current top whales")
        
        # Step 2: Get HISTORICAL top whales (24h ago) - FIX SURVIVAL BIAS!
        self.logger.info("Step 2: Fetching historical top whale addresses...")
        lookback_time = datetime.now(UTC) - timedelta(hours=self.lookback_hours)
        
        historical_top = await self.snapshot_repo.get_addresses_in_top_at_time(
            timestamp=lookback_time,
            limit=whale_limit,
            tolerance_hours=1,
            network=network
        )
        
        self.logger.info(
            f"Found {len(historical_top)} historical top whales @ {lookback_time}"
        )
        
        # Step 3: UNION - analyze ALL whales (current OR historical)
        # GEMINI: "This fixes Survival Bias - we analyze everyone who WAS or IS a whale"
        all_addresses = current_addresses | historical_top
        
        self.logger.info(
            f"UNION: {len(all_addresses)} total addresses to analyze "
            f"({len(current_addresses)} current + {len(historical_top)} historical)"
        )
        
        # Step 4: Get CURRENT balances for ALL addresses
        self.logger.info("Step 4: Fetching current balances for ALL addresses...")
        current_balances_raw = await self.multicall_client.get_balances_batch(
            addresses=list(all_addresses),
            network=network
        )
        
        # Convert to dict (address -> balance_wei)
        current_balances = {
            addr: balance for addr, balance in current_balances_raw.items()
        }
        
        # Step 4.5: Fetch LST balances (WETH + stETH)
        self.logger.info("Step 4.5: Fetching LST balances (WETH + stETH)...")
        weth_balances, steth_balances, steth_rate = await self._fetch_lst_balances(
            addresses=list(all_addresses),
            network=network
        )
        
        # Step 4.7: Fetch historical price for Bullish Divergence detection
        self.logger.info("Step 4.7: Fetching historical price (48h ago)...")
        try:
            timestamp_48h_ago = datetime.now(UTC) - timedelta(hours=48)
            price_48h_ago = await self.price_provider.get_historical_price(
                token_symbol=token_symbol,
                timestamp=timestamp_48h_ago
            )
            price_current = await self.price_provider.get_current_price(token_symbol)
            
            if price_48h_ago and price_current:
                price_change_48h_pct = (price_current - price_48h_ago) / price_48h_ago * 100
                self.logger.info(
                    f"Price context: {price_48h_ago:.2f} → {price_current:.2f} "
                    f"({price_change_48h_pct:+.2f}% over 48h)"
                )
            else:
                price_change_48h_pct = None
                self.logger.warning("Could not fetch historical price for Bullish Divergence detection")
        
        except Exception as e:
            self.logger.error(f"Error fetching historical price: {e}")
            price_change_48h_pct = None
        
        # Step 4.8: Detect DeFi looping patterns (GEMINI FIX)
        self.logger.info("Step 4.8: Detecting DeFi looping patterns...")
        looping_suspect_count = await self._detect_looping_pattern(
            addresses=list(all_addresses),
            weth_balances=weth_balances,
            steth_balances=steth_balances,
            network=network
        )
        
        # Step 5: Get HISTORICAL balances from snapshots (NO archive node!)
        self.logger.info("Step 5: Fetching historical balances from snapshots...")
        
        # Step 5.1: GEMINI FIX #7 - Validate snapshot density BEFORE fetching
        self.logger.info("Step 5.1: Validating snapshot density (GEMINI FIX #7)...")
        snapshot_density_valid = True
        snapshot_coverage_pct = 100.0
        
        try:
            is_valid, coverage, found, expected = await self.snapshot_repo.validate_snapshot_density(
                addresses=list(all_addresses),
                lookback_hours=self.lookback_hours,
                min_coverage_pct=85.0,  # Require 85% coverage
                network=network
            )
            snapshot_coverage_pct = coverage
            
        except Exception as e:
            # InsufficientSnapshotCoverageError or other errors
            self.logger.error(f"⚠️ Snapshot density validation failed: {e}")
            snapshot_density_valid = False
            
            # Extract coverage if available
            if hasattr(e, 'coverage_pct'):
                snapshot_coverage_pct = e.coverage_pct
        
        historical_snapshots = await self.snapshot_repo.get_snapshots_batch_at_time(
            addresses=list(all_addresses),
            timestamp=lookback_time,
            tolerance_hours=1,
            network=network
        )
        
        historical_balances = {
            addr: int(snapshot.balance_wei) 
            for addr, snapshot in historical_snapshots.items()
        }
        
        # Step 5.5: Fetch HISTORICAL LST balances (CRITICAL FIX for precision vulnerability)
        self.logger.info("Step 5.5: Fetching historical LST balances (WETH + stETH)...")
        weth_historical, steth_historical = await self._fetch_historical_lst_balances(
            addresses=list(all_addresses),
            timestamp=lookback_time,
            network=network
        )
        
        # Step 4.6: Detect LST migrations (MOVED AFTER Step 5.5 - needs historical LST!)
        self.logger.info("Step 4.6: Detecting LST migrations...")
        lst_migration_count = await self._detect_lst_migration(
            addresses=list(all_addresses),
            eth_current=current_balances,
            eth_historical=historical_balances,
            weth_current=weth_balances,
            steth_current=steth_balances,
            weth_historical=weth_historical,  # ✅ ADDED
            steth_historical=steth_historical,  # ✅ ADDED
            steth_rate=steth_rate,
            time_window_hours=1
        )
        
        self.logger.info(
            f"Retrieved {len(historical_balances)} historical snapshots "
            f"({len(all_addresses) - len(historical_balances)} missing)"
        )
        
        # Handle missing snapshots
        for addr in all_addresses:
            if addr not in historical_balances:
                # If no snapshot, assume balance was 0 (new whale)
                historical_balances[addr] = 0
                self.logger.warning(
                    f"No snapshot for {addr[:10]}... - assuming zero historical balance"
                )
        
        # Get current block for metadata
        current_block = await self.multicall_client.get_latest_block(network)
        historical_block = 0  # Not used anymore (snapshot-based)
        
        # Step 6: Calculate aggregate metrics
        self.logger.info("Step 6: Calculating aggregate metrics...")
        metrics = self._calculate_metrics(
            current_balances=current_balances,
            historical_balances=historical_balances,
            weth_balances=weth_balances,
            steth_balances=steth_balances,
            steth_rate=steth_rate,
            lst_migration_count=lst_migration_count,
            looping_suspect_count=looping_suspect_count,  # ✅ GEMINI
            price_change_48h_pct=price_change_48h_pct,
            token_symbol=token_symbol,
            whale_count=len(all_addresses),
            current_block=current_block,
            historical_block=historical_block
        )
        
        # Step 7: Assign smart tags
        self.logger.info("Step 7: Assigning smart tags...")
        metrics.tags = self._assign_tags(
            metrics, 
            len(all_addresses),
            looping_suspect_count=looping_suspect_count,  # ✅ GEMINI
            snapshot_density_valid=snapshot_density_valid,  # ✅ GEMINI FIX #7
            snapshot_coverage_pct=snapshot_coverage_pct  # ✅ GEMINI FIX #7
        )
        
        # Step 8: Store in database
        self.logger.info("Step 8: Storing metrics in database...")
        metric_id = await self.repository.save_metric(metrics)
        
        # Fetch stored metric to return with ID
        # Note: For MVP, we return metrics with ID manually set
        metrics_dict = metrics.model_dump()
        metrics_dict['id'] = metric_id
        stored_metric = AccumulationMetric(**metrics_dict)
        
        # Step 9: Generate professional Twitter-ready report
        self.logger.info("Step 9: Generating professional Twitter-ready report...")
        professional_report = self._format_professional_report(
            stored_metric,
            snapshot_density_valid,
            snapshot_coverage_pct
        )
        
        # Log the full report (line by line for proper formatting)
        for line in professional_report.split('\n'):
            self.logger.info(line)
        
        self.logger.info(
            f"✅ Accumulation analysis complete. "
            f"Tags: {', '.join(stored_metric.tags) if stored_metric.tags else 'None'}"
        )
        
        return stored_metric
    
    async def _fetch_lst_balances(
        self,
        addresses: List[str],
        network: str = "ethereum"
    ) -> tuple[Dict[str, int], Dict[str, int], Decimal]:
        """
        Fetch WETH and stETH balances for all addresses.
        
        WHY: LST migration detection requires tracking wrapped/staked ETH
        
        Args:
            addresses: List of whale addresses
            network: Network name
        
        Returns:
            Tuple of (weth_balances, steth_balances, steth_rate)
        """
        from src.data.multicall_client import WETH_ADDRESS, STETH_ADDRESS
        
        self.logger.info(f"Fetching LST balances (WETH + stETH) for {len(addresses)} addresses...")
        
        # Fetch WETH balances
        weth_balances = await self.multicall_client.get_erc20_balances_batch(
            addresses=addresses,
            token_address=WETH_ADDRESS,
            network=network
        )
        
        # Fetch stETH balances
        steth_balances = await self.multicall_client.get_erc20_balances_batch(
            addresses=addresses,
            token_address=STETH_ADDRESS,
            network=network
        )
        
        # Get stETH/ETH exchange rate
        steth_rate = await self.price_provider.get_steth_eth_rate()
        
        self.logger.info(
            f"LST balances fetched: "
            f"{len([b for b in weth_balances.values() if b and b > 0])} WETH holders, "
            f"{len([b for b in steth_balances.values() if b and b > 0])} stETH holders, "
            f"rate={steth_rate:.4f}"
        )
        
        return weth_balances, steth_balances, steth_rate
    
    async def _fetch_historical_lst_balances(
        self,
        addresses: List[str],
        timestamp: datetime,
        network: str = "ethereum"
    ) -> tuple[Dict[str, int], Dict[str, int]]:
        """
        Fetch HISTORICAL WETH and stETH balances from snapshots.
        
        WHY: CRITICAL FIX for precision vulnerability (Gemini report)
             Need historical LST balances to calculate accurate deltas
        
        MVP APPROACH:
        - For now, assume LST balances unchanged (conservative)
        - TODO Phase 3: Store LST snapshots hourly
        
        Args:
            addresses: List of whale addresses
            timestamp: Historical timestamp to fetch from
            network: Network name
        
        Returns:
            Tuple of (weth_historical, steth_historical)
        """
        self.logger.info(
            f"Fetching historical LST balances for {len(addresses)} addresses @ {timestamp}..."
        )
        
        # MVP: Return zero balances (assume no historical LST)
        # This is conservative - prevents false migrations
        weth_historical = {addr: 0 for addr in addresses}
        steth_historical = {addr: 0 for addr in addresses}
        
        self.logger.warning(
            f"MVP: Using zero historical LST balances (conservative estimate). "
            f"TODO Phase 3: Implement LST snapshot storage for accurate migration detection."
        )
        
        return weth_historical, steth_historical
    
    def _calculate_metrics(
        self,
        current_balances: Dict[str, int],
        historical_balances: Dict[str, int],
        weth_balances: Dict[str, int],
        steth_balances: Dict[str, int],
        steth_rate: Decimal,
        lst_migration_count: int,
        looping_suspect_count: int,  # ✅ GEMINI
        price_change_48h_pct: Optional[Decimal],
        token_symbol: str,
        whale_count: int,
        current_block: int,
        historical_block: int
    ) -> AccumulationMetricCreate:
        """
        Calculate accumulation metrics with LST correction.
        
        WHY: Aggregates ETH + WETH + stETH to get true whale positions
        
        FORMULAS:
        - total_wealth = ETH + WETH + (stETH × rate)
        - lst_adjusted_score = (wealth_now - wealth_24h_ago) / wealth_24h_ago × 100
        - MAD = median(|change_i - median(changes)|)
        - Gini = measure of inequality in balance distribution
        
        Args:
            current_balances: Current ETH balances (address -> wei)
            historical_balances: Historical ETH balances (address -> wei)
            weth_balances: Current WETH balances (address -> wei)
            steth_balances: Current stETH balances (address -> wei)
            steth_rate: stETH/ETH exchange rate
            token_symbol: Token symbol
            whale_count: Number of whales analyzed
            current_block: Current block number
            historical_block: Historical block number
        
        Returns:
            AccumulationMetricCreate: Metrics ready for database storage
        """
        # ============================================
        # STEP 1: AGGREGATE BALANCES (ETH + WETH + stETH)
        # ============================================
        
        self.logger.info("STEP 1: Aggregating LST balances (ETH + WETH + stETH)...")
        
        # Calculate aggregated balances for CURRENT state
        aggregated_current = {}
        for address in current_balances:
            eth_wei = current_balances.get(address, 0) or 0
            weth_wei = weth_balances.get(address, 0) or 0
            steth_wei = steth_balances.get(address, 0) or 0
            
            # Convert stETH to ETH equivalent
            steth_in_eth_wei = int(Decimal(str(steth_wei)) * steth_rate)
            
            # Aggregate
            total_wealth_wei = eth_wei + weth_wei + steth_in_eth_wei
            aggregated_current[address] = total_wealth_wei
        
        # Calculate aggregated balances for HISTORICAL state
        # NOTE: For MVP, we assume WETH/stETH holdings were same (simplified)
        # TODO Phase 3: Fetch historical WETH/stETH balances via archive node
        aggregated_historical = {}
        for address in historical_balances:
            eth_wei = historical_balances.get(address, 0) or 0
            # MVP: Assume LST holdings unchanged (conservative estimate)
            weth_wei = weth_balances.get(address, 0) or 0
            steth_wei = steth_balances.get(address, 0) or 0
            steth_in_eth_wei = int(Decimal(str(steth_wei)) * steth_rate)
            
            total_wealth_wei = eth_wei + weth_wei + steth_in_eth_wei
            aggregated_historical[address] = total_wealth_wei
        
        # ============================================
        # STEP 2: CALCULATE STANDARD METRICS (Native ETH)
        # ============================================
        
        total_current_wei = sum(current_balances.values())
        total_historical_wei = sum(historical_balances.values())
        total_change_wei = total_current_wei - total_historical_wei
        
        total_current_eth = Decimal(str(total_current_wei)) / Decimal('1e18')
        total_historical_eth = Decimal(str(total_historical_wei)) / Decimal('1e18')
        total_change_eth = Decimal(str(total_change_wei)) / Decimal('1e18')
        
        # Standard accumulation score (native ETH only)
        if total_historical_wei > 0:
            accumulation_score = Decimal(str(total_change_wei)) / Decimal(str(total_historical_wei)) * 100
        else:
            accumulation_score = Decimal('0')
        
        # ============================================
        # STEP 3: CALCULATE LST-ADJUSTED METRICS
        # ============================================
        
        self.logger.info("STEP 3: Calculating LST-adjusted metrics...")
        
        total_aggregated_current_wei = sum(aggregated_current.values())
        total_aggregated_historical_wei = sum(aggregated_historical.values())
        total_aggregated_change_wei = total_aggregated_current_wei - total_aggregated_historical_wei
        
        # LST-adjusted score
        if total_aggregated_historical_wei > 0:
            lst_adjusted_score = Decimal(str(total_aggregated_change_wei)) / Decimal(str(total_aggregated_historical_wei)) * 100
        else:
            lst_adjusted_score = Decimal('0')
        
        # Separate WETH/stETH totals
        total_weth_wei = sum(weth_balances.values())
        total_steth_wei = sum(steth_balances.values())
        
        total_weth_eth = Decimal(str(total_weth_wei)) / Decimal('1e18')
        total_steth_eth = Decimal(str(total_steth_wei)) / Decimal('1e18') * steth_rate
        
        # ============================================
        # STEP 4: MAD ANOMALY DETECTION
        # ============================================
        
        self.logger.info("STEP 4: Running MAD anomaly detection...")
        
        # Calculate balance changes for each whale
        balance_changes = []
        for address in aggregated_current:
            current = aggregated_current[address]
            historical = aggregated_historical.get(address, 0)
            
            if historical > 0:
                change_pct = (current - historical) / historical * 100
                balance_changes.append((address, change_pct))
        
        # Calculate MAD
        if balance_changes:
            changes_only = [c for _, c in balance_changes]
            median_change = Decimal(str(sorted(changes_only)[len(changes_only) // 2]))
            
            deviations = [abs(Decimal(str(c)) - median_change) for c in changes_only]
            mad = sorted(deviations)[len(deviations) // 2] if deviations else Decimal('0')
            
            mad_threshold = mad * 3  # 3×MAD = anomaly threshold
            
            # Find anomaly drivers
            anomalies = [
                (addr, change) for addr, change in balance_changes
                if abs(Decimal(str(change)) - median_change) > mad_threshold
            ]
            
            is_anomaly = len(anomalies) > 0
            top_anomaly_driver = anomalies[0][0] if anomalies else None
            
            self.logger.info(
                f"MAD analysis: median={median_change:.2f}%, MAD={mad:.2f}%, "
                f"threshold={mad_threshold:.2f}%, anomalies={len(anomalies)}"
            )
        else:
            mad_threshold = Decimal('0')
            is_anomaly = False
            top_anomaly_driver = None
        
        # ============================================
        # STEP 5: GINI INDEX (Concentration)
        # ============================================
        
        self.logger.info("STEP 5: Calculating Gini coefficient...")
        
        # ✅ CRITICAL FIX: Filter out RPC errors (None/0) before Gini calculation
        # WHY: None from Multicall gas errors creates artificial concentration
        valid_balances = [
            bal for addr, bal in aggregated_current.items()
            if bal is not None and bal > 0
        ]
        
        num_signals_used = len(valid_balances)
        num_signals_excluded = len(aggregated_current) - num_signals_used
        
        if num_signals_excluded > 0:
            self.logger.warning(
                f"⚠️ Excluded {num_signals_excluded}/{len(aggregated_current)} addresses "
                f"with RPC errors from Gini calculation"
            )
        
        # ✅ GEMINI FIX #8: Normalize to ETH BEFORE Gini (prevent Decimal overflow)
        # WHY: cumsum = sum(i * balance_wei) can reach 10^30 for 1000 whales
        # SOLUTION: Convert Wei → ETH first (Gini is dimensionless, result unchanged)
        # Old: sorted_balances = sorted(valid_balances)  # Wei (10^24)
        # New: sorted_balances = sorted([x / 10^18 for x in valid_balances])  # ETH
        sorted_balances_eth = sorted([
            int(bal) / 10**18 for bal in valid_balances  # Normalize to ETH
        ])
        n = len(sorted_balances_eth)
        
        if n > 0 and sum(sorted_balances_eth) > 0:
            # Gini formula: G = (2 * sum(i * x_i)) / (n * sum(x_i)) - (n + 1) / n
            # ✅ Now uses ETH values (10^6 range) instead of Wei (10^24 range)
            cumsum = sum((i + 1) * x for i, x in enumerate(sorted_balances_eth))
            total_sum = sum(sorted_balances_eth)
            
            gini = (Decimal(str(2 * cumsum)) / Decimal(str(n * total_sum))) - Decimal(n + 1) / Decimal(n)
            gini = abs(gini)  # Ensure positive
        else:
            gini = Decimal('0')
        
        self.logger.info(
            f"Gini coefficient: {gini:.4f} (0=equal, 1=concentrated) "
            f"[{num_signals_used} valid signals]"
        )
        
        # ============================================
        # STEP 6: COUNT ACCUMULATORS/DISTRIBUTORS
        # ============================================
        
        # Count accumulators vs distributors
        accumulators = 0
        distributors = 0
        
        for address in aggregated_current:
            current = aggregated_current[address]
            historical = aggregated_historical.get(address, 0)
            
            if current > historical:
                accumulators += 1
            elif current < historical:
                distributors += 1
        
        # ============================================
        # STEP 7: BUILD METRIC OBJECT
        # ============================================
        
        self.logger.debug(
            f"Metrics: total_current={total_current_eth:.2f} ETH, "
            f"total_historical={total_historical_eth:.2f} ETH, "
            f"change={total_change_eth:+.2f} ETH, "
            f"score={accumulation_score:.2f}%, "
            f"lst_adjusted={lst_adjusted_score:.2f}%, "
            f"accumulators={accumulators}, distributors={distributors}"
        )
        
        return AccumulationMetricCreate(
            token_symbol=token_symbol,
            whale_count=whale_count,
            
            # Native ETH metrics (backward compatibility)
            total_balance_current_wei=str(total_current_wei),
            total_balance_historical_wei=str(total_historical_wei),
            total_balance_change_wei=str(total_change_wei),
            total_balance_current_eth=total_current_eth,
            total_balance_historical_eth=total_historical_eth,
            total_balance_change_eth=total_change_eth,
            accumulation_score=accumulation_score,
            
            # LST-adjusted metrics
            total_weth_balance_eth=total_weth_eth,
            total_steth_balance_eth=total_steth_eth,
            lst_adjusted_score=lst_adjusted_score,
            lst_migration_count=lst_migration_count,
            steth_eth_rate=steth_rate,
            
            # Statistical quality
            concentration_gini=gini,
            num_signals_used=num_signals_used,
            num_signals_excluded=num_signals_excluded,
            is_anomaly=is_anomaly,
            mad_threshold=mad_threshold,
            top_anomaly_driver=top_anomaly_driver,
            
            # Tags (will be assigned in next step)
            tags=[],
            
            # Price context
            price_change_48h_pct=price_change_48h_pct,
            
            # Accumulators/distributors
            accumulators_count=accumulators,
            distributors_count=distributors,
            neutral_count=whale_count - accumulators - distributors,
            
            # Metadata
            current_block_number=current_block,
            historical_block_number=historical_block,
            lookback_hours=self.lookback_hours
        )
    
    async def _detect_lst_migration(
        self,
        addresses: List[str],
        eth_current: Dict[str, int],
        eth_historical: Dict[str, int],
        weth_current: Dict[str, int],
        steth_current: Dict[str, int],
        weth_historical: Dict[str, int],
        steth_historical: Dict[str, int],
        steth_rate: Decimal,
        time_window_hours: int = 1
    ) -> int:
        """
        Detect LST migration (ETH→stETH/WETH without net position change).
        
        WHY: Prevents false "whale dumping" alerts when whales move to staking
        
        LOGIC:
        1. ETH decreased
        2. stETH/WETH increased by similar amount (within gas tolerance)
        3. Net wealth change ≈ 0
        
        CRITICAL FIX (Gemini vulnerability report):
        - All comparisons now in Wei (256-bit int) to avoid float precision loss
        - Calculate CHANGES (delta), not absolute balances
        - Decimal only for stETH rate multiplication
        
        Args:
            addresses: Whale addresses to check
            eth_current/historical: Native ETH balances (Wei)
            weth_current/historical: WETH balances (Wei) 
            steth_current/historical: stETH balances (Wei)
            steth_rate: stETH/ETH exchange rate
            time_window_hours: Time tolerance for migration (default: 1h)
        
        Returns:
            int: Count of whales with detected LST migration
        """
        migration_count = 0
        
        # ✅ CRITICAL: Tolerance in Wei (no float precision loss!)
        gas_tolerance_wei = int(Decimal('0.01') * Decimal('1e18'))  # 0.01 ETH in Wei
        
        for address in addresses:
            # Get balances in Wei
            eth_now_wei = eth_current.get(address, 0) or 0
            eth_before_wei = eth_historical.get(address, 0) or 0
            weth_now_wei = weth_current.get(address, 0) or 0
            weth_before_wei = weth_historical.get(address, 0) or 0
            steth_now_wei = steth_current.get(address, 0) or 0
            steth_before_wei = steth_historical.get(address, 0) or 0
            
            # ✅ CRITICAL FIX: Calculate CHANGES in Wei (not absolute balances!)
            eth_delta_wei = eth_now_wei - eth_before_wei
            weth_delta_wei = weth_now_wei - weth_before_wei
            
            # stETH conversion with Decimal precision, then back to Wei
            steth_now_eth_wei = int(Decimal(str(steth_now_wei)) * steth_rate)
            steth_before_eth_wei = int(Decimal(str(steth_before_wei)) * steth_rate)
            steth_delta_wei = steth_now_eth_wei - steth_before_eth_wei
            
            # Total wealth change (in Wei!)
            total_delta_wei = eth_delta_wei + weth_delta_wei + steth_delta_wei
            
            # ✅ CRITICAL: All comparisons in Wei (256-bit int, no float!)
            # GEMINI FIX #6: Detect ANY LST swap with net≈0 ("Empty Delta Attack" fix)
            # WHY: Catches swaps from empty wallets (stETH↔WETH without ETH)
            # OLD: eth_delta < 0 (missed 0 ETH → WETH/stETH swaps)
            # NEW: abs(total_delta) < tolerance (catches ALL neutral swaps)
            
            # Check if ANY two assets changed (ETH, WETH, or stETH)
            has_movement = (
                abs(eth_delta_wei) > 0 or 
                abs(weth_delta_wei) > 0 or 
                abs(steth_delta_wei) > 0
            )
            
            # Migration pattern: ANY asset movement with net wealth ≈ 0
            if has_movement and abs(total_delta_wei) < gas_tolerance_wei:
                
                migration_count += 1
                
                # Display conversion (only for logging, NOT for logic!)
                self.logger.info(
                    f"LST Migration detected for {address[:10]}... "
                    f"(ETH: {Decimal(eth_delta_wei)/Decimal('1e18'):+.4f}, "
                    f"WETH: {Decimal(weth_delta_wei)/Decimal('1e18'):+.4f}, "
                    f"stETH: {Decimal(steth_delta_wei)/Decimal('1e18'):+.4f} → "
                    f"net: {Decimal(total_delta_wei)/Decimal('1e18'):+.4f})"
                )
        
        if migration_count > 0:
            self.logger.info(
                f"🔄 Detected {migration_count} LST migrations "
                f"(ETH→stETH/WETH without position change)"
            )
        
        return migration_count
    
    async def _detect_looping_pattern(
        self,
        addresses: List[str],
        weth_balances: Dict[str, int],
        steth_balances: Dict[str, int],
        network: str = "ethereum"
    ) -> int:
        """
        Detect potential DeFi looping patterns via Nonce analysis.
        
        WHY (GEMINI PROPOSAL):
        - DeFi looping (stake → borrow → buy more) happens in rapid sequences
        - Nonce tracker can identify scripted multi-step transactions
        
        LOGIC:
        1. Check if whale has significant stETH/WETH
        2. Query recent nonce sequence from NonceTracker
        3. Detect rapid sequential transactions (< 1h window)
        4. Flag as "Technical Activity" if pattern found
        
        MVP IMPLEMENTATION:
        - Simple counter for whales with large LST holdings
        - TODO Phase 3: Full NonceTracker integration for sequence analysis
        
        Args:
            addresses: Whale addresses to check
            weth_balances: Current WETH balances
            steth_balances: Current stETH balances
            network: Network name
        
        Returns:
            int: Count of whales with suspected looping patterns
        """
        looping_suspects = 0
        
        # MVP: Simple heuristic - flag whales with >100 ETH in LSTs
        # (likely to be using leverage strategies)
        lst_threshold_wei = int(Decimal('100') * Decimal('1e18'))  # 100 ETH
        
        for address in addresses:
            weth_wei = weth_balances.get(address, 0) or 0
            steth_wei = steth_balances.get(address, 0) or 0
            total_lst_wei = weth_wei + steth_wei
            
            if total_lst_wei > lst_threshold_wei:
                looping_suspects += 1
                self.logger.debug(
                    f"Looping suspect: {address[:10]}... "
                    f"({Decimal(total_lst_wei)/Decimal('1e18'):.2f} ETH in LSTs)"
                )
        
        if looping_suspects > 0:
            self.logger.info(
                f"🔄 Detected {looping_suspects} potential DeFi looping addresses "
                f"(>100 ETH in WETH/stETH - MVP heuristic)"
            )
        
        return looping_suspects
    
    def _assign_tags(
        self,
        metric: AccumulationMetricCreate,
        whale_count: int,
        looping_suspect_count: int = 0,  # ✅ GEMINI
        snapshot_density_valid: bool = True,  # ✅ GEMINI FIX #7
        snapshot_coverage_pct: float = 100.0  # ✅ GEMINI FIX #7
    ) -> List[str]:
        """
        Assign diagnostic tags based on metric analysis.
        
        WHY: Transforms raw numbers into actionable market insights
        
        VULNERABILITY FIX #4:
        - Check num_signals_used before assigning tags
        - Minimum 70% valid signals required (protects against RPC errors)
        
        GEMINI FIX #5 (Phase 2 Looping Defense):
        - Filter out stETH-dominated signals (likely leverage)
        - Downgrade confidence during depeg (margin call risk)
        - Flag high-LST addresses as technical activity
        
        TAGS:
        - [Organic Accumulation]: 25%+ whales accumulating
        - [Concentrated Signal]: Gini > 0.85 (one whale dominates)
        - [Bullish Divergence]: +score during -price (48-72h window)
        - [LST Migration]: Detected ETH→stETH/WETH within 1h
        - [High Conviction]: Score > historical MAD threshold, not anomaly
        - [Technical Activity]: stETH-driven OR high LST concentration
        - [Anomaly Alert]: Single whale driving score (MAD outlier)
        - [Depeg Risk]: stETH < 0.98 ETH (liquidation danger)
        """
        tags = []
        
        # ✅ GEMINI FIX #7: Check snapshot density FIRST (blocks all other tags)
        if not snapshot_density_valid:
            tags.append("Incomplete Data")
            self.logger.error(
                f"❌ INCOMPLETE DATA: Snapshot coverage {snapshot_coverage_pct:.1f}% < 85% required. "
                f"NO TAGS ASSIGNED to prevent false signals from incomplete history."
            )
            return tags  # Early return - no other tags
        
        # ✅ CRITICAL: Check data quality before assigning tags
        min_signals_pct = 0.70  # Require 70% valid signals
        min_signals_required = int(whale_count * min_signals_pct)
        
        if metric.num_signals_used < min_signals_required:
            self.logger.error(
                f"❌ INSUFFICIENT DATA QUALITY: Only {metric.num_signals_used}/{whale_count} "
                f"valid signals ({metric.num_signals_used/whale_count*100:.1f}%), "
                f"required {min_signals_pct*100:.0f}%. "
                f"RPC errors: {metric.num_signals_excluded}. "
                f"NO TAGS ASSIGNED to prevent false signals."
            )
            tags.append("Insufficient Data")
            return tags
        
        # [Organic Accumulation]
        if metric.accumulators_count > whale_count * 0.25:
            tags.append("Organic Accumulation")
            self.logger.debug(
                f"Tag: [Organic Accumulation] - {metric.accumulators_count}/{whale_count} whales accumulating"
            )
        
        # [Concentrated Signal]
        if metric.concentration_gini and metric.concentration_gini > Decimal('0.85'):
            tags.append("Concentrated Signal")
            self.logger.debug(
                f"Tag: [Concentrated Signal] - Gini={metric.concentration_gini:.3f} (high inequality)"
            )
        
        # [Bullish Divergence] - FIXED: Use percentage score, not absolute balance
        if (metric.price_change_48h_pct and 
            metric.price_change_48h_pct < Decimal('-2.0') and
            metric.accumulation_score and metric.accumulation_score > Decimal('0.2')):
            tags.append("Bullish Divergence")
            self.logger.debug(
                f"Tag: [Bullish Divergence] - Accumulation +{metric.accumulation_score:.2f}% "
                f"while price dropped {metric.price_change_48h_pct:.2f}% (alpha signal)"
            )
        
        # [LST Migration]
        if metric.lst_migration_count > 0:
            tags.append("LST Migration")
            self.logger.debug(
                f"Tag: [LST Migration] - {metric.lst_migration_count} whales migrated to staking"
            )
        
        # [High Conviction] - FIXED: Use 3×MAD threshold for statistical significance
        # GEMINI FIX: Filter out stETH-driven anomalies (potential DeFi looping)
        if (metric.lst_adjusted_score and 
            metric.mad_threshold and 
            metric.lst_adjusted_score > (metric.mad_threshold * Decimal('3')) and
            not metric.is_anomaly):
            
            # ✅ GEMINI: Check if signal driven by stETH anomaly (looping suspect)
            steth_dominates = (
                metric.total_steth_balance_eth and 
                metric.total_balance_change_eth and
                abs(metric.total_steth_balance_eth) > abs(metric.total_balance_change_eth) * Decimal('0.7')
            )
            
            if steth_dominates:
                tags.append("Technical Activity")
                self.logger.warning(
                    f"Tag: [Technical Activity] - Score driven by stETH ({metric.total_steth_balance_eth:.2f} ETH), "
                    f"likely DeFi looping rather than organic accumulation"
                )
            else:
                tags.append("High Conviction")
                self.logger.debug(
                    f"Tag: [High Conviction] - Score {metric.lst_adjusted_score:.4f}% "
                    f"exceeds 3×MAD threshold ({metric.mad_threshold * 3:.4f}%), no anomaly"
                )
        
        # [Depeg Risk] - CRITICAL: stETH depeg detection for liquidation protection
        # GEMINI FIX: Downgrade ALL accumulation signals during depeg (liquidation risk)
        if metric.steth_eth_rate and metric.steth_eth_rate < Decimal('0.98'):
            tags.append("Depeg Risk")
            
            # ✅ GEMINI: Remove "High Conviction" if depeg active
            if "High Conviction" in tags:
                tags.remove("High Conviction")
                self.logger.warning(
                    f"⚠️ Depeg detected: Downgraded 'High Conviction' to avoid false signal "
                    f"(stETH @ {metric.steth_eth_rate:.4f} ETH, may be margin call defense)"
                )
            
            self.logger.warning(
                f"Tag: [Depeg Risk] - stETH trading at {metric.steth_eth_rate:.4f} ETH "
                f"(< 0.98 threshold, liquidation risk in lending protocols)"
            )
        
        # [Anomaly Alert]
        if metric.is_anomaly:
            tags.append("Anomaly Alert")
            self.logger.warning(
                f"Tag: [Anomaly Alert] - Score driven by outlier whale: {metric.top_anomaly_driver}"
            )
        
        # [Looping Suspects] - GEMINI FIX: Flag addresses with high LST concentration
        if looping_suspect_count > whale_count * 0.10:  # >10% of whales
            if "Technical Activity" not in tags:  # Don't duplicate
                tags.append("Technical Activity")
            self.logger.info(
                f"Tag: [Technical Activity] - {looping_suspect_count}/{whale_count} whales "
                f"have >100 ETH in LSTs (potential DeFi looping)"
            )
        
        return tags
    
    def _format_professional_report(
        self,
        metric: AccumulationMetric,
        snapshot_density_valid: bool = True,
        snapshot_coverage_pct: float = 100.0
    ) -> str:
        """
        Generate Twitter-ready professional report with semantic tags.
        
        WHY: Transform technical metrics into actionable market insights
        AUDIENCE: Crypto traders seeking alpha signals
        STYLE: Cyberpunk analytics with emoji indicators
        
        Args:
            metric: AccumulationMetric with calculated scores and tags
            snapshot_density_valid: Whether snapshot coverage is sufficient
            snapshot_coverage_pct: Actual snapshot coverage percentage
        
        Returns:
            Formatted report string with emoji indicators and semantic explanations
        """
        report_lines = []
        
        # Header - Cyberpunk style
        report_lines.append("=" * 60)
        report_lines.append("📊 COLLECTIVE WHALE ANALYSIS REPORT")
        report_lines.append("=" * 60)
        
        # Core metrics
        report_lines.append(f"\n🎯 ACCUMULATION SCORE: {metric.lst_adjusted_score:+.2f}%")
        report_lines.append(
            f"   └─ {metric.whale_count} whales analyzed "
            f"({metric.num_signals_used} valid signals)"
        )
        report_lines.append(
            f"   └─ Net balance change: {metric.total_balance_change_eth:+,.2f} ETH"
        )
        
        # Semantic tags with explanations
        if metric.tags:
            report_lines.append(f"\n🏷️  MARKET SIGNALS:")
            
            for tag in metric.tags:
                if tag == "Organic Accumulation":
                    report_lines.append(
                        f"   [✓] {tag}: {metric.accumulators_count}/{metric.whale_count} "
                        f"whales buying (distributed accumulation, not manipulation)"
                    )
                
                elif tag == "High Conviction":
                    mad_3x = metric.mad_threshold * Decimal('3') if metric.mad_threshold else Decimal('0')
                    report_lines.append(
                        f"   [✓] {tag}: Score exceeds 3×MAD threshold "
                        f"({mad_3x:.2f}% - statistically significant movement)"
                    )
                
                elif tag == "Bullish Divergence":
                    report_lines.append(
                        f"   [⚡] {tag}: Whales accumulating +{metric.accumulation_score:.2f}% "
                        f"while price dropped {metric.price_change_48h_pct:.2f}% "
                        f"(alpha signal - smart money buying dip)"
                    )
                
                elif tag == "LST Migration":
                    report_lines.append(
                        f"   [🔄] {tag}: {metric.lst_migration_count} whales moved to staking "
                        f"(NOT a dump - capital locked in yield strategies)"
                    )
                
                elif tag == "Depeg Risk":
                    report_lines.append(
                        f"   [⚠️] {tag}: stETH trading at {metric.steth_eth_rate:.4f} ETH "
                        f"(< 0.98 depeg threshold - liquidation cascade risk in lending protocols)"
                    )
                
                elif tag == "Concentrated Signal":
                    report_lines.append(
                        f"   [⚠️] {tag}: Gini={metric.concentration_gini:.3f} "
                        f"(> 0.85 - single whale dominates, potential manipulation)"
                    )
                
                elif tag == "Anomaly Alert":
                    driver_display = metric.top_anomaly_driver[:10] + "..." if metric.top_anomaly_driver else "unknown"
                    report_lines.append(
                        f"   [🚨] {tag}: Movement driven by outlier whale "
                        f"({driver_display} - not organic market sentiment)"
                    )
                
                elif tag == "Technical Activity":
                    report_lines.append(
                        f"   [🔧] {tag}: Signal driven by stETH/WETH movements "
                        f"(likely DeFi looping or leverage strategies, not spot accumulation)"
                    )
                
                elif tag == "Insufficient Data":
                    report_lines.append(
                        f"   [❌] {tag}: Only {metric.num_signals_used}/{metric.whale_count} valid signals "
                        f"({metric.num_signals_excluded} RPC errors - IGNORE THIS SIGNAL)"
                    )
                
                elif tag == "Incomplete Data":
                    report_lines.append(
                        f"   [❌] {tag}: Snapshot coverage {snapshot_coverage_pct:.1f}% < 85% required "
                        f"(insufficient historical data - IGNORE THIS SIGNAL)"
                    )
        
        # Statistical context - for advanced traders
        report_lines.append(f"\n📈 STATISTICAL CONTEXT:")
        report_lines.append(
            f"   • Concentration (Gini): {metric.concentration_gini:.4f} "
            f"(0=equal, 1=concentrated)"
        )
        if metric.mad_threshold:
            mad_3x = metric.mad_threshold * Decimal('3')
            report_lines.append(
                f"   • MAD Threshold: {metric.mad_threshold:.2f}% "
                f"(3×MAD = {mad_3x:.2f}% for High Conviction)"
            )
        if metric.price_change_48h_pct is not None:
            report_lines.append(f"   • Price Change (48h): {metric.price_change_48h_pct:+.2f}%")
        
        # LST breakdown - shows real vs apparent wealth
        report_lines.append(f"\n💎 LST BREAKDOWN:")
        report_lines.append(
            f"   • Native ETH: {metric.total_balance_change_eth:+,.2f} ETH"
        )
        report_lines.append(
            f"   • WETH: {metric.total_weth_balance_eth:,.2f} ETH"
        )
        report_lines.append(
            f"   • stETH: {metric.total_steth_balance_eth:,.2f} ETH "
            f"(@ {metric.steth_eth_rate:.4f} rate)"
        )
        report_lines.append(
            f"   • LST-Adjusted Score: {metric.lst_adjusted_score:+.2f}%"
        )
        
        # Action recommendation - the "so what?"
        report_lines.append(f"\n💡 INTERPRETATION:")
        
        if "Insufficient Data" in metric.tags or "Incomplete Data" in metric.tags:
            report_lines.append(
                "   → ⚠️ DATA QUALITY ISSUE: Do not trade on this signal"
            )
        elif "Bullish Divergence" in metric.tags:
            report_lines.append(
                "   → Smart money is accumulating during price weakness "
                "(classic alpha setup)"
            )
        elif "High Conviction" in metric.tags and metric.lst_adjusted_score > 0:
            report_lines.append(
                "   → Strong accumulation signal with statistical significance"
            )
        elif "LST Migration" in metric.tags:
            report_lines.append(
                "   → Capital flowing to staking "
                "(long-term bullish, not immediate sell pressure)"
            )
        elif "Depeg Risk" in metric.tags:
            report_lines.append(
                "   → CAUTION: Movements may be liquidation defense, not accumulation"
            )
        elif "Anomaly Alert" in metric.tags or "Concentrated Signal" in metric.tags:
            report_lines.append(
                "   → NOISE: Single whale activity, not broad market sentiment"
            )
        else:
            report_lines.append(
                "   → Neutral - no strong directional signal"
            )
        
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
    
    async def get_latest_score(
        self,
        token_symbol: str = "ETH"
    ) -> Optional[AccumulationMetric]:
        """
        Get most recent accumulation score from database.
        
        Args:
            token_symbol: Token symbol (default: "ETH")
        
        Returns:
            AccumulationMetric: Latest score or None if not found
        """
        metrics = await self.repository.get_recent_metrics(
            token_symbol=token_symbol,
            limit=1
        )
        
        return metrics[0] if metrics else None
    
    async def get_score_history(
        self,
        token_symbol: str = "ETH",
        limit: int = 24
    ) -> List[AccumulationMetric]:
        """
        Get historical accumulation scores.
        
        Args:
            token_symbol: Token symbol (default: "ETH")
            limit: Number of recent scores to return (default: 24)
        
        Returns:
            List[AccumulationMetric]: Recent scores (newest first)
        """
        return await self.repository.get_recent_metrics(
            token_symbol=token_symbol,
            limit=limit
        )
    
    async def health_check(self) -> Dict:
        """
        Check if AccumulationScoreCalculator is working properly.
        
        Returns:
            Dict: Health status
        """
        try:
            # Check whale provider
            whale_health = await self.whale_provider.health_check()
            if whale_health["status"] != "healthy":
                return {
                    "status": "unhealthy",
                    "error": "WhaleListProvider unhealthy"
                }
            
            # Check multicall client
            multicall_health = await self.multicall_client.health_check()
            if multicall_health["status"] != "healthy":
                return {
                    "status": "unhealthy",
                    "error": "MulticallClient unhealthy"
                }
            
            # Check database connection
            recent_metrics = await self.repository.get_recent_metrics(limit=1)
            
            return {
                "status": "healthy",
                "whale_provider": "ok",
                "multicall_client": "ok",
                "database": "ok",
                "recent_metrics": len(recent_metrics),
                "lookback_hours": self.lookback_hours
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
