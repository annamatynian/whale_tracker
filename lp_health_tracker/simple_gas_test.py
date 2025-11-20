#!/usr/bin/env python3
"""
Simple test for gas calculation math - no pytest required
"""

import sys
import os

# Add src to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'src'))

def test_basic_gas_math():
    """Test basic gas calculation math without dependencies."""
    print("🧮 Testing basic gas calculation math...")
    
    try:
        from web3 import Web3
        print("✅ Web3 import successful")
        
        # Test case: 150k gas at 20 Gwei with ETH at $3000
        gas_used = 150000
        gas_price_gwei = 20
        eth_price_usd = 3000.0
        
        # Step 1: Convert Gwei to Wei
        gas_price_wei = Web3.to_wei(gas_price_gwei, 'gwei')
        print(f"   Gas price: {gas_price_gwei} Gwei = {gas_price_wei:,} Wei")
        
        # Step 2: Calculate total cost in Wei
        total_cost_wei = gas_used * gas_price_wei
        print(f"   Total cost: {gas_used:,} gas × {gas_price_wei:,} Wei = {total_cost_wei:,} Wei")
        
        # Step 3: Convert Wei to ETH
        cost_eth = float(Web3.from_wei(total_cost_wei, 'ether'))
        print(f"   Cost in ETH: {cost_eth:.6f} ETH")
        
        # Step 4: Convert to USD
        cost_usd = cost_eth * eth_price_usd
        print(f"   Cost in USD: ${cost_usd:.2f}")
        
        # Verify expected result
        expected_cost_usd = 9.0  # 150k * 20 * 3000 / 10^18
        if abs(cost_usd - expected_cost_usd) < 0.1:
            print("✅ PASS: Gas calculation math is correct")
            return True
        else:
            print(f"❌ FAIL: Expected ~${expected_cost_usd}, got ${cost_usd:.2f}")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Calculation error: {e}")
        return False

def test_gas_estimator_import():
    """Test that we can import GasEstimator."""
    print("\n📋 Testing GasEstimator import...")
    
    try:
        from src.gas_cost_calculator import GasEstimator
        print("✅ GasCostCalculator import successful")
        
        # Test supported operations
        operations = GasEstimator.get_supported_operations()
        print(f"   Found {len(operations)} supported operations:")
        
        for op in operations[:5]:  # Show first 5
            print(f"   - {op}")
        
        # Test that essential operations are present
        essential_ops = ['uniswap_v2_add_liquidity', 'erc20_approve', 'erc20_transfer']
        missing_ops = [op for op in essential_ops if op not in operations]
        
        if not missing_ops:
            print("✅ PASS: All essential operations are supported")
            return True
        else:
            print(f"❌ FAIL: Missing operations: {missing_ops}")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all simple tests."""
    print("🚀 Running simple gas calculator tests...\n")
    
    results = []
    results.append(test_basic_gas_math())
    results.append(test_gas_estimator_import())
    
    print(f"\n📊 Results: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("🎉 All basic tests PASSED! Gas calculation math is working correctly.")
        return 0
    else:
        print("❌ Some tests FAILED. Check the output above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
