"""
Демонстрация трансформации XFAIL → обычный тест

Этот файл показывает ДО и ПОСЛЕ удаления @pytest.mark.xfail декоратора
"""

import pytest
import sys
import os

# Добавляем src в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPriceStrategyTransformation:
    """Демонстрация трансформации xfail теста в обычный."""
    
    # ===== ВЕРСИЯ 1: XFAIL ТЕСТ (ОЖИДАЕТСЯ ПРОВАЛ) =====
    @pytest.mark.xfail(reason="PriceStrategyManager not implemented yet")
    def test_price_strategy_creation_XFAIL(self):
        """
        XFAIL ВЕРСИЯ: Ожидается провал, но описывает спецификацию.
        
        Этот тест показывает КАК ДОЛЖНА работать функция,
        даже если функция еще не готова.
        """
        from src.price_strategy_manager import PriceStrategyManager
        
        # Спецификация: создаем стратегию с 4 источниками
        strategy = PriceStrategyManager([
            'on_chain_uniswap',  # Priority 1
            'coingecko_api',     # Priority 2  
            'coinmarketcap_api', # Priority 3
            'cached_prices'      # Priority 4
        ])
        
        # Спецификация: объект должен создаться
        assert strategy is not None
        # Спецификация: должно быть 4 источника
        assert len(strategy.sources) == 4
    
    # ===== ВЕРСИЯ 2: ОБЫЧНЫЙ ТЕСТ (ДОЛЖЕН ПРОХОДИТЬ) =====
    def test_price_strategy_creation_NORMAL(self):
        """
        ОБЫЧНАЯ ВЕРСИЯ: Должен проходить после реализации.
        
        Точно такой же тест, но БЕЗ @pytest.mark.xfail декоратора.
        Теперь он должен проходить, потому что функция реализована!
        """
        from src.price_strategy_manager import PriceStrategyManager
        
        # Тест: создаем стратегию с 4 источниками
        strategy = PriceStrategyManager([
            'on_chain_uniswap',  # Priority 1
            'coingecko_api',     # Priority 2  
            'coinmarketcap_api', # Priority 3
            'cached_prices'      # Priority 4
        ])
        
        # Проверяем: объект создался
        assert strategy is not None
        # Проверяем: 4 источника
        assert len(strategy.sources) == 4
        
        # Дополнительные проверки (раз функция готова)
        assert isinstance(strategy.sources, list)
        assert strategy.sources[0] == 'on_chain_uniswap'  # Первый приоритет
        assert strategy.cache_hits == 0  # Изначально 0 обращений к кешу
    
    # ===== ДОПОЛНИТЕЛЬНЫЙ ТЕСТ: FALLBACK ЛОГИКА =====  
    def test_price_fallback_mechanism(self):
        """
        Тест fallback логики - еще один превращенный из xfail.
        """
        from src.price_strategy_manager import PriceStrategyManager
        
        # Создаем стратегию с failing и working источниками
        strategy = PriceStrategyManager(['failing_source', 'working_source'])
        
        # Получаем цену - должно сработать через fallback
        price = strategy.get_token_price('ETH')
        
        # Проверяем результат
        assert price is not None
        assert price > 0
        assert strategy.last_used_source == 'working_source'  # Fallback сработал
    
    # ===== ТЕСТ КЕШИРОВАНИЯ =====
    def test_price_caching_mechanism(self):
        """
        Тест кеширования цен.
        """
        from src.price_strategy_manager import PriceStrategyManager
        
        strategy = PriceStrategyManager(['working_source'])
        
        # Первый запрос - должен обратиться к источнику
        price1 = strategy.get_token_price('ETH')
        assert strategy.cache_hits == 0
        
        # Второй запрос - должен использовать кеш
        price2 = strategy.get_token_price('ETH')  
        assert strategy.cache_hits == 1
        assert price1 == price2


# Функция для демонстрации
def demonstrate_test_transformation():
    """Показывает результаты обеих версий теста."""
    
    print("🔬 ДЕМОНСТРАЦИЯ ТРАНСФОРМАЦИИ ТЕСТА")
    print("=" * 50)
    
    print("\n1️⃣  XFAIL ТЕСТ:")
    print("   @pytest.mark.xfail(reason='не реализован')")
    print("   def test_function():")
    print("       # Тот же код теста")
    print("   ")
    print("   📊 Результат pytest: XFAILED (ожидаемый провал)")
    
    print("\n2️⃣  ОБЫЧНЫЙ ТЕСТ:")
    print("   # @pytest.mark.xfail <-- УБРАЛИ эту строку")  
    print("   def test_function():")
    print("       # Точно тот же код теста!")
    print("   ")
    print("   📊 Результат pytest: PASSED ✅ или FAILED ❌")
    
    print("\n🎯 КЛЮЧЕВОЙ МОМЕНТ:")
    print("   • Код теста НЕ ИЗМЕНИЛСЯ")
    print("   • Изменился только ДЕКОРАТОР") 
    print("   • Тест превратился из 'ожидания провала' в 'проверку работы'")


if __name__ == "__main__":
    demonstrate_test_transformation()
