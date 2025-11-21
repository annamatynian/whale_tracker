# Whale Tracker AI Module

AI-powered whale transaction analysis using multiple LLMs with consensus validation.

## Architecture

```
┌─────────────────────────────────────────────────┐
│         Whale AI Analyzer                       │
│  (Main entry point for whale analysis)          │
└───────────────────┬─────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────┐
│         Consensus Engine                         │
│  (Multi-LLM validation & consensus)              │
└────────┬────────────────────────┬────────────────┘
         │                        │
         ▼                        ▼
┌────────────────────┐   ┌────────────────────┐
│  Primary LLM       │   │  Validator LLM     │
│  (DeepSeek)        │   │  (Gemini/Groq)     │
│  - Fast analysis   │   │  - Validation      │
│  - Cost-effective  │   │  - FREE tier       │
└────────────────────┘   └────────────────────┘
```

## Features

### 🧠 Multi-LLM Consensus
- **Primary LLM (DeepSeek)**: Fast, cost-effective initial analysis
- **Validator LLM (Gemini/Groq)**: FREE validation and enrichment
- **Consensus Strategies**: UNANIMOUS, MAJORITY, WEIGHTED, VALIDATOR_OVERRIDE

### 📊 Comprehensive Analysis
- One-hop dump detection
- Statistical anomaly analysis
- Market context correlation
- Whale behavior patterns
- BUY/SELL/NOTHING recommendations
- Confidence scoring (0-100%)

### 💰 Cost-Effective
- DeepSeek: ~$0.0003 per analysis
- Gemini: FREE (1,500 requests/day)
- Groq: FREE (14,400 requests/day, ULTRA-FAST)

## Installation

### Required Dependencies

```bash
pip install openai google-generativeai
```

### Environment Variables

Create `.env` file:

```bash
# Required for DeepSeek (Primary LLM)
DEEPSEEK_KEY=sk-xxx

# Optional - Choose ONE validator:
GOOGLE_API_KEY=AIzaSyxxx  # For Gemini Flash (FREE, recommended)
GROQ_API_KEY=gsk_xxx       # For Groq (FREE, ultra-fast alternative)
```

## Quick Start

### Basic Usage

```python
import asyncio
from src.ai import create_whale_ai_analyzer, WhaleTransactionContext

async def main():
    # Create analyzer
    analyzer = await create_whale_ai_analyzer(
        primary_provider="deepseek",
        validator_provider="gemini",  # or "groq"
        enable_validator=True
    )

    # Prepare transaction context
    context = WhaleTransactionContext(
        whale_address="0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
        transaction_hash="0x123...",
        amount_eth=100.0,
        amount_usd=350000.0,
        destination_type="exchange",
        destination_name="Binance",
        is_one_hop=True,
        intermediate_address="0xabc...",
        confidence_score=85.0,
        # Market context
        current_eth_price=3500.0,
        price_change_24h=-2.5,
        volume_24h=15000000000,
        # Whale history
        whale_avg_transaction=150000.0,
        is_anomaly=True,
        anomaly_confidence=75.0
    )

    # Analyze
    result = await analyzer.analyze_transaction(context)

    # Results
    print(f"Action: {result.action}")
    print(f"Confidence: {result.confidence:.1f}%")
    print(f"Agreement: {result.agreement}")
    print(f"Reasoning: {result.reasoning}")
    print(f"Cost: ${result.total_cost_usd:.6f}")
    print(f"Latency: {result.total_latency_ms:.0f}ms")

asyncio.run(main())
```

### Output Example

```
Action: SELL
Confidence: 82.5%
Agreement: True
Reasoning: Primary (85%): One-hop transfer to Binance detected with 85% confidence. Large anomalous transaction (2.3x average). Market showing weakness (-2.5% 24h).
Validator (80%): Confirmed one-hop pattern. High confidence signals including gas correlation and nonce sequence. Combined with bearish market context, strong sell signal.
Cost: $0.000280
Latency: 1250ms
```

## Advanced Usage

### Custom Consensus Strategy

```python
from src.ai import ConsensusEngine, ConsensusStrategy
from src.ai.providers import DeepSeekProvider, GeminiProvider

# Create providers
primary = DeepSeekProvider(temperature=0.0, max_tokens=500)
validator = GeminiProvider(temperature=0.7, max_tokens=500)

# Create consensus engine with custom strategy
consensus = ConsensusEngine(
    primary_llm=primary,
    validator_llm=validator,
    strategy=ConsensusStrategy.UNANIMOUS,  # Both must agree
    min_confidence_threshold=70.0
)

# Use in analyzer
from src.ai import WhaleAIAnalyzer
analyzer = WhaleAIAnalyzer(
    consensus_engine=consensus,
    enable_analysis=True,
    min_confidence_for_action=70.0
)
```

