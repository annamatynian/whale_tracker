#!/usr/bin/env python3
"""
ТЕСТ ИСПРАВЛЕНИЯ COINGECKO API LIMITS
====================================

Проверяет что система теперь использует только топ-N токенов для CoinGecko
вместо отправки всех найденных токенов.

ЦЕЛЬ: Убедиться что исправление работает и экономит API лимиты
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

# Настраиваем логирование для мониторинга
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class CoinGeckoCallCounter:
    """Мониторит вызовы CoinGecko для проверки исправления."""
    def __init__(self):
        self.call_count = 0
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def patch_coingecko_client(self):
        """Патчит CoinGecko клиент для подсчета вызовов."""
        from tools.market_data.coingecko_client import CoinGeckoClient
        
        # Сохраняем оригинальный метод
        original_method = CoinGeckoClient.get_token_info_by_contract
        
        def counting_wrapper(self, chain_name, contract_address):
            # Увеличиваем счетчик
            nonlocal call_count_ref
            call_count_ref[0] += 1
            
            self.logger.info(f"🔥 CoinGecko вызов #{call_count_ref[0]}: {chain_name}/{contract_address[:8]}...")
            
            # Вызываем оригинальный метод
            return original_method(self, chain_name, contract_address)
        
        # Ссылка на счетчик для замыкания
        call_count_ref = [0]
        
        # Заменяем метод
        CoinGeckoClient.get_token_info_by_contract = counting_wrapper
        
        return call_count_ref

async def test_coingecko_limits():
    """Тестирует исправление лимитов CoinGecko."""
    print("🧪 ТЕСТ ИСПРАВЛЕНИЯ COINGECKO API LIMITS")
    print("=" * 60)
    
    counter = CoinGeckoCallCounter()
    call_count_ref = counter.patch_coingecko_client()
    
    # Импортируем после патчинга
    from agents.orchestrator.simple_orchestrator import SimpleOrchestrator, FUNNEL_CONFIG
    
    print(f"⚙️  Конфигурация:")
    print(f"   top_n_for_enrichment: {FUNNEL_CONFIG['top_n_for_enrichment']}")
    print(f"   max_onchain_candidates: {FUNNEL_CONFIG['max_onchain_candidates']}")
    print(f"   api_calls_threshold: {FUNNEL_CONFIG['api_calls_threshold']}")
    print()
    
    print("🚀 Запускаем analysis pipeline...")
    print("   Мониторим количество вызовов CoinGecko...")
    print()
    
    try:
        orchestrator = SimpleOrchestrator()
        
        # Засекаем время
        start_time = datetime.now()
        
        # Запускаем pipeline
        alerts = await orchestrator.run_analysis_pipeline()
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Результаты
        print()
        print("📊 РЕЗУЛЬТАТЫ ТЕСТА:")
        print("=" * 40)
        print(f"🔥 CoinGecko вызовов: {call_count_ref[0]}")
        print(f"⏱️  Время выполнения: {duration:.1f}s")
        print(f"📋 Алертов создано: {len(alerts)}")
        
        # Проверяем исправление
        expected_max_calls = FUNNEL_CONFIG['top_n_for_enrichment']
        
        if call_count_ref[0] <= expected_max_calls:
            print()
            print("✅ ИСПРАВЛЕНИЕ РАБОТАЕТ!")
            print(f"   Ожидалось максимум: {expected_max_calls} вызовов")
            print(f"   Фактически сделано: {call_count_ref[0]} вызовов")
            print("   👍 API лимиты соблюдены!")
            
            # Расчет экономии
            monthly_budget = 10000
            calls_per_run = call_count_ref[0]
            runs_per_month = monthly_budget // calls_per_run if calls_per_run > 0 else 0
            
            print()
            print("💰 ЭКОНОМИЯ API ЛИМИТОВ:")
            print(f"   Месячный бюджет: {monthly_budget:,} вызовов")
            print(f"   Вызовов за запуск: {calls_per_run}")
            print(f"   Запусков в месяц: {runs_per_month:,}")
            print(f"   Запусков в день: ~{runs_per_month // 30}")
            
            return True
            
        else:
            print()
            print("❌ ИСПРАВЛЕНИЕ НЕ РАБОТАЕТ!")
            print(f"   Ожидалось максимум: {expected_max_calls} вызовов")
            print(f"   Фактически сделано: {call_count_ref[0]} вызовов")
            print("   ⚠️  Система все еще тратит слишком много API calls!")
            
            return False
            
    except Exception as e:
        print(f"❌ ОШИБКА В ТЕСТЕ: {e}")
        return False

def test_configuration():
    """Проверяет конфигурацию для тестирования."""
    print("⚙️  ПРОВЕРКА КОНФИГУРАЦИИ:")
    print("=" * 40)
    
    from agents.orchestrator.simple_orchestrator import FUNNEL_CONFIG
    
    print(f"top_n_for_enrichment: {FUNNEL_CONFIG['top_n_for_enrichment']}")
    print(f"max_onchain_candidates: {FUNNEL_CONFIG['max_onchain_candidates']}")
    print(f"api_calls_threshold: {FUNNEL_CONFIG['api_calls_threshold']}")
    
    if FUNNEL_CONFIG['top_n_for_enrichment'] > 10:
        print()
        print("⚠️  РЕКОМЕНДАЦИЯ: Для тестирования установите top_n_for_enrichment <= 10")
        print("   Это защитит от больших трат API лимитов")
        
        # Временная тестовая конфигурация
        print()
        print("💡 ВРЕМЕННАЯ ТЕСТОВАЯ КОНФИГУРАЦИЯ:")
        print("   top_n_for_enrichment: 5  # Только 5 токенов в CoinGecko")
        print("   max_onchain_candidates: 20  # Максимум 20 OnChain анализов")
        print("   api_calls_threshold: 70  # Повышенный порог для экономии")

async def main():
    """Основная функция теста."""
    print()
    print("🧪 ТЕСТ ИСПРАВЛЕНИЯ COINGECKO LIMITS")
    print("=" * 60)
    print("Цель: Проверить что система использует только топ-N токенов")
    print("Автор: Fix verification test")
    print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Проверяем конфигурацию
    test_configuration()
    print()
    
    # Запускаем тест
    success = await test_coingecko_limits()
    
    print()
    print("=" * 60)
    if success:
        print("🎉 ТЕСТ ПРОЙДЕН: Исправление работает!")
        print("✅ API лимиты экономятся как ожидается")
    else:
        print("❌ ТЕСТ НЕ ПРОЙДЕН: Требуется дополнительная отладка")
        print("⚠️  Проверьте правильность исправления кода")
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit_code = 0 if success else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏹️  Тест прерван пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)
