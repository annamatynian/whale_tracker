#!/usr/bin/env python3
"""
DeFi Llama API - Разведывательный запрос
========================================

Простой скрипт для получения реальных APY данных из DeFi Llama API.
Цель: Сравнить наши mock данные (15% WETH-USDC, 1.5% USDC-USDT) с реальностью.
"""

import requests
import json
from typing import List, Dict

def fetch_defi_llama_pools():
    """Получить все пулы из DeFi Llama API."""
    try:
        print("🌐 Отправляем запрос к DeFi Llama API...")
        url = "https://yields.llama.fi/pools"
        
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        pools = data.get('data', [])
        
        print(f"✅ Получено {len(pools)} пулов от DeFi Llama")
        return pools
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка API запроса: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
        return []

def find_target_pools(pools: List[Dict]) -> Dict:
    """Найти наши целевые пулы в данных."""
    target_pools = {
        'weth_usdc': [],
        'usdc_usdt': [],
        'eth_usdc': [],  # Альтернативные названия
        'all_uniswap': []
    }
    
    print("\n🔍 Ищем наши целевые пулы...")
    
    for pool in pools:
        symbol = pool.get('symbol', '').upper()
        project = pool.get('project', '').lower()
        
        # Собираем все Uniswap пулы для общей статистики
        if 'uniswap' in project:
            target_pools['all_uniswap'].append(pool)
        
        # Ищем WETH-USDC вариации (ТОЛЬКО V2!)
        if any(combo in symbol for combo in ['WETH-USDC', 'ETH-USDC', 'USDC-WETH', 'USDC-ETH']):
            if project == 'uniswap-v2':  # Строгая фильтрация только V2
                target_pools['weth_usdc'].append(pool)
                
        # Ищем ETH-USDC (без W, ТОЛЬКО V2!)
        if any(combo in symbol for combo in ['ETH-USDC', 'USDC-ETH']) and 'WETH' not in symbol:
            if project == 'uniswap-v2':  # Строгая фильтрация только V2
                target_pools['eth_usdc'].append(pool)
        
        # Ищем USDC-USDT вариации (ТОЛЬКО V2!)
        if any(combo in symbol for combo in ['USDC-USDT', 'USDT-USDC']):
            if project == 'uniswap-v2':  # Строгая фильтрация только V2
                target_pools['usdc_usdt'].append(pool)
    
    return target_pools

def analyze_pools(target_pools: Dict):
    """Анализ найденных пулов."""
    print("\n📊 АНАЛИЗ НАЙДЕННЫХ ПУЛОВ")
    print("=" * 50)
    
    # 1. Общая статистика Uniswap
    uniswap_pools = target_pools['all_uniswap']
    if uniswap_pools:
        apys = [pool.get('apy', 0) for pool in uniswap_pools if pool.get('apy') is not None]
        avg_apy = sum(apys) / len(apys) if apys else 0
        
        print(f"📈 Uniswap пулов найдено: {len(uniswap_pools)}")
        print(f"📊 Средний APY Uniswap: {avg_apy:.2f}%")
        print(f"📏 Диапазон APY: {min(apys):.2f}% - {max(apys):.2f}%")
    
    # 2. WETH-USDC анализ
    print(f"\n🎯 WETH-USDC ПУЛЫ (наш mock: 15.0%)")
    print("-" * 40)
    
    weth_usdc_pools = target_pools['weth_usdc'] + target_pools['eth_usdc']
    if weth_usdc_pools:
        for i, pool in enumerate(weth_usdc_pools[:5], 1):  # Показываем топ-5
            apy = pool.get('apy', 0)
            tvl = pool.get('tvlUsd', 0)
            project = pool.get('project', 'unknown')
            symbol = pool.get('symbol', 'unknown')
            
            comparison = ""
            if apy < 10:
                comparison = "🟢 Ниже нашего mock"
            elif apy > 20:
                comparison = "🔴 Выше нашего mock"
            else:
                comparison = "🟡 Близко к нашему mock"
            
            print(f"{i}. {symbol} ({project})")
            print(f"   APY: {apy:.2f}% | TVL: ${tvl:,.0f} | {comparison}")
    else:
        print("❌ WETH-USDC пулы не найдены")
    
    # 3. USDC-USDT анализ
    print(f"\n🎯 USDC-USDT ПУЛЫ (наш mock: 1.5%)")
    print("-" * 40)
    
    usdc_usdt_pools = target_pools['usdc_usdt']
    if usdc_usdt_pools:
        for i, pool in enumerate(usdc_usdt_pools[:5], 1):  # Показываем топ-5
            apy = pool.get('apy', 0)
            tvl = pool.get('tvlUsd', 0)
            project = pool.get('project', 'unknown')
            symbol = pool.get('symbol', 'unknown')
            
            comparison = ""
            if apy < 1:
                comparison = "🟢 Ниже нашего mock"
            elif apy > 2:
                comparison = "🔴 Выше нашего mock"
            else:
                comparison = "🟡 Близко к нашему mock"
            
            print(f"{i}. {symbol} ({project})")
            print(f"   APY: {apy:.2f}% | TVL: ${tvl:,.0f} | {comparison}")
    else:
        print("❌ USDC-USDT пулы не найдены")

