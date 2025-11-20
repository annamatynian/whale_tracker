"""
TheGraph Discovery Agent - Часть 3: Pagination Implementation
Реализует проверенную пагинацию для сбора ВСЕХ пар из каждого временного среза
Это логика, которая обеспечила прорыв: 60 → 572 пары

Author: Production pagination logic based on proven prototype results
Version: 1.0 - Part 3 (Pagination)
"""

import os
import asyncio
import logging
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass

# Import Part 2
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from agents.discovery.thegraph_discovery_agent_part2 import (
    TheGraphDiscoveryAgentV2, 
    TimeSlice
)
from agents.discovery.thegraph_discovery_agent_refactored import (
    SubgraphConfig, 
    create_dex_adapter
)


@dataclass
class PaginationResult:
    """Result of paginated data collection from a single subgraph slice."""
    
    subgraph_name: str
    time_slice: TimeSlice
    pairs_collected: List[Dict[str, Any]]
    total_pairs: int
    total_pages: int
    total_requests: int
    success: bool
    error_message: Optional[str] = None
    duration_seconds: float = 0.0
    
    def __str__(self) -> str:
        status = "SUCCESS" if self.success else f"FAILED: {self.error_message}"
        return f"{self.subgraph_name} Slice {self.time_slice.slice_number}: {self.total_pairs} pairs, {self.total_pages} pages ({status})"


