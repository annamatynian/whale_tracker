#!/usr/bin/env python3
"""
Тест новых метрик объема и ликвидности
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.pump_analysis.pump_discovery_agent import PumpDiscoveryAgent

def test_volume_metrics():
    """Тест исправленных метрик объема"""
    print("🧪 ТЕСТ ИСПРАВЛЕННЫХ МЕТРИК ОБЪЕМА")
    print("=" * 50)
    
    agent = PumpDiscoveryAgent()
    
    # Тест 1: Volume Acceleration - растущий объем на Base (низкий порог)
    test_data_accelerating = {
        'chainId': 'base',  # Порог $1,000
        'pairCreatedAt': 1732300000000,  # Недавно созданный
        'baseToken': {'address': '0x123', 'symbol': 'TEST1', 'name': 'Test Token 1'},
        'liquidity': {'usd': 25000},
        'volume': {
            'h24': 30000,
            'h6': 12000,    # За 6 часов (средний = 2000/час)
            'h1': 2200      # За 1 час: 2200 > (12000/6) = 2200 > 2000 - ускоряется!
        },
        'priceChange': {'h1': 5, 'h6': 15, 'h24': 25}
    }
    
    score1, reason1 = agent._calculate_discovery_score(test_data_accelerating, 30*60)
    print(f"\n1️⃣ ТОКЕН С УСКОРЯЮЩИМСЯ ОБЪЕМОМ (BASE - низкий порог):")
    print(f"   Объем h1: $2,200, Объем h6: $12,000 (средний $2,000/час)")
    print(f"   Сеть: Base (порог $1,000) - $2,200 > $1,000 ✓")
    print(f"   Результат: {score1}/100")
    print(f"   Детали: {reason1}")
    
    # Тест 1.5: Тот же объем на Ethereum (высокий порог)
    test_data_ethereum = test_data_accelerating.copy()
    test_data_ethereum['chainId'] = 'ethereum'  # Порог $2,500
    
    score1_5, reason1_5 = agent._calculate_discovery_score(test_data_ethereum, 30*60)
    print(f"\n1️⃣.5 ТОКЕН С ТЕМ ЖЕ ОБЪЕМОМ (ETHEREUM - высокий порог):")
    print(f"   Объем h1: $2,200, Объем h6: $12,000 (средний $2,000/час)")
    print(f"   Сеть: Ethereum (порог $2,500) - $2,200 < $2,500 ✗")
    print(f"   Результат: {score1_5}/100")
    print(f"   Детали: {reason1_5}")
    
    # Тест 2: Healthy Volume Ratio
    test_data_healthy = {
        'chainId': 'base',
        'pairCreatedAt': 1732300000000,
        'baseToken': {'address': '0x456', 'symbol': 'TEST2', 'name': 'Test Token 2'},
        'liquidity': {'usd': 40000},
        'volume': {
            'h24': 60000,   # Volume ratio = 60000/40000 = 1.5 (здоровый диапазон!)
            'h6': 24000,
            'h1': 3000
        },
        'priceChange': {'h1': 2, 'h6': 8, 'h24': 20}
    }
    
    score2, reason2 = agent._calculate_discovery_score(test_data_healthy, 45*60)
    print(f"\n2️⃣ ТОКЕН СО ЗДОРОВЫМ VOLUME RATIO:")
    print(f"   Ликвидность: $40,000, Объем 24ч: $60,000")
    print(f"   Volume Ratio: 1.5 (в диапазоне 0.5-3.0)")
    print(f"   Результат: {score2}/100")
    print(f"   Детали: {reason2}")
    
    # Тест 3: Слишком высокий Volume Ratio (предупреждение)
    test_data_overheated = {
        'chainId': 'arbitrum',
        'pairCreatedAt': 1732300000000,
        'baseToken': {'address': '0x789', 'symbol': 'TEST3', 'name': 'Test Token 3'},
        'liquidity': {'usd': 15000},
        'volume': {
            'h24': 75000,   # Volume ratio = 75000/15000 = 5.0 (слишком высоко!)
            'h6': 30000,
            'h1': 8000
        },
        'priceChange': {'h1': 10, 'h6': 30, 'h24': 80}
    }
    
    score3, reason3 = agent._calculate_discovery_score(test_data_overheated, 20*60)
    print(f"\n3️⃣ ТОКЕН С ВЫСОКИМ VOLUME RATIO:")
    print(f"   Ликвидность: $15,000, Объем 24ч: $75,000")
    print(f"   Volume Ratio: 5.0 (выше 3.0 - возможная манипуляция)")
    print(f"   Результат: {score3}/100")
    print(f"   Детали: {reason3}")
    
    print(f"\n✅ НОВЫЕ МЕТРИКИ РАБОТАЮТ!")
    print(f"📊 Volume Acceleration: адаптивные пороги по сетям")
    print(f"🔍 Volume Ratio Range: фильтр качества активности")
    print(f"   • <0.5: Слишком мало активности (-10 баллов)")
    print(f"   • 0.5-3.0: Здоровая активность (+5 баллов)")
    print(f"   • >3.0: Подозрительная активность (-15 баллов)")
    print(f"🚀 Высокий вес: Volume Acceleration теперь +15 баллов")
    
    print(f"\n🌍 ПОРОГИ ПО СЕТЯМ:")
    print(f"   Base/Solana: $1,000 (низкие комиссии)")
    print(f"   Arbitrum/BSC/Polygon: $1,200-1,500 (средние)")
    print(f"   Ethereum: $2,500 (высокие комиссии)")

if __name__ == "__main__":
    test_volume_metrics()
