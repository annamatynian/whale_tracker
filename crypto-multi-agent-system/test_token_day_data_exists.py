"""Check if tokenDayDatas exists in Uniswap V2 subgraph"""
import sys
import os
import requests
from dotenv import load_dotenv

sys.path.insert(0, r'C:\Users\annam\Documents\DeFi-RAG-Project\crypto-multi-agent-system')

load_dotenv()

api_key = os.getenv("GRAPH_API_KEY")
uniswap_v2_id = os.getenv("UNISWAP_V2_ID")

if not api_key or not uniswap_v2_id:
    print("GRAPH_API_KEY or UNISWAP_V2_ID not found")
    exit(1)

url = f"https://gateway.thegraph.com/api/{api_key}/subgraphs/id/{uniswap_v2_id}"

# Попробуем запросить tokenDayDatas
query = """
query TestTokenDayData {
  tokenDayDatas(first: 1, orderBy: date, orderDirection: desc) {
    id
    date
    token {
      id
      symbol
    }
    dailyVolumeUSD
    totalLiquidityUSD
  }
}
"""

print("Testing if tokenDayDatas exists in Uniswap V2 subgraph...")
print("=" * 60)

try:
    response = requests.post(
        url,
        json={"query": query},
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        
        if "errors" in data:
            print("GraphQL Error:")
            for error in data["errors"]:
                print(f"  {error['message']}")
            print("\n❌ tokenDayDatas does NOT exist in this subgraph")
        else:
            token_day_datas = data.get("data", {}).get("tokenDayDatas", [])
            if token_day_datas:
                print("✓ tokenDayDatas EXISTS!")
                print(f"\nExample data:")
                example = token_day_datas[0]
                print(f"  Token: {example['token']['symbol']}")
                print(f"  Date: {example['date']}")
                print(f"  Daily Volume USD: ${float(example['dailyVolumeUSD']):,.2f}")
                print(f"  Total Liquidity USD: ${float(example['totalLiquidityUSD']):,.2f}")
            else:
                print("⚠️ Query successful but no data returned")
    else:
        print(f"HTTP Error: {response.status_code}")
        
except Exception as e:
    print(f"Error: {e}")

print("=" * 60)
