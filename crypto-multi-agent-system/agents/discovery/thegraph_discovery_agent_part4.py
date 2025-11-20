"""
TheGraph Discovery Agent - Часть 4: Data Transformation to TokenDiscoveryReport
Преобразует сырые данные The Graph в стандартный формат системы
Обеспечивает совместимость с существующим оркестратором

Author: Integration layer for production system compatibility
Version: 1.0 - Part 4 (Data Transformation)
"""

import os
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass

# Import Part 3 and base models
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.discovery.thegraph_discovery_agent_part3 import (
    TheGraphDiscoveryAgentV3, 
    PaginationResult
)
from agents.discovery.discovery_models import TokenDiscoveryReport


@dataclass
class DiscoverySession:
    """Represents a complete discovery session across all subgraphs and time slices."""
    
    session_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_operations: int = 0
    completed_operations: int = 0
    pagination_results: List[PaginationResult] = None
    discovery_reports: List[TokenDiscoveryReport] = None
    session_stats: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.pagination_results is None:
            self.pagination_results = []
        if self.discovery_reports is None:
            self.discovery_reports = []
        if self.session_stats is None:
            self.session_stats = {}


class TheGraphDiscoveryAgentV4(TheGraphDiscoveryAgentV3):
    """
    Final version with data transformation to TokenDiscoveryReport.
    
    This completes the integration with the existing system:
    - Takes raw pagination results from Part 3
    - Transforms to standard TokenDiscoveryReport format
    - Applies discovery scoring logic
    - Provides session management for tracking progress
    """
    
    def __init__(self, config=None):
        """Initialize with data transformation capability."""
        super().__init__(config)
        
        # Session management
        self.current_session: Optional[DiscoverySession] = None
        
        # Transformation stats
        self.transformation_stats = {
            "total_raw_pairs": 0,
            "total_transformed_reports": 0,
            "transformation_errors": 0,
            "average_transformation_time_ms": 0.0
        }
    
    def transform_raw_pair_to_discovery_report(
        self, 
        raw_pair: Dict[str, Any], 
        pagination_result: PaginationResult
    ) -> Optional[TokenDiscoveryReport]:
        """
        Transform raw pair data from The Graph into TokenDiscoveryReport.
        
        This is the integration layer that makes The Graph data compatible
        with the existing discovery system.
        
        Args:
            raw_pair: Raw pair data from The Graph
            pagination_result: Context from pagination
            
        Returns:
            TokenDiscoveryReport or None if transformation fails
        """
        try:
            transform_start = time.time()
            
            # Extract basic pair information
            pair_address = raw_pair.get('pair_address', '')
            base_token_address = raw_pair.get('base_token_address', '')
            base_token_symbol = raw_pair.get('base_token_symbol', '')
            base_token_name = raw_pair.get('base_token_name', '')
            
            # Financial metrics
            liquidity_usd = float(raw_pair.get('liquidity_usd', 0))
            volume_usd = float(raw_pair.get('volume_usd', 0))
            
            # Time information
            created_at_timestamp = int(raw_pair.get('created_at_timestamp', 0))
            if created_at_timestamp > 0:
                pair_created_at = datetime.fromtimestamp(created_at_timestamp)
                age_minutes = (datetime.now() - pair_created_at).total_seconds() / 60
            else:
                # Fallback to slice information
                pair_created_at = pagination_result.time_slice.start_date
                age_minutes = (datetime.now() - pair_created_at).total_seconds() / 60
            
            # Chain ID mapping
            chain_id_mapping = {
                "ethereum": "ethereum",
                "bsc": "bsc", 
                "polygon": "polygon",
                "arbitrum": "arbitrum"
            }
            chain_id = chain_id_mapping.get(raw_pair.get('blockchain', ''), 'ethereum')
            
            # Calculate discovery score based on The Graph criteria
            discovery_score = self._calculate_thegraph_discovery_score(
                liquidity_usd=liquidity_usd,
                volume_usd=volume_usd,
                age_minutes=age_minutes,
                subgraph_name=pagination_result.subgraph_name,
                raw_pair=raw_pair
            )
            
            # Generate discovery reasoning
            discovery_reason = self._generate_discovery_reasoning(
                score=discovery_score,
                liquidity_usd=liquidity_usd,
                volume_usd=volume_usd,
                age_minutes=age_minutes,
                subgraph_name=pagination_result.subgraph_name
            )
            
            # Create TokenDiscoveryReport
            report = TokenDiscoveryReport(
                pair_address=pair_address,
                chain_id=chain_id,
                base_token_address=base_token_address,
                base_token_symbol=base_token_symbol,
                base_token_name=base_token_name,
                liquidity_usd=liquidity_usd,
                volume_h24=volume_usd,  # Map volume_usd to volume_h24
                price_usd=0.0,  # The Graph doesn't provide current price
                price_change_h1=0.0,  # The Graph doesn't provide price changes
                pair_created_at=pair_created_at,
                age_minutes=age_minutes,
                discovery_score=discovery_score,
                discovery_reason=discovery_reason,
                data_source=f"TheGraph-{pagination_result.subgraph_name}",
                discovery_timestamp=datetime.now(),
                api_response_time_ms=pagination_result.duration_seconds * 1000
            )
            
            # Update transformation stats
            transform_duration = (time.time() - transform_start) * 1000
            self.transformation_stats["total_transformed_reports"] += 1
            
            # Update average transformation time
            current_avg = self.transformation_stats["average_transformation_time_ms"]
            total_reports = self.transformation_stats["total_transformed_reports"]
            self.transformation_stats["average_transformation_time_ms"] = (
                (current_avg * (total_reports - 1) + transform_duration) / total_reports
            )
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to transform pair data: {e}")
            self.transformation_stats["transformation_errors"] += 1
            return None
    
    def _calculate_thegraph_discovery_score(
        self, 
        liquidity_usd: float,
        volume_usd: float,
        age_minutes: float,
        subgraph_name: str,
        raw_pair: Dict[str, Any]
    ) -> int:
        """
        Calculate discovery score based on The Graph specific criteria.
        
        The Graph provides different data than DexScreener, so we need
        adapted scoring logic focused on:
        - Liquidity levels (proxy for legitimacy)
        - Age within target range (45-75 days is optimal)
        - Source reliability (Uniswap V2 > SushiSwap > others)
        """
        score = 50  # Base score
        
        # Liquidity scoring (0-25 points)
        if liquidity_usd >= 100000:  # $100k+
            score += 25
        elif liquidity_usd >= 50000:  # $50k+
            score += 20
        elif liquidity_usd >= 20000:  # $20k+
            score += 15
        elif liquidity_usd >= 10000:  # $10k+
            score += 10
        elif liquidity_usd >= 5000:   # $5k+
            score += 5
        # Below $5k gets 0 bonus points
        
        # Age scoring (0-15 points) - prefer middle of target range
        age_days = age_minutes / (24 * 60)
        if 55 <= age_days <= 65:  # Sweet spot: 55-65 days
            score += 15
        elif 50 <= age_days <= 70:  # Good range: 50-70 days
            score += 10
        elif 45 <= age_days <= 75:  # Acceptable: full target range
            score += 5
        # Outside target range gets 0 points
        
        # Volume scoring (0-10 points) - if available
        if volume_usd > 0:
            volume_to_liquidity_ratio = volume_usd / max(liquidity_usd, 1)
            if volume_to_liquidity_ratio >= 1.0:  # High activity
                score += 10
            elif volume_to_liquidity_ratio >= 0.5:  # Moderate activity
                score += 7
            elif volume_to_liquidity_ratio >= 0.1:  # Some activity
                score += 3
        
        # Source reliability bonus (0-10 points)
        source_bonuses = {
            "Uniswap V2": 10,      # Most reliable
            "Uniswap V3": 8,       # Also very reliable
            "SushiSwap": 5,        # Less volume but working
            "PancakeSwap V2": 3    # BSC, lower reliability
        }
        score += source_bonuses.get(subgraph_name, 0)
        
        # Ensure score stays within bounds
        return max(0, min(100, score))
    
    def _generate_discovery_reasoning(
        self,
        score: int,
        liquidity_usd: float,
        volume_usd: float,
        age_minutes: float,
        subgraph_name: str
    ) -> str:
        """Generate human-readable reasoning for discovery score."""
        age_days = age_minutes / (24 * 60)
        
        reasons = []
        
        # Age assessment
        if 55 <= age_days <= 65:
            reasons.append(f"Optimal age ({age_days:.0f} days - prime for movement)")
        elif 45 <= age_days <= 75:
            reasons.append(f"Target age range ({age_days:.0f} days)")
        else:
            reasons.append(f"Age {age_days:.0f} days outside target")
        
        # Liquidity assessment
        if liquidity_usd >= 50000:
            reasons.append(f"Strong liquidity (${liquidity_usd:,.0f})")
        elif liquidity_usd >= 10000:
            reasons.append(f"Adequate liquidity (${liquidity_usd:,.0f})")
        else:
            reasons.append(f"Low liquidity (${liquidity_usd:,.0f})")
        
        # Volume assessment (if available)
        if volume_usd > 0:
            volume_ratio = volume_usd / max(liquidity_usd, 1)
            if volume_ratio >= 0.5:
                reasons.append(f"Active trading (V/L ratio: {volume_ratio:.2f})")
            else:
                reasons.append(f"Low activity (V/L ratio: {volume_ratio:.2f})")
        
        # Source note
        reasons.append(f"Source: {subgraph_name}")
        
        return "; ".join(reasons)
    
    async def discover_tokens_full_pipeline(self) -> DiscoverySession:
        """
        Execute full discovery pipeline: temporal slicing → pagination → transformation.
        
        This is the complete pipeline that replaces DexScreener:
        1. Generate time slices (Part 2)
        2. Paginate through each subgraph/slice combination (Part 3)  
        3. Transform raw data to TokenDiscoveryReport (Part 4)
        4. Return session with all results
        
        Returns:
            DiscoverySession with complete results
        """
        session_start = datetime.now()
        session_id = f"thegraph_discovery_{session_start.strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize session
        active_subgraphs = self.get_active_subgraphs()
        time_slices = self.generate_time_slices()
        total_operations = len(active_subgraphs) * len(time_slices)
        
        session = DiscoverySession(
            session_id=session_id,
            start_time=session_start,
            total_operations=total_operations
        )
        
        self.current_session = session
        self.logger.info(
            f"Starting discovery session {session_id}: "
            f"{len(active_subgraphs)} subgraphs × {len(time_slices)} slices = {total_operations} operations"
        )
        
        # Execute pagination for each subgraph/slice combination
        all_pagination_results = []
        all_discovery_reports = []
        
        for subgraph in active_subgraphs:
            for time_slice in time_slices:
                try:
                    # Execute pagination
                    pagination_result = await self.fetch_all_pairs_in_slice(subgraph, time_slice)
                    all_pagination_results.append(pagination_result)
                    
                    # Transform raw pairs to discovery reports
                    if pagination_result.success:
                        for raw_pair in pagination_result.pairs_collected:
                            report = self.transform_raw_pair_to_discovery_report(raw_pair, pagination_result)
                            if report:
                                all_discovery_reports.append(report)
                    
                    session.completed_operations += 1
                    
                    self.logger.info(
                        f"Session progress: {session.completed_operations}/{session.total_operations} "
                        f"({(session.completed_operations/session.total_operations)*100:.1f}%)"
                    )
                    
                except Exception as e:
                    self.logger.error(f"Failed operation {subgraph.name} × Slice {time_slice.slice_number}: {e}")
                    session.completed_operations += 1
        
        # Finalize session
        session.end_time = datetime.now()
        session.pagination_results = all_pagination_results
        session.discovery_reports = all_discovery_reports
        session.session_stats = self._calculate_session_stats(session)
        
        self.logger.info(
            f"Discovery session {session_id} complete: "
            f"{len(all_discovery_reports)} reports generated in "
            f"{(session.end_time - session.start_time).total_seconds():.1f}s"
        )
        
        return session
    
    def _calculate_session_stats(self, session: DiscoverySession) -> Dict[str, Any]:
        """Calculate comprehensive session statistics."""
        successful_operations = sum(1 for r in session.pagination_results if r.success)
        total_pairs = sum(r.total_pairs for r in session.pagination_results)
        total_requests = sum(r.total_requests for r in session.pagination_results)
        
        # Group by subgraph
        subgraph_stats = {}
        for result in session.pagination_results:
            if result.subgraph_name not in subgraph_stats:
                subgraph_stats[result.subgraph_name] = {
                    "operations": 0,
                    "successful_operations": 0,
                    "total_pairs": 0,
                    "total_requests": 0
                }
            
            stats = subgraph_stats[result.subgraph_name]
            stats["operations"] += 1
            if result.success:
                stats["successful_operations"] += 1
            stats["total_pairs"] += result.total_pairs
            stats["total_requests"] += result.total_requests
        
        return {
            "total_operations": session.total_operations,
            "completed_operations": session.completed_operations,
            "successful_operations": successful_operations,
            "success_rate": (successful_operations / session.total_operations) * 100,
            "total_pairs_collected": total_pairs,
            "total_discovery_reports": len(session.discovery_reports),
            "total_api_requests": total_requests,
            "session_duration_seconds": (session.end_time - session.start_time).total_seconds(),
            "subgraph_breakdown": subgraph_stats,
            "transformation_stats": self.transformation_stats.copy(),
            "pagination_stats": self.get_pagination_stats()
        }
    
    def get_transformation_stats(self) -> Dict[str, Any]:
        """Get current transformation statistics."""
        return self.transformation_stats.copy()


