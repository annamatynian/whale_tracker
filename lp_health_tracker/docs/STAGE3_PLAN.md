# 🌐 Stage 3 Plan: Web3Manager Integration + On-chain Data

## Overview

Stage 3 focuses on integrating real blockchain data through Web3Manager to get actual LP position data from on-chain sources, moving beyond mock data and API prices to real DeFi protocol integration.

## Current Status After Testing Migration

✅ **Foundation completed:**
- Core IL calculation engine working
- Multi-pool manager operational
- Professional pytest testing framework
- Mock data providers functional
- Documentation comprehensive

⏭️ **Next: Web3Manager Integration**

## Stage 3 Objectives

### Primary Goals
1. **Web3Manager Implementation** - Connect to Ethereum/Polygon networks
2. **On-chain LP Data Retrieval** - Get real LP token balances and pool reserves
3. **Smart Contract Integration** - Read from Uniswap V2 pair contracts
4. **Real Position Tracking** - Monitor actual user LP positions on-chain

### Success Criteria
- [ ] Web3Manager connects to mainnet/testnet
- [ ] Can read LP token balances for user wallets
- [ ] Can get pool reserves from pair contracts
- [ ] Can calculate real-time position values
- [ ] Integration tests pass with live blockchain data

## Implementation Plan

### Phase 1: Web3Manager Foundation (Week 1)

**1.1 Create Web3Manager Class**
```python
# src/web3_utils.py enhancement
class Web3Manager:
    def __init__(self, network: str = "ethereum_mainnet"):
        self.network = network
        self.w3 = None
        self.contracts = {}
    
    async def initialize(self) -> bool:
        """Initialize Web3 connection"""
        
    async def get_erc20_balance(self, token_address: str, wallet_address: str) -> float:
        """Get ERC20 token balance"""
        
    async def get_uniswap_v2_reserves(self, pair_address: str) -> Dict[str, float]:
        """Get reserves from Uniswap V2 pair"""
```

**1.2 Contract Integration**
- ERC20 token contract calls
- Uniswap V2 pair contract calls  
- LP token balance checking
- Pool reserves reading

**1.3 Network Configuration**
```python
# config/networks.py
NETWORKS = {
    'ethereum_mainnet': {
        'rpc_url': 'https://mainnet.infura.io/v3/{api_key}',
        'chain_id': 1,
        'contracts': {
            'uniswap_v2_factory': '0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f'
        }
    },
    'ethereum_sepolia': {
        'rpc_url': 'https://sepolia.infura.io/v3/{api_key}',
        'chain_id': 11155111,
        'contracts': {...}
    }
}
```

### Phase 2: On-chain Data Integration (Week 2)

**2.1 LP Position Discovery**
```python
class LPPositionScanner:
    async def find_lp_positions(self, wallet_address: str) -> List[Dict]:
        """Scan wallet for LP token holdings"""
        
    async def get_position_details(self, lp_token_address: str, wallet_address: str) -> Dict:
        """Get detailed position information"""
```

**2.2 Real-time Pool Data**
```python
class PoolDataProvider:
    async def get_pool_reserves(self, pair_address: str) -> Dict:
        """Get current pool reserves"""
        
    async def get_pool_metadata(self, pair_address: str) -> Dict:
        """Get pool token addresses, decimals, etc."""
```

**2.3 Position Value Calculation**
- Use real LP token balances
- Get actual pool reserves
- Calculate precise position values
- Account for token decimals

### Phase 3: Live Data Integration (Week 3)

**3.1 Enhanced SimpleMultiPoolManager**
```python
class SimpleMultiPoolManager:
    def __init__(self, data_provider: DataProvider, web3_manager: Web3Manager = None):
        self.data_provider = data_provider
        self.web3_manager = web3_manager  # NEW
        
    async def analyze_pool_with_onchain_data(self, position: Dict) -> Dict:
        """Analyze using real on-chain data"""
```

**3.2 Hybrid Data Sources**
- On-chain data for LP balances and reserves
- API data for token prices
- Fallback mechanisms if on-chain fails

**3.3 Data Validation**
- Cross-check on-chain vs API data
- Detect inconsistencies
- Alert on suspicious changes

### Phase 4: Testing & Validation (Week 4)

**4.1 Web3 Integration Tests**
```python
# tests/test_web3_integration.py
@pytest.mark.integration
@pytest.mark.slow
class TestWeb3Integration:
    async def test_web3_connection(self):
        """Test Web3 connection to networks"""
        
    async def test_lp_balance_reading(self):
        """Test reading real LP balances"""
        
    async def test_pool_reserves_reading(self):
        """Test reading pool reserves"""
```

**4.2 End-to-End Validation**
- Compare calculated vs actual position values
- Validate IL calculations with real data
- Test with multiple pool types

**4.3 Performance Testing**
- RPC call optimization
- Batch requests where possible
- Rate limiting compliance

## Technical Implementation Details

