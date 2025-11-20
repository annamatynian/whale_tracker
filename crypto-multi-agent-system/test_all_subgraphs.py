#!/usr/bin/env python3
"""
РАСШИРЕННЫЙ ТЕСТ: Проверка ВСЕХ субграфов The Graph
=================================================

Тестирует все настроенные субграфы для поиска работающих альтернатив
вместо ожидания восстановления Uniswap V2.

Субграфы для тестирования:
1. Uniswap V2 (проблемный)
2. SushiSwap (форк V2, может работать)  
3. Uniswap V3 (может иметь больше токенов)
4. PancakeSwap V2 (BSC, может быть стабильнее)

Цель: Найти работающие источники данных для токенов возрастом 30-90 дней
"""

import os
import sys
import requests
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

class Colors:
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
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.END}")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")

# Конфигурация субграфов
SUBGRAPHS = {
    "Uniswap V2": {
        "id": os.getenv("UNISWAP_V2_ID"),
        "type": "pairs",  # V2 использует pairs
        "chain": "Ethereum",
        "description": "Основной источник (проблемный)"
    },
    "SushiSwap": {
        "id": os.getenv("SUSHISWAP_ID"), 
        "type": "pairs",  # Форк V2, использует pairs
        "chain": "Ethereum",
        "description": "Форк Uniswap V2 (потенциальная замена)"
    },
    "Uniswap V3": {
        "id": os.getenv("UNISWAP_V3_ID"),
        "type": "pools",  # V3 использует pools
        "chain": "Ethereum", 
        "description": "Новая версия с pools"
    },
    "PancakeSwap V2": {
        "id": os.getenv("PANCAKESWAP_V2_ID"),
        "type": "pairs",  # Форк V2, использует pairs
        "chain": "BSC",
        "description": "BSC форк V2 (может быть стабильнее)"
    }
}

def build_url(subgraph_id):
    """Строит URL для субграфа."""
    api_key = os.getenv("GRAPH_API_KEY")
    return f"https://gateway.thegraph.com/api/{api_key}/subgraphs/id/{subgraph_id}"

