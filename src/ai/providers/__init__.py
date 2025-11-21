"""
AI Providers
============

LLM provider implementations for Whale Tracker.

Available Providers:
- DeepSeekProvider: Primary analysis (fast, cost-effective)
- GeminiProvider: Validator (FREE, reliable) - OPTIONAL
- GroqProvider: Alternative validator (FREE, ULTRA-FAST)

Author: Whale Tracker Project
"""

from .deepseek_provider import DeepSeekProvider
from .groq_provider import GroqProvider

# Gemini is optional - may have dependency issues
try:
    from .gemini_provider import GeminiProvider
    GEMINI_AVAILABLE = True
except ImportError as e:
    GeminiProvider = None
    GEMINI_AVAILABLE = False
    import logging
    logging.getLogger(__name__).warning(
        f"GeminiProvider not available: {e}. "
        f"Install with: pip install google-generativeai"
    )

__all__ = [
    "DeepSeekProvider",
    "GroqProvider",
]

if GEMINI_AVAILABLE:
    __all__.append("GeminiProvider")
