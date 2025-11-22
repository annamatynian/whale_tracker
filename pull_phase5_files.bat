@echo off
REM ============================================
REM Selective Pull: Phase 5 Files Only
REM Pulls AI Analyzer + Market Data files
REM WITHOUT overwriting database or saved data
REM ============================================

echo.
echo ============================================
echo  Phase 5 Selective Pull
echo ============================================
echo.

REM Get the branch name
set BRANCH=claude/whale-stats-market-data-01Ef7fuKFCHUVsJbcVFf4Sg5

echo Fetching latest changes from remote...
git fetch origin %BRANCH%

echo.
echo ============================================
echo  Pulling Phase 5 files...
echo ============================================
echo.

REM --- NEW FILES (Phase 5) ---
echo [1/10] Market Data Service...
git checkout origin/%BRANCH% -- src/services/market_data_service.py
git checkout origin/%BRANCH% -- src/services/__init__.py

echo [2/10] AI Analyzer enrichment...
git checkout origin/%BRANCH% -- src/ai/whale_ai_analyzer.py
git checkout origin/%BRANCH% -- src/ai/__init__.py
git checkout origin/%BRANCH% -- src/ai/providers/__init__.py

echo [3/10] Main.py integration...
git checkout origin/%BRANCH% -- main.py

echo [4/10] Configuration...
git checkout origin/%BRANCH% -- config/base.yaml

echo [5/10] Repository enhancements...
git checkout origin/%BRANCH% -- src/repositories/in_memory_detection_repository.py
git checkout origin/%BRANCH% -- src/repositories/sql_detection_repository.py

echo [6/10] Unit tests...
git checkout origin/%BRANCH% -- tests/unit/test_market_data_service.py
git checkout origin/%BRANCH% -- tests/unit/test_whale_statistics.py

echo [7/10] Test fixes...
git checkout origin/%BRANCH% -- tests/unit/test_repositories.py
git checkout origin/%BRANCH% -- tests/unit/test_blockchain_providers.py

echo [8/10] E2E tests...
git checkout origin/%BRANCH% -- tests/integration/test_e2e_phase5.py

echo [9/10] Abstract detection repository...
git checkout origin/%BRANCH% -- src/abstractions/detection_repository.py

echo [10/10] Repository exports...
git checkout origin/%BRANCH% -- src/repositories/__init__.py

echo.
echo ============================================
echo  SUCCESS! Phase 5 files pulled
echo ============================================
echo.

echo Files pulled:
echo   - Market Data Service (NEW)
echo   - AI Analyzer with auto-enrichment
echo   - Main.py with async setup
echo   - Config with Phase 5 settings
echo   - E2E tests
echo.

echo NOT TOUCHED (your data is safe):
echo   - Database files
echo   - .env files
echo   - Data directories
echo   - Custom configurations
echo.

echo Next steps:
echo   1. Review changes: git diff
echo   2. Test: python -m pytest tests/integration/test_e2e_phase5.py
echo   3. Update .env with API keys if needed
echo.

pause
