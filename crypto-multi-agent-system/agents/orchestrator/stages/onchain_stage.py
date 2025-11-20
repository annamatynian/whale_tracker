"""
OnChain Stage - Level 4 of analysis pipeline.
Performs expensive blockchain analysis for top candidates only.
"""

import logging
from typing import List, Dict
from agents.orchestrator.stages.base import AnalysisStage, StageResult
from agents.onchain.onchain_agent import OnChainAgent
from agents.pump_analysis.realistic_scoring import RealisticScoringMatrix, should_run_onchain_analysis
from agents.pump_analysis.pump_models import ApiUsageTracker

class OnChainStage(AnalysisStage):
    """Performs blockchain analysis for liquidity locks and holder concentration."""
    
    def __init__(self, onchain_agent: OnChainAgent, api_tracker: ApiUsageTracker):
        super().__init__("OnChain")
        self.onchain_agent = onchain_agent
        self.api_tracker = api_tracker
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def _analyze_single_candidate(self, item: Dict) -> Dict:
        """Perform OnChain analysis for single candidate."""
        candidate = item['candidate']
        current_score = item['final_score']
        
        try:
            # Check if worth spending expensive RPC calls
            available_calls = self.api_tracker.rpc_daily_limit - self.api_tracker.rpc_calls_today
            
            if not should_run_onchain_analysis(current_score, available_calls):
                reason = "low_score" if current_score < 70 else "insufficient_api_calls"
                self.logger.debug(f"   Skipping OnChain for {candidate.base_token_symbol}: {reason}")
                return item  # Return unchanged
            
            self.logger.info(f"   OnChain analysis: {candidate.base_token_symbol} ({current_score} points)")
            
            # Perform expensive OnChain analysis
            onchain_result = await self.onchain_agent.analyze_token(
                network=candidate.chain_id,
                token_address=candidate.base_token_address,
                lp_address=candidate.pair_address
            )
            
            # Update API usage tracking
            self.api_tracker.rpc_calls_today += onchain_result.api_calls_used
            self.api_tracker.etherscan_calls_today += 2  # Estimated
            
            # Recalculate score with OnChain data
            updated_indicators = item['indicators']
            updated_indicators.onchain_analysis = onchain_result
            
            updated_matrix = RealisticScoringMatrix(indicators=updated_indicators)
            updated_analysis = updated_matrix.get_detailed_analysis()
            updated_score = updated_analysis['total_score']
            
            # Log analysis results
            score_change = updated_score - current_score
            risk_status = onchain_result.overall_risk.value
            
            self.logger.info(f"     OnChain result: {score_change:+} points (risk: {risk_status})")
            
            # Log specific findings
            if onchain_result.lp_analysis:
                lp_lock = (onchain_result.lp_analysis.locked_percentage + 
                          onchain_result.lp_analysis.dead_percentage)
                self.logger.info(f"     LP lock: {lp_lock:.1f}% ({onchain_result.lp_analysis.risk_level.value})")
            
            if onchain_result.holder_analysis:
                concentration = onchain_result.holder_analysis.top_10_concentration
                self.logger.info(f"     Top-10 concentration: {concentration:.1f}% ({onchain_result.holder_analysis.risk_level.value})")
            
            return {
                'candidate': candidate,
                'final_score': updated_score,
                'recommendation': updated_analysis['recommendation'],
                'analysis': updated_analysis,
                'indicators': updated_indicators,
                'onchain_result': onchain_result,
                'score_change': score_change
            }
            
        except Exception as e:
            self._add_error(f"OnChain analysis failed for {candidate.base_token_symbol}: {str(e)}")
            return item  # Return unchanged on error
    
    async def execute(self, top_candidates: List[Dict]) -> StageResult[List[Dict]]:
        """Execute OnChain analysis for top candidates."""
        if not top_candidates:
            return self._create_result([], {"reason": "no_candidates"})
        
        self.logger.info(f"Level 4: OnChain analysis for {len(top_candidates)} candidates")
        
        analyzed_candidates = []
        onchain_calls_used = 0
        successful_analysis = 0
        
        for i, item in enumerate(top_candidates):
            result = await self._analyze_single_candidate(item)
            analyzed_candidates.append(result)
            
            # Track successful OnChain analysis
            if 'onchain_result' in result:
                successful_analysis += 1
                onchain_calls_used += result['onchain_result'].api_calls_used
        
        # Re-sort by updated scores
        analyzed_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        metadata = {
            "input_candidates": len(top_candidates),
            "onchain_analyzed": successful_analysis,
            "total_rpc_calls": onchain_calls_used,
            "average_score_change": self._calculate_average_score_change(analyzed_candidates)
        }
        
        self.logger.info(f"Level 4: OnChain analysis complete. {successful_analysis} analyzed, {onchain_calls_used} RPC calls used")
        
        return self._create_result(analyzed_candidates, metadata)
    
    def _calculate_average_score_change(self, candidates: List[Dict]) -> float:
        """Calculate average score change from OnChain analysis."""
        changes = [item.get('score_change', 0) for item in candidates if 'score_change' in item]
        return sum(changes) / len(changes) if changes else 0.0
