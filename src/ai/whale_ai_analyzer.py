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

    # Market context
    current_eth_price: Optional[float] = None
    price_change_24h: Optional[float] = None
    volume_24h: Optional[float] = None
    volatility: Optional[float] = None

    # Historical context
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

        # Historical context
        if self.whale_avg_transaction:
            prompt_parts.extend([
                f"",
                f"=== WHALE HISTORY ===",
                f"Average Transaction: ${self.whale_avg_transaction:,.2f}",
            ])

            # Compare current to average
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
        enable_analysis: bool = True,
        min_confidence_for_action: float = 60.0
    ):
        """
        Initialize whale AI analyzer.

        Args:
            consensus_engine: Consensus engine with configured LLMs
            enable_analysis: Enable AI analysis (can disable for testing)
            min_confidence_for_action: Minimum confidence for BUY/SELL (0-100)
        """
        self.consensus_engine = consensus_engine
        self.enable_analysis = enable_analysis
        self.min_confidence_for_action = min_confidence_for_action

        logger.info(
            f"WhaleAIAnalyzer initialized: "
            f"enabled={enable_analysis}, "
            f"min_confidence={min_confidence_for_action}%"
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


# Factory function for easy initialization
async def create_whale_ai_analyzer(
    primary_provider: str = "deepseek",
    validator_provider: str = "gemini",
    enable_validator: bool = True,
    enable_analysis: bool = True
) -> WhaleAIAnalyzer:
    """
    Factory function to create WhaleAIAnalyzer with configured providers.

    Args:
        primary_provider: Primary LLM provider ("deepseek")
        validator_provider: Validator LLM provider ("gemini" or "groq")
        enable_validator: Enable validator LLM
        enable_analysis: Enable AI analysis globally

    Returns:
        Configured WhaleAIAnalyzer instance

    Raises:
        ValueError: If provider names are invalid
    """
    from .providers import DeepSeekProvider, GeminiProvider, GroqProvider
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
        enable_analysis=enable_analysis,
        min_confidence_for_action=60.0
    )

    logger.info(
        f"WhaleAIAnalyzer created: "
        f"primary={primary_provider}, "
        f"validator={validator_provider if enable_validator else 'disabled'}"
    )

    return analyzer
