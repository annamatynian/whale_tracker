#!/usr/bin/env python3
"""
Быстрый тест основных компонентов
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

print("🔍 Тестирование основных компонентов...")
print("=" * 50)

try:
    print("1. Тестирование RealisticScoringMatrix...")
    from agents.pump_analysis.realistic_scoring import RealisticScoringMatrix, RealisticPumpIndicators, PumpRecommendationMVP
    from agents.pump_analysis.pump_models import NarrativeType
    
    # Создаем тестовые индикаторы
    test_indicators = RealisticPumpIndicators(
        narrative_type=NarrativeType.AI,
        has_trending_narrative=True,
        coingecko_score=75.0,
        is_honeypot=False,
        is_open_source=True,
        buy_tax_percent=5.0,
        sell_tax_percent=8.0
    )
    
    # Создаем scoring matrix
    matrix = RealisticScoringMatrix(indicators=test_indicators)
    analysis = matrix.get_detailed_analysis()
    
    print(f"   ✅ Score: {analysis['total_score']}/100")
    print(f"   ✅ Recommendation: {analysis['recommendation']}")
    
except Exception as e:
    print(f"   ❌ ОШИБКА: {e}")

try:
    print("2. Тестирование CoinGecko и GoPlus клиентов...")
    from tools.market_data.coingecko_client import CoinGeckoClient
    from tools.security.goplus_client import GoPlusClient
    
    coingecko = CoinGeckoClient()
    goplus = GoPlusClient()
    
    print("   ✅ Клиенты созданы успешно")
    
except Exception as e:
    print(f"   ❌ ОШИБКА: {e}")

try:
    print("3. Тестирование SimpleOrchestrator...")
    from agents.orchestrator.simple_orchestrator import SimpleOrchestrator
    
    orchestrator = SimpleOrchestrator()
    print("   ✅ Оркестратор инициализирован")
    
except Exception as e:
    print(f"   ❌ ОШИБКА: {e}")

print("\n🎯 Все основные компоненты протестированы!")
print("Если нет ошибок выше, система готова к запуску.")
