"""
The Graph Token Discovery - METHOD 2: Multi-DEX with PancakeSwap V2 Added
Includes Uniswap V2, SushiSwap, and PancakeSwap V2 with adaptive filters
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
PANCAKESWAP_V2_ID = os.getenv("PANCAKESWAP_V2_ID")  # NEW: PancakeSwap V2

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

# Multi-DEX configurations with adaptive thresholds
SUBGRAPHS = {
    "uniswap_v2": {
        "url": build_subgraph_url(UNISWAP_V2_ID),
        "name": "Uniswap V2",
        "liquidity_threshold": "1000",  # Higher threshold - Uniswap has more liquidity
        "chain": "Ethereum"
    },
    "sushiswap": {
        "url": build_subgraph_url(SUSHISWAP_ID),
        "name": "SushiSwap", 
        "liquidity_threshold": "1",     # Lower threshold for SushiSwap
        "chain": "Ethereum"
    },
    "pancakeswap_v2": {
        "url": build_subgraph_url(PANCAKESWAP_V2_ID),
        "name": "PancakeSwap V2",
        "liquidity_threshold": "100",   # NEW: Medium threshold for BSC (cheaper than ETH)
        "chain": "BSC"
    }
}

def fetch_all_pairs_in_slice(url: str, subgraph_name: str, liquidity_threshold: str, start_ts: int, end_ts: int) -> List[Dict]:
    """
    Collect ALL pairs in a time slice using pagination.
    Works for Uniswap V2, SushiSwap, and PancakeSwap V2 (all use 'pairs' schema).
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

def discover_tokens_multi_dex() -> Tuple[List[Dict], Dict]:
    """
    Main discovery function across multiple DEX with adaptive filters.
    Now includes Uniswap V2, SushiSwap, AND PancakeSwap V2.
    """
    print("The Graph Token Discovery - MULTI-DEX (Uniswap V2 + SushiSwap + PancakeSwap V2)")
    print("=" * 80)
    print(f"Target: {MIN_AGE_DAYS}-{MAX_AGE_DAYS} day old tokens")
    print(f"Strategy: Multi-DEX + adaptive filters + temporal slicing + pagination")
    print(f"DEX Sources: {len(SUBGRAPHS)} subgraphs")
    print()
    
    # Calculate time slices
    now = datetime.now()
    total_range_days = MAX_AGE_DAYS - MIN_AGE_DAYS
    num_slices = total_range_days // SLICE_DURATION_DAYS
    
    all_discovered_pairs = []
    subgraph_stats = {}
    
    for subgraph_name, config in SUBGRAPHS.items():
        print(f"Processing {config['name']} ({config['chain']}) - threshold: ${config['liquidity_threshold']}...")
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
            
            # Fetch pairs with DEX-specific threshold
            slice_pairs = fetch_all_pairs_in_slice(url, subgraph_name, liquidity_threshold, slice_start_ts, slice_end_ts)
            slice_results.append(len(slice_pairs))
            subgraph_pairs.extend(slice_pairs)
            
            print(f"   Slice total: {len(slice_pairs)} pairs")
        
        # Add metadata to each pair
        for pair in subgraph_pairs:
            pair['subgraph_source'] = subgraph_name
            pair['subgraph_name'] = config['name']
            pair['chain'] = config['chain']
            pair['liquidity_threshold_used'] = liquidity_threshold
        
        all_discovered_pairs.extend(subgraph_pairs)
        
        subgraph_stats[subgraph_name] = {
            "total_pairs": len(subgraph_pairs),
            "slice_results": slice_results,
            "avg_per_slice": sum(slice_results) / len(slice_results) if slice_results else 0,
            "liquidity_threshold": liquidity_threshold,
            "chain": config['chain']
        }
        
        print(f"\n   {config['name']} Summary:")
        print(f"   - Total pairs: {len(subgraph_pairs)}")
        print(f"   - Average per slice: {subgraph_stats[subgraph_name]['avg_per_slice']:.1f}")
        print(f"   - Slice distribution: {slice_results}")
        print(f"   - Chain: {config['chain']}")
        print(f"   - Liquidity threshold: ${liquidity_threshold}")
    
    return all_discovered_pairs, subgraph_stats

