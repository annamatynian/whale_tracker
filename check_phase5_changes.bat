@echo off
REM ============================================
REM Check Phase 5 Changes Before Pull
REM Shows what will be updated
REM ============================================

echo.
echo ============================================
echo  Phase 5 Changes Preview
echo ============================================
echo.

set BRANCH=claude/whale-stats-market-data-01Ef7fuKFCHUVsJbcVFf4Sg5

echo Fetching latest changes...
git fetch origin %BRANCH%

echo.
echo ============================================
echo  NEW FILES (will be created):
echo ============================================
echo.

git ls-tree -r --name-only origin/%BRANCH% | findstr /C:"src/services/market_data_service.py"
git ls-tree -r --name-only origin/%BRANCH% | findstr /C:"src/services/__init__.py"
git ls-tree -r --name-only origin/%BRANCH% | findstr /C:"tests/integration/test_e2e_phase5.py"
git ls-tree -r --name-only origin/%BRANCH% | findstr /C:"tests/unit/test_market_data_service.py"
git ls-tree -r --name-only origin/%BRANCH% | findstr /C:"tests/unit/test_whale_statistics.py"

echo.
echo ============================================
echo  MODIFIED FILES (will be updated):
echo ============================================
echo.

echo src/ai/whale_ai_analyzer.py
echo src/ai/__init__.py
echo src/ai/providers/__init__.py
echo main.py
echo config/base.yaml
echo src/repositories/in_memory_detection_repository.py
echo src/repositories/sql_detection_repository.py

echo.
echo ============================================
echo  Preview specific file changes?
echo ============================================
echo.
echo Type filename to see changes (or 'skip' to continue):
echo   1. main.py
echo   2. config/base.yaml
echo   3. src/ai/whale_ai_analyzer.py
echo   4. src/services/market_data_service.py
echo   5. skip
echo.

set /p choice="Your choice (1-5): "

if "%choice%"=="1" (
    echo.
    echo === Changes in main.py ===
    git diff HEAD origin/%BRANCH% -- main.py
    pause
)

if "%choice%"=="2" (
    echo.
    echo === Changes in config/base.yaml ===
    git diff HEAD origin/%BRANCH% -- config/base.yaml
    pause
)

if "%choice%"=="3" (
    echo.
    echo === Changes in src/ai/whale_ai_analyzer.py ===
    git diff HEAD origin/%BRANCH% -- src/ai/whale_ai_analyzer.py
    pause
)

if "%choice%"=="4" (
    echo.
    echo === New file: src/services/market_data_service.py ===
    git show origin/%BRANCH%:src/services/market_data_service.py | more
    pause
)

echo.
echo ============================================
echo  Ready to pull?
echo ============================================
echo.
echo Run: pull_phase5_files.bat
echo.

pause
