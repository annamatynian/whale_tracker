"""
Manual Test Script for MulticallClient

Tests MulticallClient with 3 known addresses that have ETH balances.

Run: python test_multicall_manual.py
"""

import asyncio
import sys
import os
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Enable debug logging to see Multicall3 details
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from src.core.web3_manager import Web3Manager
from src.data.multicall_client import MulticallClient
from config.settings import Settings


async def test_multicall():
    """Test MulticallClient with known addresses."""
    
    print("=" * 60)
    print("🧪 MULTICALL CLIENT TEST")
    print("=" * 60)
    
    # Initialize Web3Manager
    print("\n1️⃣ Initializing Web3Manager...")
    settings = Settings()
    web3_manager = Web3Manager(mock_mode=False)
    
    # Initialize connection
    success = await web3_manager.initialize()
    if not success:
        print("❌ Failed to initialize Web3Manager")
        return
    
    print("✅ Web3Manager initialized")
    
    # Initialize MulticallClient
    print("\n2️⃣ Initializing MulticallClient...")
    client = MulticallClient(web3_manager)
    print("✅ MulticallClient initialized")
    
    # Health check
    print("\n3️⃣ Running health check...")
    health = await client.health_check()
    print(f"Health status: {health}")
    
    if health.get("status") != "healthy":
        print("❌ Health check failed")
        return
    
    print("✅ Health check passed")
    
    # Test with 3 known addresses
    print("\n4️⃣ Testing with 3 known addresses...")
    
    addresses = [
        "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",  # Vitalik
        "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B",  # Tornado Cash
        "0x00000000219ab540356cBB839Cbe05303d7705Fa",  # ETH2 Deposit Contract
    ]
    
    print("\nFetching balances for:")
    for addr in addresses:
        print(f"  • {addr}")
    
    print("\n⏳ Calling get_balances_batch()...")
    balances = await client.get_balances_batch(addresses, network="ethereum")
    
    # Display results
    print("\n" + "=" * 60)
    print("📊 RESULTS")
    print("=" * 60)
    
    from web3 import Web3
    
    for addr, balance_wei in balances.items():
        balance_eth = Web3.from_wei(balance_wei, 'ether')
        print(f"\n{addr}:")
        print(f"  Balance: {balance_eth:.4f} ETH")
        print(f"  Wei: {balance_wei:,}")
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETED SUCCESSFULLY")
    print("=" * 60)
    
    # Test get_latest_block
    print("\n5️⃣ Testing get_latest_block()...")
    latest_block = await client.get_latest_block()
    print(f"✅ Latest block: {latest_block:,}")
    
    # Test historical balances (MVP - should warn about archive access)
    print("\n6️⃣ Testing get_historical_balances() (MVP mode)...")
    old_block = latest_block - 200  # 200 blocks ago (beyond free tier limit)
    print(f"Requesting balances at block {old_block:,} (should use current balances)")
    
    hist_balances = await client.get_historical_balances(
        addresses=[addresses[0]],  # Just test with Vitalik's address
        block_number=old_block
    )
    
    print(f"✅ Historical balance query completed (MVP mock mode)")
    
    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_multicall())
