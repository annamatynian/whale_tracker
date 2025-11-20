import sys
import os
import json

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Сначала проверим, что наш файл positions.json корректен
def check_positions_json():
    try:
        with open('data/positions.json', 'r', encoding='utf-8') as f:
            positions = json.load(f)
        
        print(f"✅ positions.json содержит {len(positions)} позиций")
        
        for i, position in enumerate(positions):
            print(f"\nПозиция {i+1}:")
            print(f"  Название: {position.get('name')}")
            print(f"  token_a_symbol: {position.get('token_a_symbol', 'НЕТ')}")
            print(f"  token_b_symbol: {position.get('token_b_symbol', 'НЕТ')}")
            print(f"  gas_costs_usd: {position.get('gas_costs_usd', 'НЕТ')}")
            print(f"  days_held_mock: {position.get('days_held_mock', 'НЕТ')}")
            print(f"  entry_date: {position.get('entry_date', 'НЕТ')}")
            
            # Если есть структура token_a/token_b
            if 'token_a' in position:
                print(f"  token_a.symbol: {position['token_a'].get('symbol', 'НЕТ')}")
            if 'token_b' in position:
                print(f"  token_b.symbol: {position['token_b'].get('symbol', 'НЕТ')}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка в positions.json: {e}")
        return False

# Проверим загрузку через менеджер
def test_position_loading():
    try:
        from simple_multi_pool import SimpleMultiPoolManager
        
        manager = SimpleMultiPoolManager()
        success = manager.load_positions_from_json('data/positions.json')
        
        if success:
            print(f"\n✅ SimpleMultiPoolManager успешно загрузил {manager.count_pools()} позиций")
            return True
        else:
            print(f"\n❌ SimpleMultiPoolManager не смог загрузить позиции")
            return False
    except Exception as e:
        print(f"\n❌ Ошибка в SimpleMultiPoolManager: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔍 Диагностика проблемы с загрузкой JSON")
    print("=" * 50)
    
    # Шаг 1: проверяем JSON
    json_ok = check_positions_json()
    
    # Шаг 2: проверяем загрузку менеджером
    if json_ok:
        manager_ok = test_position_loading()
        
        if manager_ok:
            print("\n🎉 Проблема исправлена! JSON загружается корректно")
        else:
            print("\n⚠️ JSON корректен, но менеджер всё ещё не может его загрузить")
    else:
        print("\n⚠️ Проблема в структуре JSON файла")
