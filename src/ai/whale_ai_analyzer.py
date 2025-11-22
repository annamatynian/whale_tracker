"""
Whale AI Analyzer
=================

AI-powered analyzer for whale transaction patterns and market movements.

This module uses LLMs (DeepSeek + Gemini/Groq) to:
1. Analyze whale transactions for dump signals
2. Correlate with market data (price, volume, volatility)
3. Provide BUY/SELL/NOTHING recommendations
4. Estimate confidence levels
5. Generate human-readable reasoning

Inspired by whale_agent.py but adapted for on-chain whale tracking.

Author: Whale Tracker Project
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass

from .consensus_engine import ConsensusEngine, ConsensusResult
from ..abstractions.llm_provider import LLMProvider


logger = logging.getLogger(__name__)


# System prompt for whale analysis (adapted from whale_agent.py)
WHALE_ANALYSIS_SYSTEM_PROMPT = """You are an expert cryptocurrency whale analyst.

Your task is to analyze whale transactions and market data to determine if this is a:
- BUY signal (whale is accumulating, bullish)
- SELL signal (whale is dumping, bearish)
- NOTHING (no clear signal, neutral)

You must respond in EXACTLY 3 lines:
Line 1: Only write BUY, SELL, or NOTHING
Line 2: One short reason why (max 100 characters)
Line 3: Only write "Confidence: X%" where X is 0-100