### Disable Validator (Speed Mode)

```python
# Create analyzer without validator (faster, cheaper, but less reliable)
analyzer = await create_whale_ai_analyzer(
    primary_provider="deepseek",
    enable_validator=False  # Only use primary LLM
)
```

### Usage Statistics

```python
# Get usage stats
stats = analyzer.get_stats()
print(f"Primary LLM: {stats['primary']}")
print(f"Validator LLM: {stats['validator']}")

# Reset stats
analyzer.reset_stats()
```

## LLM Providers

### DeepSeek (Primary)

**Model**: `deepseek-chat` (V3)

**Pricing**:
- Input: $0.27 per 1M tokens
- Output: $1.10 per 1M tokens
- ~$0.0003 per whale analysis

**Best for**:
- Primary analysis
- Fast responses
- Cost-effective at scale

### Gemini Flash (Validator)

**Model**: `gemini-1.5-flash`

**Pricing**:
- 100% FREE
- 1,500 requests/day
- 15 RPM, 1M TPM

**Best for**:
- Validation
- Commercial use
- Reliable Google infrastructure

### Groq (Alternative Validator)

**Model**: `llama-3.3-70b-versatile`

**Pricing**:
- 100% FREE
- 14,400 requests/day
- 10 RPM

**Speed**:
- **300+ tokens/second** (ULTRA-FAST)

**Best for**:
- Speed-critical applications
- Real-time validation
- High-frequency analysis

## Consensus Strategies

### UNANIMOUS
Both LLMs must agree on action. If disagreement → NOTHING.

```python
strategy=ConsensusStrategy.UNANIMOUS
```

### MAJORITY
Primary decides, validator can veto if confidence < 30%.

```python
strategy=ConsensusStrategy.MAJORITY
```

### WEIGHTED (Default)
Weighted by confidence. If disagreement, use higher confidence (reduced 20%).

```python
strategy=ConsensusStrategy.WEIGHTED
```

### VALIDATOR_OVERRIDE
Validator can override if confidence > primary.

```python
strategy=ConsensusStrategy.VALIDATOR_OVERRIDE
```

## Testing

### Connection Test

```python
from src.ai.providers import DeepSeekProvider, GeminiProvider

# Test DeepSeek
deepseek = DeepSeekProvider()
if await deepseek.test_connection():
    print("✅ DeepSeek connected")

# Test Gemini
gemini = GeminiProvider()
if await gemini.test_connection():
    print("✅ Gemini connected")
```

### Mock Context for Testing

```python
context = WhaleTransactionContext(
    whale_address="0xtest",
    transaction_hash="0xtest",
    amount_eth=10.0,
    amount_usd=35000.0,
    destination_type="exchange",
    is_one_hop=False
)
```

## Integration with Whale Tracker

See `simple_whale_watcher.py` for integration example:

```python
from src.ai import create_whale_ai_analyzer, WhaleTransactionContext

# In SimpleWhaleWatcher.__init__()
self.ai_analyzer = await create_whale_ai_analyzer()

# When one-hop detected
context = WhaleTransactionContext(...)
ai_result = await self.ai_analyzer.analyze_transaction(context)

if ai_result.action == "SELL" and ai_result.confidence > 70:
    # Send alert with AI analysis
    await self.notifier.send_whale_ai_alert(ai_result)
```

## Performance

| Provider | Speed | Cost | Free Tier | Tokens/Sec |
|----------|-------|------|-----------|------------|
| DeepSeek | Fast | $0.0003 | No | ~50 |
| Gemini | Medium | FREE | 1,500/day | ~20 |
| Groq | ULTRA-FAST | FREE | 14,400/day | **300+** |

**Typical Analysis**:
- Single LLM: 500-1000ms
- Consensus (2 LLMs): 1200-2000ms
- Cost per analysis: $0.0003 (DeepSeek + Gemini)

## Error Handling

```python
from src.abstractions.llm_provider import LLMProviderError

try:
    result = await analyzer.analyze_transaction(context)
except LLMProviderError as e:
    print(f"LLM error: {e}")
    # Fallback to statistical analysis only
```

## Modular & Testable

All components are fully modular and independently testable:

- **LLM Providers**: Test each provider independently
- **Consensus Engine**: Test with mock LLMs
- **Whale AI Analyzer**: Test with mock consensus engine
- **No side effects**: Pure functions, async/await

## Future Enhancements

- [ ] Support for Claude Sonnet (Anthropic)
- [ ] Caching for repeated analyses
- [ ] Batch analysis for multiple transactions
- [ ] Fine-tuned models on whale data
- [ ] Multi-chain support (Solana, BSC, etc.)
- [ ] Integration with on-chain data APIs

## License

Part of Whale Tracker Project.

## Author

Whale Tracker Team
