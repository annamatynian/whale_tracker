"""
AI Module for Whale Tracker
============================

AI-powered whale analysis using multiple LLMs with consensus.

Architecture:
- LLM Providers: DeepSeek (primary), Gemini/Groq (validator)
- Consensus Engine: Multi-LLM validation for robust analysis
- Whale AI Analyzer: Main analyzer for whale transactions

Quick Start:
```python
from src.ai import create_whale_ai_analyzer, WhaleTransactionContext

# Create analyzer
analyzer = await create_whale_ai_analyzer(
    primary_provider="deepseek",
    validator_provider="gemini",
    enable_validator=True
)

# Analyze transaction
context = WhaleTransactionContext(
    whale_address="0x...",
    transaction_hash="0x...",
    amount_eth=100.0,
    amount_usd=350000.0,
    destination_type="exchange",
    is_one_hop=True,
    confidence_score=85.0
)

result = await analyzer.analyze_transaction(context)
print(f"Action: {result.action}")
print(f"Confidence: {result.confidence}%")
print(f"Reasoning: {result.reasoning}")
```

Author: Whale Tracker Project
"""

from .whale_ai_analyzer import (
    WhaleAIAnalyzer,
    WhaleTransactionContext,
    create_whale_ai_analyzer,
    WHALE_ANALYSIS_SYSTEM_PROMPT
)

from .consensus_engine import (
    ConsensusEngine,
    ConsensusResult,
    ConsensusStrategy
)

from .providers import DeepSeekProvider, GroqProvider

# Gemini is optional
try:
    from .providers import GeminiProvider, GEMINI_AVAILABLE
except ImportError:
    GeminiProvider = None
    GEMINI_AVAILABLE = False

__all__ = [
    # Main analyzer
    "WhaleAIAnalyzer",
    "WhaleTransactionContext",
    "create_whale_ai_analyzer",
    "WHALE_ANALYSIS_SYSTEM_PROMPT",

    # Consensus
    "ConsensusEngine",
    "ConsensusResult",
    "ConsensusStrategy",

    # Providers
    "DeepSeekProvider",
    "GroqProvider",
]

if GEMINI_AVAILABLE:
    __all__.append("GeminiProvider")
