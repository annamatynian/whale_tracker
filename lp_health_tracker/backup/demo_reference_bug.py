#!/usr/bin/env python3
"""
Demonstration of Reference vs Copy Bug
====================================

This shows exactly why the pool data persistence bug was serious.
"""

def demonstrate_reference_problem():
    """Show the problem with storing references instead of copies."""
    print("🐛 ДЕМОНСТРАЦИЯ ПРОБЛЕМЫ: Reference vs Copy")
    print("=" * 50)
    
    # Simulate the OLD buggy behavior
    class BuggyManager:
        def __init__(self):
            self.pools = []
        
        def add_pool(self, pool_config):
            # BAD: Store reference (старая версия)
            self.pools.append(pool_config)
    
    # Simulate the FIXED behavior  
    class FixedManager:
        def __init__(self):
            self.pools = []
            
        def add_pool(self, pool_config):
            # GOOD: Store copy (новая версия)
            self.pools.append(pool_config.copy())
    
    # Test data
    original_pool = {
        'name': 'WETH-USDC Pool',
        'initial_liquidity_a': 100.0,
        'gas_costs_usd': 50.0
    }
    
    print(f"\n📊 Исходные данные пула:")
    print(f"   Название: {original_pool['name']}")
    print(f"   Ликвидность: {original_pool['initial_liquidity_a']}")
    print(f"   Газ: ${original_pool['gas_costs_usd']}")
    
    # Test both managers
    buggy = BuggyManager()
    fixed = FixedManager()
    
    # Add to both managers
    buggy.add_pool(original_pool)
    fixed.add_pool(original_pool)
    
    print(f"\n➕ Добавили пул в оба менеджера...")
    
    # Now modify the original data (как это может случиться в реальном коде)
    print(f"\n🔧 Теперь ИЗМЕНЯЕМ оригинальные данные...")
    original_pool['name'] = '❌ ПОВРЕЖДЕННЫЕ ДАННЫЕ ❌'
    original_pool['initial_liquidity_a'] = -999.0  # Невалидное значение!
    original_pool['gas_costs_usd'] = -100.0        # Отрицательная стоимость газа!?
    
    print(f"   Новое название: {original_pool['name']}")
    print(f"   Новая ликвидность: {original_pool['initial_liquidity_a']}")
    print(f"   Новый газ: ${original_pool['gas_costs_usd']}")
    
    # Check what happened in both managers
    print(f"\n🔍 РЕЗУЛЬТАТЫ:")
    
    print(f"\n❌ BUGGY MANAGER (хранит ссылки):")
    buggy_pool = buggy.pools[0]
    print(f"   Название: {buggy_pool['name']}")
    print(f"   Ликвидность: {buggy_pool['initial_liquidity_a']}")
    print(f"   Газ: ${buggy_pool['gas_costs_usd']}")
    print(f"   ⚠️ ПРОБЛЕМА: Данные испорчены внешними изменениями!")
    
    print(f"\n✅ FIXED MANAGER (хранит копии):")
    fixed_pool = fixed.pools[0] 
    print(f"   Название: {fixed_pool['name']}")
    print(f"   Ликвидность: {fixed_pool['initial_liquidity_a']}")
    print(f"   Газ: ${fixed_pool['gas_costs_usd']}")
    print(f"   ✅ ОТЛИЧНО: Данные защищены от внешних изменений!")
    
    # Demonstrate the consequences
    print(f"\n💥 ПОСЛЕДСТВИЯ В РЕАЛЬНОМ ПРИЛОЖЕНИИ:")
    print(f"   ❌ Buggy: Расчет P&L с ликвидностью -999 = CRASH!")
    print(f"   ❌ Buggy: Отрицательная стоимость газа = неверные результаты!")
    print(f"   ❌ Buggy: Название '❌ ПОВРЕЖДЕННЫЕ ДАННЫЕ ❌' в отчетах!")
    print(f"   ✅ Fixed: Все расчеты используют корректные данные!")
    
    print(f"\n🎯 ВЫВОД:")
    print(f"   Хранение ССЫЛОК → непредсказуемые баги")  
    print(f"   Хранение КОПИЙ → предсказуемое поведение")
    print(f"   Это критически важно для надежности системы!")

if __name__ == "__main__":
    demonstrate_reference_problem()
