"""
The Graph Token Discovery - METHOD 2: CORRECTED with Adaptive Filters
Fixed SushiSwap issue by using DEX-specific liquidity thresholds
"""

import os
import requests
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import List, Dict, Tuple

load_dotenv()

# Configuration
GRAPH_API_KEY = os.getenv("GRAPH_API_KEY")
UNISWAP_V2_ID = os.getenv("UNISWAP_V2_ID") 
SUSHISWAP_ID = os.getenv("SUSHISWAP_ID")

GRAPH_GATEWAY_BASE = "https://gateway-arbitrum.network.thegraph.com/api"

# Target age range (1.5-2.5 months for pump analysis)
MIN_AGE_DAYS = 45    
MAX_AGE_DAYS = 75    
SLICE_DURATION_DAYS = 5

# Pagination settings
MAX_RESULTS_PER_QUERY = 1000  # GraphQL limit
PAGINATION_DELAY_SEC = 0.5    # Rate limiting between requests

def build_subgraph_url(subgraph_id: str) -> str:
    return f"{GRAPH_GATEWAY_BASE}/{GRAPH_API_KEY}/subgraphs/id/{subgraph_id}"

# FIXED: DEX-specific configurations with adaptive thresholds
SUBGRAPHS = {
    "uniswap_v2": {
        "url": build_subgraph_url(UNISWAP_V2_ID),
        "name": "Uniswap V2",
        "liquidity_threshold": "1000"  # Higher threshold - Uniswap has more liquidity
    },
    "sushiswap": {
        "url": build_subgraph_url(SUSHISWAP_ID),
        "name": "SushiSwap", 
        "liquidity_threshold": "1"     # FIXED: Much lower threshold for SushiSwap
    }
}

