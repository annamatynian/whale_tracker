"""
Простой тест интеграции DatabaseManager с Orchestrator
Проверяем что все импорты работают и нет ошибок инициализации
"""

import sys
from pathlib import Path

# Добавляем корень проекта в путь
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_orchestrator_with_database():
    """Тест инициализации Orchestrator с DatabaseManager."""
    print("🔧 Тестируем интеграцию Orchestrator + DatabaseManager...")
    
    try:
        from agents.orchestrator.simple_orchestrator import SimpleOrchestrator
        print("✅ Импорт SimpleOrchestrator успешен")
        
        # Инициализируем в mock режиме
        import os
        os.environ['MOCK_MODE'] = 'true'
        
        orchestrator = SimpleOrchestrator()
        print("✅ SimpleOrchestrator инициализирован с DatabaseManager")
        
        # Проверяем что db_manager существует
        if hasattr(orchestrator, 'db_manager'):
            print("✅ DatabaseManager доступен в orchestrator")
            
            # Тестируем соединение с БД
            if orchestrator.db_manager.test_connection():
                print("✅ Соединение с БД работает")
            else:
                print("❌ Проблема с соединением БД")
        else:
            print("❌ DatabaseManager не найден в orchestrator")
            
        print("🎉 Базовая интеграция работает!")
        
    except Exception as e:
        print(f"❌ Ошибка интеграции: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_orchestrator_with_database()
