"""
Быстрый тест URL для проверки исправления
"""
import requests
import json

# Тестируем исправленный URL
GRAPH_API_KEY = "a8b151d24c11a49e10351cc5811646fb"
UNISWAP_V2_ID = "A3Np3RQbaBA6oKJgiwDJeo5T3zrYfGHPWFYayMwtNDum"

# Новый правильный URL
correct_url = f"https://gateway.thegraph.com/api/{GRAPH_API_KEY}/subgraphs/id/{UNISWAP_V2_ID}"

print("🧪 Тестируем исправленный URL...")
print(f"URL: {correct_url}")

# Мета-запрос
test_query = """
query {
  _meta {
    block {
      number
    }
    hasIndexingErrors
  }
}
"""

try:
    response = requests.post(
        correct_url,
        json={"query": test_query},
        headers={"Content-Type": "application/json"},
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ SUCCESS!")
        print(json.dumps(data, indent=2))
    else:
        print(f"❌ Error: {response.text}")
        
except Exception as e:
    print(f"❌ Exception: {e}")
