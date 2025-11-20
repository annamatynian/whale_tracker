#!/usr/bin/env python3
"""
Диагностика оставшихся ошибок в тестах LP Health Tracker
======================================================

Запускаем конкретные проблемные тесты для выявления точных ошибок.
"""

import subprocess
import sys
import os
import json

def run_failing_tests():
    """Запуск тестов, которые все еще падают."""
    print("🔍 Диагностика оставшихся ошибок тестов...")
    print("=" * 60)
    
    os.chdir("C:\\Users\\annam\\Documents\\DeFi-RAG-Project\\lp_health_tracker")
    
    # Список возможных проблемных тестов на основе статуса
    failing_test_patterns = [
        "tests/test_integration_stage1.py",
        "tests/test_integration_stage2.py", 
        "tests/test_simple_multi_pool_manager.py",
        "research/test_apr_vs_apy",
    ]
    
    for pattern in failing_test_patterns:
        print(f"\n🧪 Тестируем: {pattern}")
        print("-" * 40)
        
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                pattern,
                "-v", "--tb=short", "--maxfail=2"
            ], capture_output=True, text=True, timeout=30)
            
            print(f"Return Code: {result.returncode}")
            
            if result.returncode != 0:
                print("❌ STDERR (ошибки):")
                stderr_lines = result.stderr.split('\n')
                for line in stderr_lines[-20:]:  # Последние 20 строк
                    if line.strip():
                        print(f"  {line}")
                
                print("\n❌ STDOUT (вывод тестов):")
                stdout_lines = result.stdout.split('\n')
                for line in stdout_lines[-30:]:  # Последние 30 строк
                    if line.strip() and ('FAILED' in line or 'ERROR' in line or 'AssertionError' in line):
                        print(f"  {line}")
            else:
                print("✅ Тесты прошли успешно")
                
        except subprocess.TimeoutExpired:
            print("⏰ Тест превысил лимит времени")
        except Exception as e:
            print(f"💥 Ошибка запуска: {e}")

def check_apr_apy_research_files():
    """Проверка файлов исследования APR vs APY."""
    print(f"\n🔬 Проверка исследовательских файлов APR/APY...")
    print("-" * 50)
    
    research_files = [
        "research/test_apr_vs_apy_final.py",
        "research/test_apr_vs_apy_real_data.py"
    ]
    
    for file_path in research_files:
        if os.path.exists(file_path):
            try:
                result = subprocess.run([
                    sys.executable, file_path
                ], capture_output=True, text=True, timeout=15)
                
                print(f"\n📄 {file_path}:")
                print(f"  Return Code: {result.returncode}")
                
                if result.returncode != 0:
                    print("  ❌ Ошибки:")
                    for line in result.stderr.split('\n')[-10:]:
                        if line.strip():
                            print(f"    {line}")
                else:
                    print("  ✅ Файл выполнен успешно")
                    
            except Exception as e:
                print(f"  💥 Ошибка: {e}")
        else:
            print(f"❓ Файл не найден: {file_path}")

def analyze_source_files():
    """Анализ исходных файлов на предмет проблемных параметров."""
    print(f"\n📁 Анализ исходных файлов...")
    print("-" * 40)
    
    src_files = [
        "src/simple_multi_pool.py",
        "src/data_providers.py", 
        "src/net_pnl_calculator.py"
    ]
    
    search_terms = ["initial_investment", "calculate_net_pnl", "APR", "APY"]
    
    for file_path in src_files:
        if os.path.exists(file_path):
            print(f"\n📄 Анализируем {file_path}:")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                for term in search_terms:
                    if term in content:
                        lines = content.split('\n')
                        for i, line in enumerate(lines):
                            if term in line and not line.strip().startswith('#'):
                                print(f"  🎯 Строка {i+1}: {line.strip()}")
                                break
                                
            except Exception as e:
                print(f"  💥 Ошибка чтения: {e}")
        else:
            print(f"❓ Файл не найден: {file_path}")

def main():
    """Главная функция диагностики."""
    print("🩺 ДИАГНОСТИКА ОСТАВШИХСЯ ОШИБОК ТЕСТОВ")
    print("=" * 60)
    print("Цель: Выявить точные причины 4 оставшихся падающих тестов")
    print("=" * 60)
    
    # 1. Запуск проблемных тестов
    run_failing_tests()
    
    # 2. Проверка исследовательских файлов APR/APY
    check_apr_apy_research_files()
    
    # 3. Анализ исходных файлов
    analyze_source_files()
    
    print(f"\n" + "=" * 60)
    print("🎯 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Проанализируйте вывод выше для выявления конкретных ошибок")
    print("2. Найдите строки с 'FAILED', 'AssertionError', 'TypeError'")
    print("3. Исправьте найденные проблемы в тестах или исходном коде")
    print("=" * 60)

if __name__ == "__main__":
    main()
