#!/usr/bin/env python3
"""
Минимальный тест только для Pydantic Settings без всех зависимостей.
"""

import sys
import os

def test_minimal_pydantic():
    """Тест только Pydantic Settings."""
    print("🧪 Minimal Pydantic Settings test...")
    
    try:
        # Очистка кеша модулей
        if 'config.settings' in sys.modules:
            del sys.modules['config.settings']
        
        # Импорт с принудительной перезагрузкой
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from config.settings import Settings
        print("✅ Import successful")
        
        # Создание с минимальными настройками
        settings = Settings(
            TELEGRAM_BOT_TOKEN="test_token_123",
            TELEGRAM_CHAT_ID="test_chat_456"
        )
        print("✅ Settings creation successful")
        
        # Тест базовых свойств
        print(f"✅ Network: {settings.DEFAULT_NETWORK}")
        print(f"✅ Interval: {settings.CHECK_INTERVAL_MINUTES}")
        print(f"✅ Threshold: {settings.DEFAULT_IL_THRESHOLD}")
        
        # Тест валидации
        try:
            bad_settings = Settings(
                TELEGRAM_BOT_TOKEN="test",
                TELEGRAM_CHAT_ID="test", 
                CHECK_INTERVAL_MINUTES=0
            )
            print("❌ Validation failed to catch error!")
            return False
        except ValueError as e:
            print(f"✅ Validation works: {e}")
        
        print("\n🎉 Minimal test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_minimal_pydantic()
    sys.exit(0 if success else 1)
