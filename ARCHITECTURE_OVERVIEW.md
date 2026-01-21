# 🏗️ ARCHITECTURE OVERVIEW - Phase 2 LST Correction

Visual guide to system architecture and data flow.

---

## 📊 HIGH-LEVEL ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER REQUEST                              │
│                 "Calculate whale accumulation"                   │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                 run_collective_analysis.py                       │
│                    (Main Entry Point)                            │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│          AccumulationScoreCalculator                             │
│         calculate_accumulation_score()                           │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Step 1: Get current whales (WhaleListProvider)           │  │
│  │ Step 2: Get historical whales (SnapshotRepository)       │  │
│  │ Step 3: UNION addresses (survival bias fix)              │  │
│  │ Step 4: Get current balances (MulticallClient)           │  │
│  │ Step 4.5: Fetch LST balances (WETH + stETH)            NEW │
│  │ Step 4.6: Detect LST migrations                         NEW │
│  │ Step 4.7: Fetch historical price (48h)                 NEW │
│  │ Step 5: Get historical balances (SnapshotRepository)     │  │
│  │ Step 6: Calculate metrics (_calculate_metrics)           │  │
│  │   ├─ LST Aggregation                                   NEW │
│  │   ├─ MAD Anomaly Detection                             NEW │
│  │   └─ Gini Coefficient                                  NEW │
│  │ Step 7: Assign smart tags (_assign_tags)              NEW │
│  │ Step 8: Store in database (AccumulationRepository)       │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                   ENRICHED METRICS + TAGS                        │
│  - Native ETH score                                              │
│  - LST-adjusted score                                         NEW│
│  - Smart tags [Organic Accumulation] [Bullish Divergence]    NEW│
│  - Statistical quality (Gini, MAD)                           NEW│
│  - Price context (48h change)                                NEW│
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 DATA FLOW DETAIL

```
┌─────────────────┐
│  External APIs  │
└────────┬────────┘
         │
         ├─────────────────────────────────────────────────────┐
         │                                                       │
         ↓                                                       ↓
┌──────────────────┐                                  ┌──────────────────┐
│  Ethereum RPC    │                                  │   CoinGecko API  │ NEW
│  (MulticallClient)│                                  │ (PriceProvider)  │
└────────┬─────────┘                                  └────────┬─────────┘
         │                                                       │
         ├─ Current ETH balances                               ├─ stETH rate
         ├─ WETH balances                                   NEW├─ Current price
         └─ stETH balances                                  NEW└─ Historical price
         │                                                       │
         ↓                                                       ↓
┌─────────────────────────────────────────────────────────────────────┐
│              AccumulationScoreCalculator                             │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  _calculate_metrics()                                       │    │
│  │                                                              │    │
│  │  1. LST Aggregation                                      NEW│    │
│  │     wealth = ETH + WETH + (stETH × rate)                   │    │
│  │                                                              │    │
│  │  2. Standard Metrics (Native ETH)                           │    │
│  │     score = (current - historical) / historical × 100       │    │
│  │                                                              │    │
│  │  3. LST-Adjusted Metrics                                 NEW│    │
│  │     lst_score = (wealth_now - wealth_24h) / wealth_24h × 100│   │
│  │                                                              │    │
│  │  4. MAD Anomaly Detection                                NEW│    │
│  │     median_change = median(changes)                         │    │
│  │     MAD = median(|changes - median_change|)                 │    │
│  │     threshold = 3 × MAD                                     │    │
│  │     if |change - median| > threshold → anomaly              │    │
│  │                                                              │    │
│  │  5. Gini Coefficient                                     NEW│    │
│  │     sorted_balances = sort(balances)                        │    │
│  │     gini = |2×cumsum/(n×total) - (n+1)/n|                  │    │
│  │                                                              │    │
│  │  6. Count Accumulators/Distributors                         │    │
│  │     accumulators = whales with increased balance            │    │
│  │     distributors = whales with decreased balance            │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  _detect_lst_migration()                                 NEW│    │
│  │                                                              │    │
│  │  for each whale:                                             │    │
│  │    eth_delta = ETH_now - ETH_before                         │    │
│  │    lst_delta = WETH + (stETH × rate)                        │    │
│  │    total_delta = eth_delta + lst_delta                      │    │
│  │                                                              │    │
│  │    if (eth_delta < 0 AND                                    │    │
│  │        lst_delta > 0 AND                                    │    │
│  │        |total_delta| < 0.01):                               │    │
│  │      migration_count += 1                                   │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  _assign_tags()                                          NEW│    │
│  │                                                              │    │
│  │  If accumulators > 25% whale_count:                         │    │
│  │    → [Organic Accumulation]                                 │    │
│  │                                                              │    │
│  │  If gini > 0.85:                                            │    │
│  │    → [Concentrated Signal]                                  │    │
│  │                                                              │    │
│  │  If price↓2%+ AND score↑0.2%+:                             │    │
│  │    → [Bullish Divergence]                                   │    │
│  │                                                              │    │
│  │  If lst_migration_count > 0:                                │    │
│  │    → [LST Migration]                                        │    │
│  │                                                              │    │
│  │  If score > 0.5% AND !anomaly:                              │    │
│  │    → [High Conviction]                                      │    │
│  │                                                              │    │
│  │  If is_anomaly:                                             │    │
│  │    → [Anomaly Alert]                                        │    │
│  └────────────────────────────────────────────────────────────┘    │
└───────────────────────────┬───────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    AccumulationRepository                            │
│                      (Database Storage)                              │
└───────────────────────────┬───────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────────┐
│                  PostgreSQL Database                                 │
│                                                                       │
│  accumulation_metrics table:                                         │
│  ├─ Native ETH fields                                                │
│  ├─ LST fields (WETH, stETH, rate)                               NEW│
│  ├─ Statistical fields (Gini, MAD, anomaly)                      NEW│
│  ├─ Tags array                                                   NEW│
│  └─ Price context (48h change)                                   NEW│
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🧩 COMPONENT INTERACTION

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ WhaleListProvider│────▶│  MulticallClient │────▶│  Ethereum RPC    │
└──────────────────┘     └──────────────────┘     └──────────────────┘
         │                         │
         │ current whales          │ current balances (ETH + LST)
         ↓                         ↓
┌─────────────────────────────────────────────────────────────────────┐
│                                                                       │
│               AccumulationScoreCalculator                             │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
         ↑                         ↑                        ↑
         │                         │                        │
         │ historical whales       │ stETH rate             │ price history
         │                         │ current price          │
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│ SnapshotRepository│     │  CoinGeckoProvider│     │  CoinGecko API   │
└──────────────────┘     └──────────────────┘     └──────────────────┘
         │                                                    NEW
         │ historical balances
         ↓
┌──────────────────┐
│  PostgreSQL DB   │
└──────────────────┘
```

