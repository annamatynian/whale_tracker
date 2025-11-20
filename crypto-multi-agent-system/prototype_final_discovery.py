"""
The Graph Token Discovery - Final Prototype (Step 3)
Complete replacement for broken DexScreener approach
"""

import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import List, Dict, Optional

load_dotenv()

# Configuration
GRAPH_API_KEY = os.getenv("GRAPH_API_KEY")
UNISWAP_V2_ID = os.getenv("UNISWAP_V2_ID") 
SUSHISWAP_ID = os.getenv("SUSHISWAP_ID")

GRAPH_GATEWAY_BASE = "https://gateway-arbitrum.network.thegraph.com/api"

# Discovery filters (similar to current system)
MIN_LIQUIDITY_USD = 5000
MIN_VOLUME_USD = 1000  
MAX_AGE_HOURS = 48
MIN_DISCOVERY_SCORE = 30

def build_subgraph_url(subgraph_id: str) -> str:
    return f"{GRAPH_GATEWAY_BASE}/{GRAPH_API_KEY}/subgraphs/id/{subgraph_id}"

SUBGRAPHS = {
    "uniswap_v2": {
        "url": build_subgraph_url(UNISWAP_V2_ID),
        "name": "Uniswap V2",
        "chain_id": "ethereum"
    },
    "sushiswap": {
        "url": build_subgraph_url(SUSHISWAP_ID),
        "name": "SushiSwap", 
        "chain_id": "ethereum"
    }
}