def compare_with_mock_data(target_pools: Dict):
    """Сравнение с нашими mock данными."""
    print("\n🎯 СРАВНЕНИЕ С НАШИМИ MOCK ДАННЫМИ")
    print("=" * 50)
    
    # Наши текущие mock данные
    our_mock = {
        'WETH-USDC': 15.0,  # 15% APR из MockDataProvider
        'USDC-USDT': 1.5,   # 1.5% APR из MockDataProvider
    }
    
    # Анализ WETH-USDC
    weth_usdc_pools = target_pools['weth_usdc'] + target_pools['eth_usdc']
    if weth_usdc_pools:
        real_apys = [pool.get('apy', 0) for pool in weth_usdc_pools if pool.get('apy') is not None]
        avg_real_apy = sum(real_apys) / len(real_apys) if real_apys else 0
        
        print(f"📊 WETH-USDC:")
        print(f"   Наш mock: {our_mock['WETH-USDC']:.1f}%")
        print(f"   Реальный средний: {avg_real_apy:.1f}%")
        
        difference = abs(avg_real_apy - our_mock['WETH-USDC'])
        if difference < 2:
            print(f"   🟢 Отличие: {difference:.1f}% (отлично)")
        elif difference < 5:
            print(f"   🟡 Отличие: {difference:.1f}% (приемлемо)")
        else:
            print(f"   🔴 Отличие: {difference:.1f}% (нужна корректировка)")
    
    # Анализ USDC-USDT
    usdc_usdt_pools = target_pools['usdc_usdt']
    if usdc_usdt_pools:
        real_apys = [pool.get('apy', 0) for pool in usdc_usdt_pools if pool.get('apy') is not None]
        avg_real_apy = sum(real_apys) / len(real_apys) if real_apys else 0
        
        print(f"📊 USDC-USDT:")
        print(f"   Наш mock: {our_mock['USDC-USDT']:.1f}%")
        print(f"   Реальный средний: {avg_real_apy:.1f}%")
        
        difference = abs(avg_real_apy - our_mock['USDC-USDT'])
        if difference < 0.5:
            print(f"   🟢 Отличие: {difference:.1f}% (отлично)")
        elif difference < 1:
            print(f"   🟡 Отличие: {difference:.1f}% (приемлемо)")
        else:
            print(f"   🔴 Отличие: {difference:.1f}% (нужна корректировка)")

def show_api_structure_sample(pools: List[Dict]):
    """Показать структуру API response для понимания."""
    print("\n🔍 СТРУКТУРА API RESPONSE (образец)")
    print("=" * 50)
    
    if pools:
        sample_pool = pools[0]
        print("Пример одного пула из API:")
        print(json.dumps(sample_pool, indent=2, ensure_ascii=False)[:500] + "...")
        
        print(f"\nКлючевые поля:")
        print(f"- pool: {sample_pool.get('pool', 'N/A')}")
        print(f"- symbol: {sample_pool.get('symbol', 'N/A')}")
        print(f"- project: {sample_pool.get('project', 'N/A')}")
        print(f"- apy: {sample_pool.get('apy', 'N/A')}")
        print(f"- tvlUsd: {sample_pool.get('tvlUsd', 'N/A')}")

def main():
    """Главная функция разведки."""
    print("🕵️ DeFi LLAMA API - РАЗВЕДЫВАТЕЛЬНАЯ МИССИЯ")
    print("=" * 55)
    print("Цель: Получить реальные APY и сравнить с нашими mock данными")
    print("=" * 55)
    
    # 1. Получаем данные
    pools = fetch_defi_llama_pools()
    
    if not pools:
        print("❌ Не удалось получить данные. Проверьте подключение к интернету.")
        return
    
    # 2. Показываем структуру API
    show_api_structure_sample(pools)
    
    # 3. Ищем наши пулы
    target_pools = find_target_pools(pools)
    
    # 4. Анализируем
    analyze_pools(target_pools)
    
    # 5. Сравниваем с mock
    compare_with_mock_data(target_pools)
    
    print("\n" + "=" * 55)
    print("🎯 ЗАКЛЮЧЕНИЕ РАЗВЕДКИ:")
    print("Теперь мы знаем реальные APY и можем принять обоснованное решение")
    print("о корректировке наших mock данных или подтверждении текущего подхода.")
    print("=" * 55)

if __name__ == "__main__":
    main()