def analyze_multi_dex_results(all_pairs: List[Dict], stats: Dict):
    """Analyze and report multi-DEX discovery results."""
    print(f"\n" + "=" * 80)
    print(f"MULTI-DEX DISCOVERY RESULTS")
    print(f"=" * 80)
    
    total_pairs = len(all_pairs)
    print(f"Total pairs discovered: {total_pairs}")
    
    # Compare with previous results
    previous_results = {
        "Original (first: 10)": 60,
        "Method 1 estimate": 366,
        "Method 2 (Uniswap only)": 555,
        "Method 2 corrected (Uni+Sushi)": 572
    }
    
    print(f"\nComparison with previous approaches:")
    for method, count in previous_results.items():
        print(f"  {method}: {count} pairs")
    print(f"  Method 2 Multi-DEX (current): {total_pairs} pairs")
    
    improvement = total_pairs / previous_results["Original (first: 10)"]
    print(f"  Final improvement factor: {improvement:.1f}x")
    
    # Breakdown by DEX and chain
    print(f"\nBreakdown by DEX:")
    chain_totals = {}
    
    for subgraph_name, subgraph_stats in stats.items():
        pairs_count = subgraph_stats['total_pairs']
        chain = subgraph_stats['chain']
        threshold = subgraph_stats['liquidity_threshold']
        avg_per_slice = subgraph_stats['avg_per_slice']
        
        # Track chain totals
        if chain not in chain_totals:
            chain_totals[chain] = 0
        chain_totals[chain] += pairs_count
        
        print(f"  {subgraph_name} ({chain}): {pairs_count} pairs")
        print(f"    Threshold: ${threshold}")
        print(f"    Avg per slice: {avg_per_slice:.1f}")
        
        # Quality assessment
        if pairs_count > 100:
            status = "EXCELLENT data source"
        elif pairs_count > 20:
            status = "GOOD data source" 
        elif pairs_count > 5:
            status = "MODERATE data source"
        elif pairs_count > 0:
            status = "LOW volume but working"
        else:
            status = "NO DATA - needs investigation"
        
        print(f"    Status: {status}")
        print()
    
    # Chain summary
    print(f"Summary by blockchain:")
    for chain, total in chain_totals.items():
        percentage = (total / total_pairs) * 100
        print(f"  {chain}: {total} pairs ({percentage:.1f}%)")
    
    # Success evaluation
    print(f"\nDexScreener replacement evaluation:")
    if total_pairs >= 700:
        print(f"  Status: EXCELLENT - Multi-chain approach highly successful")
    elif total_pairs >= 500:
        print(f"  Status: VERY GOOD - Strong multi-DEX coverage")
    elif total_pairs >= 300:
        print(f"  Status: GOOD - Solid improvement over single-source")
    else:
        print(f"  Status: NEEDS_IMPROVEMENT - Consider more sources")
    
    return total_pairs >= 500

def main():
    """Execute multi-DEX discovery with PancakeSwap V2 added."""
    print("Initializing Multi-DEX discovery with PancakeSwap V2...")
    
    # Check if all required environment variables are set
    required_vars = ["GRAPH_API_KEY", "UNISWAP_V2_ID", "SUSHISWAP_ID", "PANCAKESWAP_V2_ID"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"ERROR: Missing environment variables: {missing_vars}")
        print("Please add PANCAKESWAP_V2_ID to your .env file")
        return 0
    
    # Execute discovery across all DEX
    all_pairs, stats = discover_tokens_multi_dex()
    
    # Analyze results
    success = analyze_multi_dex_results(all_pairs, stats)
    
    # Final recommendation
    print(f"\nFINAL ASSESSMENT:")
    print(f"=" * 30)
    
    if success:
        print(f"SUCCESS: Multi-DEX, multi-chain approach working excellently")
        print(f"- Found {len(all_pairs)} tokens across multiple DEX and chains")
        print(f"- Ethereum DEX: Uniswap V2 + SushiSwap coverage")
        print(f"- BSC DEX: PancakeSwap V2 coverage") 
        print(f"- Ready for production integration")
        print(f"- Can add more chains/DEX as needed")
    else:
        print(f"PARTIAL SUCCESS: Good foundation, room for expansion")
        print(f"- Consider adding more DEX sources")
        print(f"- May optimize thresholds further")
    
    return len(all_pairs)

if __name__ == "__main__":
    total_discovered = main()
    print(f"\nMulti-DEX discovery complete. Total pairs: {total_discovered}")
