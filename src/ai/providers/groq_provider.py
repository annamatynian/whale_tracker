"""
Groq LLM Provider
=================

Groq provider implementation using OpenAI-compatible API.

Groq offers:
- Llama 3.3 70B: 300+ tokens/second (BLAZING FAST)
- Mixtral 8x7B: Fast and efficient
- Gemma 2 9B: Lightweight

Pricing (FREE TIER):
- 100% FREE with rate limits
- No credit card required
- 14,400 requests/day (10 RPM)
- 25,000 tokens/day

Perfect for validator role due to:
- FREE tier
- ULTRA-FAST inference (300+ tokens/sec)
- Good quality open-source models
- No credit card required

Author: Whale Tracker Project
"""

import os
import time
import logging
from typing import List, Optional
from openai import OpenAI, AsyncOpenAI

from ...abstractions.llm_provider import (
    LLMProvider,
    LLMMessage,
    LLMResponse,
    LLMProviderError,
    LLMRole
)


logger = logging.getLogger(__name__)


class GroqProvider(LLMProvider):
    """
    Groq LLM provider using OpenAI-compatible API.

    Known for ULTRA-FAST inference speed (300+ tokens/sec).
    100% FREE!
    """

    # API Configuration
    BASE_URL = "https://api.groq.com/openai/v1"

    # Available models (free tier)
    MODEL_LLAMA_3_3_70B = "llama-3.3-70b-versatile"  # Fast & powerful
    MODEL_LLAMA_3_1_70B = "llama-3.1-70b-versatile"  # Alternative
    MODEL_MIXTRAL_8X7B = "mixtral-8x7b-32768"  # Good for long context
    MODEL_GEMMA_2_9B = "gemma2-9b-it"  # Lightweight

    # Rate limits (free tier)
    RATE_LIMITS = {
        "rpm": 10,  # requests per minute
        "rpd": 14400,  # requests per day (10 * 60 * 24)
        "tpd": 25000,  # tokens per day
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        role: LLMRole = LLMRole.VALIDATOR,
        use_async: bool = True
    ):
        """
        Initialize Groq provider.

        Args:
            api_key: Groq API key (loads from GROQ_API_KEY if None)
            model: Model to use (default: llama-3.3-70b-versatile)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            role: Role of this LLM (typically VALIDATOR)
            use_async: Use async client (recommended)
        """
        super().__init__(api_key, model, temperature, max_tokens, role)

        # Load API key from environment if not provided
        if not self.api_key:
            self.api_key = os.getenv("GROQ_API_KEY")

        if not self.api_key:
            raise ValueError(
                "Groq API key not provided. "
                "Set GROQ_API_KEY environment variable or pass api_key parameter."
            )

        # Set default model
        if not self.model:
            self.model = self.MODEL_LLAMA_3_3_70B

        # Initialize OpenAI-compatible client
        if use_async:
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.BASE_URL
            )
        else:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.BASE_URL
            )

        self.use_async = use_async

        logger.info(f"Groq provider initialized: model={self.model}, role={self.role.value}")

    @property
    def provider_name(self) -> str:
        """Provider name."""
        return "groq"

    @property
    def default_model(self) -> str:
        """Default model."""
        return self.MODEL_LLAMA_3_3_70B

    async def send_message(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Send messages to Groq and get response.

        Args:
            messages: List of messages in conversation
            temperature: Override temperature (optional)
            max_tokens: Override max tokens (optional)
            **kwargs: Additional parameters for Groq API

        Returns:
            LLMResponse with analysis

        Raises:
            LLMProviderError: If request fails
        """
        start_time = time.time()

        try:
            # Convert messages to OpenAI format
            formatted_messages = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

            # Use provided or default values
            temp = temperature if temperature is not None else self.temperature
            tokens = max_tokens if max_tokens is not None else self.max_tokens

            # Make API call
            logger.debug(f"Sending request to Groq: model={self.model}, messages={len(messages)}")

            if self.use_async:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=formatted_messages,
                    temperature=temp,
                    max_tokens=tokens,
                    **kwargs
                )
            else:
                # Sync fallback
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=formatted_messages,
                    temperature=temp,
                    max_tokens=tokens,
                    **kwargs
                )

            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000

            # Extract response
            content = response.choices[0].message.content.strip()

            # Calculate token usage
            total_tokens = response.usage.total_tokens if response.usage else 0
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0

            # Cost is $0.00 (free tier)
            cost = 0.0

            # Update statistics
            self._update_stats(total_tokens, cost, latency_ms)

            logger.info(
                f"Groq response received: tokens={total_tokens}, "
                f"cost=$0.00 (FREE), latency={latency_ms:.0f}ms "
                f"(~{output_tokens/(latency_ms/1000):.0f} tokens/sec)"
            )

            return LLMResponse(
                content=content,
                model=self.model,
                provider=self.provider_name,
                tokens_used=total_tokens,
                cost_usd=cost,
                latency_ms=latency_ms,
                raw_response=response
            )

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self._update_stats(0, 0.0, latency_ms, is_error=True)

            logger.error(f"Groq API error: {str(e)}")
            raise LLMProviderError(
                provider=self.provider_name,
                message=f"Failed to get response: {str(e)}",
                original_error=e
            )

    async def test_connection(self) -> bool:
        """
        Test Groq API connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            test_message = LLMMessage(role="user", content="test")
            response = await self.send_message(
                messages=[test_message],
                max_tokens=5
            )
            logger.info("Groq connection test: SUCCESS")
            return True

        except Exception as e:
            logger.error(f"Groq connection test FAILED: {str(e)}")
            return False

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost for token usage.

        For Groq FREE tier, cost is always $0.00.

        Args:
            input_tokens: Input tokens
            output_tokens: Output tokens

        Returns:
            0.0 (Groq is FREE)
        """
        return 0.0

    def get_rate_limits(self) -> dict:
        """
        Get rate limits for Groq free tier.

        Returns:
            Dict with rpm, rpd, tpd limits
        """
        return self.RATE_LIMITS.copy()
