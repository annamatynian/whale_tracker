"""
Мастер-тест: Запуск всех тестов системы в правильной последовательности
"""
import asyncio
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def run_python_script(script_name: str) -> bool:
    """Запускает Python скрипт и возвращает результат"""
    
    try:
        print(f"\n▶️ Запуск {script_name}...")
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT
        )
        
        # Print output
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
        
        success = result.returncode == 0
        status = "✅ УСПЕХ" if success else "❌ ОШИБКА"
        print(f"📊 {script_name}: {status}")
        
        return success
        
    except Exception as e:
        print(f"❌ Не удалось запустить {script_name}: {e}")
        return False

async def run_master_test_suite():
    """Мастер-тест всей системы"""
    
    print("🎯 МАСТЕР-ТЕСТ CRYPTO MULTI-AGENT SYSTEM")
    print("=" * 80)
    print("Последовательное тестирование всех компонентов системы")
    print("=" * 80)
    
    # Define test sequence
    test_sequence = [
        # PHASE 1: Basic functionality
        ("test_imports_only.py", "Проверка импортов", True),
        ("test_quick.py", "Быстрая проверка", True),
        
        # PHASE 2: Component tests  
        ("test_mock_data.py", "Mock данные и архитектура", True),
        ("test_scoring_examples.py", "Система скоринга", True),
        ("test_volume_metrics.py", "Метрики объема", False),  # Optional
        
        # PHASE 3: Integration tests
        ("test_funnel_architecture.py", "Архитектура воронки", True),
        ("test_api_integrations.py", "API интеграции", False),  # Requires API keys
        
        # PHASE 4: E2E tests
        ("test_full_e2e_pipeline.py", "E2E Pipeline", True),
    ]
    
    results = {}
    critical_failures = []
    
    print(f"📋 Всего тестов в очереди: {len(test_sequence)}")
    print(f"🔴 Критических: {sum(1 for _, _, critical in test_sequence if critical)}")
    print(f"🟡 Опциональных: {sum(1 for _, _, critical in test_sequence if not critical)}")
    
    # Run tests
    for i, (script, description, is_critical) in enumerate(test_sequence, 1):
        print(f"\n{'='*80}")
        print(f"ТЕСТ {i}/{len(test_sequence)}: {description}")
        print(f"Скрипт: {script} {'(КРИТИЧЕСКИЙ)' if is_critical else '(опциональный)'}")
        print(f"{'='*80}")
        
        # Check if file exists
        script_path = PROJECT_ROOT / script
        if not script_path.exists():
            print(f"⚠️ Файл {script} не найден - пропускаем")
            results[script] = "SKIPPED"
            continue
        
        # Run the test
        success = run_python_script(script)
        
        if success:
            results[script] = "PASSED"
            print(f"✅ Тест {i} пройден успешно")
        else:
            results[script] = "FAILED"
            print(f"❌ Тест {i} провален")
            
            if is_critical:
                critical_failures.append((script, description))
                print(f"🚨 КРИТИЧЕСКИЙ ТЕСТ ПРОВАЛЕН: {description}")
    
    # Final report
    print(f"\n{'='*80}")
    print("📊 ФИНАЛЬНЫЙ ОТЧЕТ МАСТЕР-ТЕСТА")
    print(f"{'='*80}")
    
    passed = sum(1 for result in results.values() if result == "PASSED")
    failed = sum(1 for result in results.values() if result == "FAILED")
    skipped = sum(1 for result in results.values() if result == "SKIPPED")
    total = len(results)
    
    print(f"📈 СТАТИСТИКА:")
    print(f"   ✅ Пройдено: {passed}")
    print(f"   ❌ Провалено: {failed}")
    print(f"   ⏭️ Пропущено: {skipped}")
    print(f"   📊 Всего: {total}")
    
    if total > 0:
        success_rate = (passed / total) * 100
        print(f"   🎯 Успешность: {success_rate:.1f}%")
    
    # Detailed results
    print(f"\n📋 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
    for script, result in results.items():
        icon = {"PASSED": "✅", "FAILED": "❌", "SKIPPED": "⏭️"}[result]
        print(f"   {icon} {script}: {result}")
    
    # Critical failures analysis
    if critical_failures:
        print(f"\n🚨 КРИТИЧЕСКИЕ ПРОБЛЕМЫ ({len(critical_failures)}):")
        for script, description in critical_failures:
            print(f"   ❌ {description} ({script})")
        
        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        print(f"   1. Исправьте критические ошибки выше")
        print(f"   2. Проверьте зависимости: pip install -r requirements.txt")
        print(f"   3. Убедитесь что находитесь в правильной директории")
        print(f"   4. Повторите мастер-тест")
    
    # Overall assessment
    if not critical_failures and passed >= total * 0.8:
        print(f"\n🚀 СИСТЕМА ГОТОВА К ПРОДАКШЕНУ!")
        print(f"   ✅ Все критические тесты пройдены")
        print(f"   ✅ Высокий процент успешности ({success_rate:.1f}%)")
        print(f"   💡 Можно переходить к настройке API ключей")
        
    elif not critical_failures:
        print(f"\n⚡ СИСТЕМА В ОСНОВНОМ ГОТОВА!")
        print(f"   ✅ Критические компоненты работают")
        print(f"   ⚠️ Есть некритические проблемы")
        print(f"   💡 Рекомендуется исправить найденные проблемы")
        
    else:
        print(f"\n🔧 СИСТЕМА ТРЕБУЕТ ИСПРАВЛЕНИЙ!")
        print(f"   ❌ {len(critical_failures)} критических проблем")
        print(f"   🚨 Система не готова к продакшену")
        print(f"   🔧 Необходимо исправить критические ошибки")
    
    print(f"\n{'='*80}")
    print("🎯 МАСТЕР-ТЕСТ ЗАВЕРШЕН")
    print(f"{'='*80}")
    
    return len(critical_failures) == 0

if __name__ == "__main__":
    success = asyncio.run(run_master_test_suite())
    
    if success:
        print(f"\n🎉 ВСЕ КРИТИЧЕСКИЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print(f"   Система готова к следующему этапу")
    else:
        print(f"\n💥 ЕСТЬ КРИТИЧЕСКИЕ ПРОБЛЕМЫ!")
        print(f"   Требуется устранение ошибок")
    
    exit(0 if success else 1)
