"""
SushiSwap Subgraph Diagnostic Tool
Diagnoses why SushiSwap returned 0 results and suggests fixes
"""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

GRAPH_API_KEY = os.getenv("GRAPH_API_KEY")
SUSHISWAP_ID = os.getenv("SUSHISWAP_ID")
GRAPH_GATEWAY_BASE = "https://gateway-arbitrum.network.thegraph.com/api"

def build_subgraph_url(subgraph_id: str) -> str:
    return f"{GRAPH_GATEWAY_BASE}/{GRAPH_API_KEY}/subgraphs/id/{subgraph_id}"

def test_basic_sushiswap_connectivity():
    """Test if SushiSwap subgraph is accessible and responding."""
    print("🔍 DIAGNOSTIC 1: Basic SushiSwap Connectivity")
    print("=" * 50)
    
    url = build_subgraph_url(SUSHISWAP_ID)
    
    # Simple health check query
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
                
                print(f"✅ SushiSwap subgraph is accessible")
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

def test_sushiswap_pair_schema():
    """Test what fields are available in SushiSwap pairs."""
    print(f"\n🔍 DIAGNOSTIC 2: SushiSwap Pair Schema")
    print("=" * 50)
    
    url = build_subgraph_url(SUSHISWAP_ID)
    
    # Test basic pair query without filters
    schema_query = """
    query {
      pairs(first: 3, orderBy: createdAtTimestamp, orderDirection: desc) {
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
        txCount
      }
    }
    """
    
    try:
        response = requests.post(url, json={"query": schema_query}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "errors" not in data:
                pairs = data.get("data", {}).get("pairs", [])
                print(f"✅ Found {len(pairs)} pairs (latest 3)")
                
                if pairs:
                    for i, pair in enumerate(pairs):
                        timestamp = int(pair.get("createdAtTimestamp", 0))
                        created_time = datetime.fromtimestamp(timestamp) if timestamp > 0 else "N/A"
                        age_days = (datetime.now() - created_time).days if timestamp > 0 else "N/A"
                        
                        token0_symbol = pair.get("token0", {}).get("symbol", "?")
                        token1_symbol = pair.get("token1", {}).get("symbol", "?")
                        reserve = pair.get("reserveUSD", "0")
                        
                        print(f"   Pair {i+1}: {token0_symbol}/{token1_symbol}")
                        print(f"      Created: {created_time}")
                        print(f"      Age: {age_days} days")
                        print(f"      Reserve: ${reserve}")
                return len(pairs) > 0
            else:
                print(f"❌ GraphQL errors: {data['errors']}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_different_filters():
    """Test SushiSwap with different filter parameters."""
    print(f"\n🔍 DIAGNOSTIC 3: Testing Different Filters")
    print("=" * 50)
    
    url = build_subgraph_url(SUSHISWAP_ID)
    
    # Test different filter combinations
    filter_tests = [
        {
            "name": "No liquidity filter",
            "where_clause": 'createdAtTimestamp_gte: $start, createdAtTimestamp_lte: $end'
        },
        {
            "name": "Lower liquidity ($100)",
            "where_clause": 'createdAtTimestamp_gte: $start, createdAtTimestamp_lte: $end, reserveUSD_gte: "100"'
        },
        {
            "name": "Very low liquidity ($1)",
            "where_clause": 'createdAtTimestamp_gte: $start, createdAtTimestamp_lte: $end, reserveUSD_gte: "1"'
        }
    ]
    
    # Use a recent 5-day slice for testing
    now = datetime.now()
    slice_start_time = now - timedelta(days=50)  # 50 days ago
    slice_end_time = now - timedelta(days=45)    # 45 days ago
    
    start_ts = int(slice_start_time.timestamp())
    end_ts = int(slice_end_time.timestamp())
    
    print(f"Testing date range: {slice_start_time.strftime('%Y-%m-%d')} to {slice_end_time.strftime('%Y-%m-%d')}")
    
    for test in filter_tests:
        print(f"\n   Testing: {test['name']}")
        
        query = f"""
        query($start: BigInt!, $end: BigInt!) {{
          pairs(
            where: {{ {test['where_clause']} }}
            first: 50
            orderBy: createdAtTimestamp
            orderDirection: asc
          ) {{
            id
            createdAtTimestamp
            reserveUSD
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
                        print(f"      Sample reserve values: {[float(p.get('reserveUSD', 0)) for p in pairs[:3]]}")
                else:
                    print(f"      Error: {data['errors'][0]['message']}")
            else:
                print(f"      HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"      Exception: {e}")

def test_alternative_sushiswap_subgraphs():
    """Test alternative SushiSwap subgraph IDs that might be more active."""
    print(f"\n🔍 DIAGNOSTIC 4: Testing Alternative SushiSwap Subgraphs")
    print("=" * 50)
    
    # Known SushiSwap subgraph alternatives
    alternative_subgraphs = [
        {
            "name": "SushiSwap Ethereum (Alternative)",
            "id": "sushi-qa/sushiswap-ethereum"  # Public subgraph name
        },
        {
            "name": "SushiSwap Exchange",
            "id": "sushiswap/exchange"  # Another common ID
        }
    ]
    
    print("Testing known public SushiSwap subgraphs...")
    
    for subgraph in alternative_subgraphs:
        print(f"\n   Testing: {subgraph['name']}")
        print(f"   ID: {subgraph['id']}")
        
        # For public subgraphs, use different endpoint
        public_url = f"https://api.thegraph.com/subgraphs/name/{subgraph['id']}"
        
        basic_query = """
        query {
          pairs(first: 1) {
            id
          }
        }
        """
        
        try:
            response = requests.post(public_url, json={"query": basic_query}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if "errors" not in data:
                    pairs = data.get("data", {}).get("pairs", [])
                    print(f"      ✅ Accessible - found {len(pairs)} pairs in sample")
                else:
                    print(f"      ❌ Errors: {data['errors'][0]['message']}")
            else:
                print(f"      ❌ HTTP Error: {response.status_code}")
        except Exception as e:
            print(f"      ❌ Connection Error: {e}")

def main():
    """Run complete SushiSwap diagnostic."""
    print("🔧 SushiSwap Subgraph Diagnostic Tool")
    print("=" * 60)
    print("Investigating why SushiSwap returned 0 results")
    print()
    
    # Run diagnostics
    connectivity_ok = test_basic_sushiswap_connectivity()
    
    if connectivity_ok:
        has_data = test_sushiswap_pair_schema()
        
        if has_data:
            test_different_filters()
        else:
            print(f"\n⚠️ SushiSwap subgraph has no recent pairs - may be inactive")
    
    test_alternative_sushiswap_subgraphs()
    
    print(f"\n🎯 DIAGNOSTIC SUMMARY")
    print("=" * 30)
    print("Recommendations based on results:")
    print("1. If connectivity fails: Check SUSHISWAP_ID in .env")
    print("2. If no recent pairs: Subgraph may be inactive/deprecated")
    print("3. If filter issues: Adjust reserveUSD threshold")
    print("4. Consider using alternative subgraphs if available")
    print("\nNext step: Review diagnostic output and apply recommended fixes")

if __name__ == "__main__":
    main()
