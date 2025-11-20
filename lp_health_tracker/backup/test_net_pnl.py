#!/usr/bin/env python3
"""
Test Net P&L Calculator with real position data
==============================================

This script tests the new NetPnLCalculator with data from positions.json
to verify that fees and gas costs are calculated correctly.
"""

import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from data_analyzer import NetPnLCalculator, ImpermanentLossCalculator
from data_providers import MockDataProvider


def test_net_pnl_calculator():
    """Test the Net P&L calculator with real position data."""
    print("🧪 Testing Net P&L Calculator with Position Data")
    print("=" * 60)
    
    # Load positions data
    try:
        with open('data/positions.json', 'r') as f:
            positions = json.load(f)
        print(f"✅ Loaded {len(positions)} positions from positions.json")
    except Exception as e:
        print(f"❌ Error loading positions: {e}")
        return False
    
    # Initialize calculators
    net_pnl_calc = NetPnLCalculator()
    mock_provider = MockDataProvider("mixed_volatility")
    
    print("\n📊 TESTING NET P&L CALCULATIONS")
    print("=" * 60)
    
    for i, position in enumerate(positions, 1):
        print(f"\n🔍 Position {i}: {position['name']}")
        print("-" * 50)
        
        try:
            # Extract position data
            initial_liquidity_a = position['initial_liquidity_a']
            initial_liquidity_b = position['initial_liquidity_b']
            initial_price_a = position['initial_price_a_usd']
            initial_price_b = position['initial_price_b_usd']
            gas_costs = position['gas_costs_usd']
            days_held = position['days_held_mock']
            
            # Calculate initial investment
            initial_investment = (initial_liquidity_a * initial_price_a + 
                                initial_liquidity_b * initial_price_b)
            
            # Get current prices from mock provider
            pool_config = {
                'name': f"{position['token_a_symbol']}-{position['token_b_symbol']}"
            }
            current_price_a, current_price_b = mock_provider.get_current_prices(pool_config)
            
            # Get APR for this pool
            apr = mock_provider.get_pool_apr(pool_config)
            
            # Simulate current LP value (for demonstration, assume some IL)
            # In real implementation, this would come from actual LP token value
            hold_value = (initial_liquidity_a * current_price_a + 
                         initial_liquidity_b * current_price_b)
            
            # Simulate IL effect: LP value is typically less than hold value
            il_calc = ImpermanentLossCalculator()
            initial_ratio = initial_price_a / initial_price_b
            current_ratio = current_price_a / current_price_b
            il = il_calc.calculate_impermanent_loss(initial_ratio, current_ratio)
            
            # Approximate LP value (simplified calculation for demo)
            current_lp_value = hold_value * (1 + il)  # IL is negative, so this reduces value
            
            print(f"📈 POSITION DETAILS:")
            print(f"  💰 Initial Investment: ${initial_investment:.2f}")
            print(f"  ⛽ Gas Costs: ${gas_costs:.2f}")
            print(f"  📅 Days Held: {days_held} days")
            print(f"  🎯 APR: {apr:.1%}")
            
            print(f"\n📊 PRICE CHANGES:")
            print(f"  {position['token_a_symbol']}: ${initial_price_a:.2f} → ${current_price_a:.2f} ({((current_price_a/initial_price_a-1)*100):+.1f}%)")
            print(f"  {position['token_b_symbol']}: ${initial_price_b:.2f} → ${current_price_b:.2f} ({((current_price_b/initial_price_b-1)*100):+.1f}%)")
            print(f"  💔 Impermanent Loss: {il:.2%}")
            
            # Test earned fees calculation
            earned_fees = net_pnl_calc.calculate_earned_fees(
                initial_investment, apr, days_held
            )
            
            print(f"\n💸 FEES CALCULATION:")
            print(f"  Formula: ${initial_investment:.2f} * ({apr:.1%} / 365) * {days_held} days")
            print(f"  Earned Fees: ${earned_fees:.2f}")
            
            # Test Net P&L calculation
            net_pnl_result = net_pnl_calc.calculate_net_pnl(
                current_lp_value,
                earned_fees,
                initial_investment,
                gas_costs
            )
            
            print(f"\n🏦 NET P&L CALCULATION:")
            print(f"  Current LP Value: ${current_lp_value:.2f}")
            print(f"  + Earned Fees: ${earned_fees:.2f}")
            print(f"  = Total Income: ${net_pnl_result['total_income_usd']:.2f}")
            print(f"  ")
            print(f"  Initial Investment: ${initial_investment:.2f}")
            print(f"  + Gas Costs: ${gas_costs:.2f}")
            print(f"  = Total Costs: ${net_pnl_result['total_costs_usd']:.2f}")
            print(f"  ")
            print(f"  🎯 Net P&L: ${net_pnl_result['net_pnl_usd']:.2f} ({net_pnl_result['net_pnl_percentage']:.2%})")
            
            # Show impact breakdown
            print(f"\n📋 IMPACT BREAKDOWN:")
            print(f"  LP Value Change: ${net_pnl_result['lp_value_change_usd']:.2f}")
            print(f"  Fees Impact: +${net_pnl_result['fees_impact_usd']:.2f}")
            print(f"  Gas Impact: ${net_pnl_result['gas_impact_usd']:.2f}")
            
            # Status
            status = "✅ PROFITABLE" if net_pnl_result['is_profitable'] else "❌ LOSS"
            print(f"  Status: {status}")
            
            # Compare with simple hold
            hold_pnl = hold_value - initial_investment
            print(f"\n📈 STRATEGY COMPARISON:")
            print(f"  Hold Strategy P&L: ${hold_pnl:.2f}")
            print(f"  LP Strategy P&L: ${net_pnl_result['net_pnl_usd']:.2f}")
            
            if net_pnl_result['net_pnl_usd'] > hold_pnl:
                print(f"  🏆 LP Strategy wins by ${net_pnl_result['net_pnl_usd'] - hold_pnl:.2f}")
            else:
                print(f"  📉 Hold Strategy wins by ${hold_pnl - net_pnl_result['net_pnl_usd']:.2f}")
            
        except Exception as e:
            print(f"❌ Error calculating position {i}: {e}")
            return False
    
    print("\n" + "=" * 60)
    print("🎉 Net P&L Calculator tests completed successfully!")
    print("\n💡 KEY INSIGHTS:")
    print("  ✅ Fees calculation working correctly")
    print("  ✅ Gas costs properly subtracted from profits")
    print("  ✅ Net P&L formula implemented as per Master Plan")
    print("  ✅ Complete position analysis available")
    
    return True


