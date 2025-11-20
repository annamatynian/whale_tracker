#!/usr/bin/env python3
"""
DeFi Llama API - Разведка ТОЛЬКО Uniswap V2 пулов
=================================================

ИСПРАВЛЕННАЯ версия разведки, которая фильтрует ТОЛЬКО Uniswap V2 пулы,
поскольку наш LP Health Tracker архитектурно построен именно для V2.

КРИТИЧЕСКОЕ ОТЛИЧИЕ V2 vs V3:
- V2: Постоянное произведение (x*y=k), равномерная ликвидность, наши формулы IL
- V3: Concentrated liquidity, price ranges, NFT позиции, другая математика

Цель: Получить корректные APY данные для нашей V2-архитектуры.
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

def filter_uniswap_v2_pools(pools: List[Dict]) -> List[Dict]:
    """Фильтровать ТОЛЬКО Uniswap V2 пулы."""
    v2_pools = []
    
    for pool in pools:
        project = pool.get('project', '').lower()
        
        # Фильтруем только Uniswap V2
        if project == 'uniswap-v2':
            v2_pools.append(pool)
    
    return v2_pools

def find_target_v2_pools(v2_pools: List[Dict]) -> Dict:
    """Найти наши целевые пулы в V2 данных."""
    target_pools = {
        'weth_usdc_v2': [],
        'usdc_usdt_v2': [],
        'all_v2': v2_pools
    }
    
    print("\n🔍 Ищем наши целевые пулы в UNISWAP V2...")
    
    for pool in v2_pools:
        symbol = pool.get('symbol', '').upper()
        
        # Ищем WETH-USDC вариации в V2
        if any(combo in symbol for combo in ['WETH-USDC', 'ETH-USDC', 'USDC-WETH', 'USDC-ETH']):
            target_pools['weth_usdc_v2'].append(pool)
                
        # Ищем USDC-USDT вариации в V2
        if any(combo in symbol for combo in ['USDC-USDT', 'USDT-USDC']):
            target_pools['usdc_usdt_v2'].append(pool)
    
    return target_pools

def analyze_v2_pools(target_pools: Dict):
    """Анализ найденных V2 пулов."""
    print("\n📊 АНАЛИЗ UNISWAP V2 ПУЛОВ")
    print("=" * 50)
    
    # 1. Общая статистика V2
    v2_pools = target_pools['all_v2']
    if v2_pools:
        apys = [pool.get('apy', 0) for pool in v2_pools if pool.get('apy') is not None]
        avg_apy = sum(apys) / len(apys) if apys else 0
        
        print(f"📈 Uniswap V2 пулов найдено: {len(v2_pools)}")
        print(f"📊 Средний APY V2: {avg_apy:.2f}%")
        print(f"📏 Диапазон APY V2: {min(apys):.2f}% - {max(apys):.2f}%")
    
    # 2. WETH-USDC V2 анализ
    print(f"\n🎯 WETH-USDC V2 ПУЛЫ (наш mock: 15.0%)")
    print("-" * 40)
    
    weth_usdc_v2 = target_pools['weth_usdc_v2']
    if weth_usdc_v2:
        for i, pool in enumerate(weth_usdc_v2[:5], 1):
            apy = pool.get('apy', 0)
            tvl = pool.get('tvlUsd', 0)
            symbol = pool.get('symbol', 'unknown')
            
            comparison = ""
            if apy < 10:
                comparison = "🟢 Ниже нашего mock"
            elif apy > 20:
                comparison = "🔴 Выше нашего mock"
            else:
                comparison = "🟡 Близко к нашему mock"
            
            print(f"{i}. {symbol} (uniswap-v2)")
            print(f"   APY: {apy:.2f}% | TVL: ${tvl:,.0f} | {comparison}")
    else:
        print("❌ WETH-USDC V2 пулы не найдены")
    
    # 3. USDC-USDT V2 анализ
    print(f"\n🎯 USDC-USDT V2 ПУЛЫ (наш mock: 1.5%)")
    print("-" * 40)
    
    usdc_usdt_v2 = target_pools['usdc_usdt_v2']
    if usdc_usdt_v2:
        for i, pool in enumerate(usdc_usdt_v2[:5], 1):
            apy = pool.get('apy', 0)
            tvl = pool.get('tvlUsd', 0)
            symbol = pool.get('symbol', 'unknown')
            
            comparison = ""
            if apy < 1:
                comparison = "🟢 Ниже нашего mock"
            elif apy > 2:
                comparison = "🔴 Выше нашего mock"
            else:
                comparison = "🟡 Близко к нашему mock"
            
            print(f"{i}. {symbol} (uniswap-v2)")
            print(f"   APY: {apy:.2f}% | TVL: ${tvl:,.0f} | {comparison}")
    else:
        print("❌ USDC-USDT V2 пулы не найдены")

def compare_v2_with_mock_data(target_pools: Dict):
    """Сравнение V2 данных с нашими mock."""
    print("\n🎯 СРАВНЕНИЕ V2 ДАННЫХ С НАШИМИ MOCK")
    print("=" * 50)
    
    # Наши mock данные
    our_mock = {
        'WETH-USDC': 15.0,
        'USDC-USDT': 1.5,
    }
    
    # Анализ WETH-USDC V2
    weth_usdc_v2 = target_pools['weth_usdc_v2']
    if weth_usdc_v2:
        real_apys = [pool.get('apy', 0) for pool in weth_usdc_v2 if pool.get('apy') is not None]
        avg_real_apy = sum(real_apys) / len(real_apys) if real_apys else 0
        
        print(f"📊 WETH-USDC V2:")
        print(f"   Наш mock: {our_mock['WETH-USDC']:.1f}%")
        print(f"   Реальный V2 средний: {avg_real_apy:.1f}%")
        
        difference = abs(avg_real_apy - our_mock['WETH-USDC'])
        if difference < 2:
            print(f"   🟢 Отличие: {difference:.1f}% (отлично)")
        elif difference < 5:
            print(f"   🟡 Отличие: {difference:.1f}% (приемлемо)")
        else:
            print(f"   🔴 Отличие: {difference:.1f}% (ТРЕБУЕТ КОРРЕКТИРОВКИ)")
            print(f"   💡 Рекомендация: Обновить mock с 15% на {avg_real_apy:.1f}%")
    
    # Анализ USDC-USDT V2
    usdc_usdt_v2 = target_pools['usdc_usdt_v2']
    if usdc_usdt_v2:
        real_apys = [pool.get('apy', 0) for pool in usdc_usdt_v2 if pool.get('apy') is not None]
        avg_real_apy = sum(real_apys) / len(real_apys) if real_apys else 0
        
        print(f"\n📊 USDC-USDT V2:")
        print(f"   Наш mock: {our_mock['USDC-USDT']:.1f}%")
        print(f"   Реальный V2 средний: {avg_real_apy:.1f}%")
        
        difference = abs(avg_real_apy - our_mock['USDC-USDT'])
        if difference < 0.5:
            print(f"   🟢 Отличие: {difference:.1f}% (отлично)")
        elif difference < 1:
            print(f"   🟡 Отличие: {difference:.1f}% (приемлемо)")
        else:
            print(f"   🔴 Отличие: {difference:.1f}% (ТРЕБУЕТ КОРРЕКТИРОВКИ)")
            print(f"   💡 Рекомендация: Обновить mock с 1.5% на {avg_real_apy:.1f}%")

def show_v2_vs_v3_comparison(all_pools: List[Dict]):
    """Показать почему важно разделять V2 и V3."""
    print("\n⚠️  ПОЧЕМУ V2 vs V3 КРИТИЧНО ВАЖНО")
    print("=" * 50)
    
    v2_pools = [p for p in all_pools if p.get('project') == 'uniswap-v2']
    v3_pools = [p for p in all_pools if p.get('project') == 'uniswap-v3']
    
    if v2_pools and v3_pools:
        v2_apys = [p.get('apy', 0) for p in v2_pools if p.get('apy') is not None]
        v3_apys = [p.get('apy', 0) for p in v3_pools if p.get('apy') is not None]
        
        v2_avg = sum(v2_apys) / len(v2_apys) if v2_apys else 0
        v3_avg = sum(v3_apys) / len(v3_apys) if v3_apys else 0
        
        print(f"🏗️ АРХИТЕКТУРНЫЕ ОТЛИЧИЯ:")
        print(f"   V2 пулов: {len(v2_pools)} | Средний APY: {v2_avg:.2f}%")
        print(f"   V3 пулов: {len(v3_pools)} | Средний APY: {v3_avg:.2f}%")
        print(f"   Разница в APY: {abs(v3_avg - v2_avg):.2f}%")
        
        print(f"\n🎯 НАШ ПРОЕКТ (V2):")
        print(f"   - AMM: x * y = k")
        print(f"   - LP токены: ERC-20")
        print(f"   - IL формула: Стандартная")
        print(f"   - Ликвидность: Равномерная по всему диапазону")
        
        print(f"\n⚡ UNISWAP V3 (НЕ НАША АРХИТЕКТУРА):")
        print(f"   - AMM: Concentrated liquidity")
        print(f"   - LP позиции: NFT")
        print(f"   - IL формула: Совершенно другая")
        print(f"   - Ликвидность: В узких диапазонах цен")

def main():
    """Главная функция исправленной разведки."""
    print("🕵️ DeFi LLAMA - РАЗВЕДКА ТОЛЬКО UNISWAP V2")
    print("=" * 55)
    print("⚠️  ИСПРАВЛЕННАЯ ВЕРСИЯ: Фильтруем ТОЛЬКО V2 пулы!")
    print("Причина: Наш LP Health Tracker архитектурно построен для V2")
    print("=" * 55)
    
    # 1. Получаем все данные
    all_pools = fetch_defi_llama_pools()
    
    if not all_pools:
        print("❌ Не удалось получить данные")
        return
    
    # 2. Фильтруем только V2
    v2_pools = filter_uniswap_v2_pools(all_pools)
    print(f"\n✅ Отфильтровано {len(v2_pools)} Uniswap V2 пулов")
    
    # 3. Показываем важность разделения V2/V3
    show_v2_vs_v3_comparison(all_pools)
    
    # 4. Ищем наши пулы в V2
    target_pools = find_target_v2_pools(v2_pools)
    
    # 5. Анализируем V2 пулы
    analyze_v2_pools(target_pools)
    
    # 6. Сравниваем с mock
    compare_v2_with_mock_data(target_pools)
    
    print("\n" + "=" * 55)
    print("🎯 ЗАКЛЮЧЕНИЕ V2 РАЗВЕДКИ:")
    print("Получили КОРРЕКТНЫЕ APY данные для нашей V2-архитектуры.")
    print("Теперь можем принять обоснованное решение о mock данных.")
    print("=" * 55)

if __name__ == "__main__":
    main()
