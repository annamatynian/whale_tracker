"""
Pump Analysis Module

Реалистичный подход к детекции пампов на основе доступных данных
из бесплатных API. Основан на скорректированном плане Gemini.

Components:
- pump_models.py: Pydantic модели для pump detection
- pump_discovery_agent.py: Специализированный pump discovery (наследует базовую архитектуру)
- realistic_scoring.py: Балльная система скоринга (legacy)
- tier_system.py: Новая tier + tags система (v1.0)
- tier_scoring_matrix.py: Логика определения tier'ов
- narrative_analyzer.py: Narrative detection
"""

from .pump_models import (
    PumpIndicators,
    PumpAnalysisReport, 
    ApiUsageTracker,
    NarrativeType,
    OnChainAnalysisResult,
    OnChainRiskLevel
)

# from .pump_discovery_agent import PumpDiscoveryAgent  # Temporarily disabled - file not present

# NEW: Tier + Tags System
from .tier_system import (
    TokenTier,
    TagStatus,
    TagCategory,
    TokenTag,
    TierAnalysisResult,
    TierCriteria
)

from .tier_scoring_matrix import TierScoringMatrix

# Legacy scoring (для обратной совместимости)
from .realistic_scoring import (
    RealisticScoringMatrix,
    RealisticPumpIndicators,
    PumpRecommendationMVP
)

__all__ = [
    # Core models
    'PumpIndicators',
    'PumpAnalysisReport',
    'ApiUsageTracker',
    'NarrativeType',
    'OnChainAnalysisResult',
    'OnChainRiskLevel',
    # 'PumpDiscoveryAgent',  # Temporarily disabled
    
    # Tier + Tags System (NEW)
    'TokenTier',
    'TagStatus',
    'TagCategory',
    'TokenTag',
    'TierAnalysisResult',
    'TierCriteria',
    'TierScoringMatrix',
    
    # Legacy Scoring
    'RealisticScoringMatrix',
    'RealisticPumpIndicators',
    'PumpRecommendationMVP'
]
