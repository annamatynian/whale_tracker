"""
Enrichment Stage - Level 2 of analysis pipeline.
Handles data enrichment from external APIs and scoring.
"""

import logging
from typing import List, Dict
from agents.orchestrator.stages.base import AnalysisStage, StageResult
from agents.pump_analysis.realistic_scoring import RealisticScoringMatrix, RealisticPumpIndicators
from agents.pump_analysis.pump_models import NarrativeType, ApiUsageTracker
from agents.pump_analysis.narrative_analyzer import find_narrative_in_categories
from tools.market_data.coingecko_client import CoinGeckoClient
from tools.security.goplus_client import GoPlusClient

class EnrichmentStage(AnalysisStage):
    """Enriches token candidates with external data and calculates scores."""
    
    def __init__(self, coingecko_client: CoinGeckoClient, goplus_client: GoPlusClient, 
                 api_tracker: ApiUsageTracker, api_calls_threshold: int = 45):
        super().__init__("Enrichment")
        self.coingecko_client = coingecko_client
        self.goplus_client = goplus_client
        self.api_tracker = api_tracker
        self.api_calls_threshold = api_calls_threshold
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def _should_spend_api_calls(self, preliminary_score: int) -> bool:
        """Decide whether to spend API calls on this candidate."""
        available_calls = self.api_tracker.coingecko_daily_limit - self.api_tracker.coingecko_calls_today
        
        # Conservative approach when API calls are limited
        if available_calls < 20:
            return preliminary_score > 75
        return preliminary_score > self.api_calls_threshold
    
    async def _enrich_single_candidate(self, candidate) -> Dict:
        """Enrich single candidate with external data."""
        try:
            # Check if worth spending API calls
            if not self._should_spend_api_calls(candidate.discovery_score):
                return None  # Skip this candidate
            
            # Get external data
            coingecko_data = self.coingecko_client.get_token_info_by_contract(
                candidate.chain_id, candidate.base_token_address
            )
            self.api_tracker.coingecko_calls_today += 1
            
            goplus_data = self.goplus_client.get_token_security(
                candidate.chain_id, candidate.base_token_address
            )
            
            # Analyze narrative
            found_narrative = find_narrative_in_categories(coingecko_data.get("categories", []))
            
            # Create indicators for scoring
            indicators = RealisticPumpIndicators(
                narrative_type=found_narrative if found_narrative else NarrativeType.UNKNOWN,
                has_trending_narrative=bool(found_narrative),
                coingecko_score=coingecko_data.get("community_score"),
                is_honeypot=goplus_data.get('is_honeypot') == '1',
                is_open_source=goplus_data.get('is_open_source') == '1',
                buy_tax_percent=float(goplus_data.get('buy_tax', '1')) * 100,
                sell_tax_percent=float(goplus_data.get('sell_tax', '1')) * 100
            )
            
            # Calculate score
            scoring_matrix = RealisticScoringMatrix(indicators=indicators)
            final_analysis = scoring_matrix.get_detailed_analysis()
            
            return {
                'candidate': candidate,
                'final_score': final_analysis['total_score'],
                'recommendation': final_analysis['recommendation'],
                'analysis': final_analysis,
                'indicators': indicators
            }
            
        except Exception as e:
            self._add_error(f"Failed to enrich {candidate.base_token_symbol}: {str(e)}")
            return None
    
    async def execute(self, candidates: List) -> StageResult[List[Dict]]:
        """Execute enrichment for all candidates."""
        if not candidates:
            return self._create_result([], {"skipped_reason": "no_candidates"})
        
        self.logger.info(f"Level 2: Enriching {len(candidates)} candidates")
        
        enriched_candidates = []
        skipped_count = 0
        
        for i, candidate in enumerate(candidates):
            if (i + 1) % 10 == 0:
                self.logger.info(f"   Progress: {i + 1}/{len(candidates)} candidates")
            
            enriched = await self._enrich_single_candidate(candidate)
            if enriched:
                enriched_candidates.append(enriched)
            else:
                skipped_count += 1
        
        metadata = {
            "input_candidates": len(candidates),
            "enriched_candidates": len(enriched_candidates),
            "skipped_candidates": skipped_count,
            "api_calls_used": self.api_tracker.coingecko_calls_today
        }
        
        self.logger.info(f"Level 2: Enriched {len(enriched_candidates)} candidates, skipped {skipped_count}")
        
        return self._create_result(enriched_candidates, metadata)