Be concise and data-driven. Focus on the most important signals."""


@dataclass
class WhaleTransactionContext:
    """
    Context for whale transaction analysis.

    Enhanced with structured whale_history and market_data for richer AI context.
    """
    # Transaction details
    whale_address: str
    transaction_hash: str
    amount_eth: float
    amount_usd: float
    destination_type: str  # "exchange", "unknown", "defi", etc.
    destination_name: Optional[str] = None

    # One-hop details (if applicable)
    is_one_hop: bool = False
    intermediate_address: Optional[str] = None
    confidence_score: Optional[float] = None
    signal_breakdown: Optional[Dict] = None

    # NEW: Structured whale history from DetectionRepository
    whale_history: Optional[Dict] = None
    # Expected format:
    # {
    #     'total_transactions': int,
    #     'avg_amount_eth': float,
    #     'max_amount_eth': float,
    #     'min_amount_eth': float,
    #     'days_since_last': int,
    #     'cold_start': bool  # True if no historical data
    # }

    # NEW: Structured market data from MarketDataService
    market_data: Optional[Dict] = None
    # Expected format (from MarketData Pydantic model):
    # {
    #     'current_eth_price': float,
    #     'price_change_24h': float,
    #     'price_change_7d': float,
    #     'volatility_24h': float,
    #     'volume_24h': float,
    #     'sentiment': str,
    #     'trend': str,
    #     'fear_greed_index': int
    # }

    # DEPRECATED: Legacy market context fields (kept for backwards compatibility)
    current_eth_price: Optional[float] = None
    price_change_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    volatility: Optional[float] = None

    # DEPRECATED: Legacy historical context (use whale_history instead)
    whale_avg_transaction: Optional[float] = None
    transaction_frequency: Optional[float] = None
    is_anomaly: bool = False
    anomaly_confidence: Optional[float] = None

    def to_prompt(self) -> str:
        """
        Format context as prompt for LLM.

        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            f"=== WHALE TRANSACTION ANALYSIS ===",
            f"",
            f"Whale Address: {self.whale_address[:10]}...{self.whale_address[-8:]}",
            f"Transaction: {self.transaction_hash[:10]}...{self.transaction_hash[-8:]}",
            f"",
            f"=== TRANSACTION DETAILS ===",
            f"Amount: {self.amount_eth:.4f} ETH (${self.amount_usd:,.2f} USD)",
            f"Destination Type: {self.destination_type}",
        ]

        if self.destination_name:
            prompt_parts.append(f"Destination: {self.destination_name}")

        # One-hop details
        if self.is_one_hop:
            prompt_parts.extend([
                f"",
                f"=== ONE-HOP DETECTION ===",
                f"⚠️ ONE-HOP TRANSFER DETECTED",
                f"Intermediate Address: {self.intermediate_address[:10]}...{self.intermediate_address[-8:]}",
                f"Detection Confidence: {self.confidence_score:.0f}%",
            ])

            if self.signal_breakdown:
                prompt_parts.append(f"Signal Breakdown:")
                for signal_name, signal_data in self.signal_breakdown.items():
                    if isinstance(signal_data, dict) and signal_data.get('confidence', 0) > 0:
                        prompt_parts.append(
                            f"  - {signal_name.title()}: {signal_data.get('confidence', 0)}% "
                            f"({signal_data.get('type', '')})"
                        )

        # Market context
        if self.current_eth_price:
            prompt_parts.extend([
                f"",
                f"=== MARKET CONTEXT ===",
                f"Current ETH Price: ${self.current_eth_price:,.2f}",
            ])

            if self.price_change_24h is not None:
                direction = "↑" if self.price_change_24h > 0 else "↓"
                prompt_parts.append(
                    f"24h Price Change: {direction} {abs(self.price_change_24h):.2f}%"
                )

            if self.volume_24h:
                prompt_parts.append(f"24h Volume: ${self.volume_24h:,.0f}")

            if self.volatility:
                prompt_parts.append(f"Volatility: {self.volatility:.2f}%")

        # NEW: Structured Whale History (from DetectionRepository)
        if self.whale_history:
            prompt_parts.extend([
                f"",
                f"=== WHALE HISTORICAL BEHAVIOR ===",
            ])

            # Check for cold start
            if self.whale_history.get('cold_start'):
                prompt_parts.extend([
                    f"⚠️ NEW WHALE DETECTED - Insufficient Historical Data",
                    f"",
                    f"IMPORTANT:",
                    f"- This whale has no recorded history in our system",
                    f"- DO NOT make assumptions about past behavior",
                    f"- Focus ONLY on current transaction signals and market context",
                    f"- Use MODERATE confidence (max 70%) due to lack of historical data",
                ])
            else:
                # Normal history available
                total_txns = self.whale_history.get('total_transactions_30d', 0)
                avg_eth = self.whale_history.get('avg_amount_eth', 0)
                max_eth = self.whale_history.get('max_amount_eth', 0)
                days_since = self.whale_history.get('days_since_last', 0)

                prompt_parts.extend([
                    f"Transaction History (last 30 days):",
                    f"  - Total transactions: {total_txns}",
                    f"  - Average amount: {avg_eth:.2f} ETH",
                    f"  - Max amount: {max_eth:.2f} ETH",
                    f"  - Last seen: {days_since} days ago",
                ])

                # Compare current to average
                if avg_eth > 0:
                    ratio = self.amount_eth / avg_eth
                    if ratio > 2.0:
                        prompt_parts.append(
                            f"  ⚠️ This transaction is {ratio:.1f}x LARGER than whale's average"
                        )
                    elif ratio < 0.5:
                        prompt_parts.append(
                            f"  ℹ️ This transaction is {1/ratio:.1f}x SMALLER than whale's average"
                        )
                    else:
                        prompt_parts.append(
                            f"  ℹ️ This is within whale's normal transaction range"
                        )

                # Activity level
                if total_txns > 10:
                    prompt_parts.append(f"  - Activity: HIGH (active trader)")
                elif total_txns > 5:
                    prompt_parts.append(f"  - Activity: MODERATE")
                else:
                    prompt_parts.append(f"  - Activity: LOW (infrequent trader)")

        # NEW: Structured Market Data (from MarketDataService)
        if self.market_data:
            md = self.market_data
            prompt_parts.extend([
                f"",
                f"=== MARKET CONDITIONS ===",
                f"Current State:",
                f"  - ETH Price: ${md.get('current_eth_price', 0):,.2f}",
                f"  - 24h Change: {md.get('price_change_24h', 0):+.2f}%",
                f"  - 7d Change: {md.get('price_change_7d', 0):+.2f}%",
                f"  - Volatility: {md.get('volatility_24h', 0):.1f}%",
                f"  - Volume 24h: ${md.get('volume_24h', 0):,.0f}",
            ])

            # Market sentiment
            sentiment = md.get('sentiment', 'unknown')
            fng_index = md.get('fear_greed_index', 50)
            trend = md.get('trend', 'unknown')

            prompt_parts.extend([
                f"",
                f"Market Psychology:",
                f"  - Sentiment: {sentiment.upper()}",
                f"  - Fear & Greed Index: {fng_index}/100",
                f"  - Trend: {trend.replace('_', ' ').upper()}",
            ])

            # Context interpretation
            if sentiment in ['extreme_fear', 'fear']:
                prompt_parts.append(
                    f"  ⚠️ Market in {sentiment.upper()} - whale selling may be panic or bottom fishing opportunity"
                )
            elif sentiment in ['extreme_greed', 'greed']:
                prompt_parts.append(
                    f"  ⚠️ Market in {sentiment.upper()} - whale selling may be smart profit-taking"
                )

            if md.get('volatility_24h', 0) > 10:
                prompt_parts.append(
                    f"  ⚠️ HIGH VOLATILITY - whale moves may be reactions to price swings"
                )

        # LEGACY: Fallback to old fields if new ones not available
        elif self.whale_avg_transaction:
            prompt_parts.extend([
                f"",
                f"=== WHALE HISTORY (Legacy) ===",
                f"Average Transaction: ${self.whale_avg_transaction:,.2f}",
            ])

            ratio = self.amount_usd / self.whale_avg_transaction
            if ratio > 1.3:
                prompt_parts.append(
                    f"⚠️ This transaction is {ratio:.1f}x LARGER than average"
                )
            elif ratio < 0.7:
                prompt_parts.append(
                    f"ℹ️ This transaction is {1/ratio:.1f}x SMALLER than average"
                )

            if self.transaction_frequency:
                prompt_parts.append(
                    f"Typical Frequency: Every {self.transaction_frequency:.1f} hours"
                )

            if self.is_anomaly:
                prompt_parts.append(
                    f"⚠️ ANOMALY DETECTED (Confidence: {self.anomaly_confidence:.0f}%)"
                )

        prompt_parts.extend([
            f"",
            f"=== ANALYSIS REQUEST ===",
            f"Based on the above data, determine:",
            f"1. Is this a BUY, SELL, or NOTHING signal?",
            f"2. What's the key reason?",
            f"3. What's your confidence level (0-100%)?",
            f"",
            f"Consider:",
            f"- One-hop transfers to exchanges are strong SELL signals",
            f"- Large anomalous transactions suggest potential dumps",
            f"- Market context (price trends, volatility)",
            f"- Whale's historical behavior patterns",
        ])

        return "\n".join(prompt_parts)


