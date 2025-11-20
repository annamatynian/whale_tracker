"""
Пример трансформации XFAIL → обычный тест

СЦЕНАРИЙ: Реализуем PriceStrategyManager и превращаем xfail тест в обычный
"""

import pytest
from unittest.mock import Mock
import time


# ===== ЭТАП 1: ФУНКЦИЯ НЕ РЕАЛИЗОВАНА =====
# Представим, что PriceStrategyManager пока не существует

class MockPriceStrategyManager:
    """Заглушка - показывает, что функция не готова"""
    def __init__(self, sources):
        raise NotImplementedError("PriceStrategyManager не реализован")


# ===== XFAIL ТЕСТ (ПОКА ФУНКЦИЯ НЕ ГОТОВА) =====
@pytest.mark.xfail(reason="PriceStrategyManager не реализован")
def test_price_strategy_fallback_xfail():
    """
    XFAIL ВЕРСИЯ теста
    
    Описывает КАК ДОЛЖНА работать функция, но знаем, что она не готова.
    Pytest запустит тест, он упадет, но покажет XFAILED (ожидаемо).
    """
    # Создаем стратегию с fallback источниками
    strategy = MockPriceStrategyManager(['primary', 'backup'])
    
    # Описываем ожидаемое поведение
    price = strategy.get_token_price('ETH')
    assert price > 0
    assert strategy.last_used_source in ['primary', 'backup']


# ===== ЭТАП 2: РЕАЛИЗУЕМ ФУНКЦИЮ =====
class RealPriceStrategyManager:
    """Настоящая реализация PriceStrategyManager"""
    
    def __init__(self, sources):
        self.sources = sources
        self.last_used_source = None
        
    def get_token_price(self, token):
        """Получение цены с fallback логикой"""
        for source in self.sources:
            try:
                if source == 'primary':
                    # Имитируем провал первичного источника
                    raise Exception("Primary source failed")
                elif source == 'backup':
                    # Backup источник работает
                    self.last_used_source = source
                    return 2000.0  # Цена ETH
            except:
                continue
        raise Exception("All sources failed")


# ===== ОБЫЧНЫЙ ТЕСТ (ПОСЛЕ РЕАЛИЗАЦИИ) =====
def test_price_strategy_fallback_normal():
    """
    ОБЫЧНЫЙ ТЕСТ - после реализации функции
    
    Точно такой же тест, но БЕЗ @pytest.mark.xfail декоратора.
    Теперь он ДОЛЖЕН проходить, потому что функция реализована.
    """
    # Создаем стратегию с fallback источниками
    strategy = RealPriceStrategyManager(['primary', 'backup'])
    
    # Тестируем поведение - теперь должно работать!
    price = strategy.get_token_price('ETH')
    assert price > 0
    assert strategy.last_used_source == 'backup'  # primary failed, used backup


# ===== ДЕМОНСТРАЦИЯ ПРОЦЕССА =====
def demonstrate_xfail_transformation():
    """Показывает весь процесс трансформации"""
    
    print("🔄 ПРОЦЕСС ТРАНСФОРМАЦИИ XFAIL → ОБЫЧНЫЙ ТЕСТ")
    print("=" * 60)
    
    print("\n📝 ЭТАП 1: Пишем XFAIL тест (функции нет)")
    print("   @pytest.mark.xfail(reason='не реализован')")
    print("   def test_function():")
    print("       # Описываем КАК должно работать")
    print("   ")
    print("   🟡 РЕЗУЛЬТАТ: pytest показывает 'XFAILED' (ожидаемо)")
    
    print("\n⚙️  ЭТАП 2: Реализуем функцию")
    print("   class RealPriceStrategyManager:")
    print("       def get_token_price(self): ...")
    
    print("\n✅ ЭТАП 3: Убираем @pytest.mark.xfail")
    print("   # @pytest.mark.xfail <-- удаляем эту строку")
    print("   def test_function():  # тест остается тот же!")
    print("       # Тот же самый тест")
    print("   ")
    print("   🟢 РЕЗУЛЬТАТ: pytest показывает 'PASSED' (функция работает)")
    
    print("\n🎯 ПОЛЬЗА:")
    print("   ✓ Тест служит спецификацией ПЕРЕД написанием кода")
    print("   ✓ Гарантирует, что функция работает как ожидалось")
    print("   ✓ Предотвращает забывание тестов")
    print("   ✓ Документирует ожидаемое поведение")
    

if __name__ == "__main__":
    demonstrate_xfail_transformation()
    
    print("\n" + "="*60)
    print("🧪 ТЕСТИРОВАНИЕ В ДЕЙСТВИИ:")
    
    print("\n❌ XFAIL тест (функция не готова):")
    try:
        test_price_strategy_fallback_xfail()
        print("   Неожиданно: тест прошел!")
    except Exception as e:
        print(f"   Ожидаемо: тест упал - {e}")
        print("   pytest бы показал: XFAILED")
    
    print("\n✅ Обычный тест (функция реализована):")
    try:
        test_price_strategy_fallback_normal()
        print("   Отлично: тест прошел!")
        print("   pytest показывает: PASSED")
    except Exception as e:
        print(f"   Ошибка: {e}")
        print("   Нужно исправлять реализацию!")
