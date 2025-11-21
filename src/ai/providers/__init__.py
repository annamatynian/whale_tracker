"""
AI Providers
============

LLM provider implementations for Whale Tracker.

Available Providers:
- DeepSeekProvider: Primary analysis (fast, cost-effective)
- GeminiProvider: Validator (FREE, reliable)
- GroqProvider: Alternative validator (FREE, ULTRA-FAST)

Author: Whale Tracker Project
"""

from .deepseek_provider import DeepSeekProvider
from .gemini_provider import GeminiProvider
from .groq_provider import GroqProvider

__all__ = [
    "DeepSeekProvider",
    "GeminiProvider",
    "GroqProvider",
]
