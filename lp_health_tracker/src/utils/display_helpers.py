"""
Display Helpers - Cross-platform text formatting
==============================================

This module provides cross-platform utilities for displaying text,
especially handling emojis and special characters on Windows.

Author: Generated for DeFi-RAG Project
"""

import sys
import platform
from typing import Dict


def is_windows() -> bool:
    """Check if running on Windows."""
    return platform.system() == 'Windows'


def get_safe_emoji_map() -> Dict[str, str]:
    """Get emoji to text mapping for safe display."""
    return {
        # Status emojis
        '🚀': '[START]',
        '✅': '[OK]',
        '❌': '[ERROR]', 
        '⚠️': '[WARNING]',
        '🔍': '[CHECK]',
        '💡': '[INFO]',
        '🔧': '[FIX]',
        '🎯': '[TARGET]',
        
        # Analysis emojis
        '📊': '[ANALYSIS]',
        '📈': '[UP]',
        '📉': '[DOWN]', 
        '💰': '[MONEY]',
        '🔴': '[HIGH_RISK]',
        '🟠': '[MEDIUM_RISK]',
        '🟡': '[LOW_RISK]',
        '🟢': '[SAFE]',
        
        # Activity emojis
        '🔔': '[ALERT]',
        '📱': '[TELEGRAM]',
        '⏰': '[TIME]',
        '🌐': '[NETWORK]',
        '🔗': '[BLOCKCHAIN]',
        
        # LP specific emojis  
        '🏊‍♂️': '[LP]',
        '⚖️': '[BALANCE]',
        '📋': '[REPORT]',
        '💧': '[LIQUIDITY]'
    }


def safe_format(text: str) -> str:
    """
    Format text for safe display across platforms.
    
    Args:
        text: Text that may contain emojis
        
    Returns:
        str: Safe text for current platform
    """
    if not is_windows():
        return text
    
    # Replace emojis with text on Windows
    emoji_map = get_safe_emoji_map()
    safe_text = text
    
    for emoji, replacement in emoji_map.items():
        safe_text = safe_text.replace(emoji, replacement)
    
    return safe_text


def safe_log_format(message: str, level: str = "INFO") -> str:
    """
    Format log message for safe display.
    
    Args:
        message: Log message
        level: Log level
        
    Returns:
        str: Formatted message
    """
    # Get level prefix
    level_prefixes = {
        'DEBUG': '🔍' if not is_windows() else '[DEBUG]',
        'INFO': '💡' if not is_windows() else '[INFO]',
        'WARNING': '⚠️' if not is_windows() else '[WARNING]', 
        'ERROR': '❌' if not is_windows() else '[ERROR]',
        'CRITICAL': '🔴' if not is_windows() else '[CRITICAL]'
    }
    
    prefix = level_prefixes.get(level.upper(), '[INFO]')
    formatted_message = safe_format(message)
    
    return f"{prefix} {formatted_message}"


def print_safe(message: str, **kwargs):
    """
    Safe print function that handles encoding issues.
    
    Args:
        message: Message to print
        **kwargs: Additional print arguments
    """
    safe_message = safe_format(message)
    
    try:
        print(safe_message, **kwargs)
    except UnicodeEncodeError:
        # Fallback: encode to ASCII, replace problematic characters
        ascii_message = safe_message.encode('ascii', errors='replace').decode('ascii')
        print(ascii_message, **kwargs)


def get_status_symbol(status: str) -> str:
    """
    Get status symbol for current platform.
    
    Args:
        status: Status type (success, error, warning, info)
        
    Returns:
        str: Platform-appropriate symbol
    """
    symbols = {
        'success': '✅' if not is_windows() else '[OK]',
        'error': '❌' if not is_windows() else '[ERROR]',
        'warning': '⚠️' if not is_windows() else '[WARNING]',
        'info': '💡' if not is_windows() else '[INFO]',
        'loading': '🔄' if not is_windows() else '[LOADING]',
        'rocket': '🚀' if not is_windows() else '[START]'
    }
    
    return symbols.get(status.lower(), '[INFO]')


# Convenience functions for common use cases
def log_startup(message: str) -> str:
    """Format startup message."""
    return safe_format(f"🚀 {message}")


def log_success(message: str) -> str:
    """Format success message.""" 
    return safe_format(f"✅ {message}")


def log_error(message: str) -> str:
    """Format error message."""
    return safe_format(f"❌ {message}")


def log_warning(message: str) -> str:
    """Format warning message."""
    return safe_format(f"⚠️ {message}")


def log_info(message: str) -> str:
    """Format info message."""
    return safe_format(f"💡 {message}")


# Test function
if __name__ == "__main__":
    print("Testing display helpers...")
    print(f"Platform: {platform.system()}")
    print(f"Is Windows: {is_windows()}")
    
    test_messages = [
        "🚀 Starting LP Health Tracker...",
        "✅ Configuration loaded successfully",
        "❌ Failed to connect to RPC", 
        "⚠️ High impermanent loss detected",
        "📊 Analyzing position data",
        "💰 Current LP value: $1,234.56"
    ]
    
    print("\nOriginal vs Safe format:")
    for msg in test_messages:
        print(f"Original: {msg}")
        print(f"Safe:     {safe_format(msg)}")
        print()
