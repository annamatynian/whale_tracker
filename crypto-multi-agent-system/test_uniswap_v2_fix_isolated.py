#!/usr/bin/env python3
"""
ИЗОЛИРОВАННЫЙ ТЕСТ: Проверка исправления Uniswap V2 субграфа
============================================================

Этот тест проверяет ТОЛЬКО исправление URL для Uniswap V2 субграфа,
не затрагивая остальную систему.

Что тестируется:
1. Подключение к исправленному URL
2. Мета-запрос для проверки доступности субграфа  
3. Простой запрос пар для проверки работоспособности
4. Сравнение старого и нового URL

Автор: Isolated test for Uniswap V2 fix verification
"""

import os
import sys
import requests
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class Colors:
    """ANSI цвета для красивого вывода."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    """Печать заголовка."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*60}{Colors.END}")

def print_success(text):
    """Печать успеха."""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    """Печать ошибки."""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    """Печать предупреждения."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    """Печать информации."""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

def test_url_connectivity(url, description):
    """Тестирует подключение к URL."""
    print(f"\n{Colors.PURPLE}🧪 Тестируем: {description}{Colors.END}")
    print(f"   URL: {url}")
    
    # Простой мета-запрос для проверки доступности
    meta_query = """
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
        start_time = time.time()
        
        response = requests.post(
            url,
            json={"query": meta_query},
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        response_time = (time.time() - start_time) * 1000  # мс
        
        print(f"   📊 HTTP Status: {response.status_code}")
        print(f"   ⏱️  Response Time: {response_time:.1f}ms")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'errors' in data:
                print_error("GraphQL Errors:")
                for error in data['errors']:
                    print(f"      - {error.get('message', 'Unknown error')}")
                return False, f"GraphQL errors: {len(data['errors'])} errors"
            
            if 'data' in data and '_meta' in data['data']:
                meta = data['data']['_meta']
                print_success("Субграф доступен!")
                print(f"      🎯 Block Number: {meta['block']['number']}")
                print(f"      🎯 Block Timestamp: {meta['block']['timestamp']}")
                print(f"      🎯 Deployment ID: {meta['deployment']}")
                print(f"      🎯 Indexing Errors: {meta['hasIndexingErrors']}")
                return True, "SUCCESS"
            else:
                print_error("Неожиданная структура ответа")
                return False, "Invalid response structure"
                
        else:
            print_error(f"HTTP Error: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False, f"HTTP {response.status_code}"
            
    except requests.exceptions.Timeout:
        print_error("Timeout - субграф не отвечает")
        return False, "Timeout"
    except requests.exceptions.ConnectionError:
        print_error("Connection Error - не удается подключиться")
        return False, "Connection Error"
    except Exception as e:
        print_error(f"Unexpected Error: {e}")
        return False, str(e)

def test_pairs_query(url):
    """Тестирует запрос пар для проверки работоспособности."""
    print(f"\n{Colors.PURPLE}🔍 Тестируем запрос пар...{Colors.END}")
    
    # Запрос последних 3 пар
    pairs_query = """
    query {
      pairs(first: 3, orderBy: createdAtTimestamp, orderDirection: desc) {
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
      }
    }
    """
    
    try:
        start_time = time.time()
        
        response = requests.post(
            url,
            json={"query": pairs_query},
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            data = response.json()
            
            if 'errors' in data:
                print_error("GraphQL Errors в запросе пар:")
                for error in data['errors']:
                    print(f"      - {error.get('message', 'Unknown error')}")
                return False
            
            if 'data' in data and 'pairs' in data['data']:
                pairs = data['data']['pairs']
                print_success(f"Получено {len(pairs)} пар за {response_time:.1f}ms")
                
                if pairs:
                    print("      📈 Примеры пар:")
                    for i, pair in enumerate(pairs):
                        symbol0 = pair['token0']['symbol'] or 'Unknown'
                        symbol1 = pair['token1']['symbol'] or 'Unknown'
                        reserve_usd = float(pair.get('reserveUSD', 0))
                        
                        print(f"         {i+1}. {symbol0}/{symbol1}")
                        print(f"            💰 Reserve: ${reserve_usd:,.2f}")
                        print(f"            📅 Created: {pair['createdAtTimestamp']}")
                
                return True
            else:
                print_error("Неожиданная структура ответа в запросе пар")
                return False
        else:
            print_error(f"HTTP Error в запросе пар: {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Ошибка в запросе пар: {e}")
        return False

def main():
    """Основная функция теста."""
    print_header("ТЕСТ ИСПРАВЛЕНИЯ UNISWAP V2 СУБГРАФА")
    
    # Получаем параметры из .env
    GRAPH_API_KEY = os.getenv("GRAPH_API_KEY")
    UNISWAP_V2_ID = os.getenv("UNISWAP_V2_ID")
    
    if not GRAPH_API_KEY:
        print_error("GRAPH_API_KEY не найден в .env файле")
        return False
    
    if not UNISWAP_V2_ID:
        print_error("UNISWAP_V2_ID не найден в .env файле")
        return False
    
    print_info(f"API Key: {GRAPH_API_KEY}")
    print_info(f"Subgraph ID: {UNISWAP_V2_ID}")
    
    # URL-ы для тестирования
    old_url = f"https://gateway-arbitrum.network.thegraph.com/api/{GRAPH_API_KEY}/subgraphs/id/{UNISWAP_V2_ID}"
    new_url = f"https://gateway.thegraph.com/api/{GRAPH_API_KEY}/subgraphs/id/{UNISWAP_V2_ID}"
    
    results = {}
    
    # Тест 1: Старый URL (должен НЕ работать)
    print_header("ТЕСТ 1: СТАРЫЙ URL (ОЖИДАЕМ ОШИБКУ)")
    old_success, old_error = test_url_connectivity(old_url, "Старый неправильный URL")
    results['old_url'] = (old_success, old_error)
    
    # Тест 2: Новый URL (должен работать)
    print_header("ТЕСТ 2: НОВЫЙ URL (ОЖИДАЕМ УСПЕХ)")
    new_success, new_error = test_url_connectivity(new_url, "Новый исправленный URL")
    results['new_url'] = (new_success, new_error)
    
    # Тест 3: Запрос пар (если новый URL работает)
    if new_success:
        print_header("ТЕСТ 3: ЗАПРОС ПАР")
        pairs_success = test_pairs_query(new_url)
        results['pairs_query'] = pairs_success
    else:
        print_header("ТЕСТ 3: ПРОПУЩЕН")
        print_warning("Запрос пар пропущен, так как новый URL не работает")
        results['pairs_query'] = False
    
    # Итоговый отчет
    print_header("ИТОГОВЫЙ ОТЧЕТ")
    
    print(f"\n📊 Результаты тестирования:")
    print(f"   🔗 Старый URL: {'❌ Не работает' if not results['old_url'][0] else '⚠️ Неожиданно работает'} ({results['old_url'][1]})")
    print(f"   🔗 Новый URL: {'✅ Работает' if results['new_url'][0] else '❌ Не работает'} ({results['new_url'][1]})")
    print(f"   📈 Запрос пар: {'✅ Работает' if results['pairs_query'] else '❌ Не работает'}")
    
    # Вердикт
    if results['new_url'][0] and results['pairs_query']:
        print_success("\n🎉 ИСПРАВЛЕНИЕ УСПЕШНО! Uniswap V2 субграф работает корректно.")
        print_info("Система готова к использованию исправленного URL.")
        return True
    elif results['new_url'][0] and not results['pairs_query']:
        print_warning("\n⚠️ ЧАСТИЧНЫЙ УСПЕХ: Мета-запросы работают, но есть проблемы с запросом пар.")
        print_info("Возможно, есть дополнительные проблемы с субграфом.")
        return False
    else:
        print_error("\n❌ ИСПРАВЛЕНИЕ НЕ РАБОТАЕТ: Новый URL недоступен.")
        print_info("Нужно дополнительное исследование проблемы.")
        return False

if __name__ == "__main__":
    print(f"\n{Colors.BOLD}🚀 Запуск изолированного теста Uniswap V2 исправления{Colors.END}")
    print(f"{Colors.WHITE}Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
    
    try:
        success = main()
        exit_code = 0 if success else 1
        
        print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
        print(f"{Colors.WHITE}Тест завершен с кодом: {exit_code}{Colors.END}")
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print_error("\n\nТест прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nКритическая ошибка: {e}")
        sys.exit(1)
