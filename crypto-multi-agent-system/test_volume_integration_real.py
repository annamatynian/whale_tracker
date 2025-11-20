"""Test volume integration with real API - FULL TEST LOGIC"""
import sys
import asyncio
import os
from dotenv import load_dotenv

sys.path.insert(0, r'C:\Users\annam\Documents\DeFi-RAG-Project\crypto-multi-agent-system')

from agents.discovery.volume_integration_patch import VolumeMetricsFetcher

async def test_volume_integration():
    """Тест интеграции с реальным subgraph (если есть API key)."""
    
    load_dotenv()
    
    api_key = os.getenv("GRAPH_API_KEY")
    uniswap_v2_id = os.getenv("UNISWAP_V2_ID")
    
    if not api_key or not uniswap_v2_id:
        print("⚠️ GRAPH_API_KEY or UNISWAP_V2_ID not found in .env")
        print("   Skipping real API test")
        return
    
    print("=" * 60)
    print("TEST: Volume Integration with Real API")
    print("=" * 60)
    
    fetcher = VolumeMetricsFetcher(api_key)
    
    # Тестовый адрес токена (USDC на Ethereum)
    test_token = "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    
    print(f"\nFetching volume data for token: {test_token[:10]}...")
    
    volume_data = await fetcher.fetch_token_day_data(test_token, uniswap_v2_id)
    
    if volume_data:
        print("\n✓ Successfully fetched volume data:")
        print(f"   Raw data points: {volume_data['raw_data_points']}")
        
        metrics = volume_data['metrics']
        print(f"\n   Metrics:")
        print(f"      avg_7d: ${metrics['avg_volume_last_7_days']:,.0f}")
        print(f"      avg_30d: ${metrics['avg_volume_last_30_days']:,.0f}")
        print(f"      acceleration: {metrics['acceleration_factor']:.2f}x")
        print(f"      is_accelerating: {metrics['is_accelerating']}")
        print(f"      volume_ratio: {metrics['volume_ratio']:.3f}")
        print(f"      ratio_healthy: {metrics['volume_ratio_healthy']}")
        
        print(f"\n   Filter result: {'✓ PASS' if volume_data['passed_filters'] else '✗ FAIL'}")
        print(f"   Reason: {volume_data['filter_reason']}")
    else:
        print("\n✗ Failed to fetch volume data")
    
    stats = fetcher.get_stats()
    print(f"\n   Fetcher stats: {stats}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(test_volume_integration())