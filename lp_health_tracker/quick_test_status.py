#!/usr/bin/env python3
"""
Быстрая проверка статуса и конкретных ошибок
===========================================
"""

import subprocess
import sys
import os

def quick_status_check():
    """Быстрая проверка текущего статуса тестов."""
    print("⚡ БЫСТРАЯ ПРОВЕРКА СТАТУСА ТЕСТОВ")
    print("=" * 45)
    
    os.chdir("C:\\Users\\annam\\Documents\\DeFi-RAG-Project\\lp_health_tracker")
    
    try:
        # Запуск всех тестов с кратким выводом
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", "-x", "--tb=no", "-q", "--disable-warnings"
        ], capture_output=True, text=True, timeout=60)
        
        print(f"Return Code: {result.returncode}")
        print("\nВывод тестов:")
        print(result.stdout)
        
        if result.stderr:
            print("\nОшибки:")
            print(result.stderr)
            
        # Подсчет результатов
        output = result.stdout
        if "failed" in output:
            parts = output.split()
            for i, part in enumerate(parts):
                if "failed" in part or "passed" in part:
                    print(f"\n📊 Статус: {' '.join(parts[max(0, i-2):i+3])}")
                    break
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def check_specific_failing_tests():
    """Проверка конкретных падающих тестов."""
    print(f"\n🎯 ПРОВЕРКА КОНКРЕТНЫХ ПРОБЛЕМНЫХ ТЕСТОВ")
    print("=" * 45)
    
    # На основе предыдущего статуса, проверим конкретные тесты
    specific_tests = [
        "tests/test_integration_stage1.py::TestStage1DataProviderIntegration::test_mock_data_provider_apr_values",
        "tests/test_integration_stage1.py::TestStage1NetPnLCalculation::test_calculate_net_pnl_comprehensive"
    ]
    
    for test in specific_tests:
        print(f"\n🧪 Тестируем: {test}")
        print("-" * 40)
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                test, "-v", "--tb=short"
            ], capture_output=True, text=True, timeout=30)
            
            print(f"Код: {result.returncode}")
            
            if result.returncode != 0:
                print("❌ Подробности ошибки:")
                lines = result.stdout.split('\n')
                for line in lines:
                    if any(keyword in line for keyword in ['FAILED', 'AssertionError', 'TypeError', 'Expected', 'Got']):
                        print(f"  {line}")
                        
                # Дополнительно stderr
                if result.stderr:
                    error_lines = result.stderr.split('\n')
                    for line in error_lines[-5:]:
                        if line.strip():
                            print(f"  ERR: {line}")
            else:
                print("✅ Тест прошел")
                
        except Exception as e:
            print(f"💥 Ошибка запуска: {e}")

if __name__ == "__main__":
    quick_status_check()
    check_specific_failing_tests()
    
    print(f"\n" + "=" * 45) 
    print("Если видите конкретные ошибки выше, можно их исправить")
    print("=" * 45)
