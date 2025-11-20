@echo off
REM Скрипт реорганизации тестовых файлов для Windows
REM ===============================================

echo 🚀 РЕОРГАНИЗАЦИЯ ТЕСТОВЫХ ФАЙЛОВ
echo ================================

REM Проверяем что мы в корне проекта
if not exist "config\settings.py" (
    echo ❌ Ошибка: Запустите скрипт из корня проекта
    echo Должен существовать файл config\settings.py
    pause
    exit /b 1
)

echo ✅ Корректная директория проекта найдена

REM Создаем резервную копию
echo.
echo 📦 Создание резервной копии...
if exist backup_tests rmdir /s /q backup_tests
mkdir backup_tests
for %%f in (test_*.py) do copy "%%f" backup_tests\ >nul 2>&1
echo ✅ Резервная копия создана: backup_tests\

REM Создаем недостающие директории
echo.
echo 📁 Создание структуры директорий...
mkdir tests\integration >nul 2>&1
mkdir tests\unit >nul 2>&1 
mkdir tests\e2e >nul 2>&1
mkdir tests\future >nul 2>&1
echo ✅ Структура директорий готова

REM ЭТАП 1: Перемещение файлов
echo.
echo 🔄 ЭТАП 1: Перемещение файлов...

REM Integration tests
if exist test_basic_config.py (
    move test_basic_config.py tests\integration\ >nul 2>&1
    echo ✅ test_basic_config.py → tests\integration\
)

if exist test_config.py (
    move test_config.py tests\integration\ >nul 2>&1
    echo ✅ test_config.py → tests\integration\
)

if exist test_full_compatibility.py (
    move test_full_compatibility.py tests\integration\test_yaml_compatibility.py >nul 2>&1
    echo ✅ test_full_compatibility.py → tests\integration\test_yaml_compatibility.py
)

if exist test_diagnose.py (
    move test_diagnose.py tests\integration\test_web3_connection.py >nul 2>&1
    echo ✅ test_diagnose.py → tests\integration\test_web3_connection.py
)

REM E2E tests
if exist test_fixed_functions.py (
    move test_fixed_functions.py tests\e2e\test_core_functionality.py >nul 2>&1
    echo ✅ test_fixed_functions.py → tests\e2e\test_core_functionality.py
)

REM Unit tests
if exist test_gemini_fixes.py (
    move test_gemini_fixes.py tests\unit\ >nul 2>&1
    echo ✅ test_gemini_fixes.py → tests\unit\
)

REM Future tests
if exist test_activated_xfail.py (
    move test_activated_xfail.py tests\future\test_price_strategy.py >nul 2>&1
    echo ✅ test_activated_xfail.py → tests\future\test_price_strategy.py
)

REM ЭТАП 2: Удаление устаревших файлов
echo.
echo 🗑️ ЭТАП 2: Удаление устаревших файлов...

if exist test_fix.py (
    del test_fix.py >nul 2>&1
    echo ✅ Удален: test_fix.py (временный файл)
)

if exist test_fixtures_validation.py (
    del test_fixtures_validation.py >nul 2>&1
    echo ✅ Удален: test_fixtures_validation.py (служебный файл)
)

if exist test_core_functions.py (
    del test_core_functions.py >nul 2>&1
    echo ✅ Удален: test_core_functions.py (устаревшая версия)
)

REM ЭТАП 3: Интеграция файлов (требует ручной работы)
echo.
echo 📝 ЭТАП 3: Файлы для интеграции...
echo.
echo Следующие файлы требуют РУЧНОЙ интеграции:
if exist test_alert_logic_fix.py echo   test_alert_logic_fix.py → tests\unit\test_data_analyzer.py
if exist test_fixes.py echo   test_fixes.py → tests\unit\test_data_analyzer.py
if exist test_gas_quick.py echo   test_gas_quick.py → tests\unit\test_gas_cost_calculator.py
if exist test_gas_simple.py echo   test_gas_simple.py → tests\unit\test_gas_cost_calculator.py
if exist test_improved_settings.py echo   test_improved_settings.py → tests\integration\test_config_validation.py

echo.
echo ⚠️ ВНИМАНИЕ: Эти файлы НЕ перемещены автоматически!
echo Их содержимое нужно добавить в соответствующие целевые файлы
echo и затем удалить исходные файлы.

echo.
echo 🎉 АВТОМАТИЧЕСКАЯ РЕОРГАНИЗАЦИЯ ЗАВЕРШЕНА!
echo ============================================
echo.
echo ✅ Файлы перемещены в правильные папки
echo ✅ Устаревшие файлы удалены  
echo ✅ Резервная копия создана
echo.
echo 📋 СЛЕДУЮЩИЕ ШАГИ:
echo 1. Интегрируйте оставшиеся файлы вручную (см. список выше)
echo 2. Обновите импорты в перемещенных файлах
echo 3. Запустите: python -m pytest tests/ -v
echo 4. Зафиксируйте: git add . ^&^& git commit -m "Reorganize test files"
echo.

pause
