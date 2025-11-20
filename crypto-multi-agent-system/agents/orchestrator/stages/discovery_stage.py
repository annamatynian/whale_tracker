"""
Discovery Stage - Level 1 of analysis pipeline.
Handles token discovery from multiple sources.
"""

import logging
from typing import List
from agents.orchestrator.stages.base import AnalysisStage, StageResult
from agents.pump_analysis.pump_discovery_agent import PumpDiscoveryAgent

class DiscoveryStage(AnalysisStage):
    """Discovers potential pump candidates from market data sources."""
    
    def __init__(self, discovery_agent: PumpDiscoveryAgent):
        super().__init__("Discovery")
        self.discovery_agent = discovery_agent
        self.logger = logging.getLogger(self.__class__.__name__)
        
    async def execute(self, input_data: None) -> StageResult[List]:
        """Execute token discovery process."""
        try:
            self.logger.info("Level 1: Token discovery started")
            
            # Get candidates from discovery agent
            candidates = await self.discovery_agent.discover_tokens_async()
            
            if not candidates:
                self._add_error("No candidates found from discovery sources")
                return self._create_result([], {"candidates_found": 0})
            
            self.logger.info(f"Level 1: Found {len(candidates)} candidates")
            
            metadata = {
                "candidates_found": len(candidates),
                "sources_used": ["dexscreener", "trending"],  # Could be dynamic
            }
            
            return self._create_result(candidates, metadata)
            
        except Exception as e:
            self._add_error(f"Discovery failed: {str(e)}")
            return self._create_result([], {"error": str(e)})