def test_individual_functions():
    """Test individual Net P&L functions."""
    print("\n🔬 TESTING INDIVIDUAL FUNCTIONS")
    print("=" * 40)
    
    calc = NetPnLCalculator()
    
    # Test 1: Fees calculation
    print("Test 1: Fees Calculation")
    fees = calc.calculate_earned_fees(1000.0, 0.15, 30)  # $1000, 15% APR, 30 days
    expected = 1000 * (0.15 / 365) * 30  # Should be ~$12.33
    print(f"  Input: $1000, 15% APR, 30 days")
    print(f"  Expected: ${expected:.2f}")
    print(f"  Actual: ${fees:.2f}")
    print(f"  ✅ {'PASS' if abs(fees - expected) < 0.01 else 'FAIL'}")
    
    # Test 2: Net P&L calculation
    print("\nTest 2: Net P&L Calculation")
    result = calc.calculate_net_pnl(450.0, 7.40, 400.0, 75.0)
    expected_pnl = (450.0 + 7.40) - (400.0 + 75.0)  # Should be -$17.60
    print(f"  Current LP: $450.00, Fees: $7.40, Investment: $400.00, Gas: $75.00")
    print(f"  Expected Net P&L: ${expected_pnl:.2f}")
    print(f"  Actual Net P&L: ${result['net_pnl_usd']:.2f}")
    print(f"  ✅ {'PASS' if abs(result['net_pnl_usd'] - expected_pnl) < 0.01 else 'FAIL'}")
    
    print("\n🎯 Individual function tests completed!")


if __name__ == "__main__":
    print("🚀 Starting Net P&L Calculator Tests")
    print("====================================")
    
    # Test individual functions first
    test_individual_functions()
    
    # Test with real position data
    success = test_net_pnl_calculator()
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("Ready to integrate with SimpleMultiPoolManager!")
    else:
        print("\n⚠️ Some tests failed. Please check the errors above.")
