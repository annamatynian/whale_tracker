#!/usr/bin/env python3
"""
Простая проверка PriceStrategyManager
==================================
"""

import sys
import os
from pathlib import Path

# Добавляем путь к проекту
project_dir = Path(__file__).parent
src_dir = project_dir / "src"
sys.path.insert(0, str(src_dir))

def test_import():
    """Проверка импорта."""
    try:
        from price_strategy_manager import PriceStrategyManager
        print("✅ PriceStrategyManager успешно импортирован")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False

def test_basic_creation():
    """Проверка создания объекта."""
    try:
        from price_strategy_manager import PriceStrategyManager
        
        # Тестируем конструктор как в наших тестах
        manager = PriceStrategyManager(['test_source'])
        print(f"✅ Менеджер создан с {len(manager.sources)} источниками")
        
        # Проверим основные атрибуты
        if hasattr(manager, 'sources'):
            print(f"✅ Атрибут sources: {manager.sources}")
        if hasattr(manager, 'cache_hits'):
            print(f"✅ Атрибут cache_hits: {manager.cache_hits}")
        if hasattr(manager, 'last_used_source'):
            print(f"✅ Атрибут last_used_source: {manager.last_used_source}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка создания: {e}")
        return False

def test_basic_functionality():
    """Проверка основного функционала."""
    try:
        from price_strategy_manager import PriceStrategyManager
        
        # Используем тестовые источники как в наших тестах
        manager = PriceStrategyManager(['working_source'])
        
        # Попробуем получить цену
        price = manager.get_token_price('ETH')
        print(f"✅ Получена цена ETH: {price}")
        
        if price == 2000.0:  # Ожидаемая тестовая цена
            print("✅ Цена соответствует ожидаемой (2000.0)")
            return True
        else:
            print(f"⚠️ Цена {price} не соответствует ожидаемой 2000.0")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка получения цены: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔍 БЫСТРАЯ ПРОВЕРКА PriceStrategyManager")
    print("=" * 50)
    
    tests = [
        ("Импорт", test_import),
        ("Создание объекта", test_basic_creation),  
        ("Основной функционал", test_basic_functionality)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n📋 {name}:")
        success = test_func()
        results.append(success)
        print()
    
    passed = sum(results)
    total = len(results)
    
    print("=" * 50)
    print(f"📊 РЕЗУЛЬТАТ: {passed}/{total} тестов прошли")
    
    if passed == total:
        print("🎉 ВСЕ ПРОВЕРКИ ПРОШЛИ!")
        print("🧪 Можно запускать полные pytest тесты")
        return True
    else:
        print("🚨 ЕСТЬ ПРОБЛЕМЫ - нужно исправить перед pytest")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
