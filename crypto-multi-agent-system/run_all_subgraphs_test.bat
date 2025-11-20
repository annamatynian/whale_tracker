@echo off
echo ==========================================
echo     ТЕСТ ВСЕХ СУБГРАФОВ THE GRAPH
echo ==========================================
echo.
echo Проверяем все настроенные субграфы:
echo - Uniswap V2 (проблемный)
echo - SushiSwap (потенциальная замена)
echo - Uniswap V3 (pools)
echo - PancakeSwap V2 (BSC)
echo.
echo Цель: Найти работающие источники для токенов 30-90 дней
echo.

cd /d "C:\Users\annam\Documents\DeFi-RAG-Project\crypto-multi-agent-system"

echo 🚀 Запускаем comprehensive тест...
echo.

python test_all_subgraphs.py

echo.
echo ==========================================
echo         ТЕСТ ЗАВЕРШЕН
echo ==========================================
echo.
echo Нажмите любую клавишу для закрытия...
pause >nul
