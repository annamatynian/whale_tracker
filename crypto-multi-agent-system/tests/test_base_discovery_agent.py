"""
Тест BaseDiscoveryAgent - Базовый класс архитектуры

Тестирует ТОЛЬКО базовую функциональность:
- Импорты и зависимости
- Декораторы (rate_limit, track_api_cost)
- API функции (fetch_pairs_for_chain)
- Утилиты (get_current_git_hash)
- Абстрактные методы

Поскольку BaseDiscoveryAgent абстрактный, создаем минимальную реализацию для тестов.

Author: Step-by-step testing approach
"""

import sys
import os
import asyncio
import time
from typing import Dict, Any, Tuple

# Добавляем пути
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def test_base_imports():
    """Тест 1: Импорты и зависимости"""
    print("🧪 ТЕСТ 1: Импорты BaseDiscoveryAgent")
    print("-" * 40)
    
    try:
        # Импортируем модель из актуального файла
        from agents.discovery.discovery_models import TokenDiscoveryReport
        
        # Архивные утилиты остаются для обратной совместимости
        from agents.discovery.archive.base_discovery_agent import (
            BaseDiscoveryAgent,
            fetch_pairs_for_chain,
            get_current_git_hash,
            rate_limit,
            track_api_cost,
            CHAINS_TO_SCAN,
            logger
        )
        
        print("✅ Все импорты успешны")
        print(f"   - BaseDiscoveryAgent: {BaseDiscoveryAgent}")
        print(f"   - TokenDiscoveryReport: {TokenDiscoveryReport}")
        print(f"   - CHAINS_TO_SCAN: {CHAINS_TO_SCAN}")
        print(f"   - logger: {logger}")
        
        return True, {
            'BaseDiscoveryAgent': BaseDiscoveryAgent,
            'TokenDiscoveryReport': TokenDiscoveryReport,
            'fetch_pairs_for_chain': fetch_pairs_for_chain,
            'get_current_git_hash': get_current_git_hash,
            'rate_limit': rate_limit,
            'track_api_cost': track_api_cost,
            'CHAINS_TO_SCAN': CHAINS_TO_SCAN,
            'logger': logger
        }
        
    except Exception as e:
        print(f"❌ Ошибка импорта: {e}")
        return False, {}

def test_decorators(imports):
    """Тест 2: Декораторы rate_limit и track_api_cost"""
    print("\n🧪 ТЕСТ 2: Декораторы")
    print("-" * 40)
    
    try:
        rate_limit = imports['rate_limit']
        track_api_cost = imports['track_api_cost']
        
        # Тестируем декораторы на простой функции
        @rate_limit('test_api')
        @track_api_cost('test_api', cost_units=1)
        def test_function():
            return "success"
        
        result = test_function()
        print(f"✅ Декораторы работают: {result}")
        
        # Проверяем что декораторы возвращают функции
        print(f"   - rate_limit создает декоратор: {callable(rate_limit('test'))}")
        print(f"   - track_api_cost создает декоратор: {callable(track_api_cost('test'))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка декораторов: {e}")
        return False

def test_utilities(imports):
    """Тест 3: Утилитарные функции"""
    print("\n🧪 ТЕСТ 3: Утилиты")
    print("-" * 40)
    
    try:
        get_current_git_hash = imports['get_current_git_hash']
        
        # Тест git hash
        git_hash = get_current_git_hash()
        print(f"✅ Git hash функция работает: {git_hash}")
        print(f"   - Тип результата: {type(git_hash)}")
        print(f"   - Длина (если есть): {len(git_hash) if git_hash else 'None'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка утилит: {e}")
        return False