### Web3 Connection Management

**Connection Strategy:**
```python
class Web3ConnectionManager:
    def __init__(self):
        self.providers = [
            InfuraProvider(),
            AlchemyProvider(), 
            AnkrProvider()     # Fallback
        ]
    
    async def get_connection(self) -> Web3:
        """Get working Web3 connection with fallback"""
```

**Error Handling:**
- RPC provider failures
- Network congestion
- Rate limiting
- Invalid responses

### Contract ABIs and Interfaces

**Required ABIs:**
```python
# ABIs for contract interaction
ERC20_ABI = [...]      # Token balance calls
UNISWAP_V2_PAIR_ABI = [...]  # Pool reserves, metadata
UNISWAP_V2_FACTORY_ABI = [...]  # Pair discovery
```

**Contract Wrappers:**
```python
class ERC20Contract:
    def __init__(self, address: str, web3: Web3):
        self.contract = web3.eth.contract(address=address, abi=ERC20_ABI)
    
    async def balance_of(self, wallet: str) -> int:
        """Get token balance in wei"""

class UniswapV2Pair:
    async def get_reserves(self) -> Tuple[int, int]:
        """Get pool reserves"""
```

### Data Flow Architecture

**New Data Flow:**
```
1. User Wallet Address
   ↓
2. Web3Manager → Scan for LP tokens
   ↓  
3. For each LP position found:
   - Get LP token balance
   - Get pool reserves
   - Get token prices (API)
   ↓
4. Calculate position value and IL
   ↓
5. Compare with tracked positions
   ↓
6. Generate alerts if needed
```

### Integration with Existing System

**Backwards Compatibility:**
- Keep mock data provider for testing
- Maintain API-only mode for price data
- Optional Web3 integration (can be disabled)

**Configuration:**
```env
# .env additions
ENABLE_WEB3_INTEGRATION=true
AUTO_DISCOVER_POSITIONS=false  # Manual vs automatic position discovery
WEB3_TIMEOUT_SECONDS=30
MAX_CONCURRENT_WEB3_CALLS=5
```

## Testing Strategy

### Test Phases

**Phase 1: Unit Tests**
- Web3Manager individual methods
- Contract wrapper functions
- Data parsing and validation

**Phase 2: Integration Tests**
- End-to-end position scanning
- Real LP position analysis
- Cross-validation with known positions

**Phase 3: Performance Tests**
- RPC call optimization
- Large wallet scanning
- Concurrent position monitoring

### Test Networks

**Development:** Ethereum Sepolia (testnet)
**Staging:** Ethereum Mainnet (read-only)
**Production:** Multi-network support

## Risk Assessment

### Technical Risks
- **RPC Provider Reliability** - Multiple fallback providers
- **Rate Limiting** - Batch calls and caching
- **Gas Cost** (N/A - read-only operations)
- **Contract Changes** - Version detection and compatibility

### Mitigation Strategies
- Comprehensive error handling
- Graceful degradation to API-only mode
- Extensive testing on testnets
- Monitoring and alerting for failures

## Success Metrics

### Technical Metrics
- **Web3 Connection Uptime:** >99%
- **Data Accuracy:** Position values within 1% of actual
- **Response Time:** <10 seconds for position analysis
- **Error Rate:** <2% of Web3 calls fail

### Business Metrics
- **Feature Adoption:** % of users enabling Web3 integration
- **Data Quality:** Reduction in false alerts
- **User Satisfaction:** Feedback on real-time accuracy

## Dependencies and Prerequisites

### External Dependencies
```python
# Additional requirements.txt entries
web3==6.11.3
eth-account==0.9.0
multicall-py==1.0.1  # For batch contract calls
```

### Infrastructure
- Infura/Alchemy API keys with sufficient limits
- Stable internet connection for RPC calls
- Adequate server resources for concurrent Web3 calls

## Timeline and Milestones

### Week 1: Foundation
- [ ] Web3Manager basic implementation
- [ ] Network configuration setup
- [ ] Basic contract integration
- [ ] Unit tests for core functionality

### Week 2: On-chain Integration  
- [ ] LP position scanning
- [ ] Pool data retrieval
- [ ] Position value calculation with real data
- [ ] Integration tests

### Week 3: System Integration
- [ ] Enhance SimpleMultiPoolManager
- [ ] Hybrid data source implementation
- [ ] End-to-end workflow testing
- [ ] Performance optimization

### Week 4: Validation & Polish
- [ ] Comprehensive testing
- [ ] Documentation updates
- [ ] Error handling refinement
- [ ] Ready for production deployment

## Next Steps After Stage 3

**Stage 4 Preparation:**
- Uniswap V3 concentrated liquidity support
- Multi-chain expansion (Polygon, Arbitrum)
- Advanced analytics with historical on-chain data
- Web dashboard for position visualization

---

**🎯 Ready to begin Stage 3? Let's start with Web3Manager foundation and network connectivity!**
