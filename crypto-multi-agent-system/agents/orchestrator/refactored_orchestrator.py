"""
Refactored Simple Orchestrator - Clean pipeline architecture.
Fixes architectural problems through separation of concerns and dependency injection.
"""

import logging
from typing import List, Dict, Any
from agents.orchestrator.stages.base import Pipeline
from agents.orchestrator.stages.discovery_stage import DiscoveryStage
from agents.orchestrator.stages.enrichment_stage import EnrichmentStage
from agents.orchestrator.stages.ranking_stage import RankingStage
from agents.orchestrator.stages.onchain_stage import OnChainStage
from agents.orchestrator.stages.alert_stage import AlertStage
from agents.pump_analysis.pump_models import ApiUsageTracker

class RefactoredOrchestrator:
    """
    Orchestrates analysis pipeline using modular stage architecture.
    Addresses previous issues: massive method, tight coupling, poor testability.
    """
    
    def __init__(self, discovery_agent, coingecko_client, goplus_client, onchain_agent, 
                 config: Dict[str, Any] = None):
        """
        Initialize with dependency injection to enable testing and flexibility.
        
        Args:
            discovery_agent: Token discovery service
            coingecko_client: Market data service  
            goplus_client: Security analysis service
            onchain_agent: Blockchain analysis service
            config: Pipeline configuration parameters
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Default configuration
        self.config = {
            'top_n_for_onchain': 15,
            'min_score_for_alert': 60,
            'api_calls_threshold': 45
        }
        if config:
            self.config.update(config)
        
        # Initialize API tracker
        self.api_tracker = ApiUsageTracker()
        
        # Build pipeline stages
        self.pipeline = self._build_pipeline(
            discovery_agent, coingecko_client, goplus_client, onchain_agent
        )
        
        self.logger.info("Refactored orchestrator initialized with modular pipeline")
    
    def _build_pipeline(self, discovery_agent, coingecko_client, 
                       goplus_client, onchain_agent) -> Pipeline:
        """Build analysis pipeline from individual stages."""
        stages = [
            DiscoveryStage(discovery_agent),
            EnrichmentStage(
                coingecko_client, 
                goplus_client, 
                self.api_tracker,
                self.config['api_calls_threshold']
            ),
            RankingStage(self.config['top_n_for_onchain']),
            OnChainStage(onchain_agent, self.api_tracker),
            AlertStage(self.config['min_score_for_alert'])
        ]
        
        return Pipeline(stages)
    
    async def run_analysis(self) -> List[Dict]:
        """
        Execute complete analysis pipeline.
        Replaces massive 200+ line method with clean orchestration.
        """
        self.logger.info("================ ANALYSIS PIPELINE START ================")
        
        try:
            # Execute pipeline stages
            stage_results = await self.pipeline.execute(None)
            
            # Extract final alerts
            alerts = stage_results[-1].data if stage_results else []
            
            # Log execution summary
            self._log_pipeline_summary(stage_results)
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {e}")
            return []
    
    def _log_pipeline_summary(self, stage_results: List):
        """Log pipeline execution statistics."""
        if not stage_results:
            self.logger.warning("No stage results to summarize")
            return
        
        self.logger.info("PIPELINE EXECUTION SUMMARY:")
        
        total_errors = 0
        for result in stage_results:
            stage_name = result.stage_name
            data_size = len(result.data) if hasattr(result.data, '__len__') else 1
            errors = len(result.errors)
            total_errors += errors
            
            self.logger.info(f"   {stage_name}: {data_size} items, {errors} errors")
            
            # Log stage-specific metadata
            if result.metadata:
                for key, value in result.metadata.items():
                    if key in ['candidates_found', 'enriched_candidates', 'selected_candidates', 
                             'onchain_analyzed', 'alerts_generated']:
                        self.logger.info(f"     {key}: {value}")
        
        # Overall pipeline efficiency
        discovery_count = stage_results[0].metadata.get('candidates_found', 0)
        alert_count = stage_results[-1].metadata.get('alerts_generated', 0)
        
        if discovery_count > 0:
            efficiency = (alert_count / discovery_count) * 100
            self.logger.info(f"   Pipeline efficiency: {efficiency:.1f}% ({alert_count}/{discovery_count})")
        
        if total_errors > 0:
            self.logger.warning(f"   Total errors across pipeline: {total_errors}")
        
        # API usage summary
        execution_summary = self.pipeline.get_execution_summary()
        self.logger.info(f"   Executed {execution_summary['executed_stages']}/{execution_summary['total_stages']} stages")
        
        self.logger.info("================ ANALYSIS PIPELINE END ================")

    def get_pipeline_health(self) -> Dict[str, Any]:
        """Get health metrics for monitoring and debugging."""
        return {
            'api_usage': {
                'coingecko_calls': self.api_tracker.coingecko_calls_today,
                'rpc_calls': self.api_tracker.rpc_calls_today,
                'etherscan_calls': self.api_tracker.etherscan_calls_today
            },
            'configuration': self.config,
            'pipeline_stages': len(self.pipeline.stages),
            'last_execution': self.pipeline.get_execution_summary()
        }
