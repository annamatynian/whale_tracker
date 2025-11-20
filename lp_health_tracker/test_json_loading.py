import pytest
import sys
import os
from pathlib import Path

# Убедимся что мы в правильной директории
os.chdir(Path(__file__).parent)

# Добавим путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from simple_multi_pool import SimpleMultiPoolManager

def test_load_positions_from_json():
    """Простой тест загрузки позиций из JSON."""
    print("\n🔍 Testing position loading from JSON...")
    
    # Создаем менеджер
    manager = SimpleMultiPoolManager()
    
    # Проверяем что файл существует
    positions_file = Path('data/positions.json')
    assert positions_file.exists(), f"positions.json not found at {positions_file.absolute()}"
    print(f"✅ Found positions.json at: {positions_file.absolute()}")
    
    # Загружаем позиции
    success = manager.load_positions_from_json('data/positions.json')
    assert success, "Failed to load positions from JSON"
    print(f"✅ Successfully loaded positions")
    
    # Проверяем что позиции загрузились
    pool_count = manager.count_pools()
    assert pool_count > 0, "No pools loaded"
    print(f"✅ Loaded {pool_count} pools")
    
    # Проверяем структуру загруженных позиций
    pools = manager.pools
    for i, pool in enumerate(pools):
        print(f"  Pool {i+1}: {pool.get('name', 'Unknown')}")
        assert 'token_a_symbol' in pool, f"Pool {i+1} missing token_a_symbol"
        assert 'token_b_symbol' in pool, f"Pool {i+1} missing token_b_symbol"
        assert 'gas_costs_usd' in pool, f"Pool {i+1} missing gas_costs_usd"
        print(f"    ✅ Has required fields: {pool['token_a_symbol']}-{pool['token_b_symbol']}, gas: ${pool['gas_costs_usd']}")

if __name__ == "__main__":
    try:
        test_load_positions_from_json()
        print("\n🎉 Тест прошел успешно! Проблема с JSON исправлена!")
    except AssertionError as e:
        print(f"\n❌ Тест провален: {e}")
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
