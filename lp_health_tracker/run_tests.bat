@echo off
echo 🧪 ЗАПУСКАЕМ ТЕСТЫ PriceStrategyManager
echo ========================================

cd /d "C:\Users\annam\Documents\DeFi-RAG-Project\lp_health_tracker"

echo.
echo 📊 Запуск тестов через pytest...
echo.

python -m pytest tests/test_future_features.py::TestPriceStrategyManagerFuture -v --tb=short

echo.
echo 📋 СТАТУС ЗАВЕРШЕНИЯ: %ERRORLEVEL%

if %ERRORLEVEL% == 0 (
    echo ✅ ВСЕ ТЕСТЫ ПРОШЛИ!
    echo ✅ PriceStrategyManager работает корректно
    echo ✅ Трансформация xfail → обычный тест успешна!
) else (
    echo ❌ ТЕСТЫ НЕ ПРОШЛИ
    echo ❌ Нужно исправлять реализацию
)

pause