def test_pydantic_model(imports):
    """Тест 4: Pydantic модель TokenDiscoveryReport"""
    print("\n🧪 ТЕСТ 4: TokenDiscoveryReport модель")
    print("-" * 40)
    
    try:
        TokenDiscoveryReport = imports['TokenDiscoveryReport']
        from datetime import datetime
        
        # Создаем тестовый отчет
        test_data = {
            "pair_address": "0x1234567890abcdef",
            "chain_id": "ethereum", 
            "base_token_address": "0xabcdef1234567890",
            "base_token_symbol": "TEST",
            "base_token_name": "Test Token",
            "liquidity_usd": 50000.0,
            "volume_h24": 25000.0,
            "price_usd": 1.5,
            "price_change_h1": 5.2,
            "pair_created_at": datetime.now(),
            "age_minutes": 120.0,
            "discovery_score": 75,
            "discovery_reason": "High liquidity + Good volume"
        }
        
        report = TokenDiscoveryReport(**test_data)
        print("✅ TokenDiscoveryReport создается корректно")
        print(f"   - Symbol: {report.base_token_symbol}")
        print(f"   - Score: {report.discovery_score}")
        print(f"   - Liquidity: ${report.liquidity_usd:,.0f}")
        
        # Тест валидации
        try:
            invalid_report = TokenDiscoveryReport(
                **{**test_data, "discovery_score": 150}  # Невалидный score
            )
            print("❌ Валидация не работает (принял score 150)")
            return False
        except Exception:
            print("✅ Валидация работает (отклонил невалидный score)")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка модели: {e}")
        return False

def test_api_function(imports):
    """Тест 5: API функция fetch_pairs_for_chain (без реального запроса)"""
    print("\n🧪 ТЕСТ 5: API функция (структурный тест)")
    print("-" * 40)
    
    try:
        fetch_pairs_for_chain = imports['fetch_pairs_for_chain']
        
        # Проверяем что функция существует и имеет правильную сигнатуру
        import inspect
        sig = inspect.signature(fetch_pairs_for_chain)
        print(f"✅ Функция fetch_pairs_for_chain найдена")
        print(f"   - Сигнатура: {sig}")
        print(f"   - Параметры: {list(sig.parameters.keys())}")
        
        # Проверяем что функция имеет декораторы
        if hasattr(fetch_pairs_for_chain, '__wrapped__'):
            print("✅ Функция имеет декораторы")
        else:
            print("⚠️ Декораторы могут отсутствовать")
        
        print("⚠️ Реальный API тест пропущен (требует интернет)")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка API функции: {e}")
        return False

class TestDiscoveryAgent(imports['BaseDiscoveryAgent'] if 'BaseDiscoveryAgent' in imports else object):
    """
    Минимальная реализация BaseDiscoveryAgent для тестирования
    Реализует все абстрактные методы минимально
    """
    
    def should_analyze_pair(self, pair_data: Dict[str, Any]) -> bool:
        """Тестовая реализация: принимает все пары с базовой ликвидностью"""
        return pair_data.get('liquidity', {}).get('usd', 0) > 1000
    
    def calculate_score(self, pair_data: Dict[str, Any], age_minutes: float) -> Tuple[int, str]:
        """Тестовая реализация: простой scoring"""
        liquidity = pair_data.get('liquidity', {}).get('usd', 0)
        if liquidity > 50000:
            return 80, "High liquidity test"
        elif liquidity > 10000:
            return 60, "Medium liquidity test"
        else:
            return 40, "Basic liquidity test"
    
    def create_report(self, pair_data: Dict[str, Any], score: int, reason: str, 
                     age_minutes: float, git_hash: str, api_time: float):
        """Тестовая реализация: создает базовый отчет"""
        from datetime import datetime
        
        TokenDiscoveryReport = imports['TokenDiscoveryReport']
        
        return TokenDiscoveryReport(
            pair_address=pair_data.get('pairAddress', 'test_pair'),
            chain_id=pair_data.get('chainId', 'test_chain'),
            base_token_address=pair_data.get('baseToken', {}).get('address', 'test_address'),
            base_token_symbol=pair_data.get('baseToken', {}).get('symbol', 'TEST'),
            base_token_name=pair_data.get('baseToken', {}).get('name', 'Test Token'),
            liquidity_usd=pair_data.get('liquidity', {}).get('usd', 0),
            volume_h24=pair_data.get('volume', {}).get('h24', 0),
            price_usd=float(pair_data.get('priceUsd', 1.0)),
            price_change_h1=pair_data.get('priceChange', {}).get('h1', 0),
            pair_created_at=datetime.now(),
            age_minutes=age_minutes,
            discovery_score=score,
            discovery_reason=reason,
            git_commit_hash=git_hash,
            api_response_time_ms=api_time
        )

