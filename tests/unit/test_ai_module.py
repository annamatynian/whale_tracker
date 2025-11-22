"""
AI Module Unit Tests
====================

Tests for AI whale analysis components:
- LLM providers (mocked)
- Consensus engine
- Whale AI analyzer

Author: Whale Tracker Project
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

# Import AI components
from src.abstractions.llm_provider import (
    LLMProvider,
    LLMMessage,
    LLMResponse,
    LLMRole,
    LLMProviderError
)
from src.ai.consensus_engine import (
    ConsensusEngine,
    ConsensusResult,
    ConsensusStrategy
)
from src.ai.whale_ai_analyzer import (
    WhaleAIAnalyzer,
    WhaleTransactionContext
)


# Mock LLM Provider for testing
class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, response_text="BUY\nTest reasoning\nConfidence: 80%", **kwargs):
        super().__init__(**kwargs)
        self.response_text = response_text
        self.call_count = 0

    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def default_model(self) -> str:
        return "mock-model"

    async def send_message(self, messages, temperature=None, max_tokens=None, **kwargs):
        self.call_count += 1

        # Update stats
        self._update_stats(
            tokens=100,
            cost=0.0,
            latency_ms=100.0,
            is_error=False
        )

        return LLMResponse(
            content=self.response_text,
            model=self.default_model,
            provider=self.provider_name,
            tokens_used=100,
            cost_usd=0.0,
            latency_ms=100.0
        )

    async def test_connection(self):
        return True

    def estimate_cost(self, input_tokens, output_tokens):
        return 0.0


# Tests
class TestLLMProvider:
    """Test LLM Provider abstraction."""

    @pytest.mark.asyncio
    async def test_mock_provider_basic(self):
        """Test basic mock provider functionality."""
        provider = MockLLMProvider()

        messages = [LLMMessage(role="user", content="test")]
        response = await provider.send_message(messages)

        assert response.content == "BUY\nTest reasoning\nConfidence: 80%"
        assert response.provider == "mock"
        assert provider.call_count == 1

    @pytest.mark.asyncio
    async def test_provider_stats(self):
        """Test provider statistics tracking."""
        provider = MockLLMProvider()

        messages = [LLMMessage(role="user", content="test")]
        await provider.send_message(messages)

        stats = provider.get_stats()
        assert stats.total_requests == 1
        assert stats.total_tokens == 100
        assert stats.error_count == 0

    @pytest.mark.asyncio
    async def test_provider_role(self):
        """Test provider role assignment."""
        primary = MockLLMProvider(role=LLMRole.PRIMARY)
        validator = MockLLMProvider(role=LLMRole.VALIDATOR)

        assert primary.role == LLMRole.PRIMARY
        assert validator.role == LLMRole.VALIDATOR


class TestConsensusEngine:
    """Test consensus engine."""

    @pytest.mark.asyncio
    async def test_consensus_unanimous_agreement(self):
        """Test unanimous strategy when both agree."""
        primary = MockLLMProvider(response_text="BUY\nBullish signal\nConfidence: 80%")
        validator = MockLLMProvider(response_text="BUY\nConfirmed bullish\nConfidence: 75%")

        engine = ConsensusEngine(
            primary_llm=primary,
            validator_llm=validator,
            strategy=ConsensusStrategy.UNANIMOUS
        )

        result = await engine.analyze("test prompt")

        assert result.action == "BUY"
        assert result.agreement is True
        assert 70 <= result.confidence <= 85  # Average of 80 and 75

    @pytest.mark.asyncio
    async def test_consensus_unanimous_disagreement(self):
        """Test unanimous strategy when they disagree."""
        primary = MockLLMProvider(response_text="BUY\nBullish\nConfidence: 80%")
        validator = MockLLMProvider(response_text="SELL\nBearish\nConfidence: 75%")

        engine = ConsensusEngine(
            primary_llm=primary,
            validator_llm=validator,
            strategy=ConsensusStrategy.UNANIMOUS
        )

        result = await engine.analyze("test prompt")

        assert result.action == "NOTHING"  # Disagreement -> NOTHING
        assert result.agreement is False

    @pytest.mark.asyncio
    async def test_consensus_weighted(self):
        """Test weighted consensus strategy."""
        primary = MockLLMProvider(response_text="SELL\nBearish signal\nConfidence: 90%")
        validator = MockLLMProvider(response_text="SELL\nConfirmed bearish\nConfidence: 85%")

        engine = ConsensusEngine(
            primary_llm=primary,
            validator_llm=validator,
            strategy=ConsensusStrategy.WEIGHTED
        )

        result = await engine.analyze("test prompt")

        assert result.action == "SELL"
        assert result.agreement is True
        assert 85 <= result.confidence <= 90

    @pytest.mark.asyncio
    async def test_consensus_without_validator(self):
        """Test consensus with validator disabled."""
        primary = MockLLMProvider(response_text="BUY\nBullish\nConfidence: 80%")

        engine = ConsensusEngine(
            primary_llm=primary,
            validator_llm=None,
            enable_validator=False
        )

        result = await engine.analyze("test prompt")

        assert result.action == "BUY"
        assert result.confidence == 80.0
        assert result.validator_response is None

    @pytest.mark.asyncio
    async def test_consensus_parse_response(self):
        """Test response parsing."""
        primary = MockLLMProvider(
            response_text="SELL\nOne-hop detected with high confidence\nConfidence: 95%"
        )

        engine = ConsensusEngine(primary_llm=primary, enable_validator=False)
        result = await engine.analyze("test")

        assert result.action == "SELL"
        assert result.confidence == 95.0
        assert "One-hop" in result.reasoning


class TestWhaleAIAnalyzer:
    """Test Whale AI Analyzer."""

    @pytest.mark.asyncio
    async def test_analyzer_basic(self):
        """Test basic analyzer functionality."""
        primary = MockLLMProvider(response_text="SELL\nOne-hop dump detected\nConfidence: 85%")
        validator = MockLLMProvider(response_text="SELL\nConfirmed\nConfidence: 80%")

        engine = ConsensusEngine(primary_llm=primary, validator_llm=validator)
        analyzer = WhaleAIAnalyzer(consensus_engine=engine)

        context = WhaleTransactionContext(
            whale_address="0xtest",
            transaction_hash="0xtest",
            amount_eth=100.0,
            amount_usd=350000.0,
            destination_type="exchange",
            is_one_hop=True,
            intermediate_address="0xintermediate",
            confidence_score=85.0
        )

        result = await analyzer.analyze_transaction(context)

        assert result.action == "SELL"
        assert 80 <= result.confidence <= 85

    @pytest.mark.asyncio
    async def test_analyzer_disabled(self):
        """Test analyzer with AI disabled."""
        primary = MockLLMProvider()
        engine = ConsensusEngine(primary_llm=primary)
        analyzer = WhaleAIAnalyzer(consensus_engine=engine, enable_analysis=False)

        context = WhaleTransactionContext(
            whale_address="0xtest",
            transaction_hash="0xtest",
            amount_eth=100.0,
            amount_usd=350000.0,
            destination_type="exchange"
        )

        result = await analyzer.analyze_transaction(context)

        assert result.action == "NOTHING"
        assert result.confidence == 0.0

    @pytest.mark.asyncio
    async def test_analyzer_min_confidence(self):
        """Test minimum confidence threshold."""
        primary = MockLLMProvider(response_text="BUY\nWeak signal\nConfidence: 50%")

        engine = ConsensusEngine(primary_llm=primary, enable_validator=False)
        analyzer = WhaleAIAnalyzer(
            consensus_engine=engine,
            min_confidence_for_action=60.0  # Require 60%
        )

        context = WhaleTransactionContext(
            whale_address="0xtest",
            transaction_hash="0xtest",
            amount_eth=10.0,
            amount_usd=35000.0,
            destination_type="exchange"
        )

        result = await analyzer.analyze_transaction(context)

        # Should be changed to NOTHING due to low confidence
        assert result.action == "NOTHING"

    @pytest.mark.asyncio
    async def test_context_to_prompt(self):
        """Test context formatting to prompt."""
        context = WhaleTransactionContext(
            whale_address="0x" + "a" * 40,
            transaction_hash="0x" + "b" * 64,
            amount_eth=150.0,
            amount_usd=525000.0,
            destination_type="exchange",
            destination_name="Binance",
            is_one_hop=True,
            intermediate_address="0x" + "c" * 40,
            confidence_score=88.0,
            signal_breakdown={
                "gas": {"confidence": 85, "type": "exact_match"},
                "nonce": {"confidence": 95, "type": "immediate"}
            },
            current_eth_price=3500.0,
            price_change_24h=-3.2,
            whale_avg_transaction=200000.0,
            is_anomaly=True,
            anomaly_confidence=82.0
        )

        prompt = context.to_prompt()

        assert "WHALE TRANSACTION ANALYSIS" in prompt
        assert "ONE-HOP DETECTION" in prompt
        assert "88" in prompt  # confidence score
        assert "Binance" in prompt
        assert "ANOMALY DETECTED" in prompt
        # Check price change formatting (can be "3.2" or "3.20")
        assert "3.2" in prompt or "3.20" in prompt

    def test_analyzer_stats(self):
        """Test getting analyzer statistics."""
        primary = MockLLMProvider()
        engine = ConsensusEngine(primary_llm=primary, enable_validator=False)
        analyzer = WhaleAIAnalyzer(consensus_engine=engine)

        stats = analyzer.get_stats()

        assert "primary" in stats
        assert stats["primary"]["total_requests"] == 0


# Test runner
if __name__ == "__main__":
    print("Running AI Module Tests...")
    print("=" * 60)

    # Run pytest
    pytest.main([__file__, "-v", "--tb=short"])
