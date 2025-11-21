# Whale Tracker - Development Roadmap

## Timeline Overview

```
Phase 1: MVP                    ✅ COMPLETE
    └─ Simple whale tracking
    └─ Basic one-hop detection
    └─ Telegram alerts

Phase 2: Advanced One-Hop       📋 2-3 weeks
    └─ 10 advanced signals
    └─ Database integration
    └─ Price impact tracking

Phase 3: Pattern Recognition    📋 1-2 months
    └─ ML-based patterns
    └─ Behavior classification
    └─ Predictive analytics

Phase 4: AI Analysis           📋 2-3 months
    └─ LLM integration
    └─ Natural language insights
    └─ Trading recommendations
```

---

## Phase 1: MVP ✅ COMPLETE

**Duration:** Completed
**Status:** 100% - Ready for first run

### Completed Features

#### Core Infrastructure ✅
- [x] YAML-based configuration system
- [x] Environment management (dev/prod)
- [x] .env variable support
- [x] Logging with file rotation
- [x] Error handling framework

#### Blockchain Integration ✅
- [x] Web3Manager with RPC failover (Infura → Alchemy → Ankr)
- [x] Mock mode for testing
- [x] Balance checking
- [x] Transaction retrieval
- [x] Block data access

#### Whale Monitoring ✅
- [x] Exchange address database (30+ addresses)
- [x] Address classification system
- [x] Statistical anomaly detection (rolling average)
- [x] Per-whale monitoring
- [x] Basic one-hop detection (time + amount correlation)

#### Notifications ✅
- [x] Telegram integration
- [x] Whale-specific alert formatting
- [x] Alert cooldown system
- [x] Error handling

#### Orchestration ✅
- [x] Main orchestrator with component lifecycle
- [x] APScheduler integration (periodic checks)
- [x] Graceful shutdown (SIGINT/SIGTERM)
- [x] CLI interface (--once flag)

#### Testing ✅
- [x] 139 unit tests (all passing)
- [x] Mock-based testing
- [x] Async test support

### Metrics
```
Lines of Code:     ~3,500
Unit Tests:        139/139 ✅
Components:        6/6 complete
Documentation:     Comprehensive
```

### Next Immediate Step
```bash
# First run and validation
1. Create .env file
2. Add API keys (Infura, Telegram)
3. Add whale addresses to monitor
4. Run: python main.py --once
5. Monitor for 24-48 hours
6. Collect feedback and bugs
```

---

## Phase 2: Advanced One-Hop + Price Impact

**Duration:** 2-3 weeks
**Priority:** HIGH
**Status:** 10% (documentation complete)

### Goals
1. Implement 10 advanced one-hop detection signals
2. Add database layer for persistent storage
3. Integrate price impact tracking
4. Achieve 90%+ detection accuracy

### Milestones

#### Milestone 2.1: Database Setup (Week 1)
**Priority:** CRITICAL

**Tasks:**
- [ ] PostgreSQL setup and configuration
- [ ] Database schema implementation
- [ ] SQLAlchemy ORM models
- [ ] Alembic migrations setup
- [ ] Data migration from in-memory to DB

**Deliverables:**
```python
# models/transaction.py
# models/whale_activity.py
# models/one_hop_detection.py
# alembic/versions/001_initial_schema.py
```

**Database Tables:**
- `whales` - Monitored whale addresses
- `transactions` - All transactions (whale + intermediate + exchange)
- `one_hop_detections` - Detected one-hop chains
- `multi_hop_chains` - 2-4 hop chains
- `dex_swaps` - DEX interactions
- `known_addresses` - Exchange/bridge/DEX database
- `address_relationships` - Graph edges

**Tests:**
- Database connection tests
- Model CRUD tests
- Migration tests
- Performance tests (query optimization)

#### Milestone 2.2: Top Priority Signals (Week 1-2)
**Priority:** HIGH

##### Signal #3: Nonce Tracking (HIGHEST PRIORITY)
**Effort:** 2-3 days
**Confidence boost:** +95 (STRONGEST SIGNAL)

**Tasks:**
- [ ] Integrate Etherscan API for nonce queries
- [ ] Implement nonce gap detection
- [ ] Add caching for nonce lookups
- [ ] Unit tests (10 tests)

