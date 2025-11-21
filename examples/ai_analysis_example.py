"""
AI Analysis Example
===================

Example demonstrating how to use the AI module for whale transaction analysis.

This example shows:
1. Setting up AI analyzer with DeepSeek + Gemini
2. Analyzing whale transactions
3. Handling consensus results
4. Integration with existing whale monitoring

Author: Whale Tracker Project
"""

import asyncio
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def example_basic_usage():
    """Basic usage example."""
    from src.ai import create_whale_ai_analyzer, WhaleTransactionContext

    logger.info("=== Example 1: Basic AI Analysis ===\n")

    # Create analyzer (DeepSeek + Gemini)
    analyzer = await create_whale_ai_analyzer(
        primary_provider="deepseek",
        validator_provider="gemini",
        enable_validator=True
    )

    # Create transaction context
    context = WhaleTransactionContext(
        whale_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        transaction_hash="0x123abc...",
        amount_eth=150.0,
        amount_usd=525000.0,
        destination_type="exchange",
        destination_name="Binance",
        # One-hop detection
        is_one_hop=True,
        intermediate_address="0xdef456...",
        confidence_score=88.0,
        signal_breakdown={
            "time": {"confidence": 50, "type": "golden_window"},
            "gas": {"confidence": 85, "type": "exact_match"},
            "nonce": {"confidence": 95, "type": "immediate"},
            "profile": {"confidence": 80, "type": "fresh_burner"}
        },
        # Market context
        current_eth_price=3500.0,
        price_change_24h=-3.2,
        volume_24h=18000000000,
        volatility=2.8,
        # Whale history
        whale_avg_transaction=200000.0,
        transaction_frequency=48.0,  # hours
        is_anomaly=True,
        anomaly_confidence=82.0
    )

    # Analyze
    logger.info("Analyzing whale transaction...")
    result = await analyzer.analyze_transaction(context)

    # Display results
    logger.info("\n" + "="*60)
    logger.info("AI ANALYSIS RESULTS")
    logger.info("="*60)
    logger.info(f"Action: {result.action}")
    logger.info(f"Confidence: {result.confidence:.1f}%")
    logger.info(f"Agreement: {'✅ YES' if result.agreement else '❌ NO'}")
    logger.info(f"Confidence Delta: {result.confidence_delta:.1f}%")
    logger.info(f"\nReasoning:\n{result.reasoning}")
    logger.info(f"\nPerformance:")
    logger.info(f"  Cost: ${result.total_cost_usd:.6f}")
    logger.info(f"  Latency: {result.total_latency_ms:.0f}ms")
    logger.info(f"  Primary: {result.primary_response.provider}")
    logger.info(f"  Validator: {result.validator_response.provider if result.validator_response else 'None'}")
    logger.info("="*60 + "\n")

    return result


async def example_without_validator():
    """Example without validator (faster, cheaper)."""
    from src.ai import create_whale_ai_analyzer, WhaleTransactionContext

    logger.info("=== Example 2: Without Validator (Speed Mode) ===\n")

    # Create analyzer without validator
    analyzer = await create_whale_ai_analyzer(
        primary_provider="deepseek",
        enable_validator=False  # Faster but less reliable
    )

    # Simple context
    context = WhaleTransactionContext(
        whale_address="0xabc123...",
        transaction_hash="0x789def...",
        amount_eth=50.0,
        amount_usd=175000.0,
        destination_type="exchange",
        is_one_hop=False
    )

    result = await analyzer.analyze_transaction(context)

    logger.info(f"Result: {result.action} (Confidence: {result.confidence:.1f}%)")
    logger.info(f"Latency: {result.total_latency_ms:.0f}ms (faster without validator)")
    logger.info(f"Cost: ${result.total_cost_usd:.6f}\n")


async def example_with_groq():
    """Example using Groq (ultra-fast validator)."""
    from src.ai import create_whale_ai_analyzer, WhaleTransactionContext

    logger.info("=== Example 3: With Groq (Ultra-Fast Validator) ===\n")

    # Create analyzer with Groq validator
    analyzer = await create_whale_ai_analyzer(
        primary_provider="deepseek",
        validator_provider="groq",  # 300+ tokens/sec!
        enable_validator=True
    )

    context = WhaleTransactionContext(
        whale_address="0xwhale...",
        transaction_hash="0xtx...",
        amount_eth=200.0,
        amount_usd=700000.0,
        destination_type="unknown",
        is_one_hop=True,
        confidence_score=75.0
    )

    result = await analyzer.analyze_transaction(context)

    logger.info(f"Result: {result.action} (Confidence: {result.confidence:.1f}%)")
    logger.info(f"Latency: {result.total_latency_ms:.0f}ms (Groq is ULTRA-FAST)")
    logger.info(f"Agreement: {result.agreement}\n")


