#!/usr/bin/env python3
"""
Запуск активированных xfail тестов для PriceStrategyManager
========================================================

Проверяем, что наши активированные тесты действительно работают!
"""

import subprocess
import sys
import os
from pathlib import Path

def run_tests():
    """Запуск тестов PriceStrategyManager."""
    
    # Убедимся, что мы в правильной директории
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    print("🧪 Запуск активированных xfail тестов PriceStrategyManager")
    print("=" * 60)
    print(f"📁 Директория: {project_dir}")
    
    # Команда для запуска только наших тестов
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_future_features.py::TestPriceStrategyManagerFuture",
        "-v",           # Verbose output
        "--tb=short",   # Short traceback format
        "-x",           # Stop on first failure
        "--no-header"   # Skip header
    ]
    
    print(f"🔧 Команда: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        # Запуск тестов
        result = subprocess.run(cmd, 
                              capture_output=True, 
                              text=True, 
                              timeout=30)
        
        print("📤 STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("\n📥 STDERR:")
            print(result.stderr)
        
        print(f"\n🎯 Return code: {result.returncode}")
        
        # Анализ результатов
        if result.returncode == 0:
            print("\n🎉 ВСЕ ТЕСТЫ ПРОШЛИ! Активация xfail тестов УСПЕШНА!")
            return True
        else:
            print(f"\n🚨 ТЕСТЫ НЕ ПРОШЛИ (код: {result.returncode})")
            if "FAILED" in result.stdout:
                print("💡 Некоторые тесты упали - нужно исправить код")
            elif "ImportError" in result.stdout or "ModuleNotFoundError" in result.stdout:
                print("💡 Проблема с импортами - проверьте структуру проекта")
            elif "No tests ran" in result.stdout:
                print("💡 Тесты не найдены - проверьте путь к файлу")
            return False
    
    except subprocess.TimeoutExpired:
        print("⏰ TIMEOUT! Тесты выполняются слишком долго")
        return False
    except Exception as e:
        print(f"💥 ОШИБКА: {e}")
        return False


def check_price_strategy_manager():
    """Быстрая проверка наличия PriceStrategyManager."""
    print("\n🔍 Проверка наличия PriceStrategyManager...")
    
    try:
        from src.price_strategy_manager import PriceStrategyManager
        print("✅ PriceStrategyManager найден")
        
        # Быстрая проверка инициализации  
        manager = PriceStrategyManager(['test_source'])
        print(f"✅ Создание экземпляра: sources = {len(manager.sources)}")
        return True
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка создания: {e}")
        return False


def main():
    """Главная функция."""
    print("🚀 ПРОВЕРКА АКТИВИРОВАННЫХ XFAIL ТЕСТОВ")
    print("=" * 60)
    
    # Сначала быстрая проверка
    if not check_price_strategy_manager():
        print("\n💭 PriceStrategyManager недоступен - тесты точно не пройдут")
        return False
    
    # Затем запуск полных тестов
    success = run_tests()
    
    if success:
        print("\n🎯 ИТОГ: Трансформация xfail → обычные тесты ЗАВЕРШЕНА!")
        print("   Можем переходить к следующим функциям")
    else:
        print("\n🔧 ИТОГ: Нужно исправить код или тесты")
        print("   Сначала исправим проблемы, потом продолжим")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
