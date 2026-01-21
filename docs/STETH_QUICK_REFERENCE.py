"""
Quick Reference: stETH/ETH Rate Provider
==========================================

NEW METHOD: provider.get_steth_eth_rate()
"""

# 1. BASIC USAGE
# ==============
from src.providers.coingecko_provider import CoinGeckoProvider
from decimal import Decimal

provider = CoinGeckoProvider(api_key='your_key')
rate = await provider.get_steth_eth_rate()
# Returns: Decimal('0.9987')

# 2. WHALE CONVERSION
# ====================
steth_balance = Decimal('10000')  # Whale has 10k stETH
eth_equivalent = steth_balance * await provider.get_steth_eth_rate()
# Result: Decimal('9987.0')

# 3. CACHE BEHAVIOR
# =================
rate1 = await provider.get_steth_eth_rate()  # API call
rate2 = await provider.get_steth_eth_rate()  # Cache hit (< 5min)
# Both return same value, but only 1 API call

# 4. ERROR HANDLING
# =================
try:
    rate = await provider.get_steth_eth_rate()
    # Always returns Decimal, never None
except Exception:
    # Won't happen - method catches all exceptions
    pass

# Fallback on error: Decimal('1.0')

# 5. DE-PEG DETECTION
# ===================
# Automatic warnings logged:
# - rate < 0.98: "⚠️ stETH DE-PEG DETECTED"
# - rate > 1.02: "⚠️ stETH PREMIUM DETECTED"

# 6. TYPICAL VALUES
# =================
# Normal: 0.9950 - 1.0050
# Caution: 0.9800 - 0.9950
# Alert: < 0.9800

# 7. INTEGRATION EXAMPLE
# ======================
async def normalize_whale_balance(whale_address, provider):
    """
    Convert stETH holdings to ETH equivalent.
    
    WHY: Prevents double-counting in accumulation metrics.
    """
    # Get raw balances
    steth_balance = await get_steth_balance(whale_address)
    eth_balance = await get_eth_balance(whale_address)
    
    # Normalize stETH
    steth_rate = await provider.get_steth_eth_rate()
    steth_in_eth = steth_balance * steth_rate
    
    # Total in ETH
    total_eth = eth_balance + steth_in_eth
    return total_eth

# 8. TEST COMMAND
# ===============
# pytest tests/unit/test_price_provider_steth.py -v

# 9. PERFORMANCE
# ==============
# Without cache: ~500-1000ms per call (API rate limited)
# With cache: ~1ms (99.9% faster)
# Cache TTL: 300 seconds (5 minutes)

# 10. API ENDPOINT
# ================
# https://api.coingecko.com/api/v3/simple/price
# ?ids=staked-ether
# &vs_currencies=eth
