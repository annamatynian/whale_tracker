#!/usr/bin/env python3
"""
Простой скрипт для запуска теста унифицированной системы
"""

import subprocess
import sys
import os

def main():
    print("🚀 ЗАПУСК ТЕСТА УНИФИЦИРОВАННОЙ СИСТЕМЫ ЦЕН")
    print("=" * 60)
    
    # Изменяем рабочую директорию
    os.chdir("C:/Users/annam/Documents/DeFi-RAG-Project/lp_health_tracker")
    
    try:
        # Запускаем тест
        result = subprocess.run([
            sys.executable, 
            "test_unified_price_manager.py"
        ], capture_output=True, text=True, timeout=60)
        
        print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print(result.stdout)
        
        if result.stderr:
            print("\n⚠️ STDERR:")
            print(result.stderr)
        
        print(f"\n📋 Return code: {result.returncode}")
        
        if result.returncode == 0:
            print("🎉 ТЕСТ ПРОШЕЛ УСПЕШНО!")
        else:
            print("❌ ТЕСТ НЕ ПРОШЕЛ")
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ ТЕСТ ПРЕВЫСИЛ ЛИМИТ ВРЕМЕНИ (60 секунд)")
        return False
    except Exception as e:
        print(f"❌ ОШИБКА ПРИ ЗАПУСКЕ ТЕСТА: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
