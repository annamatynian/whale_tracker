#!/usr/bin/env python3
"""
Test Stage 2: Live Data Integration
==================================

Testing real APIs: CoinGecko prices + DeFi Llama APR
"""
import sys
sys.path.append('src')

from data_providers import LiveDataProvider
from simple_multi_pool import SimpleMultiPoolManager

def test_live_prices():
    """Test CoinGecko API for real token prices."""
    print("🌐 TESTING LIVE PRICES (CoinGecko API)")
    print("=" * 45)
    
    provider = LiveDataProvider()
    
    test_pools = [
        {'name': 'WETH-USDC'},
        {'name': 'WETH-USDT'}, 
        {'name': 'USDC-USDT'}
    ]
    
    for pool in test_pools:
        try:
            prices = provider.get_current_prices(pool)
            print(f"✅ {pool['name']}: ${prices[0]:.2f} / ${prices[1]:.2f}")
        except Exception as e:
            print(f"❌ {pool['name']}: Error - {e}")

def test_live_apr():
    """Test DeFi Llama API for real APR data.""" 
    print("\n📊 TESTING LIVE APR (DeFi Llama API)")
    print("=" * 40)
    
    provider = LiveDataProvider()
    
    test_pools = [
        {'name': 'WETH-USDC'},
        {'name': 'USDC-USDT'}
    ]
    
    for pool in test_pools:
        try:
            apr = provider.get_pool_apr(pool)
            print(f"✅ {pool['name']}: {apr:.2%} APR")
        except Exception as e:
            print(f"❌ {pool['name']}: Error - {e}")

def test_live_portfolio_analysis():
    """Test portfolio analysis with live data."""
    print("\n📈 TESTING PORTFOLIO ANALYSIS WITH LIVE DATA")
    print("=" * 48)
    
    # Create manager with LIVE data provider
    live_provider = LiveDataProvider()
    manager = SimpleMultiPoolManager(live_provider)
    
    # Load positions (they have mock days_held for now)
    if manager.load_positions_from_json('data/positions.json'):
        print(f"✅ Loaded {manager.count_pools()} positions")
        
        # Analyze with LIVE prices and APR
        results = manager.analyze_all_pools_with_fees()
        
        print(f"\n📊 LIVE DATA ANALYSIS RESULTS:")
        for i, result in enumerate(results):
            if 'error' not in result:
                position_info = result['position_info']
                net_pnl = result['net_pnl']
                print(f"  Position {i+1}: {position_info['name']}")
                print(f"    Net P&L: ${net_pnl['net_pnl_usd']:.2f} ({net_pnl['net_pnl_percentage']:.2%})")
                print(f"    Status: {'✅ Profitable' if net_pnl['is_profitable'] else '❌ Loss'}")
            else:
                print(f"  Position {i+1}: Error - {result['error']}")
    else:
        print("❌ Could not load positions")

if __name__ == "__main__":
    print("🚀 MASTER PLAN STAGE 2 - LIVE DATA INTEGRATION TEST")
    print("=" * 55)
    
    test_live_prices()
    test_live_apr() 
    test_live_portfolio_analysis()
    
    print(f"\n🎯 STAGE 2 INTEGRATION TEST COMPLETE!")
    print("🔄 Next: Replace days_held_mock with real date parsing")
