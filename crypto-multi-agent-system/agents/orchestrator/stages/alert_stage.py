"""
Alert Generation Stage - Level 5 of analysis pipeline.
Filters candidates and generates final alerts based on business rules.
"""

import logging
from typing import List, Dict
from agents.orchestrator.stages.base import AnalysisStage, StageResult
from agents.pump_analysis.realistic_scoring import PumpRecommendationMVP

class AlertStage(AnalysisStage):
    """Generates alerts for candidates meeting minimum quality thresholds."""
    
    def __init__(self, min_score_for_alert: int = 60, 
                 alert_recommendations: List[PumpRecommendationMVP] = None):
        super().__init__("AlertGeneration")
        self.min_score_for_alert = min_score_for_alert
        self.alert_recommendations = alert_recommendations or [
            PumpRecommendationMVP.HIGH_POTENTIAL,
            PumpRecommendationMVP.MEDIUM_POTENTIAL
        ]
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def execute(self, analyzed_candidates: List[Dict]) -> StageResult[List[Dict]]:
        """Generate alerts from analyzed candidates."""
        if not analyzed_candidates:
            return self._create_result([], {"reason": "no_candidates"})
        
        self.logger.info(f"Level 5: Alert generation for {len(analyzed_candidates)} candidates")
        
        # Apply quality filter
        high_quality_candidates = [
            item for item in analyzed_candidates 
            if item['final_score'] >= self.min_score_for_alert
        ]
        
        # Generate alerts for qualifying candidates
        alerts = []
        for item in high_quality_candidates:
            recommendation = item['recommendation']
            
            if recommendation in [rec.value for rec in self.alert_recommendations]:
                alert = {
                    'token_symbol': item['candidate'].base_token_symbol,
                    'contract_address': item['candidate'].base_token_address,
                    'network': item['candidate'].chain_id,
                    'final_score': item['final_score'],
                    'recommendation': recommendation,
                    'details': item['analysis'],
                    'has_onchain_analysis': 'onchain_result' in item
                }
                alerts.append(alert)
                
                self.logger.info(f"   Alert: {item['candidate'].base_token_symbol} "
                               f"({item['final_score']}/105, {recommendation})")
        
        metadata = {
            "input_candidates": len(analyzed_candidates),
            "quality_filtered": len(high_quality_candidates),
            "alerts_generated": len(alerts),
            "filter_efficiency": len(alerts) / len(analyzed_candidates) if analyzed_candidates else 0,
            "min_score_threshold": self.min_score_for_alert
        }
        
        self.logger.info(f"Level 5: Generated {len(alerts)} alerts from {len(analyzed_candidates)} candidates")
        
        return self._create_result(alerts, metadata)
