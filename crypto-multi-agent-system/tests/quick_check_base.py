"""
Быстрая проверка BaseDiscoveryAgent - предварительная диагностика

Минимальный тест для проверки что базовый файл создан корректно
и основные компоненты импортируются

Author: Quick diagnostic check
"""

import sys
import os

# Добавляем пути
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(project_root)

def quick_check():
    """Быстрая проверка основных компонентов"""
    print("⚡ БЫСТРАЯ ПРОВЕРКА BaseDiscoveryAgent")
    print("=" * 40)
    
    # Проверка 1: Файл существует
    base_agent_path = os.path.join(project_root, 'agents', 'discovery', 'base_discovery_agent.py')
    exists = os.path.exists(base_agent_path)
    print(f"📁 Файл существует: {'✅' if exists else '❌'}")
    
    if not exists:
        print("❌ КРИТИЧНО: base_discovery_agent.py не найден")
        return False
    
    # Проверка 2: Размер файла
    size = os.path.getsize(base_agent_path)
    print(f"📏 Размер файла: {size} байт {'✅' if size > 1000 else '⚠️'}")
    
    # Проверка 3: Попытка импорта
    try:
        print("\n🔍 Попытка импорта...")
        
        from agents.discovery.base_discovery_agent import BaseDiscoveryAgent
        print("✅ BaseDiscoveryAgent импортирован")
        
        from agents.discovery.base_discovery_agent import TokenDiscoveryReport
        print("✅ TokenDiscoveryReport импортирован")
        
        from agents.discovery.base_discovery_agent import fetch_pairs_for_chain
        print("✅ fetch_pairs_for_chain импортирован")
        
        from agents.discovery.base_discovery_agent import CHAINS_TO_SCAN
        print("✅ CHAINS_TO_SCAN импортирован")
        
        print(f"🔗 CHAINS_TO_SCAN: {CHAINS_TO_SCAN}")
        
        # Проверка 4: BaseDiscoveryAgent абстрактный
        try:
            instance = BaseDiscoveryAgent()
            print("❌ ОШИБКА: BaseDiscoveryAgent не должен инстанцироваться")
            return False
        except TypeError:
            print("✅ BaseDiscoveryAgent правильно абстрактный")
        
        print("\n🎉 БАЗОВАЯ ПРОВЕРКА ПРОЙДЕНА")
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

if __name__ == "__main__":
    success = quick_check()
    
    if success:
        print("\n🚀 ГОТОВ К ПОЛНОМУ ТЕСТИРОВАНИЮ")
        print("Запустите: python tests/test_base_discovery_agent.py")
    else:
        print("\n🔧 ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ")
        print("Исправьте ошибки перед полным тестированием")