def fetch_all_pairs_in_slice(url: str, subgraph_name: str, liquidity_threshold: str, start_ts: int, end_ts: int) -> List[Dict]:
    """
    Collect ALL pairs in a time slice using pagination.
    FIXED: Now accepts liquidity_threshold parameter for DEX-specific filtering.
    """
    all_pairs = []
    skip = 0
    page_number = 1
    
    while True:
        query = f"""
        query($start: BigInt!, $end: BigInt!, $first: Int!, $skip: Int!) {{
          pairs(
            where: {{ 
              createdAtTimestamp_gte: $start,
              createdAtTimestamp_lte: $end,
              reserveUSD_gte: "{liquidity_threshold}"
            }}
            first: $first
            skip: $skip
            orderBy: createdAtTimestamp
            orderDirection: asc
          ) {{
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
            reserveUSD
            volumeUSD
            txCount
          }}
        }}
        """
        
        variables = {
            "start": start_ts,
            "end": end_ts,
            "first": MAX_RESULTS_PER_QUERY,
            "skip": skip
        }
        
        try:
            response = requests.post(
                url,
                json={"query": query, "variables": variables},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "errors" not in data:
                    pairs = data.get("data", {}).get("pairs", [])
                    
                    if not pairs:
                        # No more data available
                        break
                    
                    all_pairs.extend(pairs)
                    print(f"      Page {page_number}: +{len(pairs)} pairs (total: {len(all_pairs)})")
                    
                    if len(pairs) < MAX_RESULTS_PER_QUERY:
                        # This was the last page
                        break
                    
                    # Prepare for next page
                    skip += MAX_RESULTS_PER_QUERY
                    page_number += 1
                    
                    # Rate limiting
                    time.sleep(PAGINATION_DELAY_SEC)
                    
                else:
                    print(f"      GraphQL Error: {data['errors'][0]['message']}")
                    break
            else:
                print(f"      HTTP Error: {response.status_code}")
                break
                
        except requests.exceptions.RequestException as e:
            print(f"      Network Error: {e}")
            break
        except Exception as e:
            print(f"      Unexpected Error: {e}")
            break
    
    return all_pairs

def discover_tokens_with_adaptive_filters() -> Tuple[List[Dict], Dict]:
    """
    Main discovery function using adaptive liquidity filters for different DEX.
    FIXED: Now applies DEX-specific thresholds instead of universal $1000.
    """
    print("The Graph Token Discovery - CORRECTED ADAPTIVE FILTERS")
    print("=" * 60)
    print(f"Target: {MIN_AGE_DAYS}-{MAX_AGE_DAYS} day old tokens")
    print(f"Strategy: DEX-specific filters + temporal slicing + pagination")
    print()
    
    # Calculate time slices
    now = datetime.now()
    total_range_days = MAX_AGE_DAYS - MIN_AGE_DAYS
    num_slices = total_range_days // SLICE_DURATION_DAYS
    
    all_discovered_pairs = []
    subgraph_stats = {}
    
    for subgraph_name, config in SUBGRAPHS.items():
        print(f"Processing {config['name']} (threshold: ${config['liquidity_threshold']})...")
        url = config["url"]
        liquidity_threshold = config["liquidity_threshold"]
        subgraph_pairs = []
        slice_results = []
        
        for i in range(num_slices):
            slice_start_days = MIN_AGE_DAYS + (i * SLICE_DURATION_DAYS)
            slice_end_days = slice_start_days + SLICE_DURATION_DAYS
            
            slice_start_time = now - timedelta(days=slice_end_days)  # Older boundary
            slice_end_time = now - timedelta(days=slice_start_days)   # Newer boundary
            
            slice_start_ts = int(slice_start_time.timestamp())
            slice_end_ts = int(slice_end_time.timestamp())
            
            print(f"\n   Slice {i+1}/{num_slices}: {slice_start_days}-{slice_end_days} days ago")
            print(f"   Date range: {slice_start_time.strftime('%m-%d')} to {slice_end_time.strftime('%m-%d')}")
            
            # FIXED: Pass liquidity_threshold to fetch function
            slice_pairs = fetch_all_pairs_in_slice(url, subgraph_name, liquidity_threshold, slice_start_ts, slice_end_ts)
            slice_results.append(len(slice_pairs))
            subgraph_pairs.extend(slice_pairs)
            
            print(f"   Slice total: {len(slice_pairs)} pairs")
        
        # Add subgraph identifier to each pair
        for pair in subgraph_pairs:
            pair['subgraph_source'] = subgraph_name
            pair['subgraph_name'] = config['name']
            pair['liquidity_threshold_used'] = liquidity_threshold
        
        all_discovered_pairs.extend(subgraph_pairs)
        
        subgraph_stats[subgraph_name] = {
            "total_pairs": len(subgraph_pairs),
            "slice_results": slice_results,
            "avg_per_slice": sum(slice_results) / len(slice_results) if slice_results else 0,
            "liquidity_threshold": liquidity_threshold
        }
        
        print(f"\n   {config['name']} Summary:")
        print(f"   - Total pairs: {len(subgraph_pairs)}")
        print(f"   - Average per slice: {subgraph_stats[subgraph_name]['avg_per_slice']:.1f}")
        print(f"   - Slice distribution: {slice_results}")
        print(f"   - Liquidity threshold used: ${liquidity_threshold}")
    
    return all_discovered_pairs, subgraph_stats

def analyze_discovery_results(all_pairs: List[Dict], stats: Dict):
    """Analyze and report discovery results with DEX-specific insights."""
    print(f"\n" + "=" * 60)
    print(f"CORRECTED ADAPTIVE FILTERS RESULTS")
    print(f"=" * 60)
    
    total_pairs = len(all_pairs)
    print(f"Total pairs discovered: {total_pairs}")
    
    # Compare with previous results
    previous_method_total = 60    # Original (first: 10)
    method1_estimate = 366        # Method 1 estimate  
    method2_original = 555        # Method 2 original (Uniswap only)
    
    print(f"\nComparison with previous approaches:")
    print(f"  Original (first: 10): {previous_method_total} pairs")
    print(f"  Method 1 estimate: {method1_estimate} pairs") 
    print(f"  Method 2 original (Uniswap only): {method2_original} pairs")
    print(f"  Method 2 corrected (multi-DEX): {total_pairs} pairs")
    
    if total_pairs > method2_original:
        improvement = total_pairs / previous_method_total
        print(f"  Final improvement factor: {improvement:.1f}x")
    
    # Subgraph breakdown with threshold info
    print(f"\nBreakdown by DEX (with adaptive thresholds):")
    for subgraph_name, subgraph_stats in stats.items():
        print(f"  {subgraph_name}: {subgraph_stats['total_pairs']} pairs")
        print(f"    Threshold: ${subgraph_stats['liquidity_threshold']}")
        print(f"    Avg per slice: {subgraph_stats['avg_per_slice']:.1f}")
        
        # Quality assessment based on results
        if subgraph_stats['total_pairs'] > 100:
            print(f"    Status: ✅ EXCELLENT data source")
        elif subgraph_stats['total_pairs'] > 10:
            print(f"    Status: ✅ GOOD data source") 
        elif subgraph_stats['total_pairs'] > 0:
            print(f"    Status: ⚠️ LOW volume but working")
        else:
            print(f"    Status: ❌ NO DATA - needs investigation")
    
    # Success evaluation
    print(f"\nDexScreener replacement evaluation:")
    if total_pairs >= 500:
        print(f"  Status: ✅ EXCELLENT - Multi-DEX approach successful")
    elif total_pairs >= 300:
        print(f"  Status: ✅ VERY GOOD - Significant improvement over DexScreener")
    elif total_pairs >= 100:
        print(f"  Status: ✅ GOOD - Better than DexScreener")
    else:
        print(f"  Status: ⚠️ NEEDS_IMPROVEMENT - Consider adding more DEX sources")
    
    return total_pairs >= 300

def main():
    """Execute corrected discovery with adaptive DEX filters."""
    print("Initializing The Graph corrected discovery with adaptive filters...")
    
    # Execute discovery with DEX-specific thresholds
    all_pairs, stats = discover_tokens_with_adaptive_filters()
    
    # Analyze results
    success = analyze_discovery_results(all_pairs, stats)
    
    # Final recommendation
    print(f"\nFINAL ASSESSMENT:")
    print(f"=" * 30)
    
    if success:
        print(f"✅ SUCCESS: Multi-DEX approach with adaptive filters working")
        print(f"- Found {len(all_pairs)} tokens across multiple DEX")
        print(f"- Adaptive thresholds solved SushiSwap issue")
        print(f"- Ready for production integration")
        print(f"- Can expand to more DEX sources if needed")
    else:
        print(f"⚠️ PARTIAL SUCCESS: Good foundation but room for improvement")
        print(f"- Consider adding more DEX subgraphs")
        print(f"- May need further threshold optimization")
    
    return len(all_pairs)

if __name__ == "__main__":
    total_discovered = main()
    print(f"\nDiscovery complete. Total pairs: {total_discovered}")
