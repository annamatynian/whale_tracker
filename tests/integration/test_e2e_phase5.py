"""
End-to-End Integration Test for Phase 5
========================================

Tests complete data flow from detection → enrichment → AI analysis.
Uses mocks to avoid external API dependencies.
"""

import pytest
import asyncio
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

from src.services import MarketDataService, MarketData, MarketDataServiceConfig
from src.repositories import InMemoryDetectionRepository
from src.ai import WhaleAIAnalyzer, WhaleTransactionContext, ConsensusResult, ConsensusStrategy
from src.abstractions.llm_provider import LLMResponse
from models.schemas import OneHopDetectionCreate


@pytest.mark.asyncio
class TestPhase5EndToEnd:
    """End-to-end tests for Phase 5 integration."""

    async def test_full_pipeline_with_mocks(self):
        """
        Test complete pipeline: Detection → Enrichment → AI Analysis

        Pipeline:
        1. DetectionRepository has whale history
        2. MarketDataService has market data (mocked)
        3. AI Analyzer receives context
        4. AI Analyzer enriches context automatically
        5. AI Analyzer analyzes with enriched data
        6. Returns decision (BUY/SELL/MONITOR)
        """
        print("\n" + "="*60)
        print("E2E TEST: Complete Phase 5 Pipeline")
        print("="*60)

        # ========== SETUP: Services ==========
        print("\n[1/6] Setting up services...")

        # 1. DetectionRepository with whale history
        detection_repo = InMemoryDetectionRepository()
        whale_address = "0x" + "a" * 40  # Valid address

        # Add historical detections for this whale
        for i in range(5):
            detection = OneHopDetectionCreate(
                whale_address=whale_address,
                intermediate_address="0x" + "b" * 40,
                exchange_address="0x" + "c" * 40,
                whale_tx_hash="0x" + f"{i:064d}",
                exchange_tx_hash="0x" + f"{i+100:064d}",
                token_address="0xUSDT",
                amount=str(1000000 + i * 100000),
                confidence_score=80.0 + i * 2,
                detection_method="advanced",
                time_difference_seconds=300,
                whale_tx_block=1000000 + i,
                whale_tx_timestamp=datetime.now(),
                whale_amount_wei=str(1000000000000000000),
                whale_amount_eth=Decimal("1.0"),
                total_confidence=80 + i * 2,
                num_signals_used=3
            )
            await detection_repo.save_detection(detection)

        print(f"✓ Added 5 historical detections for whale {whale_address[:10]}...")

        # 2. MarketDataService with mocked data
        market_data_service = Mock()
        market_data_service.get_market_data = Mock(return_value=MarketData(
            current_eth_price=3500.0,
            price_change_24h=5.2,
            price_change_7d=12.5,
            volume_24h=15000000000.0,
            market_cap=420000000000.0,
            high_24h=3600.0,
            low_24h=3400.0,
            volatility_24h=3.5,
            sentiment="greed",  # Valid: extreme_fear, fear, neutral, greed, extreme_greed, unknown
            fear_greed_index=75,
            trend="uptrend",  # Valid: strong_downtrend, downtrend, sideways, uptrend, strong_uptrend, unknown
            updated_at=datetime.now()
        ))
        print("✓ MarketDataService mocked with bullish data")

        # 3. Mock ConsensusEngine (simulates LLM analysis)
        mock_consensus = AsyncMock()

        # Create proper ConsensusResult object
        mock_result = ConsensusResult(
            action='BUY',
            confidence=85.0,
            reasoning='Strong whale with good history + bullish market',
            primary_response=LLMResponse(
                content='BUY',
                model='mock-model',
                provider='mock-provider',
                tokens_used=100,
                cost_usd=0.001,
                latency_ms=50.0
            ),
            validator_response=None,
            agreement=True,
            confidence_delta=0.0,
            strategy_used=ConsensusStrategy.WEIGHTED,
            total_cost_usd=0.001,
            total_latency_ms=50.0
        )

        mock_consensus.analyze = AsyncMock(return_value=mock_result)
        print("✓ ConsensusEngine mocked")

        # ========== CREATE AI ANALYZER ==========
        print("\n[2/6] Creating AI Analyzer...")
        analyzer = WhaleAIAnalyzer(
            consensus_engine=mock_consensus,
            detection_repo=detection_repo,
            market_data_service=market_data_service,
            enable_analysis=True,
            min_confidence_for_action=60.0
        )
        print("✓ AI Analyzer created with services")

        # ========== CREATE TRANSACTION CONTEXT ==========
        print("\n[3/6] Creating transaction context...")
        context = WhaleTransactionContext(
            whale_address=whale_address,
            transaction_hash="0x" + "1" * 64,
            amount_eth=100.0,
            amount_usd=350000.0,
            destination_type="exchange",
            destination_name="Binance",
            is_one_hop=True,
            intermediate_address="0x" + "b" * 40,
            confidence_score=85.0,
            whale_history=None,  # ← Empty initially
            market_data=None    # ← Empty initially
        )
        print("✓ Context created (whale_history=None, market_data=None)")

        # ========== ANALYZE TRANSACTION ==========
        print("\n[4/6] Analyzing transaction (triggers auto-enrichment)...")
        result = await analyzer.analyze_transaction(context)
        print("✓ Analysis complete")

        # ========== VERIFY ENRICHMENT ==========
        print("\n[5/6] Verifying context enrichment...")

        # Check whale_history was enriched
        assert context.whale_history is not None, "❌ whale_history not enriched!"
        assert context.whale_history['total_transactions'] == 5, "❌ Wrong detection count!"
        assert context.whale_history['avg_amount_eth'] > 0, "❌ Invalid avg amount!"
        print(f"✓ Whale history enriched: {context.whale_history['total_transactions']} detections")
        print(f"  - Avg amount: {context.whale_history['avg_amount_eth']:.2f} ETH")
        print(f"  - Total volume: {context.whale_history['total_volume_eth']:.2f} ETH")

        # Check market_data was enriched
        assert context.market_data is not None, "❌ market_data not enriched!"
        assert context.market_data['current_eth_price'] == 3500.0, "❌ Wrong ETH price!"
        assert context.market_data['sentiment'] == 'greed', "❌ Wrong sentiment!"
        assert context.market_data['trend'] == 'uptrend', "❌ Wrong trend!"
        print(f"✓ Market data enriched:")
        print(f"  - ETH Price: ${context.market_data['current_eth_price']:,.2f}")
        print(f"  - Sentiment: {context.market_data['sentiment']}")
        print(f"  - Trend: {context.market_data['trend']}")

        # ========== VERIFY AI DECISION ==========
        print("\n[6/6] Verifying AI decision...")

        assert result is not None, "❌ No result returned!"
        assert result.action == 'BUY', f"❌ Expected BUY, got {result.action}"
        assert result.confidence == 85.0, f"❌ Expected 85.0, got {result.confidence}"
        print(f"✓ AI Decision: {result.action} ({result.confidence}% confidence)")
        print(f"✓ Reasoning: {result.reasoning}")

        # ========== SUCCESS ==========
        print("\n" + "="*60)
        print("✅ E2E TEST PASSED!")
        print("="*60)
        print("\n📊 Pipeline Summary:")
        print(f"  1. Whale History: {context.whale_history['total_transactions']} detections")
        print(f"  2. Market Data: ${context.market_data['current_eth_price']:,.0f} ETH")
        print(f"  3. Context Enriched: ✅")
        print(f"  4. AI Decision: {result.action} ({result.confidence}%)")
        print(f"\n🎯 Architecture Validated:")
        print(f"  ✓ Services work independently")
        print(f"  ✓ AI Analyzer enriches context automatically")
        print(f"  ✓ Full pipeline functional")


    async def test_enrichment_graceful_degradation(self):
        """Test that AI works even if services fail."""
        print("\n" + "="*60)
        print("E2E TEST: Graceful Degradation")
        print("="*60)

        # Mock services that fail
        failing_repo = AsyncMock()
        failing_repo.get_whale_statistics = AsyncMock(side_effect=Exception("DB error"))

        failing_market_service = Mock()
        failing_market_service.get_market_data = Mock(side_effect=Exception("API error"))

        mock_consensus = AsyncMock()

        # Create proper ConsensusResult for graceful degradation test
        degraded_result = ConsensusResult(
            action='MONITOR',
            confidence=50.0,
            reasoning='Limited data, monitoring recommended',
            primary_response=LLMResponse(
                content='MONITOR',
                model='mock-model',
                provider='mock-provider',
                tokens_used=80,
                cost_usd=0.0008,
                latency_ms=45.0
            ),
            validator_response=None,
            agreement=True,
            confidence_delta=0.0,
            strategy_used=ConsensusStrategy.WEIGHTED,
            total_cost_usd=0.0008,
            total_latency_ms=45.0
        )

        mock_consensus.analyze = AsyncMock(return_value=degraded_result)

        # Create analyzer with failing services
        analyzer = WhaleAIAnalyzer(
            consensus_engine=mock_consensus,
            detection_repo=failing_repo,
            market_data_service=failing_market_service,
            enable_analysis=True
        )

        context = WhaleTransactionContext(
            whale_address="0x" + "a" * 40,
            transaction_hash="0x" + "1" * 64,
            amount_eth=1.0,
            amount_usd=3500.0,
            destination_type="exchange",
            destination_name="Unknown",
            is_one_hop=True,
            intermediate_address="0x" + "b" * 40,
            confidence_score=70.0,
            whale_history=None,
            market_data=None
        )

        # Should not crash, even with failing services
        result = await analyzer.analyze_transaction(context)

        # Verify graceful degradation
        assert result is not None, "❌ Analyzer crashed on service failure!"
        assert context.whale_history == {}, "❌ Should have empty dict, not None"
        assert context.market_data == {}, "❌ Should have empty dict, not None"

        print("\n✅ Graceful Degradation Test PASSED!")
        print(f"  - Services failed, but analyzer continued")
        print(f"  - Decision: {result.action} ({result.confidence}%)")
        print(f"  - whale_history: {context.whale_history}")
        print(f"  - market_data: {context.market_data}")


if __name__ == "__main__":
    async def run():
        test = TestPhase5EndToEnd()
        print("\n🚀 Running E2E Tests...\n")

        await test.test_full_pipeline_with_mocks()
        print("\n" + "-"*60 + "\n")
        await test.test_enrichment_graceful_degradation()

        print("\n" + "="*60)
        print("🎉 ALL E2E TESTS PASSED!")
        print("="*60)

    asyncio.run(run())
