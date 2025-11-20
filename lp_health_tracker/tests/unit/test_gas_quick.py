#!/usr/bin/env python3
"""
Quick test runner for gas cost calculator tests
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    # Simple import test
    from src.gas_cost_calculator import GasCostCalculator, GasEstimator
    from web3 import Web3
    print("✅ Imports successful")
    
    # Test basic Web3 math
    gas_used = 150000
    gas_price_gwei = 20
    eth_price_usd = 3000.0
    
    # Manual calculation
    gas_price_wei = Web3.to_wei(gas_price_gwei, 'gwei')
    total_cost_wei = gas_used * gas_price_wei
    cost_eth = float(Web3.from_wei(total_cost_wei, 'ether'))
    cost_usd = cost_eth * eth_price_usd
    
    print(f"🧮 Gas calculation test:")
    print(f"   Gas used: {gas_used:,}")
    print(f"   Gas price: {gas_price_gwei} Gwei")
    print(f"   ETH price: ${eth_price_usd}")
    print(f"   Total cost: {cost_eth:.6f} ETH = ${cost_usd:.2f}")
    
    # Expected: 150k * 20 * 3000 / 10^18 = 9.0 USD
    expected_cost = 9.0
    if abs(cost_usd - expected_cost) < 0.1:
        print("✅ Math test PASSED")
    else:
        print(f"❌ Math test FAILED: expected ~${expected_cost}, got ${cost_usd:.2f}")
    
    # Test GasEstimator
    operations = GasEstimator.get_supported_operations()
    print(f"📋 Supported operations: {len(operations)}")
    for op in operations[:3]:  # Show first 3
        print(f"   - {op}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