def build_meta_query():
    """Простой мета-запрос для проверки доступности."""
    return """
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

def build_historical_pairs_query():
    """Запрос пар возрастом 30-90 дней для V2-style субграфов."""
    # Вычисляем timestamp для 30-90 дней назад
    now = datetime.now()
    start_date = now - timedelta(days=90)  # 90 дней назад
    end_date = now - timedelta(days=30)    # 30 дней назад
    
    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())
    
    return f"""
    query {{
      pairs(
        where: {{ 
          createdAtTimestamp_gte: {start_timestamp},
          createdAtTimestamp_lte: {end_timestamp},
          reserveUSD_gte: "1000"
        }}
        first: 5
        orderBy: createdAtTimestamp
        orderDirection: desc
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
      }}
    }}
    """

def build_historical_pools_query():
    """Запрос pools возрастом 30-90 дней для V3-style субграфов."""
    now = datetime.now()
    start_date = now - timedelta(days=90)
    end_date = now - timedelta(days=30)
    
    start_timestamp = int(start_date.timestamp())
    end_timestamp = int(end_date.timestamp())
    
    return f"""
    query {{
      pools(
        where: {{ 
          createdAtTimestamp_gte: {start_timestamp},
          createdAtTimestamp_lte: {end_timestamp},
          totalValueLockedUSD_gte: "1000"
        }}
        first: 5
        orderBy: createdAtTimestamp
        orderDirection: desc
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
        totalValueLockedUSD
        volumeUSD
        feeTier
      }}
    }}
    """

def test_subgraph(name, config):
    """Тестирует один субграф."""
    print(f"\n{Colors.PURPLE}🧪 Тестируем: {name}{Colors.END}")
    print(f"   Chain: {config['chain']}")
    print(f"   Type: {config['type']}")
    print(f"   Description: {config['description']}")
    
    if not config['id']:
        print_error("Subgraph ID не настроен в .env")
        return False, "No ID configured"
    
    url = build_url(config['id'])
    print(f"   ID: {config['id']}")
    
    # Тест 1: Мета-запрос
    meta_query = build_meta_query()
    
    try:
        start_time = time.time()
        response = requests.post(
            url,
            json={"query": meta_query},
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        response_time = (time.time() - start_time) * 1000
        
        print(f"   📊 Meta Query - Status: {response.status_code}, Time: {response_time:.1f}ms")
        
        if response.status_code != 200:
            print_error(f"HTTP Error: {response.status_code}")
            return False, f"HTTP {response.status_code}"
        
        data = response.json()
        
        if 'errors' in data:
            print_error("GraphQL Errors:")
            for error in data['errors']:
                print(f"      - {error.get('message', 'Unknown error')}")
            return False, f"GraphQL errors: {len(data['errors'])} errors"
        
        if 'data' in data and '_meta' in data['data']:
            meta = data['data']['_meta']
            print_success("Meta query успешен!")
            print(f"      🎯 Block: {meta['block']['number']}")
            print(f"      🎯 Deployment: {meta['deployment']}")
            print(f"      🎯 Indexing Errors: {meta['hasIndexingErrors']}")
            
            # Тест 2: Исторический запрос (30-90 дней)
            print(f"   🔍 Testing historical data (30-90 days ago)...")
            
            if config['type'] == 'pairs':
                historical_query = build_historical_pairs_query()
            else:  # pools
                historical_query = build_historical_pools_query()
            
            hist_response = requests.post(
                url,
                json={"query": historical_query},
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            
            if hist_response.status_code == 200:
                hist_data = hist_response.json()
                
                if 'errors' in hist_data:
                    print_error("Errors in historical query:")
                    for error in hist_data['errors']:
                        print(f"         - {error.get('message', 'Unknown error')}")
                    return True, "Meta OK, Historical FAILED"
                
                # Проверяем данные
                data_key = 'pairs' if config['type'] == 'pairs' else 'pools'
                if 'data' in hist_data and data_key in hist_data['data']:
                    items = hist_data['data'][data_key]
                    print_success(f"Historical data: {len(items)} {data_key} found (30-90 days old)")
                    
                    if items:
                        print("      📈 Examples:")
                        for i, item in enumerate(items[:2]):  # Показываем первые 2
                            symbol0 = item['token0']['symbol'] or 'Unknown'
                            symbol1 = item['token1']['symbol'] or 'Unknown'
                            timestamp = int(item['createdAtTimestamp'])
                            created_date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                            
                            if config['type'] == 'pairs':
                                reserve = float(item.get('reserveUSD', 0))
                                print(f"         {i+1}. {symbol0}/{symbol1} - ${reserve:,.0f} (created {created_date})")
                            else:  # pools
                                tvl = float(item.get('totalValueLockedUSD', 0))
                                fee_tier = item.get('feeTier', 0)
                                print(f"         {i+1}. {symbol0}/{symbol1} - ${tvl:,.0f}, Fee: {fee_tier} (created {created_date})")
                        
                        return True, "FULLY WORKING"
                    else:
                        print_warning("No historical data found in 30-90 day range")
                        return True, "Meta OK, No historical data"
                else:
                    print_error("Unexpected response structure in historical query")
                    return True, "Meta OK, Historical structure error"
            else:
                print_error(f"Historical query HTTP error: {hist_response.status_code}")
                return True, "Meta OK, Historical HTTP error"
        else:
            print_error("Unexpected meta response structure")
            return False, "Invalid meta structure"
            
    except requests.exceptions.Timeout:
        print_error("Timeout")
        return False, "Timeout"
    except requests.exceptions.ConnectionError:
        print_error("Connection Error")
        return False, "Connection Error"
    except Exception as e:
        print_error(f"Unexpected Error: {e}")
        return False, str(e)

def main():
    """Основная функция."""
    print_header("ТЕСТ ВСЕХ СУБГРАФОВ THE GRAPH")
    
    api_key = os.getenv("GRAPH_API_KEY")
    if not api_key:
        print_error("GRAPH_API_KEY не найден в .env")
        return False
    
    print_info(f"API Key: {api_key}")
    print_info("Цель: Найти работающие источники для токенов возрастом 30-90 дней")
    
    results = {}
    working_subgraphs = []
    
    # Тестируем все субграфы
    for name, config in SUBGRAPHS.items():
        success, status = test_subgraph(name, config)
        results[name] = (success, status)
        
        if success and "FULLY WORKING" in status:
            working_subgraphs.append(name)
    
    # Итоговый отчет
    print_header("ИТОГОВЫЙ ОТЧЕТ")
    
    print(f"\n📊 Результаты тестирования:")
    for name, (success, status) in results.items():
        if success and "FULLY WORKING" in status:
            print_success(f"{name}: {status}")
        elif success:
            print_warning(f"{name}: {status}")
        else:
            print_error(f"{name}: {status}")
    
    # Рекомендации
    if working_subgraphs:
        print_success(f"\n🎉 НАЙДЕНО {len(working_subgraphs)} РАБОТАЮЩИХ СУБГРАФОВ!")
        print_info("Рекомендации по использованию:")
        
        for subgraph in working_subgraphs:
            config = SUBGRAPHS[subgraph]
            print(f"   ✅ {subgraph} ({config['chain']}, {config['type']})")
        
        print_info("\n💡 Следующие шаги:")
        print("   1. Обновить конфигурацию для использования работающих субграфов")
        print("   2. Временно отключить проблемные субграфы")
        print("   3. Протестировать полный discovery pipeline")
        
        return True
    else:
        print_error("\n❌ НИ ОДИН СУБГРАФ НЕ РАБОТАЕТ ПОЛНОСТЬЮ")
        print_info("Возможные решения:")
        print("   1. Подождать восстановления индексеров")
        print("   2. Рассмотреть прямое взаимодействие с блокчейном")
        print("   3. Изучить альтернативные источники данных")
        
        return False

if __name__ == "__main__":
    print(f"\n{Colors.BOLD}🚀 Запуск теста всех субграфов{Colors.END}")
    print(f"{Colors.WHITE}Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}")
    
    try:
        success = main()
        exit_code = 0 if success else 1
        
        print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
        print(f"{Colors.WHITE}Тест завершен с кодом: {exit_code}{Colors.END}")
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print_error("\n\nТест прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nКритическая ошибка: {e}")
        sys.exit(1)
