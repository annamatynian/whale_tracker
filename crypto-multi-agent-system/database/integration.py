"""
Database Integration Module for Simple Orchestrator
Seamlessly integrates DatabaseManager with the analysis pipeline
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List
from contextlib import asynccontextmanager

from database.database_manager import DatabaseManager
from agents.pump_analysis.pump_models import PumpAnalysisReport


class DatabaseIntegration:
    """
    Handles all database operations for the orchestrator with proper error handling
    and performance optimization
    """
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db_manager = DatabaseManager()
        self.current_session_id = None
        self.session_start_time = None
        
    async def initialize_session(self, cycle_number: int) -> int:
        """Initialize new analysis session and return session ID"""
        try:
            self.session_start_time = datetime.utcnow()
            self.current_session_id = await self.db_manager.create_analysis_session(cycle_number)
            self.logger.info(f"Database session #{self.current_session_id} initialized for cycle {cycle_number}")
            return self.current_session_id
        except Exception as e:
            self.logger.error(f"Failed to initialize database session: {e}")
            # Continue without database - don't break the pipeline
            self.current_session_id = None
            return None

    async def save_analysis_result(self, candidate: Any, analysis_result: Dict[str, Any]) -> int:
        """
        Save comprehensive analysis result to database
        Returns analysis_id or None if failed
        """
        if not self.current_session_id:
            return None
            
        try:
            # Extract data from candidate and analysis result
            analysis_data = {
                # Token identification
                'token_address': candidate.base_token_address,
                'symbol': candidate.base_token_symbol,
                'name': candidate.base_token_name,
                'chain_id': candidate.chain_id,
                'dex': candidate.dex_id,
                'pair_address': candidate.pair_address,
                
                # Discovery stage data
                'discovery_score': candidate.discovery_score,
                'passed_initial_filters': True,  # If we reached this point, it passed
                
                # Market data from DexScreener
                'price_usd': candidate.price_usd,
                'liquidity_usd': candidate.liquidity,
                'volume_h24': candidate.volume_h24,
                'volume_h6': candidate.volume_h6,  
                'volume_h1': candidate.volume_h1,
                'fdv': candidate.fdv,
                
                # Price movements
                'price_change_m5': candidate.price_change_m5,
                'price_change_h1': candidate.price_change_h1,
                'price_change_h6': candidate.price_change_h6,
                'price_change_h24': candidate.price_change_h24,
                
                # Token metrics
                'token_age_hours': candidate.token_age_hours,
                'volume_ratio': getattr(candidate, 'volume_ratio', None),
                'is_volume_accelerating': analysis_result.get('volume_accelerating', False),
                
                # Enrichment results
                'coingecko_found': analysis_result.get('coingecko_found', False),
                'coingecko_score': analysis_result.get('coingecko_score'),
                'coingecko_categories': analysis_result.get('coingecko_categories', []),
                
                'goplus_checked': analysis_result.get('goplus_checked', False),
                'is_honeypot': analysis_result.get('is_honeypot', True),
                'is_open_source': analysis_result.get('is_open_source', False),
                'buy_tax_percent': analysis_result.get('buy_tax_percent', 100.0),
                'sell_tax_percent': analysis_result.get('sell_tax_percent', 100.0),
                
                # Narrative analysis
                'narrative_type': analysis_result.get('narrative_type', 'UNKNOWN'),
                'has_trending_narrative': analysis_result.get('has_trending_narrative', False),
                
                # OnChain analysis (if performed)
                'onchain_analysis_performed': analysis_result.get('onchain_analysis_performed', False),
                'lp_locked_percentage': analysis_result.get('lp_locked_percentage', 0.0),
                'lp_risk_level': analysis_result.get('lp_risk_level', 'CRITICAL'),
                'holder_concentration_top10': analysis_result.get('holder_concentration_top10', 100.0),
                'holder_risk_level': analysis_result.get('holder_risk_level', 'HIGH'),
                'onchain_overall_risk': analysis_result.get('onchain_overall_risk', 'CRITICAL'),
                
                # Scoring breakdown
                'narrative_score': analysis_result.get('narrative_score', 0),
                'security_score': analysis_result.get('security_score', 0),
                'social_score': analysis_result.get('social_score', 0),
                'onchain_score': analysis_result.get('onchain_score', 0),
                'final_score': analysis_result.get('total_score', 0),
                
                # Final recommendation
                'recommendation': analysis_result.get('recommendation', 'NO_POTENTIAL'),
                'confidence_level': analysis_result.get('confidence_level', 0.0),
                
                # Processing metadata
                'enrichment_successful': analysis_result.get('enrichment_successful', True),
                'errors_encountered': analysis_result.get('errors', []),
                'processing_time_seconds': analysis_result.get('processing_time_seconds', 0.0),
                
                # Raw data for future analysis
                'raw_dexscreener_data': getattr(candidate, '_raw_data', None),
                'raw_coingecko_data': analysis_result.get('raw_coingecko_data'),
                'raw_goplus_data': analysis_result.get('raw_goplus_data'),
                'raw_onchain_data': analysis_result.get('raw_onchain_data')
            }
            
            analysis_id = await self.db_manager.save_token_analysis(
                self.current_session_id, analysis_data
            )
            
            return analysis_id
            
        except Exception as e:
            self.logger.error(f"Failed to save analysis for {candidate.base_token_symbol}: {e}")
            return None

    async def create_alert_record(self, candidate: Any, analysis_result: Dict[str, Any], 
                                analysis_id: int = None) -> int:
        """
        Create alert record in database
        Returns alert_id or None if failed
        """
        if not self.current_session_id:
            return None
            
        try:
            alert_data = {
                'token_address': candidate.base_token_address,
                'alert_type': analysis_result['recommendation'],
                'final_score': analysis_result.get('total_score', 0),
                'confidence_level': analysis_result.get('confidence_level', 0.0),
                
                # Snapshot data at time of alert
                'price_usd_at_alert': candidate.price_usd,
                'liquidity_usd_at_alert': candidate.liquidity,
                'volume_24h_at_alert': candidate.volume_h24
            }
            
            alert_id = await self.db_manager.create_alert(
                self.current_session_id, analysis_id or 0, alert_data
            )
            
            return alert_id
            
        except Exception as e:
            self.logger.error(f"Failed to create alert for {candidate.base_token_symbol}: {e}")
            return None

    async def finalize_session(self, session_metrics: Dict[str, Any]):
        """
        Update session with final metrics and performance data
        """
        if not self.current_session_id:
            return
            
        try:
            # Calculate session duration
            if self.session_start_time:
                duration = (datetime.utcnow() - self.session_start_time).total_seconds()
                session_metrics['cycle_duration_seconds'] = duration
            
            # Update session metrics
            success = await self.db_manager.update_session_metrics(
                self.current_session_id, session_metrics
            )
            
            if success:
                self.logger.info(f"Session #{self.current_session_id} finalized with metrics: {session_metrics}")
            else:
                self.logger.error(f"Failed to finalize session #{self.current_session_id}")
                
        except Exception as e:
            self.logger.error(f"Error finalizing session: {e}")

    async def update_alert_notification(self, alert_id: int, sent: bool, message_id: str = None):
        """Update alert notification status"""
        if alert_id:
            await self.db_manager.update_alert_notification_status(alert_id, sent, message_id)

    async def get_recent_performance_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get recent system performance summary"""
        try:
            return await self.db_manager.get_system_overview(days)
        except Exception as e:
            self.logger.error(f"Failed to get performance summary: {e}")
            return {'error': str(e)}

    async def close(self):
        """Clean shutdown of database connections"""
        await self.db_manager.close()


# === UTILITY DECORATORS FOR DATABASE OPERATIONS ===

def db_operation_safe(func):
    """
    Decorator to make database operations safe - don't break pipeline if DB fails
    """
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger = logging.getLogger(func.__module__)
            logger.error(f"Database operation {func.__name__} failed: {e}")
            return None
    return wrapper


def track_performance(operation_name: str):
    """
    Decorator to track operation performance
    """
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            start_time = datetime.utcnow()
            try:
                result = await func(self, *args, **kwargs)
                duration = (datetime.utcnow() - start_time).total_seconds()
                
                if hasattr(self, 'db_integration') and self.db_integration:
                    # Log performance metric
                    self.logger.debug(f"Operation {operation_name} completed in {duration:.2f}s")
                
                return result
            except Exception as e:
                duration = (datetime.utcnow() - start_time).total_seconds()
                self.logger.error(f"Operation {operation_name} failed after {duration:.2f}s: {e}")
                raise
        return wrapper
    return decorator