**Implementation:**
```python
# src/analyzers/nonce_tracker.py
class NonceTracker:
    async def get_nonce_at_block(address, block_number)
    async def detect_sequential_nonces(whale_tx, intermediate_tx)
    async def calculate_nonce_gap_confidence(gap)
```

**API Integration:**
- Etherscan API key required
- Rate limiting: 5 calls/sec
- Caching strategy для reduced API usage

##### Signal #2: Gas Price Correlation
**Effort:** 1-2 days
**Confidence boost:** +80

**Tasks:**
- [ ] Extract gas price from transaction data
- [ ] Implement exact/close match detection
- [ ] EIP-1559 priority fee analysis
- [ ] Unit tests (8 tests)

**Implementation:**
```python
# src/analyzers/gas_correlator.py
class GasCorrelator:
    def check_gas_price_match(whale_tx, intermediate_tx)
    def check_priority_fee_match(whale_tx, intermediate_tx)
    def calculate_gas_correlation_confidence(whale_gas, intermediate_gas)
```

##### Signal #5: Intermediate Address Profiling
**Effort:** 3-4 days
**Confidence boost:** +75

**Tasks:**
- [ ] Fresh address detection (age < 24h)
- [ ] Empty address detection (zero balance before)
- [ ] Single-use pattern detection
- [ ] Reused intermediate detection
- [ ] Unit tests (12 tests)

**Implementation:**
```python
# src/analyzers/address_profiler.py
class AddressProfiler:
    async def is_fresh_address(address)
    async def was_empty_before(address, block_number)
    async def is_single_use_burner(address)
    async def detect_reuse_pattern(address)
```

#### Milestone 2.3: Advanced Signals (Week 2-3)
**Priority:** MEDIUM

##### Signal #4: Amount Correlation + Split Detection
**Effort:** 2-3 days
**Confidence boost:** +70

**Tasks:**
- [ ] Exact amount matching (accounting for gas)
- [ ] Split pattern detection
- [ ] Consolidation pattern detection
- [ ] Unit tests (10 tests)

##### Signal #8: DEX Interaction Detection
**Effort:** 3-4 days
**Confidence boost:** +90 (when detected)

**Tasks:**
- [ ] DEX router address database
- [ ] ABI decoding for swap transactions
- [ ] Stablecoin conversion detection
- [ ] Token transfer tracking
- [ ] Unit tests (15 tests)

**Complexity:**
- Requires ABI parsing
- Multiple DEX protocols (Uniswap V2/V3, SushiSwap, 1inch)
- Token transfer event logs

##### Signal #7: Multi-Hop Detection
**Effort:** 3-4 days
**Confidence boost:** +60

**Tasks:**
- [ ] Recursive chain following (2-4 hops)
- [ ] Path confidence scoring
- [ ] Cycle detection (avoid infinite loops)
- [ ] Database storage for chains
- [ ] Unit tests (12 tests)

**Implementation:**
```python
# src/analyzers/multihop_detector.py
class MultiHopDetector:
    async def detect_chain(whale_tx, max_hops=4)
    def score_chain_confidence(chain)
    def find_all_paths_to_exchanges(whale_addr)
```

#### Milestone 2.4: Price Impact Tracking (Week 3)
**Priority:** MEDIUM

**Tasks:**
- [ ] CoinGecko API integration
- [ ] Price snapshot at transaction time
- [ ] Scheduled price checks (1h, 6h, 24h after)
- [ ] Impact percentage calculation
- [ ] Correlation analysis (whale activity ↔ price)
- [ ] Unit tests (10 tests)

**Implementation:**
```python
# src/trackers/price_tracker.py
class PriceTracker:
    async def get_token_price(token_address, timestamp)
    async def track_price_impact(tx_hash)
    async def schedule_delayed_checks(tx_hash)
    async def calculate_impact_percentage(before, after)
```

**Database:**
```sql
CREATE TABLE price_impacts (
    transaction_hash VARCHAR(66) PRIMARY KEY,
    token_address VARCHAR(42),
    price_before DECIMAL(36, 18),
    price_1h_after DECIMAL(36, 18),
    price_6h_after DECIMAL(36, 18),
    price_24h_after DECIMAL(36, 18),
    impact_percentage DECIMAL(8, 4)
);
```