---

## 📦 MODULE DEPENDENCIES

```
run_collective_analysis.py
    ↓
    ├── AccumulationScoreCalculator
    │   ├── WhaleListProvider
    │   │   └── MulticallClient
    │   ├── SnapshotRepository
    │   ├── MulticallClient
    │   ├── CoinGeckoProvider                                      NEW
    │   └── AccumulationRepository
    │
    ├── DatabaseManager
    └── Web3Manager
```

---

## 🔢 DATA TRANSFORMATION PIPELINE

```
Step 1: RAW DATA
────────────────
Whale addresses: ["0x123...", "0x456...", ...]
Current balances: {"0x123...": 1000000000000000000, ...}  # wei
Historical balances: {"0x123...": 900000000000000000, ...}

Step 2: LST ENRICHMENT                                            NEW
─────────────────────
WETH balances: {"0x123...": 50000000000000000, ...}
stETH balances: {"0x123...": 100000000000000000, ...}
stETH rate: 0.9987

Step 3: AGGREGATION                                               NEW
──────────────────
Aggregated current: {"0x123...": 1150000000000000000, ...}
  = ETH + WETH + (stETH × rate)

Step 4: METRICS CALCULATION
──────────────────────────
Native score: +2.5%
LST-adjusted score: +1.8%                                         NEW

Step 5: STATISTICAL ANALYSIS                                      NEW
───────────────────────────
Changes per whale: [+1.2%, +1.5%, +50%, +0.8%, ...]
Median: +1.2%
MAD: 0.3%
Threshold: 0.9% (3×MAD)
Anomalies: ["0x789..." at +50%]
Gini: 0.72

Step 6: TAGGING                                                   NEW
─────────────
Conditions met:
- accumulators_count (8/20) > 25% → [Organic Accumulation]
- price (-2.3%) < -2% AND score (+1.8%) > 0.2% → [Bullish Divergence]

Step 7: OUTPUT
─────────────
{
  "accumulation_score": 2.5,
  "lst_adjusted_score": 1.8,
  "concentration_gini": 0.72,
  "is_anomaly": true,
  "top_anomaly_driver": "0x789...",
  "tags": ["Organic Accumulation", "Bullish Divergence", "Anomaly Alert"],
  "price_change_48h_pct": -2.3,
  ...
}
```

---

## 🎯 KEY ALGORITHMS

### 1. LST Aggregation
```python
for address in addresses:
    eth = native_balance[address]
    weth = weth_balance[address]
    steth = steth_balance[address] × steth_rate
    
    total_wealth[address] = eth + weth + steth
```

### 2. MAD Anomaly Detection
```python
changes = [calculate_change(addr) for addr in addresses]
median = median(changes)
deviations = [abs(c - median) for c in changes]
mad = median(deviations)
threshold = 3 × mad

anomalies = [addr for addr, change in changes 
             if abs(change - median) > threshold]
```

### 3. Gini Coefficient
```python
sorted_balances = sorted(balances)
n = len(sorted_balances)
cumsum = sum((i+1) × balance for i, balance in enumerate(sorted_balances))
total = sum(sorted_balances)

gini = abs(2×cumsum / (n×total) - (n+1)/n)
```

### 4. Smart Tags
```python
tags = []
if accumulators_count > whale_count × 0.25:
    tags.append("Organic Accumulation")
if gini > 0.85:
    tags.append("Concentrated Signal")
if price_change < -2% and score > 0.2%:
    tags.append("Bullish Divergence")
# ... more conditions
```

---

## 📈 BEFORE vs AFTER

### BEFORE Phase 2:
```
Input: Individual whale transactions
     ↓
Process: Basic balance comparison
     ↓
Output: "Whale moved $2M" (NOISE)
```

### AFTER Phase 2:
```
Input: Collective whale behavior
     ↓
Process: LST aggregation → MAD filtering → Gini analysis → Smart tagging
     ↓
Output: "30% whales accumulating +1.8% LST-adjusted
        [Organic Accumulation] [Bullish Divergence]" (SIGNAL)
```

---

**KEY INSIGHT:**  
Phase 2 transforms the system from a **transaction monitor** into a **market intelligence platform** by adding layers of statistical analysis, context enrichment, and intelligent tagging.