def test_abstract_class(imports):
    """Тест 6: Абстрактный класс и его реализация"""
    print("\n🧪 ТЕСТ 6: Абстрактный класс")
    print("-" * 40)
    
    try:
        BaseDiscoveryAgent = imports['BaseDiscoveryAgent']
        
        # Проверяем что BaseDiscoveryAgent нельзя инстанцировать напрямую
        try:
            base_agent = BaseDiscoveryAgent()
            print("❌ BaseDiscoveryAgent не должен инстанцироваться напрямую")
            return False
        except TypeError as e:
            print(f"✅ BaseDiscoveryAgent правильно абстрактный: {e}")
        
        # Создаем тестовую реализацию
        test_agent = TestDiscoveryAgent()
        print("✅ Тестовая реализация создана")
        
        # Проверяем наследование
        is_instance = isinstance(test_agent, BaseDiscoveryAgent)
        print(f"✅ Наследование работает: {is_instance}")
        
        # Проверяем что методы существуют
        required_methods = [
            'should_analyze_pair',
            'calculate_score', 
            'create_report',
            'discover_tokens',
            'discover_tokens_async',
            'get_session_stats'
        ]
        
        for method in required_methods:
            has_method = hasattr(test_agent, method)
            print(f"   - {method}: {'✅' if has_method else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка абстрактного класса: {e}")
        return False

def test_session_stats(imports):
    """Тест 7: Статистики сессии"""
    print("\n🧪 ТЕСТ 7: Статистики сессии")
    print("-" * 40)
    
    try:
        test_agent = TestDiscoveryAgent()
        
        # Проверяем начальное состояние
        initial_stats = test_agent.get_session_stats()
        print("✅ Начальные статистики получены")
        print(f"   - Пары просканированы: {initial_stats['pairs_scanned']}")
        print(f"   - Отчеты созданы: {initial_stats['reports_created']}")
        print(f"   - Success rate: {initial_stats['success_rate']:.1f}%")
        
        # Проверяем структуру статистик
        expected_keys = [
            'pairs_scanned', 'pairs_analyzed', 'reports_created',
            'api_calls_made', 'processing_start_time', 'total_api_time', 'success_rate'
        ]
        
        for key in expected_keys:
            has_key = key in initial_stats
            print(f"   - {key}: {'✅' if has_key else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка статистик: {e}")
        return False

def run_base_discovery_tests():
    """Запуск всех тестов BaseDiscoveryAgent"""
    print("🧪 ТЕСТИРОВАНИЕ BaseDiscoveryAgent")
    print("=" * 50)
    
    # Тест 1: Импорты
    imports_success, imports = test_base_imports()
    if not imports_success:
        print("\n❌ КРИТИЧЕСКАЯ ОШИБКА: Импорты не работают")
        return False
    
    # Добавляем классы в globals для TestDiscoveryAgent
    globals().update(imports)
    
    tests = [
        ("Декораторы", lambda: test_decorators(imports)),
        ("Утилиты", lambda: test_utilities(imports)),
        ("Pydantic модель", lambda: test_pydantic_model(imports)),
        ("API функция", lambda: test_api_function(imports)),
        ("Абстрактный класс", lambda: test_abstract_class(imports)),
        ("Статистики", lambda: test_session_stats(imports))
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {e}")
            results.append(False)
    
    # Итоговый результат
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 РЕЗУЛЬТАТЫ ТЕСТОВ BaseDiscoveryAgent")
    print("=" * 50)
    print(f"Пройдено: {passed}/{total}")
    print(f"Процент: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 BaseDiscoveryAgent полностью работоспособен!")
        return True
    else:
        print("⚠️ BaseDiscoveryAgent требует исправлений")
        return False

if __name__ == "__main__":
    success = run_base_discovery_tests()
    
    if success:
        print("\n🚀 ГОТОВ К СЛЕДУЮЩЕМУ ШАГУ")
        print("BaseDiscoveryAgent протестирован и работает корректно")
    else:
        print("\n🔧 ТРЕБУЕТСЯ ДОРАБОТКА")
        print("Исправьте ошибки перед переходом к следующему шагу")
