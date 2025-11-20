#!/usr/bin/env python3
"""
Быстрый тест Price Strategy Manager
================================

Проверяет основную функциональность без реальных API вызовов.
"""

import asyncio
import sys
import pytest
from pathlib import Path

# Добавить src в путь
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.price_strategy_manager import get_price_manager, PriceSource


@pytest.mark.asyncio
async def test_pydantic_models():
    """Тестируем Pydantic модели."""
    print("🔍 Тестирование Pydantic моделей...")
    
    # Правильное создание PriceSource
    try:
        source = PriceSource(
            name="test_source",
            priority=1,
            rate_limit=50,
            reliability=0.95
        )
        print(f"✅ PriceSource создан: {source.name} (rate_limit: {source.rate_limit})")
    except Exception as e:
        print(f"❌ Ошибка создания PriceSource: {e}")
        return False
    
    # Валидация работает?
    try:
        invalid_source = PriceSource(
            name="",  # Пустое имя - должно вызвать ошибку
            priority=1,
            rate_limit=50,
            reliability=0.95
        )
        print("❌ Валидация не работает - пустое имя прошло!")
        return False
    except Exception:
        print("✅ Валидация работает - пустое имя отклонено")
    
    return True


@pytest.mark.asyncio
async def test_rate_limiting():
    """Тестируем rate limiting."""
    print("\n🔍 Тестирование rate limiting...")
    
    try:
        # Получаем экземпляр price_manager
        price_manager = get_price_manager()
        
        # Проверим что semaphores созданы
        assert 'coingecko' in price_manager._rate_limiters
        assert isinstance(price_manager._rate_limiters['coingecko'], asyncio.Semaphore)
        print("✅ Rate limiters инициализированы")
        
        # Проверим что можем получить semaphore
        async with price_manager._rate_limiters['coingecko']:
            print("✅ Rate limiting semaphore работает")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка rate limiting: {e}")
        return False


@pytest.mark.asyncio
async def test_session_management():
    """Тестируем управление сессиями."""
    print("\n🔍 Тестирование управления сессиями...")
    
    try:
        # Получаем экземпляр price_manager
        price_manager = get_price_manager()
        
        # Тест context manager
        async with price_manager as pm:
            session = await pm._get_session()
            print(f"✅ Сессия создана: {type(session).__name__}")
            
            # Проверим настройки сессии
            if hasattr(session, '_timeout'):
                print(f"✅ Timeout настроен: {session._timeout}")
            
        print("✅ Context manager работает")
        return True
    except Exception as e:
        print(f"❌ Ошибка управления сессиями: {e}")
        return False


@pytest.mark.asyncio
async def test_cache_functionality():
    """Тестируем кеширование."""
    print("\n🔍 Тестирование кеширования...")
    
    try:
        # Получаем экземпляр price_manager
        price_manager = get_price_manager()
        
        # Добавим цену в кеш
        price_manager._cache_price("test_token", 100.0)
        
        # Проверим что она там есть
        if price_manager._is_price_cached("test_token"):
            cached_price = price_manager._price_cache["test_token"]
            print(f"✅ Кеш работает: цена {cached_price.price} на {cached_price.timestamp}")
            
            # Проверим Pydantic модель CachedPrice
            assert hasattr(cached_price, 'is_expired')
            print(f"✅ CachedPrice модель: expired={cached_price.is_expired}")
        else:
            print("❌ Кеш не работает")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Ошибка кеширования: {e}")
        return False


async def main():
    """Главная функция тестирования."""
    print("🚀 Запуск тестов Price Strategy Manager\n")
    
    tests = [
        test_pydantic_models,
        test_rate_limiting,
        test_session_management,
        test_cache_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
        except Exception as e:
            print(f"❌ Тест {test.__name__} упал с ошибкой: {e}")
    
    print(f"\n📊 Результаты тестов: {passed}/{total} прошли")
    
    if passed == total:
        print("🎉 Все тесты прошли! Price Strategy Manager готов к использованию!")
        return True
    else:
        print("🚨 Некоторые тесты не прошли. Требуется доработка.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