class TheGraphDiscoveryAgentV3(TheGraphDiscoveryAgentV2):
    """
    Extended version with full pagination implementation.
    
    This implements the CORE logic that achieved the breakthrough:
    - 60 pairs (original first: 10 limit) → 572 pairs (full pagination)
    - Pagination with skip parameter to get ALL data
    - Rate limiting to respect API limits
    - Robust error handling for production use
    """
    
    def __init__(self, config=None):
        """Initialize with pagination capability."""
        super().__init__(config)
        
        # Pagination statistics
        self.pagination_stats = {
            "total_requests_made": 0,
            "total_pairs_collected": 0,
            "total_pages_processed": 0,
            "failed_requests": 0,
            "average_response_time_ms": 0.0
        }
    
    def _build_subgraph_url(self, subgraph_id: str) -> str:
        """Build complete subgraph URL from ID."""
        return f"{self.config.graph_gateway_base}/{self.config.graph_api_key}/subgraphs/id/{subgraph_id}"
    
    async def fetch_all_pairs_in_slice(
        self, 
        subgraph: SubgraphConfig, 
        time_slice: TimeSlice
    ) -> PaginationResult:
        """
        Collect ALL pairs in a time slice using pagination.
        
        This is the PROVEN logic from our 572-pair prototype:
        - Start with skip=0, first=1000
        - Keep incrementing skip by 1000 until no more results
        - Collect all pages into single result set
        - Respect rate limits between requests
        
        Args:
            subgraph: Subgraph configuration
            time_slice: Time slice to query
            
        Returns:
            PaginationResult with all collected pairs
        """
        start_time = time.time()
        
        # Get DEX adapter for query building
        adapter = create_dex_adapter(subgraph.dex_type)
        
        # Build GraphQL query using adapter
        query_template = adapter.build_pairs_query(subgraph.liquidity_threshold_usd)
        
        # Build subgraph URL
        url = self._build_subgraph_url(subgraph.subgraph_id)
        
        # Pagination state
        all_pairs = []
        skip = 0
        page_number = 1
        total_requests = 0
        
        self.logger.info(
            f"Starting pagination for {subgraph.name} - "
            f"Slice {time_slice.slice_number} ({time_slice.start_days_ago}-{time_slice.end_days_ago} days ago)"
        )
        
        while True:
            # Prepare GraphQL variables
            variables = {
                "start": time_slice.start_timestamp,
                "end": time_slice.end_timestamp,
                "first": self.config.max_results_per_query,
                "skip": skip
            }
            
            try:
                # Make request with timeout
                request_start = time.time()
                
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: requests.post(
                        url,
                        json={"query": query_template, "variables": variables},
                        headers={"Content-Type": "application/json"},
                        timeout=30
                    )
                )
                
                request_duration = (time.time() - request_start) * 1000  # ms
                total_requests += 1
                self.pagination_stats["total_requests_made"] += 1
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if "errors" not in data:
                        # Extract pairs based on DEX type
                        if subgraph.dex_type.value in ["uniswap_v3"]:
                            pairs = data.get("data", {}).get("pools", [])
                        else:
                            pairs = data.get("data", {}).get("pairs", [])
                        
                        if not pairs:
                            # No more data available - end pagination
                            self.logger.debug(
                                f"Page {page_number}: No more pairs (pagination complete)"
                            )
                            break
                        
                        # Process pairs through adapter
                        processed_pairs = []
                        for raw_pair in pairs:
                            try:
                                processed_pair = adapter.parse_pair_data(raw_pair)
                                # Add metadata
                                processed_pair['subgraph_source'] = subgraph.name
                                processed_pair['subgraph_id'] = subgraph.subgraph_id
                                processed_pair['blockchain'] = subgraph.blockchain.value
                                processed_pair['dex_type'] = subgraph.dex_type.value
                                processed_pair['time_slice_number'] = time_slice.slice_number
                                processed_pair['discovery_timestamp'] = datetime.now().isoformat()
                                
                                processed_pairs.append(processed_pair)
                            except Exception as e:
                                self.logger.warning(f"Failed to process pair data: {e}")
                        
                        all_pairs.extend(processed_pairs)
                        self.pagination_stats["total_pairs_collected"] += len(processed_pairs)
                        
                        self.logger.debug(
                            f"Page {page_number}: +{len(pairs)} pairs "
                            f"(total: {len(all_pairs)}, response: {request_duration:.1f}ms)"
                        )
                        
                        # Check if this was the last page
                        if len(pairs) < self.config.max_results_per_query:
                            self.logger.debug(f"Last page reached (received {len(pairs)} < {self.config.max_results_per_query})")
                            break
                        
                        # Prepare for next page
                        skip += self.config.max_results_per_query
                        page_number += 1
                        
                        # Rate limiting - respect API limits
                        await asyncio.sleep(self.config.pagination_delay_sec)
                        
                    else:
                        # GraphQL errors
                        error_msg = data['errors'][0]['message']
                        self.logger.error(f"GraphQL Error on page {page_number}: {error_msg}")
                        self.pagination_stats["failed_requests"] += 1
                        
                        return PaginationResult(
                            subgraph_name=subgraph.name,
                            time_slice=time_slice,
                            pairs_collected=[],
                            total_pairs=0,
                            total_pages=page_number - 1,
                            total_requests=total_requests,
                            success=False,
                            error_message=f"GraphQL Error: {error_msg}",
                            duration_seconds=time.time() - start_time
                        )
                        
                else:
                    # HTTP errors
                    self.logger.error(f"HTTP Error on page {page_number}: {response.status_code}")
                    self.pagination_stats["failed_requests"] += 1
                    
                    return PaginationResult(
                        subgraph_name=subgraph.name,
                        time_slice=time_slice,
                        pairs_collected=[],
                        total_pairs=0,
                        total_pages=page_number - 1,
                        total_requests=total_requests,
                        success=False,
                        error_message=f"HTTP Error: {response.status_code}",
                        duration_seconds=time.time() - start_time
                    )
                    
            except asyncio.TimeoutError:
                self.logger.error(f"Timeout on page {page_number}")
                self.pagination_stats["failed_requests"] += 1
                
                return PaginationResult(
                    subgraph_name=subgraph.name,
                    time_slice=time_slice,
                    pairs_collected=[],
                    total_pairs=0,
                    total_pages=page_number - 1,
                    total_requests=total_requests,
                    success=False,
                    error_message="Request timeout",
                    duration_seconds=time.time() - start_time
                )
                
            except Exception as e:
                self.logger.error(f"Unexpected error on page {page_number}: {e}")
                self.pagination_stats["failed_requests"] += 1
                
                return PaginationResult(
                    subgraph_name=subgraph.name,
                    time_slice=time_slice,
                    pairs_collected=[],
                    total_pairs=0,
                    total_pages=page_number - 1,
                    total_requests=total_requests,
                    success=False,
                    error_message=str(e),
                    duration_seconds=time.time() - start_time
                )
        
        # Calculate final statistics
        duration_seconds = time.time() - start_time
        self.pagination_stats["total_pages_processed"] += page_number - 1
        
        # Update average response time
        if total_requests > 0:
            avg_per_request = (duration_seconds / total_requests) * 1000
            current_avg = self.pagination_stats["average_response_time_ms"]
            total_reqs = self.pagination_stats["total_requests_made"]
            self.pagination_stats["average_response_time_ms"] = (
                (current_avg * (total_reqs - total_requests) + avg_per_request * total_requests) / total_reqs
            )
        
        self.logger.info(
            f"Pagination complete for {subgraph.name} Slice {time_slice.slice_number}: "
            f"{len(all_pairs)} pairs collected in {page_number - 1} pages "
            f"({duration_seconds:.1f}s, {total_requests} requests)"
        )
        
        return PaginationResult(
            subgraph_name=subgraph.name,
            time_slice=time_slice,
            pairs_collected=all_pairs,
            total_pairs=len(all_pairs),
            total_pages=page_number - 1,
            total_requests=total_requests,
            success=True,
            duration_seconds=duration_seconds
        )
    
    def get_pagination_stats(self) -> Dict[str, Any]:
        """Get current pagination statistics."""
        stats = self.pagination_stats.copy()
        
        # Add derived metrics
        if stats["total_requests_made"] > 0:
            stats["success_rate"] = (
                (stats["total_requests_made"] - stats["failed_requests"]) / 
                stats["total_requests_made"]
            ) * 100
            
            if stats["total_pages_processed"] > 0:
                stats["average_pairs_per_page"] = (
                    stats["total_pairs_collected"] / stats["total_pages_processed"]
                )
        
        return stats
    
    def reset_pagination_stats(self) -> None:
        """Reset pagination statistics."""
        self.pagination_stats = {
            "total_requests_made": 0,
            "total_pairs_collected": 0,
            "total_pages_processed": 0,
            "failed_requests": 0,
            "average_response_time_ms": 0.0
        }
        
        self.logger.info("Pagination statistics reset")