#### Milestone 2.5: Integration & Testing (Week 3)
**Priority:** HIGH

**Tasks:**
- [ ] Integrate all signals into SimpleWhaleWatcher
- [ ] Composite confidence scoring
- [ ] Integration tests (20 tests)
- [ ] Performance optimization
- [ ] End-to-end testing with real data
- [ ] Documentation updates

**Confidence Scoring Algorithm:**
```python
def calculate_total_confidence(signals):
    """
    Combine multiple signals into total confidence score
    """
    # Weighted average of detected signals
    weights = {
        'nonce': 1.0,        # Strongest
        'gas': 0.9,
        'dex': 0.95,
        'time': 0.8,
        'amount': 0.75,
        'address_profile': 0.7,
        'multihop': 0.6,
    }

    total = 0
    total_weight = 0

    for signal_name, signal_data in signals.items():
        if signal_data['detected']:
            total += signal_data['confidence'] * weights[signal_name]
            total_weight += weights[signal_name]

    if total_weight == 0:
        return 0

    return min(100, int(total / total_weight))
```

### Deliverables Phase 2

**Code:**
- [ ] 5 new analyzer modules (~1500 lines)
- [ ] Database layer (~500 lines)
- [ ] Price tracking module (~300 lines)
- [ ] 80+ new unit tests

**Documentation:**
- [ ] API documentation
- [ ] Database schema documentation
- [ ] Configuration guide updates
- [ ] Deployment guide

**Metrics to achieve:**
- One-hop detection accuracy: >90%
- False positive rate: <5%
- Average detection time: <5 minutes
- Database query performance: <100ms

### Risks & Mitigation

**Risk:** API rate limits (Etherscan, CoinGecko)
**Mitigation:** Aggressive caching, rate limiting, fallback strategies

**Risk:** Database performance with large transaction volume
**Mitigation:** Proper indexing, query optimization, partitioning

**Risk:** Complex signal integration bugs
**Mitigation:** Extensive unit + integration testing, staged rollout

---

## Phase 3: Pattern Recognition & ML

**Duration:** 1-2 months
**Priority:** MEDIUM
**Status:** 0% (planned)

### Goals
1. Classify whales by behavior patterns
2. Predict whale actions
3. Entity resolution (cluster related addresses)
4. Build historical pattern database

### Prerequisites
- Phase 2 complete
- 3+ months of historical data collected
- Database with sufficient transaction history

### Milestones

#### Milestone 3.1: Data Collection & Feature Engineering (Week 1-2)

**Tasks:**
- [ ] Collect 3+ months of whale transaction data
- [ ] Feature extraction from transactions
- [ ] Temporal feature engineering
- [ ] Network feature engineering

**Features to extract:**
```python
# Transaction features
- tx_frequency (transactions per day/week)
- avg_tx_amount
- tx_time_of_day_distribution
- tx_day_of_week_distribution
- preferred_exchanges
- one_hop_usage_percentage

# Network features
- unique_addresses_interacted_with
- clustering_coefficient
- centrality_measures
- community_membership

# Temporal features
- activity_bursts
- inactivity_periods
- seasonality_patterns
```

#### Milestone 3.2: Whale Behavior Classification (Week 3-4)

**Goal:** Classify whales into behavior categories

**Categories:**
1. **Accumulator** - Buys on dips, HODLs
2. **Dumper** - Sells on pumps, takes profit
3. **Market Maker** - Two-way activity, provides liquidity
4. **Wash Trader** - Circular transactions, fake volume
5. **Arbitrageur** - Exploits price differences across exchanges

**Implementation:**
```python
# src/ml/whale_classifier.py
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans

class WhaleClassifier:
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100)
        self.clusterer = KMeans(n_clusters=5)

    def extract_features(self, whale_address):
        """Extract feature vector for whale"""
        # Transaction patterns
        # Network patterns
        # Temporal patterns
        return feature_vector

    def classify(self, whale_address):
        """Classify whale behavior"""
        features = self.extract_features(whale_address)
        prediction = self.model.predict([features])
        confidence = self.model.predict_proba([features])
        return {
            'category': CATEGORIES[prediction[0]],
            'confidence': max(confidence[0])
        }

    def train(self, labeled_data):
        """Train classifier on labeled whale data"""
        X = [self.extract_features(addr) for addr, _ in labeled_data]
        y = [label for _, label in labeled_data]
        self.model.fit(X, y)
```

