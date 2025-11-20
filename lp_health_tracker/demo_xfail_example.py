"""
Демонстрация работы xfail тестов

Этот файл показывает разницу между:
1. xfail тест (ожидается провал)
2. обычный тест (должен проходить)
"""

import pytest

# === СЦЕНАРИЙ 1: Функция НЕ РЕАЛИЗОВАНА ===
# Представим, что у нас нет функции calculate_advanced_il()

class AdvancedILCalculator:
    """Пока не реализованный класс для продвинутых IL расчетов."""
    
    def calculate_advanced_il(self, price_ratio, time_factor, volatility):
        """Эта функция пока не реализована!"""
        raise NotImplementedError("Функция пока не готова")


# === XFAIL ТЕСТ ===
@pytest.mark.xfail(reason="calculate_advanced_il не реализована")
def test_advanced_il_calculation():
    """
    XFAIL ТЕСТ - ожидается провал
    
    Этот тест описывает КАК ДОЛЖНА работать функция,
    но мы знаем, что она пока не готова.
    """
    calculator = AdvancedILCalculator()
    
    # Описываем ожидаемое поведение
    result = calculator.calculate_advanced_il(
        price_ratio=2.0,
        time_factor=30,  # 30 дней
        volatility=0.8
    )
    
    # Ожидаемый результат (спецификация)
    assert result > 0
    assert result < 1.0  # IL не может быть больше 100%
    assert isinstance(result, float)


# === ОБЫЧНЫЙ ТЕСТ ===
def test_basic_il_calculation():
    """
    ОБЫЧНЫЙ ТЕСТ - должен проходить
    
    Тестирует уже реализованную функцию.
    """
    # Простая реализованная функция
    def simple_il(price_ratio):
        return abs(2 * (price_ratio**0.5 / (1 + price_ratio)) - 1)
    
    result = simple_il(2.0)
    expected = 0.0572  # Известное значение
    
    assert abs(result - expected) < 0.001


# === ЧТО ПРОИСХОДИТ ПРИ ЗАПУСКЕ ===
if __name__ == "__main__":
    print("=== ДЕМОНСТРАЦИЯ РАБОТЫ ТЕСТОВ ===")
    
    print("\n1. XFAIL тест:")
    print("   - Функция не реализована")
    print("   - Тест упадет, но это ОЖИДАЕТСЯ")
    print("   - pytest покажет: XFAILED (ожидаемый провал)")
    
    print("\n2. Обычный тест:")
    print("   - Функция реализована") 
    print("   - Тест должен пройти")
    print("   - pytest покажет: PASSED")
    
    print("\n3. После реализации функции:")
    print("   - Убираем @pytest.mark.xfail")
    print("   - Тест становится обычным")
    print("   - Должен проходить, иначе ошибка в реализации!")
