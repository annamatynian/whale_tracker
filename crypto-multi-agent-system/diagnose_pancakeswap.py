"""
PancakeSwap V2 Subgraph Diagnostic Tool
Diagnoses why PancakeSwap V2 returned 0 results and suggests fixes
"""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

GRAPH_API_KEY = os.getenv("GRAPH_API_KEY")
PANCAKESWAP_V2_ID = os.getenv("PANCAKESWAP_V2_ID")
GRAPH_GATEWAY_BASE = "https://gateway-arbitrum.network.thegraph.com/api"

def build_subgraph_url(subgraph_id: str) -> str:
    return f"{GRAPH_GATEWAY_BASE}/{GRAPH_API_KEY}/subgraphs/id/{subgraph_id}"

def test_pancakeswap_connectivity():
    """Test if PancakeSwap V2 subgraph is accessible."""
    print("🔍 DIAGNOSTIC 1: PancakeSwap V2 Connectivity")
    print("=" * 50)
    
    if not PANCAKESWAP_V2_ID:
        print("❌ PANCAKESWAP_V2_ID not found in .env file")
        print("   Please add: PANCAKESWAP_V2_ID=your_subgraph_id")
        return False
    
    url = build_subgraph_url(PANCAKESWAP_V2_ID)
    print(f"Testing URL: {url}")
    
    # Basic health check
    basic_query = """
    query {
      _meta {
        block {
          number
          timestamp
        }
        deployment
        hasIndexingErrors
      }
    }
    """
    
    try:
        response = requests.post(url, json={"query": basic_query}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "errors" not in data:
                meta = data.get("data", {}).get("_meta", {})
                block = meta.get("block", {})
                
                print(f"✅ PancakeSwap V2 subgraph is accessible")
                print(f"   Latest block: {block.get('number', 'N/A')}")
                print(f"   Block timestamp: {block.get('timestamp', 'N/A')}")
                print(f"   Deployment: {meta.get('deployment', 'N/A')}")
                print(f"   Has indexing errors: {meta.get('hasIndexingErrors', 'N/A')}")
                return True
            else:
                print(f"❌ GraphQL errors: {data['errors']}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_pancakeswap_schema():
    """Test PancakeSwap V2 pair schema and recent data."""
    print(f"\n🔍 DIAGNOSTIC 2: PancakeSwap V2 Schema & Recent Data")
    print("=" * 50)
    
    url = build_subgraph_url(PANCAKESWAP_V2_ID)
    
    # Test basic pair query
    schema_query = """
    query {
      pairs(first: 5, orderBy: createdAtTimestamp, orderDirection: desc) {
        id
        token0 {
          symbol
        }
        token1 {
          symbol
        }
        createdAtTimestamp
        reserveUSD
        volumeUSD
      }
    }
    """
    
    try:
        response = requests.post(url, json={"query": schema_query}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "errors" not in data:
                pairs = data.get("data", {}).get("pairs", [])
                print(f"✅ Found {len(pairs)} recent pairs")
                
                if pairs:
                    print(f"   Recent PancakeSwap V2 pairs:")
                    for i, pair in enumerate(pairs):
                        timestamp = int(pair.get("createdAtTimestamp", 0))
                        created_time = datetime.fromtimestamp(timestamp) if timestamp > 0 else "N/A"
                        age_days = (datetime.now() - created_time).days if timestamp > 0 else "N/A"
                        
                        token0_symbol = pair.get("token0", {}).get("symbol", "?")
                        token1_symbol = pair.get("token1", {}).get("symbol", "?")
                        reserve = float(pair.get("reserveUSD", 0))
                        
                        print(f"      {i+1}. {token0_symbol}/{token1_symbol}")
                        print(f"         Created: {created_time}")
                        print(f"         Age: {age_days} days")
                        print(f"         Reserve: ${reserve:,.2f}")
                    return True
                else:
                    print(f"   ⚠️ No recent pairs found")
                    return False
            else:
                print(f"❌ GraphQL errors: {data['errors']}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_pancakeswap_filters():
    """Test different liquidity filters for PancakeSwap V2."""
    print(f"\n🔍 DIAGNOSTIC 3: Testing Liquidity Filters")
    print("=" * 50)
    
    url = build_subgraph_url(PANCAKESWAP_V2_ID)
    
    # Test with different thresholds
    filter_tests = [
        {"name": "No filter", "threshold": None},
        {"name": "$1 threshold", "threshold": "1"},
        {"name": "$10 threshold", "threshold": "10"},
        {"name": "$100 threshold", "threshold": "100"},
        {"name": "$1000 threshold", "threshold": "1000"}
    ]
    
    # Use recent time slice for testing
    now = datetime.now()
    slice_start_time = now - timedelta(days=50)  # 50 days ago
    slice_end_time = now - timedelta(days=45)    # 45 days ago
    
    start_ts = int(slice_start_time.timestamp())
    end_ts = int(slice_end_time.timestamp())
    
    print(f"Testing date range: {slice_start_time.strftime('%Y-%m-%d')} to {slice_end_time.strftime('%Y-%m-%d')}")
    
    for test in filter_tests:
        print(f"\n   Testing: {test['name']}")
        
        if test['threshold']:
            where_clause = f'createdAtTimestamp_gte: $start, createdAtTimestamp_lte: $end, reserveUSD_gte: "{test["threshold"]}"'
        else:
            where_clause = 'createdAtTimestamp_gte: $start, createdAtTimestamp_lte: $end'
        
        query = f"""
        query($start: BigInt!, $end: BigInt!) {{
          pairs(
            where: {{ {where_clause} }}
            first: 20
            orderBy: createdAtTimestamp
            orderDirection: asc
          ) {{
            id
            createdAtTimestamp
            reserveUSD
            token0 {{ symbol }}
            token1 {{ symbol }}
          }}
        }}
        """
        
        try:
            response = requests.post(
                url,
                json={"query": query, "variables": {"start": start_ts, "end": end_ts}},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if "errors" not in data:
                    pairs = data.get("data", {}).get("pairs", [])
                    print(f"      Result: {len(pairs)} pairs found")
                    
                    if pairs:
                        reserves = [float(p.get('reserveUSD', 0)) for p in pairs[:3]]
                        symbols = [f"{p.get('token0',{}).get('symbol','?')}/{p.get('token1',{}).get('symbol','?')}" for p in pairs[:3]]
                        print(f"      Sample pairs: {symbols}")
                        print(f"      Sample reserves: ${reserves}")
                else:
                    print(f"      Error: {data['errors'][0]['message']}")
            else:
                print(f"      HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"      Exception: {e}")

def test_alternative_pancakeswap_ids():
    """Test alternative PancakeSwap subgraph IDs."""
    print(f"\n🔍 DIAGNOSTIC 4: Alternative PancakeSwap Subgraphs")
    print("=" * 50)
    
    # Common PancakeSwap subgraph alternatives
    alternatives = [
        {
            "name": "PancakeSwap V2 (public)",
            "endpoint": "https://api.thegraph.com/subgraphs/name/pancakeswap/exchange-v2"
        },
        {
            "name": "PancakeSwap BSC (public)", 
            "endpoint": "https://api.thegraph.com/subgraphs/name/pancakeswap/pairs"
        }
    ]
    
    print("Testing known public PancakeSwap subgraphs...")
    
    for alt in alternatives:
        print(f"\n   Testing: {alt['name']}")
        print(f"   Endpoint: {alt['endpoint']}")
        
        basic_query = """
        query {
          pairs(first: 1) {
            id
            token0 { symbol }
            token1 { symbol }
          }
        }
        """
        
        try:
            response = requests.post(alt['endpoint'], json={"query": basic_query}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "errors" not in data:
                    pairs = data.get("data", {}).get("pairs", [])
                    if pairs:
                        pair = pairs[0]
                        token0 = pair.get("token0", {}).get("symbol", "?")
                        token1 = pair.get("token1", {}).get("symbol", "?")
                        print(f"      ✅ Accessible - sample pair: {token0}/{token1}")
                    else:
                        print(f"      ⚠️ Accessible but no pairs found")
                else:
                    print(f"      ❌ Errors: {data['errors'][0]['message']}")
            else:
                print(f"      ❌ HTTP Error: {response.status_code}")
        except Exception as e:
            print(f"      ❌ Connection Error: {e}")

def main():
    """Run complete PancakeSwap V2 diagnostic."""
    print("🔧 PancakeSwap V2 Subgraph Diagnostic Tool")
    print("=" * 60)
    print("Investigating why PancakeSwap V2 returned 0 results")
    print()
    
    # Check environment
    if not PANCAKESWAP_V2_ID:
        print("❌ PANCAKESWAP_V2_ID not set in .env file")
        print("Please add it and re-run diagnostics")
        return
    
    # Run diagnostics
    connectivity_ok = test_pancakeswap_connectivity()
    
    if connectivity_ok:
        has_data = test_pancakeswap_schema()
        
        if has_data:
            test_pancakeswap_filters()
        else:
            print(f"\n⚠️ PancakeSwap subgraph has no recent pairs")
    
    test_alternative_pancakeswap_ids()
    
    print(f"\n🎯 PANCAKESWAP DIAGNOSTIC SUMMARY")
    print("=" * 40)
    print("Possible issues and solutions:")
    print("1. Wrong PANCAKESWAP_V2_ID: Try alternative subgraph IDs")
    print("2. Threshold too high: Lower from $100 to $1 or $10")
    print("3. BSC vs Ethereum: Ensure using BSC-specific subgraph")
    print("4. Subgraph inactive: Use public alternatives")
    print("5. Time range issue: BSC may have different activity patterns")
    print("\nRecommended next steps:")
    print("- If connectivity fails: Update PANCAKESWAP_V2_ID")
    print("- If no data: Lower liquidity threshold")
    print("- If schema errors: Use alternative public subgraphs")

if __name__ == "__main__":
    main()