class WhaleAIAnalyzer:
    """
    AI-powered whale transaction analyzer.

    Uses consensus between multiple LLMs for robust analysis.
    """

    def __init__(
        self,
        consensus_engine: ConsensusEngine,
        detection_repo=None,
        market_data_service=None,
        enable_analysis: bool = True,
        min_confidence_for_action: float = 60.0
    ):
        """
        Initialize whale AI analyzer.

        Args:
            consensus_engine: Consensus engine with configured LLMs
            detection_repo: Detection repository for whale history (optional)
            market_data_service: Market data service for enrichment (optional)
            enable_analysis: Enable AI analysis (can disable for testing)
            min_confidence_for_action: Minimum confidence for BUY/SELL (0-100)
        """
        self.consensus_engine = consensus_engine
        self.detection_repo = detection_repo
        self.market_data_service = market_data_service
        self.enable_analysis = enable_analysis
        self.min_confidence_for_action = min_confidence_for_action

        logger.info(
            f"WhaleAIAnalyzer initialized: "
            f"enabled={enable_analysis}, "
            f"min_confidence={min_confidence_for_action}%, "
            f"whale_history={'enabled' if detection_repo else 'disabled'}, "
            f"market_data={'enabled' if market_data_service else 'disabled'}"
        )

    async def analyze_transaction(
        self,
        context: WhaleTransactionContext
    ) -> ConsensusResult:
        """
        Analyze whale transaction with AI.

        Args:
            context: Transaction context with all relevant data

        Returns:
            ConsensusResult with action, confidence, reasoning
        """
        if not self.enable_analysis:
            logger.info("AI analysis disabled, returning neutral result")
            # Return neutral result without calling LLM
            from ..abstractions.llm_provider import LLMResponse
            dummy_response = LLMResponse(
                content="NOTHING\nAI analysis disabled\nConfidence: 0%",
                model="none",
                provider="none",
                tokens_used=0,
                cost_usd=0.0,
                latency_ms=0.0
            )
            from .consensus_engine import ConsensusResult, ConsensusStrategy
            return ConsensusResult(
                action="NOTHING",
                confidence=0.0,
                reasoning="AI analysis disabled",
                primary_response=dummy_response,
                validator_response=None,
                agreement=True,
                confidence_delta=0.0,
                strategy_used=ConsensusStrategy.WEIGHTED,
                total_cost_usd=0.0,
                total_latency_ms=0.0
            )

        # Enrich context with whale history and market data (if available)
        await self._enrich_context(context)

        # Generate prompt from context
        prompt = context.to_prompt()

        logger.info(
            f"Analyzing whale transaction: "
            f"whale={context.whale_address[:10]}..., "
            f"amount=${context.amount_usd:,.0f}, "
            f"type={context.destination_type}, "
            f"one_hop={context.is_one_hop}"
        )

        # Get consensus analysis
        result = await self.consensus_engine.analyze(
            prompt=prompt,
            system_prompt=WHALE_ANALYSIS_SYSTEM_PROMPT
        )

        # Apply confidence threshold
        if result.confidence < self.min_confidence_for_action:
            if result.action != "NOTHING":
                logger.info(
                    f"Confidence {result.confidence}% below threshold "
                    f"{self.min_confidence_for_action}%, changing to NOTHING"
                )
                result.action = "NOTHING"

        logger.info(
            f"AI Analysis complete: "
            f"action={result.action}, "
            f"confidence={result.confidence:.1f}%, "
            f"agreement={result.agreement}, "
            f"cost=${result.total_cost_usd:.6f}, "
            f"latency={result.total_latency_ms:.0f}ms"
        )

        return result

    def get_stats(self) -> Dict:
        """
        Get usage statistics from LLMs.

        Returns:
            Dict with stats from primary and validator LLMs
        """
        stats = {
            "primary": self.consensus_engine.primary_llm.get_stats().__dict__,
        }

        if self.consensus_engine.validator_llm:
            stats["validator"] = self.consensus_engine.validator_llm.get_stats().__dict__

        return stats

    def reset_stats(self) -> None:
        """Reset usage statistics."""
        self.consensus_engine.primary_llm.reset_stats()
        if self.consensus_engine.validator_llm:
            self.consensus_engine.validator_llm.reset_stats()

    async def _enrich_context(self, context: WhaleTransactionContext):
        """
        Enrich transaction context with whale history and market data.

        This method automatically fetches additional context data if services
        are available, maintaining loose coupling with SimpleWhaleWatcher.

        Args:
            context: Transaction context to enrich (modified in-place)
        """
        # Enrich with whale history (if detection_repo available)
        if self.detection_repo and not context.whale_history:
            try:
                whale_history = await self.detection_repo.get_whale_statistics(
                    whale_address=context.whale_address,
                    days=30
                )
                context.whale_history = whale_history
                logger.debug(
                    f"Enriched context with whale history: "
                    f"{whale_history.get('total_transactions', 0)} transactions"
                )
            except Exception as e:
                logger.warning(f"Failed to fetch whale history: {e}")
                context.whale_history = {}  # Empty dict for cold start

        # Enrich with market data (if market_data_service available)
        if self.market_data_service and not context.market_data:
            try:
                market_data = self.market_data_service.get_market_data()
                # Convert Pydantic model to dict for context
                if hasattr(market_data, 'model_dump'):
                    market_data_dict = market_data.model_dump()
                elif hasattr(market_data, 'dict'):
                    market_data_dict = market_data.dict()
                else:
                    market_data_dict = market_data  # Already dict

                context.market_data = market_data_dict
                logger.debug(
                    f"Enriched context with market data: "
                    f"ETH=${market_data_dict.get('current_eth_price', 'N/A')}"
                )
            except Exception as e:
                logger.warning(f"Failed to fetch market data: {e}")
                context.market_data = {}  # Empty dict on error


