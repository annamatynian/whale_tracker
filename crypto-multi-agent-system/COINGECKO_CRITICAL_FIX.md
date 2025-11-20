"""
КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: CoinGecko API Limits
============================================

ПРОБЛЕМА: Система обрабатывает ВСЕ токены в CoinGecko вместо топ-50
РЕШЕНИЕ: Исправить цикл обогащения для использования отфильтрованного списка

Файл: simple_orchestrator.py
Строка: ~200 (в цикле обогащения)
"""

# НАЙДЕННАЯ ОШИБКА:
# for i, candidate in enumerate(initial_candidates):  # ❌ ВСЕ токены

# ПРАВИЛЬНЫЙ КОД:
# for i, candidate_data in enumerate(enrichment_candidates):  # ✅ Только топ-50
