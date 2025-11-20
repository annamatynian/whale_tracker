"""
Быстрая проверка импортов - найти ошибки без полного тестирования
"""

import sys
import os

# Добавляем путь к корню проекта
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
print(f"Добавлен путь: {project_root}")

print("🔍 БЫСТРАЯ ПРОВЕРКА ИМПОРТОВ")
print("=" * 40)

# Проверяем каждый модуль отдельно
modules_to_test = [
    ("base_discovery_agent", "agents.discovery.base_discovery_agent"),
    ("pump_models", "agents.pump_analysis.pump_models"),
    ("realistic_scoring", "agents.pump_analysis.realistic_scoring"),
    # ("enhanced_discovery", "agents.pump_analysis.enhanced_discovery"), # Архивирован
    ("pump_discovery_agent", "agents.pump_analysis.pump_discovery_agent")
]

errors_found = []

for name, module_path in modules_to_test:
    try:
        print(f"Проверяем {name}...")
        __import__(module_path)
        print(f"✅ {name} - OK")
    except ImportError as e:
        error_msg = f"❌ {name} - ImportError: {e}"
        print(error_msg)
        errors_found.append(error_msg)
    except Exception as e:
        error_msg = f"❌ {name} - Error: {e}"
        print(error_msg)
        errors_found.append(error_msg)

print(f"\n📊 РЕЗУЛЬТАТ:")
if not errors_found:
    print("🎉 Все импорты работают!")
else:
    print("⚠️  Найдены ошибки:")
    for error in errors_found:
        print(f"   {error}")

print("\n🔧 Следующий шаг:")
if not errors_found:
    print("   Можно запускать полные тесты")
else:
    print("   Нужно исправить ошибки импортов")
