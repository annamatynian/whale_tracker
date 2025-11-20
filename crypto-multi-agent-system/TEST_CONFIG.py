"""
ВРЕМЕННАЯ КОНФИГУРАЦИЯ ДЛЯ ТЕСТИРОВАНИЯ
======================================

Минимальные API лимиты для безопасного тестирования
"""

# Добавьте в simple_orchestrator.py для тестирования:

# ТЕСТОВАЯ конфигурация воронки - ЭКСТРЕМАЛЬНО ОГРАНИЧЕННАЯ
TEST_FUNNEL_CONFIG = {
    'min_discovery_score_for_onchain': 30,     # Минимальный Discovery score для OnChain
    'top_n_for_enrichment': 5,                 # ТОЛЬКО 5 токенов в CoinGecko для тестирования! 
    'min_score_for_alert': 50,                 # ПОНИЖЕН с 60 до 50 для получения алертов
    'max_onchain_candidates': 20,              # Максимум 20 OnChain анализов за цикл
    'api_calls_threshold': 60                  # Повышен порог для экономии
}

# Заменить в коде:
# FUNNEL_CONFIG = TEST_FUNNEL_CONFIG  # Для тестирования