# Factory function for easy initialization
async def create_whale_ai_analyzer(
    primary_provider: str = "deepseek",
    validator_provider: str = "gemini",
    enable_validator: bool = True,
    enable_analysis: bool = True,
    detection_repo=None,
    market_data_service=None
) -> WhaleAIAnalyzer:
    """
    Factory function to create WhaleAIAnalyzer with configured providers.

    Args:
        primary_provider: Primary LLM provider ("deepseek")
        validator_provider: Validator LLM provider ("gemini" or "groq")
        enable_validator: Enable validator LLM
        enable_analysis: Enable AI analysis globally
        detection_repo: Detection repository for whale history (optional)
        market_data_service: Market data service for enrichment (optional)

    Returns:
        Configured WhaleAIAnalyzer instance

    Raises:
        ValueError: If provider names are invalid
    """
    from .providers import DeepSeekProvider, GroqProvider, get_gemini_provider
    from ..abstractions.llm_provider import LLMRole

    # Create primary LLM
    if primary_provider == "deepseek":
        primary_llm = DeepSeekProvider(
            role=LLMRole.PRIMARY,
            temperature=0.0,  # Deterministic for analysis
            max_tokens=500
        )
    else:
        raise ValueError(f"Unknown primary provider: {primary_provider}")

    # Create validator LLM
    validator_llm = None
    if enable_validator:
        if validator_provider == "gemini":
            GeminiProvider = get_gemini_provider()
            if GeminiProvider is None:
                raise ValueError("GeminiProvider not available. Please install google-generativeai.")
            validator_llm = GeminiProvider(
                role=LLMRole.VALIDATOR,
                temperature=0.7,
                max_tokens=500
            )
        elif validator_provider == "groq":
            validator_llm = GroqProvider(
                role=LLMRole.VALIDATOR,
                temperature=0.7,
                max_tokens=500
            )
        else:
            raise ValueError(f"Unknown validator provider: {validator_provider}")

    # Test connections
    logger.info("Testing LLM connections...")
    primary_ok = await primary_llm.test_connection()
    if not primary_ok:
        raise RuntimeError(f"Primary LLM ({primary_provider}) connection test failed")

    if validator_llm:
        validator_ok = await validator_llm.test_connection()
        if not validator_ok:
            logger.warning(
                f"Validator LLM ({validator_provider}) connection test failed, "
                f"disabling validator"
            )
            validator_llm = None
            enable_validator = False

    # Create consensus engine
    from .consensus_engine import ConsensusStrategy
    consensus_engine = ConsensusEngine(
        primary_llm=primary_llm,
        validator_llm=validator_llm,
        strategy=ConsensusStrategy.WEIGHTED,
        enable_validator=enable_validator
    )

    # Create analyzer
    analyzer = WhaleAIAnalyzer(
        consensus_engine=consensus_engine,
        detection_repo=detection_repo,
        market_data_service=market_data_service,
        enable_analysis=enable_analysis,
        min_confidence_for_action=60.0
    )

    logger.info(
        f"WhaleAIAnalyzer created: "
        f"primary={primary_provider}, "
        f"validator={validator_provider if enable_validator else 'disabled'}"
    )

    return analyzer
