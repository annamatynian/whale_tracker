"""
Integration Test for Phase 5: Whale Statistics & Market Data
=============================================================

Tests real integration of MarketDataService and DetectionRepository with AI Analyzer.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal

from src.services import MarketDataService, MarketDataServiceConfig, MarketData
from src.repositories import InMemoryDetectionRepository
from src.ai.whale_ai_analyzer import WhaleAIAnalyzer, WhaleTransactionContext
from models.schemas import OneHopDetectionCreate


@pytest.mark.asyncio
class TestPhase5Integration:
    """Integration tests for Phase 5 components."""

    async def test_market_data_service_initialization(self):
        """Test MarketDataService starts and fetches data."""
        config = MarketDataServiceConfig(
            update_interval=60,  # 1 minute for test
            request_timeout=10,
            max_retries=2
        )
        service = MarketDataService(config=config)

        # Start service
        await service.start()

        # Wait a bit for first update
        await asyncio.sleep(2)

        # Get market data
        market_data = service.get_market_data()

        # Verify we got data
        assert market_data is not None
        assert hasattr(market_data, 'btc_price')
        assert hasattr(market_data, 'eth_price')

        # Stop service
        await service.stop()

        print(f"✅ MarketDataService: BTC=${market_data.btc_price}, ETH=${market_data.eth_price}")

    async def test_detection_repository_with_whale_stats(self):
        """Test DetectionRepository stores and retrieves whale statistics."""
        repo = InMemoryDetectionRepository()

        # Add test detections for a whale
        whale_address = "0x1234567890123456789012345678901234567890"

        for i in range(5):
            detection = OneHopDetectionCreate(
                whale_address=whale_address,
                intermediate_address=f"0xintermediate{i}",
                exchange_address="0xexchange",
                whale_tx_hash=f"0xwhaletx{i}",
                exchange_tx_hash=f"0xexchangetx{i}",
                token_address="0xtoken",
                amount=str(1000000 + i * 100000),
                confidence_score=70.0 + i * 5,
                detection_method="pattern",
                time_difference_seconds=300 + i * 60
            )
            await repo.create_detection(detection)

        # Get whale statistics
        stats = await repo.get_whale_statistics(
            whale_address=whale_address,
            days=30
        )

        # Verify statistics
        assert stats is not None
        assert stats['total_detections'] == 5
        assert stats['total_volume'] > 0
        assert 'avg_confidence' in stats
        assert 'last_detection' in stats

        print(f"✅ DetectionRepository: {stats['total_detections']} detections, "
              f"avg confidence: {stats['avg_confidence']:.1f}%")

    async def test_ai_analyzer_context_enrichment(self):
        """Test AI Analyzer enriches context with whale stats and market data."""
        # Setup MarketDataService (with mock data)
        market_config = MarketDataServiceConfig(
            update_interval=60,
            request_timeout=10,
            max_retries=2
        )
        market_service = MarketDataService(config=market_config)
        await market_service.start()
        await asyncio.sleep(2)  # Wait for first update

        # Setup DetectionRepository with test data
        detection_repo = InMemoryDetectionRepository()
        whale_address = "0x1234567890123456789012345678901234567890"

        # Add historical detections
        for i in range(3):
            detection = OneHopDetectionCreate(
                whale_address=whale_address,
                intermediate_address=f"0xintermediate{i}",
                exchange_address="0xexchange",
                whale_tx_hash=f"0xwhaletx{i}",
                exchange_tx_hash=f"0xexchangetx{i}",
                token_address="0xtoken",
                amount=str(500000 + i * 100000),
                confidence_score=75.0 + i * 5,
                detection_method="pattern",
                time_difference_seconds=300
            )
            await detection_repo.create_detection(detection)

        # Create AI Analyzer with services (using mock consensus engine)
        from unittest.mock import Mock, AsyncMock

        mock_consensus = AsyncMock()
        mock_consensus.analyze = AsyncMock(return_value={
            'action': 'MONITOR',
            'confidence': 65.0,
            'reasoning': 'Test analysis'
        })

        analyzer = WhaleAIAnalyzer(
            consensus_engine=mock_consensus,
            detection_repo=detection_repo,
            market_data_service=market_service,
            enable_analysis=True
        )

        # Create transaction context (without whale_history and market_data)
        context = WhaleTransactionContext(
            tx_hash="0xtesthash",
            whale_address=whale_address,
            intermediate_address="0xintermediate",
            exchange_address="0xexchange",
            amount=Decimal("1000000"),
            token_symbol="USDT",
            detection_confidence=80.0,
            time_difference_seconds=250,
            whale_history=None,  # Empty initially
            market_data=None,    # Empty initially
            detection_method="advanced"
        )

        # Enrich context
        await analyzer._enrich_context(context)

        # Verify enrichment
        assert context.whale_history is not None, "Whale history should be enriched"
        assert context.market_data is not None, "Market data should be enriched"

        # Verify whale_history content
        assert context.whale_history['total_detections'] == 3
        assert context.whale_history['total_volume'] > 0

        # Verify market_data content
        assert 'btc_price' in context.market_data
        assert 'eth_price' in context.market_data

        print(f"✅ Context Enrichment:")
        print(f"   - Whale History: {context.whale_history['total_detections']} detections")
        print(f"   - Market Data: BTC=${context.market_data['btc_price']}, ETH=${context.market_data['eth_price']}")

        # Cleanup
        await market_service.stop()

    async def test_full_integration_flow(self):
        """Test complete integration: services → AI Analyzer → enriched analysis."""
        # 1. Initialize all services
        print("\n🔧 Initializing services...")

        market_config = MarketDataServiceConfig(
            update_interval=60,
            request_timeout=10,
            max_retries=2
        )
        market_service = MarketDataService(config=market_config)
        detection_repo = InMemoryDetectionRepository()

        await market_service.start()
        await asyncio.sleep(2)

        # 2. Add historical whale data
        whale_address = "0xTestWhale"
        for i in range(5):
            detection = OneHopDetectionCreate(
                whale_address=whale_address,
                intermediate_address=f"0xint{i}",
                exchange_address="0xexchange",
                whale_tx_hash=f"0xwtx{i}",
                exchange_tx_hash=f"0xetx{i}",
                token_address="0xtoken",
                amount=str(1000000),
                confidence_score=80.0,
                detection_method="pattern",
                time_difference_seconds=300
            )
            await detection_repo.create_detection(detection)

        print(f"✅ Added 5 historical detections for whale {whale_address[:10]}...")

        # 3. Create AI Analyzer with services
        from unittest.mock import AsyncMock

        mock_consensus = AsyncMock()
        mock_consensus.analyze = AsyncMock(return_value={
            'action': 'BUY',
            'confidence': 85.0,
            'reasoning': 'Strong whale signal with good history'
        })

        analyzer = WhaleAIAnalyzer(
            consensus_engine=mock_consensus,
            detection_repo=detection_repo,
            market_data_service=market_service,
            enable_analysis=True
        )

        print("✅ AI Analyzer initialized with both services")

        # 4. Analyze transaction (should auto-enrich)
        context = WhaleTransactionContext(
            tx_hash="0xtest",
            whale_address=whale_address,
            intermediate_address="0xint",
            exchange_address="0xexch",
            amount=Decimal("2000000"),
            token_symbol="USDT",
            detection_confidence=85.0,
            time_difference_seconds=200,
            whale_history=None,
            market_data=None,
            detection_method="advanced"
        )

        # This should trigger _enrich_context() automatically
        result = await analyzer.analyze_transaction(context)

        # 5. Verify enrichment happened
        assert context.whale_history is not None, "Auto-enrichment failed: no whale_history"
        assert context.market_data is not None, "Auto-enrichment failed: no market_data"

        print(f"\n✅ Full Integration Test PASSED!")
        print(f"   - Whale History: {context.whale_history['total_detections']} detections")
        print(f"   - Avg Confidence: {context.whale_history['avg_confidence']:.1f}%")
        print(f"   - Market Data: BTC=${context.market_data['btc_price']}")
        print(f"   - AI Decision: {result['action']} ({result['confidence']:.1f}% confidence)")

        # 6. Cleanup
        await market_service.stop()
        print("✅ Services cleaned up")


if __name__ == "__main__":
    # Run integration tests
    async def run_tests():
        test = TestPhase5Integration()

        print("=" * 60)
        print("Phase 5 Integration Tests")
        print("=" * 60)

        print("\n[1/4] Testing MarketDataService...")
        await test.test_market_data_service_initialization()

        print("\n[2/4] Testing DetectionRepository...")
        await test.test_detection_repository_with_whale_stats()

        print("\n[3/4] Testing AI Analyzer Context Enrichment...")
        await test.test_ai_analyzer_context_enrichment()

        print("\n[4/4] Testing Full Integration Flow...")
        await test.test_full_integration_flow()

        print("\n" + "=" * 60)
        print("✅ ALL INTEGRATION TESTS PASSED!")
        print("=" * 60)

    asyncio.run(run_tests())
