#!/usr/bin/env python3
"""
Тест исправления Uniswap V2 субграфа
Проверяем, работает ли новый правильный URL
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_corrected_uniswap_v2_url():
    """Тестируем исправленный URL для Uniswap V2."""
    
    # Параметры из .env
    GRAPH_API_KEY = os.getenv("GRAPH_API_KEY")
    UNISWAP_V2_ID = os.getenv("UNISWAP_V2_ID")
    
    if not GRAPH_API_KEY or not UNISWAP_V2_ID:
        print("❌ GRAPH_API_KEY или UNISWAP_V2_ID не найдены в .env")
        return False
    
    # Исправленный URL
    correct_url = f"https://gateway.thegraph.com/api/{GRAPH_API_KEY}/subgraphs/id/{UNISWAP_V2_ID}"
    
    print(f"🧪 Тестируем исправленный URL:")
    print(f"   {correct_url}")
    
    # Простой мета-запрос для проверки доступности
    test_query = """
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
        response = requests.post(
            correct_url,
            json={"query": test_query},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"📊 HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'errors' in data:
                print("❌ GraphQL Errors:")
                for error in data['errors']:
                    print(f"   - {error.get('message', 'Unknown error')}")
                return False
            
            if 'data' in data and '_meta' in data['data']:
                meta = data['data']['_meta']
                print("✅ SUCCESS! Субграф работает!")
                print(f"🎯 Блок: {meta['block']['number']}")
                print(f"🎯 Timestamp: {meta['block']['timestamp']}")
                print(f"🎯 Deployment: {meta['deployment']}")
                print(f"🎯 Indexing Errors: {meta['hasIndexingErrors']}")
                return True
            else:
                print("❌ Неожиданная структура ответа:")
                print(json.dumps(data, indent=2))
                return False
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка запроса: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def test_simple_pairs_query():
    """Тестируем простой запрос пар."""
    
    GRAPH_API_KEY = os.getenv("GRAPH_API_KEY")
    UNISWAP_V2_ID = os.getenv("UNISWAP_V2_ID")
    
    correct_url = f"https://gateway.thegraph.com/api/{GRAPH_API_KEY}/subgraphs/id/{UNISWAP_V2_ID}"
    
    # Запрос первых 5 пар
    pairs_query = """
    query {
      pairs(first: 5, orderBy: createdAtTimestamp, orderDirection: desc) {
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
      }
    }
    """
    
    print(f"\n🔍 Тестируем запрос пар...")
    
    try:
        response = requests.post(
            correct_url,
            json={"query": pairs_query},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if 'errors' in data:
                print("❌ GraphQL Errors в запросе пар:")
                for error in data['errors']:
                    print(f"   - {error.get('message', 'Unknown error')}")
                return False
            
            if 'data' in data and 'pairs' in data['data']:
                pairs = data['data']['pairs']
                print(f"✅ Получено {len(pairs)} пар!")
                
                for i, pair in enumerate(pairs[:3]):  # Показываем первые 3
                    print(f"   {i+1}. {pair['token0']['symbol']}/{pair['token1']['symbol']}")
                    print(f"      ID: {pair['id']}")
                    print(f"      Reserve USD: ${float(pair['reserveUSD']):,.2f}")
                
                return True
            else:
                print("❌ Неожиданная структура ответа в запросе пар")
                return False
        else:
            print(f"❌ HTTP Error в запросе пар: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка в запросе пар: {e}")
        return False

if __name__ == "__main__":
    print("🚀 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЯ UNISWAP V2 СУБГРАФА")
    print("=" * 60)
    
    # Тест 1: Проверка доступности
    meta_success = test_corrected_uniswap_v2_url()
    
    if meta_success:
        # Тест 2: Проверка запроса пар
        pairs_success = test_simple_pairs_query()
        
        if pairs_success:
            print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
            print("✅ Проблема с Uniswap V2 субграфом РЕШЕНА!")
        else:
            print("\n⚠️  Мета-запрос работает, но есть проблемы с запросом пар")
    else:
        print("\n❌ Проблема не решена. Нужно дополнительное исследование.")
    
    print("=" * 60)
