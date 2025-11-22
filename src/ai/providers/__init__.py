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

# Gemini is optional - lazy import to avoid dependency issues
GeminiProvider = None
GEMINI_AVAILABLE = False

def get_gemini_provider():
    """Lazy import GeminiProvider only when needed."""
    global GeminiProvider, GEMINI_AVAILABLE
    if GeminiProvider is None and not GEMINI_AVAILABLE:
        try:
            from .gemini_provider import GeminiProvider as _GeminiProvider
            GeminiProvider = _GeminiProvider
            GEMINI_AVAILABLE = True
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(
                f"GeminiProvider not available: {e}. "
                f"Install with: pip install google-generativeai"
            )
            GEMINI_AVAILABLE = False
    return GeminiProvider

__all__ = [
    "DeepSeekProvider",
    "GroqProvider",
]

if GEMINI_AVAILABLE:
    __all__.append("GeminiProvider")
