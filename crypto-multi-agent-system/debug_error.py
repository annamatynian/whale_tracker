#!/usr/bin/env python3
"""
Debug скрипт для выяснения причины ошибки в main.py
"""
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

print("🔍 ДИАГНОСТИКА ОШИБКИ CRYPTO MULTI-AGENT SYSTEM")
print("=" * 60)

# Проверим импорты по одному
try:
    print("1. Проверка базовой конфигурации...")
    from config.settings import Settings, setup_logging, get_settings
    from config.validation import validate_environment
    print("✅ Базовая конфигурация - OK")
except Exception as e:
    print(f"❌ ОШИБКА в базовой конфигурации: {e}")
    sys.exit(1)

try:
    print("2. Проверка SimpleOrchestrator...")
    from agents.orchestrator.simple_orchestrator import SimpleOrchestrator
    print("✅ SimpleOrchestrator - OK")
except Exception as e:
    print(f"❌ ОШИБКА в SimpleOrchestrator: {e}")

try:
    print("3. Проверка PumpDiscoveryAgent...")
    from agents.pump_analysis.pump_discovery_agent import PumpDiscoveryAgent
    print("✅ PumpDiscoveryAgent - OK")
except Exception as e:
    print(f"❌ ОШИБКА в PumpDiscoveryAgent: {e}")

try:
    print("4. Проверка CoinGeckoClient...")
    from tools.market_data.coingecko_client import CoinGeckoClient
    client = CoinGeckoClient()
    print("✅ CoinGeckoClient - OK")
except Exception as e:
    print(f"❌ ОШИБКА в CoinGeckoClient: {e}")

try:
    print("5. Проверка GoPlusClient...")
    from tools.security.goplus_client import GoPlusClient
    client = GoPlusClient()
    print("✅ GoPlusClient - OK")
except Exception as e:
    print(f"❌ ОШИБКА в GoPlusClient: {e}")

try:
    print("6. Проверка RealisticScoringMatrix...")
    from agents.pump_analysis.realistic_scoring import RealisticScoringMatrix, RealisticPumpIndicators, PumpRecommendationMVP
    print("✅ RealisticScoringMatrix - OK")
except Exception as e:
    print(f"❌ ОШИБКА в RealisticScoringMatrix: {e}")

try:
    print("7. Проверка инициализации Orchestrator...")
    orchestrator = SimpleOrchestrator()
    print("✅ Инициализация Orchestrator - OK")
except Exception as e:
    print(f"❌ ОШИБКА при инициализации Orchestrator: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Диагностика завершена!")