**Deliverables:**
- Trained classifier model
- Validation metrics (accuracy, precision, recall)
- Classification API endpoint

#### Milestone 3.3: Entity Resolution & Clustering (Week 5-6)

**Goal:** Identify addresses belonging to same entity

**Approaches:**
1. **Graph-based clustering**
   - Build transaction graph
   - Apply community detection (Louvain, Label Propagation)
   - Identify strongly connected components

2. **Heuristic-based clustering**
   - Addresses that always transact together
   - Shared gas price patterns
   - Temporal correlation of activity

**Implementation:**
```python
# src/ml/entity_resolver.py
import networkx as nx

class EntityResolver:
    def __init__(self):
        self.graph = nx.DiGraph()

    def build_graph(self, transactions):
        """Build transaction graph"""
        for tx in transactions:
            self.graph.add_edge(
                tx.from_address,
                tx.to_address,
                weight=tx.amount,
                timestamp=tx.timestamp
            )

    def detect_entity_clusters(self):
        """Find clusters of addresses likely owned by same entity"""
        # Convert to undirected for community detection
        G_undirected = self.graph.to_undirected()

        # Louvain community detection
        communities = nx.community.louvain_communities(G_undirected)

        # Score each community
        scored_communities = []
        for community in communities:
            score = self.score_community_cohesion(community)
            if score > 0.7:  # High cohesion
                scored_communities.append({
                    'addresses': list(community),
                    'cohesion_score': score,
                    'likely_same_entity': True
                })

        return scored_communities

    def score_community_cohesion(self, community):
        """Score how likely addresses are same entity"""
        # Check gas price correlation
        # Check temporal correlation
        # Check amount patterns
        # Return 0.0-1.0 score
        pass
```

#### Milestone 3.4: Predictive Models (Week 7-8)

**Goal:** Predict whale's next action

**Models:**
1. **Time-to-next-transaction predictor**
2. **Dump probability predictor**
3. **Target price predictor**

**Implementation:**
```python
# src/ml/predictor.py
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.ensemble import GradientBoostingClassifier

class WhaleActionPredictor:
    def __init__(self):
        self.time_predictor = GradientBoostingRegressor()
        self.dump_classifier = GradientBoostingClassifier()

    def predict_next_transaction_time(self, whale_address):
        """Predict when whale will transact next"""
        features = self.extract_temporal_features(whale_address)
        hours_until_next = self.time_predictor.predict([features])[0]
        return {
            'predicted_time': datetime.now() + timedelta(hours=hours_until_next),
            'confidence': self.get_prediction_confidence(features)
        }

    def predict_dump_probability(self, whale_address, current_price):
        """Predict probability of dump in next 24h"""
        features = self.extract_dump_features(whale_address, current_price)
        dump_prob = self.dump_classifier.predict_proba([features])[0][1]
        return {
            'dump_probability': dump_prob,
            'recommendation': 'HIGH_RISK' if dump_prob > 0.7 else 'NORMAL'
        }
```

### Deliverables Phase 3

**Code:**
- [ ] ML pipeline (~1000 lines)
- [ ] Feature engineering module (~500 lines)
- [ ] Classifier models
- [ ] Predictor models
- [ ] 50+ ML tests

**Models:**
- [ ] Whale behavior classifier (trained)
- [ ] Entity resolution model
- [ ] Dump predictor model

**Documentation:**
- [ ] ML model documentation
- [ ] Feature engineering guide
- [ ] Model training guide
- [ ] Prediction API docs

**Metrics to achieve:**
- Classifier accuracy: >85%
- Entity resolution precision: >80%
- Dump prediction accuracy: >70%

---

## Phase 4: AI Analysis & Insights

**Duration:** 2-3 months
**Priority:** LOW (future enhancement)
**Status:** 0% (planned)

### Goals
1. LLM-based pattern interpretation
2. Natural language insights generation
3. News/social sentiment correlation
4. Automated trading recommendations

### Milestones

#### Milestone 4.1: LLM Integration (Week 1-2)

