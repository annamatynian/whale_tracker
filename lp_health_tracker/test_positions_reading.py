#!/usr/bin/env python3
"""
Test script for reading updated positions.json with new fee fields
================================================================

This script tests that our updated positions.json file loads correctly
and displays the new fee-related fields we added for Net P&L calculations.
"""

import json
import os
from pathlib import Path


def test_positions_file():
    """Test reading and parsing the positions.json file."""
    print("🧪 Testing positions.json file with new fee fields")
    print("=" * 60)
    
    # Get the data file path
    data_dir = Path(__file__).parent / "data"
    positions_file = data_dir / "positions.json"
    
    # Check if file exists
    if not positions_file.exists():
        print("❌ ERROR: positions.json file not found!")
        print(f"Expected location: {positions_file}")
        return False
    
    print(f"✅ File found: {positions_file}")
    
    try:
        # Read and parse JSON
        with open(positions_file, 'r', encoding='utf-8') as f:
            positions = json.load(f)
        
        print(f"✅ JSON loaded successfully: {len(positions)} positions found")
        print()
        
        # Test each position
        for i, position in enumerate(positions, 1):
            print(f"📊 Position {i}: {position['name']}")
            print("-" * 40)
            
            # Check required original fields
            required_fields = ['name', 'initial_price_a_usd', 'initial_price_b_usd']
            for field in required_fields:
                if field in position:
                    print(f"  ✅ {field}: {position[field]}")
                else:
                    print(f"  ❌ Missing field: {field}")
            
            # Check NEW fee-related fields
            fee_fields = {
                'gas_costs_usd': 'Gas costs for entering LP',
                'days_held_mock': 'Mock days held for fee calculation'
            }
            
            print("  🆕 NEW FEE FIELDS:")
            for field, description in fee_fields.items():
                if field in position:
                    print(f"    ✅ {field}: {position[field]} ({description})")
                else:
                    print(f"    ❌ Missing: {field} ({description})")
            
            # Calculate some sample values
            if 'gas_costs_usd' in position and 'days_held_mock' in position:
                # Calculate initial investment value
                initial_liquidity_a = position.get('initial_liquidity_a', 0)
                initial_liquidity_b = position.get('initial_liquidity_b', 0)
                price_a = position.get('initial_price_a_usd', 0)
                price_b = position.get('initial_price_b_usd', 0)
                
                initial_investment = (initial_liquidity_a * price_a) + (initial_liquidity_b * price_b)
                
                # Mock APR calculation (15% for WETH pairs, 1.5% for stable pairs)
                if 'USDC-USDT' in position['name']:
                    mock_apr = 0.015  # 1.5% for stablecoins
                else:
                    mock_apr = 0.15   # 15% for volatile pairs
                
                # Calculate estimated fees earned
                days_held = position['days_held_mock']
                estimated_fees = initial_investment * (mock_apr / 365) * days_held
                
                print("  📈 CALCULATED VALUES:")
                print(f"    💰 Initial Investment: ${initial_investment:.2f}")
                print(f"    ⛽ Gas Costs: ${position['gas_costs_usd']:.2f}")
                print(f"    📅 Days Held: {days_held} days")
                print(f"    🎯 Mock APR: {mock_apr:.1%}")
                print(f"    💸 Estimated Fees Earned: ${estimated_fees:.2f}")
                
                # Net cost basis for P&L calculation
                total_costs = initial_investment + position['gas_costs_usd']
                print(f"    🏦 Total Cost Basis: ${total_costs:.2f}")
            
            print()
        
        # Summary
        print("=" * 60)
        print("🎯 SUMMARY:")
        print(f"  📁 Positions loaded: {len(positions)}")
        print(f"  ✅ All positions have fee fields: {all('gas_costs_usd' in pos and 'days_held_mock' in pos for pos in positions)}")
        print("  🚀 Ready for Net P&L calculations!")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def show_fee_calculation_example():
    """Show example of how fees will be calculated using the new fields."""
    print("\n" + "=" * 60)
    print("💡 FEE CALCULATION EXAMPLE")
    print("=" * 60)
    
    print("For a WETH-USDC position:")
    print("  📊 Initial: 0.1 ETH ($2000) + 200 USDC = $400 investment")
    print("  ⛽ Gas costs: $75")
    print("  📅 Held for: 45 days")
    print("  🎯 APR: 15%")
    print()
    print("Calculations:")
    print("  💸 Fees earned = $400 * (15% / 365) * 45 = $7.40")
    print("  🏦 Total costs = $400 + $75 = $475")
    print("  📈 If LP value = $450, Net P&L = ($450 + $7.40) - $475 = -$17.60")
    print()
    print("📝 This shows the COMPLETE picture including all costs and earnings!")


if __name__ == "__main__":
    success = test_positions_file()
    show_fee_calculation_example()
    
    if success:
        print("\n🎉 Test completed successfully! Ready for next step.")
    else:
        print("\n⚠️ Test failed. Please check the file and try again.")
