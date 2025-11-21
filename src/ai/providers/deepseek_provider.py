"""
DeepSeek LLM Provider
=====================

DeepSeek provider implementation using OpenAI-compatible API.

DeepSeek offers:
- deepseek-chat (V3): Fast, efficient, cost-effective
- deepseek-reasoner (R1): Advanced reasoning capabilities

Pricing (as of 2025):
- Very competitive pricing
- Good balance of quality and speed

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


class DeepSeekProvider(LLMProvider):
    """
    DeepSeek LLM provider using OpenAI-compatible API.

    Supports both sync and async operations.
    """

    # API Configuration
    BASE_URL = "https://api.deepseek.com"

    # Available models
    MODEL_CHAT = "deepseek-chat"  # V3 - Fast & efficient
    MODEL_REASONER = "deepseek-reasoner"  # R1 - Advanced reasoning

    # Pricing (USD per 1M tokens)
    PRICING = {
        MODEL_CHAT: {
            "input": 0.27,  # $0.27 per 1M input tokens
            "output": 1.10,  # $1.10 per 1M output tokens
        },
        MODEL_REASONER: {
            "input": 0.55,  # $0.55 per 1M input tokens
            "output": 2.19,  # $2.19 per 1M output tokens
        }
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.0,  # Lower for more deterministic analysis
        max_tokens: int = 500,
        role: LLMRole = LLMRole.PRIMARY,
        use_async: bool = True
    ):
        """
        Initialize DeepSeek provider.

        Args:
            api_key: DeepSeek API key (loads from DEEPSEEK_KEY if None)
            model: Model to use (default: deepseek-chat)
            temperature: Sampling temperature (0.0-1.0, default 0.0 for analysis)
            max_tokens: Maximum tokens in response
            role: Role of this LLM
            use_async: Use async client (recommended)
        """
        super().__init__(api_key, model, temperature, max_tokens, role)

        # Load API key from environment if not provided
        if not self.api_key:
            self.api_key = os.getenv("DEEPSEEK_KEY")

        if not self.api_key:
            raise ValueError(
                "DeepSeek API key not provided. "
                "Set DEEPSEEK_KEY environment variable or pass api_key parameter."
            )

        # Set default model
        if not self.model:
            self.model = self.MODEL_CHAT

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

        logger.info(f"DeepSeek provider initialized: model={self.model}, role={self.role.value}")

    @property
    def provider_name(self) -> str:
        """Provider name."""
        return "deepseek"

    @property
    def default_model(self) -> str:
        """Default model."""
        return self.MODEL_CHAT

    async def send_message(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Send messages to DeepSeek and get response.

        Args:
            messages: List of messages in conversation
            temperature: Override temperature (optional)
            max_tokens: Override max tokens (optional)
            **kwargs: Additional parameters for DeepSeek API

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
            logger.debug(f"Sending request to DeepSeek: model={self.model}, messages={len(messages)}")

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

            # Calculate token usage and cost
            total_tokens = response.usage.total_tokens if response.usage else 0
            input_tokens = response.usage.prompt_tokens if response.usage else 0
            output_tokens = response.usage.completion_tokens if response.usage else 0
            cost = self.estimate_cost(input_tokens, output_tokens)

            # Update statistics
            self._update_stats(total_tokens, cost, latency_ms)

            logger.info(
                f"DeepSeek response received: tokens={total_tokens}, "
                f"cost=${cost:.6f}, latency={latency_ms:.0f}ms"
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

            logger.error(f"DeepSeek API error: {str(e)}")
            raise LLMProviderError(
                provider=self.provider_name,
                message=f"Failed to get response: {str(e)}",
                original_error=e
            )

    async def test_connection(self) -> bool:
        """
        Test DeepSeek API connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            test_message = LLMMessage(role="user", content="test")
            response = await self.send_message(
                messages=[test_message],
                max_tokens=5
            )
            logger.info("DeepSeek connection test: SUCCESS")
            return True

        except Exception as e:
            logger.error(f"DeepSeek connection test FAILED: {str(e)}")
            return False

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost for token usage.

        Args:
            input_tokens: Input tokens
            output_tokens: Output tokens

        Returns:
            Estimated cost in USD
        """
        if self.model not in self.PRICING:
            logger.warning(f"Unknown model {self.model}, using default pricing")
            pricing = self.PRICING[self.MODEL_CHAT]
        else:
            pricing = self.PRICING[self.model]

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost
