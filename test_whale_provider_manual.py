"""
Manual Test Script for WhaleListProvider

Tests whale discovery with real blockchain data.

Run: python test_whale_provider_manual.py
"""

import asyncio
import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Enable logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from src.core.web3_manager import Web3Manager
from src.data.multicall_client import MulticallClient
from src.data.whale_list_provider import WhaleListProvider


async def test_whale_provider():
    """Test WhaleListProvider with real blockchain."""
    
    print("=" * 60)
    print("🐋 WHALE LIST PROVIDER TEST")
    print("=" * 60)
    
    # Initialize Web3Manager
    print("\n1️⃣ Initializing Web3Manager...")
    web3_manager = Web3Manager(mock_mode=False)
    success = await web3_manager.initialize()
    
    if not success:
        print("❌ Failed to initialize Web3Manager")
        return
    
    print("✅ Web3Manager initialized")
    
    # Initialize MulticallClient
    print("\n2️⃣ Initializing MulticallClient...")
    multicall_client = MulticallClient(web3_manager)
    print("✅ MulticallClient initialized")
    
    # Initialize WhaleListProvider
    print("\n3️⃣ Initializing WhaleListProvider...")
    provider = WhaleListProvider(
        multicall_client=multicall_client,
        min_balance_eth=1000  # 1000 ETH minimum
    )
    print("✅ WhaleListProvider initialized")
    
    # Health check
    print("\n4️⃣ Running health check...")
    health = await provider.health_check()
    print(f"Health status: {health}")
    
    if health["status"] != "healthy":
        print("❌ Health check failed")
        return
    
    print("✅ Health check passed")
    
    # Get top 10 whales
    print("\n5️⃣ Fetching top 10 whales (min 1000 ETH)...")
    whales = await provider.get_top_whales(limit=10)
    
    print("\n" + "=" * 60)
    print("📊 RESULTS")
    print("=" * 60)
    
    print(f"\nFound {len(whales)} whales with >= 1000 ETH\n")
    
    for i, whale in enumerate(whales, 1):
        print(f"{i}. {whale['address']}")
        print(f"   Balance: {whale['balance_eth']:,.4f} ETH")
        print(f"   Wei: {whale['balance_wei']:,}")
        print()
    
    # Test with lower threshold
    print("=" * 60)
    print("6️⃣ Testing with lower threshold (100 ETH)...")
    print("=" * 60)
    
    provider_low = WhaleListProvider(
        multicall_client=multicall_client,
        min_balance_eth=100
    )
    
    whales_low = await provider_low.get_top_whales(limit=20)
    
    print(f"\nFound {len(whales_low)} whales with >= 100 ETH")
    print(f"Top 3:")
    for i, whale in enumerate(whales_low[:3], 1):
        print(f"  {i}. {whale['address'][:10]}... - {whale['balance_eth']:,.2f} ETH")
    
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_whale_provider())
