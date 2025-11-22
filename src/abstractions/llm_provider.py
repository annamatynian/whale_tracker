"""
LLM Provider Abstraction
========================

Abstract base class for Large Language Model providers.

This abstraction allows seamless switching between different LLM providers
(DeepSeek, Gemini, Groq, Claude, etc.) without changing business logic.

Author: Whale Tracker Project
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from enum import Enum


class LLMRole(Enum):
    """Role of the LLM in the system."""
    PRIMARY = "primary"  # Main analysis
    VALIDATOR = "validator"  # Validates primary analysis
    FALLBACK = "fallback"  # Backup if primary fails


@dataclass
class LLMMessage:
    """Message in LLM conversation."""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """Response from LLM."""
    content: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    latency_ms: Optional[float] = None
    raw_response: Optional[Any] = None


@dataclass
class LLMUsageStats:
    """Usage statistics for an LLM provider."""
    total_requests: int
    total_tokens: int
    total_cost_usd: float
    avg_latency_ms: float
    error_count: int


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All LLM integrations (DeepSeek, Gemini, Groq, etc.) must implement this interface.

    Features:
    - Async message sending
    - Token/cost tracking
    - Error handling
    - Rate limiting awareness
    - Model configuration
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        role: LLMRole = LLMRole.PRIMARY
    ):
        """
        Initialize LLM provider.

        Args:
            api_key: API key for the provider (if None, loads from env)
            model: Model name (if None, uses provider default)
            temperature: Sampling temperature (0.0 - 1.0)
            max_tokens: Maximum tokens in response
            role: Role of this LLM in the system
        """
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.role = role

        # Statistics
        self._stats = LLMUsageStats(
            total_requests=0,
            total_tokens=0,
            total_cost_usd=0.0,
            avg_latency_ms=0.0,
            error_count=0
        )

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Name of the LLM provider.

        Returns:
            Provider name (e.g., "deepseek", "gemini", "groq")
        """
        pass

    @property
    @abstractmethod
    def default_model(self) -> str:
        """
        Default model for this provider.

        Returns:
            Model identifier
        """
        pass

    @abstractmethod
    async def send_message(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Send messages to LLM and get response.

        Args:
            messages: List of messages in conversation
            temperature: Override default temperature (optional)
            max_tokens: Override default max tokens (optional)
            **kwargs: Provider-specific parameters

        Returns:
            LLMResponse with content and metadata

        Raises:
            LLMProviderError: If request fails
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test if provider is accessible and configured correctly.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost for given token usage.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        pass

    def get_stats(self) -> LLMUsageStats:
        """
        Get usage statistics for this provider.

        Returns:
            LLMUsageStats object
        """
        return self._stats

    def reset_stats(self) -> None:
        """Reset usage statistics."""
        self._stats = LLMUsageStats(
            total_requests=0,
            total_tokens=0,
            total_cost_usd=0.0,
            avg_latency_ms=0.0,
            error_count=0
        )

    def _update_stats(
        self,
        tokens: int,
        cost: float,
        latency_ms: float,
        is_error: bool = False
    ) -> None:
        """
        Update internal statistics.

        Args:
            tokens: Tokens used in request
            cost: Cost of request in USD
            latency_ms: Request latency in milliseconds
            is_error: Whether request resulted in error
        """
        self._stats.total_requests += 1
        self._stats.total_tokens += tokens
        self._stats.total_cost_usd += cost

        if is_error:
            self._stats.error_count += 1

        # Update average latency
        n = self._stats.total_requests
        self._stats.avg_latency_ms = (
            (self._stats.avg_latency_ms * (n - 1) + latency_ms) / n
        )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<{self.__class__.__name__} "
            f"provider={self.provider_name} "
            f"model={self.model or self.default_model} "
            f"role={self.role.value}>"
        )


class LLMProviderError(Exception):
    """Exception raised when LLM provider encounters an error."""

    def __init__(self, provider: str, message: str, original_error: Optional[Exception] = None):
        """
        Initialize error.

        Args:
            provider: Name of the provider
            message: Error message
            original_error: Original exception if available
        """
        self.provider = provider
        self.original_error = original_error
        super().__init__(f"[{provider}] {message}")
