"""
Ranking Stage - Level 3 of analysis pipeline.
Sorts enriched candidates and selects top performers for expensive analysis.
"""

import logging
from typing import List, Dict
from agents.orchestrator.stages.base import AnalysisStage, StageResult

class RankingStage(AnalysisStage):
    """Ranks candidates by score and selects top N for further analysis."""
    
    def __init__(self, top_n: int = 15):
        super().__init__("Ranking")
        self.top_n = top_n
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def execute(self, enriched_candidates: List[Dict]) -> StageResult[List[Dict]]:
        """Execute ranking and selection logic."""
        if not enriched_candidates:
            return self._create_result([], {"reason": "no_enriched_candidates"})
        
        self.logger.info(f"Level 3: Ranking {len(enriched_candidates)} candidates")
        
        # Sort by final score (descending)
        enriched_candidates.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Log top 10 for monitoring
        self.logger.info("TOP-10 CANDIDATES BY SCORE:")
        for i, item in enumerate(enriched_candidates[:10]):
            candidate = item['candidate']
            score = item['final_score']
            recommendation = item['recommendation']
            self.logger.info(f"   #{i+1}: {candidate.base_token_symbol} - {score}/105 points ({recommendation})")
        
        # Select top N candidates
        top_candidates = enriched_candidates[:self.top_n]
        
        # Calculate selection statistics
        worst_selected_score = top_candidates[-1]['final_score'] if top_candidates else 0
        best_rejected_score = 0
        if len(enriched_candidates) > self.top_n:
            best_rejected_score = enriched_candidates[self.top_n]['final_score']
        
        metadata = {
            "total_candidates": len(enriched_candidates),
            "selected_candidates": len(top_candidates),
            "selection_threshold": worst_selected_score,
            "rejected_best_score": best_rejected_score,
            "score_distribution": self._calculate_score_distribution(enriched_candidates)
        }
        
        self.logger.info(f"Level 3: Selected {len(top_candidates)} candidates for next stage")
        if best_rejected_score > 0:
            self.logger.info(f"   Selection boundary: {worst_selected_score} points (rejected {best_rejected_score} points)")
        
        return self._create_result(top_candidates, metadata)
    
    def _calculate_score_distribution(self, candidates: List[Dict]) -> Dict[str, int]:
        """Calculate distribution of scores for monitoring."""
        distribution = {
            "90-105": 0,
            "75-89": 0,
            "60-74": 0,
            "45-59": 0,
            "below_45": 0
        }
        
        for candidate in candidates:
            score = candidate['final_score']
            if score >= 90:
                distribution["90-105"] += 1
            elif score >= 75:
                distribution["75-89"] += 1
            elif score >= 60:
                distribution["60-74"] += 1
            elif score >= 45:
                distribution["45-59"] += 1
            else:
                distribution["below_45"] += 1
        
        return distribution
