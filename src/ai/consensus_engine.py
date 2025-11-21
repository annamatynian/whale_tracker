"""
AI Consensus Engine
===================

Multi-LLM consensus system for validating whale analysis.

This engine combines responses from multiple LLMs to:
1. Reduce hallucinations
2. Increase confidence in analysis
3. Detect disagreements between models
4. Provide more robust recommendations

Architecture:
- Primary LLM (DeepSeek): Fast initial analysis
- Validator LLM (Gemini/Groq): Validates and enriches analysis
- Consensus algorithm: Combines insights from both

Author: Whale Tracker Project
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..abstractions.llm_provider import (
    LLMProvider,
    LLMMessage,
    LLMResponse
)


logger = logging.getLogger(__name__)


class ConsensusStrategy(Enum):
    """Strategy for reaching consensus between LLMs."""
    UNANIMOUS = "unanimous"  # Both must agree
    MAJORITY = "majority"  # Primary decides, validator can veto
    WEIGHTED = "weighted"  # Weighted average of confidence
    VALIDATOR_OVERRIDE = "validator_override"  # Validator can override primary


@dataclass
class ConsensusResult:
    """
    Result of consensus analysis between multiple LLMs.
    """
    # Final consensus
    action: str  # BUY, SELL, NOTHING
    confidence: float  # 0-100
    reasoning: str  # Combined reasoning

    # Individual responses
    primary_response: LLMResponse
    validator_response: Optional[LLMResponse]

    # Consensus metadata
    agreement: bool  # Do both LLMs agree on action?
    confidence_delta: float  # Difference in confidence between LLMs
    strategy_used: ConsensusStrategy

    # Cost and performance
    total_cost_usd: float
    total_latency_ms: float

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "action": self.action,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "agreement": self.agreement,
            "confidence_delta": self.confidence_delta,
            "strategy": self.strategy_used.value,
            "cost_usd": self.total_cost_usd,
            "latency_ms": self.total_latency_ms,
            "primary_provider": self.primary_response.provider,
            "validator_provider": self.validator_response.provider if self.validator_response else None,
        }


class ConsensusEngine:
    """
    Multi-LLM consensus engine for robust whale analysis.

    Combines insights from primary and validator LLMs to provide
    more reliable recommendations.
    """

    def __init__(
        self,
        primary_llm: LLMProvider,
        validator_llm: Optional[LLMProvider] = None,
        strategy: ConsensusStrategy = ConsensusStrategy.WEIGHTED,
        min_confidence_threshold: float = 50.0,
        enable_validator: bool = True
    ):
        """
        Initialize consensus engine.

        Args:
            primary_llm: Primary LLM for initial analysis
            validator_llm: Validator LLM for validation (optional)
            strategy: Consensus strategy to use
            min_confidence_threshold: Minimum confidence for action (0-100)
            enable_validator: Enable validator LLM (can disable for speed)
        """
        self.primary_llm = primary_llm
        self.validator_llm = validator_llm
        self.strategy = strategy
        self.min_confidence_threshold = min_confidence_threshold
        self.enable_validator = enable_validator and validator_llm is not None

        logger.info(
            f"ConsensusEngine initialized: "
            f"primary={primary_llm.provider_name}, "
            f"validator={validator_llm.provider_name if validator_llm else 'None'}, "
            f"strategy={strategy.value}, "
            f"enabled={self.enable_validator}"
        )

    async def analyze(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> ConsensusResult:
        """
        Analyze with consensus between LLMs.

        Args:
            prompt: User prompt for analysis
            system_prompt: System instructions (optional)
            **kwargs: Additional parameters

        Returns:
            ConsensusResult with combined analysis
        """
        # Prepare messages
        messages = []
        if system_prompt:
            messages.append(LLMMessage(role="system", content=system_prompt))
        messages.append(LLMMessage(role="user", content=prompt))

        # Get primary analysis
        logger.info(f"Getting primary analysis from {self.primary_llm.provider_name}...")
        primary_response = await self.primary_llm.send_message(messages, **kwargs)

        # Parse primary response
        primary_action, primary_confidence, primary_reasoning = self._parse_response(
            primary_response.content
        )

        logger.info(
            f"Primary analysis: action={primary_action}, "
            f"confidence={primary_confidence}%"
        )

        # If validator disabled or not available, return primary result
        if not self.enable_validator:
            logger.info("Validator disabled, using primary result only")
            return ConsensusResult(
                action=primary_action,
                confidence=primary_confidence,
                reasoning=primary_reasoning,
                primary_response=primary_response,
                validator_response=None,
                agreement=True,  # N/A
                confidence_delta=0.0,
                strategy_used=self.strategy,
                total_cost_usd=primary_response.cost_usd or 0.0,
                total_latency_ms=primary_response.latency_ms or 0.0
            )

        # Get validator analysis
        logger.info(f"Getting validator analysis from {self.validator_llm.provider_name}...")

        # Add primary result to validator prompt for context
        validator_prompt = (
            f"{prompt}\n\n"
            f"Primary Analysis Result:\n"
            f"Action: {primary_action}\n"
            f"Confidence: {primary_confidence}%\n"
            f"Reasoning: {primary_reasoning}\n\n"
            f"Please validate this analysis and provide your own assessment."
        )

        validator_messages = []
        if system_prompt:
            validator_messages.append(LLMMessage(role="system", content=system_prompt))
        validator_messages.append(LLMMessage(role="user", content=validator_prompt))

        validator_response = await self.validator_llm.send_message(validator_messages, **kwargs)

        # Parse validator response
        validator_action, validator_confidence, validator_reasoning = self._parse_response(
            validator_response.content
        )

        logger.info(
            f"Validator analysis: action={validator_action}, "
            f"confidence={validator_confidence}%"
        )

        # Calculate consensus
        consensus = self._calculate_consensus(
            primary_action, primary_confidence, primary_reasoning,
            validator_action, validator_confidence, validator_reasoning
        )

        # Calculate totals
        total_cost = (primary_response.cost_usd or 0.0) + (validator_response.cost_usd or 0.0)
        total_latency = (primary_response.latency_ms or 0.0) + (validator_response.latency_ms or 0.0)

        logger.info(
            f"Consensus reached: action={consensus['action']}, "
            f"confidence={consensus['confidence']}%, "
            f"agreement={consensus['agreement']}"
        )

        return ConsensusResult(
            action=consensus["action"],
            confidence=consensus["confidence"],
            reasoning=consensus["reasoning"],
            primary_response=primary_response,
            validator_response=validator_response,
            agreement=consensus["agreement"],
            confidence_delta=abs(primary_confidence - validator_confidence),
            strategy_used=self.strategy,
            total_cost_usd=total_cost,
            total_latency_ms=total_latency
        )

    def _parse_response(self, content: str) -> Tuple[str, float, str]:
        """
        Parse LLM response into action, confidence, reasoning.

        Expected format (from whale_agent.py):
        Line 1: BUY / SELL / NOTHING
        Line 2: Reasoning
        Line 3: Confidence: X%

        Args:
            content: Raw LLM response

        Returns:
            Tuple of (action, confidence, reasoning)
        """
        lines = [line.strip() for line in content.split('\n') if line.strip()]

        if not lines:
            logger.warning("Empty response from LLM")
            return "NOTHING", 0.0, "No analysis provided"

        # Parse action (first line)
        action = lines[0].upper()
        if action not in ['BUY', 'SELL', 'NOTHING']:
            logger.warning(f"Invalid action '{action}', defaulting to NOTHING")
            action = "NOTHING"

        # Parse reasoning (middle lines)
        reasoning_lines = []
        confidence = 50.0  # Default

        for line in lines[1:]:
            if 'confidence' in line.lower():
                # Extract confidence percentage
                import re
                matches = re.findall(r'(\d+(?:\.\d+)?)%', line)
                if matches:
                    try:
                        confidence = float(matches[0])
                        confidence = max(0.0, min(100.0, confidence))
                    except ValueError:
                        pass
            else:
                reasoning_lines.append(line)

        reasoning = " ".join(reasoning_lines) if reasoning_lines else "No reasoning provided"

        return action, confidence, reasoning

    def _calculate_consensus(
        self,
        primary_action: str,
        primary_confidence: float,
        primary_reasoning: str,
        validator_action: str,
        validator_confidence: float,
        validator_reasoning: str
    ) -> Dict:
        """
        Calculate consensus between primary and validator.

        Args:
            primary_action: Action from primary LLM
            primary_confidence: Confidence from primary LLM
            primary_reasoning: Reasoning from primary LLM
            validator_action: Action from validator LLM
            validator_confidence: Confidence from validator LLM
            validator_reasoning: Reasoning from validator LLM

        Returns:
            Dict with final action, confidence, reasoning, agreement
        """
        agreement = primary_action == validator_action

        if self.strategy == ConsensusStrategy.UNANIMOUS:
            # Both must agree
            if agreement:
                # Take average confidence
                final_confidence = (primary_confidence + validator_confidence) / 2
                final_action = primary_action
            else:
                # Disagreement -> default to NOTHING
                final_confidence = 0.0
                final_action = "NOTHING"

            final_reasoning = (
                f"Primary: {primary_reasoning}\n"
                f"Validator: {validator_reasoning}"
            )

        elif self.strategy == ConsensusStrategy.MAJORITY:
            # Primary decides, validator can veto low confidence
            if agreement or validator_confidence < 30:
                final_action = primary_action
                final_confidence = primary_confidence
            else:
                # Validator vetoes
                final_action = validator_action
                final_confidence = validator_confidence

            final_reasoning = (
                f"Primary: {primary_reasoning}\n"
                f"Validator: {validator_reasoning}"
            )

        elif self.strategy == ConsensusStrategy.WEIGHTED:
            # Weighted by confidence
            if agreement:
                # Average confidence when agreeing
                final_confidence = (primary_confidence + validator_confidence) / 2
                final_action = primary_action
            else:
                # Use higher confidence
                if primary_confidence > validator_confidence:
                    final_action = primary_action
                    final_confidence = primary_confidence * 0.8  # Reduce due to disagreement
                else:
                    final_action = validator_action
                    final_confidence = validator_confidence * 0.8

            final_reasoning = (
                f"Primary ({primary_confidence}%): {primary_reasoning}\n"
                f"Validator ({validator_confidence}%): {validator_reasoning}"
            )

        elif self.strategy == ConsensusStrategy.VALIDATOR_OVERRIDE:
            # Validator can override
            if validator_confidence > primary_confidence:
                final_action = validator_action
                final_confidence = validator_confidence
            else:
                final_action = primary_action
                final_confidence = primary_confidence

            final_reasoning = (
                f"Primary: {primary_reasoning}\n"
                f"Validator: {validator_reasoning}"
            )

        else:
            # Default to primary
            final_action = primary_action
            final_confidence = primary_confidence
            final_reasoning = primary_reasoning

        return {
            "action": final_action,
            "confidence": final_confidence,
            "reasoning": final_reasoning,
            "agreement": agreement
        }