**Tasks:**
- [ ] OpenAI/Anthropic API integration
- [ ] Prompt engineering for whale analysis
- [ ] Context management (RAG approach)
- [ ] Response parsing and validation

**Implementation:**
```python
# src/ai/llm_analyzer.py
from anthropic import Anthropic

class LLMAnalyzer:
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    async def analyze_whale_activity(self, whale_address, recent_txs):
        """Generate natural language insights"""

        prompt = f"""
        Analyze the recent activity of whale {whale_address}:

        Recent transactions:
        {format_transactions_for_llm(recent_txs)}

        Whale classification: {get_whale_classification(whale_address)}
        Historical patterns: {get_historical_patterns(whale_address)}
        Current market conditions: {get_market_context()}

        Provide:
        1. Summary of recent activity
        2. Interpretation of behavior
        3. Potential intentions
        4. Risk assessment
        5. Recommended actions for traders
        """

        response = await self.client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        return self.parse_llm_response(response.content[0].text)
```

#### Milestone 4.2: News & Sentiment Correlation (Week 3-4)

**Tasks:**
- [ ] News API integration (CryptoNews, NewsAPI)
- [ ] Social sentiment tracking (Twitter/X, Reddit)
- [ ] Correlation analysis (whale activity ↔ news/sentiment)
- [ ] Event detection

**Example correlation:**
```
Whale dumps 1000 ETH
    ↓
Check recent news:
    - SEC announces crypto regulation hearing (2 hours ago)
    - Major DeFi exploit reported (4 hours ago)
    ↓
Correlation: Likely reacting to regulatory news
Insight: "Whale appears to be de-risking ahead of regulatory uncertainty"
```

#### Milestone 4.3: Trading Advisor (Week 5-6)

**Goal:** Automated trading recommendations based on whale activity

**Implementation:**
```python
# src/ai/trading_advisor.py

class TradingAdvisor:
    async def generate_recommendation(self, whale_alert):
        """
        Generate trading recommendation based on whale activity
        """
        # Analyze whale's historical accuracy
        whale_accuracy = self.analyze_historical_whale_accuracy(whale_alert.whale_address)

        # Get current market conditions
        market_conditions = await self.get_market_conditions()

        # Get AI analysis
        ai_insights = await self.llm_analyzer.analyze_whale_activity(...)

        # Generate recommendation
        if whale_alert.confidence > 90 and whale_accuracy > 0.8:
            return {
                'action': 'SELL',
                'urgency': 'HIGH',
                'position_size': '50%',  # Reduce position by 50%
                'stop_loss': market_conditions.current_price * 0.95,
                'reasoning': ai_insights.summary
            }
        elif whale_alert.confidence > 70:
            return {
                'action': 'WATCH',
                'urgency': 'MEDIUM',
                'reasoning': 'Monitor for additional confirmation'
            }
        else:
            return {
                'action': 'HOLD',
                'urgency': 'LOW'
            }
```

### Deliverables Phase 4

**Code:**
- [ ] LLM integration (~500 lines)
- [ ] News correlator (~400 lines)
- [ ] Trading advisor (~600 lines)
- [ ] 40+ AI tests

**Features:**
- [ ] Natural language insights
- [ ] News/sentiment correlation
- [ ] Trading recommendations
- [ ] Risk scoring

**Documentation:**
- [ ] AI features guide
- [ ] Trading advisor documentation
- [ ] API reference

---

## Infrastructure & DevOps Improvements

### Ongoing (All Phases)

#### Docker & Deployment
**Priority:** HIGH for production

**Tasks:**
- [ ] Dockerfile for application
- [ ] Docker Compose (app + PostgreSQL + Redis)
- [ ] Production deployment guide
- [ ] Environment-specific configs

**Docker Compose Example:**
```yaml
version: '3.8'

services:
  whale_tracker:
    build: .
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://user:pass@db:5432/whale_tracker
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=whale_tracker
      - POSTGRES_PASSWORD=secure_password
      - POSTGRES_DB=whale_tracker
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

#### CI/CD Pipeline
**Priority:** MEDIUM

**Tasks:**
- [ ] GitHub Actions workflow
- [ ] Automated testing on push
- [ ] Docker image building
- [ ] Deployment automation

**GitHub Actions Example:**
```yaml
name: CI/CD

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ -v --cov

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v2
      - name: Build Docker image
        run: docker build -t whale_tracker:latest .
      - name: Push to registry
        run: docker push whale_tracker:latest