# === ЧАСТЬ 4 ЗАВЕРШЕНА ===
# Реализованная функциональность:
# - Трансформация сырых данных в TokenDiscoveryReport
# - Адаптированный scoring для The Graph данных
# - Полный пайплайн от временных срезов до финальных отчетов
# - Сессионное управление с детальной статистикой
# - Готовность к интеграции с оркестратором

if __name__ == "__main__":
    # Test Part 4 data transformation (dry run)
    async def test_transformation():
        try:
            agent = TheGraphDiscoveryAgentV4()
            
            print(f"Part 4 Data Transformation successful")
            print(f"   Agent initialized with {len(agent.get_active_subgraphs())} subgraphs")
            
            # Test transformation with mock data
            mock_raw_pair = {
                'pair_address': '0x1234...5678',
                'base_token_address': '0xabcd...ef00',
                'base_token_symbol': 'TEST',
                'base_token_name': 'Test Token',
                'liquidity_usd': 25000.0,
                'volume_usd': 5000.0,
                'created_at_timestamp': int((datetime.now() - timedelta(days=60)).timestamp()),
                'blockchain': 'ethereum'
            }
            
            # Mock pagination result
            from agents.discovery.thegraph_discovery_agent_part2 import TimeSlice
            mock_time_slice = TimeSlice(1, 45, 50, 0, 0, datetime.now(), datetime.now())
            mock_pagination_result = PaginationResult(
                subgraph_name="Uniswap V2",
                time_slice=mock_time_slice,
                pairs_collected=[],
                total_pairs=1,
                total_pages=1,
                total_requests=1,
                success=True,
                duration_seconds=1.0
            )
            
            # Test transformation
            report = agent.transform_raw_pair_to_discovery_report(mock_raw_pair, mock_pagination_result)
            
            if report:
                print(f"   Transformation test successful:")
                print(f"      Token: {report.base_token_symbol} ({report.base_token_name})")
                print(f"      Liquidity: ${report.liquidity_usd:,.0f}")
                print(f"      Age: {report.age_minutes/1440:.1f} days")
                print(f"      Score: {report.discovery_score}/100")
                print(f"      Reason: {report.discovery_reason}")
                print(f"      Data source: {report.data_source}")
            
            # Show transformation stats
            stats = agent.get_transformation_stats()
            print(f"   Transformation stats: {stats}")
            
            print(f"\n   Ready for Part 5: Integration with orchestrator")
            
        except Exception as e:
            print(f"Part 4 error: {e}")
            import traceback
            traceback.print_exc()
    
    # Run async test
    asyncio.run(test_transformation())
