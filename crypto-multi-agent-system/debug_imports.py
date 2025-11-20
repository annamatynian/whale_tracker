#!/usr/bin/env python3
"""
Debug script to check imports
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

print("🔍 Проверка импортов...")
print("=" * 50)

try:
    print("1. Проверка config.settings...")
    from config.settings import Settings, setup_logging, get_settings
    print("✅ config.settings - OK")
except Exception as e:
    print(f"❌ config.settings - ОШИБКА: {e}")

try:
    print("2. Проверка PumpDiscoveryAgent...")
    from agents.pump_analysis.pump_discovery_agent import PumpDiscoveryAgent
    print("✅ PumpDiscoveryAgent - OK")
except Exception as e:
    print(f"❌ PumpDiscoveryAgent - ОШИБКА: {e}")

try:
    print("3. Проверка CoinGeckoClient...")
    from tools.market_data.coingecko_client import CoinGeckoClient
    print("✅ CoinGeckoClient - OK")
except Exception as e:
    print(f"❌ CoinGeckoClient - ОШИБКА: {e}")

try:
    print("4. Проверка GoPlusClient...")
    from tools.security.goplus_client import GoPlusClient
    print("✅ GoPlusClient - OK")
except Exception as e:
    print(f"❌ GoPlusClient - ОШИБКА: {e}")

try:
    print("5. Проверка RealisticScoringMatrix...")
    from agents.pump_analysis.realistic_scoring import RealisticScoringMatrix, RealisticPumpIndicators, PumpRecommendationMVP
    print("✅ RealisticScoringMatrix - OK")
except Exception as e:
    print(f"❌ RealisticScoringMatrix - ОШИБКА: {e}")

try:
    print("6. Проверка pump_models...")
    from agents.pump_analysis.pump_models import ApiUsageTracker, NarrativeType, PumpAnalysisReport
    print("✅ pump_models - OK")
except Exception as e:
    print(f"❌ pump_models - ОШИБКА: {e}")

try:
    print("7. Проверка narrative_analyzer...")
    from agents.pump_analysis.narrative_analyzer import find_narrative_in_categories
    print("✅ narrative_analyzer - OK")
except Exception as e:
    print(f"❌ narrative_analyzer - ОШИБКА: {e}")

try:
    print("8. Проверка SimpleOrchestrator...")
    from agents.orchestrator.simple_orchestrator import SimpleOrchestrator
    print("✅ SimpleOrchestrator - OK")
except Exception as e:
    print(f"❌ SimpleOrchestrator - ОШИБКА: {e}")

print("\n🔍 Все импорты проверены!")