# === ЧАСТЬ 3 ЗАВЕРШЕНА ===
# Реализованная функциональность:
# - Полная пагинация с skip параметром (проверенная логика)
# - Асинхронная обработка с rate limiting
# - Надежная обработка ошибок и таймаутов
# - Детальная статистика по производительности
# - Поддержка всех типов DEX через адаптеры

if __name__ == "__main__":
    # Test Part 3 pagination (dry run - no actual requests)
    async def test_pagination():
        try:
            agent = TheGraphDiscoveryAgentV3()
            
            print(f"Part 3 Pagination Implementation successful")
            print(f"   Agent initialized with {len(agent.get_active_subgraphs())} subgraphs")
            
            # Generate test time slices
            time_slices = agent.generate_time_slices()
            print(f"   Generated {len(time_slices)} time slices for pagination")
            
            # Show what would be processed
            active_subgraphs = agent.get_active_subgraphs()
            total_operations = len(active_subgraphs) * len(time_slices)
            
            print(f"   Would execute {total_operations} pagination operations:")
            for subgraph in active_subgraphs[:2]:  # Show first 2
                print(f"      {subgraph.name} ({subgraph.dex_type.value}): {len(time_slices)} slices")
            
            print(f"   Pagination config:")
            print(f"      Max results per query: {agent.config.max_results_per_query}")
            print(f"      Delay between requests: {agent.config.pagination_delay_sec}s")
            
            # Show initial stats
            stats = agent.get_pagination_stats()
            print(f"   Initial pagination stats: {stats}")
            
            print(f"\n   Ready for Part 4: Data transformation to TokenDiscoveryReport")
            
        except Exception as e:
            print(f"Part 3 error: {e}")
            import traceback
            traceback.print_exc()
    
    # Run async test
    asyncio.run(test_pagination())
