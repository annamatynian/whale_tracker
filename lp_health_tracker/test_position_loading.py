import os
import sys

# Добавим путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from simple_multi_pool import SimpleMultiPoolManager

# Создадим менеджер и попробуем загрузить позиции
manager = SimpleMultiPoolManager()

print("Testing position loading from JSON...")
success = manager.load_positions_from_json('data/positions.json')

if success:
    print("✅ Positions loaded successfully!")
    print(f"Loaded {manager.count_pools()} positions")
    pool_names = manager.list_pools()
    print(f"Pool names: {pool_names}")
else:
    print("❌ Failed to load positions")
