"""
Простой тест DatabaseManager
Проверяет базовую функциональность
"""

import sys
from pathlib import Path

# Добавляем корень проекта в путь
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.config import create_tables
from database.database_manager import DatabaseManager

def test_database_manager():
    """Простой тест DatabaseManager."""
    print("🧪 Тестируем DatabaseManager...")
    
    # Создаем таблицы если их нет
    try:
        create_tables()
        print("✅ Таблицы созданы/проверены")
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        return
    
    # Инициализируем DatabaseManager
    try:
        db_manager = DatabaseManager()
        print("✅ DatabaseManager инициализирован")
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        return
    
    # Тестируем соединение
    if db_manager.test_connection():
        print("✅ Соединение с БД работает")
    else:
        print("❌ Проблема с соединением")
        return
    
    print("🎉 Базовые тесты пройдены!")

if __name__ == "__main__":
    test_database_manager()
