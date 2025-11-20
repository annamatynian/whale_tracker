@echo off
echo 🚀 Запуск активированных xfail тестов...
echo =====================================

cd /d "C:\Users\annam\Documents\DeFi-RAG-Project\lp_health_tracker"

python test_activated_xfail.py > test_results.txt 2>&1

echo.
echo 📋 Результаты тестов сохранены в test_results.txt
echo.

type test_results.txt

pause
