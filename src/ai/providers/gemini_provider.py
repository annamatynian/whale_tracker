"""
Google Gemini Flash LLM Provider
=================================

Gemini Flash provider implementation using Google's Generative AI SDK.

Gemini Flash offers:
- Gemini 1.5 Flash: 1,500 requests/day FREE (fast, efficient)
- Gemini 2.5 Flash: 250 requests/day FREE (newer, more capable)

Pricing (FREE TIER):
- Input tokens: FREE
- Output tokens: FREE
- Commercial usage: ALLOWED
- Rate limits: 15 RPM, 1M TPM (1.5 Flash) / 10 RPM, 250K TPM (2.5 Flash)

Perfect for validator role due to:
- FREE tier
- Fast responses
- Good reasoning capabilities
- Reliable Google infrastructure

Author: Whale Tracker Project
"""

import os
import time
import logging
from typing import List, Optional

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("google-generativeai not installed. Install with: pip install google-generativeai")

from ...abstractions.llm_provider import (
    LLMProvider,
    LLMMessage,
    LLMResponse,
    LLMProviderError,
    LLMRole
)


logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """
    Google Gemini Flash provider.

    Uses Google's Generative AI SDK for async operations.
    100% FREE for our use case!
    """

    # Available models
    MODEL_FLASH_1_5 = "gemini-1.5-flash"  # 1,500 requests/day
    MODEL_FLASH_2_5 = "gemini-2.5-flash"  # 250 requests/day (newer)

    # Rate limits (free tier)
    RATE_LIMITS = {
        MODEL_FLASH_1_5: {
            "rpm": 15,  # requests per minute
            "tpm": 1_000_000,  # tokens per minute
            "rpd": 1500,  # requests per day
        },
        MODEL_FLASH_2_5: {
            "rpm": 10,
            "tpm": 250_000,
            "rpd": 250,
        }
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 500,
        role: LLMRole = LLMRole.VALIDATOR
    ):
        """
        Initialize Gemini provider.

        Args:
            api_key: Google API key (loads from GOOGLE_API_KEY if None)
            model: Model to use (default: gemini-1.5-flash)
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens in response
            role: Role of this LLM (typically VALIDATOR)
        """
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )

        super().__init__(api_key, model, temperature, max_tokens, role)

        # Load API key from environment if not provided
        if not self.api_key:
            self.api_key = os.getenv("GOOGLE_API_KEY")

        if not self.api_key:
            raise ValueError(
                "Google API key not provided. "
                "Set GOOGLE_API_KEY environment variable or pass api_key parameter."
            )

        # Configure Gemini
        genai.configure(api_key=self.api_key)

        # Set default model
        if not self.model:
            self.model = self.MODEL_FLASH_1_5

        # Initialize model
        self.gemini_model = genai.GenerativeModel(self.model)

        logger.info(f"Gemini provider initialized: model={self.model}, role={self.role.value}")

    @property
    def provider_name(self) -> str:
        """Provider name."""
        return "gemini"

    @property
    def default_model(self) -> str:
        """Default model."""
        return self.MODEL_FLASH_1_5

    async def send_message(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Send messages to Gemini and get response.

        Args:
            messages: List of messages in conversation
            temperature: Override temperature (optional)
            max_tokens: Override max tokens (optional)
            **kwargs: Additional parameters for Gemini API

        Returns:
            LLMResponse with analysis

        Raises:
            LLMProviderError: If request fails
        """
        start_time = time.time()

        try:
            # Convert messages to Gemini format
            # Gemini uses a different format - combine all messages into prompt
            prompt_parts = []

            for msg in messages:
                if msg.role == "system":
                    prompt_parts.append(f"Instructions: {msg.content}")
                elif msg.role == "user":
                    prompt_parts.append(f"User: {msg.content}")
                elif msg.role == "assistant":
                    prompt_parts.append(f"Assistant: {msg.content}")

            prompt = "\n\n".join(prompt_parts)

            # Use provided or default values
            temp = temperature if temperature is not None else self.temperature
            tokens = max_tokens if max_tokens is not None else self.max_tokens

            # Configure generation
            generation_config = genai.types.GenerationConfig(
                temperature=temp,
                max_output_tokens=tokens,
                **kwargs
            )

            # Make API call
            logger.debug(f"Sending request to Gemini: model={self.model}, messages={len(messages)}")

            response = await self.gemini_model.generate_content_async(
                prompt,
                generation_config=generation_config
            )

            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000

            # Extract response
            content = response.text.strip()

            # Estimate token usage (Gemini doesn't always provide this)
            # Rough estimate: 1 token ≈ 4 characters
            input_tokens = len(prompt) // 4
            output_tokens = len(content) // 4
            total_tokens = input_tokens + output_tokens

            # Cost is $0.00 (free tier)
            cost = 0.0

            # Update statistics
            self._update_stats(total_tokens, cost, latency_ms)

            logger.info(
                f"Gemini response received: tokens≈{total_tokens}, "
                f"cost=$0.00 (FREE), latency={latency_ms:.0f}ms"
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

            logger.error(f"Gemini API error: {str(e)}")
            raise LLMProviderError(
                provider=self.provider_name,
                message=f"Failed to get response: {str(e)}",
                original_error=e
            )

    async def test_connection(self) -> bool:
        """
        Test Gemini API connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            test_message = LLMMessage(role="user", content="test")
            response = await self.send_message(
                messages=[test_message],
                max_tokens=5
            )
            logger.info("Gemini connection test: SUCCESS")
            return True

        except Exception as e:
            logger.error(f"Gemini connection test FAILED: {str(e)}")
            return False

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost for token usage.

        For Gemini FREE tier, cost is always $0.00.

        Args:
            input_tokens: Input tokens
            output_tokens: Output tokens

        Returns:
            0.0 (Gemini is FREE)
        """
        return 0.0

    def get_rate_limits(self) -> dict:
        """
        Get rate limits for current model.

        Returns:
            Dict with rpm, tpm, rpd limits
        """
        return self.RATE_LIMITS.get(self.model, self.RATE_LIMITS[self.MODEL_FLASH_1_5])
