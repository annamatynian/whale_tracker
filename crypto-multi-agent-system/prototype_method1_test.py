"""
The Graph Discovery - Testing Gemini Method 1: first: 300
Quick test to see if increasing 'first' parameter breaks the 10-pair limit
"""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

GRAPH_API_KEY = os.getenv("GRAPH_API_KEY")
UNISWAP_V2_ID = os.getenv("UNISWAP_V2_ID")
GRAPH_GATEWAY_BASE = "https://gateway-arbitrum.network.thegraph.com/api"

def build_subgraph_url(subgraph_id: str) -> str:
    return f"{GRAPH_GATEWAY_BASE}/{GRAPH_API_KEY}/subgraphs/id/{subgraph_id}"

def test_increased_first():
    """Test single slice with first: 300 vs first: 10"""
    url = build_subgraph_url(UNISWAP_V2_ID)
    
    # Calculate one 5-day slice (45-50 days ago)
    now = datetime.now()
    slice_start_time = now - timedelta(days=50)  # 50 days ago
    slice_end_time = now - timedelta(days=45)    # 45 days ago
    
    start_ts = int(slice_start_time.timestamp())
    end_ts = int(slice_end_time.timestamp())
    
    print(f"Testing slice: 45-50 days ago")
    print(f"Range: {slice_start_time.strftime('%Y-%m-%d')} to {slice_end_time.strftime('%Y-%m-%d')}")
    
    # Test 1: Previous approach (first: 10)
    query_small = """
    query($start: BigInt!, $end: BigInt!) {
      pairs(
        where: { 
          createdAtTimestamp_gte: $start,
          createdAtTimestamp_lte: $end,
          reserveUSD_gte: "1000"
        }
        first: 10
        orderBy: createdAtTimestamp
        orderDirection: desc
      ) {
        id
        createdAtTimestamp
      }
    }
    """
    
    # Test 2: Gemini Method 1 (first: 300)
    query_large = """
    query($start: BigInt!, $end: BigInt!) {
      pairs(
        where: { 
          createdAtTimestamp_gte: $start,
          createdAtTimestamp_lte: $end,
          reserveUSD_gte: "1000"
        }
        first: 300
        orderBy: createdAtTimestamp
        orderDirection: desc
      ) {
        id
        createdAtTimestamp
      }
    }
    """
    
    variables = {"start": start_ts, "end": end_ts}
    
    print(f"\n🧪 Test 1: first: 10 (previous approach)")
    try:
        response = requests.post(url, json={"query": query_small, "variables": variables}, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if "errors" not in data:
                pairs = data.get("data", {}).get("pairs", [])
                print(f"   Result: {len(pairs)} pairs")
            else:
                print(f"   Error: {data['errors']}")
        else:
            print(f"   HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    print(f"\n🚀 Test 2: first: 300 (Gemini Method 1)")
    try:
        response = requests.post(url, json={"query": query_large, "variables": variables}, timeout=20)
        if response.status_code == 200:
            data = response.json()
            if "errors" not in data:
                pairs = data.get("data", {}).get("pairs", [])
                print(f"   Result: {len(pairs)} pairs")
                
                if len(pairs) > 10:
                    print(f"   ✅ SUCCESS: Broke the 10-pair limit!")
                    print(f"   📈 Improvement: {len(pairs) - 10} additional pairs")
                elif len(pairs) == 10:
                    print(f"   ⚠️ Still 10 pairs - may need different approach")
                else:
                    print(f"   📊 Found {len(pairs)} pairs in this slice")
            else:
                print(f"   Error: {data['errors']}")
        else:
            print(f"   HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   Exception: {e}")

if __name__ == "__main__":
    print("🔍 Quick Test: Gemini Method 1 (first: 300)")
    print("=" * 50)
    test_increased_first()
    print(f"\nTest complete - checking if 'first' parameter was the bottleneck")