class TokenCandidate:
    """Represents a discovered token candidate."""
    def __init__(self, pair_data: Dict, subgraph_name: str, chain_id: str):
        self.pair_address = pair_data.get("id", "")
        self.chain_id = chain_id
        self.subgraph_name = subgraph_name
        
        # Token information
        token0 = pair_data.get("token0", {})
        token1 = pair_data.get("token1", {})
        
        self.token0_address = token0.get("id", "")
        self.token0_symbol = token0.get("symbol", "UNKNOWN")
        self.token1_address = token1.get("id", "")
        self.token1_symbol = token1.get("symbol", "UNKNOWN")
        
        # Financial metrics
        self.volume_usd = float(pair_data.get("volumeUSD", 0))
        self.liquidity_usd = float(pair_data.get("reserveUSD", 0))
        
        # Time information
        timestamp = pair_data.get("createdAtTimestamp", "0")
        self.created_at = datetime.fromtimestamp(int(timestamp)) if timestamp != "0" else datetime.now()
        self.age_hours = (datetime.now() - self.created_at).total_seconds() / 3600
        self.age_minutes = self.age_hours * 60
        
        # Scoring
        self.discovery_score = self._calculate_score()
        self.discovery_reason = self._generate_reason()
    
    def _calculate_score(self) -> int:
        """Calculate discovery score similar to existing system."""
        score = 40  # Base score
        
        # Age bonus (newer is better)
        if self.age_hours <= 6:
            score += 25
        elif self.age_hours <= 24:
            score += 15
        elif self.age_hours <= 48:
            score += 5
        
        # Liquidity bonus
        if self.liquidity_usd >= 50000:
            score += 20
        elif self.liquidity_usd >= 20000:
            score += 15
        elif self.liquidity_usd >= MIN_LIQUIDITY_USD:
            score += 10
        
        # Volume bonus  
        if self.volume_usd >= 100000:
            score += 15
        elif self.volume_usd >= 10000:
            score += 10
        elif self.volume_usd >= MIN_VOLUME_USD:
            score += 5
        
        return min(score, 100)
    
    def _generate_reason(self) -> str:
        """Generate reasoning similar to existing system."""
        reasons = []
        
        reasons.append(f"Age={self.age_hours:.1f}h")
        
        if self.liquidity_usd >= MIN_LIQUIDITY_USD:
            reasons.append(f"Liq=${self.liquidity_usd/1000:.0f}k")
        
        if self.volume_usd >= MIN_VOLUME_USD:
            reasons.append(f"Vol=${self.volume_usd/1000:.0f}k")
        
        return " | ".join(reasons)
    
    def passes_filters(self) -> bool:
        """Check if candidate passes discovery filters."""
        return (
            self.age_hours <= MAX_AGE_HOURS and
            self.liquidity_usd >= MIN_LIQUIDITY_USD and
            self.discovery_score >= MIN_DISCOVERY_SCORE
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format compatible with existing system."""
        return {
            "pair_address": self.pair_address,
            "chain_id": self.chain_id,
            "base_token_address": self.token0_address,
            "base_token_symbol": self.token0_symbol,
            "base_token_name": self.token0_symbol,  # Using symbol as name for now
            "quote_token_address": self.token1_address,
            "quote_token_symbol": self.token1_symbol,
            "liquidity_usd": self.liquidity_usd,
            "volume_h24": self.volume_usd,  # Using total volume as approximation
            "price_usd": 0.0,  # Not available from subgraph
            "price_change_h1": 0.0,  # Not available from subgraph
            "pair_created_at": self.created_at,
            "age_minutes": self.age_minutes,
            "discovery_score": self.discovery_score,
            "discovery_reason": self.discovery_reason,
            "data_source": f"TheGraph-{self.subgraph_name}",
            "discovery_timestamp": datetime.now()
        }

def fetch_recent_pairs(subgraph_name: str, subgraph_config: Dict, hours_lookback: int = 48) -> List[Dict]:
    """Fetch recent pairs from a subgraph."""
    url = subgraph_config["url"]
    
    # Calculate timestamp threshold
    threshold_time = datetime.now() - timedelta(hours=hours_lookback)
    timestamp_threshold = int(threshold_time.timestamp())
    
    print(f"🔍 Fetching pairs from {subgraph_name} (last {hours_lookback}h)...")
    
    query = """
    query($timestamp: BigInt!) {
      pairs(
        where: { 
          createdAtTimestamp_gte: $timestamp,
          reserveUSD_gte: "1000"
        }
        orderBy: createdAtTimestamp
        orderDirection: desc
        first: 50
      ) {
        id
        token0 {
          id
          symbol
        }
        token1 {
          id
          symbol
        }
        createdAtTimestamp
        volumeUSD
        reserveUSD
        txCount
      }
    }
    """
    
    try:
        response = requests.post(
            url,
            json={
                "query": query,
                "variables": {"timestamp": timestamp_threshold}
            },
            headers={"Content-Type": "application/json"},
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" not in data:
                pairs = data.get("data", {}).get("pairs", [])
                print(f"✅ Found {len(pairs)} recent pairs from {subgraph_name}")
                return pairs
            else:
                print(f"❌ GraphQL Errors in {subgraph_name}: {data['errors']}")
        else:
            print(f"❌ HTTP Error for {subgraph_name}: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error fetching from {subgraph_name}: {e}")
    
    return []

def process_discovered_tokens(all_pairs: List[TokenCandidate]) -> List[TokenCandidate]:
    """Process and filter discovered tokens."""
    print(f"\n📊 Processing {len(all_pairs)} discovered pairs...")
    
    # Apply filters
    filtered_pairs = [pair for pair in all_pairs if pair.passes_filters()]
    print(f"✅ {len(filtered_pairs)} pairs passed filters")
    
    # Remove duplicates (same token pair from different subgraphs)
    unique_pairs = []
    seen_tokens = set()
    
    for pair in filtered_pairs:
        # Create token pair identifier (order-independent)
        token_set = frozenset([pair.token0_address.lower(), pair.token1_address.lower()])
        
        if token_set not in seen_tokens:
            unique_pairs.append(pair)
            seen_tokens.add(token_set)
        else:
            print(f"⚠️ Duplicate removed: {pair.token0_symbol}/{pair.token1_symbol}")
    
    print(f"✅ {len(unique_pairs)} unique pairs after deduplication")
    
    # Sort by discovery score
    unique_pairs.sort(key=lambda x: x.discovery_score, reverse=True)
    
    return unique_pairs

def discover_new_tokens() -> List[Dict]:
    """Main discovery function - replacement for DexScreener approach."""
    print("🚀 The Graph Token Discovery Pipeline")
    print("=" * 60)
    
    all_candidates = []
    
    # Fetch from all configured subgraphs
    for subgraph_name, config in SUBGRAPHS.items():
        pairs_data = fetch_recent_pairs(subgraph_name, config, MAX_AGE_HOURS)
        
        # Convert to TokenCandidate objects
        for pair_data in pairs_data:
            candidate = TokenCandidate(pair_data, subgraph_name, config["chain_id"])
            all_candidates.append(candidate)
    
    if not all_candidates:
        print("⚠️ No pairs found from any subgraph")
        return []
    
    # Process and filter
    final_candidates = process_discovered_tokens(all_candidates)
    
    # Convert to format compatible with existing system
    discovery_reports = [candidate.to_dict() for candidate in final_candidates]
    
    return discovery_reports

def main():
    """Test the complete token discovery pipeline."""
    print("🔍 The Graph Token Discovery - Final Test")
    print("=" * 60)
    print(f"Configuration:")
    print(f"  Min Liquidity: ${MIN_LIQUIDITY_USD:,}")
    print(f"  Min Volume: ${MIN_VOLUME_USD:,}")
    print(f"  Max Age: {MAX_AGE_HOURS} hours")
    print(f"  Min Score: {MIN_DISCOVERY_SCORE}")
    print()
    
    # Run discovery
    discovered_tokens = discover_new_tokens()
    
    if discovered_tokens:
        print(f"\n🎯 DISCOVERY RESULTS")
        print(f"=" * 40)
        print(f"Found {len(discovered_tokens)} promising tokens:")
        
        for i, token in enumerate(discovered_tokens[:10], 1):  # Show top 10
            print(f"\n#{i}: {token['base_token_symbol']}/{token['quote_token_symbol']}")
            print(f"   Score: {token['discovery_score']}/100")
            print(f"   Reason: {token['discovery_reason']}")
            print(f"   Age: {token['age_minutes']:.0f} minutes")
            print(f"   Source: {token['data_source']}")
            print(f"   Pair: {token['pair_address'][:10]}...")
        
        print(f"\n🚀 SUCCESS: Ready to replace DexScreener pipeline!")
        print(f"   Integration point: Return `discovered_tokens` from discovery agent")
        
    else:
        print(f"\n⚠️ No tokens found matching criteria")
        print(f"   Try adjusting filters or expanding time window")
    
    return discovered_tokens

if __name__ == "__main__":
    result = main()
    print(f"\nDiscovery complete. Found {len(result)} tokens.")
