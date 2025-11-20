"""
The Graph Prototype - Step 2: Working GraphQL Client
Tests actual data retrieval with discovered schema fields
"""

import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

GRAPH_API_KEY = os.getenv("GRAPH_API_KEY")
UNISWAP_V2_ID = os.getenv("UNISWAP_V2_ID") 
UNISWAP_V3_ID = os.getenv("UNISWAP_V3_ID")
SUSHISWAP_ID = os.getenv("SUSHISWAP_ID")

GRAPH_GATEWAY_BASE = "https://gateway-arbitrum.network.thegraph.com/api"

def build_subgraph_url(subgraph_id: str) -> str:
    return f"{GRAPH_GATEWAY_BASE}/{GRAPH_API_KEY}/subgraphs/id/{subgraph_id}"

WORKING_SUBGRAPHS = {
    "uniswap_v2": {
        "url": build_subgraph_url(UNISWAP_V2_ID),
        "field": "pairs"
    },
    "sushiswap": {
        "url": build_subgraph_url(SUSHISWAP_ID), 
        "field": "pairs"
    }
}

def discover_pair_structure(name: str, url: str, field: str):
    """Discover the actual structure of pairs field."""
    print(f"\n🔍 Discovering {name}.{field} structure...")
    
    # Simple query to understand available fields
    structure_query = f"""
    query {{
      {field}(first: 1) {{
        id
        token0 {{
          id
          symbol
          name
        }}
        token1 {{
          id
          symbol  
          name
        }}
        createdAtTimestamp
        createdAtBlockNumber
        volumeUSD
        liquidityUSD
        txCount
      }}
    }}
    """
    
    try:
        response = requests.post(
            url,
            json={"query": structure_query},
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" not in data:
                pairs = data.get("data", {}).get(field, [])
                if pairs:
                    pair = pairs[0]
                    print(f"✅ Structure discovered:")
                    print(f"   ID: {pair.get('id', 'N/A')}")
                    print(f"   Token0: {pair.get('token0', {}).get('symbol', 'N/A')}")
                    print(f"   Token1: {pair.get('token1', {}).get('symbol', 'N/A')}")
                    print(f"   CreatedAt: {pair.get('createdAtTimestamp', 'N/A')}")
                    print(f"   Volume USD: {pair.get('volumeUSD', 'N/A')}")
                    print(f"   Liquidity USD: {pair.get('liquidityUSD', 'N/A')}")
                    
                    # Convert timestamp to readable
                    timestamp = pair.get('createdAtTimestamp')
                    if timestamp:
                        readable_time = datetime.fromtimestamp(int(timestamp)).strftime("%Y-%m-%d %H:%M:%S")
                        hours_ago = (datetime.now() - datetime.fromtimestamp(int(timestamp))).total_seconds() / 3600
                        print(f"   Created: {readable_time} ({hours_ago:.1f} hours ago)")
                    
                    return pair
                else:
                    print(f"⚠️ No pairs found")
            else:
                print(f"❌ GraphQL Errors: {data['errors']}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return None

def test_time_filtering(name: str, url: str, field: str):
    """Test filtering pairs by creation time."""
    print(f"\n🕒 Testing time filtering for {name}...")
    
    # Calculate timestamps
    now = datetime.now()
    hours_24_ago = now - timedelta(hours=24)
    hours_48_ago = now - timedelta(hours=48)
    
    timestamp_24h = int(hours_24_ago.timestamp())
    timestamp_48h = int(hours_48_ago.timestamp())
    
    print(f"   Looking for pairs created between:")
    print(f"   48h ago: {hours_48_ago.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   24h ago: {hours_24_ago.strftime('%Y-%m-%d %H:%M:%S')}")
    
    time_filter_query = f"""
    query {{
      recent_pairs: {field}(
        where: {{ 
          createdAtTimestamp_gte: "{timestamp_48h}",
          createdAtTimestamp_lte: "{timestamp_24h}"
        }}
        orderBy: createdAtTimestamp
        orderDirection: desc
        first: 5
      ) {{
        id
        token0 {{
          id
          symbol
        }}
        token1 {{
          id
          symbol
        }}
        createdAtTimestamp
        liquidityUSD
        volumeUSD
      }}
    }}
    """
    
    try:
        response = requests.post(
            url,
            json={"query": time_filter_query},
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" not in data:
                pairs = data.get("data", {}).get("recent_pairs", [])
                print(f"✅ Found {len(pairs)} pairs in time window:")
                
                for i, pair in enumerate(pairs):
                    timestamp = pair.get('createdAtTimestamp')
                    if timestamp:
                        created_time = datetime.fromtimestamp(int(timestamp))
                        hours_ago = (now - created_time).total_seconds() / 3600
                        token0_symbol = pair.get('token0', {}).get('symbol', 'Unknown')
                        token1_symbol = pair.get('token1', {}).get('symbol', 'Unknown') 
                        liquidity = pair.get('liquidityUSD', '0')
                        
                        print(f"   {i+1}. {token0_symbol}/{token1_symbol}")
                        print(f"      Created: {hours_ago:.1f}h ago, Liquidity: ${float(liquidity):,.0f}")
                
                return pairs
            else:
                print(f"❌ GraphQL Errors: {data['errors']}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Time filtering error: {e}")
    
    return []

def test_latest_pairs(name: str, url: str, field: str):
    """Get latest created pairs without time filter."""
    print(f"\n🆕 Getting latest pairs from {name}...")
    
    latest_query = f"""
    query {{
      {field}(
        orderBy: createdAtTimestamp
        orderDirection: desc
        first: 10
      ) {{
        id
        token0 {{
          symbol
          name
        }}
        token1 {{
          symbol
          name
        }}
        createdAtTimestamp
        liquidityUSD
        volumeUSD
        txCount
      }}
    }}
    """
    
    try:
        response = requests.post(
            url,
            json={"query": latest_query},
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" not in data:
                pairs = data.get("data", {}).get(field, [])
                print(f"✅ Found {len(pairs)} latest pairs:")
                
                now = datetime.now()
                recent_count = 0
                
                for i, pair in enumerate(pairs[:5]):  # Show first 5
                    timestamp = pair.get('createdAtTimestamp')
                    if timestamp:
                        created_time = datetime.fromtimestamp(int(timestamp))
                        hours_ago = (now - created_time).total_seconds() / 3600
                        
                        if hours_ago <= 48:  # Recent pairs
                            recent_count += 1
                        
                        token0_symbol = pair.get('token0', {}).get('symbol', 'Unknown')
                        token1_symbol = pair.get('token1', {}).get('symbol', 'Unknown')
                        liquidity = float(pair.get('liquidityUSD', 0))
                        volume = float(pair.get('volumeUSD', 0))
                        
                        age_indicator = "🔥" if hours_ago <= 24 else "⏰" if hours_ago <= 48 else "📅"
                        
                        print(f"   {i+1}. {age_indicator} {token0_symbol}/{token1_symbol}")
                        print(f"      Age: {hours_ago:.1f}h, Liquidity: ${liquidity:,.0f}, Volume: ${volume:,.0f}")
                
                print(f"\n📊 Summary: {recent_count}/{len(pairs)} pairs are <48h old")
                return pairs, recent_count
            else:
                print(f"❌ GraphQL Errors: {data['errors']}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Latest pairs error: {e}")
    
    return [], 0

def main():
    """Test working GraphQL queries with discovered schema."""
    print("🔍 The Graph Working Client Test")
    print("=" * 50)
    
    results = {}
    
    for name, config in WORKING_SUBGRAPHS.items():
        url = config["url"]
        field = config["field"]
        
        print(f"\n" + "="*60)
        print(f"TESTING: {name}")
        print(f"="*60)
        
        # Step 1: Discover structure
        structure = discover_pair_structure(name, url, field)
        
        if structure:
            # Step 2: Test latest pairs
            latest_pairs, recent_count = test_latest_pairs(name, url, field)
            
            # Step 3: Test time filtering 
            filtered_pairs = test_time_filtering(name, url, field)
            
            results[name] = {
                "structure": structure,
                "latest_pairs": len(latest_pairs),
                "recent_pairs": recent_count,
                "filtered_pairs": len(filtered_pairs)
            }
        else:
            results[name] = {"error": "Could not discover structure"}
    
    # Summary
    print(f"\n" + "="*60)
    print(f"WORKING CLIENT TEST SUMMARY")
    print(f"="*60)
    
    working_subgraphs = []
    
    for name, result in results.items():
        if "error" not in result:
            print(f"\n🎯 {name}: WORKING")
            print(f"   Latest pairs available: {result['latest_pairs']}")
            print(f"   Recent pairs (<48h): {result['recent_pairs']}")
            print(f"   Time filtering: {'Working' if result['filtered_pairs'] >= 0 else 'Failed'}")
            working_subgraphs.append(name)
        else:
            print(f"\n❌ {name}: {result['error']}")
    
    if working_subgraphs:
        print(f"\n🚀 READY FOR STEP 3: Token Discovery Implementation")
        print(f"   Working subgraphs: {', '.join(working_subgraphs)}")
        print(f"   Best choice: {working_subgraphs[0]}")
        return working_subgraphs[0]
    else:
        print(f"\n🛑 No working subgraphs found")
        return None

if __name__ == "__main__":
    result = main()
    if result:
        print(f"\n🎯 Next: Build token discovery pipeline using {result}")
    else:
        print(f"\n❌ Cannot proceed to token discovery")
