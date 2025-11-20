"""
Crypto Multi-Agent Analysis System
=================================

A sophisticated multi-agent system for discovering and analyzing 
promising cryptocurrency tokens using AI/ML techniques.

Implements the proven Konenkov strategy through specialized agents:
- Market analysis based on USDT dominance
- Early token discovery via on-chain + social signals  
- Multi-layered security and scam detection
- Quantified risk assessment with position sizing
- Automated decision making with Telegram alerts

Author: Crypto Multi-Agent Team
"""

__version__ = "0.1.0"
__author__ = "Crypto Multi-Agent Team"
__description__ = "Multi-agent system for crypto token analysis"

# Expose main components
from config.settings import Settings, get_settings
from config.validation import validate_environment

__all__ = [
    "Settings",
    "get_settings", 
    "validate_environment",
    "__version__",
    "__author__",
    "__description__"
]