```

#### Monitoring & Alerting
**Priority:** MEDIUM (Phase 2+)

**Tasks:**
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] Error tracking (Sentry)
- [ ] Uptime monitoring

**Metrics to track:**
```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

whale_checks_total = Counter('whale_checks_total', 'Total whale checks')
alerts_sent_total = Counter('alerts_sent_total', 'Total alerts sent')
one_hop_detected_total = Counter('one_hop_detected_total', 'One-hop detections')
detection_confidence = Histogram('detection_confidence', 'Confidence distribution')
active_whales = Gauge('active_whales_count', 'Number of active whales monitored')
```

---

## Success Metrics

### Phase 1 (MVP)
- ✅ All components implemented
- ✅ 139 tests passing
- ⏳ First successful run
- ⏳ 24h continuous operation without errors

### Phase 2 (Advanced One-Hop)
- [ ] >90% one-hop detection accuracy
- [ ] <5% false positive rate
- [ ] <5 min average detection time
- [ ] Database queries <100ms
- [ ] All 10 signals implemented

### Phase 3 (ML/Patterns)
- [ ] >85% whale classification accuracy
- [ ] >80% entity resolution precision
- [ ] >70% dump prediction accuracy
- [ ] 3+ months historical data collected

### Phase 4 (AI)
- [ ] LLM insights generated for all alerts
- [ ] News correlation working
- [ ] Trading recommendations generated
- [ ] User feedback >4/5 stars

---

## Resource Requirements

### Phase 1 (MVP)
**APIs:**
- Infura (free tier: 100K requests/day) ✅
- Telegram Bot API (free) ✅

**Infrastructure:**
- Single server/VPS
- 2GB RAM
- 20GB storage

**Cost:** ~$0/month (using free tiers)

### Phase 2
**APIs:**
- Etherscan API (free: 5 calls/sec)
- CoinGecko API (free: 50 calls/min)
- Consider paid tiers if needed

**Infrastructure:**
- VPS with 4GB RAM
- PostgreSQL database (50GB)
- Redis cache (2GB)

**Cost:** ~$20-40/month

### Phase 3
**APIs:**
- Same as Phase 2
- Potentially ML API credits

**Infrastructure:**
- 8GB RAM for ML training
- 100GB storage for historical data

**Cost:** ~$50-80/month

### Phase 4
**APIs:**
- OpenAI/Anthropic API (~$100-200/month)
- News APIs (~$50/month)
- Social sentiment APIs (~$50/month)

**Infrastructure:**
- Same as Phase 3

**Cost:** ~$250-400/month

---

## Timeline Summary

```
Now         Week 1-2      Week 3-4      Month 2-3     Month 3-4
 │            │             │              │             │
 │  Phase 1   │  Phase 2    │  Phase 2     │  Phase 3    │  Phase 4
 │    MVP     │  Database   │  Signals     │  ML/Patterns│  AI
 │            │  + Top      │  + Price     │  + Predict  │  + Insights
 │            │  Signals    │  Tracking    │             │
 ▼            ▼             ▼              ▼             ▼
```

**Total estimated time:** 3-4 months to Phase 4
**MVP to production-ready Phase 2:** 2-3 weeks

---

## Next Actions (Immediate)

### This Week
1. ✅ Documentation complete
2. ⏳ First MVP run
3. ⏳ Bug fixes from first run
4. ⏳ 48h stability test

### Next Week (Phase 2 Start)
1. [ ] PostgreSQL setup
2. [ ] Database schema implementation
3. [ ] Signal #3 (Nonce tracking) implementation
4. [ ] Signal #2 (Gas correlation) implementation

### Week 3-4
1. [ ] Remaining signals (4, 5, 7, 8)
2. [ ] Price tracking integration
3. [ ] Integration testing
4. [ ] Performance optimization

---

**Версия документа:** 1.0
**Дата создания:** 2025-11-21
**Последнее обновление:** 2025-11-21
**Статус:** Living document - будет обновляться по мере прогресса
