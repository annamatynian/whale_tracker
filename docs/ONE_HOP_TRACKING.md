# One-Hop Tracking - The Real Edge

## Оглавление
- [Почему One-Hop это наш Edge](#почему-one-hop-это-наш-edge)
- [10 Advanced Signals](#10-advanced-signals)
- [Implementation Strategy](#implementation-strategy)
- [Database Schema](#database-schema)
- [Performance Optimization](#performance-optimization)
- [Examples и Case Studies](#examples-и-case-studies)

---

## Почему One-Hop это наш Edge

### Проблема

**Существующие whale trackers (включая Arkham):**
```
Показывают:
"Vitalik sent 1000 ETH to 0xabc123..."

НЕ показывают автоматически:
"...and 0xabc123 sent 1000 ETH to Binance 15 minutes later"
```

### Статистика

- **~80% опытных китов** используют промежуточные адреса
- **~90% крупных дампов** (>$1M) идут через intermediaries
- **Типичное время** между whale → intermediate → exchange: **5-30 минут**

### Наше решение

**Автоматическое обнаружение цепочек:**
```
Whale Address
    ↓ (1000 ETH)
Intermediate Address (0xabc123)
    ↓ (1000 ETH, 15 min later)
Exchange Address (Binance)

=> ALERT: High probability dump incoming!
```

**Value proposition:**
- Предупреждение о дампе **ДО того как он произойдет**
- Время на реакцию: 5-30 минут
- Возможность закрыть позицию или установить stop-loss

---

## 10 Advanced Signals

### Signal #1: Time Correlation ⏰

**Статус:** ✅ Базовая версия в MVP, 📋 Advanced версия в Phase 2

**Идея:**
Если intermediate address получил от кита и отправил на exchange **в узком временном окне**, это сильный сигнал.

**Оптимальное окно:**
- **5-15 минут:** Очень высокая вероятность (90%+)
- **15-30 минут:** Высокая вероятность (70-90%)
- **30-60 минут:** Средняя вероятность (40-70%)
- **1+ час:** Низкая вероятность (<40%)

**MVP Implementation (простая версия):**
```python
def check_time_correlation(whale_tx, intermediate_txs):
    """Simple time window check"""
    TIME_WINDOW = 30 * 60  # 30 minutes

    for tx in intermediate_txs:
        time_diff = tx.timestamp - whale_tx.timestamp
        if 0 < time_diff < TIME_WINDOW:
            return True
    return False
```

**Advanced Implementation (Phase 2):**
```python
def advanced_time_correlation(whale_tx, intermediate_txs):
    """Adaptive time window with confidence scoring"""

    confidence = 0

    for tx in intermediate_txs:
        time_diff = tx.timestamp - whale_tx.timestamp

        # Adaptive scoring based on time
        if time_diff < 5 * 60:  # < 5 min
            confidence += 90
        elif time_diff < 15 * 60:  # 5-15 min
            confidence += 70
        elif time_diff < 30 * 60:  # 15-30 min
            confidence += 50
        elif time_diff < 60 * 60:  # 30-60 min
            confidence += 30

        # Time-of-day patterns
        hour = tx.timestamp.hour
        if 9 <= hour <= 16:  # Business hours (US Eastern)
            confidence += 10  # Exchanges more active

        # Weekend/weekday
        if tx.timestamp.weekday() < 5:  # Weekday
            confidence += 5

    return min(confidence, 100)
```

**Confidence Impact:** +50 to +90

---

### Signal #2: Gas Price Correlation ⛽

**Статус:** 📋 Phase 2

**Идея:**
Если whale transaction и intermediate → exchange transaction имеют **одинаковую gas price**, вероятно это **одна и та же entity** (тот же wallet software, та же стратегия).

**Почему это работает:**
- Gas price меняется каждую секунду
- Probability of exact match by chance: ~0.1%
- Если exact match → **99%+ confidence** что это тот же человек/бот

**Implementation:**
```python
def check_gas_price_correlation(whale_tx, intermediate_tx):
    """
    Check if gas prices match within small threshold
    """
    # Exact match
    if whale_tx.gas_price == intermediate_tx.gas_price:
        return {
            'match': True,
            'confidence': 95,
            'type': 'exact'
        }

    # Close match (within 0.1 Gwei)
    THRESHOLD = 0.1 * 10**9  # 0.1 Gwei
    diff = abs(whale_tx.gas_price - intermediate_tx.gas_price)

    if diff < THRESHOLD:
        return {
            'match': True,
            'confidence': 80,
            'type': 'close'
        }

    # Check if both used same strategy (e.g., baseFee + 2 Gwei)
    if both_used_same_priority_fee(whale_tx, intermediate_tx):
        return {
            'match': True,
            'confidence': 70,
            'type': 'strategy'
        }

    return {'match': False, 'confidence': 0}

def both_used_same_priority_fee(tx1, tx2):
    """Check if both transactions used same priority fee strategy"""
    # EIP-1559: maxFeePerGas and maxPriorityFeePerGas
    if hasattr(tx1, 'maxPriorityFeePerGas'):
        return tx1.maxPriorityFeePerGas == tx2.maxPriorityFeePerGas
    return False
```

**Confidence Impact:** +70 to +95

**Requirements:**
- Full transaction details (включая gas fields)
- EIP-1559 transaction support

---

### Signal #3: Nonce Tracking 🔢

**Статус:** 📋 Phase 2 (HIGHEST PRIORITY)

**Идея:**
Nonce = transaction counter для каждого адреса. Если intermediate address имеет **sequential nonces**, это STRONGEST SIGNAL.

**Example:**
```
Block 18000000: Whale sends to 0xIntermediate (tx from whale)
                0xIntermediate nonce at this block: 5

Block 18000001: 0xIntermediate sends to Exchange
                0xIntermediate nonce: 6

=> Sequential nonces! GAP = 1 => BINGO!
```

**Почему это strongest signal:**
- Nonce gap = 1 означает: intermediate **СРАЗУ ЖЕ** отправил на exchange
- Никаких других транзакций между ними
- Probability это случайность: ~0.01%

**Implementation:**
```python
async def check_nonce_sequence(web3, whale_tx, intermediate_tx):
    """
    Check if intermediate address had sequential nonces
    STRONGEST SIGNAL for one-hop detection
    """
    intermediate_addr = whale_tx.to_address

    # Get intermediate's nonce at the time of whale tx
    whale_block = whale_tx.block_number
    nonce_at_whale_tx = await web3.eth.get_transaction_count(
        intermediate_addr,
        block_identifier=whale_block
    )

    # Get intermediate's nonce for exchange tx
    exchange_tx_nonce = intermediate_tx.nonce

    # Calculate gap
    nonce_gap = exchange_tx_nonce - nonce_at_whale_tx

    if nonce_gap == 1:
        return {
            'match': True,
            'confidence': 95,
            'gap': 1,
            'signal_strength': 'STRONGEST'
        }
    elif nonce_gap <= 3:
        return {
            'match': True,
            'confidence': 75,
            'gap': nonce_gap,
            'signal_strength': 'STRONG'
        }
    elif nonce_gap <= 10:
        return {
            'match': True,
            'confidence': 40,
            'gap': nonce_gap,
            'signal_strength': 'WEAK'
        }

    return {'match': False, 'confidence': 0}
```

**Confidence Impact:** +40 to +95 (HIGHEST)

**Requirements:**
- Archival node access (для historical nonce queries)
- OR Etherscan API (get transaction list + nonce)

**API Call Example (Etherscan):**
```python
async def get_nonce_at_block(address, block_number):
    """Get nonce using Etherscan API"""
    url = f"https://api.etherscan.io/api?module=proxy&action=eth_getTransactionCount&address={address}&tag={block_number}&apikey={API_KEY}"

    response = await aiohttp.get(url)
    data = await response.json()
    return int(data['result'], 16)
```

---

### Signal #4: Amount Correlation + Split Detection 💰

**Статус:** 📋 Phase 2

**Идея:**
Проверить совпадение сумм (с учетом fees) и обнаружить splits.

**Scenarios:**

#### 4.1: Exact Amount Match
```
Whale sends:        1000 ETH
Intermediate sends: 999.98 ETH (minus gas)
=> Exact match! Confidence +80
```

**Implementation:**
```python
def check_amount_match(whale_amount, intermediate_amount, gas_used):
    """Check if amounts match (accounting for gas)"""

    expected_amount = whale_amount - (gas_used / 10**18)

    # Exact match (within 0.01 ETH tolerance)
    if abs(intermediate_amount - expected_amount) < 0.01:
        return {'match': True, 'confidence': 80, 'type': 'exact'}

    # Close match (within 1% difference)
    diff_pct = abs(intermediate_amount - expected_amount) / expected_amount
    if diff_pct < 0.01:  # 1%
        return {'match': True, 'confidence': 65, 'type': 'close'}

    return {'match': False, 'confidence': 0}
```

#### 4.2: Split Detection
```
Whale sends:        1000 ETH to 0xIntermediate
Intermediate sends: 500 ETH to Binance
                    500 ETH to Coinbase
=> Split pattern! Confidence +70
```

**Implementation:**
```python
def detect_split_pattern(whale_amount, intermediate_txs):
    """Detect if whale amount was split across multiple exchanges"""

    total_sent = sum(tx.amount for tx in intermediate_txs)

    # Check if sum of splits ≈ whale amount
    if abs(total_sent - whale_amount) / whale_amount < 0.02:  # 2% tolerance
        return {
            'split_detected': True,
            'confidence': 70,
            'num_destinations': len(intermediate_txs),
            'destinations': [tx.to_address for tx in intermediate_txs]
        }

    return {'split_detected': False}
```

#### 4.3: Consolidation Detection (обратный паттерн)
```
Multiple whales send to intermediate:
  Whale1: 500 ETH
  Whale2: 300 ETH
  Whale3: 200 ETH

Intermediate consolidates and sends: 1000 ETH to Exchange
=> OTC deal or coordinated dump
```

**Confidence Impact:** +65 to +80

---

### Signal #5: Intermediate Address Profiling 🔍

**Статус:** 📋 Phase 2

**Идея:**
Анализ характеристик промежуточного адреса для определения его "типа".

**Profiles:**

#### 5.1: Fresh Address
```python
async def is_fresh_address(web3, address):
    """
    Fresh address = created recently (< 24 hours ago)
    Strong signal for one-time intermediate
    """
    # Get first transaction timestamp
    first_tx = await get_first_transaction(address)

    if not first_tx:
        return False

    age_hours = (datetime.now() - first_tx.timestamp).total_seconds() / 3600

    if age_hours < 1:
        return {'fresh': True, 'confidence': 90, 'age_hours': age_hours}
    elif age_hours < 24:
        return {'fresh': True, 'confidence': 70, 'age_hours': age_hours}

    return {'fresh': False, 'confidence': 0}
```

#### 5.2: Empty Address (перед whale tx)
```python
async def was_empty_before(web3, address, whale_tx_block):
    """
    Check if address had 0 balance before whale transaction
    Strong signal for burner address
    """
    balance = await web3.eth.get_balance(
        address,
        block_identifier=whale_tx_block - 1
    )

    if balance == 0:
        return {'was_empty': True, 'confidence': 85}

    return {'was_empty': False, 'confidence': 0}
```

#### 5.3: Single-Use Address
```python
async def is_single_use(address):
    """
    Check if address was used only for this one operation
    Whale -> Intermediate -> Exchange -> Empty
    """
    txs = await get_all_transactions(address)

    if len(txs) == 2:  # Only incoming + outgoing
        # Check if empty now
        current_balance = await web3.eth.get_balance(address)
        if current_balance < 0.01 * 10**18:  # < 0.01 ETH
            return {
                'single_use': True,
                'confidence': 95,
                'pattern': 'burner'
            }

    return {'single_use': False}
```

#### 5.4: Reused Intermediate Detection
```python
async def check_reuse_pattern(address):
    """
    Some whales reuse same intermediate addresses
    Pattern: Multiple whale -> intermediate -> exchange cycles
    """
    txs = await get_all_transactions(address)

    # Group into cycles
    cycles = detect_cycles(txs)

    if len(cycles) > 3:
        return {
            'reused': True,
            'confidence': 75,
            'num_cycles': len(cycles),
            'pattern': 'professional_operation'
        }

    return {'reused': False}
```

**Confidence Impact:** +70 to +95

---

### Signal #6: Network Clustering (Graph Analysis) 🕸️

**Статус:** 📋 Phase 2-3 (требует database)

**Идея:**
Построить граф транзакций и найти кластеры связанных адресов.

**Graph Structure:**
```
Nodes: Addresses
Edges: Transactions (with weight = amount)

Example:
Whale1 ----1000ETH----> 0xABC
Whale1 ----500ETH-----> 0xDEF
0xABC  ----1000ETH----> Binance
0xDEF  ----500ETH-----> Binance
=> Cluster detected: Whale1 -> {0xABC, 0xDEF} -> Binance
```

**Implementation (using NetworkX):**
```python
import networkx as nx

class TransactionGraph:
    def __init__(self):
        self.G = nx.DiGraph()

    def add_transaction(self, from_addr, to_addr, amount, timestamp):
        """Add transaction as edge"""
        self.G.add_edge(
            from_addr,
            to_addr,
            amount=amount,
            timestamp=timestamp
        )

    def find_paths(self, whale_addr, exchange_addrs, max_hops=4):
        """Find all paths from whale to exchanges"""
        paths = []

        for exchange in exchange_addrs:
            # Find all simple paths (no cycles)
            all_paths = nx.all_simple_paths(
                self.G,
                source=whale_addr,
                target=exchange,
                cutoff=max_hops
            )
            paths.extend(list(all_paths))

        return paths

    def compute_path_confidence(self, path):
        """Score path based on multiple signals"""
        confidence = 0

        # Check time correlation along path
        edges = [(path[i], path[i+1]) for i in range(len(path)-1)]
        timestamps = [self.G[u][v]['timestamp'] for u, v in edges]

        # All transactions within 1 hour?
        time_span = max(timestamps) - min(timestamps)
        if time_span < 3600:  # 1 hour
            confidence += 50

        # Check amount preservation
        amounts = [self.G[u][v]['amount'] for u, v in edges]
        if all(abs(amounts[i] - amounts[0])/amounts[0] < 0.05 for i in range(len(amounts))):
            confidence += 30  # Amounts preserved within 5%

        # Shorter path = higher confidence
        confidence += max(0, 20 - (len(path) * 5))

        return min(confidence, 100)

    def detect_communities(self):
        """Find clusters of related addresses"""
        # Convert to undirected for community detection
        G_undirected = self.G.to_undirected()

        # Louvain community detection
        communities = nx.community.louvain_communities(G_undirected)

        return communities
```

**Database Schema для Graph:**
```sql
CREATE TABLE transaction_graph (
    id SERIAL PRIMARY KEY,
    from_address VARCHAR(42) NOT NULL,
    to_address VARCHAR(42) NOT NULL,
    amount DECIMAL(36, 18),
    timestamp TIMESTAMP,
    tx_hash VARCHAR(66) UNIQUE,

    INDEX idx_from (from_address),
    INDEX idx_to (to_address),
    INDEX idx_timestamp (timestamp)
);

-- Query для поиска paths (PostgreSQL WITH RECURSIVE)
WITH RECURSIVE whale_paths AS (
    -- Base case: direct transactions from whale
    SELECT
        from_address,
        to_address,
        amount,
        timestamp,
        tx_hash,
        1 as hop,
        ARRAY[from_address, to_address] as path
    FROM transaction_graph
    WHERE from_address = '0xWHALE_ADDRESS'

    UNION ALL

    -- Recursive case: follow the chain
    SELECT
        tg.from_address,
        tg.to_address,
        tg.amount,
        tg.timestamp,
        tg.tx_hash,
        wp.hop + 1,
        wp.path || tg.to_address
    FROM transaction_graph tg
    JOIN whale_paths wp ON tg.from_address = wp.to_address
    WHERE wp.hop < 4  -- Max 4 hops
        AND tg.timestamp > wp.timestamp
        AND tg.timestamp < wp.timestamp + INTERVAL '2 hours'
)
SELECT * FROM whale_paths
WHERE to_address IN (SELECT address FROM known_exchanges);
```

**Confidence Impact:** +30 to +60 (дополнительный сигнал)

**Requirements:**
- PostgreSQL с recursive query support
- OR Neo4j graph database
- NetworkX для Python-based analysis

---

### Signal #7: Multi-Hop Detection (2-4 hops) 🪜

**Статус:** 📋 Phase 2

**Идея:**
Опытные киты используют несколько промежуточных адресов.

**Patterns:**

#### 2-Hop (Simple)
```
Whale -> Intermediate1 -> Exchange
```
✅ MVP уже детектит

#### 3-Hop (Advanced)
```
Whale -> Intermediate1 -> Intermediate2 -> Exchange
```

#### 4-Hop (Sophisticated Privacy)
```
Whale -> Int1 -> Int2 -> Int3 -> Exchange
```

**Implementation:**
```python
async def detect_multi_hop_chain(whale_tx, max_hops=4, time_window_hours=2):
    """
    Recursively follow transaction chain up to max_hops
    """

    def find_chain(current_addr, depth, visited, chain):
        if depth > max_hops:
            return []

        # Get outgoing transactions from current address
        txs = get_transactions_from(
            current_addr,
            min_timestamp=whale_tx.timestamp,
            max_timestamp=whale_tx.timestamp + timedelta(hours=time_window_hours)
        )

        chains = []
        for tx in txs:
            if tx.to_address in visited:
                continue  # Avoid cycles

            new_chain = chain + [tx]
            new_visited = visited | {tx.to_address}

            # Check if reached exchange
            if is_exchange_address(tx.to_address):
                chains.append(new_chain)
            else:
                # Recurse deeper
                deeper_chains = find_chain(
                    tx.to_address,
                    depth + 1,
                    new_visited,
                    new_chain
                )
                chains.extend(deeper_chains)

        return chains

    # Start from intermediate address
    intermediate = whale_tx.to_address
    all_chains = find_chain(
        current_addr=intermediate,
        depth=1,
        visited={whale_tx.from_address, intermediate},
        chain=[]
    )

    return all_chains

def score_chain_confidence(chain):
    """Score multi-hop chain"""

    base_confidence = 50

    # Time coherence
    timestamps = [tx.timestamp for tx in chain]
    time_span = max(timestamps) - min(timestamps)
    if time_span < 1800:  # 30 min
        base_confidence += 30
    elif time_span < 3600:  # 1 hour
        base_confidence += 20

    # Amount preservation
    amounts = [tx.amount for tx in chain]
    if all(abs(amounts[i] - amounts[0])/amounts[0] < 0.1 for i in range(len(amounts))):
        base_confidence += 20

    # Penalty for longer chains (less certain)
    penalty = len(chain) * 5

    return max(0, min(100, base_confidence - penalty))
```

**Confidence Impact:** +40 to +70 (decreases with chain length)

---

### Signal #8: DEX Interaction Detection 🔄

**Статус:** 📋 Phase 2

**Идея:**
Киты часто конвертируют ETH → Stablecoin через DEX перед отправкой на exchange.

**Pattern:**
```
Whale sends 1000 ETH to Intermediate
    ↓
Intermediate swaps ETH -> USDT on Uniswap
    ↓
Intermediate sends USDT to Exchange

=> VERY STRONG SIGNAL of intended sell
```

**Почему это важно:**
- Swap to stablecoin = clear intent to cash out
- Часто используется для избежания price impact на CEX
- Confidence: 90%+ это dump

**Implementation:**
```python
# Known DEX router addresses
DEX_ROUTERS = {
    '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D': 'Uniswap V2',
    '0xE592427A0AEce92De3Edee1F18E0157C05861564': 'Uniswap V3',
    '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F': 'SushiSwap',
    '0x1111111254fb6c44bACaAF66b763F4944826e0C4': '1inch',
}

STABLECOINS = {
    '0xdAC17F958D2ee523a2206206994597C13D831ec7': 'USDT',
    '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48': 'USDC',
    '0x6B175474E89094C44Da98b954EedeAC495271d0F': 'DAI',
}

async def detect_dex_interaction(intermediate_addr, whale_tx):
    """
    Check if intermediate address interacted with DEX
    """

    txs = await get_transactions_from(
        intermediate_addr,
        min_timestamp=whale_tx.timestamp,
        max_timestamp=whale_tx.timestamp + timedelta(hours=1)
    )

    dex_interactions = []

    for tx in txs:
        # Check if transaction is to DEX router
        if tx.to_address in DEX_ROUTERS:
            # Decode swap parameters
            swap_info = decode_swap_transaction(tx)

            if swap_info:
                dex_interactions.append({
                    'dex': DEX_ROUTERS[tx.to_address],
                    'from_token': swap_info['tokenIn'],
                    'to_token': swap_info['tokenOut'],
                    'amount_in': swap_info['amountIn'],
                    'amount_out': swap_info['amountOut'],
                    'timestamp': tx.timestamp
                })

    # Check for ETH -> Stablecoin swaps
    for interaction in dex_interactions:
        if (interaction['from_token'] == 'ETH' and
            interaction['to_token'] in STABLECOINS.values()):

            # Check if stablecoin was sent to exchange
            stablecoin_addr = get_token_address(interaction['to_token'])
            exchange_transfer = check_token_transfer_to_exchange(
                intermediate_addr,
                stablecoin_addr,
                after_timestamp=interaction['timestamp']
            )

            if exchange_transfer:
                return {
                    'dex_detected': True,
                    'confidence': 90,
                    'pattern': 'ETH -> Stablecoin -> Exchange',
                    'details': {
                        'dex': interaction['dex'],
                        'stablecoin': interaction['to_token'],
                        'exchange': exchange_transfer['exchange']
                    }
                }

    return {'dex_detected': False}

def decode_swap_transaction(tx):
    """Decode Uniswap/DEX swap transaction"""
    # Parse transaction input data
    # This requires ABI decoding

    # Example for Uniswap V2 swapExactETHForTokens
    if tx.input.startswith('0x7ff36ab5'):  # Function selector
        # Decode parameters...
        return {
            'tokenIn': 'ETH',
            'tokenOut': '...',  # Decode from input
            'amountIn': tx.value,
            'amountOut': '...'  # Decode from logs
        }

    return None
```

**Confidence Impact:** +80 to +90 (VERY STRONG)

---

### Signal #9: Cross-Chain Bridge Detection 🌉

**Статус:** 📋 Phase 3

**Идея:**
Киты используют bridges для перевода активов между блокчейнами перед дампом.

**Pattern:**
```
Ethereum: Whale sends ETH to Bridge Contract
    ↓
Base/Arbitrum: Whale receives equivalent amount
    ↓
Base/Arbitrum: Whale sends to Exchange

=> Cross-chain dump
```

**Known Bridge Contracts:**
```python
BRIDGE_CONTRACTS = {
    # Ethereum Mainnet
    '0x49048044D57e1C92A77f79988d21Fa8fAF74E97e': 'Optimism Bridge',
    '0x8484Ef722627bf18ca5Ae6BcF031c23E6e922B30': 'Arbitrum Bridge',
    '0x3154Cf16ccdb4C6d922629664174b904d80F2C35': 'Base Bridge',
    '0x401F6c983eA34274ec46f84D70b31C151321188b': 'Polygon Bridge',
}
```

**Implementation:**
```python
async def detect_cross_chain_bridge(whale_addr, whale_tx):
    """
    Detect if whale used bridge, then track on destination chain
    """

    # Check if transaction is to known bridge
    if whale_tx.to_address not in BRIDGE_CONTRACTS:
        return {'bridge_detected': False}

    bridge_name = BRIDGE_CONTRACTS[whale_tx.to_address]

    # Determine destination chain
    destination_chain = get_destination_chain(whale_tx.to_address)

    # Wait for bridge confirmation (usually 10-30 min)
    await asyncio.sleep(600)  # 10 min

    # Check destination chain for whale's address activity
    destination_web3 = get_web3_for_chain(destination_chain)

    destination_txs = await get_recent_transactions(
        destination_web3,
        whale_addr,
        since=whale_tx.timestamp + timedelta(minutes=10),
        until=whale_tx.timestamp + timedelta(hours=2)
    )

    # Check if whale sent to exchange on destination chain
    for tx in destination_txs:
        if is_exchange_address(tx.to_address):
            return {
                'bridge_detected': True,
                'confidence': 85,
                'pattern': 'cross_chain_dump',
                'details': {
                    'bridge': bridge_name,
                    'source_chain': 'ethereum',
                    'dest_chain': destination_chain,
                    'dest_exchange': get_exchange_name(tx.to_address)
                }
            }

    return {'bridge_detected': False}
```

**Confidence Impact:** +70 to +85

**Requirements:**
- Multi-chain RPC providers (Ethereum, Base, Arbitrum, etc.)
- Bridge event monitoring
- Cross-chain address tracking

---

### Signal #10: Privacy Protocol Detection 🔒

**Статус:** 📋 Phase 3

**Идея:**
Обнаружение использования privacy mixers (Tornado Cash, Railgun).

**Pattern:**
```
Whale -> Tornado Cash (deposit)
    ↓ (mixing period: hours/days)
Tornado Cash -> New Address (withdrawal)
    ↓
New Address -> Exchange

=> Sophisticated privacy, but detectable
```

**Known Privacy Protocols:**
```python
PRIVACY_PROTOCOLS = {
    # Tornado Cash
    '0x12D66f87A04A9E220743712cE6d9bB1B5616B8Fc': 'Tornado Cash 0.1 ETH',
    '0x47CE0C6eD5B0Ce3d3A51fdb1C52DC66a7c3c2936': 'Tornado Cash 1 ETH',
    '0x910Cbd523D972eb0a6f4cAe4618aD62622b39DbF': 'Tornado Cash 10 ETH',
    '0xA160cdAB225685dA1d56aa342Ad8841c3b53f291': 'Tornado Cash 100 ETH',

    # Railgun
    '0xFA7093CDD9EE6932B4eb2c9e1cde7CE00B1FA4b9': 'Railgun',
}
```

**Detection Strategy:**
```python
async def detect_privacy_mixer_usage(whale_addr):
    """
    Monitor whale's deposits to privacy protocols
    Then try to correlate withdrawals
    """

    # Check for deposits
    deposits = await get_privacy_deposits(whale_addr)

    if not deposits:
        return {'privacy_detected': False}

    # For each deposit, monitor withdrawals
    for deposit in deposits:
        # Get all withdrawals from same pool within 7 days
        withdrawals = await get_privacy_withdrawals(
            pool=deposit.pool,
            min_timestamp=deposit.timestamp,
            max_timestamp=deposit.timestamp + timedelta(days=7)
        )

        # Statistical correlation
        # (This is HARD - Tornado is designed to prevent this)
        # But we can use timing, amount patterns, etc.

        for withdrawal in withdrawals:
            score = calculate_correlation_score(deposit, withdrawal)

            if score > 0.7:  # High correlation
                # Check if withdrawal address sent to exchange
                withdrawal_addr_txs = await get_transactions_from(
                    withdrawal.to_address,
                    since=withdrawal.timestamp
                )

                for tx in withdrawal_addr_txs:
                    if is_exchange_address(tx.to_address):
                        return {
                            'privacy_detected': True,
                            'confidence': 60,  # Lower due to uncertainty
                            'pattern': 'privacy_mixer_to_exchange',
                            'details': {
                                'mixer': PRIVACY_PROTOCOLS[deposit.pool],
                                'suspected_withdrawal_addr': withdrawal.to_address,
                                'correlation_score': score
                            }
                        }

    return {'privacy_detected': False}

def calculate_correlation_score(deposit, withdrawal):
    """
    Heuristic scoring for deposit-withdrawal correlation
    NOTE: This is probabilistic, not definitive
    """
    score = 0.0

    # Timing pattern (e.g., withdrawal exactly 24h after deposit)
    time_diff = (withdrawal.timestamp - deposit.timestamp).total_seconds()
    if time_diff % 86400 < 3600:  # Within 1 hour of 24h increment
        score += 0.3

    # Amount pattern (same pool = same amount)
    score += 0.2

    # Gas price similarity
    if abs(deposit.gas_price - withdrawal.gas_price) < 1e9:  # 1 Gwei
        score += 0.2

    # Other heuristics...

    return score
```

**Confidence Impact:** +40 to +60 (uncertain due to mixer design)

**Challenges:**
- Tornado Cash **designed to prevent correlation**
- Can only use statistical heuristics
- Lower confidence than other signals
- But still valuable to flag privacy usage

---

## Implementation Strategy

### Phase 1: MVP (COMPLETE ✅)
**Signals implemented:**
- ✅ Signal #1: Basic time correlation
- ✅ Signal #4: Basic amount matching
- ✅ Exchange destination detection

**Confidence:** 50-70%

### Phase 2: Advanced One-Hop (NEXT)
**Priority order:**

1. **Signal #3: Nonce Tracking** (HIGHEST PRIORITY)
   - Strongest signal
   - Relatively easy to implement
   - Requires Etherscan API or archival node
   - Expected confidence: +95

2. **Signal #2: Gas Price Correlation**
   - Strong signal
   - Easy to implement (data already in transaction)
   - Expected confidence: +80

3. **Signal #5: Intermediate Address Profiling**
   - Multiple sub-signals
   - Easy to implement
   - Expected confidence: +75

4. **Signal #4: Advanced Amount Correlation + Splits**
   - Medium complexity
   - Expected confidence: +70

5. **Signal #8: DEX Interaction**
   - Requires ABI decoding
   - Very strong signal when detected
   - Expected confidence: +90

6. **Signal #7: Multi-Hop (2-4 hops)**
   - Requires recursive search
   - Medium complexity
   - Expected confidence: +60

### Phase 3: Graph Analysis
**Signals:**
- Signal #6: Network Clustering
- Signal #9: Cross-Chain Bridges
- Signal #10: Privacy Protocols

**Requires:**
- Graph database (Neo4j or PostgreSQL + recursive queries)
- Multi-chain support
- Advanced correlation algorithms

---

## Database Schema

### Core Tables

```sql
-- Whales being monitored
CREATE TABLE whales (
    address VARCHAR(42) PRIMARY KEY,
    label VARCHAR(255),
    added_at TIMESTAMP DEFAULT NOW(),
    active BOOLEAN DEFAULT TRUE
);

-- All transactions (whale + intermediate + exchange)
CREATE TABLE transactions (
    tx_hash VARCHAR(66) PRIMARY KEY,
    block_number BIGINT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    from_address VARCHAR(42) NOT NULL,
    to_address VARCHAR(42),
    value DECIMAL(36, 18),
    gas_price BIGINT,
    gas_used BIGINT,
    nonce BIGINT,
    input_data TEXT,

    INDEX idx_from (from_address, timestamp),
    INDEX idx_to (to_address, timestamp),
    INDEX idx_block (block_number),
    INDEX idx_timestamp (timestamp)
);

-- Detected one-hop chains
CREATE TABLE one_hop_detections (
    id SERIAL PRIMARY KEY,
    whale_address VARCHAR(42) NOT NULL,
    whale_tx_hash VARCHAR(66) NOT NULL,
    intermediate_address VARCHAR(42) NOT NULL,
    exchange_tx_hash VARCHAR(66),
    exchange_address VARCHAR(42),

    -- Timing
    whale_tx_timestamp TIMESTAMP,
    exchange_tx_timestamp TIMESTAMP,
    time_diff_seconds INT,

    -- Amounts
    whale_amount DECIMAL(36, 18),
    exchange_amount DECIMAL(36, 18),

    -- Signal scores
    time_correlation_score INT,
    gas_correlation_score INT,
    nonce_correlation_score INT,
    amount_correlation_score INT,
    address_profile_score INT,
    dex_interaction_score INT,
    total_confidence INT,

    -- Status
    detected_at TIMESTAMP DEFAULT NOW(),
    alert_sent BOOLEAN DEFAULT FALSE,

    FOREIGN KEY (whale_tx_hash) REFERENCES transactions(tx_hash),
    FOREIGN KEY (exchange_tx_hash) REFERENCES transactions(tx_hash),
    INDEX idx_whale (whale_address, detected_at),
    INDEX idx_confidence (total_confidence DESC)
);

-- Multi-hop chains (2-4 hops)
CREATE TABLE multi_hop_chains (
    id SERIAL PRIMARY KEY,
    whale_address VARCHAR(42) NOT NULL,
    chain_path JSONB NOT NULL,  -- Array of addresses
    tx_hashes JSONB NOT NULL,   -- Array of transaction hashes
    hop_count INT,
    total_confidence INT,
    detected_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_whale (whale_address),
    INDEX idx_hops (hop_count),
    INDEX idx_confidence (total_confidence DESC)
);

-- DEX interactions
CREATE TABLE dex_swaps (
    id SERIAL PRIMARY KEY,
    tx_hash VARCHAR(66) UNIQUE NOT NULL,
    from_address VARCHAR(42) NOT NULL,
    dex_router VARCHAR(42) NOT NULL,
    dex_name VARCHAR(50),
    token_in VARCHAR(42),
    token_out VARCHAR(42),
    amount_in DECIMAL(36, 18),
    amount_out DECIMAL(36, 18),
    timestamp TIMESTAMP,

    INDEX idx_from (from_address, timestamp),
    INDEX idx_dex (dex_router),
    INDEX idx_tokens (token_in, token_out)
);

-- Known addresses (exchanges, bridges, etc.)
CREATE TABLE known_addresses (
    address VARCHAR(42) PRIMARY KEY,
    name VARCHAR(255),
    category VARCHAR(50),  -- 'exchange', 'bridge', 'dex', 'mixer'
    tags JSONB,
    verified BOOLEAN DEFAULT FALSE,
    added_at TIMESTAMP DEFAULT NOW()
);

-- Address relationships (for graph analysis)
CREATE TABLE address_relationships (
    id SERIAL PRIMARY KEY,
    address1 VARCHAR(42) NOT NULL,
    address2 VARCHAR(42) NOT NULL,
    relationship_type VARCHAR(50),  -- 'whale_to_intermediate', 'intermediate_to_exchange', etc.
    strength DECIMAL(5, 2),  -- 0.0 to 1.0
    last_interaction TIMESTAMP,
    interaction_count INT DEFAULT 1,

    UNIQUE(address1, address2),
    INDEX idx_addr1 (address1),
    INDEX idx_addr2 (address2)
);
```

---

## Performance Optimization

### 1. Caching Strategy

```python
from functools import lru_cache
import redis

# Redis for distributed caching
redis_client = redis.Redis(host='localhost', port=6379, db=0)

@lru_cache(maxsize=1000)
def is_known_exchange(address):
    """Cache exchange lookups"""
    # Check Redis first
    cached = redis_client.get(f"exchange:{address}")
    if cached:
        return json.loads(cached)

    # Query database
    result = db.query(KnownAddress).filter_by(
        address=address,
        category='exchange'
    ).first()

    # Cache result
    redis_client.setex(
        f"exchange:{address}",
        3600,  # 1 hour TTL
        json.dumps(result is not None)
    )

    return result is not None
```

### 2. Batch Processing

```python
async def batch_check_intermediates(whale_txs):
    """
    Process multiple whale transactions in parallel
    """
    tasks = [
        check_one_hop_for_transaction(tx)
        for tx in whale_txs
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### 3. Database Indexing

```sql
-- Optimize transaction lookups
CREATE INDEX CONCURRENTLY idx_tx_from_timestamp
    ON transactions(from_address, timestamp DESC);

CREATE INDEX CONCURRENTLY idx_tx_to_timestamp
    ON transactions(to_address, timestamp DESC);

-- Optimize one-hop queries
CREATE INDEX CONCURRENTLY idx_onehop_whale_confidence
    ON one_hop_detections(whale_address, total_confidence DESC, detected_at DESC);

-- Partial index for high-confidence detections only
CREATE INDEX CONCURRENTLY idx_onehop_high_confidence
    ON one_hop_detections(whale_address, detected_at DESC)
    WHERE total_confidence >= 70;
```

### 4. Rate Limiting

```python
from asyncio import Semaphore

class RateLimiter:
    def __init__(self, max_calls_per_second=5):
        self.semaphore = Semaphore(max_calls_per_second)
        self.call_times = []

    async def __aenter__(self):
        await self.semaphore.acquire()
        # Ensure we don't exceed rate limit
        now = time.time()
        self.call_times = [t for t in self.call_times if now - t < 1.0]
        if len(self.call_times) >= 5:
            sleep_time = 1.0 - (now - self.call_times[0])
            await asyncio.sleep(sleep_time)
        self.call_times.append(now)
        return self

    async def __aexit__(self, *args):
        self.semaphore.release()

# Usage
rate_limiter = RateLimiter(max_calls_per_second=5)

async def get_transaction_with_rate_limit(tx_hash):
    async with rate_limiter:
        return await web3.eth.get_transaction(tx_hash)
```

---

## Examples и Case Studies

### Example 1: Simple One-Hop Dump

**Real scenario (Vitalik's donation):**
```
1. Vitalik sent 600 ETH to fresh address (0xabc...)
   Time: 2023-05-10 14:32:00 UTC

2. 0xabc... sent 600 ETH to Coinbase
   Time: 2023-05-10 14:47:00 UTC (15 min later)

Detected signals:
✅ Time correlation: 15 min -> +80
✅ Amount match: exact -> +80
✅ Fresh address: created same day -> +70
✅ Nonce gap: 1 (immediate) -> +95
✅ Exchange destination -> +50

Total confidence: 95/100
Alert: HIGH PROBABILITY DUMP
```

### Example 2: Split Pattern

**Scenario:**
```
1. Whale sends 1000 ETH to 0xIntermediate

2. 0xIntermediate splits:
   - 500 ETH to Binance (12 min later)
   - 500 ETH to Coinbase (14 min later)

Detected signals:
✅ Time correlation: <15 min -> +85
✅ Split pattern detected -> +70
✅ Multiple exchanges -> +60
✅ Gas prices match (same entity) -> +80

Total confidence: 89/100
Alert: COORDINATED DUMP ACROSS EXCHANGES
```

### Example 3: DEX + Exchange Pattern

**Scenario:**
```
1. Whale sends 1000 ETH to 0xIntermediate

2. 0xIntermediate swaps on Uniswap:
   1000 ETH -> 3,500,000 USDT (8 min later)

3. 0xIntermediate sends 3,500,000 USDT to Binance (3 min later)

Detected signals:
✅ Time correlation: <15 min total -> +85
✅ DEX interaction: ETH -> USDT -> Exchange -> +90
✅ Fresh address -> +70
✅ Sequential nonces -> +95

Total confidence: 96/100
Alert: VERY HIGH CONFIDENCE DUMP - STABLECOIN CONVERSION
```

### Example 4: Multi-Hop Chain

**Scenario:**
```
1. Whale sends 1000 ETH to 0xInt1

2. 0xInt1 sends 1000 ETH to 0xInt2 (5 min later)

3. 0xInt2 sends 1000 ETH to Binance (7 min later)

Detected signals:
✅ 3-hop chain detected -> +60
✅ Time coherence: 12 min total -> +70
✅ Amount preserved through chain -> +65
✅ Both intermediates are fresh addresses -> +70

Total confidence: 82/100
Alert: MULTI-HOP DUMP DETECTED (3 hops)
```

---

**Версия документа:** 1.0
**Дата создания:** 2025-11-21
**Статус:** Phase 1 signals implemented, Phase 2 documented