async def example_usage_stats():
    """Example showing usage statistics."""
    from src.ai import create_whale_ai_analyzer, WhaleTransactionContext

    logger.info("=== Example 4: Usage Statistics ===\n")

    analyzer = await create_whale_ai_analyzer()

    # Run multiple analyses
    for i in range(3):
        context = WhaleTransactionContext(
            whale_address=f"0xwhale{i}...",
            transaction_hash=f"0xtx{i}...",
            amount_eth=100.0 + i*50,
            amount_usd=350000.0 + i*175000,
            destination_type="exchange",
            is_one_hop=i % 2 == 0
        )
        await analyzer.analyze_transaction(context)

    # Get stats
    stats = analyzer.get_stats()

    logger.info("Primary LLM Stats:")
    for key, value in stats['primary'].items():
        logger.info(f"  {key}: {value}")

    if 'validator' in stats:
        logger.info("\nValidator LLM Stats:")
        for key, value in stats['validator'].items():
            logger.info(f"  {key}: {value}")

    logger.info("")


async def example_integration_with_whale_watcher():
    """Example showing integration with SimpleWhaleWatcher."""
    logger.info("=== Example 5: Integration with Whale Watcher ===\n")

    # This is how you would integrate AI analysis in SimpleWhaleWatcher
    logger.info("Integration pattern:")
    logger.info("""
    # In SimpleWhaleWatcher.__init__():
    from src.ai import create_whale_ai_analyzer

    self.ai_analyzer = await create_whale_ai_analyzer(
        primary_provider="deepseek",
        validator_provider="gemini",
        enable_validator=True
    )

    # When one-hop detected in _check_advanced_one_hop():
    if average_confidence > 60:
        # Prepare AI context
        from src.ai import WhaleTransactionContext

        ai_context = WhaleTransactionContext(
            whale_address=whale_address,
            transaction_hash=whale_tx.get('hash', ''),
            amount_eth=amount_eth,
            amount_usd=amount_usd,
            destination_type="exchange",
            destination_name=exchange_info.name,
            is_one_hop=True,
            intermediate_address=intermediate,
            confidence_score=average_confidence,
            signal_breakdown=signals,
            current_eth_price=3500.0,  # Get from price provider
            price_change_24h=price_change,
            whale_avg_transaction=self.analyzer.get_whale_stats(whale_address).avg_amount_usd,
            is_anomaly=True,
            anomaly_confidence=average_confidence
        )

        # Get AI analysis
        ai_result = await self.ai_analyzer.analyze_transaction(ai_context)

        # Include AI analysis in alert
        if ai_result.action in ["SELL", "BUY"] and ai_result.confidence > 60:
            await self.notifier.send_whale_onehop_alert(
                whale_address=whale_address,
                whale_tx={...},
                intermediate_address=intermediate,
                onehop_result={
                    ...,
                    'ai_action': ai_result.action,
                    'ai_confidence': ai_result.confidence,
                    'ai_reasoning': ai_result.reasoning
                }
            )
    """)

    logger.info("\nThis provides:")
    logger.info("  ✅ Technical detection (gas, nonce, profiling)")
    logger.info("  ✅ AI-powered market context analysis")
    logger.info("  ✅ Multi-LLM consensus validation")
    logger.info("  ✅ Actionable BUY/SELL/NOTHING signals")
    logger.info("")


async def main():
    """Run all examples."""
    logger.info("="*60)
    logger.info("WHALE TRACKER AI MODULE - EXAMPLES")
    logger.info("="*60 + "\n")

    try:
        # Example 1: Basic usage
        await example_basic_usage()

        # Example 2: Without validator
        await example_without_validator()

        # Example 3: With Groq
        # await example_with_groq()  # Uncomment if you have GROQ_API_KEY

        # Example 4: Usage stats
        await example_usage_stats()

        # Example 5: Integration pattern
        await example_integration_with_whale_watcher()

        logger.info("="*60)
        logger.info("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"Example failed: {str(e)}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
