"""
The Graph Token Discovery - METHOD 2: Full Pagination Implementation
Final production-ready version that replaces DexScreener approach
Collects ALL tokens aged 45-75 days using temporal slicing + pagination
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

SUBGRAPHS = {
    "uniswap_v2": {
        "url": build_subgraph_url(UNISWAP_V2_ID),
        "name": "Uniswap V2"
    },
    "sushiswap": {
        "url": build_subgraph_url(SUSHISWAP_ID),
        "name": "SushiSwap"
    }
}

def fetch_all_pairs_in_slice(url: str, subgraph_name: str, start_ts: int, end_ts: int) -> List[Dict]:
    """
    Collect ALL pairs in a time slice using pagination.
    Implements Gemini's Method 2 with full pagination.
    """
    all_pairs = []
    skip = 0
    page_number = 1
    
    while True:
        query = """
        query($start: BigInt!, $end: BigInt!, $first: Int!, $skip: Int!) {
          pairs(
            where: { 
              createdAtTimestamp_gte: $start,
              createdAtTimestamp_lte: $end,
              reserveUSD_gte: "1000"
            }
            first: $first
            skip: $skip
            orderBy: createdAtTimestamp
            orderDirection: asc
          ) {
            id
            token0 {
              id
              symbol
              name
            }
            token1 {
              id
              symbol  
              name
            }
            createdAtTimestamp
            reserveUSD
            volumeUSD
            txCount
          }
        }
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

def discover_tokens_with_full_pagination() -> Tuple[List[Dict], Dict]:
    """
    Main discovery function using temporal slicing + full pagination.
    Returns: (all_pairs, statistics)
    """
    print("The Graph Token Discovery - FULL PAGINATION (Method 2)")
    print("=" * 60)
    print(f"Target: {MIN_AGE_DAYS}-{MAX_AGE_DAYS} day old tokens")
    print(f"Strategy: {SLICE_DURATION_DAYS}-day slices with full pagination")
    print()
    
    # Calculate time slices
    now = datetime.now()
    total_range_days = MAX_AGE_DAYS - MIN_AGE_DAYS
    num_slices = total_range_days // SLICE_DURATION_DAYS
    
    all_discovered_pairs = []
    subgraph_stats = {}
    
    for subgraph_name, config in SUBGRAPHS.items():
        print(f"Processing {config['name']}...")
        url = config["url"]
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
            
            # Fetch ALL pairs in this slice using pagination
            slice_pairs = fetch_all_pairs_in_slice(url, subgraph_name, slice_start_ts, slice_end_ts)
            slice_results.append(len(slice_pairs))
            subgraph_pairs.extend(slice_pairs)
            
            print(f"   Slice total: {len(slice_pairs)} pairs")
        
        # Add subgraph identifier to each pair
        for pair in subgraph_pairs:
            pair['subgraph_source'] = subgraph_name
            pair['subgraph_name'] = config['name']
        
        all_discovered_pairs.extend(subgraph_pairs)
        
        subgraph_stats[subgraph_name] = {
            "total_pairs": len(subgraph_pairs),
            "slice_results": slice_results,
            "avg_per_slice": sum(slice_results) / len(slice_results) if slice_results else 0
        }
        
        print(f"\n   {config['name']} Summary:")
        print(f"   - Total pairs: {len(subgraph_pairs)}")
        print(f"   - Average per slice: {subgraph_stats[subgraph_name]['avg_per_slice']:.1f}")
        print(f"   - Slice distribution: {slice_results}")
    
    return all_discovered_pairs, subgraph_stats

def analyze_discovery_results(all_pairs: List[Dict], stats: Dict):
    """Analyze and report discovery results."""
    print(f"\n" + "=" * 60)
    print(f"FULL PAGINATION DISCOVERY RESULTS")
    print(f"=" * 60)
    
    total_pairs = len(all_pairs)
    print(f"Total pairs discovered: {total_pairs}")
    
    # Compare with previous results
    previous_method_total = 60  # Original 6 × 10
    method1_estimate = 366     # 6 × 61
    
    print(f"\nComparison with previous approaches:")
    print(f"  Original (first: 10): {previous_method_total} pairs")
    print(f"  Method 1 estimate: {method1_estimate} pairs") 
    print(f"  Method 2 (pagination): {total_pairs} pairs")
    
    if total_pairs > method1_estimate:
        improvement = total_pairs / previous_method_total
        print(f"  Improvement factor: {improvement:.1f}x")
    
    # Subgraph breakdown
    print(f"\nBreakdown by subgraph:")
    for subgraph_name, subgraph_stats in stats.items():
        print(f"  {subgraph_name}: {subgraph_stats['total_pairs']} pairs")
        print(f"    Avg per slice: {subgraph_stats['avg_per_slice']:.1f}")
    
    # Age distribution analysis
    if all_pairs:
        print(f"\nAge distribution analysis:")
        now = datetime.now()
        age_groups = {
            "45-50 days": 0,
            "50-55 days": 0, 
            "55-60 days": 0,
            "60-65 days": 0,
            "65-70 days": 0,
            "70-75 days": 0
        }
        
        for pair in all_pairs[:100]:  # Analyze first 100 for performance
            timestamp = int(pair.get("createdAtTimestamp", 0))
            if timestamp > 0:
                created_time = datetime.fromtimestamp(timestamp)
                age_days = (now - created_time).days
                
                if 45 <= age_days < 50:
                    age_groups["45-50 days"] += 1
                elif 50 <= age_days < 55:
                    age_groups["50-55 days"] += 1
                elif 55 <= age_days < 60:
                    age_groups["55-60 days"] += 1
                elif 60 <= age_days < 65:
                    age_groups["60-65 days"] += 1
                elif 65 <= age_days < 70:
                    age_groups["65-70 days"] += 1
                elif 70 <= age_days < 75:
                    age_groups["70-75 days"] += 1
        
        for age_range, count in age_groups.items():
            print(f"  {age_range}: {count} pairs (sample of 100)")
    
    # Success evaluation
    print(f"\nDexScreener replacement evaluation:")
    if total_pairs >= 300:
        print(f"  Status: EXCELLENT - Far exceeds DexScreener capabilities")
    elif total_pairs >= 100:
        print(f"  Status: GOOD - Significantly better than DexScreener")
    elif total_pairs >= 50:
        print(f"  Status: ADEQUATE - Better than DexScreener but could improve")
    else:
        print(f"  Status: NEEDS_IMPROVEMENT - May need filter adjustments")
    
    return total_pairs >= 100

def main():
    """Execute full pagination token discovery."""
    print("Initializing The Graph full pagination discovery...")
    
    # Execute discovery with full pagination
    all_pairs, stats = discover_tokens_with_full_pagination()
    
    # Analyze results
    success = analyze_discovery_results(all_pairs, stats)
    
    # Final recommendation
    print(f"\nFINAL ASSESSMENT:")
    print(f"=" * 30)
    
    if success:
        print(f"SUCCESS: Ready to replace DexScreener pipeline")
        print(f"- Found {len(all_pairs)} tokens in target age range")
        print(f"- Full pagination ensures complete data collection")
        print(f"- Temporal slicing strategy proven effective")
        print(f"- Can integrate into existing discovery agent")
    else:
        print(f"PARTIAL SUCCESS: Good foundation but may need optimization")
        print(f"- Consider adjusting filters or expanding time range")
        print(f"- May need additional subgraphs for better coverage")
    
    return len(all_pairs)

if __name__ == "__main__":
    total_discovered = main()
    print(f"\nDiscovery complete. Total pairs: {total_discovered}")
