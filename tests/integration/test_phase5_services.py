"""
Phase 5 Services Integration Test (Simplified)
==============================================

Tests MarketDataService and DetectionRepository integration without AI module.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.market_data_service import MarketDataService, MarketDataServiceConfig
from src.repositories.in_memory_detection_repository import InMemoryDetectionRepository
from models.schemas import OneHopDetectionCreate


async def test_market_data_service():
    """Test MarketDataService initialization and data fetching."""
    print("\n" + "="*60)
    print("TEST 1: MarketDataService")
    print("="*60)

    config = MarketDataServiceConfig(
        update_interval=60,
        request_timeout=10,
        max_retries=2
    )

    service = MarketDataService(config=config)

    print("✓ MarketDataService created")

    # Start service
    await service.start()
    print("✓ Service started, waiting for first update...")

    # Wait for first update
    await asyncio.sleep(3)

    # Get market data
    market_data = service.get_market_data()

    if market_data:
        print(f"✓ Market data received:")
        print(f"  - BTC Price: ${market_data.btc_price:,.2f}")
        print(f"  - ETH Price: ${market_data.eth_price:,.2f}")
        print(f"  - BTC 24h Change: {market_data.btc_24h_change:+.2f}%")
        print(f"  - ETH 24h Change: {market_data.eth_24h_change:+.2f}%")
        print(f"  - Sentiment: {market_data.sentiment}")
        print(f"  - Trend: {market_data.trend}")
        result = "✅ PASSED"
    else:
        print("✗ No market data received")
        result = "❌ FAILED"

    # Stop service
    await service.stop()
    print("✓ Service stopped and cleaned up")

    print(f"\n{result}")
    return market_data is not None


async def test_detection_repository():
    """Test DetectionRepository with whale statistics."""
    print("\n" + "="*60)
    print("TEST 2: DetectionRepository + Whale Statistics")
    print("="*60)

    repo = InMemoryDetectionRepository()
    print("✓ InMemoryDetectionRepository created")

    # Add test detections
    whale_address = "0x1234567890123456789012345678901234567890"
    print(f"✓ Adding detections for whale: {whale_address[:10]}...")

    for i in range(10):
        detection = OneHopDetectionCreate(
            whale_address=whale_address,
            intermediate_address=f"0xintermediate{i:04d}",
            exchange_address="0xbinance",
            whale_tx_hash=f"0xwhaletx{i:04d}",
            exchange_tx_hash=f"0xexchangetx{i:04d}",
            token_address="0xUSDT",
            amount=str(500000 + i * 50000),
            confidence_score=70.0 + i * 2,
            detection_method="pattern",
            time_difference_seconds=250 + i * 10
        )
        await repo.create_detection(detection)

    print(f"✓ Added 10 detections")

    # Get whale statistics
    stats = await repo.get_whale_statistics(
        whale_address=whale_address,
        days=30
    )

    if stats:
        print(f"\n✓ Whale statistics retrieved:")
        print(f"  - Total Detections: {stats['total_detections']}")
        print(f"  - Total Volume: ${stats['total_volume']:,.2f}")
        print(f"  - Avg Confidence: {stats['avg_confidence']:.2f}%")
        print(f"  - High Confidence Count: {stats['high_confidence_count']}")
        print(f"  - Last Detection: {stats['last_detection']}")

        # Validate
        assert stats['total_detections'] == 10, "Should have 10 detections"
        assert stats['total_volume'] > 0, "Should have non-zero volume"
        assert stats['avg_confidence'] > 0, "Should have positive avg confidence"

        result = "✅ PASSED"
    else:
        print("✗ No statistics retrieved")
        result = "❌ FAILED"

    print(f"\n{result}")
    return stats is not None


async def test_context_enrichment_flow():
    """Test how services would be used for context enrichment."""
    print("\n" + "="*60)
    print("TEST 3: Context Enrichment Flow Simulation")
    print("="*60)

    # Setup services
    market_config = MarketDataServiceConfig(
        update_interval=60,
        request_timeout=10,
        max_retries=2
    )
    market_service = MarketDataService(config=market_config)
    detection_repo = InMemoryDetectionRepository()

    print("✓ Services initialized")

    # Start market service
    await market_service.start()
    await asyncio.sleep(2)

    # Add historical whale data
    whale_address = "0xWhaleAddress123"
    for i in range(5):
        detection = OneHopDetectionCreate(
            whale_address=whale_address,
            intermediate_address=f"0xint{i}",
            exchange_address="0xexchange",
            whale_tx_hash=f"0xwtx{i}",
            exchange_tx_hash=f"0xetx{i}",
            token_address="0xtoken",
            amount=str(1000000 + i * 100000),
            confidence_score=75.0 + i * 3,
            detection_method="advanced",
            time_difference_seconds=300
        )
        await detection_repo.create_detection(detection)

    print(f"✓ Added 5 historical detections for {whale_address[:15]}...")

    # Simulate context enrichment (what AI Analyzer would do)
    print("\n--- Simulating Context Enrichment ---")

    # Step 1: Get whale history
    whale_history = await detection_repo.get_whale_statistics(
        whale_address=whale_address,
        days=30
    )

    if whale_history:
        print(f"✓ Whale History Fetched:")
        print(f"  - {whale_history['total_detections']} detections")
        print(f"  - Avg confidence: {whale_history['avg_confidence']:.1f}%")
    else:
        print("✗ Failed to fetch whale history")

    # Step 2: Get market data
    market_data = market_service.get_market_data()

    if market_data:
        print(f"✓ Market Data Fetched:")
        print(f"  - BTC: ${market_data.btc_price:,.2f} ({market_data.btc_24h_change:+.1f}%)")
        print(f"  - ETH: ${market_data.eth_price:,.2f} ({market_data.eth_24h_change:+.1f}%)")
        print(f"  - Market Sentiment: {market_data.sentiment}")
    else:
        print("✗ Failed to fetch market data")

    # Step 3: Simulate enriched analysis decision
    print("\n--- Enriched Analysis Decision ---")

    if whale_history and market_data:
        # This is what AI Analyzer would do with enriched context
        confidence_bonus = 0

        # Bonus for whale's good history
        if whale_history['avg_confidence'] > 75:
            confidence_bonus += 5
            print(f"  + Whale has strong history (avg {whale_history['avg_confidence']:.1f}%) → +5% confidence")

        # Bonus for bullish market
        if market_data.sentiment == "bullish":
            confidence_bonus += 5
            print(f"  + Market sentiment is bullish → +5% confidence")

        # Bonus for positive BTC trend
        if market_data.btc_24h_change > 0:
            confidence_bonus += 3
            print(f"  + BTC trending up (+{market_data.btc_24h_change:.1f}%) → +3% confidence")

        base_confidence = 70.0
        final_confidence = base_confidence + confidence_bonus

        print(f"\n  Base Detection Confidence: {base_confidence}%")
        print(f"  Context Enrichment Bonus: +{confidence_bonus}%")
        print(f"  Final Confidence: {final_confidence}%")

        if final_confidence >= 75:
            decision = "BUY"
            print(f"\n  📈 Decision: {decision} (High confidence signal)")
        else:
            decision = "MONITOR"
            print(f"\n  👁 Decision: {decision} (Watch for now)")

        result = "✅ PASSED"
    else:
        print("✗ Enrichment incomplete")
        result = "❌ FAILED"

    # Cleanup
    await market_service.stop()
    print("\n✓ Services cleaned up")

    print(f"\n{result}")
    return whale_history is not None and market_data is not None


async def run_all_tests():
    """Run all integration tests."""
    print("\n" + "="*60)
    print("PHASE 5 INTEGRATION TESTS")
    print("MarketDataService + DetectionRepository + Context Enrichment")
    print("="*60)

    results = []

    # Test 1: MarketDataService
    try:
        result = await test_market_data_service()
        results.append(("MarketDataService", result))
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        results.append(("MarketDataService", False))

    # Test 2: DetectionRepository
    try:
        result = await test_detection_repository()
        results.append(("DetectionRepository", result))
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        results.append(("DetectionRepository", False))

    # Test 3: Context Enrichment Flow
    try:
        result = await test_context_enrichment_flow()
        results.append(("Context Enrichment", result))
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        results.append(("Context Enrichment", False))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {name}")

    print(f"\n{passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("\nArchitecture Validation:")
        print("✓ MarketDataService works independently")
        print("✓ DetectionRepository provides whale statistics")
        print("✓ Context enrichment flow is functional")
        print("✓ Services integrate seamlessly for AI analysis")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    exit(exit_code)
