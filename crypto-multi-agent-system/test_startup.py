#!/usr/bin/env python3
"""
Простая проверка запуска системы после рефакторинга
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

print("🚀 ПРОВЕРКА ЗАПУСКА СИСТЕМЫ ПОСЛЕ РЕФАКТОРИНГА")
print("=" * 60)

try:
    # Проверяем, что можем импортировать main компоненты
    print("📦 Импортируем основные компоненты...")
    
    from agents.orchestrator.simple_orchestrator import SimpleOrchestrator
    print("✅ SimpleOrchestrator импортирован")
    
    from agents.pump_analysis.pump_discovery_agent import PumpDiscoveryAgent  
    print("✅ PumpDiscoveryAgent импортирован")
    
    from agents.pump_analysis.realistic_scoring import RealisticScoringMatrix
    print("✅ RealisticScoringMatrix импортирован")
    
    # Проверяем конфигурацию
    from agents.orchestrator.simple_orchestrator import FUNNEL_CONFIG
    print(f"✅ FUNNEL_CONFIG загружен: {FUNNEL_CONFIG}")
    
    print(f"\n🎯 ПРОВЕРЯЕМ КЛЮЧЕВЫЕ ИЗМЕНЕНИЯ:")
    print(f"   📊 Топ-N для OnChain: {FUNNEL_CONFIG['top_n_for_onchain']}")
    print(f"   🎚️ Минимальный балл алерта: {FUNNEL_CONFIG['min_score_for_alert']}")  
    print(f"   ⚡ Порог API calls: {FUNNEL_CONFIG['api_calls_threshold']}")
    
    print(f"\n✅ ВСЕ ОСНОВНЫЕ КОМПОНЕНТЫ ГОТОВЫ!")
    print(f"🌊 Многоуровневая воронка доступна для использования")
    
    print(f"\n💡 ДЛЯ ПОЛНОГО ТЕСТИРОВАНИЯ ЗАПУСТИТЕ:")
    print(f"   python test_imports_only.py           # Быстрый тест импортов")
    print(f"   python test_refactor_integration.py   # Полный тест логики") 
    print(f"   python main.py --dry-run              # Реальный запуск (требует API ключи)")
    
except ImportError as e:
    print(f"❌ ОШИБКА ИМПОРТА: {e}")
    print(f"🔧 Проверьте структуру проекта и зависимости")
    sys.exit(1)
    
except Exception as e:
    print(f"❌ НЕОЖИДАННАЯ ОШИБКА: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\n🎉 СИСТЕМА ГОТОВА К РАБОТЕ!")
